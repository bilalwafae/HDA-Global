"""
Vues de l'application demandes :
- create : formulaire public de demande de devis
- confirmation : page de succès après soumission
- suivi : portail client sécurisé par token UUID
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_POST

from clients.models import Client
from services.models import Service
from .models import Demande, PieceJointe
from .forms import DemandeDevisForm
from .emails import envoyer_confirmation_client, envoyer_notification_admin
from .securite_suivi import demande_du_lien, suivi_securise, page_expiree


def create(request):
    """
    Formulaire public de demande de devis.
    À la soumission :
    1. Création automatique du client (ou mise à jour s'il existe déjà)
    2. Création de la demande avec référence auto
    3. Sauvegarde des photos de chantier
    4. Envoi emails (confirmation client + alerte admin)
    5. Redirection vers la page de confirmation
    """
    # Pré-sélection d'un service si passé en paramètre GET (depuis la page détail service)
    service_preselect = request.GET.get("service")

    if request.method == "POST":
        form = DemandeDevisForm(request.POST, request.FILES)
        if form.is_valid():
            cd = form.cleaned_data

            # Honeypot : si rempli (bot), simuler un succès silencieux
            if cd.get("website"):
                return redirect("demandes:confirmation", reference="BOT-DETECTED")

            # 1. Créer/récupérer le client
            client, _ = Client.get_or_create_from_form(
                nom=cd["nom_complet"],
                email=cd["email"],
                telephone=cd["telephone"],
                ville=cd["ville_chantier"],
            )

            # 2. Créer la demande
            demande = Demande.objects.create(
                client=client,
                service=cd.get("service"),
                ville_chantier=cd["ville_chantier"],
                adresse_chantier=cd["adresse_chantier"],
                date_souhaitee=cd.get("date_souhaitee"),
                surface_m2=cd.get("surface_m2"),
                description_besoin=cd["description_besoin"],
                statut=Demande.STATUT_NOUVELLE,
            )

            # 3. Sauvegarder les pièces jointes (photos du chantier)
            for fichier in request.FILES.getlist("photos"):
                # Validation du type de fichier
                if fichier.content_type not in [
                    "image/jpeg", "image/png", "image/webp", "application/pdf"
                ]:
                    continue
                if fichier.size > 10 * 1024 * 1024:
                    continue
                PieceJointe.objects.create(
                    demande=demande,
                    fichier=fichier,
                    nom_original=fichier.name,
                )

            # 4. Envoi des emails automatiques
            envoyer_confirmation_client(demande)
            envoyer_notification_admin(demande)

            # 4bis. Pré-génération d'un devis BROUILLON (si activée).
            # L'IA / le moteur ne doivent JAMAIS bloquer la soumission du
            # client : tout échec est ignoré silencieusement.
            from django.conf import settings as hda_settings
            if getattr(hda_settings, "DEVIS_AUTO_A_LA_CREATION", True):
                try:
                    from devis.auto import generer_devis_automatique
                    generer_devis_automatique(demande, utiliser_ia=True)
                except Exception:
                    # L'IA / le moteur ne bloquent jamais une demande client.
                    pass

            # 5. Redirection vers la confirmation
            return redirect("demandes:confirmation", reference=demande.reference)
        else:
            messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
    else:
        initial = {}
        if service_preselect:
            try:
                service_obj = Service.objects.get(slug=service_preselect, actif=True)
                initial["service"] = service_obj
            except Service.DoesNotExist:
                pass
        form = DemandeDevisForm(initial=initial)

    return render(request, "demandes/create.html", {
        "form": form,
        "page_title": "Demander un devis — H.D.A GLOBAL",
    })


def confirmation(request, reference):
    """
    Page de confirmation post-soumission.
    Affiche le numéro de référence et le lien de suivi.
    """
    try:
        demande = Demande.objects.select_related("client", "service").get(reference=reference)
    except Demande.DoesNotExist:
        demande = None

    return render(request, "demandes/confirmation.html", {
        "demande": demande,
        "reference": reference,
        "page_title": "Demande envoyée avec succès — H.D.A GLOBAL",
    })


@suivi_securise
def suivi(request, token):
    """
    Portail client sécurisé par token UUID (voir securite_suivi.py) :
    n'affiche QUE la demande du lien, expire après une longue inactivité.
    """
    demande, expiree = demande_du_lien(request, token)
    if expiree:
        return page_expiree(request)
    client = demande.client
    devis_actif = demande.get_devis_actif()
    historique = demande.historique.all()

    return render(request, "demandes/suivi.html", {
        "demande": demande,
        "client": client,
        "devis_actif": devis_actif,
        "historique": historique,
        "page_title": f"Suivi de votre demande {demande.reference}",
    })

