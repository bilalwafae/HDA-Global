"""
Outils de données de l'assistant IA (aucune IA ici : uniquement des requêtes ORM).

Règle d'or : tous les chiffres donnés à l'administrateur sont CALCULÉS ICI, de façon
déterministe, à partir de la base. Le modèle de langage ne fait que choisir l'outil et
reformuler le résultat ; il ne calcule jamais.

Définitions (rappelées dans chaque résultat, champ « definitions ») :
- Intervention « dans la période » = date de début des travaux comprise dans la période.
- Chiffre d'affaires = somme des devis au statut « Accepté », par date d'émission du devis.
- Demandes « dans la période » = date de création de la demande.
"""
import unicodedata
from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP

from clients.models import Client
from demandes.models import Demande
from devis.models import Devis
from interventions.models import Intervention

MAX_LIGNES = 40  # taille maximale des listes détaillées renvoyées au modèle

STATUTS_INTERVENTION = [c[0] for c in Intervention.STATUT_CHOICES]
STATUTS_DEMANDE = [c[0] for c in Demande.STATUT_CHOICES]


# ─── utilitaires ────────────────────────────────────────────────────────────
def _norm(texte) -> str:
    """Minuscule, sans accents ni espaces superflus : « Mohammédia » == « mohammedia »."""
    texte = unicodedata.normalize("NFKD", str(texte or ""))
    return " ".join("".join(c for c in texte if not unicodedata.combining(c)).lower().split())


def _date(valeur, nom):
    if valeur in (None, ""):
        return None
    if isinstance(valeur, date):
        return valeur
    try:
        return datetime.strptime(str(valeur).strip()[:10], "%Y-%m-%d").date()
    except ValueError:
        raise ValueError(f"{nom} invalide : « {valeur} » (format attendu AAAA-MM-JJ).")


def _periode(date_debut, date_fin):
    d1, d2 = _date(date_debut, "date_debut"), _date(date_fin, "date_fin")
    if d1 and d2 and d1 > d2:
        raise ValueError("date_debut est postérieure à date_fin.")
    return d1, d2


def _joli(nom: str, ancien: str = "") -> str:
    """Nom de ville affiché : préfère la graphie avec majuscule (« Casablanca » plutôt que « casablanca »)."""
    nom = " ".join(str(nom).split())
    return nom if (nom[:1].isupper() or not ancien) and not (ancien[:1].isupper() and not nom[:1].isupper()) else ancien


def _q2(valeur) -> Decimal:
    return Decimal(valeur or 0).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def mad(valeur) -> str:
    """12345.6 -> « 12 345,60 MAD »."""
    v = _q2(valeur)
    entier, dec = f"{v:.2f}".split(".")
    entier = f"{int(entier):,}".replace(",", " ")
    return f"{entier},{dec} MAD"


def _periode_txt(d1, d2) -> str:
    if d1 and d2:
        return f"du {d1:%d/%m/%Y} au {d2:%d/%m/%Y}"
    if d1:
        return f"à partir du {d1:%d/%m/%Y}"
    if d2:
        return f"jusqu'au {d2:%d/%m/%Y}"
    return "toute la période (sans filtre de dates)"


DEFINITIONS = {
    "intervention": "Intervention dans la période = date de début des travaux comprise dans la période.",
    "chiffre_affaires": "Chiffre d'affaires = somme des devis au statut « Accepté » (montants HT et TTC), "
                        "par date d'émission du devis.",
    "demande": "Demande dans la période = date de création de la demande.",
}


def _interv_qs(d1, d2, statut=None):
    qs = Intervention.objects.select_related("demande__client", "demande__service")
    if d1:
        qs = qs.filter(date_debut__gte=d1)
    if d2:
        qs = qs.filter(date_debut__lte=d2)
    if statut:
        if statut not in STATUTS_INTERVENTION:
            raise ValueError(f"statut inconnu « {statut} » ; valeurs possibles : {', '.join(STATUTS_INTERVENTION)}.")
        qs = qs.filter(statut_chantier=statut)
    return qs


def _devis_acceptes(d1, d2):
    qs = Devis.objects.filter(statut=Devis.STATUT_ACCEPTE).select_related("demande__client", "demande__service")
    if d1:
        qs = qs.filter(date_emission__gte=d1)
    if d2:
        qs = qs.filter(date_emission__lte=d2)
    return qs


