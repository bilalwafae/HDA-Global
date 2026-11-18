"""
Modèles de l'application demandes :
- Demande : formulaire de demande de devis soumis par un visiteur/client
- PieceJointe : photos de chantier attachées à la demande
- HistoriqueStatut : traçabilité complète des changements de statut
"""
import uuid
from django.db import models
from django.utils import timezone

from clients.models import Client
from services.models import Service


class Demande(models.Model):
    """
    Demande de devis / d'intervention reçue de la part d'un client.
    Le statut suit un workflow défini dans SPEC : Nouvelle → Terminée.
    Le token_suivi (UUID4) permet au client d'accéder à son espace sans mot de passe.
    """

    # --- Statuts du workflow ---
    STATUT_NOUVELLE = "nouvelle"
    STATUT_EN_ETUDE = "en_etude"
    STATUT_DEVIS_ENVOYE = "devis_envoye"
    STATUT_ACCEPTEE = "acceptee"
    STATUT_PLANIFIEE = "planifiee"
    STATUT_EN_COURS = "en_cours"
    STATUT_TERMINEE = "terminee"
    STATUT_REFUSEE = "refusee"
    STATUT_ANNULEE = "annulee"

    STATUT_CHOICES = [
        (STATUT_NOUVELLE, "Nouvelle"),
        (STATUT_EN_ETUDE, "En étude"),
        (STATUT_DEVIS_ENVOYE, "Devis envoyé"),
        (STATUT_ACCEPTEE, "Acceptée"),
        (STATUT_PLANIFIEE, "Planifiée"),
        (STATUT_EN_COURS, "En cours"),
        (STATUT_TERMINEE, "Terminée"),
        (STATUT_REFUSEE, "Refusée"),
        (STATUT_ANNULEE, "Annulée"),
    ]

    # Couleur Bootstrap associée à chaque statut (pour les badges)
    STATUT_COULEURS = {
        STATUT_NOUVELLE: "primary",
        STATUT_EN_ETUDE: "info",
        STATUT_DEVIS_ENVOYE: "warning",
        STATUT_ACCEPTEE: "success",
        STATUT_PLANIFIEE: "secondary",
        STATUT_EN_COURS: "warning",
        STATUT_TERMINEE: "dark",
        STATUT_REFUSEE: "danger",
        STATUT_ANNULEE: "secondary",
    }

    # Identifiants
    reference = models.CharField(
        max_length=30,
        unique=True,
        blank=True,
        verbose_name="Référence",
        help_text="Générée automatiquement. Ex : DEM-2026-0001",
    )
    token_suivi = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        verbose_name="Token de suivi client",
        help_text="UUID4 sécurisé permettant au client de suivre sa demande sans mot de passe",
    )

    # Relations
    client = models.ForeignKey(
        Client,
        on_delete=models.PROTECT,
        related_name="demandes",
        verbose_name="Client",
    )
    service = models.ForeignKey(
        Service,
        on_delete=models.PROTECT,
        related_name="demandes",
        verbose_name="Service demandé",
        null=True,
        blank=True,
    )

    # Localisation du chantier
    ville_chantier = models.CharField(max_length=100, verbose_name="Ville du chantier")
    adresse_chantier = models.TextField(verbose_name="Adresse complète du chantier")
    surface_m2 = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Surface estimée (m²)",
    )

    # Détails de la demande
    date_souhaitee = models.DateField(
        null=True,
        blank=True,
        verbose_name="Date souhaitée d'intervention",
    )
    description_besoin = models.TextField(verbose_name="Description du besoin")

    # Statut & suivi
    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default=STATUT_NOUVELLE,
        verbose_name="Statut",
        db_index=True,
    )
    notes_internes = models.TextField(
        blank=True,
        verbose_name="Notes internes",
        help_text="Notes confidentielles pour l'équipe (non visibles par le client)",
    )

    # Horodatage
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Reçue le", db_index=True)
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Modifiée le")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Demande de devis"
        verbose_name_plural = "Demandes de devis"
        indexes = [
            models.Index(fields=["statut"]),
            models.Index(fields=["ville_chantier"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.reference} — {self.client.nom_complet} ({self.get_statut_display()})"

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = self._generer_reference()
        super().save(*args, **kwargs)

    def _generer_reference(self):
        """Génère une référence séquentielle de type DEM-2026-0001."""
        from core.models import Parametres
        params = Parametres.get()
        annee = timezone.now().year
        # Compter les demandes de l'année en cours
        count = Demande.objects.filter(created_at__year=annee).count() + 1
        return f"{params.prefixe_demande}-{annee}-{count:04d}"

    def get_badge_couleur(self):
        return self.STATUT_COULEURS.get(self.statut, "secondary")

    def get_devis_actif(self):
        """Retourne le devis le plus récent non refusé."""
        return self.devis_set.exclude(statut="refuse").order_by("-created_at").first()

    def changer_statut(self, nouveau_statut, auteur="Système", commentaire=""):
        """Change le statut et enregistre l'historique."""
        ancien_statut = self.statut
        if ancien_statut == nouveau_statut:
            return False
        HistoriqueStatut.objects.create(
            demande=self,
            ancien_statut=ancien_statut,
            nouveau_statut=nouveau_statut,
            auteur=auteur,
            commentaire=commentaire,
        )
        self.statut = nouveau_statut
        self.save(update_fields=["statut", "updated_at"])
        if nouveau_statut == self.STATUT_ACCEPTEE:
            from devis.workflow import devis_auto_a_l_acceptation
            devis_auto_a_l_acceptation(self)
        return True


class PieceJointe(models.Model):
    """Photos ou documents attachés à une demande (max 10 Mo par fichier)."""
    demande = models.ForeignKey(
        Demande,
        on_delete=models.CASCADE,
        related_name="pieces_jointes",
        verbose_name="Demande",
    )
    fichier = models.FileField(
        upload_to="demandes/pieces_jointes/%Y/%m/",
        verbose_name="Fichier",
    )
    nom_original = models.CharField(max_length=255, blank=True, verbose_name="Nom du fichier")
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="Uploadé le")

    class Meta:
        verbose_name = "Pièce jointe"
        verbose_name_plural = "Pièces jointes"

    def __str__(self):
        return f"{self.nom_original or self.fichier.name} — {self.demande.reference}"

    def save(self, *args, **kwargs):
        if self.fichier and not self.nom_original:
            self.nom_original = self.fichier.name.split("/")[-1]
        super().save(*args, **kwargs)

    def extension(self):
        name = self.nom_original or self.fichier.name
        return name.rsplit(".", 1)[-1].lower() if "." in name else "?"

    def est_image(self):
        return self.extension() in ("jpg", "jpeg", "png", "gif", "webp")


class HistoriqueStatut(models.Model):
    """
    Traçabilité complète des changements de statut d'une demande.
    Chaque transition est enregistrée avec son auteur et un commentaire optionnel.
    """
    demande = models.ForeignKey(
        Demande,
        on_delete=models.CASCADE,
        related_name="historique",
        verbose_name="Demande",
    )
    ancien_statut = models.CharField(
        max_length=20,
        choices=Demande.STATUT_CHOICES,
        verbose_name="Ancien statut",
    )
    nouveau_statut = models.CharField(
        max_length=20,
        choices=Demande.STATUT_CHOICES,
        verbose_name="Nouveau statut",
    )
    commentaire = models.TextField(blank=True, verbose_name="Commentaire")
    auteur = models.CharField(max_length=150, default="Système", verbose_name="Auteur")
    date_changement = models.DateTimeField(auto_now_add=True, verbose_name="Date")

    class Meta:
        ordering = ["-date_changement"]
        verbose_name = "Historique de statut"
        verbose_name_plural = "Historiques de statut"

    def __str__(self):
        return (
            f"{self.demande.reference} : "
            f"{self.get_ancien_statut_display()} → {self.get_nouveau_statut_display()}"
            f" ({self.date_changement.strftime('%d/%m/%Y %H:%M')})"
        )

