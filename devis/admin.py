from django.contrib import admin
from .models import Devis, LigneDevis
from .pricing import recalculer_devis


def fmt_mad(montant) -> str:
    """Format français « 1 085 400,00 MAD » pour les listes de l'admin."""
    from .pdf import fmt_mad as _fmt
    return _fmt(montant) + " MAD"


class LigneDevisInline(admin.TabularInline):
    model = LigneDevis
    extra = 1
    fields = ("designation", "quantite", "unite", "prix_unitaire_ht", "total_ligne_ht", "ordre")
    readonly_fields = ("total_ligne_ht",)


@admin.register(Devis)
class DevisAdmin(admin.ModelAdmin):
    list_display = ("numero", "client_nom", "statut_badge", "total_ttc_mad", "date_emission", "date_validite")
    list_filter = ("statut", "date_emission")
    search_fields = ("numero", "demande__client__nom_complet", "demande__reference")
    readonly_fields = ("numero", "sous_total_ht", "montant_tva", "total_ttc", "created_at", "updated_at")
    inlines = [LigneDevisInline]

    def total_ttc_mad(self, obj):
        return fmt_mad(obj.total_ttc)
    total_ttc_mad.short_description = "Total TTC"
    total_ttc_mad.admin_order_field = "total_ttc"

    fieldsets = (
        ("Identification", {
            "fields": ("numero", "demande", "statut"),
        }),
        ("Paramètres financiers", {
            "fields": ("taux_tva", "sous_total_ht", "montant_tva", "total_ttc"),
        }),
        ("Dates", {
            "fields": ("date_emission", "date_validite"),
        }),
        ("Conditions & Notes", {
            "fields": ("conditions_reglement", "notes"),
            "classes": ("collapse",),
        }),
        ("PDF", {
            "fields": ("fichier_pdf",),
            "classes": ("collapse",),
        }),
    )

    def client_nom(self, obj):
        return obj.demande.client.nom_complet
    client_nom.short_description = "Client"

    def statut_badge(self, obj):
        from django.utils.html import format_html
        couleur = obj.get_badge_couleur()
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            couleur, obj.get_statut_display()
        )
    statut_badge.short_description = "Statut"

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        recalculer_devis(obj)

