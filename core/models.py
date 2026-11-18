"""
Modèles de l'application core.

Parametres : singleton contenant les informations de l'entreprise H.D.A GLOBAL.
Un seul enregistrement est autorisé en base (pattern Singleton via save()).
"""
from django.db import models
from django.core.exceptions import ValidationError


class Parametres(models.Model):
    """
    Singleton des paramètres de l'entreprise H.D.A GLOBAL.
    Contient le logo, les coordonnées, la TVA et la numérotation des devis.
    """
    nom_entreprise = models.CharField(
        max_length=200,
        default="H.D.A GLOBAL SARL",
        verbose_name="Raison sociale",
    )
    slogan = models.CharField(
        max_length=300,
        default="Votre partenaire de confiance pour tous vos projets BTP",
        verbose_name="Slogan",
    )
    logo = models.ImageField(
        upload_to="core/logos/",
        blank=True,
        null=True,
        verbose_name="Logo de l'entreprise",
    )
    telephone = models.CharField(
        max_length=20,
        default="+212 661103988",
        verbose_name="Téléphone",
    )
    telephone_whatsapp = models.CharField(
        max_length=20,
        blank=True,
        default="212661103988",
        verbose_name="Numéro WhatsApp (sans +, sans espaces)",
        help_text="Utilisé pour générer le lien wa.me/. Ex: 212661103988",
    )
    email_contact = models.EmailField(
        default="hda.global82@gmail.com",
        verbose_name="Email de contact",
    )
    adresse_siege = models.CharField(
        max_length=300,
        default="Beni Yakhlef, Mohammedia",
        verbose_name="Adresse du siège",
    )
    adresse_casablanca = models.CharField(
        max_length=300,
        blank=True,
        default="11, rue Ahmed Sitou, Etage 2, Appt 3, BD Mohamed V, 20000, Casablanca",
        verbose_name="Adresse de Casablanca",
    )
    zones_intervention = models.TextField(
        default="Mohammedia, Casablanca, Beni Yakhlef, Berrechid, Settat et environs",
        verbose_name="Zones d'intervention",
        help_text="Séparez les villes par des virgules",
    )
    tva_defaut = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=20.00,
        verbose_name="Taux TVA par défaut (%)",
        help_text="TVA marocaine standard : 20%",
    )
    prefixe_devis = models.CharField(
        max_length=10,
        default="DEV",
        verbose_name="Préfixe numérotation devis",
        help_text="Ex : DEV → DEV-2026-0001",
    )
    prefixe_demande = models.CharField(
        max_length=10,
        default="DEM",
        verbose_name="Préfixe numérotation demandes",
    )
    validite_devis_jours = models.PositiveIntegerField(
        default=30,
        verbose_name="Validité des devis (jours)",
    )
    mentions_legales_devis = models.TextField(
        blank=True,
        default=(
            "Devis valable 30 jours à compter de la date d'émission. "
            "Le règlement s'effectue à 30% à la commande et 70% à la livraison. "
            "TVA 20% applicable."
        ),
        verbose_name="Mentions légales des devis PDF",
    )

    # Identifiants légaux : source UNIQUE pour le PDF, le pied de page et la page Contact
    ice = models.CharField(max_length=20, blank=True, default="002984125000084", verbose_name="ICE",
                           help_text="Identifiant Commun de l'Entreprise (15 chiffres)")
    identifiant_fiscal = models.CharField(max_length=20, blank=True, default="45982130",
                                          verbose_name="Identifiant Fiscal (IF)")
    rc = models.CharField(max_length=40, blank=True, default="Casablanca",
                          verbose_name="Registre de Commerce (RC)",
                          help_text="Ex : 123456 Casablanca")

    class Meta:
        verbose_name = "Paramètres de l'entreprise"
        verbose_name_plural = "Paramètres de l'entreprise"

    def __str__(self):
        return f"Paramètres — {self.nom_entreprise}"

    @property
    def mentions_identifiants(self):
        """« ICE : … — RC : … — IF : … » pour les seuls champs renseignés."""
        parts = [f"{lib} : {val}" for lib, val in
                 (("ICE", self.ice), ("RC", self.rc), ("IF", self.identifiant_fiscal)) if val]
        return " — ".join(parts)

    def clean(self):
        # Singleton : interdire la création d'un second enregistrement
        if not self.pk and Parametres.objects.exists():
            raise ValidationError(
                "Un seul enregistrement de paramètres est autorisé. "
                "Modifiez l'enregistrement existant."
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @classmethod
    def get(cls):
        """Retourne le singleton des paramètres (ou un objet par défaut)."""
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

