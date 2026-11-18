"""
Prévisualisation des pages admin pour captures d'écran headless.
Génère des fichiers HTML autonomes (liens statiques réécrits en file://)
dans %TEMP%\opencode\previews\ — à capturer avec Edge headless.
Usage : .\\venv\\Scripts\\python.exe outils\\previews_admin.py [avant|apres]
"""
import os
import re
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hda_project.settings")

import django  # noqa: E402

django.setup()

from django.contrib.staticfiles import finders  # noqa: E402
from django.test import Client  # noqa: E402
from django.contrib.auth.models import User  # noqa: E402

SORTIE = Path(os.environ.get("TEMP", "/tmp")) / "opencode" / "previews"
PREFIXE = sys.argv[1] if len(sys.argv) > 1 else "apres"
UTILISATEUR = "_preview_admin_"


def reecrit_static(html: str) -> str:
    """Réécrit les liens /static/ en chemins file:// pour la capture locale."""
    def remplacement(m):
        chemin = Path(finders.find(m.group(1) or ""))
        if not chemin or not chemin.exists():
            return m.group(0)
        return f'href="file:///{chemin.resolve().as_posix()}"'

    html = re.sub(r'href="/static/([^"]+)"', remplacement, html)
    return html


def main():
    SORTIE.mkdir(parents=True, exist_ok=True)
    client = Client(SERVER_NAME="localhost")

    # Page de login (sans session)
    pages = {"login": client.get("/admin/login/").content.decode("utf-8")}

    # Session staff pour les autres pages
    user, _ = User.objects.get_or_create(
        username=UTILISATEUR,
        defaults={"is_staff": True, "is_superuser": True},
    )
    user.is_staff = True
    user.is_superuser = True
    user.save()
    client.force_login(user)

    try:
        pages["dashboard"] = client.get("/admin/").content.decode("utf-8")
        pages["demandes"] = client.get("/admin/demandes/demande/").content.decode("utf-8")
        pages["devis"] = client.get("/admin/devis/devis/").content.decode("utf-8")
        pages["clients"] = client.get("/admin/clients/client/").content.decode("utf-8")

        from demandes.models import Demande  # noqa: E402
        demande = Demande.objects.first()
        if demande:
            pages["change_demande"] = client.get(
                f"/admin/demandes/demande/{demande.pk}/change/"
            ).content.decode("utf-8")
    finally:
        # Nettoyage : l'utilisateur de prévisualisation ne reste pas
        user.delete()

    for nom, html in pages.items():
        fichier = SORTIE / f"{PREFIXE}_{nom}.html"
        fichier.write_text(reecrit_static(html), encoding="utf-8")
        print(f"ecrit : {fichier}")


if __name__ == "__main__":
    main()
