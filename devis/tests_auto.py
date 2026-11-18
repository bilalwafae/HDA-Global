"""
Tests du moteur de devis automatique (devis/auto.py, ai.py, pdf.py, pricing.py).

Tests UNITAIRES PURS : aucune base de données, aucun accès réseau, aucun
appel à l'API IA (on valide la sortie SANS IA : le repli local fonctionne).
"""
from decimal import Decimal
from unittest import TestCase

from devis import ai, auto as moteur, vision
from devis.pdf import (
    construire_pdf, montant_en_lettres, filtrer_notes_client,
    fmt_mad, charger_polices,
)
from devis.pricing import calculer_totaux


def _propose(service_nom, ville, surface, description, ia=None):
    return moteur.proposer_devis(
        service_nom=service_nom,
        ville=ville,
        surface_saisie=surface,
        description=description,
        resultat_ia=ia,
    )


class DetectionFamilleTests(TestCase):
    """test_coherence_catalogue + détection de famille."""

    def test_detection_famille_par_service(self):
        cas = [
            ("Climatisation et ventilation", "climatisation"),
            ("Plomberie générale", "plomberie"),
            ("Aménagement intérieur et extérieur", "amenagement"),
            ("Gestion de projets TCE", "gestion_tce"),
            ("Construction & rénovation", "construction_renovation"),
            ("Services divers sur mesure", "divers"),
        ]
        for nom_service, famille_attendue in cas:
            self.assertEqual(
                moteur.detecter_famille(nom_service, "description longue libre"),
                famille_attendue,
                f"Échec pour le service « {nom_service} »",
            )

    def test_detection_famille_par_description(self):
        # service inconnu : la description tranche
        self.assertEqual(
            moteur.detecter_famille("Autre", "je veux une clim inverter pour le salon"),
            "climatisation",
        )
        self.assertEqual(
            moteur.detecter_famille(None, "fuite d'eau sous l'évier, réparation urgente"),
            "plomberie",
        )
        self.assertEqual(
            moteur.detecter_famille("", "faux plafond suspendu chambre"),
            "amenagement",
        )

    def test_coherence_catalogue_formules(self):
        """Chaque code des FORMULES existe au CATALOGUE ; prix > 0 ; modes connus."""
        for famille, codes in moteur.FORMULES.items():
            self.assertTrue(codes, f"Formule vide pour {famille}")
            for code in codes:
                self.assertIn(code, moteur.CATALOGUE, f"Code inconnu : {code}")
                poste = moteur.CATALOGUE[code]
                self.assertGreater(poste.prix_unitaire_ht, Decimal("0.00"))
                self.assertIn(poste.mode, ("surface", "forfait"))
        # le poste déplacement n'est PAS dans les formules (ajout moteur seul)
        for codes in moteur.FORMULES.values():
            self.assertNotIn(moteur.CODE_DEPLACEMENT, codes)


class TotauxDeterministesTests(TestCase):
    """Chiffrage 85 m² de climatisation à Casablanca : 37 200 HT / 7 440 TVA / 44 640 TTC."""

    def test_totaux_deterministes_85m2_climatisation_casablanca(self):
        prop = _propose(
            service_nom="Climatisation et ventilation",
            ville="Casablanca",
            surface=Decimal("85.00"),
            description="Un salon et deux chambres, appartement de 85 m2",
        )
        self.assertEqual(prop.totaux["sous_total_ht"], Decimal("37200.00"))
        self.assertEqual(prop.totaux["montant_tva"], Decimal("7440.00"))
        self.assertEqual(prop.totaux["total_ttc"], Decimal("44640.00"))

    def test_totaux_via_pricing_pur(self):
        """calculer_totaux accepte tuples > dict > objets, toujours Decimal."""
        resultat = calculer_totaux(
            [(Decimal("85.00"), Decimal("320.00")), (Decimal("1.00"), Decimal("10000.00"))],
            Decimal("20.00"),
        )
        self.assertEqual(resultat["sous_total_ht"], Decimal("37200.00"))
        self.assertEqual(resultat["montant_tva"], Decimal("7440.00"))
        self.assertEqual(resultat["total_ttc"], Decimal("44640.00"))


