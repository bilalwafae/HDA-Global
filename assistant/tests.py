"""Tests de l'assistant : outils (chiffres exacts), garde-fous et boucle IA simulée (aucun appel réseau)."""
import json
from datetime import date
from decimal import Decimal
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from clients.models import Client
from demandes.models import Demande
from devis.models import Devis
from interventions.models import Intervention
from services.models import Service
from . import llm, outils


def _fabriquer():
    clim = Service.objects.create(nom="Climatisation & Ventilation", description_courte="x")
    cons = Service.objects.create(nom="Construction & Rénovation", description_courte="x")
    omar = Client.objects.create(nom_complet="Omar Benjelloun", email="omar@x.ma", telephone="1", ville="Casablanca")
    sara = Client.objects.create(nom_complet="Sara Alaoui", email="sara@x.ma", telephone="2", ville="Rabat")

    def dem(client, service, ville):
        return Demande.objects.create(client=client, service=service, ville_chantier=ville,
                                      adresse_chantier="adr", description_besoin="d")

    def inter(d, ville, debut, statut="terminee"):
        return Intervention.objects.create(demande=d, ville=ville, date_debut=debut, statut_chantier=statut,
                                           responsable_chantier="Chef")

    def devis(d, ht, statut="accepte", emis=date(2026, 3, 10)):
        dv = Devis.objects.create(demande=d, statut=statut, taux_tva=Decimal("20"))
        Devis.objects.filter(pk=dv.pk).update(sous_total_ht=Decimal(ht), montant_tva=Decimal(ht) * Decimal("0.2"),
                                              total_ttc=Decimal(ht) * Decimal("1.2"), date_emission=emis)
    d1, d2, d3, d4 = dem(omar, clim, "Casablanca"), dem(omar, cons, "Mohammédia"), dem(sara, clim, "Casablanca"), dem(sara, clim, "Rabat")
    inter(d1, "Casablanca", date(2026, 3, 5)); inter(d2, "Mohammédia", date(2026, 4, 1))
    inter(d3, "casablanca", date(2025, 12, 20), "en_cours"); inter(d4, "Rabat", date(2026, 5, 2), "planifiee")
    devis(d1, "1000"); devis(d2, "5000", emis=date(2026, 4, 2)); devis(d3, "2000"); devis(d4, "800", statut="envoye")


class OutilsTests(TestCase):
    def setUp(self):
        _fabriquer()

    def test_par_ville_insensible_casse_et_accents(self):
        r = outils.interventions_par_ville()
        self.assertEqual(r["total_interventions"], 4)
        self.assertEqual({l["ville"].lower(): l["nombre"] for l in r["par_ville"]}["casablanca"], 2)

    def test_ville_avec_periode(self):
        r = outils.interventions_d_une_ville("mohammedia", "2026-01-01", "2026-12-31")
        self.assertEqual(r["nombre_interventions"], 1)
        r = outils.interventions_d_une_ville("Casablanca", "2026-01-01", "2026-12-31")
        self.assertEqual(r["nombre_interventions"], 1)  # celle de décembre 2025 est exclue

    def test_client(self):
        r = outils.activite_client("omar")
        self.assertEqual(r["nombre_interventions"], 2)
        self.assertEqual(r["nombre_devis_acceptes"], 2)
        self.assertEqual(r["montant_devis_acceptes_ttc"], "7 200,00 MAD")
        self.assertFalse(outils.activite_client("inconnu zzz")["trouve"])

    def test_client_ambigu(self):
        Client.objects.create(nom_complet="Omar Tazi", email="ot@x.ma", telephone="3", ville="Fès")
        r = outils.activite_client("omar")
        self.assertTrue(r["ambigu"])

    def test_classement_services(self):
        r = outils.classement_services()
        self.assertEqual(r["service_le_plus_demande"], ["Climatisation & Ventilation"])
        self.assertEqual(r["service_le_plus_rentable_ttc"], ["Construction & Rénovation"])
        clim = next(s for s in r["services"] if s["service"].startswith("Clim"))
        self.assertEqual((clim["nombre_demandes"], clim["devis_acceptes"]), (3, 2))
        self.assertEqual(clim["chiffre_affaires_ttc"], "3 600,00 MAD")  # 1000+2000 HT -> 3600 TTC ; devis « envoyé » exclu

    def test_chiffre_affaires_par_mois_et_periode(self):
        r = outils.chiffre_affaires("2026-04-01", "2026-04-30")
        self.assertEqual(r["total_ttc"], "6 000,00 MAD")
        r = outils.chiffre_affaires(regrouper_par="mois")
        self.assertEqual([l["groupe"] for l in r["lignes"]], ["2026-03", "2026-04"])

    def test_erreurs_lisibles(self):
        self.assertIn("erreur", outils.executer("interventions_par_ville", {"date_debut": "hier"}))
        self.assertIn("erreur", outils.executer("outil_inconnu", {}))
        self.assertIn("erreur", outils.executer("interventions_par_ville", {"statut": "nimporte"}))
        self.assertIn("erreur", outils.executer("interventions_par_ville", {"date_debut": "2026-05-01", "date_fin": "2026-01-01"}))

    def test_rechercher_demande(self):
        r = outils.rechercher_demande("sara")
        self.assertEqual(r["nombre_resultats"], 2)


