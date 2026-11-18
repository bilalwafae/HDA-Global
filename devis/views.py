"""Vues de l'application devis."""
from demandes.securite_suivi import demande_du_lien, page_expiree, suivi_securise
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.http import FileResponse, Http404
from django.contrib import messages
from django.views.decorators.http import require_POST

from demandes.models import Demande
from .models import Devis, LigneDevis
from .pricing import recalculer_devis
from .pdf import sauvegarder_pdf_devis
from .auto import generer_devis_automatique, lire_notes_auto


@staff_member_required
def creer_devis(request, demande_id):
    """Vue admin : création d'un devis depuis une demande."""
    demande = get_object_or_404(Demande, pk=demande_id)

    if request.method == "POST":
        # Créer le devis
        from core.models import Parametres
        params = Parametres.get()
        devis = Devis.objects.create(
            demande=demande,
            taux_tva=params.tva_defaut,
            conditions_reglement="30% à la commande, 70% à la livraison.",
        )
        messages.success(request, f"Devis {devis.numero} créé. Ajoutez maintenant les lignes de prestations.")
        return redirect("devis:editer", pk=devis.pk)

    return render(request, "devis/creer.html", {
        "demande": demande,
        "page_title": f"Créer un devis — {demande.reference}",
    })


@staff_member_required
@require_POST
def generer_auto(request, demande_id):
    """
    Génère le devis BROUILLON automatiquement pour une demande, puis
    redirige vers l'édition pour relecture humaine.

    Attention :
    - le devis ne part JAMAIS tout seul : il reste en « brouillon »
      jusqu'au clic sur « Envoyer au client » ;
    - l'IA est optionnelle (sans clé API, chiffrage catalogue pur) ;
    - en cas d'échec, on revient vers la création manuelle.
    """
    demande = get_object_or_404(Demande, pk=demande_id)
    try:
        devis = generer_devis_automatique(demande, utiliser_ia=True)
        # Si un devis actif existait déjà : idempotent, on le dit
        messages.success(
            request,
            f"Devis brouillon {devis.numero} généré automatiquement. "
            "Relisez les lignes et les quantités avant envoi au client.",
        )
        return redirect("devis:editer", pk=devis.pk)
    except Exception as erreur:
        messages.error(
            request,
            f"Échec de la génération automatique : {erreur}. "
            "Vous pouvez créer le devis manuellement.",
        )
        return redirect("devis:creer", demande_id=demande.pk)


@staff_member_required
def editer_devis(request, pk):
    """Vue admin : édition des lignes d'un devis et calcul automatique."""
    devis = get_object_or_404(Devis, pk=pk)

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "ajouter_ligne":
            designation = request.POST.get("designation", "").strip()
            quantite = request.POST.get("quantite", "1")
            unite = request.POST.get("unite", "m²")
            prix = request.POST.get("prix_unitaire_ht", "0")
            if designation:
                LigneDevis.objects.create(
                    devis=devis,
                    designation=designation,
                    quantite=quantite,
                    unite=unite,
                    prix_unitaire_ht=prix,
                    ordre=devis.lignes.count(),
                )
                recalculer_devis(devis)
                messages.success(request, "Ligne ajoutée.")

        elif action == "supprimer_ligne":
            ligne_id = request.POST.get("ligne_id")
            LigneDevis.objects.filter(pk=ligne_id, devis=devis).delete()
            recalculer_devis(devis)
            messages.success(request, "Ligne supprimée.")

        elif action == "sauvegarder":
            notes = request.POST.get("notes", "")
            conditions = request.POST.get("conditions_reglement", "")
            devis.notes = notes
            devis.conditions_reglement = conditions
            devis.save(update_fields=["notes", "conditions_reglement", "updated_at"])
            messages.success(request, "Devis sauvegardé.")

        elif action == "generer_pdf":
            sauvegarder_pdf_devis(devis)
            messages.success(request, f"PDF du devis {devis.numero} généré avec succès.")

        elif action == "envoyer_client":
            from demandes.emails import envoyer_devis_client
            if not devis.lignes.exists():
                messages.error(request, "Ajoutez au moins une ligne avant d'envoyer le devis.")
            else:
                ok, erreur = envoyer_devis_client(devis)  # régénère le PDF + email avec pièce jointe
                if ok:
                    devis.statut = Devis.STATUT_ENVOYE
                    devis.save(update_fields=["statut", "updated_at"])
                    devis.demande.changer_statut(
                        "devis_envoye",
                        auteur=request.user.get_full_name() or request.user.username,
                        commentaire=f"Devis {devis.numero} envoyé au client par email (PDF joint)",
                    )
                    messages.success(
                        request,
                        f"Devis {devis.numero} envoyé à {devis.demande.client.email} (PDF en pièce jointe).",
                    )
                else:
                    messages.error(
                        request,
                        f"L'email n'a PAS été envoyé : {erreur}. Le statut n'a pas changé ; "
                        "vérifiez la configuration SMTP (.env) puis réessayez.",
                    )

        return redirect("devis:editer", pk=devis.pk)

    return render(request, "devis/editer.html", {
        "devis": devis,
        "lignes": devis.lignes.all(),
        "notes_auto": lire_notes_auto(devis),
        "page_title": f"Édition devis {devis.numero}",
    })


@suivi_securise
def telecharger_pdf(request, token, pk):
    """Téléchargement sécurisé du PDF par le client (via son token)."""
    demande, expiree = demande_du_lien(request, token)
    if expiree:
        return page_expiree(request)
    devis = get_object_or_404(Devis, pk=pk, demande=demande)
    if not devis.fichier_pdf:
        sauvegarder_pdf_devis(devis)
    return FileResponse(
        devis.fichier_pdf.open("rb"),
        as_attachment=True,
        filename=f"devis_{devis.numero}.pdf",
        content_type="application/pdf",
    )


@require_POST
@suivi_securise
def action_client(request, token, pk):
    """Le client accepte ou refuse le devis depuis son portail de suivi."""
    demande, expiree = demande_du_lien(request, token)
    if expiree:
        return page_expiree(request)
    devis = get_object_or_404(
        Devis, pk=pk, demande=demande,
        statut__in=[Devis.STATUT_ENVOYE, Devis.STATUT_BROUILLON],
    )
    action = request.POST.get("action")

    if action == "accepter":
        devis.statut = Devis.STATUT_ACCEPTE
        devis.save(update_fields=["statut", "updated_at"])
        demande.changer_statut("acceptee", auteur=demande.client.nom_complet, commentaire="Devis accepté par le client via le portail de suivi")
        messages.success(request, f"Vous avez accepté le devis {devis.numero}. Notre équipe vous contactera pour planifier les travaux.")
    elif action == "refuser":
        motif = request.POST.get("motif_refus", "")
        devis.statut = Devis.STATUT_REFUSE
        devis.notes += f"\n[Refus client] {motif}" if motif else "\n[Devis refusé par le client]"
        devis.save(update_fields=["statut", "notes", "updated_at"])
        demande.changer_statut("refusee", auteur=demande.client.nom_complet, commentaire=f"Devis refusé. Motif : {motif}")
        messages.info(request, "Vous avez refusé le devis. Nous restons disponibles pour toute question.")

    return redirect("suivi:detail", token=token)

