"""
Moteur de devis automatique pour H.D.A GLOBAL.

Principe directeur : « l'IA propose, le moteur calcule, l'humain valide ».
- L'IA (optionnelle, devis/ai.py) extrait des éléments du besoin : surface,
  postes pertinents, résumé, questions.
- Le MOTEUR (ce fichier) applique les données du CATALOGUE et les FORMULES ;
  c'est lui seul qui dimensionne les quantités et fixe les prix unitaires.
- L'HUMAIN relit le brouillon généré avant envoi au client.

Règles d'or :
- Aucun prix ne vient de l'IA : tout montant provient du CATALOGUE et de
  devis/pricing.py (Decimal, ROUND_HALF_UP).
- Les prix du catalogue sont des valeurs de DÉMONSTRATION : à remplacer par la
  vraie grille tarifaire de l'entreprise.
- Le devis généré reste « brouillon » jusqu'à envoi réel au client.
"""
from dataclasses import dataclass, field
from decimal import Decimal
import re
from typing import Dict, List, Optional

from .pricing import calculer_totaux
from . import ai

# TVA standard utilisée pour l'aperçu des totaux (le devis réel prend la TVA
# des Parametres de l'entreprise).
TVA_DEFAUT = Decimal("20.00")


# ─── POSTES DU CATALOGUE ─────────────────────────────────────────────────────
# code -> PosteCatalogue(désignation, unité, prix unitaire HT en MAD, mode).
# mode "surface"  : la quantité suit la surface du chantier (fallback : 1).
# mode "forfait"  : quantité fixe de 1.
# ⚠️ PRIX DE DÉMONSTRATION — remplacer par la grille réelle de l'entreprise.
@dataclass(frozen=True)
class PosteCatalogue:
    code: str
    designation: str
    unite: str
    prix_unitaire_ht: Decimal
    mode: str  # "surface" | "forfait"


CATALOGUE: Dict[str, PosteCatalogue] = {
    # --- Construction & rénovation ---
    "DEM-BET": PosteCatalogue("DEM-BET", "Démolition et déposes diverses", "m²", Decimal("85.00"), "surface"),
    "CLO-MUR": PosteCatalogue("CLO-MUR", "Cloisonnement et plâtrerie", "m²", Decimal("130.00"), "surface"),
    "PEI-MUR": PosteCatalogue("PEI-MUR", "Peinture intérieure (2 couches + finitions)", "m²", Decimal("85.00"), "surface"),
    "CAR-SOL": PosteCatalogue("CAR-SOL", "Carrelage sol (fourniture + pose)", "m²", Decimal("220.00"), "surface"),
    "FAI-MUR": PosteCatalogue("FAI-MUR", "Faïence murale (fourniture + pose)", "m²", Decimal("180.00"), "surface"),
    # --- Gestion de projets TCE ---
    "GE-PRO": PosteCatalogue("GE-PRO", "Étude technique et définition du projet (forfait)", "forfait", Decimal("3500.00"), "forfait"),
    "GE-SUI": PosteCatalogue("GE-SUI", "Suivi et coordination des corps d'état (forfait)", "forfait", Decimal("5500.00"), "forfait"),
    # --- Aménagement intérieur / extérieur ---
    "AME-PLA": PosteCatalogue("AME-PLA", "Cloisons et habillage en placo", "m²", Decimal("150.00"), "surface"),
    "AME-FPX": PosteCatalogue("AME-FPX", "Faux plafond suspendu et éclairages intégrés", "m²", Decimal("190.00"), "surface"),
    "AME-PIN": PosteCatalogue("AME-PIN", "Peinture décorative et finitions", "m²", Decimal("90.00"), "surface"),
    "AME-SOL": PosteCatalogue("AME-SOL", "Revêtement de sol (fourniture et pose)", "m²", Decimal("160.00"), "surface"),
    # --- Climatisation & ventilation ---
    "CLIM-SPL": PosteCatalogue("CLIM-SPL", "Climatisation (fourniture, pose et raccordements)", "m²", Decimal("320.00"), "surface"),
    "CLIM-INS": PosteCatalogue("CLIM-INS", "Kit d'installation et mise en service", "forfait", Decimal("10000.00"), "forfait"),
    # --- Plomberie générale ---
    "PLB-RED": PosteCatalogue("PLB-RED", "Réseau plomberie (alimentation + évacuation)", "m²", Decimal("160.00"), "surface"),
    "PLB-SAN": PosteCatalogue("PLB-SAN", "Pose sanitaire (WC, douche, lavabo) — forfait", "forfait", Decimal("4800.00"), "forfait"),
    "PLB-THE": PosteCatalogue("PLB-THE", "Pose de chauffe-eau — forfait", "forfait", Decimal("1600.00"), "forfait"),
    # --- Services divers sur mesure ---
    "DIV-PST": PosteCatalogue("DIV-PST", "Prestation sur mesure (unité standard)", "forfait", Decimal("800.00"), "forfait"),
    # --- Frais annexes (uniquement ajoutes par le moteur) ---
    "DEP-VILLE": PosteCatalogue("DEP-VILLE", "Frais de déplacement hors zone (forfait)", "forfait", Decimal("400.00"), "forfait"),
}

