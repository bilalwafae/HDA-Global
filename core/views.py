"""
Vues de l'application core : Accueil, À propos, Contact, et Tableau de bord analytique.
"""
from decimal import Decimal
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Count, Sum

from services.models import Service
from clients.models import Client
from demandes.models import Demande
from devis.models import Devis
from interventions.models import Intervention


def home(request):
    """Page d'accueil : présentation de l'entreprise, 6 services TCE et CTA devis."""
    services_actifs = Service.objects.filter(actif=True).order_by("ordre_affichage")[:6]
    featured_service = services_actifs.first()
    other_services = services_actifs[1:4] if len(services_actifs) > 1 else []
    context = {
        "services": services_actifs,
        "featured_service": featured_service,
        "other_services": other_services,
        "page_title": "H.D.A GLOBAL — BTP & Construction TCE Casablanca & Mohammedia",
    }
    return render(request, "core/home.html", context)


def about(request):
    """Page À propos : histoire, valeurs et zones d'intervention H.D.A GLOBAL."""
    return render(request, "core/about.html", {
        "page_title": "À propos — H.D.A GLOBAL",
    })


def contact(request):
    """Page Contact avec formulaire de prise de contact rapide."""
    if request.method == "POST":
        nom = request.POST.get("nom", "").strip()
        email = request.POST.get("email", "").strip()
        telephone = request.POST.get("telephone", "").strip()
        sujet = request.POST.get("sujet", "Message depuis le site").strip()
        message_corps = request.POST.get("message", "").strip()
        honeypot = request.POST.get("website", "")
        if honeypot:
            messages.success(request, "Votre message a été envoyé. Nous vous répondrons dans les plus brefs délais.")
            return redirect("core:contact")

        if nom and email and message_corps:
            try:
                send_mail(
                    subject=f"[HDA Contact] {sujet} — {nom}",
                    message=(
                        f"Nouveau message de contact reçu sur le site H.D.A GLOBAL.\n\n"
                        f"Nom : {nom}\n"
                        f"Email : {email}\n"
                        f"Téléphone : {telephone}\n\n"
                        f"Message :\n{message_corps}"
                    ),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[settings.HDA_EMAIL],
                    fail_silently=True,
                )
                messages.success(
                    request,
                    "Votre message a été envoyé avec succès ! Nous vous répondrons dans les plus brefs délais.",
                )
            except Exception:
                messages.warning(
                    request,
                    "Message reçu. Vous pouvez aussi nous joindre directement par téléphone.",
                )
            return redirect("core:contact")
        else:
            messages.error(request, "Veuillez remplir tous les champs obligatoires.")

    return render(request, "core/contact.html", {
        "page_title": "Contact — H.D.A GLOBAL",
    })


def mentions_legales(request):
    return render(request, "core/mentions_legales.html", {
        "page_title": "Mentions légales — H.D.A GLOBAL",
    })


