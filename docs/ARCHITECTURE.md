# ARCHITECTURE TECHNIQUE & MODÈLE DE DONNÉES — H.D.A GLOBAL

> **Projet** : Plateforme Web H.D.A GLOBAL (Construction TCE – Aménagement)  
> **Contexte** : Projet de Fin d'Études (Génie Logiciel) — Délai : 8 jours  
> **Stack** : Python 3.12, Django 5 (MVT, templates serveur), PostgreSQL 16, Docker Compose, ReportLab, Tailwind / Bootstrap 5  
> **Livrable** : `docs/ARCHITECTURE.md` (Étape B)

---

## 1. Principes Architecturaux & Organisation Modulaire

L'application respecte rigoureusement le modèle architectural canonique **MVT (Modèle - Vue - Template)** de Django. Conformément aux spécifications, il n'y a aucune Single Page Application (SPA) cliente : le rendu HTML est généré côté serveur, garantissant un référencement (SEO) optimal pour le BTP, un temps de chargement ultra-rapide sur mobile, et une robustesse accrue.

Le projet est découpé en 6 applications Django spécialisées, indépendantes et hautement cohésives :

```
hda_project/
├── core/           # Pages institutionnelles (Accueil, Contact, À propos), Singleton Paramètres, Context Processors
├── services/       # Catalogue des 6 prestations TCE, gestion des réalisations et tarifs indicatifs
├── clients/        # Gestion des clients, déduplication par email, historique des demandes
├── demandes/       # Formulaire public de demande de devis, anti-spam, upload photos, token de suivi UUID4
├── devis/          # Chiffrage (lignes, sous-total HT, TVA 20%, TTC), moteur pricing.py, génération PDF ReportLab
└── interventions/  # Gestion des chantiers (FSM), planification, affectation d'équipes et chefs de chantier
```

---

## 2. Diagramme des Cas d'Utilisation (Rôles & Interactions)

```mermaid
flowchart LR
    subgraph Acteurs
        V["Visiteur"]
        C["Client"]
        A["Administrateur (Entreprise)"]
    end

    subgraph "Espace Public"
        UC1["Consulter la vitrine et les 6 services TCE"]
        UC2["Soumettre une demande de devis avec photos"]
        UC3["Recevoir email de confirmation + lien de suivi"]
    end

    subgraph "Portail Client (Token UUID)"
        UC4["Consulter l'état de sa demande en temps réel"]
        UC5["Télécharger le devis officiel en PDF"]
        UC6["Accepter ou Refuser le devis en 1 clic"]
        UC7["Déposer une nouvelle demande préremplie"]
    end

    subgraph "Back-Office Entreprise"
        UC8["Tableau de bord KPIs (statuts, villes, devis)"]
        UC9["Pipeline et qualification des demandes"]
        UC10["Édition des devis et calcul automatique HT/TVA/TTC"]
        UC11["Planification de chantier et affectation équipe"]
        UC12["Gestion du catalogue TCE et paramètres entreprise"]
    end

    V --> UC1
    V --> UC2
    UC2 --> UC3

    C --> UC4
    C --> UC5
    C --> UC6
    C --> UC7

    A --> UC8
    A --> UC9
    A --> UC10
    A --> UC11
    A --> UC12
```

---

## 3. Modèle de Données Conceptuel & Diagramme Entité-Relation (ER)