CODE_DEPLACEMENT = "DEP-VILLE"  # jamais proposé par l'IA, ajouté par le moteur

# Quantité de repli quand la surface est inconnue
QUANTITE_REPLI = Decimal("1.00")


# ─── FORMULES PAR FAMILLE DE SERVICE ────────────────────────────────────────
FORMULES: Dict[str, List[str]] = {
    "construction_renovation": ["DEM-BET", "CLO-MUR", "PEI-MUR", "CAR-SOL"],
    "gestion_tce": ["GE-PRO", "GE-SUI"],
    "amenagement": ["AME-PLA", "AME-FPX", "AME-PIN", "AME-SOL"],
    "climatisation": ["CLIM-SPL", "CLIM-INS"],
    "plomberie": ["PLB-RED", "PLB-SAN", "PLB-THE"],
    "divers": ["DIV-PST"],
}

# Villes proches du siège (pas de frais de déplacement)
ZONES_PROCHE = ["mohammedia", "casablanca", "beni yakhlef", "benslimane"]


# ─── DÉTECTION DE FAMILLE ───────────────────────────────────────────────────
# d'abord sur le service choisi par le client, puis sur la description libre.
MOTS_CLES_FAMILLES = {
    "climatisation": [
        "climatisation", "clim", "ventilation", "cvc", "split", "reversible",
        "vrv", "vmb", "gaine", "aer", "chauffage",
    ],
    "plomberie": [
        "plomberie", "plombier", "sanitaire", "tuyauterie", "canalisation",
        "evacuation", "chauffe eau", "chauffe-eau", "douche", "robinet", "wc",
        "toilettes", "eaux usees", "eaux", "fuite", "baignoire", "lavabo",
    ],
    "amenagement": [
        "amenagement", "agencement", "cloison", "plafond", "placo",
        "interieur", "exterieur", "terrasse", "jardin", "mobilier", "meuble",
        "cuisine", "decor", "murale",
    ],
    "gestion_tce": [
        "gestion", "tce", "coordination", "maitre d oeuvre", "maitrise",
        "conducteur", "suivi de chantier", "corps d etat", "etude",
    ],
    "construction_renovation": [
        "construction", "renovation", "rehabilitation", "demolition",
        "extension", "gros oeuvre", "grossoeuvre", "beton", "maconnerie",
        "reprise", "mur porteur",
    ],
}

# Ordre de sélection sur la description libre (spécifique → générique)
ORDRE_DETECTION = [
    "climatisation", "plomberie", "amenagement", "gestion_tce",
    "construction_renovation",
]


