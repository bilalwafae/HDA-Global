from django.contrib import admin
from .models import Service, GalerieService


class GalerieInline(admin.TabularInline):
    model = GalerieService
    extra = 1
    fields = ("image", "legende", "ordre")


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("nom", "prix_affiche", "unite", "actif", "ordre_affichage")
    list_editable = ("actif", "ordre_affichage")
    list_filter = ("actif", "unite")
    search_fields = ("nom", "description_courte")
    prepopulated_fields = {"slug": ("nom",)}
    inlines = [GalerieInline]
    fieldsets = (
        ("Identité du service", {
            "fields": ("nom", "slug", "actif", "ordre_affichage"),
        }),
        ("Descriptions", {
            "fields": ("description_courte", "description_complete", "etapes_realisation"),
        }),
        ("Tarification", {
            "fields": ("prix_indicatif", "unite"),
        }),
        ("Visuel", {
            "fields": ("image_principale",),
        }),
    )

