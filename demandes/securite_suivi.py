"""
Sécurité du portail de suivi client (accès par lien secret, sans mot de passe).

Mesures :
 1. le lien ne donne accès qu'à SA demande (jamais aux autres demandes du client) ;
 2. expiration : le lien cesse de fonctionner si le dossier est inactif depuis SUIVI_VALIDITE_JOURS jours
    (le personnel connecté n'est pas concerné : « Voir comme le client ») ;
 3. limite de requêtes par adresse IP (freine le devinage de liens) ;
 4. en-têtes : pas d'indexation par les moteurs de recherche, pas de fuite du lien via le « Referer »,
    pas de mise en cache des pages contenant des prix.
"""
from datetime import timedelta
from functools import wraps

from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from .models import Demande


def _ip(request):
    return request.META.get("REMOTE_ADDR", "inconnue")


def _en_tetes(reponse):
    reponse["Referrer-Policy"] = "no-referrer"
    reponse["X-Robots-Tag"] = "noindex, nofollow, noarchive"
    reponse["Cache-Control"] = "no-store, private"
    return reponse


def demande_du_lien(request, token):
    """Retourne la demande liée au jeton, ou lève Http404. Renvoie (demande, expiree)."""
    demande = get_object_or_404(Demande.objects.select_related("client", "service"), token_suivi=token)
    jours = getattr(settings, "SUIVI_VALIDITE_JOURS", 90)
    expiree = False
    if jours and not (request.user.is_authenticated and request.user.is_staff):
        expiree = demande.updated_at < timezone.now() - timedelta(days=jours)
    return demande, expiree


def suivi_securise(vue):
    """Décorateur : limite de débit + en-têtes de sécurité (l'expiration est gérée par demande_du_lien)."""
    @wraps(vue)
    def enveloppe(request, *args, **kwargs):
        limite = getattr(settings, "SUIVI_LIMITE_PAR_MINUTE", 60)
        cle = f"suivi:{_ip(request)}"
        n = cache.get(cle, 0)
        if limite and n >= limite:
            return _en_tetes(HttpResponse("Trop de requêtes. Patientez une minute puis réessayez.", status=429,
                                          content_type="text/plain; charset=utf-8"))
        cache.set(cle, n + 1, 60)
        return _en_tetes(vue(request, *args, **kwargs))
    return enveloppe


def page_expiree(request):
    return render(request, "demandes/suivi_expire.html", status=410)
