# SPEC — Plateforme web H.D.A GLOBAL (Construction TCE – Aménagement)

## 1. Contexte
H.D.A GLOBAL est une petite entreprise BTP basée à Mohammedia (Beni Yakhlef), Maroc.
Elle intervient aussi dans d'autres villes marocaines. Elle n'a pas de produits, seulement des services.
Aujourd'hui les demandes arrivent par WhatsApp et appels, sans suivi organisé.

Objectif : une application web qui (1) présente les services de façon professionnelle,
(2) permet à un visiteur de demander un devis, (3) donne à l'entreprise un back-office
pour gérer demandes, clients, devis et interventions de façon automatisée.

Projet de fin d'études (ingénierie génie logiciel). Délai : 8 jours. Priorité : une base propre,
fonctionnelle et démontrable, avec les fonctionnalités essentielles.

## 2. Stack imposée
- Python 3.12, Django 5 (templates Django, pas de SPA)
- PostgreSQL (pas SQLite)
- Django Admin activé et personnalisé pour le back-office de base
- Bootstrap 5 ou Tailwind pour l'UI (responsive, mobile-first)
- ReportLab ou WeasyPrint pour les PDF de devis
- Docker Compose (web + db) pour lancer le projet facilement
- Interface en français (i18n prête pour arabe/anglais plus tard)

## 3. Méthode de travail demandée
Outils : si l'outil REA (MCP de reverse engineering) est installé, l'utiliser uniquement pour observer
le comportement de sites ou applications publics et autorisés (structure des pages, parcours de demande de devis).
Pour les dépôts GitHub ci-dessous, le code source est déjà lisible : le lire directement, sans reverse engineering.
Ne pas analyser de logiciel propriétaire sans autorisation ; documenter seulement le comportement observable.

Étape A : analyser les dépôts de référence ci-dessous. Pour chacun, extraire la liste des
fonctionnalités et du modèle de données, puis écrire `docs/ANALYSE.md` (tableau :
fonctionnalité / dépôt source / retenue oui-non / pourquoi).
Étape B : concevoir l'architecture et le modèle de données (`docs/ARCHITECTURE.md`).
Étape B bis : générer l'application. Réimplémenter les idées avec un code propre et original.
Ne pas copier-coller de code (licences, notamment AGPL). Citer les dépôts dans `docs/REFERENCES.md`.
Étape C : données de démonstration (fixtures), tests de base, README d'installation.

Dépôts de référence (idées uniquement) :
- github.com/GodOfStrategy/ecommdev-platform : structure Django modulaire (services, clients, devis, factures)
- github.com/invoicerr-app/invoicerr : cycle devis -> facture, statuts, PDF, signature
- github.com/TWN-Systems/summit : portail client avec magic link
- github.com/kodlyft/fsm : field service (demandes, planning, suivi client)
- github.com/djm-1/QuotePilot : calcul de prix déterministe côté backend + PDF

## 4. Rôles
- Visiteur : non connecté, consulte les services, envoie une demande.
- Client : créé automatiquement à la première demande, suit ses demandes via un lien sécurisé (token / magic link par email), sans mot de passe.
- Admin (entreprise) : accès complet au back-office.

## 5. Fonctionnalités

### 5.1 Partie publique (MVP, priorité haute)
- Accueil : présentation de l'entreprise, services principaux, zones d'intervention, appel à l'action "Demander un devis".
- Page Services : cartes avec image, titre, description courte, prix indicatif ("à partir de X MAD / m²" ou "sur devis").
- Page détail d'un service : description complète, étapes de réalisation, galerie d'images, bouton "Demander ce service".
- Page À propos / Contact : présentation, téléphone, email, adresse (Mohammedia, Beni Yakhlef), carte, boutons WhatsApp et appel.
- Formulaire de demande de devis : service, nom, téléphone, email, ville, adresse du chantier, date souhaitée, surface (optionnelle), description, pièces jointes (photos). Validation côté serveur, protection anti-spam (honeypot ou captcha simple).
- Après envoi : page de confirmation avec numéro de demande + lien de suivi.

