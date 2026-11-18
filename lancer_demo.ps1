# Lance l'application dans Docker + un lien HTTPS public gratuit (Cloudflare). Usage :  .\lancer_demo.ps1
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
if (-not (Test-Path ".env")) { Write-Host "Fichier .env introuvable (copiez .env.example en .env)." -ForegroundColor Red; exit 1 }
if (-not (Test-Path "db.sqlite3")) { Write-Host "db.sqlite3 introuvable : lancez d'abord  python manage.py migrate  (ou utilisez votre base)." -ForegroundColor Red; exit 1 }

# clé secrète de démo, générée une seule fois (jamais publiée)
if (-not (Test-Path ".demo_secret")) {
    -join ((1..64) | ForEach-Object { '{0:x}' -f (Get-Random -Maximum 16) }) | Set-Content ".demo_secret" -NoNewline
}
$env:DEMO_SECRET_KEY = (Get-Content ".demo_secret" -Raw).Trim()
$env:SITE_URL_DEMO = "http://localhost:8000"
$f = "docker-compose.demo.yml"

Write-Host "Démarrage (la première fois, la construction prend quelques minutes)..." -ForegroundColor Cyan
docker compose -f $f up -d --build

Write-Host "Création du lien public..." -ForegroundColor Cyan
$url = $null
for ($i = 0; $i -lt 60 -and -not $url; $i++) {
    Start-Sleep -Seconds 2
    $logs = (docker compose -f $f logs tunnel 2>&1 | Out-String)
    if ($logs -match 'https://[a-z0-9-]+\.trycloudflare\.com') { $url = $Matches[0] }
}
if (-not $url) { Write-Host "Lien introuvable. Voir :  docker compose -f $f logs tunnel" -ForegroundColor Red; exit 1 }

# les liens des emails (suivi client) doivent pointer vers ce lien public
$env:SITE_URL_DEMO = $url
docker compose -f $f up -d web | Out-Null

Write-Host ""
Write-Host "Application en ligne : $url" -ForegroundColor Green
Write-Host "Administration       : $url/admin/" -ForegroundColor Green
Write-Host "Le lien change à chaque lancement. Le PC doit rester allumé. Arrêt :  .\arreter_demo.ps1"
