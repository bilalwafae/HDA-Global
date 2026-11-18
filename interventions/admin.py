from django.contrib import admin
from .models import Intervention


@admin.register(Intervention)
class InterventionAdmin(admin.ModelAdmin):
    list_display = ("demande", "responsable_chantier", "ville", "date_debut", "date_fin", "statut_chantier")
    list_filter = ("statut_chantier", "ville", "date_debut")
    search_fields = ("demande__reference", "responsable_chantier", "ville")
    date_hierarchy = "date_debut"
    fieldsets = (
        ("Chantier", {
            "fields": ("demande", "statut_chantier", "ville"),
        }),
        ("Planification", {
            "fields": ("date_debut", "date_fin", "date_fin_reelle"),
        }),
        ("Équipe", {
            "fields": ("responsable_chantier", "equipe_assignee"),
        }),
        ("Instructions", {
            "fields": ("instructions_techniques",),
            "classes": ("collapse",),
        }),
    )

