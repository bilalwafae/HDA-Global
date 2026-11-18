from django.test import TestCase
from django.utils import timezone
from clients.models import Client
from services.models import Service
from demandes.models import Demande, HistoriqueStatut


class DemandeWorkflowTests(TestCase):
    """Tests unitaires sur la numérotation des demandes et les transitions de statut."""

    def setUp(self):
        self.client_obj = Client.objects.create(
            nom_complet="Fatima Zahra",
            email="fz@test.ma",
            telephone="+212612345678",
            ville="Beni Yakhlef",
        )
        self.service = Service.objects.create(
            nom="Plomberie",
            slug="plomberie-test",
            description_courte="Plomberie desc",
            description_complete="Plomberie long desc",
        )

    def test_generation_reference_automatique(self):
        """Vérifie la génération séquentielle de référence DEM-2026-0001."""
        d1 = Demande.objects.create(
            client=self.client_obj,
            service=self.service,
            ville_chantier="Mohammedia",
            adresse_chantier="Rue 1, Beni Yakhlef",
            description_besoin="Fuite d'eau importante",
        )
        annee = timezone.now().year
        self.assertTrue(d1.reference.startswith(f"DEM-{annee}-"))
        self.assertIsNotNone(d1.token_suivi)

    def test_changement_statut_et_historique(self):
        """Vérifie que changer de statut crée un enregistrement d'HistoriqueStatut."""
        d = Demande.objects.create(
            client=self.client_obj,
            service=self.service,
            ville_chantier="Mohammedia",
            adresse_chantier="Rue 1, Beni Yakhlef",
            description_besoin="Projet rénovation",
        )
        self.assertEqual(d.statut, Demande.STATUT_NOUVELLE)

        # Transition vers en_etude
        succes = d.changer_statut(
            Demande.STATUT_EN_ETUDE,
            auteur="Admin BTP",
            commentaire="Prise en charge par l'ingénieur",
        )
        self.assertTrue(succes)
        self.assertEqual(d.statut, Demande.STATUT_EN_ETUDE)

        # Vérifier l'historique
        self.assertEqual(d.historique.count(), 1)
        hist = d.historique.first()
        self.assertEqual(hist.ancien_statut, Demande.STATUT_NOUVELLE)
        self.assertEqual(hist.nouveau_statut, Demande.STATUT_EN_ETUDE)
        self.assertEqual(hist.auteur, "Admin BTP")




from datetime import timedelta
from django.core.cache import cache
from django.test import override_settings
from django.utils import timezone


class SecuriteSuiviTests(TestCase):
    """Portail client à lien secret : une seule demande, expiration, limite de débit, en-têtes."""

    def setUp(self):
        cache.clear()
        c = Client.objects.create(nom_complet="Test", email="t@test.ma", telephone="+212600000000", ville="Mohammedia")
        s = Service.objects.create(nom="S", slug="s-sec", description_courte="a", description_complete="b")
        self.d1 = Demande.objects.create(client=c, service=s, ville_chantier="Mohammedia", adresse_chantier="Rue 1", description_besoin="Peinture")
        self.d2 = Demande.objects.create(client=c, service=s, ville_chantier="Rabat", adresse_chantier="Rue 2", description_besoin="Sol")

    def test_ne_montre_que_sa_demande(self):
        r = self.client.get(f"/suivi/{self.d1.token_suivi}/")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, self.d1.reference)
        self.assertNotContains(r, str(self.d2.token_suivi))
        self.assertNotIn("toutes_demandes", r.context)

    def test_en_tetes_de_securite(self):
        r = self.client.get(f"/suivi/{self.d1.token_suivi}/")
        self.assertEqual(r["Referrer-Policy"], "no-referrer")
        self.assertIn("noindex", r["X-Robots-Tag"])
        self.assertIn("no-store", r["Cache-Control"])

    def test_lien_expire_apres_inactivite(self):
        Demande.objects.filter(pk=self.d1.pk).update(updated_at=timezone.now() - timedelta(days=120))
        r = self.client.get(f"/suivi/{self.d1.token_suivi}/")
        self.assertEqual(r.status_code, 410)

    @override_settings(SUIVI_VALIDITE_JOURS=0)
    def test_expiration_desactivable(self):
        Demande.objects.filter(pk=self.d1.pk).update(updated_at=timezone.now() - timedelta(days=500))
        self.assertEqual(self.client.get(f"/suivi/{self.d1.token_suivi}/").status_code, 200)

    def test_le_personnel_connecte_n_est_pas_bloque(self):
        from django.contrib.auth import get_user_model
        u = get_user_model().objects.create_user("adm", password="x", is_staff=True)
        self.client.force_login(u)
        Demande.objects.filter(pk=self.d1.pk).update(updated_at=timezone.now() - timedelta(days=400))
        self.assertEqual(self.client.get(f"/suivi/{self.d1.token_suivi}/").status_code, 200)

    @override_settings(SUIVI_LIMITE_PAR_MINUTE=3)
    def test_limite_de_requetes(self):
        codes = [self.client.get(f"/suivi/{self.d1.token_suivi}/").status_code for _ in range(5)]
        self.assertEqual(codes[:3], [200, 200, 200])
        self.assertEqual(codes[3], 429)

    def test_jeton_inconnu_404(self):
        import uuid
        self.assertEqual(self.client.get(f"/suivi/{uuid.uuid4()}/").status_code, 404)
