"""
Service d'envoi d'emails automatiques (SMTP Gmail en production, console en dev).

- Emails HTML + version texte (meilleure délivrabilité, pas de HTML brut en texte).
- Logo officiel incorporé (image « cid:logo_hda ») : visible sans « afficher les images ».
- Pièce jointe possible (PDF du devis).
- `_send` ne lève jamais d'exception : il retourne (ok, message_erreur) pour que l'appelant
  informe l'administrateur au lieu de planter ou de faire croire que tout est parti.
"""
import os
from email.mime.image import MIMEImage

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

LOGO_PATH = os.path.join(settings.BASE_DIR, "static", "img", "logo_hda.png")


def _contexte(contexte):
    ctx = dict(contexte)
    ctx.setdefault("site_url", settings.SITE_URL.rstrip("/"))
    ctx.setdefault("hda_email", settings.HDA_EMAIL)
    ctx.setdefault("hda_phone", settings.HDA_PHONE)
    return ctx


def _texte_brut(html):
    """Version texte lisible : retire <style>, balises ; garde les sauts de ligne."""
    import re
    html = re.sub(r"(?is)<(style|head)[^>]*>.*?</\1>", "", html)
    html = re.sub(r"(?i)<br\s*/?>|</(p|h\d|div|tr)>", "\n", html)
    texte = strip_tags(html)
    lignes = [l.strip() for l in texte.splitlines()]
    return "\n".join(l for l in lignes if l)


def _send(subject, template, context, recipient_list, pieces_jointes=None, reply_to=None):
    """Envoie un email HTML. Retourne (True, "") ou (False, "message d'erreur")."""
    try:
        html = render_to_string(template, _contexte(context))
        email = EmailMultiAlternatives(
            subject=subject,
            body=_texte_brut(html),
            from_email=f"H.D.A GLOBAL <{settings.DEFAULT_FROM_EMAIL}>",
            to=list(recipient_list),
            reply_to=reply_to or [settings.HDA_EMAIL],
        )
        email.attach_alternative(html, "text/html")
        # Logo incorporé (le HTML y fait référence par cid:logo_hda)
        if "cid:logo_hda" in html and os.path.isfile(LOGO_PATH):
            with open(LOGO_PATH, "rb") as f:
                logo = MIMEImage(f.read(), _subtype="png")
            logo.add_header("Content-ID", "<logo_hda>")
            logo.add_header("Content-Disposition", "inline", filename="logo_hda.png")
            email.attach(logo)
        for nom, contenu, mimetype in (pieces_jointes or []):
            email.attach(nom, contenu, mimetype)
        email.send(fail_silently=False)
        return True, ""
    except Exception as e:  # SMTP refusé, mot de passe invalide, réseau coupé…
        print(f"[EMAIL] Erreur envoi '{subject}': {e}")
        return False, str(e)


def envoyer_confirmation_client(demande):
    """Email de confirmation envoyé au client après soumission de sa demande."""
    return _send(
        subject=f"[H.D.A GLOBAL] Votre demande {demande.reference} a bien été reçue",
        template="demandes/emails/confirmation_client.html",
        context={"demande": demande},
        recipient_list=[demande.client.email],
    )


def envoyer_notification_admin(demande):
    """Alerte envoyée à H.D.A GLOBAL lors d'une nouvelle demande."""
    return _send(
        subject=f"[NOUVELLE DEMANDE] {demande.reference} — {demande.client.nom_complet} — {demande.ville_chantier}",
        template="demandes/emails/notification_admin.html",
        context={"demande": demande},
        recipient_list=[settings.HDA_EMAIL],
    )


def envoyer_notification_changement_statut(demande):
    """Notifie le client que le statut de sa demande a changé."""
    return _send(
        subject=f"[H.D.A GLOBAL] Mise à jour de votre demande {demande.reference}",
        template="demandes/emails/changement_statut.html",
        context={"demande": demande},
        recipient_list=[demande.client.email],
    )


def envoyer_devis_client(devis):
    """
    Envoie le devis au client : PDF OFFICIEL EN PIÈCE JOINTE + lien sécurisé de suivi
    (acceptation / refus en ligne). Régénère le PDF avant l'envoi pour qu'il reflète
    exactement les lignes actuelles. Retourne (ok, erreur).
    """
    from devis.pdf import sauvegarder_pdf_devis
    try:
        sauvegarder_pdf_devis(devis)
        devis.fichier_pdf.open("rb")
        try:
            contenu_pdf = devis.fichier_pdf.read()
        finally:
            devis.fichier_pdf.close()
    except Exception as e:
        return False, f"Génération du PDF impossible : {e}"
    return _send(
        subject=f"[H.D.A GLOBAL] Votre devis {devis.numero} est disponible",
        template="devis/emails/devis_client.html",
        context={"devis": devis, "demande": devis.demande},
        recipient_list=[devis.demande.client.email],
        pieces_jointes=[(f"Devis_{devis.numero}.pdf", contenu_pdf, "application/pdf")],
    )
