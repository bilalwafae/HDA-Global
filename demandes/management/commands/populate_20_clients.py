"""
Commande Django : populate_20_clients
Génère 20 clients réalistes marocains avec leurs demandes, devis,
lignes de chiffrage, historiques de statuts et interventions de chantier.
Permet d'alimenter le Dashboard analytique et de tester l'espace client.
"""
from decimal import Decimal
import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone

from clients.models import Client
from services.models import Service
from demandes.models import Demande, HistoriqueStatut
from devis.models import Devis, LigneDevis
from devis.pricing import recalculer_devis
from interventions.models import Intervention


CLIENTS_DATA = [
    {
        "nom_complet": "Mohammed El Alami",
        "email": "m.elalami@gmail.com",
        "telephone": "+212 661 123 456",
        "ville": "Casablanca",
        "adresse": "14 Rue Ibn Battouta, Quartier Maarif, Casablanca",
        "notes_admin": "Client particulier exigeant, recherche finitions haut standing.",
        "demande": {
            "service_slug": "construction-renovation",
            "ville_chantier": "Casablanca",
            "adresse_chantier": "Rue des Orangers, Ain Diab, Casablanca",
            "surface_m2": Decimal("90.00"),
            "date_souhaitee": timezone.localdate() - datetime.timedelta(days=20),
            "description": "Rénovation complète d'un appartement de 90m² : démolition des cloisons de séparation, pose carrelage 60x60 effet marbre, réfection totale plomberie et peinture.",
            "statut": Demande.STATUT_EN_COURS,
            "notes": "Chantier démarré le 05 du mois. Gros œuvre terminé, plomberie en cours.",
        },
        "devis": {
            "statut": Devis.STATUT_ACCEPTE,
            "conditions": "30% versés à la signature (reçus). 40% à mi-chantier, 30% à la livraison.",
            "lignes": [
                ("Démolition des cloisons & évacuation des gravats", Decimal("1"), "forfait", Decimal("4500.00")),
                ("Pose carrelage 60x60 grès cérame poli", Decimal("90"), "m²", Decimal("180.00")),
                ("Peinture intérieure satinée 2 couches + enduit", Decimal("220"), "m²", Decimal("65.00")),
                ("Rénovation plomberie multicouche & sanitaires", Decimal("1"), "forfait", Decimal("9500.00")),
            ],
        },
        "intervention": {
            "statut": Intervention.STATUT_EN_COURS,
            "debut_offset": -15,
            "fin_offset": 20,
            "responsable": "Si Rachid (Conducteur de travaux)",
            "equipe": "Hamid (Maçon), Yassine (Carreleur), Brahim (Plombier)",
            "instructions": "Accès immeuble par monte-charge côté cour. Respecter horaires 8h30-17h30.",
        },
        "historique": [
            ("nouvelle", "en_etude", "Admin", "Dossier pris en charge par le métreur"),
            ("en_etude", "devis_envoye", "Admin", "Devis chiffré et envoyé par email"),
            ("devis_envoye", "acceptee", "Mohammed El Alami", "Devis accepté en ligne"),
            ("acceptee", "en_cours", "Admin", "Démarrage effectif du chantier"),
        ],
    },
    {
        "nom_complet": "Fatima Zahra Benali",
        "email": "fz.benali@outlook.com",
        "telephone": "+212 654 789 012",
        "ville": "Mohammedia",
        "adresse": "Résidence Al Amal, Appt 5, Bd Hassan II, Mohammedia",
        "notes_admin": "Contactée par recommandation d'un ancien client.",
        "demande": {
            "service_slug": "climatisation-ventilation",
            "ville_chantier": "Mohammedia",
            "adresse_chantier": "Avenue des FAR, Résidence Les Palmiers, Mohammedia",
            "surface_m2": Decimal("75.00"),
            "date_souhaitee": timezone.localdate() + datetime.timedelta(days=7),
            "description": "Fourniture et installation de 3 unités de climatisation split inverter (salon 18000 BTU, 2 chambres 9000 BTU) avec liaisons frigorifiques discrètes.",
            "statut": Demande.STATUT_DEVIS_ENVOYE,
            "notes": "En attente du retour de la cliente sur le choix de la marque.",
        },
        "devis": {
            "statut": Devis.STATUT_ENVOYE,
            "conditions": "Paiement 50% à la livraison du matériel, solde à la mise en service.",
            "lignes": [
                ("Climatiseur Split Inverter 18000 BTU (Salon)", Decimal("1"), "unité", Decimal("7200.00")),
                ("Climatiseurs Split Inverter 9000 BTU (Chambres)", Decimal("2"), "unité", Decimal("4800.00")),
                ("Liaisons frigorifiques calorifugées & goulottes", Decimal("3"), "forfait", Decimal("950.00")),
                ("Tirage au vide, mise en gaz & tests thermiques", Decimal("3"), "unité", Decimal("350.00")),
            ],
        },
        "historique": [
            ("nouvelle", "en_etude", "Admin", "Prise de contact téléphonique effectuée"),
            ("en_etude", "devis_envoye", "Admin", "Devis détaillé transmis avec fiche technique"),
        ],
    },
    {
        "nom_complet": "Société IMMO ATLAS SARL",
        "email": "contact@immoatlas.ma",
        "telephone": "+212 522 345 678",
        "ville": "Casablanca",
        "adresse": "Bd Zerktouni, Tour Atlas 3ème étage, Casablanca",
        "notes_admin": "Promoteur immobilier, potentiel de plusieurs chantiers annuels.",
        "demande": {
            "service_slug": "gestion-projets-tce",
            "ville_chantier": "Casablanca",
            "adresse_chantier": "Zone Industrielle Ain Sebaa, Lot 45, Casablanca",
            "surface_m2": Decimal("520.00"),
            "date_souhaitee": timezone.localdate() + datetime.timedelta(days=30),
            "description": "Construction TCE d'un entrepôt logistique et bureaux de 520m² sur terrain viabilisé. Gros œuvre béton armé, charpente métallique, électricité industrielle et voirie.",
            "statut": Demande.STATUT_NOUVELLE,
            "notes": "Plans architecte reçus en format DWG. Rendez-vous prévu sur site jeudi.",
        },
        "historique": [
            ("nouvelle", "nouvelle", "Système", "Demande enregistrée via formulaire web"),
        ],
    },
    {
        "nom_complet": "Karim Tazi",
        "email": "karim.tazi@menara.ma",
        "telephone": "+212 661 987 654",
        "ville": "Casablanca",
        "adresse": "Villa 12, Rue Franklin, Quartier Racine, Casablanca",
        "notes_admin": "Chantier d'aménagement intérieur haut standing.",
        "demande": {
            "service_slug": "amenagement-interieur-exterieur",
            "ville_chantier": "Casablanca",
            "adresse_chantier": "Rue Franklin, Racine, Casablanca",
            "surface_m2": Decimal("220.00"),
            "date_souhaitee": timezone.localdate() - datetime.timedelta(days=10),
            "description": "Aménagement complet villa : faux plafonds staff avec corniches et gorges lumineuses LED, peinture stucco décorative salon, parquet chêne massif dans les chambres.",
            "statut": Demande.STATUT_EN_COURS,
            "notes": "Matériaux livrés. Équipe staffeurs sur place.",
        },
        "devis": {
            "statut": Devis.STATUT_ACCEPTE,
            "conditions": "40% acompte, 30% mi-parcours, 30% réception des travaux.",
            "lignes": [
                ("Faux plafonds en staff lisse avec gorges lumineuses", Decimal("220"), "m²", Decimal("210.00")),
                ("Peinture décorative Stucco vénitien (Salon & Hall)", Decimal("110"), "m²", Decimal("160.00")),
                ("Fourniture et pose parquet chêne contrecollé", Decimal("130"), "m²", Decimal("380.00")),
                ("Portes intérieures en bois massif Iroko laqué blanc", Decimal("8"), "unité", Decimal("2400.00")),
            ],
        },
        "intervention": {
            "statut": Intervention.STATUT_EN_COURS,
            "debut_offset": -8,
            "fin_offset": 25,
            "responsable": "Mourad (Chef décorateur)",
            "equipe": "Abdelali (Staffeur), Khalid (Parqueteur), Hassan (Peintre)",
            "instructions": "Protéger le marbre du hall existant avec film feutre épais.",
        },
        "historique": [
            ("nouvelle", "en_etude", "Admin", "Métré sur place effectué le 02"),
            ("en_etude", "devis_envoye", "Admin", "Devis envoyé avec échantillons"),
            ("devis_envoye", "acceptee", "Karim Tazi", "Devis signé et acompte versé"),
            ("acceptee", "en_cours", "Admin", "Démarrage phase faux-plafonds"),
        ],
    },
    {
        "nom_complet": "Dr. Youssef Berrada",
        "email": "dr.berrada@clinique-espoir.ma",
        "telephone": "+212 662 334 455",
        "ville": "Casablanca",
        "adresse": "Bd d'Anfa, Clinique Al Amal, Casablanca",
        "notes_admin": "Chantier médical nécessitant matériaux certifiés et anti-bactériens.",
        "demande": {
            "service_slug": "plomberie-generale",
            "ville_chantier": "Casablanca",
            "adresse_chantier": "Boulevard d'Anfa, Étage 2, Casablanca",
            "surface_m2": Decimal("350.00"),
            "date_souhaitee": timezone.localdate() + datetime.timedelta(days=12),
            "description": "Rénovation de la plomberie sanitaire de 8 chambres médicalisées et du bloc d'accueil : remplacement tuyauterie par PPR thermo-fusion, pose robinetterie électronique sans contact et sanitaires PMR.",
            "statut": Demande.STATUT_PLANIFIEE,
            "notes": "Planification calée avec la direction de la clinique pendant les congés.",
        },
        "devis": {
            "statut": Devis.STATUT_ACCEPTE,
            "conditions": "Règlement à 30 jours fin de mois, bon de commande administratif.",
            "lignes": [
                ("Réseau alimentation eau PPR Green Pipe haute pression", Decimal("1"), "forfait", Decimal("22000.00")),
                ("Robinetterie médicale électronique infra-rouge", Decimal("12"), "unité", Decimal("1850.00")),
                ("Cuvettes suspendues anti-bactériennes PMR avec bâti-support", Decimal("8"), "unité", Decimal("3200.00")),
                ("Réseau évacuation PVC acoustique renforcé", Decimal("1"), "forfait", Decimal("8900.00")),
            ],
        },
        "intervention": {
            "statut": Intervention.STATUT_PLANIFIEE,
            "debut_offset": 5,
            "fin_offset": 22,
            "responsable": "Kamal (Ingénieur Fluides)",
            "equipe": "Adil (Chef plombier), Simohamed (Technicien PPR), Othmane",
            "instructions": "Travaux en milieu médical : tenues blanches et silence obligatoire après 12h.",
        },
        "historique": [
            ("nouvelle", "en_etude", "Admin", "Cahier des charges sanitaire étudié"),
            ("en_etude", "devis_envoye", "Admin", "Devis transmis à la commission des achats"),
            ("devis_envoye", "acceptee", "Dr. Youssef Berrada", "Devis validé par la direction"),
            ("acceptee", "planifiee", "Admin", "Intervention programmée"),
        ],
    },
    {
        "nom_complet": "Meriem Chraibi",
        "email": "meriem.chraibi@yahoo.fr",
        "telephone": "+212 663 112 233",
        "ville": "Mohammedia",
        "adresse": "Quartier Miramar, Résidence Les Dauphins, Mohammedia",
        "notes_admin": "Demande de climatisation discrète pour villa vue mer.",
        "demande": {
            "service_slug": "climatisation-ventilation",
            "ville_chantier": "Mohammedia",
            "adresse_chantier": "Corniche Miramar, Villa n°8, Mohammedia",
            "surface_m2": Decimal("180.00"),
            "date_souhaitee": timezone.localdate() + datetime.timedelta(days=15),
            "description": "Installation d'un système de climatisation gainable centralisé avec régulation zone par zone (Airzone) dans salon et 3 suites de villa.",
            "statut": Demande.STATUT_DEVIS_ENVOYE,
            "notes": "Devis transmis avec option traitement anti-corrosion marine pour groupe extérieur.",
        },
        "devis": {
            "statut": Devis.STATUT_ENVOYE,
            "conditions": "40% à la commande, 40% livraison unités, 20% mise en service.",
            "lignes": [
                ("Groupe extérieur Inverter Tropicalisé 48000 BTU anti-corrosion", Decimal("1"), "unité", Decimal("22500.00")),
                ("Unités intérieures gainables extra-plates avec plénum", Decimal("4"), "unité", Decimal("4800.00")),
                ("Système de régulation Airzone avec thermostats tactiles", Decimal("4"), "unité", Decimal("1900.00")),
                ("Gaines isolées aluminium & grilles de soufflage linéaires", Decimal("1"), "forfait", Decimal("4900.00")),
            ],
        },
        "historique": [
            ("nouvelle", "en_etude", "Admin", "Visite technique avec installateur agréé"),
            ("en_etude", "devis_envoye", "Admin", "Devis envoyé par email"),
        ],
    },
    {
        "nom_complet": "Cabinet Me. Naciri & Associés",
        "email": "contact@naciri-avocats.ma",
        "telephone": "+212 522 998 877",
        "ville": "Casablanca",
        "adresse": "72 Boulevard d'Anfa, Immeuble Zenith, Casablanca",
        "notes_admin": "Projet de prestige livré dans les délais et au budget convenu.",
        "demande": {
            "service_slug": "amenagement-interieur-exterieur",
            "ville_chantier": "Casablanca",
            "adresse_chantier": "72 Boulevard d'Anfa, Casablanca",
            "surface_m2": Decimal("140.00"),
            "date_souhaitee": timezone.localdate() - datetime.timedelta(days=60),
            "description": "Aménagement complet d'un cabinet d'avocats de 140m² : cloisons amovibles vitrées acoustiques, moquette en dalles grand passage, électricité réseau RJ45 catégorie 6A et peinture satinée.",
            "statut": Demande.STATUT_TERMINEE,
            "notes": "Chantier réceptionné sans réserve. Client très satisfait.",
        },
        "devis": {
            "statut": Devis.STATUT_ACCEPTE,
            "conditions": "Payé intégralement à la livraison.",
            "lignes": [
                ("Cloisons vitrées bord à bord acoustiques avec portes verre", Decimal("45"), "ml", Decimal("950.00")),
                ("Moquette plombante en dalles Balsan trafic intense", Decimal("140"), "m²", Decimal("190.00")),
                ("Câblage réseau VDI 36 prises RJ45 + baie de brassage", Decimal("1"), "forfait", Decimal("9800.00")),
                ("Peinture murs et boiseries vernies", Decimal("280"), "m²", Decimal("55.00")),
            ],
        },
        "intervention": {
            "statut": Intervention.STATUT_TERMINEE,
            "debut_offset": -50,
            "fin_offset": -10,
            "responsable": "Tariq (Superviseur Chantiers BTP)",
            "equipe": "Reda (Monteur cloisons), Nabil (Câbleur réseau), Mustapha",
            "instructions": "Travaux de nuit et week-end autorisés par le syndic de l'immeuble.",
        },
        "historique": [
            ("nouvelle", "en_etude", "Admin", "Cahier des charges reçu"),
            ("en_etude", "devis_envoye", "Admin", "Devis transmis"),
            ("devis_envoye", "acceptee", "Cabinet Naciri", "Devis approuvé"),
            ("acceptee", "en_cours", "Admin", "Travaux lancés"),
            ("en_cours", "terminee", "Admin", "Réception définitive des travaux et procès-verbal signé"),
        ],
    },
    {
        "nom_complet": "Hassan El Mansouri",
        "email": "h.mansouri77@gmail.com",
        "telephone": "+212 664 556 677",
        "ville": "Beni Yakhlef",
        "adresse": "Douar Oulad Sidi Ali, Beni Yakhlef, Mohammedia",
        "notes_admin": "Voisin direct du siège H.D.A GLOBAL.",
        "demande": {
            "service_slug": "construction-renovation",
            "ville_chantier": "Beni Yakhlef",
            "adresse_chantier": "Beni Yakhlef Centre, Mohammedia",
            "surface_m2": Decimal("110.00"),
            "date_souhaitee": timezone.localdate() + datetime.timedelta(days=20),
            "description": "Surélévation d'un étage supplémentaire sur maison R+1 existante. Coulage de poteaux-poutres béton armé, dalle hourdis 16+4, maçonnerie brique rouge 12 trous et enduit extérieur.",
            "statut": Demande.STATUT_EN_ETUDE,
            "notes": "Étude de sol et plan de béton armé en cours d'analyse par l'ingénieur conseil.",
        },
        "historique": [
            ("nouvelle", "en_etude", "Admin", "Vérification de la solidité des fondations existantes"),
        ],
    },
    {
        "nom_complet": "Bouchra Amrani",
        "email": "bouchra.amrani@gmail.com",
        "telephone": "+212 670 123 987",
        "ville": "Rabat",
        "adresse": "Avenue Fal Ould Oumeir, Agdal, Rabat",
        "notes_admin": "Souhaite des travaux soignés à Rabat.",
        "demande": {
            "service_slug": "construction-renovation",
            "ville_chantier": "Rabat",
            "adresse_chantier": "Quartier Agdal, Rue Oukaimeden, Rabat",
            "surface_m2": Decimal("45.00"),
            "date_souhaitee": timezone.localdate() + datetime.timedelta(days=14),
            "description": "Rénovation complète d'une cuisine moderne et de 2 salles de bain d'appartement : dépose de l'ancien carrelage, création d'une douche à l'italienne, faux plafond hydrofuge et robinetterie encastrée.",
            "statut": Demande.STATUT_NOUVELLE,
            "notes": "Photos des pièces envoyées. Métrage prévu lors de notre prochaine tournée Rabat.",
        },
        "historique": [
            ("nouvelle", "nouvelle", "Système", "Demande en ligne enregistrée"),
        ],
    },
    {
        "nom_complet": "Société AGRO MAGHREB",
        "email": "direction@agromaghreb.co.ma",
        "telephone": "+212 522 765 432",
        "ville": "Berrechid",
        "adresse": "Zone Industrielle Sud, Lot 108, Berrechid",
        "notes_admin": "Entreprise agro-alimentaire nécessitant une étanchéité certifiée sans fuite.",
        "demande": {
            "service_slug": "services-divers-sur-mesure",
            "ville_chantier": "Berrechid",
            "adresse_chantier": "Zone Industrielle Berrechid",
            "surface_m2": Decimal("800.00"),
            "date_souhaitee": timezone.localdate() - datetime.timedelta(days=5),
            "description": "Travaux d'étanchéité multicouche bitumineuse avec chape aluminium autoprotegée et isolation thermique polystyrène expansé sur toiture terrasse de dépôt de stockage de 800m².",
            "statut": Demande.STATUT_EN_COURS,
            "notes": "Chantier en cours. 50% de la surface traitée avant les pluies.",
        },
        "devis": {
            "statut": Devis.STATUT_ACCEPTE,
            "conditions": "Acompte 30% versé. Reste 70% à la livraison avec garantie décennale.",
            "lignes": [
                ("Nettoyage, décapage et forme de pente en mortier", Decimal("800"), "m²", Decimal("45.00")),
                ("Isolation thermique polystyrène haute densité 50mm", Decimal("800"), "m²", Decimal("55.00")),
                ("Étanchéité bicouche bitume élastomère SBS 4mm + gravillons", Decimal("800"), "m²", Decimal("85.00")),
                ("Traitement des relevés d'étanchéité et solins métalliques", Decimal("160"), "ml", Decimal("95.00")),
            ],
        },
        "intervention": {
            "statut": Intervention.STATUT_EN_COURS,
            "debut_offset": -6,
            "fin_offset": 12,
            "responsable": "Chakib (Responsable Étanchéité & Gros Œuvre)",
            "equipe": "Équipe étancheurs n°2 (4 ouvriers qualifiés)",
            "instructions": "Précautions feu lors de la soudure au chalumeau. Extincteurs obligatoires.",
        },
        "historique": [
            ("nouvelle", "en_etude", "Admin", "Diagnostic toiture par drone et sondages"),
            ("en_etude", "devis_envoye", "Admin", "Devis avec garantie décennale émis"),
            ("devis_envoye", "acceptee", "AGRO MAGHREB", "Bon pour accord reçu"),
            ("acceptee", "en_cours", "Admin", "Démarrage des travaux"),
        ],
    },
    {
        "nom_complet": "Omar Benjelloun",
        "email": "omar.benjelloun@gmail.com",
        "telephone": "+212 661 445 566",
        "ville": "Casablanca",
        "adresse": "Villa Les Acacias, Quartier Californie, Casablanca",
        "notes_admin": "Aménagement extérieur piscine et terrasse en pierre d'Ifrane.",
        "demande": {
            "service_slug": "amenagement-interieur-exterieur",
            "ville_chantier": "Casablanca",
            "adresse_chantier": "Quartier Californie, Casablanca",
            "surface_m2": Decimal("160.00"),
            "date_souhaitee": timezone.localdate() - datetime.timedelta(days=12),
            "description": "Aménagement plage de piscine et terrasse en pierre naturelle bouchardée, installation d'une pergola bioclimatique aluminium motorisée et éclairage d'ambiance LED étanche.",
            "statut": Demande.STATUT_EN_COURS,
            "notes": "Pose des margelles terminée, structure pergola en cours d'assemblage.",
        },
        "devis": {
            "statut": Devis.STATUT_ACCEPTE,
            "conditions": "35% acompte, 35% livraison pierre, 30% solde.",
            "lignes": [
                ("Pose de dallage pierre naturelle bouchardée 40x40", Decimal("160"), "m²", Decimal("240.00")),
                ("Pergola aluminium thermolaqué à lames orientables 6x4m", Decimal("1"), "forfait", Decimal("38000.00")),
                ("Spots LED encastrés au sol IP67 & raccordement étanche", Decimal("16"), "unité", Decimal("450.00")),
            ],
        },
        "intervention": {
            "statut": Intervention.STATUT_EN_COURS,
            "debut_offset": -10,
            "fin_offset": 10,
            "responsable": "Si Rachid (Conducteur de travaux)",
            "equipe": "Aziz (Menuisier alu), Younes (Électricien extérieur), Mehdi",
            "instructions": "Attention à la pelouse et aux arrosages automatiques existants.",
        },
        "historique": [
            ("nouvelle", "en_etude", "Admin", "Plan 3D extérieur validé"),
            ("en_etude", "devis_envoye", "Admin", "Chiffrage transmis"),
            ("devis_envoye", "acceptee", "Omar Benjelloun", "Accord client"),
            ("acceptee", "en_cours", "Admin", "Chantier en cours"),
        ],
    },
    {
        "nom_complet": "Salma Kabbaj",
        "email": "salma.kabbaj@hotmail.com",
        "telephone": "+212 662 990 011",
        "ville": "Mohammedia",
        "adresse": "Quartier Wafa 2, Rue 14, Mohammedia",
        "notes_admin": "Projet chauffe-eau solaire et rénovation buanderie.",
        "demande": {
            "service_slug": "plomberie-generale",
            "ville_chantier": "Mohammedia",
            "adresse_chantier": "Quartier Wafa, Mohammedia",
            "surface_m2": Decimal("25.00"),
            "date_souhaitee": timezone.localdate() + datetime.timedelta(days=10),
            "description": "Installation d'un chauffe-eau solaire 300 Litres sur toiture avec appoint électrique, et raccordement de la distribution eau chaude pour toute la maison.",
            "statut": Demande.STATUT_DEVIS_ENVOYE,
            "notes": "Devis transmis avec proposition ballon inox garanti 5 ans.",
        },
        "devis": {
            "statut": Devis.STATUT_ENVOYE,
            "conditions": "Paiement à la livraison et mise en route.",
            "lignes": [
                ("Chauffe-eau solaire 300L capteurs sous vide certifié", Decimal("1"), "unité", Decimal("12500.00")),
                ("Châssis support toiture renforcé pour zone côtière", Decimal("1"), "unité", Decimal("1800.00")),
                ("Tuyauterie cuivre calorifugée haute température", Decimal("25"), "ml", Decimal("95.00")),
            ],
        },
        "historique": [
            ("nouvelle", "en_etude", "Admin", "Étude ensoleillement toiture"),
            ("en_etude", "devis_envoye", "Admin", "Devis envoyé"),
        ],
    },
    {
        "nom_complet": "SARL TEXTILE DU NORD",
        "email": "contact@textiledunord.ma",
        "telephone": "+212 522 234 567",
        "ville": "Casablanca",
        "adresse": "Boulevard Al Qods, Ain Chock, Casablanca",
        "notes_admin": "Atelier de confection textile.",
        "demande": {
            "service_slug": "services-divers-sur-mesure",
            "ville_chantier": "Casablanca",
            "adresse_chantier": "Ain Chock, Casablanca",
            "surface_m2": Decimal("400.00"),
            "date_souhaitee": timezone.localdate() + datetime.timedelta(days=18),
            "description": "Mise aux normes électriques atelier de confection : remplacement tableau divisionnaire général, installation éclairage LED industriel 150W haute luminosité et gaines de ventilation.",
            "statut": Demande.STATUT_PLANIFIEE,
            "notes": "Planifié pendant l'arrêt technique d'usine fin de mois.",
        },
        "devis": {
            "statut": Devis.STATUT_ACCEPTE,
            "conditions": "Paiement échelonné 50% début, 50% fin de travaux.",
            "lignes": [
                ("Armoire électrique générale Schneider avec disjoncteurs différentiels", Decimal("1"), "forfait", Decimal("19500.00")),
                ("Cloches LED industrielles 150W 18000 lumens étanches IP65", Decimal("24"), "unité", Decimal("850.00")),
                ("Chemins de câbles métalliques perforés et filerie", Decimal("120"), "ml", Decimal("120.00")),
                ("Extracteurs d'air industriels pour renouvellement d'air", Decimal("4"), "unité", Decimal("2200.00")),
            ],
        },
        "intervention": {
            "statut": Intervention.STATUT_PLANIFIEE,
            "debut_offset": 8,
            "fin_offset": 15,
            "responsable": "Tariq (Superviseur Chantiers BTP)",
            "equipe": "Équipe électriciens industriels (3 techniciens)",
            "instructions": "Travaux sans poussière au dessus des machines à coudre.",
        },
        "historique": [
            ("nouvelle", "en_etude", "Admin", "Audit électrique effectué"),
            ("en_etude", "devis_envoye", "Admin", "Devis envoyé"),
            ("devis_envoye", "acceptee", "SARL Textile", "Devis signé"),
            ("acceptee", "planifiee", "Admin", "Date calée sur arrêt machine"),
        ],
    },
    {
        "nom_complet": "Mehdi Fassi Fihri",
        "email": "mehdi.fassi@fihri.ma",
        "telephone": "+212 661 778 899",
        "ville": "Bouskoura",
        "adresse": "Ville Verte de Bouskoura, Villa Les Pins, Casablanca",
        "notes_admin": "Client grand compte résidentiel.",
        "demande": {
            "service_slug": "amenagement-interieur-exterieur",
            "ville_chantier": "Bouskoura",
            "adresse_chantier": "Ville Verte Bouskoura",
            "surface_m2": Decimal("130.00"),
            "date_souhaitee": timezone.localdate() - datetime.timedelta(days=45),
            "description": "Peinture intérieure complète marque haut de gamme Tollens, application papier peint panoramique dans la suite parentale et pose de plinthes laquées blanches assorties.",
            "statut": Demande.STATUT_TERMINEE,
            "notes": "Livré le mois dernier. Facture acquittée sans incident.",
        },
        "devis": {
            "statut": Devis.STATUT_ACCEPTE,
            "conditions": "Règlement 100% à la livraison.",
            "lignes": [
                ("Préparation minutieuse des fonds (2 passes d'enduit fin)", Decimal("320"), "m²", Decimal("35.00")),
                ("Peinture veloutée Tollens dépolluante teintes au choix", Decimal("320"), "m²", Decimal("65.00")),
                ("Pose papier peint panoramique intissé raccord sauté", Decimal("2"), "forfait", Decimal("1800.00")),
            ],
        },
        "intervention": {
            "statut": Intervention.STATUT_TERMINEE,
            "debut_offset": -40,
            "fin_offset": -20,
            "responsable": "Mourad (Chef décorateur)",
            "equipe": "Hassan (Peintre), Noureddine",
            "instructions": "Finitions de précision sous lumière rasante.",
        },
        "historique": [
            ("nouvelle", "en_etude", "Admin", "Choix du nuancier de couleurs"),
            ("en_etude", "devis_envoye", "Admin", "Devis envoyé"),
            ("devis_envoye", "acceptee", "Mehdi Fassi", "Accord client"),
            ("acceptee", "en_cours", "Admin", "Chantier ouvert"),
            ("en_cours", "terminee", "Admin", "Travaux validés et réceptionnés"),
        ],
    },
    {
        "nom_complet": "Khadija Idrissi",
        "email": "khadija.idrissi@gmail.com",
        "telephone": "+212 663 887 766",
        "ville": "Casablanca",
        "adresse": "Rue Cadi Iass, Quartier CIL, Casablanca",
        "notes_admin": "Rénovation de duplex familial.",
        "demande": {
            "service_slug": "gestion-projets-tce",
            "ville_chantier": "Casablanca",
            "adresse_chantier": "Quartier CIL, Casablanca",
            "surface_m2": Decimal("170.00"),
            "date_souhaitee": timezone.localdate() + datetime.timedelta(days=25),
            "description": "Rénovation globale TCE d'un duplex : démolition d'un escalier béton et remplacement par un escalier hélicoïdal métallique et bois, création d'une suite avec dressing et réagencement complet du rez-de-chaussée.",
            "statut": Demande.STATUT_EN_ETUDE,
            "notes": "Étude d'ingénierie structure en cours pour la trémie d'escalier.",
        },
        "historique": [
            ("nouvelle", "en_etude", "Admin", "Visite sur place avec l'ingénieur béton"),
        ],
    },
    {
        "nom_complet": "Restaurant LE BISTROT DU PORT",
        "email": "direction@bistrotduport.ma",
        "telephone": "+212 523 321 000",
        "ville": "Mohammedia",
        "adresse": "Port de Plaisance, Corniche de Mohammedia",
        "notes_admin": "Restaurant réputé de la corniche.",
        "demande": {
            "service_slug": "climatisation-ventilation",
            "ville_chantier": "Mohammedia",
            "adresse_chantier": "Port de Mohammedia",
            "surface_m2": Decimal("150.00"),
            "date_souhaitee": timezone.localdate() - datetime.timedelta(days=15),
            "description": "Installation d'une hotte d'extraction professionnelle en inox 304L avec moteur tourelle 400°C 2h pour cuisine de restaurant, et système d'apport d'air neuf compensé.",
            "statut": Demande.STATUT_EN_COURS,
            "notes": "Hotte installée, raccordement du conduit d'extraction en toiture en cours.",
        },
        "devis": {
            "statut": Devis.STATUT_ACCEPTE,
            "conditions": "40% commande, 30% pose hotte, 30% tests d'aspiration.",
            "lignes": [
                ("Hotte inox 304L 3500mm avec filtres à chicane et bac graisses", Decimal("1"), "forfait", Decimal("28000.00")),
                ("Tourelle d'extraction 400°/2h 4500 m3/h avec variateur", Decimal("1"), "unité", Decimal("14500.00")),
                ("Conduit d'évacuation inox double paroi coupe-feu 2h", Decimal("18"), "ml", Decimal("950.00")),
                ("Centrale de traitement d'air neuf compensé avec filtration", Decimal("1"), "unité", Decimal("12800.00")),
            ],
        },
        "intervention": {
            "statut": Intervention.STATUT_EN_COURS,
            "debut_offset": -12,
            "fin_offset": 8,
            "responsable": "Kamal (Ingénieur Fluides)",
            "equipe": "Équipe ventilation professionnelle (3 techniciens)",
            "instructions": "Intervention le matin avant ouverture du service à 11h.",
        },
        "historique": [
            ("nouvelle", "en_etude", "Admin", "Audit normes d'hygiène et extraction"),
            ("en_etude", "devis_envoye", "Admin", "Devis validé par le gérant"),
            ("devis_envoye", "acceptee", "Le Bistrot du Port", "Bon de commande officiel signé"),
            ("acceptee", "en_cours", "Admin", "Fabrication et montage sur site"),
        ],
    },
    {
        "nom_complet": "Rachid Slaoui",
        "email": "rachid.slaoui@gmail.com",
        "telephone": "+212 661 554 433",
        "ville": "Settat",
        "adresse": "Quartier M'dina Jadida, Settat",
        "notes_admin": "Projet de construction de villa neuve R+1 clé en main.",
        "demande": {
            "service_slug": "construction-renovation",
            "ville_chantier": "Settat",
            "adresse_chantier": "Lotissement Al Firdaous, Settat",
            "surface_m2": Decimal("260.00"),
            "date_souhaitee": timezone.localdate() - datetime.timedelta(days=25),
            "description": "Construction d'une villa neuve moderne R+1 avec sous-sol partiel : terrassement en déblai/remblai, semelles isolées béton armé, élévation des murs et dalles, étanchéité toiture.",
            "statut": Demande.STATUT_EN_COURS,
            "notes": "Dalle du premier étage coulée hier. Séchage 21 jours.",
        },
        "devis": {
            "statut": Devis.STATUT_ACCEPTE,
            "conditions": "Paiement par tranches selon avancement certifié par le bureau de contrôle.",
            "lignes": [
                ("Terrassement général en masse et fouilles", Decimal("1"), "forfait", Decimal("22000.00")),
                ("Béton armé en fondations (semelles, longrines, amorces)", Decimal("65"), "m³", Decimal("1300.00")),
                ("Béton armé en élévation (poteaux, poutres, dalles hourdis)", Decimal("110"), "m³", Decimal("1450.00")),
                ("Maçonnerie en double cloison brique avec laine de roche", Decimal("380"), "m²", Decimal("135.00")),
            ],
        },
        "intervention": {
            "statut": Intervention.STATUT_EN_COURS,
            "debut_offset": -22,
            "fin_offset": 60,
            "responsable": "Chakib (Responsable Gros Œuvre)",
            "equipe": "Équipe Gros Œuvre Settat (8 ouvriers, ferrailleurs, coffreurs)",
            "instructions": "Prélèvements d'éprouvettes béton à chaque coulage pour laboratoire LPEE.",
        },
        "historique": [
            ("nouvelle", "en_etude", "Admin", "Vérification des plans BA avec bureau de contrôle"),
            ("en_etude", "devis_envoye", "Admin", "Devis phase gros œuvre envoyé"),
            ("devis_envoye", "acceptee", "Rachid Slaoui", "Contrat de construction paraphé"),
            ("acceptee", "en_cours", "Admin", "Ouverture du chantier et coulage fondations"),
        ],
    },
    {
        "nom_complet": "Nadia Bennani",
        "email": "nadia.bennani@archi-studio.ma",
        "telephone": "+212 662 119 988",
        "ville": "Casablanca",
        "adresse": "Rue Molière, Quartier Gauthier, Casablanca",
        "notes_admin": "Architecte d'intérieur partenaire.",
        "demande": {
            "service_slug": "amenagement-interieur-exterieur",
            "ville_chantier": "Casablanca",
            "adresse_chantier": "Rue Molière, Gauthier, Casablanca",
            "surface_m2": Decimal("85.00"),
            "date_souhaitee": timezone.localdate() + datetime.timedelta(days=15),
            "description": "Rénovation de plateau de bureau pour agence d'architecture : création de niches décoratives en plâtre, installation verrières atelier acier noir et éclairage sur rails magnétiques.",
            "statut": Demande.STATUT_DEVIS_ENVOYE,
            "notes": "Devis transmis avec proposition verrière sur-mesure serrurerie.",
        },
        "devis": {
            "statut": Devis.STATUT_ENVOYE,
            "conditions": "Acompte 40% au lancement, 60% à la livraison.",
            "lignes": [
                ("Verrière style atelier en acier thermolaqué noir avec vitrage 33.2", Decimal("14"), "m²", Decimal("1400.00")),
                ("Création de bibliothèques et niches encastrées en placo BA13", Decimal("1"), "forfait", Decimal("6500.00")),
                ("Rails magnétiques 48V avec spots orientables et suspensions", Decimal("18"), "ml", Decimal("350.00")),
            ],
        },
        "historique": [
            ("nouvelle", "en_etude", "Admin", "Métré précis de la trémie verrière"),
            ("en_etude", "devis_envoye", "Admin", "Devis envoyé par email"),
        ],
    },
    {
        "nom_complet": "Groupe Scolaire LES ÉLITES",
        "email": "intendance@leselites-ecole.ma",
        "telephone": "+212 522 654 321",
        "ville": "Casablanca",
        "adresse": "Bd El Qods, Quartier Oulfa, Casablanca",
        "notes_admin": "Établissement scolaire privé (Maternelle à Lycée).",
        "demande": {
            "service_slug": "services-divers-sur-mesure",
            "ville_chantier": "Casablanca",
            "adresse_chantier": "Quartier Oulfa, Casablanca",
            "surface_m2": Decimal("600.00"),
            "date_souhaitee": timezone.localdate() - datetime.timedelta(days=55),
            "description": "Travaux annuels de maintenance estivale : rénovation complète des blocs sanitaires élèves (16 toilettes, lavabos collectifs), peinture des couloirs et réfection des escaliers antidérapants.",
            "statut": Demande.STATUT_TERMINEE,
            "notes": "Chantier livré avant la rentrée scolaire de septembre.",
        },
        "devis": {
            "statut": Devis.STATUT_ACCEPTE,
            "conditions": "Facture acquittée par virement bancaire.",
            "lignes": [
                ("Rénovation des blocs sanitaires (faïence, robinetterie temporisée)", Decimal("16"), "unité", Decimal("1800.00")),
                ("Peinture lavable haute résistance couloirs et classes", Decimal("600"), "m²", Decimal("45.00")),
                ("Nez de marche antidérapants aluminium sur 4 cages d'escaliers", Decimal("120"), "ml", Decimal("85.00")),
            ],
        },
        "intervention": {
            "statut": Intervention.STATUT_TERMINEE,
            "debut_offset": -50,
            "fin_offset": -20,
            "responsable": "Tariq (Superviseur Chantiers BTP)",
            "equipe": "Équipe maintenance générale H.D.A GLOBAL (5 artisans)",
            "instructions": "Chantier en période de vacances scolaires, livraison impérative le 25.",
        },
        "historique": [
            ("nouvelle", "en_etude", "Admin", "Visite des locaux avec le directeur"),
            ("en_etude", "devis_envoye", "Admin", "Devis chiffré transmis"),
            ("devis_envoye", "acceptee", "Groupe Les Elites", "Bon de commande signé"),
            ("acceptee", "en_cours", "Admin", "Travaux exécutés"),
            ("en_cours", "terminee", "Admin", "Réception finale avant rentrée"),
        ],
    },
    {
        "nom_complet": "Tariq Zoubair",
        "email": "tariq.zoubair@gmail.com",
        "telephone": "+212 661 223 344",
        "ville": "Dar Bouazza",
        "adresse": "Tamaris, Dar Bouazza, Casablanca",
        "notes_admin": "Client a reporté pour cause de budget insuffisant cette année.",
        "demande": {
            "service_slug": "services-divers-sur-mesure",
            "ville_chantier": "Dar Bouazza",
            "adresse_chantier": "Tamaris 2, Dar Bouazza",
            "surface_m2": Decimal("120.00"),
            "date_souhaitee": timezone.localdate() - datetime.timedelta(days=15),
            "description": "Aménagement jardin extérieur : clôture en serrurerie métallique galvanisée, portail coulissant motorisé de 4m et pergola terrasse en bois traité autoclave.",
            "statut": Demande.STATUT_REFUSEE,
            "notes": "Client a trouvé le devis supérieur à son budget prévisionnel. À relancer au printemps.",
        },
        "devis": {
            "statut": Devis.STATUT_REFUSE,
            "conditions": "Paiement 30% acompte, 70% solde.",
            "lignes": [
                ("Clôture barreaudée acier galvanisé thermolaqué anti-sel", Decimal("35"), "ml", Decimal("650.00")),
                ("Portail coulissant motorisé 4x2m avec télécommandes", Decimal("1"), "forfait", Decimal("18500.00")),
                ("Pergola bois autoclave classe 4 avec toilage étanche", Decimal("1"), "forfait", Decimal("14000.00")),
            ],
        },
        "historique": [
            ("nouvelle", "en_etude", "Admin", "Visite sur place à Tamaris"),
            ("en_etude", "devis_envoye", "Admin", "Devis envoyé"),
            ("devis_envoye", "refusee", "Tariq Zoubair", "Refus client : budget reporté à 2027"),
        ],
    },
]