def normaliser(texte: str) -> str:
    """Minuscule, sans accents, sans & — pour les mots-clés de détection."""
    import unicodedata
    if not texte:
        return ""
    texte = unicodedata.normalize("NFKD", texte).encode("ascii", "ignore").decode("ascii")
    return texte.lower().replace("&", " et ")


def detecter_famille(nom_service: Optional[str], description: str) -> str:
    """
    Détecte la famille métier d'une demande :
    1. mots-clés sur le nom du service choisi par le client ;
    2. sinon mots-clés sur la description libre (français simplifié, la
       description venant du client peut contenir des fautes de frappe) ;
    3. sinon « divers ».
    """
    service_norm = normaliser(nom_service)
    for famille, mots_cles in MOTS_CLES_FAMILLES.items():
        for mot in mots_cles:
            if mot in service_norm:
                return famille

    description_norm = normaliser(description)
    for famille in ORDRE_DETECTION:
        for mot in MOTS_CLES_FAMILLES[famille]:
            if mot in description_norm:
                return famille

    return "divers"


# ─── PROPOSITION ────────────────────────────────────────────────────────────
@dataclass
class LigneProposee:
    """Une ligne de devis proposée par le moteur (prix TOUJOURS du catalogue)."""
    code: str
    designation: str
    unite: str
    quantite: Decimal
    prix_unitaire_ht: Decimal


@dataclass
class PropositionDevis:
    """Résultat de proposer_devis : lignes + contexte de relire pour l'humain."""
    lignes: List[LigneProposee]
    alertes: List[str] = field(default_factory=list)
    confiance: str = "moyenne"            # "elevee" | "moyenne" | "faible"
    resume: str = ""
    famille: str = "divers"
    surface_utilisee: Optional[Decimal] = None
    totaux: dict = field(default_factory=dict)


def _ville_hors_zone(ville: str) -> bool:
    """True si la ville déclarée est hors des zones proches du siège."""
    ville_norm = normaliser(ville)
    return not any(z in ville_norm for z in ZONES_PROCHE)


