# Documentation technique : tests, gestion des erreurs et gestion des risques
**Projet : plateforme web H.D.A GLOBAL — Construction TCE & Aménagement**
**Version :** 2.0 · **Mise à jour :** octobre 2026 · **Auteur :** équipe d'ingénierie H.D.A GLOBAL (révision des risques : Claude)

---

## Sommaire
0. [Synthèse](#0-synthèse)
1. [Stratégie et inventaire des tests (59 tests)](#1-stratégie-et-inventaire-des-tests-59-tests)
2. [Gestion des erreurs et résilience](#2-gestion-des-erreurs-et-résilience)
3. [Registre des risques](#3-registre-des-risques)
   - [3.1 Méthode de cotation](#31-méthode-de-cotation)
   - [3.2 Matrice de criticité](#32-matrice-de-criticité)
   - [3.3 Risques de sécurité (SEC)](#33-risques-de-sécurité-sec)
   - [3.4 Risques liés à l'IA (IA)](#34-risques-liés-à-lia-ia)
   - [3.5 Risques métier et financiers (MET)](#35-risques-métier-et-financiers-met)
   - [3.6 Risques d'infrastructure et de disponibilité (INF)](#36-risques-dinfrastructure-et-de-disponibilité-inf)
4. [Plan d'actions priorisé](#4-plan-dactions-priorisé)
5. [Check-list pré-déploiement](#5-check-list-pré-déploiement)
6. [Annexe : écarts constatés entre documentation et code](#6-annexe--écarts-constatés-entre-documentation-et-code)

---

## 0. Synthèse

| Indicateur | Valeur |
|---|---|
| Tests automatisés | **59** (100 % de réussite) : intégration, unitaires purs, flux devis, assistant IA |
| Risques recensés | **33** (dont 13 critiques, 15 modérés, 5 faibles) |
| Risques déjà maîtrisés | 12 · partiellement : 12 · **ouverts : 9** |
| Principe de conception | « l'IA propose, le moteur calcule, l'humain valide » |

**Les 5 points à traiter avant la mise en production :**
1. Remplacer toutes les clés et mots de passe partagés (Gmail, OpenRouter) et ne jamais publier le `.env` (**R-SEC-05**).
2. Rendre les PDF de devis non devinables / protégés (**R-SEC-06**).
3. Renseigner les vraies mentions légales (ICE, IF, RC) dans les paramètres : le PDF affiche encore des zéros (**R-MET-05**).
4. Remplacer le CDN Tailwind « play » par une feuille de style compilée (**R-INF-04**).
5. Calibrer le catalogue de prix avec la vraie grille de l'entreprise (**R-MET-06**).

---

## 1. Stratégie et inventaire des tests (59 tests)

### 1.1 Vue d'ensemble

| Suite | Fichiers | Tests | Particularité |
|---|---|:---:|---|
| **A. Intégration & base de données** | `clients/`, `core/`, `demandes/`, `devis/tests.py` | 12 | Base de test Django, URL, gabarits, workflow |
| **B. Unitaires purs (moteur, IA devis, PDF, vision)** | `devis/tests_auto.py` | 24 | Sans réseau ; aucune API réelle appelée |
| **C. Flux « Acceptée → devis → envoi »** | `devis/tests_workflow.py` | 4 | Email simulé (locmem), pièce jointe PDF vérifiée |
| **D. Assistant IA admin** | `assistant/tests.py` | 19 | Modèle simulé : outils, garde-fous, bascule de modèle |
| **Total** | | **59** | 0 échec, 0 erreur |

```
            ┌───────────────────────────────────┐
            │  Vues / accès (5) + flux devis (4)│
            ├───────────────────────────────────┤
            │  Intégration base de données (7)  │
            ├───────────────────────────────────┤
            │  Assistant IA : outils + garde-fous (19) │
            ├───────────────────────────────────┤
            │  Unitaires purs : moteur/PDF/IA (24)     │
            └───────────────────────────────────┘
```

### 1.2 Suite A — Intégration et base de données (12 tests)

Fichiers : `clients/tests.py`, `core/tests.py`, `demandes/tests.py`, `devis/tests.py`.

| Application | Classe de Test | Méthode | Objectif & Assertions Clés |
|---|---|---|---|
| **clients** | `ClientAutoCreationTests` | `test_creation_nouveau_client` | Vérifie la création automatique d'un client lors d'un devis public avec normalisation des champs (`assertTrue(created)`). |
| **clients** | `ClientAutoCreationTests` | `test_deduplication_client_existant` | Vérifie que la détection d'un email existant (même en casse mixte `KARIM.TAZI@...`) met à jour les coordonnées sans créer de doublon (`assertEqual(count, 1)`). |
| **core** | `CoreViewsTest` | `test_home_page` | Valide le code HTTP 200 de la page d'accueil et la présence de la marque "H.D.A GLOBAL". |
| **core** | `CoreViewsTest` | `test_about_page` | Valide le rendu de la page « À propos » et son code 200. |
| **core** | `CoreViewsTest` | `test_contact_page` | Valide la page contact et l'intégration du formulaire public (code 200). |
| **core** | `CoreViewsTest` | `test_dashboard_login_required` | Vérifie le blocage d'un visiteur anonyme tentant d'accéder au dashboard exécutif (Redirection 302 vers `/admin/login/`). |
| **core** | `CoreViewsTest` | `test_dashboard_staff_access` | Vérifie l'accès autorisé pour un profil `is_staff=True` (code 200) et la présence des SVG des graphiques donuts (`donut-metiers`, `donut-pipeline`). |
| **demandes** | `DemandeWorkflowTests` | `test_generation_reference_automatique` | Valide l'attribution déterministe de la référence séquentielle `DEM-YYYY-XXXX` et l'affectation d'un `token_suivi` UUID4 non nul. |
| **demandes** | `DemandeWorkflowTests` | `test_changement_statut_et_historique` | Contrôle la machine à états : le passage de `nouvelle` à `en_etude` crée un enregistrement d'audit `HistoriqueStatut` traçant auteur et date. |
| **devis** | `PricingEngineTests` | `test_arrondi_monnaie` | Vérifie que l'arrondi monétaire utilise strictement `ROUND_HALF_UP` à 2 décimales (ex: `12.345` → `12.35`, `12.344` → `12.34`). |
| **devis** | `PricingEngineTests` | `test_calculer_total_ligne` | Valide le produit unitaire Quantité × Prix Unitaire HT avec le type `Decimal`. |
| **devis** | `PricingEngineTests` | `test_recalculer_devis_complet` | Valide l'intégrité de la cascade de calcul : sous-total HT, TVA 20.00% et total TTC sur plusieurs lignes de prestations. |

---

---

### 1.3 Suite B — Unitaires purs : moteur déterministe, IA devis, PDF (20 tests)

Fichier : `devis/tests_auto.py`.

Ces tests s'exécutent **sans base de données ni réseau** pour une vitesse et une isolation maximales :

| Classe de Test | Méthode | Rôle & Scénario Validé |
|---|---|---|
| **DetectionFamilleTests** | `test_detection_famille_par_service` | Correspondance exacte entre le service sélectionné et la famille de chiffrage (Climatisation, Plomberie, Aménagement, TCE, etc.). |
| **DetectionFamilleTests** | `test_detection_famille_par_description` | Capacité de secours : si le service est "Autre" ou vide, les mots-clés dans la description client aiguillent vers la bonne famille. |
| **DetectionFamilleTests** | `test_coherence_catalogue_formules` | Intégrité référentielle statique : chaque code poste dans `FORMULES` existe dans le `CATALOGUE`, a un prix > 0 et un mode valide. |
| **TotauxDeterministesTests** | `test_totaux_deterministes_85m2_climatisation_casablanca` | Chiffrage exact d'un cas réel (85 m² à Casablanca = 37 200.00 MAD HT / 7 440.00 TVA / 44 640.00 MAD TTC). |
| **TotauxDeterministesTests** | `test_totaux_via_pricing_pur` | `calculer_totaux()` accepte indifféremment des tuples, dicts ou objets tout en garantissant des instances `Decimal`. |
| **ReglesMoteurTests** | `test_surface_manquante_confiance_faible` | Si la surface est absente, bascule le niveau de confiance en `faible` et génère une alerte explicite à destination de l'artisan. |
| **ReglesMoteurTests** | `test_extraction_surface_proposition_confiance` | Extraction automatique d'une surface mentionnée dans le texte libre (« 85 m2 ») via expression régulière avec alerte de confirmation. |
| **ReglesMoteurTests** | `test_frais_deplacement_hors_zone` | Application automatique du forfait de déplacement (`DEP-VILLE`) dès lors que le chantier est hors du périmètre direct Mohammedia/Casablanca (ex : Rabat). |
| **ReglesMoteurTests** | `test_ville_autre_confiance_faible` | Gestion de l'inconnu géographique : abaissement de confiance si la commune n'est pas reconnue. |
| **ValidationIATests** | `test_ia_ne_peut_pas_injecter_prix_ni_poste_inconnu` | **Sécurité critique (Sandbox IA)** : toute tentative d'injection de prix unitaire ou de codes inventés par le LLM est purgée. Seuls les prix du catalogue local font foi. |
| **ValidationIATests** | `test_json_invalide_sans_effet` | Robustesse face aux réponses tronquées, malformées ou accompagnées de texte parasite émises par l'API de langage. |
| **ValidationIATests** | `test_extraction_surface_regex` | Tolérance aux variantes orthographiques (`85 m2`, `90 M2`, `12,5 m²`) et sélection de la surface principale la plus pertinente. |
| **ValidationIATests** | `test_postes_ia_utilises` | Conservation des postes proposés par l'IA uniquement s'ils sont homologués au catalogue ; repli automatique sur la formule par défaut sinon. |
| **MontantEnLettresTests** | `test_exemples_recap` | Conversion légale en lettres selon la grammaire française : "quatre-vingt mille dirhams (arrêté)", "deux cents dirhams", "un million de dirhams". |
| **MontantEnLettresTests** | `test_autres_montants_en_lettres` | Validation des montants complexes avec centimes et accords pluriels ("un million deux cents mille dirhams..."). |
| **PDFTests** | `test_construire_pdf_pur` | Génération binaire du flux PDF ReportLab (`%PDF-`), validant la conformité du buffer et sa taille minimale. |
| **PDFTests** | `test_construire_pdf_avec_logo_inexistant_ne_crash_pas` | Résilience : si le fichier du logo est introuvable sur le disque du serveur, le PDF se compile sans planter en sautant l'en-tête graphique. |
| **FormatEtFiltreTests** | `test_fmt_mad` | Formatage comptable marocain avec espace insécable et virgule décimale (`1 085 400,00`). |
| **FormatEtFiltreTests** | `test_filtrer_notes_client` | **Secret professionnel** : exclusion automatique des balises `[IA]`, `• Réf. interne` et notes de marge avant génération du PDF destiné au client. |
| **FormatEtFiltreTests** | `test_charger_polices_repli_generic` | Repli transparent sur la fonte Helvetica standard en l'absence de fichiers TrueType personnalisés. |

---

**Complément (4 tests de la suite B ajoutés depuis la version 1.0) — extension « photos + vision » :**

| Classe | Méthode | Rôle |
|---|---|---|
| **VisionPhotoTests** | `test_vision_valide_sortie_et_borne` | La sortie de l'analyse de photos est validée et bornée (taille, nombre d'éléments). |
| **VisionPhotoTests** | `test_vision_sortie_invalide` | Une sortie vision malformée est ignorée sans erreur. |
| **VisionPhotoTests** | `test_fusion_vision_dans_resultat_ia` | Les observations des photos enrichissent le brouillon sans jamais modifier un prix. |
| **VisionPhotoTests** | `test_alertes_photo_trouvent_le_moteur` | Les alertes issues des photos remontent dans les notes internes du devis. |

### 1.4 Suite C — Flux « demande acceptée → devis automatique → envoi au client » (4 tests)

Fichier : `devis/tests_workflow.py`.

| Méthode | Scénario validé |
|---|---|
| `test_acceptation_genere_devis_brouillon_avec_pdf_sans_envoyer` | Le passage à « Acceptée » crée **un** devis brouillon avec lignes et PDF ; **aucun email** n'est envoyé ; un second passage à « Acceptée » ne crée pas de doublon. |
| `test_action_admin_groupee` | L'action groupée de l'admin accepte la demande, génère le devis et affiche le lien « Envoyer au client ». |
| `test_envoi_au_client_avec_pdf_joint` | L'email part vers le client, avec le **PDF en pièce jointe** (`%PDF`), le logo incorporé, une version HTML ; statuts devis = « Envoyé », demande = « Devis envoyé ». |
| `test_echec_smtp_ne_change_pas_le_statut` | Si le SMTP échoue : message d'erreur clair à l'administrateur, **statuts inchangés** (le devis n'est pas faussement marqué envoyé). |

### 1.5 Suite D — Assistant IA de l'administration (19 tests)

Fichier : `assistant/tests.py` (jeu de données fabriqué : 2 services, 2 clients, 4 interventions, 4 devis).

| Groupe | Tests | Ce qui est garanti |
|---|:---:|---|
| **OutilsTests** | 8 | Chiffres exacts : interventions par ville (insensible à la casse et aux accents), par ville et période, par client (nombre, devis acceptés, montant TTC), client ambigu ou inconnu, classement des services (le plus demandé / le plus rentable, devis « envoyé » exclu du chiffre d'affaires), chiffre d'affaires par période et par mois, erreurs lisibles (date invalide, statut inconnu, période inversée), recherche de demande. |
| **VerificationNombresTests** | 3 | Un nombre présent dans les données est accepté ; un nombre inventé est détecté ; les puces « 1. 2. » sont ignorées. |
| **BoucleIATests** | 6 | Réponse exacte acceptée ; **réponse avec nombre halluciné remplacée par les données de la base** ; question hors sujet avec chiffres → phrase de refus fixe ; bascule sur le modèle suivant en cas de quota (HTTP 429) ; sans clé : pas de crash, questions rapides disponibles ; panne totale : message clair. |
| **VuesTests** | 2 | Accès réservé au personnel (redirection si anonyme) ; page de chat et questions rapides fonctionnelles. |

### 1.6 Commandes d'exécution

```bash
python manage.py test                        # tout le banc d'essai (59 tests)
python manage.py test devis.tests_auto       # moteur de devis / PDF / IA / vision (24)
python manage.py test devis.tests_workflow   # flux acceptation → envoi (4)
python manage.py test assistant              # assistant IA (19)
python manage.py test clients core demandes devis   # intégration (12 + suites devis)
```

---

## 2. Gestion des erreurs et résilience

### 2.1 Philosophie « Non-Bloquante » (Fail-Safe)

Dans le secteur BTP, l'acquisition d'un prospect ne doit subir **aucun point de rupture technique**. Un échec de composant auxiliaire (IA indisponible, serveur SMTP ralenti, quota dépassé) ne doit en aucun cas empêcher l'enregistrement d'une demande de travaux.

```
Soumission Client
       │
       ├─► 1. Sauvegarde Client & Demande en base ──► [OBLIGATOIRE - Transactionnelle]
       │
       ├─► 2. Sauvegarde Pièces Jointes ───────────► [Tolérance aux fichiers invalides]
       │
       ├─► 3. Notifications Emails ───────────────► [fail_silently = True]
       │
       └─► 4. Pré-génération Devis Auto (IA) ──────► [try / except silencieux]
               • En cas d'erreur IA ───────────────► Repli sur Regex + Catalogue Local
               • En cas d'erreur Moteur ───────────► Demande reste créée, devis créé à la main
```

> **Mise à jour v2.0 :** l'envoi du devis au client n'est PLUS « silencieux » : si l'email échoue, l'administrateur voit l'erreur et le statut ne change pas (voir 2.3). Les emails de confirmation à la soumission restent non bloquants pour le client.

### 2.2 Validation des formulaires et barrières anti-intrusion

1. **Honeypot Anti-Spam (`clean_website`)** :
   - Un champ HTML caché `website` (invisible pour les humains) est inséré dans tous les formulaires publics.
   - Les bots d'indexation le remplissent systématiquement.
   - Si renseigné, le contrôleur intercepte la soumission et simule un succès sans écrire en base de données ni solliciter les serveurs email.
2. **Normalisation téléphonique (`clean_telephone`)** :
   - Suppression des séparateurs (espaces, tirets, points) pour vérifier la présence d'au moins 8 chiffres.
   - Compatible avec les formats marocains (`06...`, `05...`, `+212...`).
3. **Sécurité des uploads de fichiers (`PieceJointe`)** :
   - **Taille maximale** : bridée à 10 Mo par fichier (`FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024`).
   - **Types MIME autorisés** : uniquement `image/jpeg`, `image/png`, `image/webp` et `application/pdf`. Tout autre fichier est rejeté silencieusement.
4. **Validation de consistance textuelle (`clean_description_besoin`)** :
   - Exigence d'au moins 20 caractères pour éliminer les soumissions accidentelles ou vides.

### 2.3 Isolation des dépendances externes (IA et messagerie)

1. **IA de chiffrage (`devis/ai.py`, `devis/vision.py`)** : appel API par `urllib` (aucune dépendance lourde), délai maximal borné, JSON validé, **aucun prix accepté de l'IA** (seuls les prix du `CATALOGUE` local comptent). Sans clé ou en cas d'erreur : repli sur le moteur local (regex + catalogue).
2. **Assistant IA admin (`assistant/`)** :
   - le modèle n'accède pas à la base : il appelle 7 **outils** qui calculent tous les chiffres ;
   - température 0 ; consignes strictes (réponses uniquement d'après les outils, refus du hors-sujet, précision de la période et des définitions) ;
   - **contrôle automatique des nombres** : toute valeur absente des résultats des outils fait remplacer la réponse par les données brutes ;
   - bascule entre modèles (liste `OPENROUTER_MODELS`), limite de 15 questions/minute/utilisateur, accès réservé au personnel ;
   - sans IA : 5 « questions rapides » calculées directement.
3. **Messagerie SMTP** : envoi du devis = `(ok, erreur)` renvoyé à la vue ; échec → message à l'administrateur, aucun changement de statut, possibilité de réessayer. Délai SMTP borné (`EMAIL_TIMEOUT = 20 s`). Emails de confirmation à la soumission : non bloquants.

### 2.4 Filtrage étanche de l'information (Anti-Fuite PDF)

Lorsqu'un devis est rédigé, l'équipe technique annote des informations internes dans le champ `notes` (ex : *"Marge faible sur ce poste"*, `[IA] Alerte surface`, *"[Photo] Traces d'humidité visibles"*).
- La fonction `filtrer_notes_client()` appliquée lors de la génération du document PDF élimine systématiquement :
  - Toutes les lignes préfixées par `[` (balises système, alertes IA).
  - Toutes les lignes préfixées par `• Réf.`.
  - Les résumés internes.
- Seules les consignes d'exécution destinées au maître d'ouvrage sont imprimées sur le document officiel.

### 2.5 Contrôle d'accès et erreurs HTTP

- **Pages d'administration, dashboard, planning, édition de devis, assistant IA** : décorateur `@staff_member_required`. Un visiteur **non connecté ou sans droit « staff »** est **redirigé (302) vers la page de connexion admin** (et non une erreur 403 comme indiqué dans la version 1.0).
- **Espace client sans mot de passe (`/suivi/<uuid:token>/`)** : jeton UUIDv4 (122 bits aléatoires), modifications en `POST` uniquement (`@require_POST`), `get_object_or_404` pour un jeton invalide (page 404).
- **Envoi du devis, génération automatique, assistant** : actions `POST` protégées par CSRF.

---

## 3. Registre des risques

### 3.1 Méthode de cotation

- **Probabilité (P)** : 1 = rare · 2 = possible · 3 = probable.
- **Impact (I)** : 1 = faible · 2 = moyen · 3 = élevé (financier, juridique, image ou arrêt de service).
- **Score = P × I** : **≥ 6 critique** · **3 à 5 modéré** · **≤ 2 faible**.
- **Statut** : ✅ maîtrisé (mesure en place et testée) · 🟡 partiel · 🔴 ouvert (action requise).
- Les risques **SEC-01 à 04, MET-01 à 04 et INF-01 à 03** proviennent de la version 1.0 ; les autres sont issus de la revue de la version 2.0 (assistant IA, envoi d'emails, mise en production).

### 3.2 Matrice de criticité (Probabilité × Impact)

| Impact ↓ / Probabilité → | 1 – Rare | 2 – Possible | 3 – Probable |
|---|---|---|---|
| **3 – Élevé** | SEC-03, SEC-04, MET-01, MET-02 | SEC-01, SEC-06, SEC-07, SEC-09, IA-01, IA-02, MET-05, INF-01, INF-05 | SEC-05, MET-06 |
| **2 – Moyen** | SEC-02, MET-03, MET-04 | SEC-10, IA-03, IA-05, IA-06, MET-07, MET-08, MET-09, INF-02, INF-06, INF-08 | SEC-08, INF-04 |
| **1 – Faible** | INF-03 | INF-07 | IA-04 |

Légende : les identifiants sont abrégés (`SEC-05` = R-SEC-05). Zone haute-droite = priorité absolue.


### 3.3 Risques de sécurité (SEC)

| ID | Risque | P | I | Score | Niveau | Mesure en place | Statut | Action recommandée |
|---|---|:-:|:-:|:-:|---|---|:-:|---|
| **R-SEC-01** | Fuite de la SECRET_KEY ou d'une clé d'API (IA, SMTP) | 2 | 3 | 6 | 🔴 Critique | Aucune clé en dur : `python-decouple` + `.env` exclu par `.gitignore` ; sans clé, repli sur les algorithmes locaux. | 🟡 | Voir R-SEC-05 : les clés actuelles ont été partagées en clair, à régénérer. |
| **R-SEC-02** | Usurpation d'accès au dossier client (IDOR) | 1 | 2 | 2 | 🟢 Faible | Jeton UUIDv4 (`/suivi/<uuid>/`), aucun identifiant séquentiel exposé, 404 si jeton invalide. | ✅ | — |
| **R-SEC-03** | Injection via les formulaires (SQL, XSS, CSRF) | 1 | 3 | 3 | 🟠 Modéré | CSRF Django, échappement automatique des gabarits, ORM paramétré, actions sensibles en POST. | ✅ | — |
| **R-SEC-04** | Fichier malveillant téléversé | 1 | 3 | 3 | 🟠 Modéré | Validation extension + type MIME, limite 10 Mo, dossier `/media/` sans exécution. | ✅ | Ajouter un antivirus (ClamAV) si volume important. |
| **R-SEC-05** | Secrets partagés hors du dépôt (mot de passe d'application Gmail, clé OpenRouter) et fichier `.env` livré dans des archives | 3 | 3 | 9 | 🔴 Critique | `.env` ignoré par Git ; `.env.example` sans secret. | 🔴 | Révoquer et régénérer le mot de passe d'application et la clé OpenRouter ; ne plus envoyer `.env` par messagerie ; variables d'environnement sur le serveur. |
| **R-SEC-06** | PDF de devis accessibles par URL devinable (`/media/devis/…`) | 2 | 3 | 6 | 🔴 Critique | Fichiers servis uniquement si `DEBUG` ; noms basés sur la référence du devis. | 🔴 | Nommer les PDF avec un jeton aléatoire ou les servir via une vue authentifiée (staff ou jeton client). |
| **R-SEC-07** | Attaque par force brute sur `/admin/` | 2 | 3 | 6 | 🔴 Critique | Mots de passe Django hachés ; aucune limitation de tentatives. | 🔴 | `django-axes` ou limitation au niveau du proxy, URL admin non standard, double authentification. |
| **R-SEC-08** | Spam / abus du formulaire public de demande et de l'envoi d'emails | 3 | 2 | 6 | 🔴 Critique | CSRF seulement ; aucun CAPTCHA ni limite de débit. | 🔴 | Champ « pot de miel », reCAPTCHA/hCaptcha ou limitation par IP. |
| **R-SEC-09** | Paramètres HTTPS absents (`SECURE_*`, cookies sécurisés, HSTS) | 2 | 3 | 6 | 🔴 Critique | Aucun drapeau `SECURE_*` dans `settings.py`. | 🔴 | Activer `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, HSTS en production. |
| **R-SEC-10** | Comptes personnel/administrateur partagés ou à droits excessifs | 2 | 2 | 4 | 🟠 Modéré | Accès staff contrôlé par Django. | 🟡 | Comptes nominatifs, groupes de permissions (métreur, gérant), revue périodique. |

### 3.4 Risques liés à l’IA (IA)

| ID | Risque | P | I | Score | Niveau | Mesure en place | Statut | Action recommandée |
|---|---|:-:|:-:|:-:|---|---|:-:|---|
| **R-IA-01** | L'IA de chiffrage invente un prix ou une quantité | 2 | 3 | 6 | 🔴 Critique | Prix uniquement issus du `CATALOGUE` local ; sortie JSON validée et bornée ; devis en brouillon jusqu'à validation humaine. | ✅ | — |
| **R-IA-02** | L'assistant admin donne un chiffre faux (hallucination) | 2 | 3 | 6 | 🔴 Critique | Outils ORM déterministes, température 0, contrôle automatique des nombres (réponse remplacée par les données si un nombre n'est pas vérifié) — 19 tests. | ✅ | Surveiller les formulations ambiguës (période, définition du CA). |
| **R-IA-03** | Réponses hors sujet ou fuite de données sensibles via l'assistant | 2 | 2 | 4 | 🟠 Modéré | Consignes strictes, phrase de refus fixe, accès réservé au personnel, outils en lecture seule. | ✅ | — |
| **R-IA-04** | Indisponibilité ou quota du service gratuit OpenRouter (429, latence) | 3 | 1 | 3 | 🟠 Modéré | Liste de modèles avec bascule, délai borné, « questions rapides » sans IA. | 🟡 | Prévoir un modèle payant de secours si usage quotidien. |
| **R-IA-05** | Données clients (noms, adresses) envoyées à un tiers (OpenRouter) ; modèles gratuits pouvant journaliser les requêtes | 2 | 2 | 4 | 🟠 Modéré | Seuls les résultats agrégés des outils sont renvoyés au modèle ; pas d'accès direct à la base. | 🟡 | Informer les clients (politique de confidentialité, loi 09-08 / CNDP) ; éviter d'envoyer des données personnelles dans les résultats. |
| **R-IA-06** | Injection de prompt via le texte libre d'une demande client | 2 | 2 | 4 | 🟠 Modéré | L'IA ne fait que proposer ; le moteur calcule ; validation humaine ; sortie validée. | ✅ | — |

### 3.5 Risques métier et financiers (MET)

| ID | Risque | P | I | Score | Niveau | Mesure en place | Statut | Action recommandée |
|---|---|:-:|:-:|:-:|---|---|:-:|---|
| **R-MET-01** | Erreur d'arrondi / TVA contestée | 1 | 3 | 3 | 🟠 Modéré | `Decimal` + `ROUND_HALF_UP`, TVA 20 %, tests unitaires. | ✅ | — |
| **R-MET-02** | Envoi d'un devis erroné généré automatiquement | 1 | 3 | 3 | 🟠 Modéré | Brouillon obligatoire ; envoi uniquement après clic « Envoyer au client » ; échec SMTP sans changement de statut — testé. | ✅ | — |
| **R-MET-03** | Fuite de notes internes ou de marges sur le PDF | 1 | 2 | 2 | 🟢 Faible | Filtrage `test_filtrer_notes_client`. | ✅ | — |
| **R-MET-04** | Mentions légales absentes | 1 | 2 | 2 | 🟢 Faible | Pied de page PDF avec ICE/RC/IF et montant en lettres. | 🟡 | Voir R-MET-05 : valeurs actuelles non fiables. |
| **R-MET-05** | Mentions légales incohérentes ou factices (ICE/IF/RC) : PDF à zéros, 3 versions différentes entre PDF, pied de site et page Contact | 2 | 3 | 6 | 🔴 Critique | Source unique (V0.7+) : champs ICE / IF / RC dans *Paramètres*, repris par le PDF, le pied de page et la page Contact ; plus de valeur factice. | 🟡 | Valeurs du pied de page (ICE 002984125000084, IF 45982130, RC Casablanca) appliquées par défaut ; à confirmer avec le certificat officiel (RC : ajouter le numéro). |
| **R-MET-06** | Prix du catalogue non calibrés avec la grille réelle → devis sous- ou sur-évalués | 3 | 3 | 9 | 🔴 Critique | Prix indicatifs ; validation humaine avant envoi. | 🟡 | Faire valider le catalogue par le métreur/gérant ; revue annuelle. |
| **R-MET-07** | Devis « Acceptée » créé en doublon ou régénéré par erreur | 2 | 2 | 4 | 🟠 Modéré | Génération idempotente (`get_devis_actif`), testée. | ✅ | — |
| **R-MET-08** | Email du devis non reçu (spam, adresse erronée, quota Gmail ≈ 500/jour) | 2 | 2 | 4 | 🟠 Modéré | Erreur visible par l'admin, réessai possible ; version texte + HTML. | 🟡 | Adresse d'expédition sur domaine propre (SPF/DKIM) ; service transactionnel si volume. |
| **R-MET-09** | Validité du devis dépassée / acceptation tardive sans mise à jour des prix | 2 | 2 | 4 | 🟠 Modéré | Date de validité affichée. | 🟡 | Alerte automatique à l'expiration ; recalcul avant acceptation tardive. |

### 3.6 Risques d’infrastructure et de disponibilité (INF)

| ID | Risque | P | I | Score | Niveau | Mesure en place | Statut | Action recommandée |
|---|---|:-:|:-:|:-:|---|---|:-:|---|
| **R-INF-01** | Verrouillage SQLite en production | 2 | 3 | 6 | 🔴 Critique | SQLite en dev ; PostgreSQL 16 prévu via Docker Compose. | 🟡 | Déployer avec `USE_SQLITE=False`. |
| **R-INF-02** | Saturation du disque (photos téléversées, PDF) | 2 | 2 | 4 | 🟠 Modéré | Limite 10 Mo par fichier. | 🟡 | Surveillance disque ; stockage objet (S3/Wasabi) si besoin. |
| **R-INF-03** | Panne du fournisseur de tuiles de carte | 1 | 1 | 1 | 🟢 Faible | CDN Esri, repli visuel CSS. | ✅ | — |
| **R-INF-04** | Dépendance au CDN Tailwind « play » (non prévu pour la production, requiert Internet, ralentit le rendu) et Bootstrap/CDN | 3 | 2 | 6 | 🔴 Critique | Aucune. | 🔴 | Compiler Tailwind (CLI) et héberger les CSS/JS en local ; Bootstrap déjà isolé dans `.hda-bs`. |
| **R-INF-05** | Perte de données (pas de sauvegarde automatique) | 2 | 3 | 6 | 🔴 Critique | Volume Docker PostgreSQL. | 🔴 | Sauvegarde quotidienne `pg_dump` + copie de `/media/`, test de restauration trimestriel. |
| **R-INF-06** | Fichiers statiques manquants après déploiement (WhiteNoise « manifest ») | 2 | 2 | 4 | 🟠 Modéré | WhiteNoise installé. | 🟡 | `collectstatic` dans la procédure de déploiement / Dockerfile. |
| **R-INF-07** | Dépendances inutilisées ou obsolètes (`requirements.txt` : Celery, Redis, storages, factory-boy…) → surface d'attaque, installation lourde | 2 | 1 | 2 | 🟢 Faible | — | 🔴 | Nettoyer et figer les versions ; `pip-audit` régulier. |
| **R-INF-08** | Absence de supervision et de journalisation des erreurs | 2 | 2 | 4 | 🟠 Modéré | Logs Django par défaut. | 🔴 | Sentry ou logs centralisés ; alerte sur échec d'envoi d'email. |

---

## 4. Plan d'actions priorisé

### Priorité 1 — avant toute mise en production (risques ouverts critiques)

1. **R-SEC-05** — Secrets partagés hors du dépôt → Révoquer et régénérer le mot de passe d'application et la clé OpenRouter ; ne plus envoyer `.env` par messagerie ; variables d'environnement sur le serveur.
2. **R-SEC-06** — PDF de devis accessibles par URL devinable → Nommer les PDF avec un jeton aléatoire ou les servir via une vue authentifiée (staff ou jeton client).
3. **R-SEC-07** — Attaque par force brute sur `/admin/` → `django-axes` ou limitation au niveau du proxy, URL admin non standard, double authentification.
4. **R-SEC-08** — Spam / abus du formulaire public de demande et de l'envoi d'emails → Champ « pot de miel », reCAPTCHA/hCaptcha ou limitation par IP.
5. **R-SEC-09** — Paramètres HTTPS absents → Activer `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, HSTS en production.
6. **R-INF-04** — Dépendance au CDN Tailwind « play » → Compiler Tailwind (CLI) et héberger les CSS/JS en local ; Bootstrap déjà isolé dans `.hda-bs`.
7. **R-INF-05** — Perte de données → Sauvegarde quotidienne `pg_dump` + copie de `/media/`, test de restauration trimestriel.

### Priorité 2 — premier mois (risques ouverts modérés/faibles)

1. **R-INF-08** — Absence de supervision et de journalisation des erreurs → Sentry ou logs centralisés ; alerte sur échec d'envoi d'email.
2. **R-INF-07** — Dépendances inutilisées ou obsolètes → Nettoyer et figer les versions ; `pip-audit` régulier.

### Priorité 3 — amélioration continue (mesures partielles à compléter)

1. **R-SEC-01** — Fuite de la SECRET_KEY ou d'une clé d'API → Voir R-SEC-05 : les clés actuelles ont été partagées en clair, à régénérer.
2. **R-SEC-10** — Comptes personnel/administrateur partagés ou à droits excessifs → Comptes nominatifs, groupes de permissions (métreur, gérant), revue périodique.
3. **R-IA-04** — Indisponibilité ou quota du service gratuit OpenRouter → Prévoir un modèle payant de secours si usage quotidien.
4. **R-IA-05** — Données clients → Informer les clients (politique de confidentialité, loi 09-08 / CNDP) ; éviter d'envoyer des données personnelles dans les résultats.
5. **R-MET-04** — Mentions légales absentes → Voir R-MET-05 : valeurs actuelles non fiables.
6. **R-MET-05** — Mentions légales incohérentes ou factices → Valeurs du pied de page (ICE 002984125000084, IF 45982130, RC Casablanca) appliquées par défaut ; à confirmer avec le certificat officiel (RC : ajouter le numéro).
7. **R-MET-06** — Prix du catalogue non calibrés avec la grille réelle → devis sous- ou sur-évalués → Faire valider le catalogue par le métreur/gérant ; revue annuelle.
8. **R-MET-08** — Email du devis non reçu → Adresse d'expédition sur domaine propre (SPF/DKIM) ; service transactionnel si volume.
9. **R-MET-09** — Validité du devis dépassée / acceptation tardive sans mise à jour des prix → Alerte automatique à l'expiration ; recalcul avant acceptation tardive.
10. **R-INF-01** — Verrouillage SQLite en production → Déployer avec `USE_SQLITE=False`.
11. **R-INF-02** — Saturation du disque → Surveillance disque ; stockage objet (S3/Wasabi) si besoin.
12. **R-INF-06** — Fichiers statiques manquants après déploiement → `collectstatic` dans la procédure de déploiement / Dockerfile.


---

## 5. Check-list pré-déploiement

**Configuration**
- [ ] `DEBUG=False` ; `SECRET_KEY` aléatoire de 50 caractères ; `ALLOWED_HOSTS=hda-global.ma,www.hda-global.ma`.
- [ ] `USE_SQLITE=False` ; PostgreSQL joignable ; sauvegarde automatique configurée (R-INF-05).
- [ ] `SITE_URL=https://hda-global.ma` (liens des emails et QR code du PDF).
- [ ] `EMAIL_BACKEND=…smtp.EmailBackend`, mot de passe d'application Gmail **régénéré**, test d'envoi réussi.
- [ ] `OPENROUTER_API_KEY` **régénérée** ; `ANTHROPIC_API_KEY` si utilisée ; aucun secret dans Git.

**Sécurité**
- [ ] `SECURE_SSL_REDIRECT=True`, `SESSION_COOKIE_SECURE=True`, `CSRF_COOKIE_SECURE=True`, `SECURE_HSTS_SECONDS`.
- [ ] URL `/admin/` non standard ou protégée (limitation des tentatives / double authentification) — R-SEC-07.
- [ ] Mots de passe administrateur forts, comptes nominatifs, pas de compte `admin/admin123`.
- [ ] PDF de devis non accessibles par URL devinable — R-SEC-06.
- [ ] Limitation du débit du formulaire public — R-SEC-08.

**Données légales**
- [ ] ICE, IF, RC, adresse du siège renseignés dans *Paramètres de l'entreprise* et identiques sur le site, le PDF et les emails — R-MET-05.
- [ ] Prix du catalogue remplacés par la grille réelle ; TVA vérifiée — R-MET-06.

**Technique**
- [ ] `python manage.py migrate` puis `python manage.py collectstatic --noinput` (obligatoire avec WhiteNoise « manifest ») — R-INF-06.
- [ ] Remplacer le CDN Tailwind par un CSS compilé — R-INF-04.
- [ ] `python manage.py test` : **59 tests au vert**.
- [ ] Test de bout en bout : demande → « Acceptée » → devis → email reçu avec PDF → acceptation par le client.

---

## 6. Annexe : écarts constatés entre documentation et code

| # | Constat (version 1.0 du document ou du code) | Réalité vérifiée | Action |
|---|---|---|---|
| 1 | « Les PDF intègrent ICE 003 143 978 000 059 / IF 47510890 » | Le pied de page du PDF contient **ICE 000000000000000 – RC 000000 – IF 00000000** ; le pied du site affiche **ICE 002984125000084 / IF 45982130** ; la page Contact affiche **ICE 003 143 978 000 059 / IF 47510890**. Trois versions différentes. | Choisir les vraies valeurs, les saisir une seule fois dans *Paramètres* et les réutiliser partout (R-MET-05). |
| 2 | « Utilisateur connecté sans droit staff → 403 » | `staff_member_required` **redirige vers la connexion admin** (302). | Documentation corrigée (2.5). |
| 3 | « Tous les `send_mail` utilisent `fail_silently=True` » | L'envoi du **devis** signale désormais l'échec à l'administrateur ; seuls les emails de confirmation restent non bloquants. | Documentation corrigée (2.3). |
| 4 | « 32 tests » | **59 tests** (24 dans `tests_auto.py`, + flux devis, + assistant). | Documentation mise à jour (1). |
| 5 | « Clé API Anthropic uniquement » | L'assistant admin utilise **OpenRouter** (`OPENROUTER_API_KEY`). | Documentation mise à jour (2.3, R-IA). |
| 6 | `requirements.txt` : `qrcode==8.0`, plus Celery, Redis, django-storages, factory-boy, django-extensions | L'environnement local utilise `qrcode 8.2` ; Celery/Redis/storages/factory-boy/extensions **ne sont pas utilisés** dans le code. | Aligner les versions et retirer les dépendances inutilisées (surface d'attaque et temps d'installation). |
| 7 | Dossier `.venv` (Windows, ≈ 88 Mo) et `__pycache__` dans l'archive | Spécifiques à la machine, ne doivent pas être livrés ; déjà exclus par `.gitignore`. | Recréer avec `python -m venv .venv` et `pip install -r requirements.txt`. |
