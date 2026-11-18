from django.contrib import admin, messages
from django.urls import reverse
from django.utils.html import format_html
from .models import Demande, PieceJointe, HistoriqueStatut


class PieceJointeInline(admin.TabularInline):
    model = PieceJointe
    extra = 0
    readonly_fields = ("nom_original", "uploaded_at")
    fields = ("fichier", "nom_original", "uploaded_at")


class HistoriqueStatutInline(admin.TabularInline):
    model = HistoriqueStatut
    extra = 0
    readonly_fields = ("ancien_statut", "nouveau_statut", "auteur", "commentaire", "date_changement")
    ordering = ["-date_changement"]
    can_delete = False


@admin.register(Demande)
class DemandeAdmin(admin.ModelAdmin):
    list_display = (
        "reference", "client", "service", "statut_badge",
        "ville_chantier", "created_at",
    )
    list_filter = ("statut", "ville_chantier", "service", "created_at")
    search_fields = ("reference", "client__nom_complet", "client__email", "ville_chantier")
    readonly_fields = ("reference", "token_suivi", "created_at", "updated_at", "devis_lien")
    actions = ["accepter_et_generer_devis"]
    inlines = [PieceJointeInline, HistoriqueStatutInline]
    date_hierarchy = "created_at"
    list_per_page = 25

    fieldsets = (
        ("Identification", {
            "fields": ("reference", "token_suivi", "statut", "devis_lien"),
        }),
        ("Client & Service", {
            "fields": ("client", "service"),
        }),
        ("Chantier", {
            "fields": ("ville_chantier", "adresse_chantier", "surface_m2", "date_souhaitee"),
        }),
        ("Description", {
            "fields": ("description_besoin",),
        }),
        ("Notes internes (admin)", {
            "fields": ("notes_internes",),
            "classes": ("collapse",),
        }),
        ("Métadonnées", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    def statut_badge(self, obj):
        from django.utils.html import format_html
        couleur = obj.get_badge_couleur()
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            couleur, obj.get_statut_display()
        )
    statut_badge.short_description = "Statut"

    def devis_lien(self, obj):
        """Lien direct vers le devis (relecture / envoi au client)."""
        if not obj or not obj.pk:
            return "—"
        devis = obj.get_devis_actif()
        if devis is None:
            return "Aucun devis — il sera généré automatiquement quand le statut passera à « Acceptée »."
        url = reverse("devis:editer", args=[devis.pk])
        return format_html(
            '<a class="button" href="{}">Ouvrir le devis {} ({}) → relire et envoyer au client</a>',
            url, devis.numero, devis.get_statut_display(),
        )
    devis_lien.short_description = "Devis"

    def _signaler_devis_auto(self, request, demande):
        """Message admin après acceptation : devis généré + lien pour l'envoyer."""
        from devis.workflow import devis_auto_a_l_acceptation
        devis, cree = devis_auto_a_l_acceptation(demande)
        if devis is None:
            messages.warning(request, f"{demande.reference} : le devis n'a pas pu être généré automatiquement. "
                                      "Créez-le depuis la fiche de la demande.")
            return
        url = reverse("devis:editer", args=[devis.pk])
        verbe = "généré automatiquement" if cree else "déjà existant"
        messages.success(request, format_html(
            'Devis <b>{}</b> {} pour {}. <a href="{}"><b>Ouvrir, relire et cliquer « Envoyer au client »</b></a>',
            devis.numero, verbe, demande.reference, url,
        ))

    @admin.action(description="Marquer « Acceptée » et générer le devis automatiquement")
    def accepter_et_generer_devis(self, request, queryset):
        auteur = request.user.get_full_name() or request.user.username
        for demande in queryset:
            if demande.statut != Demande.STATUT_ACCEPTEE:
                demande.changer_statut(Demande.STATUT_ACCEPTEE, auteur=auteur,
                                       commentaire="Acceptée via action groupée (back-office)")
            else:
                self._signaler_devis_auto(request, demande)
                continue
            self._signaler_devis_auto(request, demande)

    def save_model(self, request, obj, form, change):
        ancien = None
        if change:
            ancien = Demande.objects.get(pk=obj.pk).statut
            if ancien != obj.statut:
                HistoriqueStatut.objects.create(
                    demande=obj,
                    ancien_statut=ancien,
                    nouveau_statut=obj.statut,
                    auteur=request.user.get_full_name() or request.user.username,
                    commentaire="Changement via back-office admin",
                )
        super().save_model(request, obj, form, change)
        # Statut passé à « Acceptée » : génération automatique du devis brouillon
        if change and ancien != obj.statut and obj.statut == Demande.STATUT_ACCEPTEE:
            self._signaler_devis_auto(request, obj)
