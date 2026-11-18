Set-Location $PSScriptRoot
$env:DEMO_SECRET_KEY = "arret"
docker compose -f docker-compose.demo.yml down
Write-Host "Démo arrêtée (vos données db.sqlite3 et media/ sont conservées)."
