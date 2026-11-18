# Publier gratuitement avec un lien https (GitHub → Render)

1. Créez un dépôt GitHub et poussez le projet (le fichier `.env` et `db.sqlite3` sont ignorés : ne les ajoutez jamais).
2. Sur https://render.com, connectez-vous avec GitHub.
3. **New + → Blueprint**, choisissez le dépôt : Render lit `render.yaml`, crée la base PostgreSQL gratuite et le site.
4. Renseignez si vous le souhaitez `OPENROUTER_API_KEY` (assistant IA) ; laissez `EMAIL_HOST_PASSWORD` vide.
5. Après le build (5 à 10 min), le lien est de la forme `https://hda-global-xxxx.onrender.com`.
   Admin : `/admin/` (compte `admin`, mot de passe de `load_demo_data` : changez-le immédiatement).

## Limites du gratuit
- Le site s'endort après 15 min d'inactivité (premier chargement ~1 min).
- La base PostgreSQL gratuite expire après 30 jours.
- Les fichiers envoyés (PDF de devis, uploads) ne sont pas conservés.
- Render bloque le SMTP sortant : les e-mails Gmail ne partiront pas depuis ce lien.