def _ligne_interv(i):
    d = i.demande
    return {
        "reference": d.reference,
        "client": d.client.nom_complet,
        "service": d.service.nom if d.service else "—",
        "ville": i.ville,
        "date_debut": i.date_debut.strftime("%d/%m/%Y"),
        "date_fin_prevue": i.date_fin.strftime("%d/%m/%Y") if i.date_fin else "—",
        "statut": i.get_statut_chantier_display(),
        "responsable": i.responsable_chantier,
    }


def _compter_statuts(interventions):
    out = defaultdict(int)
    for i in interventions:
        out[i.get_statut_chantier_display()] += 1
    return dict(out)


# ─── OUTILS ─────────────────────────────────────────────────────────────────
def interventions_par_ville(date_debut=None, date_fin=None, statut=None):
    """Nombre d'interventions par ville, sur une période (optionnelle)."""
    d1, d2 = _periode(date_debut, date_fin)
    ints = list(_interv_qs(d1, d2, statut))
    comptes = defaultdict(int)
    noms = {}
    for i in ints:
        cle = _norm(i.ville)
        comptes[cle] += 1
        noms[cle] = _joli(i.ville, noms.get(cle, ""))
    lignes = sorted(({"ville": noms[k], "nombre": n} for k, n in comptes.items()),
                    key=lambda x: (-x["nombre"], x["ville"]))
    return {"periode": _periode_txt(d1, d2), "filtre_statut": statut or "tous les statuts",
            "total_interventions": len(ints), "par_ville": lignes,
            "definitions": [DEFINITIONS["intervention"]]}


def interventions_d_une_ville(ville, date_debut=None, date_fin=None, statut=None):
    """Interventions réalisées/planifiées dans UNE ville (nombre + liste détaillée)."""
    if not ville:
        raise ValueError("Le nom de la ville est obligatoire.")
    d1, d2 = _periode(date_debut, date_fin)
    cible = _norm(ville)
    ints = [i for i in _interv_qs(d1, d2, statut).order_by("date_debut") if cible in _norm(i.ville)]
    villes = sorted({i.ville.strip() for i in ints})
    return {"ville_recherchee": ville, "villes_correspondantes": villes, "periode": _periode_txt(d1, d2),
            "filtre_statut": statut or "tous les statuts", "nombre_interventions": len(ints),
            "repartition_par_statut": _compter_statuts(ints),
            "interventions": [_ligne_interv(i) for i in ints[:MAX_LIGNES]],
            "liste_tronquee": len(ints) > MAX_LIGNES,
            "definitions": [DEFINITIONS["intervention"]]}


def _trouver_clients(texte):
    cible = _norm(texte)
    tous = list(Client.objects.all())
    exacts = [c for c in tous if _norm(c.nom_complet) == cible or _norm(c.email) == cible]
    return exacts or [c for c in tous if cible and (cible in _norm(c.nom_complet) or cible in _norm(c.email))]


def activite_client(client, date_debut=None, date_fin=None):
    """Activité d'UN client : demandes, interventions, devis acceptés et montant."""
    if not client:
        raise ValueError("Le nom (ou l'email) du client est obligatoire.")
    d1, d2 = _periode(date_debut, date_fin)
    trouves = _trouver_clients(client)
    if not trouves:
        return {"client_recherche": client, "trouve": False,
                "message": "Aucun client ne correspond à ce nom dans la base."}
    if len(trouves) > 1:
        return {"client_recherche": client, "trouve": False, "ambigu": True,
                "clients_possibles": [{"nom": c.nom_complet, "email": c.email} for c in trouves[:10]],
                "message": "Plusieurs clients correspondent : demander à l'administrateur de préciser."}
    c = trouves[0]
    demandes = list(c.demandes.select_related("service")) if hasattr(c, "demandes") else \
        list(Demande.objects.filter(client=c).select_related("service"))
    ints = [i for i in _interv_qs(d1, d2) if i.demande.client_id == c.pk]
    devis = [d for d in _devis_acceptes(d1, d2) if d.demande.client_id == c.pk]
    return {"client": c.nom_complet, "email": c.email, "ville_residence": c.ville, "periode": _periode_txt(d1, d2),
            "nombre_demandes_total": len(demandes),
            "nombre_interventions": len(ints), "repartition_interventions_par_statut": _compter_statuts(ints),
            "interventions": [_ligne_interv(i) for i in ints[:MAX_LIGNES]],
            "nombre_devis_acceptes": len(devis),
            "montant_devis_acceptes_ht": mad(sum((d.sous_total_ht for d in devis), Decimal(0))),
            "montant_devis_acceptes_ttc": mad(sum((d.total_ttc for d in devis), Decimal(0))),
            "definitions": [DEFINITIONS["intervention"], DEFINITIONS["chiffre_affaires"]]}


