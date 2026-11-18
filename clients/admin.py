from django.contrib import admin
from .models import Client


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("nom_complet", "email", "telephone", "ville", "nb_demandes", "created_at")
    search_fields = ("nom_complet", "email", "telephone", "ville")
    list_filter = ("ville", "created_at")
    readonly_fields = ("created_at", "updated_at", "nb_demandes")
    fieldsets = (
        ("Coordonnées", {
            "fields": ("nom_complet", "email", "telephone", "ville", "adresse_principale"),
        }),
        ("Notes internes", {
            "fields": ("notes_admin",),
            "classes": ("collapse",),
        }),
        ("Métadonnées", {
            "fields": ("created_at", "updated_at", "nb_demandes"),
            "classes": ("collapse",),
        }),
    )

    def nb_demandes(self, obj):
        return obj.nb_demandes()
    nb_demandes.short_description = "Nbre demandes"

