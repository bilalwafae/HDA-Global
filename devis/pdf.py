"""
Générateur de devis PDF pour H.D.A GLOBAL — version 2.

Architecture en DEUX NIVEAUX pour la testabilité :
- construire_pdf(data: dict) -> bytes : fonction PURE (testable sans Django,
  sans base de données : polices/logo/QR sont passés via le dictionnaire) ;
- generer_pdf_devis(devis) : adaptateur qui traduit le modèle Django vers ce
  dictionnaire ; sauvegarder_pdf_devis(devis) : signature inchangée.

Contenu du PDF (v2) :
- en-tête avec logo (Parametres.logo, sinon static/img/logo_hda_icon.png) et
  marque « H.D.A GLOBAL – Construction TCE – Aménagement », « DEVIS N° … » ;
- blocs émetteur et destinataire ; objet / réf. demande / validité / chantier ;
- tableau des prestations (N°, désignation, qté, unité, P.U. HT, total HT) ;
- totaux HT / TVA / TTC (TTC sur bandeau orange) ;
- montant « arrêté en toutes lettres » (montant_en_lettres, orthographe
  française : quatre-vingt mille, deux cents, un million de dirhams) ;
- conditions de règlement ; bloc « Bon pour accord » (signature, cachet) ;
- QR code vers le portail de suivi (SITE_URL + /suivi/<token>/), repli
  silencieux si la librairie qrcode n'est pas installée ;
- pied de page légal sur chaque page, avec numérotation (« Page 2 »).

Format français : 12 345,60 (espaces insécables).
Police Liberation Sans (licence OFL) si présente dans static/fonts/,
repli Helvetica — la police standard non embarquée ne rend pas toujours « m² »
dans certains lecteurs PDF.

⚠️ Les notes internes (lignes commençant par « [ », « • » ou « Résumé »)
sont filtrées par filtrer_notes_client() et n'apparaissent JAMAIS sur le
PDF présenté au client.
"""
import os
from decimal import Decimal
from io import BytesIO

from django.core.files.base import ContentFile

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, HRFlowable,
)

# ─── Palette H.D.A GLOBAL ────────────────────────────────────────────────────
HDA_BLEU_FONCE = colors.HexColor("#1E3A8A")
HDA_BLEU_CLAIR = colors.HexColor("#1E5BB8")
HDA_ORANGE = colors.HexColor("#F97316")
HDA_GRIS_CLAIR = colors.HexColor("#F8FAFC")
HDA_GRIS = colors.HexColor("#6B7280")
HDA_BLANC = colors.white
HDA_NOIR = colors.HexColor("#111827")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS_DIR = os.path.join(BASE_DIR, "static", "fonts")
IMG_DIR = os.path.join(BASE_DIR, "static", "img")

_NBS = "\u00a0"  # espace insécable pour les montants


# ─── POLICES : Liberation Sans (bêta OFL) avec repli Helvetica ──────────────
def charger_polices(polices_dir: str = None):
    """
    Enregistre Liberation Sans si les TTF sont dans static/fonts/ (OFL).
    Repli : Helvetica (puce listée). Renvoie (fonte_normale, fonte_gras).
    """
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    dossier = polices_dir or FONTS_DIR
    ttf_normale = os.path.join(dossier, "LiberationSans-Regular.ttf")
    ttf_gras = os.path.join(dossier, "LiberationSans-Bold.ttf")
    try:
        if os.path.isfile(ttf_normale) and os.path.isfile(ttf_gras):
            pdfmetrics.registerFont(TTFont("LiberationSans", ttf_normale))
            pdfmetrics.registerFont(TTFont("LiberationSans-Bold", ttf_gras))
            return "LiberationSans", "LiberationSans-Bold"
    except Exception:
        pass
    return "Helvetica", "Helvetica-Bold"