class ReglesMoteurTests(TestCase):
    """Surface manquante, déplacement hors zone, ville « Autre »."""

    def test_surface_manquante_confiance_faible(self):
        prop = _propose(
            service_nom="Climatisation et ventilation",
            ville="Casablanca",
            surface=None,
            description="Pas de surface dans le message client",
        )
        self.assertEqual(prop.confiance, "faible")
        self.assertTrue(any("Surface" in a for a in prop.alertes))
        for ligne in prop.lignes:
            if ligne.code == "CLIM-SPL":
                self.assertEqual(ligne.quantite, Decimal("1.00"))

    def test_extraction_surface_proposition_confiance(self):
        """Regex : « 85 m2 » extrait de la description → alerte confirmation."""
        prop = _propose(
            service_nom="Autre", ville="Casablanca", surface=None,
            description="mon Appart de 85 m2 à équiper srte vpl",
        )
        self.assertEqual(prop.surface_utilisee, Decimal("85"))
        self.assertTrue(any("Surface extraite" in a for a in prop.alertes))

    def test_frais_deplacement_hors_zone(self):
        prop = _propose(
            service_nom="Aménagement intérieur et extérieur",
            ville="Rabat",
            surface=Decimal("60.00"),
            description="aménagement complet du bureau, deux pièces",
        )
        codes = [l.code for l in prop.lignes]
        self.assertIn("DEP-VILLE", codes)
        self.assertTrue(any("déplacement" in a for a in prop.alertes))

    def test_ville_autre_confiance_faible(self):
        prop = _propose(
            service_nom="Plomberie générale", ville="",
            surface=Decimal("50.00"), description="rénovation complète salle de bain douche wc",
        )
        self.assertEqual(prop.confiance, "faible")
        self.assertTrue(any("Ville" in a for a in prop.alertes))


class ValidationIATests(TestCase):
    """L'IA ne peut NI fixer un prix, NI injecter un poste inconnu, NI casser le flux."""

    def test_ia_ne_peut_pas_injecter_prix_ni_poste_inconnu(self):
        sortie_ia = {
            "surface_m2": "60",
            "postes": ["CLIM-SPL", "CODE-INCONNU", "DEP-VILLE", "CLIM-INS"],
            "resume": "climatisation 60 m2",
            "urgence": "haute",
            "questions": ["Combien de pièces ?", "Accès ascenseur ?"],
            # TENTATIVE d'injection de prix — doit être ignorée :
            "prix_unitaire_ht": "999999.00",
            "tot_aux": {"sous_total": "1"},
        }
        valide = ai.analyser_reponse_json(__import__("json").dumps(sortie_ia))
        self.assertNotIn("prix_unitaire_ht", valide)
        self.assertNotIn("tot_aux", valide)
        self.assertNotIn("CODE-INCONNU", valide.get("postes", []))
        self.assertNotIn("DEP-VILLE", valide.get("postes", []))
        self.assertEqual(valide["postes"], ["CLIM-SPL", "CLIM-INS"])

        # Les PRIX restent ceux du catalogue :
        prop = _propose(
            service_nom="Climatisation et ventilation", ville="Casablanca",
            surface=Decimal("60.00"), description="climatisation 60 m2",
            ia=valide,
        )
        for ligne in prop.lignes:
            if ligne.code in moteur.CATALOGUE:
                self.assertEqual(
                    ligne.prix_unitaire_ht, moteur.CATALOGUE[ligne.code].prix_unitaire_ht
                )

    def test_json_invalide_sans_effet(self):
        self.assertEqual(ai.analyser_reponse_json("ceci n'est pas du json"), {})
        self.assertEqual(ai.analyser_reponse_json("{question mal fermée :"), {})
        # L'IA entourée de texte : l'objet est quand même extrait
        resultat = ai.analyser_reponse_json('Parfait ! {"resume": "ok", "asc": 1} Voilà.')
        self.assertEqual(resultat["resume"], "ok")

    def test_extraction_surface_regex(self):
        # « 85 m2 » principal + terrasse 12,5 m² : on garde la plus grande
        self.assertEqual(
            ai.extraire_surface_regex("appartement 85 m2 avec terrasse de 12,5 m²"),
            Decimal("85"),
        )
        self.assertEqual(ai.extraire_surface_regex("90 M2"), Decimal("90"))
        self.assertIsNone(ai.extraire_surface_regex("aucune surface ici"))
        self.assertIsNone(ai.extraire_surface_regex(""))

    def test_postes_ia_utilises(self):
        ia = {"postes": ["PAINT", "CLEAN"], "resume": ""}  # codes inexistants
        prop = _propose(
            service_nom="Plomberie générale", ville="Mohammedia",
            surface=Decimal("30.00"), description="rénovation plomberie sanitaire wc",
            ia=ia,
        )
        # codes IA invalides → formule de la famille
        codes = [l.code for l in prop.lignes]
        self.assertEqual(codes, moteur.FORMULES["plomberie"])

        ia2 = {"postes": ["PLB-RED", "PLB-THE"], "resume": "service plomberie"}
        prop2 = _propose(
            service_nom="Plomberie générale", ville="Mohammedia",
            surface=Decimal("30.00"), description="rénovation plomberie sanitaire wc",
            ia=ai.analyser_reponse_json(__import__("json").dumps(ia2)),
        )
        codes2 = [l.code for l in prop2.lignes]
        self.assertEqual(codes2, ["PLB-RED", "PLB-THE"])  # postes IA conservés