def proposer_devis(
    service_nom: Optional[str],
    ville: str,
    surface_saisie: Optional[Decimal],
    description: str,
    resultat_ia: Optional[dict] = None,
) -> PropositionDevis:
    """
    Construit une PROPOSITION de devis à partir des données de la demande.

    Args:
        service_nom  : nom du service choisi (ex. « Climatisation et ventilation »)
        ville        : ville du chantier déclarée par le client
        surface_saisie : surface saisie dans le formulaire (Decimal ou None)
        description  : description libre du besoin par le client
        resultat_ia  : sortie VALIDÉE de devis/ai.py (dict) — jamais prix.

    Returns:
        PropositionDevis (les totaux calculés via pricing.calculer_totaux).
    """
    resultat_ia = resultat_ia or {}
    alertes: List[str] = []
    famille = detecter_famille(service_nom, description)
    confiance = "elevee"

    # ── 1. Surface : saisie client > IA > regex description > inconnue
    surface = None
    if surface_saisie is not None and surface_saisie > 0:
        surface = Decimal(surface_saisie)
    elif resultat_ia.get("surface_m2"):
        try:
            candidat = Decimal(str(resultat_ia["surface_m2"]))
            if 0 < candidat <= Decimal("100000"):
                surface = candidat
        except (ValueError, ArithmeticError):
            pass
    else:
        extraite = ai.extraire_surface_regex(description)
        if extraite is not None:
            surface = extraite
            alertes.append(
                f"Surface extraite automatiquement de la description ({surface} m²) — à confirmer."
            )

    if surface is None:
        confiance = "faible"
        alertes.append(
            "Surface inconnue : les postes au m² sont chiffrés sur 1 unité. "
            "Demander la surface avant envoi pour un chiffrage réaliste."
        )

    # ── 2. Postes : ceux de l'IA s'ils existent au catalogue (≥2), sinon formule
    codes_ia = [c for c in resultat_ia.get("postes", []) if c in CATALOGUE and c != CODE_DEPLACEMENT]
    if len(codes_ia) >= 2:
        codes = codes_ia
    elif codes_ia:
        codes = FORMULES[famille]
        alertes.append("Postes IA insuffisants : repli sur la formule standard de la famille.")
    else:
        codes = FORMULES[famille]

    # ── 3. Génération des lignes (prix et quantités : moteur uniquement)
    lignes: List[LigneProposee] = []
    for code in codes:
        poste = CATALOGUE[code]
        if poste.mode == "surface":
            quantite = surface if surface is not None else QUANTITE_REPLI
        else:
            quantite = Decimal("1.00")
        lignes.append(LigneProposee(
            code=poste.code,
            designation=poste.designation,
            unite=poste.unite,
            quantite=quantite,
            prix_unitaire_ht=poste.prix_unitaire_ht,
        ))

    # ── 4. Ville hors zone → frais de déplacement
    if not ville or normaliser(ville) in ("autre", "autre ville"):
        confiance = "faible"
        alertes.append(
            f"Ville du chantier non précisée (« {ville or 'vide'} ») — à clarifier avec le client."
        )
    elif _ville_hors_zone(ville):
        poste_dep = CATALOGUE[CODE_DEPLACEMENT]
        lignes.append(LigneProposee(
            code=poste_dep.code,
            designation=poste_dep.designation,
            unite=poste_dep.unite,
            quantite=Decimal("1.00"),
            prix_unitaire_ht=poste_dep.prix_unitaire_ht,
        ))
        alertes.append(
            f"Chantier hors zone proche ({ville}) : ligne de déplacement ajoutée — à ajuster selon la distance réelle."
        )

    # ── 5. Confiance abaissée si description trop courte ou famille « divers »
    if len((description or "").strip()) < 40:
        confiance = "moyenne" if confiance != "faible" else confiance
    if famille == "divers" and confiance == "elevee":
        confiance = "moyenne"

    # ── 6. Résumé et questions de l'IA
    resume = (resultat_ia.get("resume") or "").strip()[:300]
    if not resume:
        service_txt = service_nom or "prestation"
        surface_txt = f"{surface} m²" if surface else "surface à préciser"
        resume = f"{service_txt.capitalize()} — {ville or 'ville à préciser'} — {surface_txt}."

    for question in resultat_ia.get("questions", []):
        alertes.append(f"Question client : {question}")

    # Indices issus de l'analyse des photos de chantier (devis/vision.py)
    for indice_photo in resultat_ia.get("alertes_photo", []):
        alertes.append(str(indice_photo)[:200])

    urgence = (resultat_ia.get("urgence") or "").strip()[:20]
    if urgence and urgence.lower() in ("tres haute", "haute", "immediat"):
        alertes.append(f"Urgence déclarée par l'IA : {urgence}.")

    totaux = calculer_totaux(
        [(l.quantite, l.prix_unitaire_ht) for l in lignes],
        TVA_DEFAUT,
    )

    return PropositionDevis(
        lignes=lignes,
        alertes=alertes,
        confiance=confiance,
        resume=resume,
        famille=famille,
        surface_utilisee=surface,
        totaux=totaux,
    )