# ─── FORMATS FRANÇAIS ───────────────────────────────────────────────────────
def fmt_mad(valeur) -> str:
    """Format français : 12 345,60 (espace insécable de millisation + virgule)."""
    nombre = Decimal(str(valeur)).quantize(Decimal("0.01"))
    texte = f"{nombre:,.2f}".replace(",", _NBS).replace(".", ",")
    return texte


def fmt_quantite(valeur) -> str:
    """Quantité : 85 -> « 85,00 »."""
    nombre = Decimal(str(valeur)).quantize(Decimal("0.01"))
    return f"{nombre:,.2f}".replace(",", _NBS).replace(".", ",")


# ─── MONTANT EN LETTRES (orthographe française) ────────────────────────────
# 80 000  -> « quatre-vingt mille dirhams »
# 200     -> « deux cents dirhams »
# 1000000 -> « un million de dirhams »
UNITE_LETTRE = [
    "zéro", "un", "deux", "trois", "quatre", "cinq", "six", "sept", "huit",
    "neuf", "dix", "onze", "douze", "treize", "quatorze", "quinze", "seize",
    "dix-sept", "dix-huit", "dix-neuf",
]


def _sous_100(n: int) -> str:
    """0..99 : soixante-et-onze, quatre-vingts, quatre-vingt-onze..."""
    if n < 20:
        return UNITE_LETTRE[n]
    d, u = divmod(n, 10)
    if d == 7:
        if u == 1:
            return "soixante-et-onze"
        if u == 0:
            return "soixante-dix"
        return "soixante-" + _sous_100(10 + u)   # soixante-douze...
    if d == 8:
        if u == 0:
            return "quatre-vingts"
        return "quatre-vingt-" + UNITE_LETTRE[u]
    if d == 9:
        if u == 0:
            return "quatre-vingt-dix"
        return "quatre-vingt-" + _sous_100(10 + u)  # quatre-vingt-quinze...
    base = {2: "vingt", 3: "trente", 4: "quarante", 5: "cinquante", 6: "soixante"}[d]
    if u == 0:
        return base
    if u == 1:
        return base + "-et-un"
    return base + "-" + UNITE_LETTRE[u]


def _sous_1000(n: int) -> str:
    """0..999 : cent, deux cents, deux cent trois..."""
    if n < 100:
        return _sous_100(n)
    cent, reste = divmod(n, 100)
    if cent == 1:
        mot = "cent"
    else:
        mot = UNITE_LETTRE[cent] + " cent"
    if reste == 0 and cent > 1:
        return mot + "s"          # deux cents
    if reste > 0:
        return mot + " " + _sous_100(reste)
    return mot                    # « cent » uniquement sans « s »


