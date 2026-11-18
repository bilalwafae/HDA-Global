"""
Workflow « demande acceptée » → devis généré → relecture admin → envoi au client.

Règle métier : dès que l'administrateur passe une demande au statut « Acceptée »,
le devis est GÉNÉRÉ AUTOMATIQUEMENT (lignes, totaux, PDF au format officiel avec logo).
Il reste « brouillon » : l'administrateur le relit puis clique sur « Envoyer au client ».
Rien ne part tout seul vers le client.
"""
from django.conf import settings


def devis_auto_a_l_acceptation(demande):
    """
    Génère le devis brouillon d'une demande acceptée.
    Retourne (devis | None, cree: bool). Jamais d'exception : en cas d'échec -> (None, False).
    Idempotent : si un devis actif existe déjà, il est réutilisé (pas de doublon).
    """
    if not getattr(settings, "DEVIS_AUTO_A_L_ACCEPTATION", True):
        return None, False
    try:
        from .auto import generer_devis_automatique
        existant = demande.get_devis_actif()
        if existant is not None:
            return existant, False
        return generer_devis_automatique(demande, utiliser_ia=True), True
    except Exception as e:  # ne jamais bloquer le changement de statut
        print(f"[DEVIS AUTO] échec pour {demande.reference}: {e}")
        return None, False
