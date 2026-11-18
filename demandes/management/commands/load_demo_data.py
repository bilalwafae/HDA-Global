"""
Commande de gestion Django : load_demo_data
Peuple la base de données avec les données de démonstration :
- Les 6 services TCE officiels H.D.A GLOBAL
- Les paramètres de l'entreprise
- 3 clients de démonstration
- Des demandes et devis d'exemple
- Un compte superutilisateur admin
"""
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone


User = get_user_model()


SERVICES_HDA = [
    {
        "nom": "Construction & Rénovation",
        "slug": "construction-renovation",
        "description_courte": "Gros œuvre, maçonnerie, réhabilitation et surélévation de bâtiments résidentiels et commerciaux.",
        "description_complete": (
            "H.D.A GLOBAL prend en charge tous vos projets de construction neuve et de rénovation. "
            "Nos équipes qualifiées maîtrisent les techniques de gros œuvre marocain (fondations, dalles, voiles), "
            "la maçonnerie traditionnelle et moderne, la réhabilitation de bâtiments anciens et les travaux de surélévation.\n\n"
            "Nous intervenons sur des projets résidentiels (villas, appartements, riads) et commerciaux (bureaux, locaux industriels, commerces)."
        ),
        "etapes_realisation": (
            "1. Étude technique et diagnostic sur site\n"
            "2. Établissement du plan de travaux et du devis détaillé\n"
            "3. Préparation et sécurisation du chantier\n"
            "4. Exécution des travaux par nos équipes certifiées\n"
            "5. Contrôle qualité et réception des travaux\n"
            "6. Remise des clés et garantie décennale"
        ),
        "prix_indicatif": Decimal("1200.00"),
        "unite": "m2",
        "ordre_affichage": 1,
    },
    {
        "nom": "Gestion Complète de Projets TCE",
        "slug": "gestion-projets-tce",
        "description_courte": "Coordination de tous les corps d'état, pilotage de chantier de A à Z pour vos projets BTP.",
        "description_complete": (
            "Tous Corps d'État (TCE) : H.D.A GLOBAL assure la coordination complète de votre projet BTP. "
            "Nous gérons et synchronisons l'ensemble des corps de métier (maçonnerie, plomberie, électricité, "
            "menuiserie, peinture, carrelage, climatisation) pour vous livrer un projet clé en main, "
            "dans les délais convenus et le budget maîtrisé.\n\n"
            "Notre rôle de maître d'œuvre vous garantit un interlocuteur unique tout au long du chantier."
        ),
        "etapes_realisation": (
            "1. Audit technique et étude de faisabilité\n"
            "2. Conception du planning général de chantier\n"
            "3. Consultation et sélection des sous-traitants\n"
            "4. Coordination quotidienne des équipes sur site\n"
            "5. Contrôle de la conformité et de la qualité\n"
            "6. Réception des travaux TCE et remise du dossier des ouvrages exécutés"
        ),
        "prix_indicatif": None,
        "unite": "forfait",
        "ordre_affichage": 2,
    },
    {
        "nom": "Aménagement Intérieur & Extérieur",
        "slug": "amenagement-interieur-exterieur",
        "description_courte": "Plâtrerie, peinture, revêtements sols/murs, faux plafonds, menuiserie, façades et espaces extérieurs.",
        "description_complete": (
            "Donnez vie à vos espaces avec les équipes d'aménagement H.D.A GLOBAL. "
            "Nous réalisons tous les travaux de finition intérieure (plâtrerie, enduits, peinture décorative, "
            "pose de carrelage, parquet, faux plafonds en plâtre ou PVC) et extérieure (ravalement de façades, "
            "isolation thermique par l'extérieur ITE, aménagements paysagers, terrasses, clôtures)."
        ),
        "etapes_realisation": (
            "1. Consultation et proposition de matériaux\n"
            "2. Préparation des supports (ragréage, nettoyage)\n"
            "3. Travaux de plâtrerie et doublage\n"
            "4. Pose des revêtements de sol et mural\n"
            "5. Peinture et finitions décoratives\n"
            "6. Contrôle final et livraison"
        ),
        "prix_indicatif": Decimal("350.00"),
        "unite": "m2",
        "ordre_affichage": 3,
    },
    {
        "nom": "Climatisation & Ventilation",
        "slug": "climatisation-ventilation",
        "description_courte": "Installation de systèmes split, gainable, cassette et VMC. Maintenance préventive et curative.",
        "description_complete": (
            "Confort thermique garanti par H.D.A GLOBAL. Nos techniciens certifiés installent "
            "et entretiennent tous types de systèmes de climatisation (split mural, gainable, cassette, "
            "VRV/VRF multi-split) et de ventilation (VMC simple et double flux, grilles de ventilation).\n\n"
            "Nous intervenons aussi bien en résidentiel qu'en tertiaire (bureaux, commerces, hôtels, cliniques)."
        ),
        "etapes_realisation": (
            "1. Audit thermique et dimensionnement\n"
            "2. Choix des équipements selon votre besoin\n"
            "3. Installation des unités intérieures et extérieures\n"
            "4. Tirage au vide et charge en fluide frigorigène\n"
            "5. Mise en service et paramétrage\n"
            "6. Formation utilisateur et contrat de maintenance"
        ),
        "prix_indicatif": Decimal("4500.00"),
        "unite": "unite",
        "ordre_affichage": 4,
    },
    {
        "nom": "Plomberie Générale",
        "slug": "plomberie-generale",
        "description_courte": "Réseaux sanitaires, évacuation, tuyauterie, robinetterie, chauffe-eau et dépannage urgent.",
        "description_complete": (
            "H.D.A GLOBAL assure l'installation, la rénovation et le dépannage de tous vos réseaux plomberie. "
            "Nos plombiers qualifiés maîtrisent les installations sanitaires (salles de bains, cuisines), "
            "les réseaux d'eau chaude et froide (cuivre, PPR, PER), les systèmes d'évacuation (PVC), "
            "la pose de chauffe-eau électriques et thermodynamiques, et le dépannage d'urgence."
        ),
        "etapes_realisation": (
            "1. Diagnostic de l'installation existante\n"
            "2. Plan de l'installation ou de la rénovation\n"
            "3. Fourniture et pose des équipements\n"
            "4. Essais d'étanchéité et mise en pression\n"
            "5. Raccordement et mise en service\n"
            "6. Test de l'ensemble du réseau"
        ),
        "prix_indicatif": Decimal("250.00"),
        "unite": "heure",
        "ordre_affichage": 5,
    },
    {
        "nom": "Services Divers sur Mesure",
        "slug": "services-divers-sur-mesure",
        "description_courte": "Électricité bâtiment, étanchéité, serrurerie, menuiserie aluminium et travaux spécifiques sur mesure.",
        "description_complete": (
            "H.D.A GLOBAL propose également une gamme de services spécialisés pour répondre à tous vos besoins BTP : "
            "électricité bâtiment (tableau électrique, câblage, prises, éclairage), "
            "étanchéité terrasses et toitures (membrane bitumineuse, résine polyuréthane), "
            "serrurerie métallique (portes, portails, escaliers, garde-corps), "
            "et menuiserie aluminium (fenêtres, portes-fenêtres, vérandas)."
        ),
        "etapes_realisation": (
            "1. Étude du besoin spécifique sur site\n"
            "2. Devis détaillé et choix des matériaux\n"
            "3. Planification et approvisionnement\n"
            "4. Réalisation par nos artisans spécialisés\n"
            "5. Contrôle et réception des travaux"
        ),
        "prix_indicatif": None,
        "unite": "forfait",
        "ordre_affichage": 6,
    },
]


