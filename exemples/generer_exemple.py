"""
Génère un devis PDF EXEMPLE : exemples/generer_exemple.py
→ exemples/devis_exemple_DEV-2026-0001.pdf

Client 100 % FICTIF (jamais de données réelles dans les exemples).
La génération est pure : aucune base de données nécessaire.
Usage : .\\venv\\Scripts\\python.exe exemples\\generer_exemple.py
"""
import os
import sys
from decimal import Decimal
from pathlib import Path

from django.conf import settings

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hda_project.settings")
import django  # noqa: E402

if not settings.configured:
    django.setup()

from devis.pdf import construire_pdf, montant_en_lettres  # noqa: E402

# ─── Exemple : climatisation 85 m² à Casablanca (coïncide avec tests_auto) ──
LIGNES = [
    ("1", "Climatisation (fourniture, pose et raccordements)", "85,00", "m²", "320,00", "27 200,00"),
    ("2", "Kit d'installation et mise en service", "1,00", "forfait", "10 000,00", "10 000,00"),
]

DATA = {
    "emetteur": {
        "nom": "H.D.A GLOBAL SARL",
        "marque": "H.D.A GLOBAL – Construction TCE – Aménagement",
        "adresses": ["Beni Yakhlef, Mohammedia", "11, rue Ahmed Sitou, Etage 2, Appt 3, BD Mohamed V, 20000, Casablanca"],
        "telephone": "+212 661103988",
        "email": "hda.global82@gmail.com",
        "pied_legal": (
            "Devis valable 30 jours à compter de la date d'émission. Le règlement s'effectue à 30% à la "
            "commande et 70% à la livraison. TVA 20% applicable. H.D.A GLOBAL SARL – Mohammedia, Maroc"
        ),
    },
    "devis": {
        "numero": "DEV-2026-0001",
        "objet": "Prestation Climatisation",
        "taux_tva": "20",
        "date_validite": "30/11/2026",
    },
    "client": {
        "nom": "Client Exemple (fictif)",
        "telephone": "+212 6 12 34 56 78",
        "email": "exemple.client@introuvable.example",
        "ville": "Casablanca",
    },
    "chantier": {
        "reference": "DEM-2026-0001",
        "ville": "Casablanca",
        "adresse": "123 avenue Exemple, Casablanca",
    },
    "lignes": [
        {"n": n, "designation": d, "quantite": q, "unite": u, "pu": pu, "total": t}
        for (n, d, q, u, pu, t) in LIGNES
    ],
    "totaux": {"sous_total_ht": "37 200,00", "montant_tva": "7 440,00", "total_ttc": "44 640,00"},
    "montant_lettres": montant_en_lettres(Decimal("44640.00")),
    "conditions": "30% à la commande, 70% à la livraison des travaux. Délai d'exécution : 15 jours ouvrés.",
    "url_suivi": "http://localhost:8000/suivi/exemple-token-suivi/",
    "logo_path": None,
    "polices_dir": None,
}


def main():
    sortie = Path(__file__).parent / "devis_exemple_DEV-2026-0001.pdf"
    pdf_bytes = construire_pdf(DATA)
    sortie.write_bytes(pdf_bytes)
    print(f"PDF exemple écrit : {sortie}")


if __name__ == "__main__":
    main()