def entier_en_lettres(n: int) -> str:
    """0..999 999 999 999 : mille invariable, quatre-vingt mille (s tombé), etc."""
    if n == 0:
        return "zéro"
    parts = []
    milliards = n // 10**9
    millions = (n // 10**6) % 1000
    milliers = (n // 1000) % 1000
    reste = n % 1000
    if milliards:
        parts.append("un milliard" if milliards == 1 else _sous_1000(milliards) + " milliards")
    if millions:
        parts.append("un million" if millions == 1 else _sous_1000(millions) + " millions")
    if milliers:
        if milliers == 1:
            parts.append("mille")
        else:
            mot = _sous_1000(milliers)
            if mot == "quatre-vingts":   # quatre-vingt mille (pas « vingt-s »)
                mot = "quatre-vingt"
            parts.append(mot + " mille")
    if reste:
        parts.append(_sous_1000(reste))
    return " ".join(parts)


def montant_en_lettres(montant) -> str:
    """Montant MAD en lettres + « (arrêté) ». Cf. exemples du module."""
    montant = Decimal(str(montant)).quantize(Decimal("0.01"))
    dirhams = int(montant)
    centimes = int(((montant - dirhams) * 100).to_integral_value())

    if dirhams == 0:
        partie_dirhams = ""
    elif dirhams == 1:
        partie_dirhams = "un dirham"
    elif dirhams >= 10**6 and dirhams % 10**6 == 0:
        partie_dirhams = entier_en_lettres(dirhams) + " de dirhams"   # un million DE dirhams
    else:
        partie_dirhams = entier_en_lettres(dirhams) + " dirhams"

    if centimes == 0:
        resultat = partie_dirhams or "zéro dirham"
    else:
        centime_lettres = ("un centime" if centimes == 1 else entier_en_lettres(centimes) + " centimes")
        resultat = centime_lettres if dirhams == 0 else f"{partie_dirhams} et {centime_lettres}"
    return resultat + " (arrêté)"


# ─── NOTES INTERNES : JAMAIS VISIBLES DU CLIENT ────────────────────────────
def filtrer_notes_client(notes: str) -> list:
    """
    Notes que l'on peut naturellement afficher au client : toute ligne
    commençant par « [ », « • » ou « Résumé » (.notes internes du moteur)
    est filtrée et n'apparaît JAMAIS sur le PDF.
    """
    visibles = []
    for ligne in (notes or "").splitlines():
        ligne = ligne.strip()
        if not ligne:
            continue
        if ligne.startswith(("[", "•", "Résumé")):
            continue
        visibles.append(ligne)
    return visibles


# ─── QR CODE VERS LE PORTAIL DE SUIVI ──────────────────────────────────────
def flux_qr(texte: str):
    """PNG (flux mémoire) du QR code si la librairie « qrcode » est installée ;
    sinon None → le PDF sort sans QR (jamais bloqué)."""
    try:
        import qrcode
        qr = qrcode.QRCode(box_size=4, border=1)
        qr.add_data(texte)
        qr.make(fit=True)
        image = qr.make_image(fill_color="#1E3A8A", back_color="white")
        tampon = BytesIO()
        image.save(tampon, format="PNG")
        tampon.seek(0)
        return tampon
    except Exception:
        return None


# ─── CANVAS NUMÉROTÉ : pied de page légal sur CHAQUE page ──────────────────
class CanvasNumerote(Canvas):
    """Canvas ReportLab (pattern NumberedCanvas) ajoutant sur CHAQUE page :
    - le filet bleu + le pied de page légal ;
    - la numérotation « Page X sur Y » (omise sur la page 1)."""

    def __init__(self, *args, pied_texte: str = "", fontes=("Helvetica", "Helvetica-Bold"), **kwargs):
        super().__init__(*args, **kwargs)
        self.pied_texte = pied_texte
        self.fontes = fontes
        self._pages_sauvegardees = []

    def showPage(self):
        self._pages_sauvegardees.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total = len(self._pages_sauvegardees)
        for numero, etat in enumerate(self._pages_sauvegardees, start=1):
            self.__dict__.update(etat)
            self._dessiner_pied(numero, total)
            Canvas.showPage(self)
        Canvas.save(self)

    def _dessiner_pied(self, numero, total):
        largeur, _ = self._pagesize
        self.saveState()
        # Filet bleu discret au-dessus du pied de page
        self.setStrokeColor(HDA_BLEU_CLAIR)
        self.setLineWidth(0.7)
        self.line(1.5 * cm, 1.35 * cm, largeur - 1.5 * cm, 1.35 * cm)
        fonte_normale, _ = self.fontes
        self.setFillColor(HDA_GRIS)
        self.setFont(fonte_normale, 6.5)
        # Le pied légal peut être long (ICE, RC, IF…) : retour à la ligne, jamais de débordement
        from reportlab.lib.utils import simpleSplit
        lignes = simpleSplit(self.pied_texte or "", fonte_normale, 6.5, largeur - 3 * cm)[:3]
        y = 1.05 * cm
        for ligne in lignes:
            self.drawCentredString(largeur / 2, y, ligne)
            y -= 0.28 * cm
        if numero > 1:
            self.setFont(fonte_normale, 7)
            self.drawCentredString(largeur / 2, 0.3 * cm, f"Page {numero} sur {total}")
        self.restoreState()


# ─── CONSTRUCTION DU PDF (fonction PURE) ───────────────────────────────────
def construire_pdf(data: dict) -> bytes:
    """
    Construit le PDF (octets) à partir d'un dict data. PURE et testable :
    aucun accès Django/DB — logo, polices, QR sont passés dans data.
    """
    fonte_normale, fonte_gras = charger_polices(data.get("polices_dir"))

    style_titre = ParagraphStyle("titre", fontName=fonte_gras, fontSize=15, textColor=HDA_BLEU_FONCE)
    style_sous_titre = ParagraphStyle("sous_titre", fontName=fonte_normale, fontSize=8.5, textColor=HDA_GRIS)
    style_normal = ParagraphStyle("normal_hda", fontName=fonte_normale, fontSize=8, textColor=HDA_NOIR, leading=11)
    style_gras = ParagraphStyle("gras_hda", fontName=fonte_gras, fontSize=8.5, textColor=HDA_NOIR)
    style_rubrique = ParagraphStyle("rubrique", fontName=fonte_gras, fontSize=7.5, textColor=HDA_BLEU_CLAIR)
    style_bleu_gras = ParagraphStyle("bleu_gras", fontName=fonte_gras, fontSize=8.5, textColor=HDA_BLEU_FONCE)
    style_tete = ParagraphStyle("tete_tableau", fontName=fonte_gras, fontSize=8, textColor=HDA_BLANC)
    style_centre = ParagraphStyle("centre", fontName=fonte_normale, fontSize=8, textColor=HDA_NOIR, alignment=TA_CENTER)
    style_droite = ParagraphStyle("droite", fontName=fonte_normale, fontSize=8, textColor=HDA_NOIR, alignment=TA_RIGHT)
    style_droite_gras = ParagraphStyle("droite_gras", fontName=fonte_gras, fontSize=8, textColor=HDA_BLEU_FONCE, alignment=TA_RIGHT)
    style_lettres = ParagraphStyle("lettres", fontName=fonte_gras, fontSize=8.5, textColor=HDA_BLEU_FONCE, leading=12)
    style_condition = ParagraphStyle("condition", fontName=fonte_normale, fontSize=8, textColor=HDA_NOIR, leading=11.5)
    style_small_gris = ParagraphStyle("small_gris", fontName=fonte_normale, fontSize=7.5, textColor=HDA_GRIS, leading=10)

    flux = BytesIO()
    doc = SimpleDocTemplate(
        flux, pagesize=A4,
        leftMargin=1.5 * cm, rightMargin=1.5 * cm,
        topMargin=1.4 * cm, bottomMargin=1.8 * cm,
        title=f"Devis {data['devis']['numero']} – H.D.A GLOBAL",
        author=data["emetteur"]["nom"],
    )
    largeur_utile = doc.width
    elements = []

    # ── EN-TÊTE ──────────────────────────────────────────────────────────
    logo_cell = ""
    chemin_logo = data.get("logo_path")
    if chemin_logo and os.path.isfile(chemin_logo):
        try:
            from reportlab.lib.utils import ImageReader
            lecteur = ImageReader(chemin_logo)
            w0, h0 = lecteur.getSize()
            h = 2.3 * cm
            w = min(w0 * (h / h0), 7.2 * cm)
            logo_cell = Image(chemin_logo, width=w, height=h)
        except Exception:
            logo_cell = ""

    entete_gauche = [] if logo_cell else [
        Paragraph(data["emetteur"]["nom"], style_titre),
        Paragraph(data["emetteur"]["marque"], style_sous_titre),
    ]
    entete_droite = [
        Paragraph("DEVIS N°", style_sous_titre),
        Paragraph(
            f'<font name="{fonte_gras}" size="15" color="#1E3A8A">{data["devis"]["numero"]}</font>',
            style_normal,
        ),
    ]
    table_entete = Table(
        [[logo_cell or "", entete_gauche, entete_droite]],
        colWidths=[7.6 * cm, 4.7 * cm, 5.7 * cm] if logo_cell else [4.9 * cm, 7.4 * cm, 5.7 * cm],
    )
    table_entete.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    elements.append(table_entete)
    elements.append(Spacer(1, 0.2 * cm))
    elements.append(HRFlowable(width="100%", thickness=2.2, color=HDA_ORANGE, spaceAfter=10))

    # ── ÉMETTEUR / DESTINATAIRE ──────────────────────────────────────────
    emetteur = [Paragraph("ÉMETTEUR", style_rubrique), Paragraph(data["emetteur"]["nom"], style_gras)]
    for adresse in data["emetteur"]["adresses"]:
        if adresse:
            emetteur.append(Paragraph(adresse, style_normal))
    emetteur.append(Paragraph(f"Tél : {data['emetteur']['telephone']}", style_normal))
    emetteur.append(Paragraph(f"Email : {data['emetteur']['email']}", style_normal))

    destinataire = [
        Paragraph("DESTINATAIRE", style_rubrique),
        Paragraph(data["client"]["nom"], style_gras),
        Paragraph(f"Tél : {data['client']['telephone']}", style_normal),
        Paragraph(f"Email : {data['client']['email']}", style_normal),
        Paragraph(f"Ville : {data['client']['ville']}", style_normal),
    ]
    table_deux = Table([[emetteur, destinataire]], colWidths=[9 * cm, 9 * cm])
    table_deux.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BACKGROUND", (1, 0), (1, 0), HDA_GRIS_CLAIR),
        ("BOX", (1, 0), (1, 0), 0.5, HDA_BLEU_CLAIR),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(table_deux)
    elements.append(Spacer(1, 0.35 * cm))

    # ── OBJET / RÉF / VALIDITÉ / CHANTIER ────────────────────────────────
    info = [
        ["Objet :", data["devis"]["objet"] or "Prestation selon votre demande",
         "Réf. demande :", data["chantier"]["reference"]],
        ["Validité :", f"jusqu'au {data['devis']['date_validite']}",
         "Chantier :", f"{data['chantier']['ville']} - {data['chantier']['adresse']}"],
    ]
    grille_info = Table(info, colWidths=[2.2 * cm, 6.8 * cm, 2.4 * cm, 6.6 * cm])
    grille_info.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), fonte_gras),
        ("FONTNAME", (2, 0), (2, -1), fonte_gras),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("TEXTCOLOR", (0, 0), (0, -1), HDA_GRIS),
        ("TEXTCOLOR", (2, 0), (2, -1), HDA_GRIS),
        ("TEXTCOLOR", (3, 0), (3, -1), HDA_NOIR),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    elements.append(grille_info)
    elements.append(Spacer(1, 0.25 * cm))

    # ── TABLEAU DES PRESTATIONS ──────────────────────────────────────────
    en_tetes = [
        Paragraph("N°", style_tete),
        Paragraph("Désignation des travaux", style_tete),
        Paragraph("Qté", style_tete),
        Paragraph("Unité", style_tete),
        Paragraph("P.U. HT (MAD)", style_tete),
        Paragraph("Total HT (MAD)", style_tete),
    ]
    data_lignes = [en_tetes]
    for ligne in data["lignes"]:
        data_lignes.append([
            Paragraph(str(ligne["n"]), style_normal),
            Paragraph(ligne["designation"], style_normal),
            Paragraph(ligne["quantite"], style_centre),
            Paragraph(ligne["unite"], style_centre),
            Paragraph(ligne["pu"], style_droite),
            Paragraph(ligne["total"], style_droite_gras),
        ])
    table_lignes = Table(
        data_lignes,
        colWidths=[0.9 * cm, 8.35 * cm, 1.7 * cm, 1.7 * cm, 2.65 * cm, 2.7 * cm],
        repeatRows=1,
    )
    table_lignes.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), HDA_BLEU_FONCE),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [HDA_BLANC, HDA_GRIS_CLAIR]),
        ("GRID", (0, 0), (-1, -1), 0.3, HDA_GRIS),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4.5),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(table_lignes)
    elements.append(Spacer(1, 0.25 * cm))

    # ── TOTAUX ───────────────────────────────────────────────────────────
    largeur_totaux = [7.2 * cm, 7.2 * cm, 3.6 * cm]
    grille_totaux = Table([
        ["", "Sous-total HT :", f"{data['totaux']['sous_total_ht']}" + _NBS + " MAD"],
        ["", f"TVA ({data['devis']['taux_tva']}%) :", f"{data['totaux']['montant_tva']}" + _NBS + " MAD"],
    ], colWidths=largeur_totaux)
    grille_totaux.setStyle(TableStyle([
        ("FONTNAME", (1, 0), (2, -1), fonte_gras),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (1, 0), (2, -1), "RIGHT"),
        ("TEXTCOLOR", (1, 0), (2, -1), HDA_BLEU_FONCE),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
    ]))
    elements.append(grille_totaux)

    ligne_ttc = Table([
        ["", "TOTAL TTC :", f"{data['totaux']['total_ttc']}" + _NBS + " MAD"],
    ], colWidths=largeur_totaux)
    ligne_ttc.setStyle(TableStyle([
        ("BACKGROUND", (1, 0), (2, 0), HDA_ORANGE),
        ("TEXTCOLOR", (1, 0), (2, 0), HDA_BLANC),
        ("FONTNAME", (1, 0), (2, 0), fonte_gras),
        ("FONTSIZE", (1, 0), (2, 0), 10.5),
        ("ALIGN", (1, 0), (2, 0), "RIGHT"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (2, 0), (2, 0), 8),
    ]))
    elements.append(ligne_ttc)
    elements.append(Spacer(1, 0.25 * cm))

    # ── MONTANT EN TOUTES LETTRES ───────────────────────────────────────
    bandeau = Table([[
        Paragraph(
            "Arrêté le présent devis à la somme de : "
            f"{data.get('montant_lettres', '')}",
            style_lettres,
        )
    ]], colWidths=[largeur_utile])
    bandeau.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), HDA_GRIS_CLAIR),
        ("BOX", (0, 0), (-1, -1), 0.5, HDA_BLEU_CLAIR),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    elements.append(bandeau)
    elements.append(Spacer(1, 0.3 * cm))

    # ── CONDITIONS ──────────────────────────────────────────────────────
    if data.get("conditions"):
        elements.append(Paragraph("Conditions de règlement :", style_bleu_gras))
        elements.append(Paragraph(data["conditions"], style_condition))
        elements.append(Spacer(1, 0.25 * cm))

    # ── BLOC « BON POUR ACCORD » ────────────────────────────────────────
    bloc_accord = Table([[
        Paragraph(
            "<b>Bon pour accord</b><br/>"
            "Signature et cachet du client :<br/><br/><br/>"
            "____________________________",
            style_condition,
        ),
    ]], colWidths=[7 * cm])
    bloc_accord.setStyle(TableStyle([
        ("BOX", (0, 0), (0, 0), 0.7, HDA_NOIR),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    elements.append(bloc_accord)

    # ── QR CODE VERS LE PORTAIL DE SUIVI ────────────────────────────────
    if data.get("url_suivi"):
        flux_qr_image = flux_qr(data["url_suivi"])
        if flux_qr_image is not None:
            table_qr = Table(
                [[
                    Image(flux_qr_image, width=1.8 * cm, height=1.8 * cm),
                    Paragraph(
                        "Suivez ce devis en ligne (sans mot de passe) :<br/>"
                        f"<font name='{fonte_gras}'>{data['url_suivi']}</font><br/>"
                        "Acceptez ou refusez directement depuis ce lien.",
                        style_small_gris,
                    ),
                ]],
                colWidths=[2.2 * cm, largeur_utile - 2.4 * cm],
            )
            table_qr.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
            ]))
            elements.append(table_qr)

    # ── GÉNÉRATION ───────────────────────────────────────────────────────
    doc.build(
        elements,
        canvasmaker=lambda *args, **kwargs: CanvasNumerote(
            *args,
            pied_texte=data["emetteur"]["pied_legal"],
            fontes=(fonte_normale, fonte_gras),
            **kwargs,
        ),
    )
    flux.seek(0)
    return flux.read()