class VerificationNombresTests(TestCase):
    donnees = json.dumps({"total_interventions": 4, "total_ttc": "12 345,60 MAD", "date": "05/03/2026"})

    def test_nombres_corrects(self):
        self.assertEqual(llm.nombres_non_verifies("4 interventions pour 12 345,60 MAD le 05/03/2026.", self.donnees), [])

    def test_nombre_invente(self):
        self.assertEqual(llm.nombres_non_verifies("Il y a 7 interventions.", self.donnees), ["7"])

    def test_puces_ignorees(self):
        self.assertEqual(llm.nombres_non_verifies("1. Casablanca : 4\n2. Rabat : 4", self.donnees), [])


@override_settings(OPENROUTER_API_KEY="cle-test", OPENROUTER_MODELS="m1,m2", ASSISTANT_ENABLED=True)
class BoucleIATests(TestCase):
    def setUp(self):
        _fabriquer()

    @staticmethod
    def _tool_call(nom, args):
        return {"model": "m1", "choices": [{"message": {"content": None, "tool_calls": [
            {"id": "c1", "type": "function", "function": {"name": nom, "arguments": json.dumps(args)}}]}}]}

    @staticmethod
    def _texte(t):
        return {"model": "m1", "choices": [{"message": {"content": t}}]}

    def test_reponse_exacte(self):
        seq = [self._tool_call("interventions_d_une_ville", {"ville": "Casablanca", "date_debut": "2026-01-01", "date_fin": "2026-12-31"}),
               self._texte("**1** intervention à Casablanca en 2026.")]
        with mock.patch.object(llm, "_appel", side_effect=seq):
            r = llm.repondre("Combien d'interventions à Casablanca en 2026 ?")
        self.assertEqual(r["source"], "ia")
        self.assertEqual(r["outils"], ["interventions_d_une_ville"])

    def test_nombre_halluciné_remplace_par_donnees(self):
        seq = [self._tool_call("interventions_par_ville", {}), self._texte("Il y a 99 interventions au total.")]
        with mock.patch.object(llm, "_appel", side_effect=seq):
            r = llm.repondre("Interventions par ville ?")
        self.assertEqual(r["source"], "donnees")
        self.assertNotIn("99", r["reponse"])
        self.assertIn("Casablanca", r["reponse"])

    def test_hors_sujet_sans_outil_avec_chiffres_refuse(self):
        with mock.patch.object(llm, "_appel", return_value=self._texte("La capitale de la France a 2 millions d'habitants.")):
            r = llm.repondre("Parle-moi de Paris")
        self.assertEqual(r["source"], "refus")
        self.assertEqual(r["reponse"], llm.REFUS)

    def test_bascule_sur_modele_suivant(self):
        import urllib.error
        err = urllib.error.HTTPError("u", 429, "rate", {}, None)
        with mock.patch.object(llm, "_appel", side_effect=[err, self._texte(llm.REFUS)]):
            r = llm.repondre("blague ?")
        self.assertEqual(r["source"], "refus")

    @override_settings(OPENROUTER_API_KEY="")
    def test_sans_cle_pas_de_crash(self):
        self.assertEqual(llm.repondre("bonjour")["source"], "refus")   # salutation, pas de crash
        self.assertEqual(llm.question_rapide("services")["source"], "donnees")

    def test_panne_totale_message_clair(self):
        with mock.patch.object(llm, "_appel", side_effect=OSError("réseau")):
            r = llm.repondre("Combien de demandes ?")
        self.assertEqual(r["source"], "donnees")   # le routeur interroge la base malgré la panne de l'IA
        self.assertIn("4", r["reponse"])           # 4 demandes dans la base de test


