from django.shortcuts import render, get_object_or_404
from .models import Service


def service_list(request):
    """Catalogue de tous les services TCE actifs."""
    services = Service.objects.filter(actif=True).order_by("ordre_affichage")
    return render(request, "services/list.html", {
        "services": services,
        "page_title": "Nos Services — H.D.A GLOBAL",
    })


def service_detail(request, slug):
    """Fiche détaillée d'un service avec galerie et bouton de demande de devis."""
    service = get_object_or_404(Service, slug=slug, actif=True)
    galerie = service.galerie.all()
    autres_services = Service.objects.filter(actif=True).exclude(pk=service.pk)[:3]
    return render(request, "services/detail.html", {
        "service": service,
        "galerie": galerie,
        "autres_services": autres_services,
        "page_title": f"{service.nom} — H.D.A GLOBAL",
    })

