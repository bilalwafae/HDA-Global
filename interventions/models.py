"""
Modèle Intervention : planification des chantiers H.D.A GLOBAL.
Inspiré du modèle FSM de KodLyft — réimplémenté nativement en Django.
"""
from django.db import models
from demandes.models import Demande


class Intervention(models.Model):
    """
    Intervention sur chantier suite à l'acceptation d'un devis.
    Permet de planifier les dates, l'équipe et de suivre l'avancement des travaux.
    """
    STATUT_PLANIFIEE = "planifiee"
    STATUT_EN_COURS = "en_cours"
    STATUT_TERMINEE = "terminee"
    STATUT_ANNULEE = "annulee"

    STATUT_CHOICES = [
        (STATUT_PLANIFIEE, "Planifiée"),
        (STATUT_EN_COURS, "En cours"),
        (STATUT_TERMINEE, "Terminée"),
        (STATUT_ANNULEE, "Annulée"),
    ]

    demande = models.OneToOneField(
        Demande,
        on_delete=models.PROTECT,
        related_name="intervention",
        verbose_name="Demande",
    )
    statut_chantier = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default=STATUT_PLANIFIEE,
        verbose_name="Statut du chantier",
    )
    date_debut = models.DateField(verbose_name="Date de début des travaux")
    date_fin = models.DateField(
        null=True, blank=True,
        verbose_name="Date de fin prévue",
    )
    date_fin_reelle = models.DateField(
        null=True, blank=True,
        verbose_name="Date de fin réelle",
    )
    responsable_chantier = models.CharField(
        max_length=200,
        verbose_name="Responsable / Chef de chantier",
    )
    equipe_assignee = models.TextField(
        blank=True,
        verbose_name="Équipe assignée",
        help_text="Liste des ouvriers / techniciens assignés à ce chantier",
    )
    ville = models.CharField(
        max_length=100,
        verbose_name="Ville du chantier",
    )
    instructions_techniques = models.TextField(
        blank=True,
        verbose_name="Instructions et notes techniques",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["date_debut"]
        verbose_name = "Intervention chantier"
        verbose_name_plural = "Interventions chantier"

    def __str__(self):
        return (
            f"Chantier {self.demande.reference} — {self.ville} "
            f"({self.date_debut.strftime('%d/%m/%Y')})"
        )

