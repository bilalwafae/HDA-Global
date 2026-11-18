"""
Couche IA pour la génération de devis automatiques (H.D.A GLOBAL).

- Appel HTTPS DIRECT à l'API Anthropic (urllib, bibliothèque standard du
  système : aucune dépendance externe à installer).
- Config : ANTHROPIC_API_KEY (via .env / python-decouple), ANTHROPIC_MODEL.
- La sortie de l'IA est TOUJOURS VALIDÉE par analyser_reponse_json() :
  on n'accepte que surface_m2 (numérique), postes (codes existants au
  catalogue), resume, urgence, questions. Aucun prix ne transite ici —
  ce que l'IA renverrait serait de toute façon ignoré.
- L'IA est OPTIONNELLE : sans clé API, ou en cas d'erreur (réseau, quota,
  JSON invalide, timeout), le devis se génère quand même via le repli local
  (extraire_surface_regex + formules du catalogue). L'IA ne bloque jamais
  le flux métier.

CONFIDENTIALITÉ : seuls le service, la ville, la surface et la description
libre sont envoyés à l'IA — jamais le nom, l'email ou le téléphone du client.
À signaler à l'entreprise : la loi marocaine 09-08 / CNDP demande la
protection des données personnelles ; l'envoi de la description à un
prestataire IA (serveurs hors Maroc) doit être mentionné dans la politique de
confidentialité.
"""
import json
import re
import unicodedata
from decimal import Decimal, InvalidOperation
from urllib import request as urllib_request
from urllib.error import URLError, HTTPError

from decouple import config
from django.conf import settings

API_URL = "https://api.anthropic.com/v1/messages"
API_VERSION = "2023-06-01"
TIMEOUT_SECONDES = 20

# Longueurs maximales acceptées sur les champs libres (sécurité anti-abus)
LE_MAX_RESUME = 300
MAX_QUESTION = 200
MAX_URGENCE = 20
MAX_QUESTIONS = 3
MAX_POSTES = 6


def ia_disponible() -> bool:
    """True si une clé API Anthropic est configurée (sinon le devis
    se calcule localement : IA jamais bloquante)."""
    return bool(config("ANTHROPIC_API_KEY", default=""))


def construire_prompt(service_nom, ville, surface_saisie, description, codes_catalogue) -> str:
    """
    Construit le prompt de qualification du besoin.

    Consignes clés :
    - réponse STRICTEMENT au format JSON (un seul objet, pas de texte autour) ;
    - postes : 2 à 6 codes parmi ceux passés (jamais de code inventé) ;
    - questions de l'IA ajoutées aux alertes ;
    - INTERDIT de proposer des prix ou des montants : ils viennent du catalogue
      et de pricing.py côté serveur.
    """
    service = service_nom or "non précisé"
    retour = (
        "Répond STRICTEMENT au format JSON (un seul objet, sans commentaire, "
        "sans texte autour) :\n"
        "{\n"
        '  "surface_m2": <nombre ou null si inconnue>,\n'
        '  "postes": [<codes>, 2 à 6],\n'
        '  "resume": "<1 phrase en français, max 300 caractères>",\n'
        '  "urgence": "<basse|moyenne|haute, max 20 caractères>",\n'
        '  "questions": ["<question à poser au client>", 0 à 3]\n'
        "}\n"
        "INTERDICTIONS absolues :\n"
        "- proposer un prix, un montant, un taux, une remise : tout chiffre "
        "financier est interdit et serait ignoré (les prix viennent de la "
        "grille du catalogue, côté serveur) ;\n"
        "- inventer des codes de postes : seuls les codes ci-dessous existent ;\n"
        "- inclure le code de déplacement : il ne s'applique pas.\n"
    )
    catalogue = ", ".join(codes_catalogue)
    contexte = (
        f"Service demandé : {service}\n"
        f"Ville du chantier : {ville or 'non précisée'}\n"
        f"Surface saisie par le client : {surface_saisie or 'non précisée'}\n"
        f"Description libre du client (français, parfois darija, avec fautes de frappe) :\n"
        f"{(description or '').strip()[:2000]}\n"
        f"Codes de postes disponibles au catalogue : {catalogue}\n"
    )
    return retour + "\n" + contexte


def analyser_demande(service_nom, ville, surface_saisie, description, codes_catalogue=None) -> dict:
    """
    Analyse IA d'une demande. Retourne TOUJOURS un dict (sortie validée) :
    - {} en cas d'absence de clé, d'erreur réseau/quota ou de sortie invalide.
    - {surface_m2, postes, resume, urgence, questions} sinon (sous-ensemble validé).
    Appel HTTP sans dépendance externe (urllib, bibliothèque standard).
    """
    if not ia_disponible():
        return {}

    if codes_catalogue is None:
        from .auto import CATALOGUE, CODE_DEPLACEMENT
        codes_catalogue = [c for c in CATALOGUE if c != CODE_DEPLACEMENT]

    prompt = construire_prompt(service_nom, ville, surface_saisie, description, codes_catalogue)
    payload = json.dumps({
        "model": config("ANTHROPIC_MODEL", default="claude-sonnet-4-5-20250929"),
        "max_tokens": 500,
        "messages": [
            {"role": "user", "content": prompt}
        ],
    }).encode("utf-8")

    req = urllib_request.Request(
        API_URL,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "x-api-key": config("ANTHROPIC_API_KEY", default=""),
            "anthropic-version": API_VERSION,
        },
        method="POST",
    )

    try:
        with urllib_request.urlopen(req, timeout=TIMEOUT_SECONDES) as reponse:
            corps = json.loads(reponse.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, ValueError):
        # Réseau indisponible, quota 429, authentification 401 ou corps non JSON
        return {}

    # Corps Anthropic : {"content": [{"type": "text", "text": "..."}]}
    texte = ""
    for bloc in corps.get("content", []):
        if isinstance(bloc, dict) and bloc.get("type") == "text":
            texte += bloc.get("text", "")

    return analyser_reponse_json(texte)


