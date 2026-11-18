# Assistant IA de l'administration (OpenRouter)

Accès : Admin → bouton « ✨ Assistant IA » (réservé au personnel), URL /admin/assistant/.

## Principe anti-erreur
1. L'IA ne lit pas la base : elle appelle des **outils** (assistant/outils.py) qui calculent tout (ORM).
2. Elle ne fait que choisir l'outil et reformuler. Température 0, consignes strictes (assistant/llm.py : SYSTEM_PROMPT).
3. **Contrôle automatique** : tout nombre de la réponse doit exister dans les résultats des outils, sinon la réponse
   est remplacée par un rendu direct des données.
4. Hors sujet → phrase de refus fixe. Information absente → « Je ne dispose pas de cette information ».
5. Sans IA (clé absente / quota) : les « questions rapides » fonctionnent quand même.

## Configuration (.env)
OPENROUTER_API_KEY=sk-or-v1-...
OPENROUTER_MODELS=openrouter/free        # ou une liste : modele1:free,modele2:free (essayés dans l'ordre)

## Définitions utilisées
- Intervention dans la période = date de début des travaux dans la période.
- Chiffre d'affaires = somme des devis « Accepté » (HT/TTC), par date d'émission.
- Demande dans la période = date de création.

## Exemples
« Combien d'interventions à Casablanca en 2026 ? » · « Interventions par ville ce mois-ci » ·
« Combien d'interventions pour Omar Benjelloun ? » · « Service le plus demandé et argent gagné ? » ·
« Chiffre d'affaires par mois » · « Où en est la demande DEM-2026-0007 ? »
