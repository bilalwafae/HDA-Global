# ANALYSE COMPARATIVE DES DÉPÔTS & ÉTUDE PRÉALABLE — H.D.A GLOBAL

> **Projet** : Plateforme web H.D.A GLOBAL (Construction TCE – Aménagement)  
> **Contexte** : Projet de Fin d'Études (Génie Logiciel) — Délai : 8 jours  
> **Date** : 20 Octobre 2026  
> **Auteur** : Antigravity (Assistant Ingénierie & Architecture)

---

## 1. Synthèse de l'Analyse du Document de Spécification (`SPEC.md`)

### 1.1 Contexte & Problématique Métier
H.D.A GLOBAL est une entreprise BTP / TCE (Tous Corps d'État) et aménagement basée à Mohammedia (Beni Yakhlef) et intervenant également à Casablanca et dans plusieurs villes marocaines.
- **Problème identifié** : Les demandes de devis et d'interventions arrivent de manière informelle (appels téléphoniques, messages WhatsApp), entraînant des pertes d'informations, l'absence de traçabilité et des retards dans l'envoi des devis.
- **Objectif** : Mettre en place une application web robuste assurant :
  1. Une présence et vitrine professionnelle (présentation des 6 services TCE).
  2. Un tunnel de demande de devis simple et accessible pour les particuliers et professionnels.
  3. Un espace client sécurisé par lien magique / token (sans obligation de créer un mot de passe).
  4. Un back-office centralisé pour la gestion des demandes, le chiffrage des devis (génération PDF), la conversion client et la planification des interventions.

### 1.2 Stack Technique Imposée
- **Backend** : Python 3.12, Django 5 (architecture MVT : Django Templates, **pas de SPA**).
- **Base de données** : PostgreSQL 16 (pas de SQLite en production).
- **Back-office** : Django Admin personnalisé + Vues d'administration dédiées (Dashboard, Pipeline).
- **Frontend** : HTML5 sémantique, Tailwind CSS / Bootstrap 5 (mobile-first, responsive).
- **Génération PDF** : ReportLab ou WeasyPrint.
- **Conteneurisation** : Docker & Docker Compose (`web` + `db`).
- **Langue** : Français (architecture prête pour l'internationalisation i18n Arabe/Anglais).

---

## 2. Analyse de l'Identité Visuelle (`HDA.Fiche-Services.jpeg`) & Diagnostic REA

### 2.1 Éléments Extraits de la Fiche Commerciale
L'analyse de l'image publicitaire officielle (`HDA.Fiche-Services.jpeg`) fournit l'identité de marque et les données réelles :
- **Raison Sociale** : H.D.A GLOBAL — Construction TCE – Aménagement
- **Slogan** : *"Votre partenaire de confiance pour tous vos projets BTP"*
- **Contact Tél** : `+212 661103988`
- **Email Commercial** : `hda.global82@gmail.com`
- **Site Web actuel** : `https://hdaglobal.netlify.app/`
- **Charte Graphique** :
  - Bleu foncé / Navy BTP (`#1E3A8A` / `#0B3B60`) : Confiance, solidité, professionnalisme.
  - Bleu ciel / Cyan (`#3B82F6` / `#0284C7`) : Clarté, modernité.
  - Orange de sécurité BTP (`#F97316` / `#EA580C`) : Appels à l'action (CTA), devis, dynamisme.
  - Blanc et Gris clair (`#F8FAFC`) : Lisibilité optimale sur mobile.

### 2.2 Les 6 Services TCE Officiels (à intégrer en Fixtures)
1. **Construction & rénovation** (Gros œuvre, maçonnerie, réhabilitation, surélévation)
2. **Gestion complète de projets TCE** (Coordination tous corps d'état, suivi de chantier de A à Z)
3. **Aménagement intérieur et extérieur** (Plâtrerie, peinture, revêtements sols/murs, faux plafonds, menuiserie, façades)
4. **Climatisation & ventilation** (Installation split, gainable, VMC, maintenance)
5. **Plomberie générale** (Réseaux sanitaires, évacuation, tuyauterie, robinetterie, dépannage)
6. **Services divers sur mesure** (Électricité bâtiment, étanchéité, serrurerie, travaux spécifiques)

### 2.3 Diagnostic REA (Reverse-Engineering du site existant Netlify)
L'observation du bundle JavaScript déployé sur `https://hdaglobal.netlify.app/` a révélé :
- Il s'agit d'une SPA statique minimale propulsée par Vite/React.
- Le formulaire de contact repose sur EmailJS client-side (`service_8fd2g4s`), envoyant directement un email sans enregistrement en base de données.
- **Absence totale de persistance, de back-office, de calcul de devis, de suivi client ou de gestion d'interventions.**
- **Conclusion** : Le site existant n'est qu'une plaquette vitrine statique. Le projet Django à développer comble exactement cette lacune opérationnelle en fournissant un système d'information complet.

---

## 3. Analyse Critique des Dépôts GitHub Mentionnés

| Dépôt GitHub | Rôle suggéré dans SPEC | Technologies observées | Licence | Retenu pour clone direct ? | Patterns & Bonnes idées retenus |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`GodOfStrategy/ecommdev-platform`** | Structure Django modulaire | *Introuvable (404/privé)* | Inconnue | ❌ **Non** | Organisation modulaire Django classique (`services`, `clients`, `demandes`, `devis`, `interventions`, `core`). |
| **`invoicerr-app/invoicerr`** | Cycle devis -> facture, statuts, PDF | TypeScript, NestJS, Prisma, Next.js, React | **AGPL-3.0** | ❌ **Non** (incompatibilité stack + licence AGPL restrictive) | Cycle d'états d'un devis (`Brouillon`, `Envoyé`, `Accepté`, `Refusé`), lignes d'articles, génération PDF professionnelle. |
| **`TWN-Systems/summit`** | Portail client magic link | TypeScript, Next.js 15, Drizzle ORM | MIT | ❌ **Non** (stack Next.js/Node.js) | Authentification sans mot de passe via lien sécurisé / jeton unique UUID (`token_suivi`) pour le client. |
| **`kodlyft/fsm`** | Field service (demandes, planning) | Python (Frappe), ERPNext, Vue.js | MIT | ❌ **Non** (dépendance lourde à ERPNext/Frappe) | Modèle d'intervention BTP : date début/fin, affectation d'un chef d'équipe, liaison directe avec la demande et l'adresse chantier. |
| **`djm-1/QuotePilot`** | Calcul de prix backend + PDF | Python (FastAPI), React, Pinecone, LLM | Non spécifiée | ❌ **Non** (prototype IA orienté SaaS) | Règle de gestion : calcul déterministe strict côté serveur (Total HT = $\sum$, TVA configurable 20%, Total TTC). |

---

## 4. Réponse à la Question : "Peut-on cloner une application existante avec REA ?"

### Réponse directe : **NON, aucun des dépôts ne peut (ni ne doit) être cloné directement.**

Voici les justifications fondamentales :

1. **Incompatibilité Technique Majeure (Stack Imposée)** :
   - La spécification impose rigoureusement : **Python 3.12, Django 5 (architecture MVT avec templates serveur, AUCUNE SPA)** et PostgreSQL.
   - Les dépôts examinés utilisent des architectures radicalement différentes :
     - `invoicerr` est une SPA React / NestJS.
     - `summit` est une application Next.js / TypeScript.
     - `kodlyft/fsm` est une extension ERPNext basée sur le framework Frappe.
     - `QuotePilot` est un agent IA sous FastAPI / React.
   - Cloner l'un de ces projets violerait immédiatement la contrainte centrale de votre PFE.

2. **Contraintes Légales et Exigences Académiques (PFE)** :
   - Le dépôt `invoicerr` est sous licence **GNU AGPL-3.0**. Cloner ou incorporer son code imposerait la licence AGPL à l'ensemble du projet.
   - La spécification stipule expressément :
     > *"Ne pas copier-coller de code (licences, notamment AGPL). Réimplémenter les idées avec un code propre et original."*
   - Pour un Projet de Fin d'Études en Génie Logiciel, un jury évalue la conception propre, la maîtrise de l'architecture Django et la pertinence de la modélisation métier.

3. **Inadéquation Métier (BTP Marocain vs Outils Génériques)** :
   - Aucun de ces dépôts ne couvre le besoin d'une entreprise marocaine BTP/TCE :
     - Formulaire de demande de devis adapté aux chantiers (surface en m², photos de chantier, ville marocaine).
     - Tarification indicative en Dirhams marocains (MAD).
     - TVA marocaine à 20% configurable.
     - Prise en charge des adresses de chantier distinctes des coordonnées du client.

### Conclusion Opérationnelle : La Stratégie Gagnante
Plutôt qu'un clonage impossible et non conforme, la démarche méthodologique recommandée par la spécification consiste à :
1. **Adopter l'architecture Django 5 modulaire** en 6 applications distinctes (`core`, `services`, `clients`, `demandes`, `devis`, `interventions`).
2. **Implémenter le cycle de devis et la génération PDF** inspirés d'Invoicerr et QuotePilot, mais codés nativement avec les modèles Django et ReportLab/WeasyPrint.
3. **Mettre en place le portail de suivi client par jeton UUID sécurisé** inspiré du pattern de Summit.
4. **Intégrer le module d'intervention chantier léger** inspiré du modèle FSM de KodLyft.

Cette approche garantit un projet 100 % conforme à la spécification, élégant, démontrable sous Docker en moins de 8 jours, et valorisant pour votre soutenance de PFE.

