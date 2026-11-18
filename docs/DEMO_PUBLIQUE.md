# Démo publique gratuite (soutenance) — Docker + lien HTTPS Cloudflare

Aucun compte, aucune carte, aucun domaine. L'application tourne dans Docker **sur votre PC** et Cloudflare crée un lien
`https://xxxx.trycloudflare.com` accessible depuis n'importe quel appareil.

## Utilisation (Windows / PowerShell)
1. Lancer **Docker Desktop** et attendre qu'il soit démarré.
2. Dans le dossier du projet (celui qui contient `docker-compose.demo.yml`) :
   ```
   .\lancer_demo.ps1
   ```
   Si PowerShell refuse : `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` puis relancer.
3. Le script affiche l'adresse publique, par exemple `https://mon-lien.trycloudflare.com` (et `/admin/` pour l'administration).
4. Arrêter : `.\arreter_demo.ps1`.

## À savoir
- Les données utilisées sont votre `db.sqlite3` et votre dossier `media/` (rien à migrer).
- Le lien **change à chaque lancement** ; le script met à jour `SITE_URL` automatiquement pour que les liens de suivi envoyés
  par email pointent vers le bon lien. Un email envoyé lors d'une session précédente aura donc un lien mort.
- Le PC doit rester allumé et connecté. Ouvrez le site par le **lien public** (les cookies de connexion sont sécurisés :
  `http://localhost:8000` ne conserve pas la session administrateur).
- Mode production (`DEBUG=False`) : pas de pages de débogage visibles de l'extérieur.
- Pour un site permanent avec votre propre domaine : `docs/DEPLOIEMENT.md`.