class Command(BaseCommand):
    help = "Popule la base de données avec 20 clients marocains réalistes, leurs demandes, devis et interventions."

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("=== Insertion des 20 clients marocains complets H.D.A GLOBAL ==="))

        services = {s.slug: s for s in Service.objects.all()}
        if not services:
            self.stdout.write(self.style.ERROR("Aucun service trouve. Lancez d'abord load_demo_data."))
            return

        for index, item in enumerate(CLIENTS_DATA, start=1):
            client, _ = Client.objects.update_or_create(
                email=item["email"],
                defaults={
                    "nom_complet": item["nom_complet"],
                    "telephone": item["telephone"],
                    "ville": item["ville"],
                    "adresse_principale": item["adresse"],
                    "notes_admin": item.get("notes_admin", ""),
                },
            )

            d_data = item["demande"]
            service = services.get(d_data["service_slug"])

            # Vérifier si la demande existe déjà pour éviter les doublons
            demande = Demande.objects.filter(client=client, service=service).first()
            if not demande:
                demande = Demande.objects.create(
                    client=client,
                    service=service,
                    ville_chantier=d_data["ville_chantier"],
                    adresse_chantier=d_data["adresse_chantier"],
                    surface_m2=d_data.get("surface_m2"),
                    date_souhaitee=d_data.get("date_souhaitee"),
                    description_besoin=d_data["description"],
                    statut=d_data["statut"],
                    notes_internes=d_data.get("notes", ""),
                )
            else:
                demande.statut = d_data["statut"]
                demande.save(update_fields=["statut"])

            # Historique des statuts
            demande.historique.all().delete()
            for h in item.get("historique", []):
                HistoriqueStatut.objects.create(
                    demande=demande,
                    ancien_statut=h[0],
                    nouveau_statut=h[1],
                    auteur=h[2],
                    commentaire=h[3],
                )

            # Devis associé si présent
            if "devis" in item:
                dv_data = item["devis"]
                devis = Devis.objects.filter(demande=demande).first()
                if not devis:
                    devis = Devis.objects.create(
                        demande=demande,
                        statut=dv_data["statut"],
                        taux_tva=Decimal("20.00"),
                        conditions_reglement=dv_data.get("conditions", ""),
                    )
                else:
                    devis.statut = dv_data["statut"]
                    devis.conditions_reglement = dv_data.get("conditions", "")
                    devis.save(update_fields=["statut", "conditions_reglement"])

                devis.lignes.all().delete()
                for idx, l in enumerate(dv_data["lignes"], start=1):
                    LigneDevis.objects.create(
                        devis=devis,
                        designation=l[0],
                        quantite=l[1],
                        unite=l[2],
                        prix_unitaire_ht=l[3],
                        ordre=idx,
                    )
                recalculer_devis(devis)

            # Intervention associée si présente
            if "intervention" in item:
                iv_data = item["intervention"]
                today = timezone.localdate()
                date_deb = today + datetime.timedelta(days=iv_data["debut_offset"])
                date_f = today + datetime.timedelta(days=iv_data["fin_offset"])
                Intervention.objects.update_or_create(
                    demande=demande,
                    defaults={
                        "statut_chantier": iv_data["statut"],
                        "date_debut": date_deb,
                        "date_fin": date_f,
                        "responsable_chantier": iv_data["responsable"],
                        "equipe_assignee": iv_data["equipe"],
                        "ville": d_data["ville_chantier"],
                        "instructions_techniques": iv_data.get("instructions", ""),
                    },
                )

            self.stdout.write(f"  [{index}/20] [OK] {client.nom_complet} ({client.ville}) -> Demande: {demande.reference} ({demande.get_statut_display()})")

        self.stdout.write(self.style.SUCCESS("\n=== [OK] 20 Clients et leurs dossiers inseres avec succes ! ==="))