@override_settings(OPENROUTER_API_KEY="")
class VuesTests(TestCase):
    def test_acces_reserve_au_staff(self):
        self.assertEqual(self.client.get(reverse("assistant:chat")).status_code, 302)
        self.assertEqual(self.client.post(reverse("assistant:poser"), "{}", content_type="application/json").status_code, 302)

    def test_chat_et_question_rapide(self):
        _fabriquer()
        u = get_user_model().objects.create_superuser("a", "a@a.ma", "pw"); self.client.force_login(u)
        r = self.client.get(reverse("assistant:chat")); self.assertContains(r, "Assistant IA")
        r = self.client.post(reverse("assistant:poser"), json.dumps({"rapide": "villes_annee"}), content_type="application/json")
        self.assertEqual(r.status_code, 200); self.assertEqual(r.json()["source"], "donnees")


@override_settings(OPENROUTER_API_KEY="cle-test", OPENROUTER_MODELS="m1", ASSISTANT_ENABLED=True)
class QuestionsLibresTests(TestCase):
    """Questions écrites librement : la base est TOUJOURS interrogée, le hors sujet est refusé."""

    def setUp(self):
        _fabriquer()

    def test_question_libre_sans_ia(self):
        with override_settings(OPENROUTER_API_KEY=""):
            r = llm.repondre("Combien d'interventions à Casablanca en 2026 ?")
        self.assertEqual(r["source"], "donnees")
        self.assertEqual(r["outils"], ["interventions_d_une_ville"])
        self.assertIn("1", r["reponse"])

    def test_modele_qui_ne_consulte_pas_la_base_est_corrige(self):
        faux = {"model": "m1", "choices": [{"message": {"content": "Il y a environ 12 chantiers."}}]}
        with mock.patch.object(llm, "_appel", return_value=faux):
            r = llm.repondre("combien d'interventions à Rabat ?")
        self.assertEqual(r["source"], "donnees")
        self.assertNotIn("12", r["reponse"])

    def test_refus_a_tort_du_modele_est_corrige(self):
        refus = {"model": "m1", "choices": [{"message": {"content": llm.REFUS}}]}
        with mock.patch.object(llm, "_appel", return_value=refus):
            r = llm.repondre("Quel est le chiffre d'affaires par mois ?")
        self.assertEqual(r["source"], "donnees")
        self.assertEqual(r["outils"], ["chiffre_affaires"])

    def test_hors_sujet_refuse_sans_appeler_le_modele(self):
        with mock.patch.object(llm, "_appel") as appel:
            for q in ("Quelle est la capitale de la France ?", "écris-moi un poème", "combien font 2+2 ?",
                      "Qui est le président des États-Unis ?"):
                self.assertEqual(llm.repondre(q)["source"], "refus", q)
        appel.assert_not_called()

    def test_client_cite_par_son_nom(self):
        with override_settings(OPENROUTER_API_KEY=""):
            r = llm.repondre("Que rapporte Omar Benjelloun ?")
        self.assertEqual(r["outils"], ["activite_client"])

    def test_classement_et_ca_par_service(self):
        with override_settings(OPENROUTER_API_KEY=""):
            self.assertEqual(llm.repondre("quel est le service le plus demandé ?")["outils"], ["classement_services"])
            self.assertEqual(llm.repondre("chiffre d'affaires par service")["outils"], ["chiffre_affaires"])
            self.assertEqual(llm.repondre("combien de demandes par statut ?")["outils"], ["statistiques_demandes"])
