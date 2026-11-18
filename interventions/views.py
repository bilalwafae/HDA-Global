from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from .models import Intervention


@staff_member_required
def planning(request):
    """Vue liste du planning des chantiers H.D.A GLOBAL."""
    interventions = Intervention.objects.select_related("demande__client", "demande__service").order_by("date_debut")
    stats = {
        "total": interventions.count(),
        "planifiee": interventions.filter(statut_chantier="planifiee").count(),
        "en_cours": interventions.filter(statut_chantier="en_cours").count(),
        "terminee": interventions.filter(statut_chantier="terminee").count(),
    }
    return render(request, "interventions/planning.html", {
        "interventions": interventions,
        "stats": stats,
        "page_title": "Planning des chantiers — H.D.A GLOBAL",
    })

