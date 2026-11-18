"""
Analyse VISUELLE des photos de chantier (PIÈCES JOINTES) pour enrichir
le brouillon de devis automatique — priorité 1 de la feuille de route.

Principe (inchangé) :
- L'IA « regarde » un petit nombre de photos et renvoie des OBSERVATIONS
  structurées (état, type de pièces, contrainte d'accès, hauteur, humidité...).
- Le MOTEUR reste seul maître des prix : la sortie de la vision ne peut
  contenir qu'observations / indices / questions — tout champ « prix »,
  « montant », « devis »... est IGNORÉ (voir valider_reponse_vision).
- L'IA est OPTIONNELLE et ne bloque JAMAIS : sans clé API, sans image
  exploitable ou sur erreur (réseau, quota, format), retour {} et le flux
  continue avec l'analyse texte seule.

Confidentialité : les photos sont envoyées sans le nom ni les coordonnées
du client (loi 09-08 / CNDP — à mentionner dans la politique de
confidentialité de l'entreprise).
"""
import base64
import json
from urllib import request as urllib_request
from urllib.error import HTTPError, URLError

from django.conf import settings

from . import ai as couche_ia

MAX_PHOTOS = getattr(settings, "DEVIS_VISION_MAX_PHOTOS", 3)
TAILLE_MAX_PHOTO = 1_200_000  # octets (~1,2 Mo par photo envoyée)
FORMATS_ACCEPTES = {"jpeg", "jpg", "png", "webp"}
LE_MAX_OBSERVATIONS = 380
MAX_INDICES = 6
MAX_QUESTION = 200

MEDIA_TYPE = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "webp": "image/webp"}


def valider_reponse_vision(donnees) -> dict:
    """
    VALIDE la sortie du modèle de vision : ne conserve que
    observations / indices / questions, aux longueurs bornées.
    Retourne {} si rien d'exploitable. Toute tentative de « prix », de
    « montant » ou de coût est ignorée.
    """
    if not isinstance(donnees, dict):
        return {}

    resultat: dict = {}

    observations = donnees.get("observations")
    if isinstance(observations, str) and observations.strip():
        resultat["observations"] = observations.strip()[:LE_MAX_OBSERVATIONS]

    indices = donnees.get("indices")
    if isinstance(indices, list):
        indices_valides = []
        for indice in indices:
            if isinstance(indice, str) and indice.strip():
                indices_valides.append(indice.strip()[:MAX_QUESTION])
            if len(indices_valides) >= MAX_INDICES:
                break
        if indices_valides:
            resultat["indices"] = indices_valides

    questions = donnees.get("questions")
    if isinstance(questions, list):
        questions_valides = []
        for question in questions:
            if isinstance(question, str) and question.strip():
                questions_valides.append(question.strip()[:MAX_QUESTION])
            if len(questions_valides) >= couche_ia.MAX_QUESTIONS:
                break
        if questions_valides:
            resultat["questions"] = questions_valides

    return resultat


def construire_prompt_vision(contexte_texte: str) -> list:
    """
    Contenu de message multi-modal : texte consigné + images base64.
    Interdictions : prix/montants (de toute façon ignorés), et il ne faut
    rien inventer sur ce qui n'est pas visible.
    """
    consignes = (
        "Vous regardez des photos d'un chantier portant sur une demande BTP "
        "(construction, rénovation, aménagement, climatisation, plomberie). "
        "Décrivez ce qui est UTILE au chiffrage : état des surfaces, type de "
        "pièces visibles, équipements existants, contrainte d'accès, traces "
        "d'humidité, hauteur plafond, présence de grenier/gaine technique. "
        "Répondez STRICTEMENT en JSON (un seul objet, sans texte autour) :\n"
        "{\n"
        '  "observations": "<résumé factuel, max 380 caractères, en français>",\n'
        '  "indices": ["<indice utile au chiffrage>", 0 à 6],\n'
        '  "questions": ["<question à poser au client (si info manquante)>", 0 à 3]\n'
        "}\n"
        "INTERDICTIONS absolues : proposer un prix, un montant, un chiffrage "
        "(toute reconfiguration serait ignorée — les prix viennent de la grille "
        "du catalogue côté serveur) ; déduire des marques ou dimensions non "
        "visibles ; affirmer ce qui n'apparaît pas sur les photos.\n"
        f"Contexte de la demande (texte du client, sans ses coordonnées) :\n{contexte_texte[:1200]}\n"
    )
    return consignes


