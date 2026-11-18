"""Tests du flux : statut « Acceptée » → devis auto → envoi au client (PDF joint)."""
from unittest import mock

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from clients.models import Client
from demandes.models import Demande
from services.models import Service
from .models import Devis


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
                   DEVIS_AUTO_A_L_ACCEPTATION=True)
class FluxAcceptationTests(TestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_superuser("adm", "a@a.ma", "pw")
        self.client.force_login(self.admin)
        svc = Service.objects.create(nom="Climatisation & Ventilation", description_courte="x")
        cli = Client.objects.create(nom_complet="Test Perso", email="perso@example.com",
                                    telephone="+212600000000", ville="Casablanca")
        self.demande = Demande.objects.create(
            client=cli, service=svc, ville_chantier="Casablanca", adresse_chantier="Maarif",
            surface_m2=85, description_besoin="Climatisation appartement 85 m2")

    def _accepter_via_admin(self):
        url = reverse("admin:demandes_demande_change", args=[self.demande.pk])
        data = {
            "statut": "acceptee", "client": self.demande.client_id, "service": self.demande.service_id,
            "ville_chantier": "Casablanca", "adresse_chantier": "Maarif", "surface_m2": "85",
            "description_besoin": "Climatisation appartement 85 m2", "notes_internes": "",
            "pieces_jointes-TOTAL_FORMS": 0, "pieces_jointes-INITIAL_FORMS": 0,
            "pieces_jointes-MIN_NUM_FORMS": 0, "pieces_jointes-MAX_NUM_FORMS": 1000,
            "historique-TOTAL_FORMS": 0, "historique-INITIAL_FORMS": 0,
            "historique-MIN_NUM_FORMS": 0, "historique-MAX_NUM_FORMS": 1000,
        }
        return self.client.post(url, data, follow=True)

    def test_acceptation_genere_devis_brouillon_avec_pdf_sans_envoyer(self):
        # le formulaire admin a des préfixes d'inlines variables : on passe par changer_statut,
        # exactement ce que fait l'action groupée et le portail
        self.demande.changer_statut("acceptee", auteur="adm")
        devis = Devis.objects.get(demande=self.demande)
        self.assertEqual(devis.statut, Devis.STATUT_BROUILLON)
        self.assertTrue(devis.lignes.exists())
        self.assertTrue(devis.fichier_pdf)
        self.assertEqual(len(mail.outbox), 0)          # rien ne part tout seul
        # idempotent
        self.demande.changer_statut("planifiee"); self.demande.changer_statut("acceptee")
        self.assertEqual(Devis.objects.filter(demande=self.demande).count(), 1)

    def test_action_admin_groupee(self):
        url = reverse("admin:demandes_demande_changelist")
        r = self.client.post(url, {"action": "accepter_et_generer_devis",
                                   "_selected_action": [self.demande.pk]}, follow=True)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Devis.objects.filter(demande=self.demande).count(), 1)
        self.assertContains(r, "Envoyer au client")

    def test_envoi_au_client_avec_pdf_joint(self):
        self.demande.changer_statut("acceptee", auteur="adm")
        devis = Devis.objects.get(demande=self.demande)
        r = self.client.post(reverse("devis:editer", args=[devis.pk]), {"action": "envoyer_client"})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)
        m = mail.outbox[0]
        self.assertEqual(m.to, ["perso@example.com"])
        noms = [a[0] if isinstance(a, tuple) else a.get_filename() for a in m.attachments]
        self.assertIn(f"Devis_{devis.numero}.pdf", noms)
        pdf = [a for a in m.attachments if isinstance(a, tuple)][0][1]
        self.assertTrue(pdf.startswith(b"%PDF"))
        self.assertTrue(any(not isinstance(a, tuple) and a["Content-ID"] == "<logo_hda>" for a in m.attachments))
        self.assertIn("text/html", m.alternatives[0][1])
        devis.refresh_from_db(); self.demande.refresh_from_db()
        self.assertEqual(devis.statut, Devis.STATUT_ENVOYE)
        self.assertEqual(self.demande.statut, "devis_envoye")

    def test_echec_smtp_ne_change_pas_le_statut(self):
        self.demande.changer_statut("acceptee", auteur="adm")
        devis = Devis.objects.get(demande=self.demande)
        with mock.patch("django.core.mail.EmailMultiAlternatives.send", side_effect=OSError("SMTP KO")):
            r = self.client.post(reverse("devis:editer", args=[devis.pk]),
                                 {"action": "envoyer_client"}, follow=True)
        self.assertContains(r, "PAS été envoyé")
        devis.refresh_from_db()
        self.assertEqual(devis.statut, Devis.STATUT_BROUILLON)