class MontantEnLettresTests(TestCase):
    """montant_en_lettres : 80 000 → quatre-vingt mille, 200 → deux cents, etc."""

    def test_exemples_recap(self):
        self.assertEqual(
            montant_en_lettres(Decimal("80000.00")),
            "quatre-vingt mille dirhams (arrêté)",
        )
        self.assertEqual(
            montant_en_lettres(Decimal("200.00")),
            "deux cents dirhams (arrêté)",
        )
        self.assertEqual(
            montant_en_lettres(Decimal("1000000.00")),
            "un million de dirhams (arrêté)",
        )

    def test_autres_montants_en_lettres(self):
        # 1 200 000 : million SANS « de » (du chiffre suit)
        self.assertTrue(
            montant_en_lettres(Decimal("1200000.00")).startswith("un million deux cents mille dirhams")
        )
        # centimes
        self.assertTrue(
            montant_en_lettres(Decimal("44640.50")).endswith("et cinquante centimes (arrêté)")
        )
        # 100 000 → « cent mille »
        self.assertTrue(
            montant_en_lettres(Decimal("100000.00")).startswith("cent mille dirhams")
        )


class PDFTests(TestCase):
    """construire_pdf : fonction pure, marche sans base ni Django."""

    def _data(self):
        return {
            "emetteur": {
                "nom": "H.D.A GLOBAL SARL",
                "marque": "H.D.A GLOBAL – Construction TCE – Aménagement",
                "adresses": ["Beni Yakhlef, Mohammedia", ""],
                "telephone": "+212 661103988",
                "email": "hda.global82@gmail.com",
                "pied_legal": "Mentions légales de test",
            },
            "devis": {
                "numero": "DEV-2026-0001",
                "objet": "Prestation Climatisation",
                "taux_tva": "20",
                "date_validite": "31/12/2026",
            },
            "client": {
                "nom": "Client Test",
                "telephone": "+212600000000",
                "email": "client@test.ma",
                "ville": "Casablanca",
            },
            "chantier": {
                "reference": "DEM-2026-0001",
                "ville": "Casablanca",
                "adresse": "12 rue Test",
            },
            "lignes": [
                {
                    "n": 1,
                    "designation": "Climatisation (fourniture, pose et raccordements) m² sup",
                    "quantite": "85,00",
                    "unite": "m²",
                    "pu": "320,00",
                    "total": "27 200,00",
                },
            ],
            "totaux": {
                "sous_total_ht": "27 200,00",
                "montant_tva": "5 440,00",
                "total_ttc": "32 640,00",
            },
            "montant_lettres": montant_en_lettres(Decimal("32640.00")),
            "conditions": "30% à la commande, 70% à la livraison.",
            "url_suivi": "http://localhost:8000/suivi/00000000-0000-0000-0000-000000000000/",
            "logo_path": None,
            "polices_dir": None,  # Helvetica en repli
        }

    def test_construire_pdf_pur(self):
        data = self._data()
        pdf_bytes = construire_pdf(data)
        self.assertTrue(pdf_bytes.startswith(b"%PDF-"))
        self.assertGreater(len(pdf_bytes), 2000)

    def test_construire_pdf_avec_logo_inexistant_ne_crash_pas(self):
        data = self._data()
        data["logo_path"] = "/dev/inexistant/logo.png"
        pdf_bytes = construire_pdf(data)
        self.assertTrue(pdf_bytes.startswith(b"%PDF-"))