def analyser_reponse_json(texte: str) -> dict:
    """
    VALIDE une sortie d'IA et en extrait uniquement les champs autorisés.

    - Extrait l'objet JSON (gère les cas où l'IA entoure le JSON de texte).
    - postes : ne garde que les codes existant au catalogue (hors déplacement).
    - borne les longueurs (resume, question, urgence) ;
    - ignore tout autre champ (par exemple un prix que l'IA aurait proposé) ;
    - retourne {} si la sortie est totalement invalide.
    """
    if not texte or not texte.strip():
        return {}

    json_extrait = extraire_json(texte)
    if json_extrait is None:
        return {}

    try:
        donnees = json.loads(json_extrait)
    except (json.JSONDecodeError, ValueError):
        return {}
    if not isinstance(donnees, dict):
        return {}

    resultat: dict = {}

    # surface_m2 : numérique, boré (anti « 9999999 m² »)
    surface = donnees.get("surface_m2")
    if surface is not None:
        try:
            valeur = Decimal(str(surface))
            if 0 < valeur <= Decimal("100000"):
                resultat["surface_m2"] = valeur
        except (InvalidOperation, ValueError):
            pass

    # postes : uniquement des codes réels du catalogue, hors déplacement
    from .auto import CATALOGUE, CODE_DEPLACEMENT  # import tardif : évite le cycle ai↔auto
    postes_bruts = donnees.get("postes")
    if isinstance(postes_bruts, list):
        postes_valides = []
        for code in postes_bruts:
            if isinstance(code, str) and re.fullmatch(r"[A-Z0-9\-]{2,20}", code.strip()):
                net = code.strip()
                if net in CATALOGUE and net != CODE_DEPLACEMENT and net not in postes_valides:
                    postes_valides.append(net)
            if len(postes_valides) >= MAX_POSTES:
                break
        if postes_valides:
            resultat["postes"] = postes_valides

    resume = donnees.get("resume")
    if isinstance(resume, str) and resume.strip():
        resultat["resume"] = resume.strip()[:LE_MAX_RESUME]

    urgence = donnees.get("urgence")
    if isinstance(urgence, str) and urgence.strip():
        resultat["urgence"] = urgence.strip().lower()[:MAX_URGENCE]

    questions = donnees.get("questions")
    if isinstance(questions, list):
        questions_valides = []
        for question in questions:
            if isinstance(question, str) and question.strip():
                questions_valides.append(question.strip()[:MAX_QUESTION])
            if len(questions_valides) >= MAX_QUESTIONS:
                break
        if questions_valides:
            resultat["questions"] = questions_valides

    return resultat


def extraire_json(texte: str):
    """
    Extrait la première expression JSON objet (entre accolades équilibrées)
    d'un texte qui peut contenir du texte autour. Retourne la CHAÎNE JSON
    (pas l'objet) ou None.
    """
    texte = texte.strip()
    debut = texte.find("{")
    if debut < 0:
        return None

    prof = 0
    fin = -1
    dans_chaine = False
    echappe = False
    for i in range(debut, len(texte)):
        c = texte[i]
        if dans_chaine:
            if echappe:
                echappe = False
            elif c == "\\":
                echappe = True
            elif c == '"':
                dans_chaine = False
        elif c == '"':
            dans_chaine = True
        elif c == "{":
            prof += 1
        elif c == "}":
            prof -= 1
            if prof == 0:
                fin = i
                break
    if fin < 0:
        return None
    return texte[debut:fin + 1]


def extraire_surface_regex(texte: str):
    """
    Repli local SANS IA : extraction d'une surface du texte du client.

    Reconnaît « 85 m2 », « 85m2 », « 12,5 m² », « 90 M2 », « 85 m² ».
    Prend la PLUS GRANDE valeur trouvée (l'appartement est plus grand que la
    terrasse). L'IA n'est pas sollicitée ici : c'est un pur repli local.
    Limite connue : « 85m » sans « 2 » n'est pas reconnu — un des cas que
    l'IA doit rattraper (français, darija, fautes de frappe).
    """
    if not texte:
        return None
    texte_norm = unicodedata.normalize("NFKD", texte).encode("ascii", "ignore").decode("ascii")

    valeurs = re.findall(r"(\d+(?:[.,]\d+)?)\s*(?:m\s?2|m\s?square|m²|m2)", texte_norm, flags=re.IGNORECASE)
    if not valeurs:
        return None

    meilleure = None
    for brut in valeurs:
        try:
            valeur = Decimal(brut.replace(",", "."))
        except (InvalidOperation, ValueError):
            continue
        if valeur > 0 and (meilleure is None or valeur > meilleure):
            meilleure = valeur
    return meilleure
