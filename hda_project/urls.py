from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# Personnalisation de l'interface Django Admin
admin.site.site_header = "Administration"
admin.site.site_title = "Administration H.D.A GLOBAL"
admin.site.index_title = "Gestion des Demandes, Devis & Chantiers"

urlpatterns = [
    # Back-office Django Admin
    path("admin/assistant/", include("assistant.urls", namespace="assistant")),
    path("admin/", admin.site.urls),

    # Applications métier
    path("", include("core.urls", namespace="core")),
    path("services/", include("services.urls", namespace="services")),
    path("demande/", include("demandes.urls", namespace="demandes")),
    path("suivi/", include("demandes.urls_suivi", namespace="suivi")),
    path("devis/", include("devis.urls", namespace="devis")),
    path("interventions/", include("interventions.urls", namespace="interventions")),
]

# Médias privés servis par Django au personnel connecté (en production, Caddy ne sert que /media/services/)
if not settings.DEBUG:
    from core.views import media_protege
    urlpatterns += [path("media/<path:chemin>", media_protege, name="media_protege")]

# Servir les fichiers médias en développement
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