```mermaid
erDiagram
    PARAMETRES {
        int id PK
        string nom_entreprise
        string slogan
        string telephone
        string email_contact
        string adresse_siege
        string ville
        decimal tva_defaut
        string prefixe_devis
        string logo
    }

    SERVICE {
        int id PK
        string nom
        string slug UK
        string description_courte
        text description_complete
        string image_principale
        decimal prix_indicatif
        string unite
        boolean actif
        int ordre_affichage
        datetime created_at
    }

    CLIENT {
        int id PK
        string nom_complet
        string email UK
        string telephone
        string ville
        string adresse_principale
        datetime created_at
        datetime updated_at
    }

    DEMANDE {
        int id PK
        string reference UK
        uuid token_suivi UK
        int client_id FK
        int service_id FK
        string ville_chantier
        string adresse_chantier
        date date_souhaitee
        decimal surface_m2
        text description_besoin
        string statut
        text notes_internes
        datetime created_at
        datetime updated_at
    }

    PIECE_JOINTE {
        int id PK
        int demande_id FK
        string fichier
        string nom_original
        datetime uploaded_at
    }

    HISTORIQUE_STATUT {
        int id PK
        int demande_id FK
        string ancien_statut
        string nouveau_statut
        text commentaire
        string auteur
        datetime date_changement
    }

    DEVIS {
        int id PK
        string numero UK
        int demande_id FK
        string statut
        decimal sous_total_ht
        decimal taux_tva
        decimal montant_tva
        decimal total_ttc
        string fichier_pdf
        date date_emission
        date date_validite
        text conditions_reglement
        datetime created_at
        datetime updated_at
    }

    LIGNE_DEVIS {
        int id PK
        int devis_id FK
        string designation
        decimal quantite
        string unite
        decimal prix_unitaire_ht
        decimal total_ligne_ht
        int ordre
    }

    INTERVENTION {
        int id PK
        int demande_id FK
        date date_debut
        date date_fin
        string responsable_chantier
        string equipe_assignee
        string ville
        text instructions_techniques
        string statut_chantier
        datetime created_at
        datetime updated_at
    }

    CLIENT ||--o{ DEMANDE : "passe"
    SERVICE ||--o{ DEMANDE : "est concerne par"
    DEMANDE ||--o{ PIECE_JOINTE : "comporte"
    DEMANDE ||--o{ HISTORIQUE_STATUT : "trace"
    DEMANDE ||--o{ DEVIS : "donne lieu a"
    DEVIS ||--|{ LIGNE_DEVIS : "detaille"
    DEMANDE ||--o| INTERVENTION : "declenche"
```

---

## 4. Diagrammes d'États & Cycles de Vie

### 4.1 Cycle de Vie d'une Demande de Devis
```mermaid
stateDiagram-v2
    [*] --> Nouvelle : Formulaire visiteur validé
    Nouvelle --> En_Etude : Prise en charge par l'Admin
    En_Etude --> Devis_Envoye : Devis chiffré et transmis au client
    Devis_Envoye --> Acceptee : Client accepte via son lien de suivi
    Devis_Envoye --> Refusee : Client refuse le devis
    Acceptee --> Planifiee : Intervention programmée avec date & équipe
    Planifiee --> En_Cours : Démarrage des travaux sur le chantier
    En_Cours --> Terminee : Réception des travaux et livraison
    
    Nouvelle --> Annulee : Demande invalide ou sans suite
    En_Etude --> Annulee : Abandon du projet
    Refusee --> [*]
    Annulee --> [*]
    Terminee --> [*]
```

### 4.2 Cycle de Vie d'un Devis
```mermaid
stateDiagram-v2
    [*] --> Brouillon : Création et saisie des lignes
    Brouillon --> Envoyé : Validation Admin & envoi email client
    Envoyé --> Accepté : Validation client sur son portail
    Envoyé --> Refusé : Rejet client avec motif
    Envoyé --> Périmé : Dépassement date validité (ex: 30 jours)
    Accepté --> [*]
    Refusé --> [*]
    Périmé --> [*]
```

---

## 5. Plan de Routage des URLs & Vues (Django)