Services de départ (fixtures) :
1. Construction & rénovation
2. Gestion complète de projets TCE (Tous Corps d'État)
3. Aménagement intérieur et extérieur
4. Climatisation & ventilation
5. Plomberie générale
6. Services divers sur mesure

### 5.2 Espace client (priorité moyenne)
- Lien de suivi sécurisé : liste de ses demandes, statut actuel, historique, devis reçu (PDF), bouton Accepter / Refuser le devis.
- Possibilité de refaire une demande sans ressaisir ses informations.

### 5.3 Back-office entreprise (priorité haute)
- Tableau de bord : nombre de nouvelles demandes, demandes par statut, par ville, par service, derniers clients.
- CRUD Services (nom, description, image, prix indicatif, unité, actif/inactif, ordre d'affichage).
- Gestion des demandes : liste filtrable (statut, ville, service, date), détail, changement de statut, notes internes, historique des changements.
- Statuts : Nouvelle -> En étude -> Devis envoyé -> Acceptée -> Planifiée -> En cours -> Terminée (et Refusée / Annulée).
- Gestion des clients : fiche client, historique de ses demandes. Un visiteur devient client à sa première demande.
- Devis : création depuis une demande, lignes (désignation, quantité, unité, prix unitaire), calcul automatique HT / TVA (20 % configurable) / TTC, génération PDF avec logo et coordonnées, envoi par email, suivi (Brouillon / Envoyé / Accepté / Refusé).
- Planification simple : date de début/fin d'intervention, ville, équipe ou responsable assigné, calendrier ou liste.
- Paramètres : infos entreprise, logo, TVA, numérotation des devis (DEV-2026-0001), zones d'intervention.

### 5.4 Automatisations (priorité moyenne)
- Création automatique du client et du numéro de demande à l'envoi du formulaire.
- Email automatique au client (confirmation) et à l'admin (nouvelle demande).
- Email automatique au client quand le statut ou le devis change.
- Numérotation automatique des demandes et devis.
- Calcul automatique des totaux de devis (logique côté backend).

### 5.5 Hors périmètre (à mentionner comme perspectives)
Facturation et paiement en ligne, application mobile, signature électronique, assistant IA, notifications WhatsApp via API, gestion des stocks.

## 6. Modèle de données (proposition, à affiner)
- Service(id, nom, slug, description_courte, description, image, prix_indicatif, unite, actif, ordre)
- Client(id, nom, telephone, email unique, ville, adresse, created_at)
- Demande(id, reference, client, service, ville, adresse_chantier, date_souhaitee, surface, description, statut, token_suivi, created_at)
- PieceJointe(id, demande, fichier)
- HistoriqueStatut(id, demande, ancien_statut, nouveau_statut, note, date, auteur)
- Devis(id, numero, demande, statut, tva_taux, total_ht, total_tva, total_ttc, pdf, date_emission, validite)
- LigneDevis(id, devis, designation, quantite, unite, prix_unitaire, total)
- Intervention(id, demande, date_debut, date_fin, responsable, ville, notes)
- Parametres (singleton : infos entreprise, logo, TVA par défaut)
Index sur statut, ville, created_at. Contraintes d'intégrité et clés étrangères explicites.

## 7. Exigences non fonctionnelles
- Sécurité : CSRF, validation des uploads (type et taille), tokens de suivi non devinables, variables sensibles via .env, pas de secrets dans le dépôt.
- Design : propre, professionnel, couleurs bleu/orange inspirées de l'identité H.D.A GLOBAL, très lisible sur mobile.
- Code : apps Django séparées (services, clients, demandes, devis, interventions, core), commentaires utiles, README clair.
- Tests : tests unitaires sur le calcul des devis, la création auto du client et les changements de statut.

## 8. Livrables
1. Application fonctionnelle lançable avec `docker compose up`
2. Fixtures de démonstration (services, clients, demandes, devis d'exemple)
3. docs/ANALYSE.md, docs/ARCHITECTURE.md (avec diagrammes ER et cas d'utilisation en Mermaid), docs/REFERENCES.md
4. README avec installation, comptes de démo, captures d'écran

## 9. Ordre de développement
1. Setup Docker, Django, PostgreSQL, modèles, admin
2. Pages publiques : accueil, services, détail, contact
3. Formulaire de demande + création auto du client + emails
4. Back-office : dashboard, demandes, statuts, historique
5. Devis + PDF + envoi
6. Espace de suivi client (token)
7. Planification, paramètres, polish UI
8. Tests, fixtures, documentation

Commencer par l'étape A (analyse), puis demander validation de l'architecture avant de générer le code.
