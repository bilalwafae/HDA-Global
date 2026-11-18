"""
Administration Django pour le modèle Parametres.
Le Singleton est affiché comme un lien direct (pas de liste) dans l'admin.
"""
from django.contrib import admin
from django.shortcuts import redirect
from django.urls import reverse
from .models import Parametres


@admin.register(Parametres)
class ParametresAdmin(admin.ModelAdmin):
    """Administration du singleton Parametres — affiche directement le formulaire d'édition."""

    fieldsets = (
        ("Identité de l'entreprise", {
            "fields": ("nom_entreprise", "slogan", "logo"),
        }),
        ("Coordonnées & Contact", {
            "fields": ("telephone", "telephone_whatsapp", "email_contact",
                       "adresse_siege", "adresse_casablanca", "zones_intervention"),
        }),
        ("Identifiants légaux (PDF, pied de page, page Contact)", {
            "fields": ("ice", "identifiant_fiscal", "rc"),
        }),
        ("Paramètres Financiers", {
            "fields": ("tva_defaut", "prefixe_devis", "prefixe_demande",
                       "validite_devis_jours", "mentions_legales_devis"),
        }),
    )

    def has_add_permission(self, request):
        # Interdire la création d'un second enregistrement via l'admin
        return not Parametres.objects.exists()

    def has_delete_permission(self, request, obj=None):
        # Interdire la suppression du singleton
        return False

    def changelist_view(self, request, extra_context=None):
        # Rediriger directement vers le formulaire d'édition du singleton
        obj, _ = Parametres.objects.get_or_create(pk=1)
        return redirect(
            reverse("admin:core_parametres_change", args=[obj.pk])
        )

