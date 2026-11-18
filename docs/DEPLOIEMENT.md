# Déploiement en production — https://votre-domaine

Architecture : **Caddy** (HTTPS automatique) → **gunicorn + Django** → **PostgreSQL**, le tout dans Docker.
Fichiers : `docker-compose.prod.yml`, `Caddyfile`, `.env.prod.example`.

## 1. Ce qu'il vous faut
| Élément | Exemple | Coût indicatif |
|---|---|---|
| Un serveur (VPS) Linux, 2 Go de RAM | Hetzner, OVH, Contabo, DigitalOcean (Ubuntu 24.04) | ≈ 4 à 6 €/mois |
| Un nom de domaine | `hda-global.ma` (registrar marocain) ou `.com` | ≈ 100 à 300 MAD/an |

Pour un simple test sans acheter de domaine : un sous-domaine gratuit (ex. DuckDNS : `hda-global.duckdns.org`).

## 2. Pointer le domaine vers le serveur
Chez le registrar, dans la zone DNS, créer deux enregistrements **A** vers l'adresse IP du serveur :
`@` (hda-global.ma) et `www`. Attendre la propagation (quelques minutes à quelques heures).

## 3. Préparer le serveur (une seule fois)
```bash
ssh root@IP_DU_SERVEUR
curl -fsSL https://get.docker.com | sh          # installe Docker + docker compose
ufw allow OpenSSH && ufw allow 80 && ufw allow 443 && ufw enable
```

## 4. Envoyer le projet
Copiez le dossier du projet sur le serveur (zip + `scp`, ou `git clone`), SANS `db.sqlite3` ni `.env` de développement :
```bash
scp HDA-Global.zip root@IP_DU_SERVEUR:/opt/ && ssh root@IP_DU_SERVEUR
cd /opt && apt-get install -y unzip && unzip HDA-Global.zip && cd HDA-Global
cp .env.prod.example .env && nano .env
```
Dans `.env` : `DOMAIN`, `ALLOWED_HOSTS`, `SITE_URL` (en `https://…`), `POSTGRES_PASSWORD` (long et aléatoire), `SECRET_KEY`
(`python3 -c "import secrets; print(secrets.token_urlsafe(60))"`), mot de passe d'application Gmail, clé OpenRouter.
**Ces secrets ne doivent jamais être collés dans un chat, un mail ou un dépôt Git.**

## 5. Démarrer
```bash
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml logs -f web caddy     # Ctrl+C pour quitter
```
Au premier accès, Caddy obtient tout seul le certificat HTTPS (le DNS doit déjà pointer vers le serveur, ports 80 et 443 ouverts).

## 6. Créer l'administrateur et les données
```bash
docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
# Données de démonstration (facultatif, une seule fois) :
docker compose -f docker-compose.prod.yml exec web python manage.py load_demo_data
```
Images de services (dossier `media/` du projet) :
```bash
docker compose -f docker-compose.prod.yml cp media/. web:/app/media/
```
Reprendre les données d'une base SQLite de développement :
```bash
# sur le PC (USE_SQLITE=True)
python manage.py dumpdata --natural-foreign --natural-primary -e contenttypes -e auth.permission > data.json
# sur le serveur
docker compose -f docker-compose.prod.yml cp data.json web:/app/data.json
docker compose -f docker-compose.prod.yml exec web python manage.py loaddata data.json
```

## 7. Vérifier
- `https://votre-domaine` s'ouvre avec le cadenas ; `http://` redirige vers `https://`.
- `/admin/` : connexion, envoi d'un devis par email, liens de suivi en `https://…`.
- Quand tout est validé, mettre `SECURE_HSTS_SECONDS=31536000` dans `.env`, puis `docker compose -f docker-compose.prod.yml up -d`.

## 8. Mettre à jour l'application
Remplacer les fichiers du projet (sans toucher `.env`), puis :
```bash
docker compose -f docker-compose.prod.yml up -d --build
```
Les migrations s'appliquent automatiquement au démarrage.

## 9. Sauvegardes (à planifier, ex. chaque nuit avec cron)
```bash
docker compose -f docker-compose.prod.yml exec -T db pg_dump -U hda_user hda_db > sauvegarde_$(date +%F).sql
docker run --rm -v hda-global_media_files:/m -v $PWD:/b alpine tar czf /b/media_$(date +%F).tgz -C /m .
```
Restauration : `cat sauvegarde.sql | docker compose -f docker-compose.prod.yml exec -T db psql -U hda_user hda_db`.
Copiez les sauvegardes AILLEURS que sur le serveur.

## 10. Sécurité : liste de contrôle
- [ ] `DEBUG=False` (imposé par le compose) et `SECRET_KEY` unique (l'application refuse de démarrer sinon).
- [ ] Mots de passe PostgreSQL et administrateur longs ; accès SSH par clé de préférence.
- [ ] `.env` jamais publié ; clés Gmail / OpenRouter régénérées si elles ont fuité.
- [ ] Les photos de chantier et PDF de devis ne sont accessibles qu'au personnel connecté ; seules les images de services sont publiques.
- [ ] Le suivi client est protégé par lien secret (voir `demandes/securite_suivi.py`).
- [ ] Sauvegardes testées (restauration essayée au moins une fois).

## Dépannage
| Symptôme | Cause probable |
|---|---|
| Pas de cadenas / erreur de certificat | DNS pas encore propagé, ports 80/443 fermés, mauvais `DOMAIN` |
| `Bad Request (400)` | Le domaine n'est pas dans `ALLOWED_HOSTS` |
| `CSRF verification failed` | `SITE_URL`/`ALLOWED_HOSTS` en `https://` mal renseignés (ou `CSRF_TRUSTED_ORIGINS`) |
| Le conteneur `web` redémarre en boucle | `SECRET_KEY` trop faible/absente : `docker compose … logs web` |
| Images de services absentes | Copier `media/` (étape 6) |
| Emails non reçus | Voir les logs `web` ; mot de passe d'application Gmail du compte `EMAIL_HOST_USER` |