def classement_services(date_debut=None, date_fin=None):
    """Par service : nombre de demandes, devis acceptés et argent gagné. Désigne le plus demandé et le plus rentable."""
    d1, d2 = _periode(date_debut, date_fin)
    dem = Demande.objects.select_related("service")
    if d1:
        dem = dem.filter(created_at__date__gte=d1)
    if d2:
        dem = dem.filter(created_at__date__lte=d2)
    agg = defaultdict(lambda: {"demandes": 0, "devis_acceptes": 0, "ht": Decimal(0), "ttc": Decimal(0)})
    for d in dem:
        agg[d.service.nom if d.service else "Sans service"]["demandes"] += 1
    for dv in _devis_acceptes(d1, d2):
        a = agg[dv.demande.service.nom if dv.demande.service else "Sans service"]
        a["devis_acceptes"] += 1
        a["ht"] += dv.sous_total_ht
        a["ttc"] += dv.total_ttc
    lignes = [{"service": s, "nombre_demandes": a["demandes"], "devis_acceptes": a["devis_acceptes"],
               "chiffre_affaires_ht": mad(a["ht"]), "chiffre_affaires_ttc": mad(a["ttc"]), "_ttc": a["ttc"]}
              for s, a in agg.items()]
    lignes.sort(key=lambda x: (-x["nombre_demandes"], x["service"]))
    res = {"periode": _periode_txt(d1, d2), "total_demandes": sum(l["nombre_demandes"] for l in lignes),
           "services": lignes, "definitions": [DEFINITIONS["demande"], DEFINITIONS["chiffre_affaires"]]}
    if lignes:
        maxi = lignes[0]["nombre_demandes"]
        res["service_le_plus_demande"] = [l["service"] for l in lignes if l["nombre_demandes"] == maxi]
        ca_max = max(l["_ttc"] for l in lignes)
        if ca_max > 0:
            res["service_le_plus_rentable_ttc"] = [l["service"] for l in lignes if l["_ttc"] == ca_max]
    for l in lignes:
        l.pop("_ttc")
    return res


def chiffre_affaires(date_debut=None, date_fin=None, regrouper_par="aucun"):
    """Chiffre d'affaires (devis acceptés) total ou regroupé par service / ville / client / mois."""
    if regrouper_par not in ("aucun", "service", "ville", "client", "mois"):
        raise ValueError("regrouper_par doit être : aucun, service, ville, client ou mois.")
    d1, d2 = _periode(date_debut, date_fin)
    devis = list(_devis_acceptes(d1, d2))
    res = {"periode": _periode_txt(d1, d2), "nombre_devis_acceptes": len(devis),
           "total_ht": mad(sum((d.sous_total_ht for d in devis), Decimal(0))),
           "total_ttc": mad(sum((d.total_ttc for d in devis), Decimal(0))),
           "definitions": [DEFINITIONS["chiffre_affaires"]]}
    if regrouper_par != "aucun":
        def cle(d):
            if regrouper_par == "service":
                return d.demande.service.nom if d.demande.service else "Sans service"
            if regrouper_par == "ville":
                return d.demande.ville_chantier
            if regrouper_par == "client":
                return d.demande.client.nom_complet
            return d.date_emission.strftime("%Y-%m")
        g = defaultdict(lambda: [0, Decimal(0), Decimal(0)])
        for d in devis:
            x = g[cle(d)]
            x[0] += 1; x[1] += d.sous_total_ht; x[2] += d.total_ttc
        lignes = sorted(g.items(), key=lambda kv: (kv[0] if regrouper_par == "mois" else -kv[1][2]))
        res["regroupement"] = regrouper_par
        res["lignes"] = [{"groupe": k, "devis_acceptes": v[0], "total_ht": mad(v[1]), "total_ttc": mad(v[2])}
                         for k, v in lignes[:MAX_LIGNES]]
    return res


def statistiques_demandes(date_debut=None, date_fin=None):
    """Nombre de demandes par statut et par ville de chantier."""
    d1, d2 = _periode(date_debut, date_fin)
    qs = Demande.objects.all()
    if d1:
        qs = qs.filter(created_at__date__gte=d1)
    if d2:
        qs = qs.filter(created_at__date__lte=d2)
    dem = list(qs)
    par_statut, par_ville, noms = defaultdict(int), defaultdict(int), {}
    for d in dem:
        par_statut[d.get_statut_display()] += 1
        k = _norm(d.ville_chantier); par_ville[k] += 1; noms[k] = _joli(d.ville_chantier, noms.get(k, ""))
    return {"periode": _periode_txt(d1, d2), "total_demandes": len(dem), "par_statut": dict(par_statut),
            "par_ville": sorted(({"ville": noms[k], "nombre": n} for k, n in par_ville.items()),
                                key=lambda x: (-x["nombre"], x["ville"])),
            "definitions": [DEFINITIONS["demande"]]}


