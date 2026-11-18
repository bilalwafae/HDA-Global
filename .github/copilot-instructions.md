# Instructions pour les agents IA (VS Code / Copilot / Cursor / Claude Code)

Projet : H.D.A GLOBAL, Django 5.1 (apps core, services, clients, demandes, devis, interventions, assistant).

## Règles absolues
- Ne jamais lire, afficher, modifier ni commiter `.env`, `db.sqlite3`, `media/` (hors `media/services/`). Ne jamais écrire de secret (mot de passe Gmail, clé OpenRouter, SECRET_KEY) dans le code, un commit, une issue ou un log.
- Ne pas changer le code applicatif quand on te demande seulement de déployer. Le déploiement ne touche que : `Dockerfile`, `docker-compose*.yml`, `render.yaml`, `Caddyfile`, `.github/`, `docs/`.
- Toute action irréversible (push --force, suppression de base, `docker compose down -v`, rotation de secrets) : demander confirmation d'abord.

## Avant tout déploiement
1. `python manage.py test` doit passer (USE_SQLITE=True).
2. `git status` : vérifier qu'aucun secret n'est suivi (`git ls-files | grep -E "\.env$|sqlite3"` doit être vide).
3. Commit clair, push sur `main`.

## Chemins de déploiement
- Local / test Docker : `docker compose up --build` (http://localhost:8000).
- Lien https gratuit depuis GitHub : Render, voir `docs/PUBLIER_RENDER.md` (`render.yaml`, Blueprint).
- Serveur avec domaine : `docker compose -f docker-compose.prod.yml up -d --build`, voir `docs/DEPLOIEMENT.md`.
- Démo depuis le PC : `lancer_demo.ps1` (tunnel Cloudflare).

## Variables d'environnement (noms seulement)
SECRET_KEY, DEBUG, ALLOWED_HOSTS, SITE_URL, USE_SQLITE, POSTGRES_*, DB_HOST, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD, HDA_EMAIL, OPENROUTER_API_KEY, SUIVI_VALIDITE_JOURS, SUIVI_LIMITE_PAR_MINUTE. En production DEBUG=False et SECRET_KEY ≥ 40 caractères, sinon l'application refuse de démarrer.

## Limites connues
Render gratuit : site endormi après 15 min, base expirant à 30 jours, uploads non persistants, SMTP sortant bloqué (les e-mails de devis ne partent pas ; utiliser un VPS ou un service d'e-mail par API).
