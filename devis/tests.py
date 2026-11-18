from decimal import Decimal
from django.test import TestCase

from clients.models import Client
from services.models import Service
from demandes.models import Demande
from devis.models import Devis, LigneDevis
from devis.pricing import arrondir_monnaie, calculer_total_ligne, recalculer_devis


class PricingEngineTests(TestCase):
    """Tests unitaires du moteur de calcul financier déterministe (pricing.py)."""

    def setUp(self):
        self.client_obj = Client.objects.create(
            nom_complet="Test Client",
            email="test@client.ma",
            telephone="+212600000000",
            ville="Casablanca",
        )
        self.service = Service.objects.create(
            nom="Rénovation",
            slug="renovation-test",
            description_courte="Test desc",
            description_complete="Test long desc",
        )
        self.demande = Demande.objects.create(
            client=self.client_obj,
            service=self.service,
            ville_chantier="Casablanca",
            adresse_chantier="Test address",
            description_besoin="Besoin test",
        )
        self.devis = Devis.objects.create(
            demande=self.demande,
            taux_tva=Decimal("20.00"),
        )

    def test_arrondi_monnaie(self):
        """Vérifie l'arrondi ROUND_HALF_UP à 2 décimales."""
        self.assertEqual(arrondir_monnaie("12.345"), Decimal("12.35"))
        self.assertEqual(arrondir_monnaie("12.344"), Decimal("12.34"))
        self.assertEqual(arrondir_monnaie(Decimal("100.00")), Decimal("100.00"))

    def test_calculer_total_ligne(self):
        """Vérifie le calcul unitaire Quantité × P.U. HT."""
        # 10 m² à 150.50 MAD = 1505.00 MAD
        total = calculer_total_ligne(Decimal("10.00"), Decimal("150.50"))
        self.assertEqual(total, Decimal("1505.00"))

    def test_recalculer_devis_complet(self):
        """
        Vérifie le calcul complet du devis :
        Ligne 1 : 10 m² × 100.00 MAD = 1000.00 MAD
        Ligne 2 : 5 unités × 200.00 MAD = 1000.00 MAD
        Sous-total HT = 2000.00 MAD
        TVA 20% = 400.00 MAD
        Total TTC = 2400.00 MAD
        """
        LigneDevis.objects.create(
            devis=self.devis,
            designation="Travaux 1",
            quantite=Decimal("10.00"),
            unite="m²",
            prix_unitaire_ht=Decimal("100.00"),
        )
        LigneDevis.objects.create(
            devis=self.devis,
            designation="Travaux 2",
            quantite=Decimal("5.00"),
            unite="unité",
            prix_unitaire_ht=Decimal("200.00"),
        )

        recalculer_devis(self.devis)

        self.assertEqual(self.devis.sous_total_ht, Decimal("2000.00"))
        self.assertEqual(self.devis.montant_tva, Decimal("400.00"))
        self.assertEqual(self.devis.total_ttc, Decimal("2400.00"))