def rechercher_demande(texte):
    """Retrouve une demande par référence (DEM-2026-0007) ou par nom de client."""
    if not texte:
        raise ValueError("Le texte de recherche est obligatoire.")
    cible = _norm(texte)
    res = [d for d in Demande.objects.select_related("client", "service")
           if cible in _norm(d.reference) or cible in _norm(d.client.nom_complet)]
    out = []
    for d in res[:MAX_LIGNES]:
        dv = d.get_devis_actif()
        out.append({"reference": d.reference, "client": d.client.nom_complet,
                    "service": d.service.nom if d.service else "—", "ville": d.ville_chantier,
                    "statut": d.get_statut_display(), "date_creation": d.created_at.strftime("%d/%m/%Y"),
                    "devis": f"{dv.numero} ({dv.get_statut_display()}) — {mad(dv.total_ttc)} TTC" if dv else "aucun"})
    return {"recherche": texte, "nombre_resultats": len(res), "demandes": out, "liste_tronquee": len(res) > MAX_LIGNES}


# ─── Registre + schéma (format « function calling » OpenAI / OpenRouter) ───
_DATES = {
    "date_debut": {"type": "string", "description": "Début de période AAAA-MM-JJ (optionnel)."},
    "date_fin": {"type": "string", "description": "Fin de période AAAA-MM-JJ incluse (optionnel)."},
}
_STATUT_I = {"type": "string", "enum": STATUTS_INTERVENTION, "description": "Filtre sur le statut du chantier (optionnel)."}


def _fn(nom, desc, props, required=()):
    return {"type": "function", "function": {"name": nom, "description": desc,
            "parameters": {"type": "object", "properties": props, "required": list(required)}}}


OUTILS = {
    "interventions_par_ville": interventions_par_ville,
    "interventions_d_une_ville": interventions_d_une_ville,
    "activite_client": activite_client,
    "classement_services": classement_services,
    "chiffre_affaires": chiffre_affaires,
    "statistiques_demandes": statistiques_demandes,
    "rechercher_demande": rechercher_demande,
}

SCHEMAS = [
    _fn("interventions_par_ville", "Nombre d'interventions de chantier PAR VILLE (toutes les villes), sur une période.",
        {**_DATES, "statut": _STATUT_I}),
    _fn("interventions_d_une_ville", "Nombre et liste des interventions dans UNE ville donnée, sur une période.",
        {"ville": {"type": "string"}, **_DATES, "statut": _STATUT_I}, ["ville"]),
    _fn("activite_client", "Activité d'UN client : demandes, interventions, devis acceptés et argent rapporté.",
        {"client": {"type": "string", "description": "Nom ou email du client."}, **_DATES}, ["client"]),
    _fn("classement_services", "Classement des services : le plus demandé, nombre de demandes, argent gagné par service.",
        {**_DATES}),
    _fn("chiffre_affaires", "Chiffre d'affaires (devis acceptés), total ou regroupé par service, ville, client ou mois.",
        {**_DATES, "regrouper_par": {"type": "string", "enum": ["aucun", "service", "ville", "client", "mois"]}}),
    _fn("statistiques_demandes", "Nombre de demandes de devis par statut et par ville, sur une période.", {**_DATES}),
    _fn("rechercher_demande", "Retrouver une demande par sa référence (ex. DEM-2026-0007) ou le nom du client.",
        {"texte": {"type": "string"}}, ["texte"]),
]


def executer(nom, arguments: dict):
    """Exécute un outil ; ne lève jamais : renvoie {'erreur': ...} lisible par le modèle."""
    fn = OUTILS.get(nom)
    if fn is None:
        return {"erreur": f"Outil inconnu : {nom}."}
    try:
        args = {k: v for k, v in (arguments or {}).items() if v not in (None, "")}
        return fn(**args)
    except TypeError as e:
        return {"erreur": f"Paramètres invalides pour {nom} : {e}"}
    except ValueError as e:
        return {"erreur": str(e)}
    except Exception as e:  # sécurité : jamais de crash côté chat
        return {"erreur": f"Erreur interne dans {nom} : {e}"}
