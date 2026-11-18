from django.test import TestCase
from clients.models import Client


class ClientAutoCreationTests(TestCase):
    """Tests unitaires sur la création automatique et déduplication des clients."""

    def test_creation_nouveau_client(self):
        """Un visiteur inconnu est enregistré comme nouveau client."""
        client, created = Client.get_or_create_from_form(
            nom="Karim Tazi",
            email="karim.tazi@example.ma",
            telephone="+212611223344",
            ville="Mohammedia",
            adresse="Quartier Wafa, Mohammedia",
        )
        self.assertTrue(created)
        self.assertEqual(client.nom_complet, "Karim Tazi")
        self.assertEqual(client.email, "karim.tazi@example.ma")
        self.assertEqual(client.ville, "Mohammedia")

    def test_deduplication_client_existant(self):
        """Si l'email existe déjà, le client existant est réutilisé et mis à jour."""
        c1, created1 = Client.get_or_create_from_form(
            nom="Karim Tazi",
            email="karim.tazi@example.ma",
            telephone="+212611223344",
            ville="Mohammedia",
        )
        self.assertTrue(created1)

        # Seconde demande avec même email mais nouveau numéro
        c2, created2 = Client.get_or_create_from_form(
            nom="Karim Tazi",
            email="KARIM.TAZI@EXAMPLE.MA",  # Majuscules
            telephone="+212699887766",
            ville="Casablanca",
        )
        self.assertFalse(created2)
        self.assertEqual(c1.pk, c2.pk)
        self.assertEqual(c2.telephone, "+212699887766")
        self.assertEqual(c2.ville, "Casablanca")
        self.assertEqual(Client.objects.count(), 1)