class Command(BaseCommand):
    help = "Charge les données de démonstration H.D.A GLOBAL (services, clients, demandes, devis)"

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("=== Chargement des données de démonstration H.D.A GLOBAL ==="))

        self._creer_parametres()
        self._creer_superuser()
        self._creer_services()
        self._creer_clients_et_demandes()

        self.stdout.write(self.style.SUCCESS("\n=== [OK] Donnees de demonstration chargees avec succes ! ==="))
        self.stdout.write(self.style.SUCCESS("-> Admin : http://localhost:8000/admin/"))
        self.stdout.write(self.style.SUCCESS("-> Login : admin / admin123"))
        self.stdout.write(self.style.SUCCESS("-> Vitrine : http://localhost:8000/"))

    def _creer_parametres(self):
        from core.models import Parametres
        params, created = Parametres.objects.get_or_create(pk=1)
        if created:
            self.stdout.write("  [OK] Parametres entreprise crees")
        else:
            self.stdout.write("  -> Parametres entreprise : deja existants")

    def _creer_superuser(self):
        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser(
                username="admin",
                email="hda.global82@gmail.com",
                password="admin123",
                first_name="Administrateur",
                last_name="H.D.A GLOBAL",
            )
            self.stdout.write("  [OK] Superutilisateur admin cree (login: admin / admin123)")
        else:
            self.stdout.write("  -> Superutilisateur admin : deja existant")

    def _creer_services(self):
        from services.models import Service
        for data in SERVICES_HDA:
            service, created = Service.objects.get_or_create(
                slug=data["slug"],
                defaults=data,
            )
            if created:
                self.stdout.write(f"  [OK] Service cree : {service.nom}")
            else:
                self.stdout.write(f"  -> Service deja existant : {service.nom}")
            self._lier_image(service)

    # Images fournies dans media/services/images/ (convention : service_<n>_<nom>.jpg)
    IMAGES_SERVICES = {
        "construction-renovation": "service_1_construction.jpg",
        "gestion-projets-tce": "service_2_tce.jpg",
        "amenagement-interieur-exterieur": "service_3_amenagement.jpg",
        "climatisation-ventilation": "service_4_climatisation.jpg",
        "plomberie-generale": "service_5_plomberie.jpg",
        "services-divers-sur-mesure": "service_6_sur_mesure.jpg",
    }

    def _lier_image(self, service):
        """Associe l'image du service si le fichier existe et qu'aucune image n'est définie."""
        from django.conf import settings
        import os
        nom = self.IMAGES_SERVICES.get(service.slug)
        if not nom or service.image_principale:
            return
        if os.path.exists(os.path.join(settings.MEDIA_ROOT, "services", "images", nom)):
            service.image_principale = f"services/images/{nom}"
            service.save(update_fields=["image_principale"])
            self.stdout.write(f"  [OK] Image liee : {nom}")

    def _creer_clients_et_demandes(self):
        from clients.models import Client
        from services.models import Service
        from demandes.models import Demande, HistoriqueStatut
        from devis.models import Devis, LigneDevis
        from devis.pricing import recalculer_devis

        # Clients de démonstration
        clients_data = [
            {
                "nom_complet": "Mohammed El Alami",
                "email": "m.elalami@demo.ma",
                "telephone": "+212 661 123 456",
                "ville": "Casablanca",
                "adresse_principale": "Rue Ibn Battouta, Quartier Maarif, Casablanca",
            },
            {
                "nom_complet": "Fatima Zahra Benali",
                "email": "fz.benali@demo.ma",
                "telephone": "+212 654 789 012",
                "ville": "Mohammedia",
                "adresse_principale": "Avenue Hassan II, Mohammedia",
            },
            {
                "nom_complet": "Société IMMO ATLAS SARL",
                "email": "contact@immoatlas.ma",
                "telephone": "+212 522 345 678",
                "ville": "Casablanca",
                "adresse_principale": "Boulevard Zerktouni, Tour Atlas, Bureau 12, Casablanca",
            },
        ]

        clients = []
        for data in clients_data:
            client, created = Client.objects.get_or_create(
                email=data["email"], defaults=data
            )
            clients.append(client)
            if created:
                self.stdout.write(f"  [OK] Client cree : {client.nom_complet}")

        if Demande.objects.exists():
            self.stdout.write("  -> Demandes : deja existantes (skip)")
            return

        service_construction = Service.objects.get(slug="construction-renovation")
        service_tce = Service.objects.get(slug="gestion-projets-tce")
        service_clim = Service.objects.get(slug="climatisation-ventilation")

        # Demande 1 — En cours avec devis accepté
        d1 = Demande.objects.create(
            client=clients[0],
            service=service_construction,
            ville_chantier="Casablanca",
            adresse_chantier="Rue des Orangers, Ain Diab, Casablanca",
            description_besoin="Rénovation complète d'un appartement de 90m² : démolition cloisons, nouveau carrelage, peinture et plomberie.",
            surface_m2=Decimal("90"),
            statut=Demande.STATUT_EN_COURS,
        )
        HistoriqueStatut.objects.create(demande=d1, ancien_statut="nouvelle", nouveau_statut="en_etude", auteur="admin", commentaire="Prise en charge")
        HistoriqueStatut.objects.create(demande=d1, ancien_statut="en_etude", nouveau_statut="devis_envoye", auteur="admin", commentaire="Devis DEV-2026-0001 envoyé")
        HistoriqueStatut.objects.create(demande=d1, ancien_statut="devis_envoye", nouveau_statut="acceptee", auteur=clients[0].nom_complet, commentaire="Devis accepté par le client")
        HistoriqueStatut.objects.create(demande=d1, ancien_statut="acceptee", nouveau_statut="en_cours", auteur="admin", commentaire="Chantier démarré")

        dv1 = Devis.objects.create(
            demande=d1,
            statut=Devis.STATUT_ACCEPTE,
            taux_tva=Decimal("20"),
            conditions_reglement="30% versés à la commande (payé). Solde à la livraison.",
        )
        LigneDevis.objects.create(devis=dv1, designation="Démolition des cloisons existantes", quantite=Decimal("1"), unite="forfait", prix_unitaire_ht=Decimal("3500"), ordre=1)
        LigneDevis.objects.create(devis=dv1, designation="Pose carrelage 60×60 marbre blanc (fourni)", quantite=Decimal("90"), unite="m²", prix_unitaire_ht=Decimal("180"), ordre=2)
        LigneDevis.objects.create(devis=dv1, designation="Peinture intérieure (2 couches + sous-couche)", quantite=Decimal("200"), unite="m²", prix_unitaire_ht=Decimal("65"), ordre=3)
        LigneDevis.objects.create(devis=dv1, designation="Rénovation réseau plomberie appartement", quantite=Decimal("1"), unite="forfait", prix_unitaire_ht=Decimal("8000"), ordre=4)
        recalculer_devis(dv1)
        self.stdout.write(f"  [OK] Devis demo cree : {dv1.numero} (Total TTC : {dv1.total_ttc} MAD)")

        # Demande 2 — Devis envoyé en attente de réponse
        d2 = Demande.objects.create(
            client=clients[1],
            service=service_clim,
            ville_chantier="Mohammedia",
            adresse_chantier="Immeuble Al Amal, Appartement 5, Avenue des FAR, Mohammedia",
            description_besoin="Installation de 3 climatiseurs split pour appartement 3 pièces.",
            surface_m2=Decimal("75"),
            statut=Demande.STATUT_DEVIS_ENVOYE,
        )
        HistoriqueStatut.objects.create(demande=d2, ancien_statut="nouvelle", nouveau_statut="en_etude", auteur="admin")
        HistoriqueStatut.objects.create(demande=d2, ancien_statut="en_etude", nouveau_statut="devis_envoye", auteur="admin")

        dv2 = Devis.objects.create(
            demande=d2,
            statut=Devis.STATUT_ENVOYE,
            taux_tva=Decimal("20"),
        )
        LigneDevis.objects.create(devis=dv2, designation="Climatiseur split 12000 BTU (fourni + installé)", quantite=Decimal("3"), unite="unité", prix_unitaire_ht=Decimal("4500"), ordre=1)
        LigneDevis.objects.create(devis=dv2, designation="Câblage électrique dédié climatisation", quantite=Decimal("3"), unite="unité", prix_unitaire_ht=Decimal("600"), ordre=2)
        LigneDevis.objects.create(devis=dv2, designation="Percements et finitions murales", quantite=Decimal("3"), unite="unité", prix_unitaire_ht=Decimal("200"), ordre=3)
        recalculer_devis(dv2)
        self.stdout.write(f"  [OK] Devis demo cree : {dv2.numero} (Total TTC : {dv2.total_ttc} MAD)")

        # Demande 3 — Nouvelle (pas encore traitée)
        d3 = Demande.objects.create(
            client=clients[2],
            service=service_tce,
            ville_chantier="Casablanca",
            adresse_chantier="Zone Industrielle Ain Sebaa, Lot 45, Casablanca",
            description_besoin=(
                "Construction TCE d'un entrepôt de 500m² sur terrain nu. "
                "Fondations, dalle béton, structure métallique, bardage, électricité et plomberie industrielle."
            ),
            surface_m2=Decimal("500"),
            statut=Demande.STATUT_NOUVELLE,
        )
        self.stdout.write(f"  [OK] Demande demo creee : {d3.reference} (Nouvelle -- en attente de traitement)")

