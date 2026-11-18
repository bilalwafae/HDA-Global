"""
Modèles de l'application devis.
- Devis : document de chiffrage rattaché à une demande
- LigneDevis : articles/prestations du devis avec calculs unitaires
"""
from decimal import Decimal
from django.db import models
from django.utils import timezone

from demandes.models import Demande


class Devis(models.Model):
    """
    Devis commercial émis par H.D.A GLOBAL en réponse à une demande.
    Les montants sont calculés côté backend (moteur pricing.py).
    """

    STATUT_BROUILLON = "brouillon"
    STATUT_ENVOYE = "envoye"
    STATUT_ACCEPTE = "accepte"
    STATUT_REFUSE = "refuse"
    STATUT_PERIME = "perime"

    STATUT_CHOICES = [
        (STATUT_BROUILLON, "Brouillon"),
        (STATUT_ENVOYE, "Envoyé"),
        (STATUT_ACCEPTE, "Accepté"),
        (STATUT_REFUSE, "Refusé"),
        (STATUT_PERIME, "Périmé"),
    ]

    STATUT_COULEURS = {
        STATUT_BROUILLON: "secondary",
        STATUT_ENVOYE: "warning",
        STATUT_ACCEPTE: "success",
        STATUT_REFUSE: "danger",
        STATUT_PERIME: "muted",
    }

    # Identifiant
    numero = models.CharField(
        max_length=30,
        unique=True,
        blank=True,
        verbose_name="Numéro de devis",
        help_text="Généré automatiquement. Ex : DEV-2026-0001",
    )

    # Relation avec la demande
    demande = models.ForeignKey(
        Demande,
        on_delete=models.PROTECT,
        related_name="devis_set",
        verbose_name="Demande",
    )

    # Statut
    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default=STATUT_BROUILLON,
        verbose_name="Statut",
        db_index=True,
    )

    # Paramètres financiers
    taux_tva = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("20.00"),
        verbose_name="Taux TVA (%)",
    )

    # Totaux calculés (mis à jour par pricing.py)
    sous_total_ht = models.DecimalField(
        max_digits=12, decimal_places=2,
        default=Decimal("0.00"),
        verbose_name="Sous-total HT (MAD)",
    )
    montant_tva = models.DecimalField(
        max_digits=12, decimal_places=2,
        default=Decimal("0.00"),
        verbose_name="Montant TVA (MAD)",
    )
    total_ttc = models.DecimalField(
        max_digits=12, decimal_places=2,
        default=Decimal("0.00"),
        verbose_name="Total TTC (MAD)",
    )

    # Dates
    date_emission = models.DateField(
        default=timezone.localdate,
        verbose_name="Date d'émission",
    )
    date_validite = models.DateField(
        null=True, blank=True,
        verbose_name="Date limite de validité",
    )

    # PDF généré
    fichier_pdf = models.FileField(
        upload_to="devis/pdf/",
        blank=True,
        null=True,
        verbose_name="Fichier PDF",
    )

    # Conditions & notes
    conditions_reglement = models.TextField(
        blank=True,
        default="30% à la commande, 70% à la livraison des travaux.",
        verbose_name="Conditions de règlement",
    )
    notes = models.TextField(blank=True, verbose_name="Notes additionnelles")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Devis"
        verbose_name_plural = "Devis"

    def __str__(self):
        return f"{self.numero} — {self.demande.client.nom_complet} ({self.get_statut_display()})"

    def save(self, *args, **kwargs):
        if not self.numero:
            self.numero = self._generer_numero()
        if not self.date_validite:
            from core.models import Parametres
            params = Parametres.get()
            from datetime import timedelta
            self.date_validite = timezone.localdate() + timedelta(
                days=params.validite_devis_jours
            )
        super().save(*args, **kwargs)

    def _generer_numero(self):
        """Génère un numéro séquentiel de type DEV-2026-0001."""
        from core.models import Parametres
        params = Parametres.get()
        annee = timezone.now().year
        count = Devis.objects.filter(date_emission__year=annee).count() + 1
        return f"{params.prefixe_devis}-{annee}-{count:04d}"

    def get_badge_couleur(self):
        return self.STATUT_COULEURS.get(self.statut, "secondary")

    def est_perime(self):
        if self.date_validite and self.statut == self.STATUT_ENVOYE:
            return timezone.localdate() > self.date_validite
        return False


class LigneDevis(models.Model):
    """
    Article / ligne de prestation d'un devis.
    Le total de la ligne est calculé côté backend via pricing.py.
    """
    devis = models.ForeignKey(
        Devis,
        on_delete=models.CASCADE,
        related_name="lignes",
        verbose_name="Devis",
    )
    designation = models.CharField(max_length=300, verbose_name="Désignation des travaux")
    quantite = models.DecimalField(
        max_digits=10, decimal_places=2,
        default=Decimal("1.00"),
        verbose_name="Quantité",
    )
    unite = models.CharField(
        max_length=20,
        default="m²",
        verbose_name="Unité",
        help_text="m², ml, forfait, h, unité...",
    )
    prix_unitaire_ht = models.DecimalField(
        max_digits=10, decimal_places=2,
        default=Decimal("0.00"),
        verbose_name="Prix unitaire HT (MAD)",
    )
    total_ligne_ht = models.DecimalField(
        max_digits=12, decimal_places=2,
        default=Decimal("0.00"),
        verbose_name="Total ligne HT (MAD)",
        editable=False,
    )
    ordre = models.PositiveIntegerField(default=0, verbose_name="Ordre")

    class Meta:
        ordering = ["ordre", "pk"]
        verbose_name = "Ligne de devis"
        verbose_name_plural = "Lignes de devis"

    def __str__(self):
        return f"{self.designation} — {self.quantite} {self.unite} × {self.prix_unitaire_ht} MAD"