def _blocs_contenu(demande, contexte_texte: str):
    """Construit [texte, image... image] — photos triées et bornées."""
    pieces = [
        piece for piece in demande.pieces_jointes.all()
        if piece.est_image() and piece.extension() in FORMATS_ACCEPTES
    ][:MAX_PHOTOS]

    blocs = [{"type": "text", "text": construire_prompt_vision(contexte_texte)}]
    for piece in pieces:
        try:
            if piece.est_image() and piece.fichier.size <= TAILLE_MAX_PHOTO:
                with piece.fichier.open("rb") as source:
                    blocs.append({
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": MEDIA_TYPE[piece.extension()],
                            "data": base64.b64encode(source.read()).decode("ascii"),
                        },
                    })
        except Exception:
            # photo illisible / storage indisponible : on continue sans elle
            continue
    return blocs if len(blocs) > 1 else None


def analyser_photos_demande(demande, contexte_texte: str = "") -> dict:
    """
    Analyse IA (vision) des photos de la demande. Retourne un dict validé :
    {"observations": ..., "indices": [...], "questions": [...]} — ou {} si
    l'IA est indisponible, sans image exploitable, ou en cas d'erreur.
    """
    if not couche_ia.ia_disponible():
        return {}

    if not contexte_texte:
        contexte_texte = f"{demande.service or ''} {demande.description_besoin}"

    contenu = _blocs_contenu(demande, contexte_texte)
    if contenu is None:
        return {}

    payload = json.dumps({
        "model": getattr(settings, "ANTHROPIC_MODEL", "claude-sonnet-4-5-20250929"),
        "max_tokens": 700,
        "messages": [{"role": "user", "content": contenu}],
    }).encode("utf-8")

    requete = urllib_request.Request(
        couche_ia.API_URL,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "x-api-key": settings.ANTHROPIC_API_KEY,
            "anthropic-version": couche_ia.API_VERSION,
        },
        method="POST",
    )
    try:
        with urllib_request.urlopen(requete, timeout=couche_ia.TIMEOUT_SECONDES) as reponse:
            corps = json.loads(reponse.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, ValueError):
        return {}

    texte = ""
    for bloc in corps.get("content", []):
        if isinstance(bloc, dict) and bloc.get("type") == "text":
            texte += bloc.get("text", "")

    json_extrait = couche_ia.extraire_json(texte)
    if json_extrait is None:
        return {}
    try:
        donnees = json.loads(json_extrait)
    except (json.JSONDecodeError, ValueError):
        return {}
    return valider_reponse_vision(donnees)


def fusionner_dans_resultat_ia(resultat_ia: dict, analyse_vision: dict) -> dict:
    """
    Fusionne l'analyse vision dans resultat_ia (du modèle texte) :
    - indices → champs « alertes_photo » consommés par proposer_devis
      (préfixés « [Photo] », ajoutés aux alertes) ;
    - questions → ajoutées aux questions (dans la limite autorisée) ;
    - observations → utilisées comme « resume » si le modèle texte n'en
      a pas proposé.
    """
    fusionne = dict(resultat_ia)
    if not analyse_vision:
        return fusionne

    alertes_photo = [
        f"[Photo] {indice}" for indice in analyse_vision.get("indices", [])
    ]
    if alertes_photo:
        fusionne["alertes_photo"] = alertes_photo

    questions = analyse_vision.get("questions") or []
    if questions:
        nouvelles = list(fusionne.get("questions", [])) + questions
        fusionne["questions"] = nouvelles[:couche_ia.MAX_QUESTIONS]

    if not fusionne.get("resume") and analyse_vision.get("observations"):
        fusionne["resume"] = analyse_vision["observations"]

    return fusionne
