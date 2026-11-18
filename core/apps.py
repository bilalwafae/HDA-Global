"""
App core : pages institutionnelles, paramètres singleton de l'entreprise,
context processor global et gestion des emails automatiques.
"""
from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"
    verbose_name = "Paramètres & Gestion Globale"