| URL Pattern | Vue (App) | Rôle & Description |
| :--- | :--- | :--- |
| **Vitrine Publique** | | |
| `/` | `core:home` | Accueil : présentation entreprise, 6 services TCE, réalisations, CTA devis |
| `/services/` | `services:list` | Catalogue complet des services avec filtres et prix indicatifs au m² |
| `/services/<slug:slug>/` | `services:detail` | Fiche détaillée d'un service (étapes, galerie, formulaire contextuel) |
| `/a-propos/` | `core:about` | Présentation H.D.A GLOBAL, histoire, valeurs, zones d'intervention |
| `/contact/` | `core:contact` | Coordonnées, adresses Casablanca/Mohammedia, carte, WhatsApp direct |
| **Tunnel Demande de Devis** | | |
| `/devis/demande/` | `demandes:create` | Formulaire de demande (avec upload photos, honeypot anti-spam) |
| `/devis/confirmation/<str:reference>/` | `demandes:confirmation` | Page post-soumission avec numéro de référence et récapitulatif |
| **Portail Client (Token UUID)** | | |
| `/suivi/<uuid:token>/` | `demandes:suivi` | Dashboard client sans mot de passe : statut, historique, devis |
| `/suivi/<uuid:token>/devis/<int:devis_id>/pdf/` | `devis:telecharger_pdf` | Téléchargement sécurisé du PDF officiel ReportLab |
| `/suivi/<uuid:token>/devis/<int:devis_id>/action/`| `devis:client_action` | Endpoint POST pour Accepter ou Refuser le devis |
| `/suivi/<uuid:token>/nouvelle-demande/` | `demandes:client_nouvelle` | Formulaire prérempli pour renouveler une demande |
| **Back-Office Entreprise** | | |
| `/admin/` | `admin:index` | Interface d'administration Django hautement personnalisée |
| `/admin/dashboard/` | `core:admin_dashboard` | Tableau de bord analytique (KPIs, graphiques d'activité, métriques) |
| `/admin/demandes/<int:pk>/` | `demandes:admin_detail` | Vue détaillée avec aperçu des photos du chantier et changement d'état |
| `/admin/devis/creer/<int:demande_id>/` | `devis:admin_create` | Chiffreur interactif de devis avec ajout dynamique de lignes |
| `/admin/devis/<int:pk>/envoyer/` | `devis:admin_send` | Déclenchement de l'envoi email avec PDF joint et lien magique |
| `/admin/interventions/planning/` | `interventions:planning`| Vue calendrier/liste des chantiers planifiés et équipes affectées |

---

## 6. Moteur de Calcul & Règles Métier Financières

Inspiré de l'algorithme déterministe extrait de `QuotePilot`, le calcul des devis est encapsulé dans `devis/services/pricing.py` :

1. **Règle d'arrondi monétaire** :
   Tous les montants sont manipulés via le type Python standard `Decimal` avec quantification à 2 décimales et arrondi `ROUND_HALF_UP`.
2. **Calcul unitaire de chaque ligne** :
   $$\text{Total Ligne HT} = \text{Quantité} \times \text{Prix Unitaire HT}$$
3. **Sous-Total Hors Taxes** :
   $$\text{Sous-Total HT} = \sum_{i=1}^{n} \text{Total Ligne HT}_i$$
4. **Montant de la TVA (20 % par défaut au Maroc)** :
   $$\text{Montant TVA} = \text{Sous-Total HT} \times \left(\frac{\text{Taux TVA}}{100}\right)$$
5. **Total Toutes Taxes Comprises (TTC)** :
   $$\text{Total TTC} = \text{Sous-Total HT} + \text{Montant TVA}$$

---

## 7. Moteur de Génération PDF (ReportLab)

Le générateur est implémenté dans `devis/services/pdf.py` selon les standards graphiques de H.D.A GLOBAL :
- **Format** : A4 vertical, marges de 1.5 cm.
- **En-tête** : Logo vectoriel / haute résolution de H.D.A GLOBAL, coordonnées complètes (Beni Yakhlef / Casablanca, téléphone, email, IF, ICE, RC).
- **Bloc Destinataire** : Nom du client, adresse du chantier, date d'émission, date limite de validité (30 jours).
- **Tableau des prestations** : Colonnes stylisées (N°, Désignation des travaux, Unité, Quantité, Prix unitaire HT en MAD, Total HT en MAD) avec alternance de couleurs de lignes (`#F8FAFC`).
- **Bloc Récapitulatif Financier** : Total HT, TVA 20 %, Total TTC en Dirhams marocains (MAD).
- **Pied de page légal** : Mentions de garantie décennale BTP, conditions de règlement et signature.

---

## 8. Conteneurisation & Environnement Docker

Le déploiement local et la démonstration sont orchestrés via Docker Compose :
- **Service `db`** : Image officielle `postgres:16-alpine` avec volume persistant `postgres_data` et variables d'environnement sécurisées.
- **Service `web`** : Image basée sur `python:3.12-slim`, installation des dépendances système (compilateur C, bibliothèques d'images pour ReportLab/Pillow), exécution automatique des migrations, collecte des fichiers statiques et lancement du serveur Gunicorn / Django dev server.
- **Fixtures automatiques** : Commande Django de peuplement (`python manage.py load_demo_data`) créant les 6 services TCE officiels, les paramètres d'entreprise, un compte administrateur et un jeu de demandes/devis de démonstration.

