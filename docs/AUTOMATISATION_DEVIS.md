# Automatisation des devis H.D.A GLOBAL

> Principe directeur : **« l'IA propose, le moteur calcule, l'humain valide »**.

Transformer une demande client floue (WhatsApp / téléphone) en **devis
professionnel** avec un minimum de saisie manuelle — le devis final reste
tâche d'un humain, qui relit le brouillon avant envoi.

## 1. Flux de bout en bout

```
Client (formulaire public)
   │  service, ville, surface, description, photos
   ▼
Demande créée ──► emails confirmation + alerte admin
   │
   ├─► [IA OPTIONNELLE] devis/ai.py ─ analyse du besoin (surface, postes,
   │     résumé, questions) ── rejet si sortie invalide ── repli local regex
   ▼
devis/auto.py : proposer_devis() ─► catalogue des prix ─► totaux pricing.py
   ▼
Devis BROUILLON (lignes + PDF + notes internes)
   │                    ▲ idempotent : pas de 2ᵉ devis tant que le 1er est actif
   ▼
Admin ─ bandeau « à relire » ─ relecture ─► « Envoyer au client »
   │                                        (PDF + email + statut "devis_envoye")
   ▼
Portail client /suivi/<token>/ ─► accepte / refuse
```

Le statut de la demande reste **« Nouvelle »** après génération : il passe à
**« Devis envoyé »** uniquement lors de l'envoi réel du devis.

## 2. Tableau des couches

| Couche | Fichier | Rôle |
|---|---|---|
| Catalogue | `devis/auto.py` — `CATALOGUE`, `FORMULES` | postes types, unités, **prix HT en MAD de DÉMONSTRATION**, à remplacer par la vraie grille de l'entreprise (Semaine 1 de la feuille de route) |
| Détection / proposition | `devis/auto.py` — `detecter_famille()`, `proposer_devis()` | famille métier (mots-clés sans accents), surface (saisie > IA > regex > inconnue), postes IA (si valides) sinon formule, frais de déplacement hors zone, confiances « élevée / moyenne / faible » + alertes |
| Calcul | `devis/pricing.py` | `Decimal`, `ROUND_HALF_UP`, HT / TVA / TTC (versions BD et pure `calculer_totaux`) |
| IA (optionnelle) | `devis/ai.py` | appel HTTPS **stdlib-only** (urllib) à l'API Anthropic ; validation stricte `analyser_reponse_json()` ; jamais de prix ; repli `extraire_surface_regex()` |
| Vision photos | `devis/vision.py` | **Extension** : analyse des **photos de chantier** (`PieceJointe`, max 3, ~1,2 Mo) par le modèle de vision Anthropic (contenu multi-modal base64) ; sortie validée `valider_reponse_vision()` : observations / indices / questions uniquement — jamais de prix ; fusion dans le brouillon (`fusionner_dans_resultat_ia`), alertes préfixées « [Photo] » ; échec toléré, optionnel |
| PDF | `devis/pdf.py` | `construire_pdf()` pure + `generer_pdf_devis()` ; logo, montant en lettres, QR portail de suivi, conditions, tableau, footer paginé ; **filtrage permanent des notes internes** |
| Front admin | `devis/views.py` (vue `generer_auto`), `devis/urls.py` (route `auto/<int:demande_id>/`), bouton sur `templates/devis/creer.html`, bandeau de relecture sur `editer.html` | **Vous validez** avant envoi |
| Génération à la création | `demandes/views.py` (réglage `DEVIS_AUTO_A_LA_CREATION`) | brouillon pré-généré, jamais bloquant (try/except) |

## 3. Activation / configuration

- **Sans configuration du tout** (0 `$`, 0 clé API) : tout fonctionne déjà —
  bouton « Générer le devis automatiquement » basé catalogue + regex.
- **Clé API** (optionnelle, débloque : résumé, détection darija/français avec
  fautes, questions au client) — dans **.env seulement, jamais commitée** :

```
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-sonnet-4-5-20250929   # défaut
DEVIS_VISION_MAX_PHOTOS=3                    # défaut : 3 photos analysées
SITE_URL=https://votre-domaine.ma            # QR code / lien du PDF
DEVIS_AUTO_A_LA_CREATION=True                # default True
```

- **Confidentialité (loi marocaine 09-08 / CNDP)** : seule la description et
  les infos de chantier sont envoyées vers l'IA, jamais le nom ni les
  coordonnées du client. À signaler dans la politique de confidentialité.

## 4. Garanties (à vérifier si vous modifiez)

1. L'IA ne fixe JAMAIS un prix : test `test_ia_ne_peut_pas_injecter_prix_ni_poste_inconnu` +
   `test_vision_valide_sortie_et_borne` (vision).
2. Toute sortie IA est validée (`devis/ai.py::analyser_reponse_json`,
   `devis/vision.py::valider_reponse_vision`).
3. L'IA est optionnelle et échoue silencieusement : le devis se génère quand même.
4. Le devis reste « brouillon » jusqu'à « Envoyer au client ».
5. Les notes internes (`[IA] ...`, lignes « • / Résumé », indices « [Photo] »)
   sont filtrées du PDF client par `devis/pdf.py::filtrer_notes_client`.
6. Ne rien casser : statuts, portail client et chiffrage manuel restent actifs.

## 5. La grille tarifaire et la production

- ⚠️ **Prix du catalogue fictifs** : à remplacer par la grille de
  l'entreprise (Semaine 1).
- ⚠️ Aucun appel IA réel exécuté : validation + repli sont testés (unitaires).
- Avant production : téléverser le logo original (haute résolution) dans
  Admin → *Paramètres de l'entreprise* → *Logo* ; l'icône extraite du flyer
  est en résolution limitée — demander le fichier d'origine.

## 6. Tests

```bash
# 24 tests unitaires (détection de famille, totaux déterministes
# 37 200 / 7 440 / 44 640, surface manquante, déplacement hors zone,
# IA sans prix ni code inconnu, JSON invalide, regex de surface,
# postes IA, montant en lettres, PDF, filtre notes, catalogue, vision photos)
./.venv/Scripts/python.exe manage.py test devis.tests_auto -v 1

# tous (36) — tests existants + nouveaux
./.venv/Scripts/python.exe manage.py test -v 1
```

Succès attendu : `Ran 36 tests ... OK`.

## 7. Exemple de devis

```bash
./.venv/Scripts/python.exe exemples/generer_exemple.py
# → exemples/devis_exemple_DEV-2026-0001.pdf (client 100 % fictif)
```

## 8. À valider visuellement (hors code)

- Pages d'admin (accueil / listes / formulaires / connexion / mobile) :
  à relire via `manage.py runserver`, thèmes OS clair ET sombre (le CSS force
  le clair) ;
- La page `/devis/<id>/editer/` dépend du CDN Bootstrap : non vérifiée hors
  ligne ;
- Coût des appels IA par demande à mesurer sur des demandes réelles
  (Semaine 3 de la feuille de route).