class VisionPhotoTests(TestCase):
    """Extension photos + vision : validation stricte, jamais de prix, jamais bloquante."""

    def test_vision_valide_sortie_et_borne(self):
        sortie = {
            "observations": "salle de bain vétuste, traces d'humidité " * 50,
            "indices": ["placard encastré", "aucun circuit gainable visible"],
            "questions": ["Accès par ascenseur ?", "Hauteur sous plafond ?"],
            # tentative d'injection de prix — ignorée :
            "prix": "5000",
            "montant_ttc": "999",
            "devis_propose": "abcd",
        }
        valide = vision.valider_reponse_vision(sortie)
        self.assertFalse(any(k for k in valide if "prix" in k.lower() or "montant" in k.lower()))
        self.assertNotIn("devis_propose", valide)
        self.assertIn("observations", valide)
        self.assertLessEqual(len(valide["observations"]), 380)
        self.assertEqual(len(valide["indices"]), 2)

    def test_vision_sortie_invalide(self):
        self.assertEqual(vision.valider_reponse_vision("texte brut"), {})
        self.assertEqual(vision.valider_reponse_vision(None), {})
        self.assertEqual(vision.valider_reponse_vision({"indice_extravagant"} - set()), {})
        self.assertEqual(vision.valider_reponse_vision({}), {})

    def test_fusion_vision_dans_resultat_ia(self):
        base = {"resume": "climatisation salon", "postes": ["CLIM-SPL"]}
        analyse = {
            "observations": "un seul mur libre pour l'unité extérieure",
            "indices": ["fenêtre côté rue : bruit, prudence niveau"],
            "questions": ["Combien de pièces ?"],
        }
        fusionne = vision.fusionner_dans_resultat_ia(base, analyse)
        self.assertIn("[Photo]", fusionne["alertes_photo"][0])
        self.assertEqual(fusionne["resume"], "climatisation salon")  # resume texte prioritaire
        self.assertEqual(fusionne["questions"], ["Combien de pièces ?"])

    def test_alertes_photo_trouvent_le_moteur(self):
        prop = _propose(
            service_nom="Aménagement intérieur et extérieur", ville="Casablanca",
            surface=Decimal("40.00"), description="aménagement boutique, étagères placo",
            ia={"alertes_photo": ["[Photo] mur mitoyen humidité"], "postes": ["AME-PLA", "AME-PIN"]},
        )
        self.assertTrue(any("Photo" in a for a in prop.alertes))


class FormatEtFiltreTests(TestCase):
    """Format français + filtre des notes internes."""

    def test_fmt_mad(self):
        self.assertEqual(fmt_mad(Decimal("1085400.00")), "1" + "\u00a0" + "085" + "\u00a0" + "400,00")

    def test_filtrer_notes_client(self):
        notes = "\n".join([
            "[IA] Confiance : elevee",
            "• Réf. interne",
            "Résumé : climatisation",
            "Pensez à commander le carrelage gris avant lundi",
        ])
        visibles = filtrer_notes_client(notes)
        self.assertEqual(visibles, ["Pensez à commander le carrelage gris avant lundi"])
        # aucune ligne du moteur ne fuit : préfixe « [ » aussi bloqué
        self.assertEqual(filtrer_notes_client("[IA] Alerte : surface ?"), [])

    def test_charger_polices_repli_generic(self):
        fontes = charger_polices("/dossier/inexistant")  # pas de polices → Helvetica
        self.assertEqual(fontes[0], "Helvetica")
