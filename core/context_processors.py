"""
Context processor global : injecte les paramètres de l'entreprise H.D.A GLOBAL
dans tous les templates sans avoir besoin de les passer manuellement dans chaque vue.
"""
from .models import Parametres


def parametres_entreprise(request):
    """Injecte 'parametres' dans chaque template rendu."""
    return {"parametres": Parametres.get()}