# ─── ADAPTATEUR DU MODÈLE ───────────────────────────────────────────────────
def generer_pdf_devis(devis) -> bytes:
    """Génère le PDF (octets) depuis le modèle : traduit en dict data pure."""
    from core.models import Parametres
    from django.conf import settings

    params = Parametres.get()
    client = devis.demande.client
    demande = devis.demande

    # Logo : UN SEUL logo officiel pour toute l'application (site, admin, PDF, emails)
    chemin_logo = os.path.join(IMG_DIR, "logo_hda.png")
    if not os.path.isfile(chemin_logo):
        chemin_logo = None

    lignes_data = []
    for num, ligne in enumerate(devis.lignes.all(), start=1):
        lignes_data.append({
            "n": num,
            "designation": ligne.designation,
            "quantite": fmt_quantite(ligne.quantite),
            "unite": ligne.unite,
            "pu": fmt_mad(ligne.prix_unitaire_ht),
            "total": fmt_mad(ligne.total_ligne_ht),
        })

    url_suivi = f"{getattr(settings, 'SITE_URL', 'http://localhost:8000')}/suivi/{demande.token_suivi}/"
    taux_texte = str(int(devis.taux_tva)) if devis.taux_tva == devis.taux_tva.to_integral_value() else str(devis.taux_tva)
    service_nom = demande.service.nom if demande.service else ""
    mentions = params.mentions_legales_devis or (
        f"{params.nom_entreprise} SARL – Construction TCE & Aménagement – Mohammedia, Maroc"
    )
    if params.mentions_identifiants:
        mentions = f"{mentions} {params.mentions_identifiants}"

    data = {
        "emetteur": {
            "nom": params.nom_entreprise,
            "marque": f"{params.nom_entreprise} – Construction TCE – Aménagement",
            "adresses": [params.adresse_siege, params.adresse_casablanca],
            "telephone": params.telephone,
            "email": params.email_contact,
            "pied_legal": mentions,
        },
        "devis": {
            "numero": devis.numero,
            "objet": f"Prestation {service_nom}".strip() or "Prestation selon votre demande",
            "taux_tva": taux_texte,
            "date_validite": devis.date_validite.strftime("%d/%m/%Y") if devis.date_validite else "—",
        },
        "client": {
            "nom": client.nom_complet,
            "telephone": client.telephone,
            "email": client.email,
            "ville": client.ville,
        },
        "chantier": {
            "reference": demande.reference,
            "ville": demande.ville_chantier,
            "adresse": demande.adresse_chantier,
        },
        "lignes": lignes_data,
        "totaux": {
            "sous_total_ht": fmt_mad(devis.sous_total_ht),
            "montant_tva": fmt_mad(devis.montant_tva),
            "total_ttc": fmt_mad(devis.total_ttc),
        },
        "montant_lettres": montant_en_lettres(devis.total_ttc),
        "conditions": devis.conditions_reglement,
        "url_suivi": url_suivi,
        "logo_path": chemin_logo,
        "polices_dir": FONTS_DIR,
    }
    # Sécurité : les notes internes ne sont volontairement PAS incluses dans
    # data (jamais visibles du client, voir filtrer_notes_client).
    return construire_pdf(data)


def sauvegarder_pdf_devis(devis) -> None:
    """Génère le PDF du devis et l'enregistre dans fichier_pdf."""
    pdf_bytes = generer_pdf_devis(devis)
    nom_fichier = f"devis_{devis.numero}.pdf"
    devis.fichier_pdf.save(nom_fichier, ContentFile(pdf_bytes), save=True)