# ─── GÉNÉRATION DE LA DEMANDE ───────────────────────────────────────────────
def generer_devis_automatique(demande, utiliser_ia: bool = True):
    """
    Génère (ou retourne, si existant) un Devis BROUILLON à partir d'une Demande.

    - L'IA (désactivable, optionnelle) analyse le besoin ; en cas d'échec
      (pas de clé API, réseau, JSON invalide) le devis se génère quand même.
    - Lignes + totaux via le moteur ; PDF sauvegardé.
    - Notes internes (confiance, résumé, alertes) : jamais visibles du client.
    - Idempotent : un devis actif existe déjà → retour sans doublon.
    - Le statut de la demande reste « Nouvelle » : il passe à « Devis envoyé »
      uniquement lors de l'envoi réel du devis.
    """
    from core.models import Parametres
    from .models import Devis, LigneDevis
    from .pricing import recalculer_devis
    from .pdf import sauvegarder_pdf_devis

    # Idempotence : ne pas créer un deuxième devis pour la même demande
    devis_existant = demande.get_devis_actif()
    if devis_existant is not None:
        return devis_existant

    params = Parametres.get()

    # ── 1. Analyse IA (texte puis photos ; optionnelles, ne bloquent JAMAIS)
    resultat_ia: dict = {}
    if utiliser_ia and ai.ia_disponible():
        try:
            resultat_ia = ai.analyser_demande(
                service_nom=demande.service.nom if demande.service else None,
                ville=demande.ville_chantier,
                surface_saisie=demande.surface_m2,
                description=demande.description_besoin,
            )
            # Extension « photos + vision » : observations des photos de
            # chantier (PieceJointe) → indices/questions. Échec toléré.
            try:
                from . import vision
                analyse_photo = vision.analyser_photos_demande(
                    demande, contexte_texte=demande.description_besoin,
                )
                if analyse_photo:
                    resultat_ia = vision.fusionner_dans_resultat_ia(resultat_ia, analyse_photo)
            except Exception:
                pass  # la vision ne bloque jamais le flux
        except Exception:
            # Erreur réseau, quota, ... : l'IA ne bloque jamais une demande
            resultat_ia = {}

    # ── 2. Proposition du moteur (prix 100 % catalogue)
    proposition = proposer_devis(
        service_nom=demande.service.nom if demande.service else None,
        ville=demande.ville_chantier,
        surface_saisie=demande.surface_m2,
        description=demande.description_besoin,
        resultat_ia=resultat_ia,
    )

    # ── 3. Création du devis brouillon
    devis = Devis.objects.create(
        demande=demande,
        taux_tva=params.tva_defaut,
        conditions_reglement="30% à la commande, 70% à la livraison des travaux.",
        notes=_notes_internes(proposition),
    )

    for ordre, ligne in enumerate(proposition.lignes):
        LigneDevis.objects.create(
            devis=devis,
            designation=ligne.designation,
            quantite=ligne.quantite,
            unite=ligne.unite,
            prix_unitaire_ht=ligne.prix_unitaire_ht,
            ordre=ordre,
        )

    recalculer_devis(devis)
    sauvegarder_pdf_devis(devis)
    return devis


def _notes_internes(proposition: PropositionDevis) -> str:
    """
    Notes internes du brouillon — préfixées pour être filtrées du PDF client
    (les lignes commençant par « [ », « • » ou « Résumé » ne sortent jamais).
    """
    blocs = [
        f"[IA] Famille : {proposition.famille}",
        f"[IA] Confiance : {proposition.confiance}",
        f"[IA] Résumé : {proposition.resume}",
    ]
    if proposition.surface_utilisee is not None:
        blocs.insert(3, f"[IA] Surface utilisée : {proposition.surface_utilisee} m²")
    for alerte in proposition.alertes:
        blocs.append(f"[IA] Alerte : {alerte}")
    return "\n".join(blocs)


def lire_notes_auto(devis) -> dict:
    """
    Lit les méta-données d'automatisation depuis les notes internes d'un
    devis (pour l'affichage admin : bandeau de relecture). Retourne :
    {"genere_auto": bool, "confiance": str, "resume": str, "alertes": [...]}
    """
    info = {"genere_auto": False, "confiance": "", "resume": "", "alertes": []}
    if not devis.notes:
        return info
    for ligne in devis.notes.splitlines():
        ligne = ligne.strip()
        match = re.match(r"^\[IA\]\s*([^:]+):\s*(.*)$", ligne)
        if not match:
            continue
        label = match.group(1).strip().lower()
        valeur = match.group(2).strip()
        info["genere_auto"] = True
        if label == "confiance":
            info["confiance"] = valeur
        elif label == "résumé":
            info["resume"] = valeur
        elif label == "alerte":
            info["alertes"].append(valeur)
    return info
