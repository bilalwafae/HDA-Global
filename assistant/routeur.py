"""
Routeur de questions SANS IA : comprend une question libre (période, ville, client, service…),
choisit l'outil de données adapté et renvoie son résultat calculé par la base.

Il sert à trois choses :
 1. garde-fou de PÉRIMÈTRE : une question qui ne parle pas des données de l'entreprise est refusée
    avant même d'appeler le modèle ;
 2. filet de sécurité : si l'IA est indisponible, saturée, ne sait pas utiliser les outils ou répond
    sans interroger la base, la question est traitée ici, avec les mêmes outils ;
 3. cohérence : les chiffres viennent toujours de `assistant/outils.py` (jamais d'une estimation).
"""
import re
from calendar import monthrange
from datetime import date, timedelta

from clients.models import Client
from demandes.models import Demande
from interventions.models import Intervention
from services.models import Service

from .outils import _norm

MOIS = {"janvier": 1, "fevrier": 2, "mars": 3, "avril": 4, "mai": 5, "juin": 6, "juillet": 7, "aout": 8,
        "septembre": 9, "octobre": 10, "novembre": 11, "decembre": 12}

# mots qui prouvent que la question porte sur les données de H.D.A GLOBAL
MOTS_METIER = ("demande", "devis", "client", "intervention", "chantier", "service", "chiffre d'affaire",
               "chiffre affaire", "affaires", "argent", "revenu", "gagne", "rapporte", "montant", "ville",
               "statut", "planning", "planifi", "travaux", "accepte", "refuse", "en attente", "en cours",
               "termine", "rentable", "factur", "encaiss", "recettes", "turnover", "benefice")
SALUTATIONS = ("bonjour", "bonsoir", "salut", "salam", "hello", "merci")


def _periode(q: str):
    """(date_debut, date_fin, libellé) ; (None, None, None) = toute la période."""
    auj = date.today()
    m = re.search(r"\b(20\d\d)\b", q)
    annee = int(m.group(1)) if m else None
    for nom, num in MOIS.items():
        if re.search(rf"\b{nom}\b", q):
            a = annee or auj.year
            return date(a, num, 1), date(a, num, monthrange(a, num)[1]), f"{nom} {a}"
    if re.search(r"mois (dernier|precedent|passe)", q):
        fin = auj.replace(day=1) - timedelta(days=1)
        return fin.replace(day=1), fin, "mois dernier"
    if re.search(r"(ce mois|mois en cours|mois courant)", q):
        return auj.replace(day=1), date(auj.year, auj.month, monthrange(auj.year, auj.month)[1]), "ce mois-ci"
    if re.search(r"(annee derniere|annee passee)", q):
        return date(auj.year - 1, 1, 1), date(auj.year - 1, 12, 31), str(auj.year - 1)
    if re.search(r"(cette annee|annee en cours|annee courante)", q):
        return date(auj.year, 1, 1), date(auj.year, 12, 31), str(auj.year)
    t = re.search(r"\b(?:t|trimestre )([1-4])\b", q)
    if t:
        a = annee or auj.year
        mois_deb = 3 * (int(t.group(1)) - 1) + 1
        return date(a, mois_deb, 1), date(a, mois_deb + 2, monthrange(a, mois_deb + 2)[1]), f"T{t.group(1)} {a}"
    if annee:
        return date(annee, 1, 1), date(annee, 12, 31), str(annee)
    return None, None, None


def _villes_connues():
    vus = {}
    for v in list(Intervention.objects.values_list("ville", flat=True)) + list(
            Demande.objects.values_list("ville_chantier", flat=True)):
        if v and _norm(v):
            vus.setdefault(_norm(v), v.strip())
    return vus


def _contient(q: str, mot: str) -> bool:
    return re.search(rf"(?<![a-z0-9]){re.escape(mot)}(?![a-z0-9])", q) is not None


def dans_le_perimetre(question: str) -> bool:
    q = _norm(question)
    if any(m in q for m in MOTS_METIER) or re.search(r"\b(dem|dev)-\d{4}-\d+", q):
        return True
    noms = [_norm(c.nom_complet) for c in Client.objects.all()] + [_norm(s.nom) for s in Service.objects.all()]
    return any(n and len(n) > 3 and n in q for n in noms) or any(_contient(q, v) for v in _villes_connues())


def est_salutation(question: str) -> bool:
    q = _norm(question)
    return len(q) < 30 and any(q.startswith(s) for s in SALUTATIONS)


def router(question: str):
    """Retourne (nom_outil, arguments) ou None si la question n'est pas comprise."""
    q = re.sub(r"[?!.,;:]", " ", _norm(question)); q = " ".join(q.split())
    d1, d2, _ = _periode(q)
    dates = {}
    if d1 and d2:
        dates = {"date_debut": d1.isoformat(), "date_fin": d2.isoformat()}

    ref = re.search(r"\b(dem|dev)-\d{4}-\d+", q)
    if ref:
        return "rechercher_demande", {"texte": ref.group(0).upper().replace("DEV", "DEM")}

    # un client cité par son nom ou son email ?
    for c in Client.objects.all():
        if _norm(c.nom_complet) in q or (c.email and _norm(c.email) in q):
            return "activite_client", {"client": c.nom_complet, **dates}
    m = re.search(r"\bclient\s+([a-z' -]{3,40})$", q)
    if m and not re.search(r"(combien|par client|liste)", q):
        return "activite_client", {"client": m.group(1).strip(), **dates}

    statut = None
    for mot, st in (("termin", "terminee"), ("en cours", "en_cours"), ("planifi", "planifiee"), ("annul", "annulee")):
        if mot in q:
            statut = st
            break

    if re.search(r"(chiffre d.?affaire|chiffre affaire|\bca\b|argent|revenu|gagn|rapporte|recettes|encaiss|factur|montant)", q) \
            and not re.search(r"(service le plus|classement)", q):
        groupe = "aucun"
        for cle, mots in (("mois", r"par mois|mensuel|chaque mois"), ("service", r"par service"),
                          ("ville", r"par ville"), ("client", r"par client")):
            if re.search(mots, q):
                groupe = cle
                break
        return "chiffre_affaires", {**dates, "regrouper_par": groupe}

    if re.search(r"(service.*(plus demande|populaire|rentable|classement|demande)|plus demande|rentable|classement)", q):
        return "classement_services", dates

    if re.search(r"(intervention|chantier|travaux|planning|planifi)", q):
        for cle, nom in _villes_connues().items():
            if _contient(q, cle):
                return "interventions_d_une_ville", {"ville": nom, **dates, **({"statut": statut} if statut else {})}
        return "interventions_par_ville", {**dates, **({"statut": statut} if statut else {})}

    if re.search(r"(demande|statut|devis|combien)", q):
        return "statistiques_demandes", dates

    for cle, nom in _villes_connues().items():
        if _contient(q, cle):
            return "interventions_d_une_ville", {"ville": nom, **dates}
    return None
