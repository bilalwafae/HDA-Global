# 🏗️ Plateforme Web H.D.A GLOBAL (Construction TCE – Aménagement)

> **Application Web d'Entreprise BTP & Système de Devis en Ligne**  
> Développée dans le cadre d'un **Projet de Fin d'Études (Ingénierie Génie Logiciel)**  
> **Entreprise cible :** H.D.A GLOBAL SARL (Beni Yakhlef, Mohammedia & Casablanca, Maroc)

---

## 🌟 Présentation du Projet

H.D.A GLOBAL est une entreprise marocaine spécialisée dans les travaux de bâtiment Tous Corps d'État (TCE), la rénovation, l'aménagement intérieur/extérieur, la climatisation et la plomberie.

Cette plateforme web moderne répond à trois objectifs fondamentaux :
1. **Vitrine Professionnelle** : Présentation claire et élégante des 6 prestations de l'entreprise avec tarification indicative en Dirhams (MAD).
2. **Tunnel de Devis Simplifié** : Formulaire accessible pour les particuliers et professionnels avec upload de photos de chantier et géolocalisation.
3. **Espace Client Sécurisé Sans Mot de Passe** : Suivi en temps réel de l'avancement via un **lien magique (Token UUID4)**, téléchargement de devis PDF certifiés et validation/refus en 1 clic.
4. **Back-Office d'Administration Centralisé** : Gestion des demandes par pipeline d'états, chiffrage déterministe (HT, TVA 20%, TTC), génération PDF ReportLab et planification des interventions d'équipes sur chantier.

---

## 🛠️ Stack Technique Imposée

| Composant | Technologie |
| :--- | :--- |
| **Backend** | Python 3.12, Django 5.1 (Architecture MVT native, pas de SPA) |
| **Base de données** | PostgreSQL 16 (persistant via volume Docker) |
| **Génération PDF** | ReportLab 4.2 (Devis A4 officiel avec charte graphique BTP) |
| **Design & UI** | Bootstrap 5.3 + Bootstrap Icons + Custom CSS BTP (Mobile-First) |
| **Conteneurisation** | Docker & Docker Compose (`web` + `db`) |
| **Internationalisation** | Français par défaut, prêt pour i18n (Arabe / Anglais) |

---

## 🚀 Démarrage Rapide avec Docker Compose

L'intégralité de la plateforme (base de données, migrations, fichiers statiques et données de démonstration) démarre en une seule commande :

```bash
docker compose up --build
```

Une fois les conteneurs démarrés :
- 🌐 **Site Public & Vitrine :** [http://localhost:8000/](http://localhost:8000/)
- 📋 **Formulaire de Devis :** [http://localhost:8000/demande/](http://localhost:8000/demande/)
- 🔒 **Back-Office Administrateur :** [http://localhost:8000/admin/](http://localhost:8000/admin/)
- 📅 **Planning des Chantiers :** [http://localhost:8000/interventions/planning/](http://localhost:8000/interventions/planning/)

---

## 🔑 Identifiants des Comptes de Démonstration

Les fixtures automatiques (`python manage.py load_demo_data`) initialisent automatiquement les comptes et données d'exemple :

### 1. Compte Super-Administrateur (Back-Office)
- **Identifiant :** `admin`
- **Mot de passe :** `admin123`
- **Email :** `hda.global82@gmail.com`

### 2. Dossiers Clients Pré-chargés pour les Tests
Chaque client a reçu un lien de suivi sécurisé sans mot de passe :
- **Client 1 :** Mohammed El Alami (Casablanca) — Demande `DEM-2026-0001` (Rénovation 90 m², Devis accepté `DEV-2026-0001` de **25 908 MAD TTC**).
- **Client 2 :** Fatima Zahra Benali (Mohammedia) — Demande `DEM-2026-0002` (Climatisation 3 splits, Devis envoyé `DEV-2026-0002` en attente).
- **Client 3 :** IMMO ATLAS SARL (Casablanca) — Demande `DEM-2026-0003` (Projet TCE 500 m², statut *Nouvelle*).

---

## 📂 Organisation Modulaire du Code Django

```
d:/HDA-Global/
├── core/                # Pages vitrine (Accueil, À propos, Contact), Singleton Paramètres
├── services/            # Catalogue des 6 prestations TCE, fiches de réalisations
├── clients/             # Répertoire client, déduplication par email unique
├── demandes/            # Formulaire devis, upload photos, token UUID, gestion emails
│   └── management/commands/load_demo_data.py  # Fixtures complètes
├── devis/               # Chiffrage déterministe pricing.py, générateur PDF ReportLab
├── interventions/       # Planification chantier (FSM), équipes et dates
├── templates/           # Templates Django HTML5 / Bootstrap 5 responsive
├── static/              # Feuilles de styles CSS BTP et JavaScript
├── docs/                # Documentation PFE (ANALYSE.md, ARCHITECTURE.md, REFERENCES.md)
├── Dockerfile           # Image conteneur Python 3.12
└── docker-compose.yml   # Orchestration web (Django) + db (PostgreSQL 16)
```

---

## 🧪 Lancement des Tests Unitaires

Pour exécuter la suite de tests unitaires (calcul financier, déduplication client, workflow statuts) :

```bash
docker compose exec web python manage.py test
```
*Ou en local :*
```bash
python manage.py test
```

---

## 📄 Documentation du Projet
- 📊 [docs/ANALYSE.md](docs/ANALYSE.md) : Analyse comparative des dépôts open source de référence et diagnostic du site existant Netlify.
- 📐 [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) : Modèle conceptuel (Mermaid ER), diagrammes d'états, règles de chiffrage et routage.
- 📚 [docs/REFERENCES.md](docs/REFERENCES.md) : Citations et respect des licences open source.


## Mise en production (HTTPS)
Voir `docs/DEPLOIEMENT.md` : `docker-compose.prod.yml` (gunicorn + PostgreSQL + Caddy/HTTPS automatique), `Caddyfile`, `.env.prod.example`.
