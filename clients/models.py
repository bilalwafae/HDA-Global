"""
Modèle Client : un visiteur devient automatiquement un client
lors de l'envoi de sa première demande de devis.
Déduplication par adresse email unique.
"""
from django.db import models


class Client(models.Model):
    """
    Représente un client de H.D.A GLOBAL.
    Créé automatiquement lors de la 1ère demande.
    Aucun mot de passe : l'accès se fait via un token UUID dans l'URL.
    """
    nom_complet = models.CharField(max_length=200, verbose_name="Nom complet")
    email = models.EmailField(unique=True, verbose_name="Email")
    telephone = models.CharField(max_length=20, verbose_name="Téléphone")
    ville = models.CharField(max_length=100, verbose_name="Ville de résidence")
    adresse_principale = models.TextField(
        blank=True,
        verbose_name="Adresse principale",
    )
    notes_admin = models.TextField(
        blank=True,
        verbose_name="Notes internes (admin uniquement)",
        help_text="Visible uniquement depuis le back-office",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Client depuis")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Dernière modification")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Client"
        verbose_name_plural = "Clients"

    def __str__(self):
        return f"{self.nom_complet} ({self.email})"

    def nb_demandes(self):
        """Nombre total de demandes passées."""
        return self.demandes.count()

    def derniere_demande(self):
        """La demande la plus récente du client."""
        return self.demandes.order_by("-created_at").first()

    @classmethod
    def get_or_create_from_form(cls, nom, email, telephone, ville, adresse=""):
        """
        Retrouve un client existant par email ou en crée un nouveau.
        Utilisé lors de la soumission du formulaire de demande.
        """
        client, created = cls.objects.get_or_create(
            email=email.lower().strip(),
            defaults={
                "nom_complet": nom.strip(),
                "telephone": telephone.strip(),
                "ville": ville.strip(),
                "adresse_principale": adresse.strip(),
            },
        )
        if not created:
            # Mettre à jour les infos de contact si le client revient
            updated = False
            if telephone and client.telephone != telephone.strip():
                client.telephone = telephone.strip()
                updated = True
            if ville and client.ville != ville.strip():
                client.ville = ville.strip()
                updated = True
            if updated:
                client.save()
        return client, created

