"""
Modèle Service : catalogue des prestations TCE de H.D.A GLOBAL.
6 services de départ sont chargés par les fixtures de démonstration.
"""
from django.db import models
from django.utils.text import slugify


class Service(models.Model):
    """
    Prestation proposée par H.D.A GLOBAL.
    Exemples : Construction & rénovation, Climatisation, Plomberie, etc.
    """
    UNITE_CHOICES = [
        ("m2", "m²"),
        ("ml", "mètre linéaire"),
        ("forfait", "Forfait"),
        ("unite", "Unité"),
        ("heure", "Heure"),
    ]

    nom = models.CharField(max_length=200, verbose_name="Nom du service")
    slug = models.SlugField(max_length=220, unique=True, blank=True, verbose_name="Slug URL")
    description_courte = models.CharField(
        max_length=300,
        verbose_name="Description courte",
        help_text="Affiché sur la carte service (max 300 caractères)",
    )
    description_complete = models.TextField(
        verbose_name="Description complète",
        help_text="Description longue affichée sur la page détail du service",
    )
    etapes_realisation = models.TextField(
        blank=True,
        verbose_name="Étapes de réalisation",
        help_text="Une étape par ligne. Ex : '1. Diagnostic initial'",
    )
    image_principale = models.ImageField(
        upload_to="services/images/",
        blank=True,
        null=True,
        verbose_name="Image principale",
    )
    prix_indicatif = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Prix indicatif (MAD)",
        help_text="Laissez vide pour afficher 'Sur devis'",
    )
    unite = models.CharField(
        max_length=20,
        choices=UNITE_CHOICES,
        default="m2",
        verbose_name="Unité de prix",
    )
    actif = models.BooleanField(default=True, verbose_name="Service actif")
    ordre_affichage = models.PositiveIntegerField(
        default=0,
        verbose_name="Ordre d'affichage",
        help_text="Nombre faible = affiché en premier",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Modifié le")

    class Meta:
        ordering = ["ordre_affichage", "nom"]
        verbose_name = "Service TCE"
        verbose_name_plural = "Services TCE"

    def __str__(self):
        return self.nom

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nom)
        super().save(*args, **kwargs)

    def prix_affiche(self):
        """Retourne le prix formaté ou 'Sur devis'."""
        if self.prix_indicatif:
            return f"À partir de {self.prix_indicatif:,.0f} MAD/{self.get_unite_display()}"
        return "Sur devis"

    def get_etapes_list(self):
        """Retourne les étapes de réalisation sous forme de liste."""
        if not self.etapes_realisation:
            return []
        return [line.strip() for line in self.etapes_realisation.split("\n") if line.strip()]


class GalerieService(models.Model):
    """Photos de réalisations associées à un service."""
    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name="galerie",
        verbose_name="Service",
    )
    image = models.ImageField(upload_to="services/galerie/", verbose_name="Photo")
    legende = models.CharField(max_length=200, blank=True, verbose_name="Légende")
    ordre = models.PositiveIntegerField(default=0, verbose_name="Ordre")

    class Meta:
        ordering = ["ordre"]
        verbose_name = "Photo de réalisation"
        verbose_name_plural = "Galerie de réalisations"

    def __str__(self):
        return f"Photo {self.pk} — {self.service.nom}"