@staff_member_required
def dashboard(request):
    """
    Tableau de bord de gestion & KPIs analytiques pour l'entreprise H.D.A GLOBAL.
    Version Haute Fidélité Bento Grid avec données dynamiques temps réel.
    """
    total_demandes = Demande.objects.count()
    nouvelles_demandes = Demande.objects.filter(statut=Demande.STATUT_NOUVELLE).count()
    en_etude = Demande.objects.filter(statut=Demande.STATUT_EN_ETUDE).count()
    chantiers_en_cours = Demande.objects.filter(statut=Demande.STATUT_EN_COURS).count()

    total_devis = Devis.objects.count()
    devis_acceptes = Devis.objects.filter(statut=Devis.STATUT_ACCEPTE)
    nb_devis_acceptes = devis_acceptes.count()

    ca_total_ttc = devis_acceptes.aggregate(total=Sum("total_ttc"))["total"] or Decimal("0.00")
    ca_potentiel_ttc = Devis.objects.aggregate(total=Sum("total_ttc"))["total"] or Decimal("0.00")

    taux_conversion = (nb_devis_acceptes / total_devis * 100) if total_devis > 0 else 0

    # 1. Donut Chart 1 : Répartition du CA par Métier TCE
    circumference = 339.29
    colors_metiers = ["#2563EB", "#EA580C", "#059669", "#0284C7", "#7C3AED", "#D97706"]
    ca_total_float = float(ca_total_ttc) if ca_total_ttc > 0 else 1.0
    services_donut = []
    offset_metiers = 0.0

    for i, s in enumerate(Service.objects.all().order_by("ordre_affichage")):
        ca_srv = float(
            Devis.objects.filter(demande__service=s, statut=Devis.STATUT_ACCEPTE).aggregate(
                total=Sum("total_ttc")
            )["total"]
            or 0
        )
        pct = (ca_srv / ca_total_float * 100) if ca_total_float > 0 else 0.0
        dash = (pct / 100.0) * circumference
        services_donut.append({
            "id": f"slice-{i+1}",
            "nom": s.nom,
            "ca": ca_srv,
            "ca_formatted": f"{ca_srv:,.0f} MAD".replace(",", " "),
            "pct": round(pct, 1),
            "color": colors_metiers[i % len(colors_metiers)],
            "dasharray": f"{dash:.2f} {circumference:.2f}",
            "dashoffset": f"{-offset_metiers:.2f}",
        })
        offset_metiers += dash

    # 2. Donut Chart 2 : Pipeline Demandes & Conversion
    pipeline_config = [
        {"id": "pipe-1", "label": "En cours sur site", "statuts": [Demande.STATUT_EN_COURS], "color": "#EA580C", "tag": "chantiers"},
        {"id": "pipe-2", "label": "Devis émis au client", "statuts": [Demande.STATUT_DEVIS_ENVOYE], "color": "#00102D", "tag": "devis"},
        {"id": "pipe-3", "label": "Nouvelles demandes", "statuts": [Demande.STATUT_NOUVELLE], "color": "#F59E0B", "tag": "à chiffrer"},
        {"id": "pipe-4", "label": "Réceptionnées / Finies", "statuts": [Demande.STATUT_TERMINEE], "color": "#10B981", "tag": "livrées"},
        {"id": "pipe-5", "label": "En métré & étude", "statuts": [Demande.STATUT_EN_ETUDE, Demande.STATUT_PLANIFIEE, Demande.STATUT_REFUSEE, Demande.STATUT_ANNULEE], "color": "#64748B", "tag": "dossiers"},
    ]
    pipeline_donut = []
    offset_pipe = 0.0
    for p in pipeline_config:
        cnt = Demande.objects.filter(statut__in=p["statuts"]).count()
        pct = (cnt / total_demandes * 100) if total_demandes > 0 else 0.0
        dash = (pct / 100.0) * circumference
        pipeline_donut.append({
            "id": p["id"],
            "label": p["label"],
            "count": cnt,
            "tag": p["tag"],
            "color": p["color"],
            "pct": round(pct, 1),
            "dasharray": f"{dash:.2f} {circumference:.2f}",
            "dashoffset": f"{-offset_pipe:.2f}",
        })
        offset_pipe += dash

    # 3. Histogramme Géographique Villes BTP
    villes_raw = Demande.objects.values("ville_chantier").annotate(count=Count("ville_chantier")).order_by("-count")
    villes_data = []
    palette_villes = [
        {"bg": "bg-gradient-to-r from-primary to-[#1E3A6C]", "badge": "Grand Casa", "desc": "Gauthier, CIL, Racine, Oulfa"},
        {"bg": "bg-secondary", "badge": "Axe Nord", "desc": "Port, Parc & Centre"},
        {"bg": "bg-teal-600", "badge": "Périphérie", "desc": "Siège H.D.A & Périphérie"},
        {"bg": "bg-indigo-600", "badge": "Industriel", "desc": "Zone Industrielle & Pavillons"},
        {"bg": "bg-slate-400", "badge": "Sud", "desc": "Bouskoura Ville Verte & Settat"},
    ]
    for i, v in enumerate(villes_raw[:5]):
        cnt = v["count"]
        pct = (cnt / total_demandes * 100) if total_demandes > 0 else 0.0
        style = palette_villes[i % len(palette_villes)]
        villes_data.append({
            "ville": v["ville_chantier"],
            "count": cnt,
            "pct": round(pct, 1),
            "width": max(15, min(100, int(cnt / (villes_raw[0]["count"] or 1) * 85))),
            "bg": style["bg"],
            "desc": style["desc"],
        })

    # 4. Liste Complète des Dossiers Clients avec Devis rattaché
    demandes_qs = (
        Demande.objects.select_related("client", "service")
        .prefetch_related("devis_set")
        .order_by("-created_at")
    )
    demandes_table = []
    for d in demandes_qs:
        devis_actif = d.get_devis_actif()
        montant = float(devis_actif.total_ttc) if devis_actif else 0.0
        
        # Style de badge par statut
        badge_class = "bg-slate-100 text-slate-700 border-slate-200"
        if d.statut == Demande.STATUT_NOUVELLE:
            badge_class = "bg-amber-50 text-amber-700 border-amber-200"
        elif d.statut == Demande.STATUT_EN_COURS:
            badge_class = "bg-orange-50 text-[#C84500] border-orange-200 font-bold"
        elif d.statut == Demande.STATUT_TERMINEE:
            badge_class = "bg-emerald-50 text-emerald-700 border-emerald-200"
        elif d.statut == Demande.STATUT_DEVIS_ENVOYE:
            badge_class = "bg-blue-50 text-blue-700 border-blue-200"
        elif d.statut == Demande.STATUT_EN_ETUDE:
            badge_class = "bg-indigo-50 text-indigo-700 border-indigo-200"
        elif d.statut == Demande.STATUT_REFUSEE:
            badge_class = "bg-rose-50 text-rose-700 border-rose-200"

        demandes_table.append({
            "id": d.id,
            "reference": d.reference,
            "client_nom": d.client.nom_complet,
            "client_email": d.client.email,
            "client_tel": d.client.telephone,
            "service_nom": d.service.nom if d.service else "TCE Multi-lots",
            "ville": d.ville_chantier,
            "adresse": d.adresse_chantier,
            "statut": d.statut,
            "statut_label": d.get_statut_display(),
            "badge_class": badge_class,
            "devis": devis_actif,
            "montant": montant,
            "montant_formatted": f"{montant:,.0f} MAD".replace(",", " ") if montant > 0 else "Non chiffré",
            "token_suivi": d.token_suivi,
        })

    context = {
        "page_title": "Tableau de Bord Exécutif — H.D.A GLOBAL",
        "total_demandes": total_demandes,
        "nouvelles_demandes": nouvelles_demandes,
        "en_etude": en_etude,
        "chantiers_en_cours": chantiers_en_cours,
        "total_devis": total_devis,
        "nb_devis_acceptes": nb_devis_acceptes,
        "ca_total_ttc": ca_total_ttc,
        "ca_total_formatted": f"{float(ca_total_ttc):,.0f} MAD".replace(",", " "),
        "ca_potentiel_ttc": ca_potentiel_ttc,
        "ca_potentiel_formatted": f"{float(ca_potentiel_ttc):,.0f} MAD".replace(",", " "),
        "taux_conversion": round(taux_conversion, 1),
        "services_donut": services_donut,
        "pipeline_donut": pipeline_donut,
        "villes_data": villes_data,
        "demandes_table": demandes_table,
    }
    return render(request, "core/dashboard.html", context)


# ── Médias privés (production) ───────────────────────────────────────────────
from django.contrib.admin.views.decorators import staff_member_required as _staff_required
from django.conf import settings as _settings
from django.http import FileResponse as _FileResponse, Http404 as _Http404
from django.utils._os import safe_join as _safe_join
import mimetypes as _mimetypes
import os as _os


def media_protege(request, chemin):
    """Photos de chantier et PDF de devis : réservés au personnel connecté.
    Les images de services (dossier services/) sont publiques."""
    if not chemin.startswith("services/") and not (request.user.is_authenticated and request.user.is_staff):
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path(), "/admin/login/")
    try:
        fichier = _safe_join(_settings.MEDIA_ROOT, chemin)
    except Exception:
        raise _Http404()
    if not _os.path.isfile(fichier):
        raise _Http404()
    return _FileResponse(open(fichier, "rb"), content_type=_mimetypes.guess_type(fichier)[0] or "application/octet-stream")
