# Flux « Acceptée → devis automatique → envoi au client »

1. Admin → Demandes de devis → ouvrir une demande → Statut = **Acceptée** → Enregistrer
   (ou cocher plusieurs demandes → action « Marquer Acceptée et générer le devis »).
2. Le devis BROUILLON (lignes + totaux + PDF avec logo) est généré automatiquement ; un message vert
   donne le lien pour l'ouvrir ; la fiche de la demande affiche aussi le bouton « Ouvrir le devis ».
3. L'administrateur relit/modifie puis clique **Envoyer au client par email** :
   email HTML (logo) + **PDF en pièce jointe** + lien de suivi sécurisé. Le statut passe à « Devis envoyé »
   uniquement si l'email est réellement parti (sinon message d'erreur et rien ne change).

## Configuration SMTP (.env)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com / EMAIL_PORT=587 / EMAIL_USE_TLS=True
EMAIL_HOST_USER=hda.global82@gmail.com
EMAIL_HOST_PASSWORD=<mot de passe d'application Gmail, sans espaces>
HDA_EMAIL=hda.global82@gmail.com
SITE_URL=http://localhost:8000   (URL publique en production : sert aux liens des emails et au QR du PDF)
Pour tester sans envoyer : EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend

## Tester avec votre email perso
python manage.py migrate
python manage.py creer_client_test --email VOTRE_EMAIL --nom "Votre Nom"
puis suivre les étapes 1-3 sur la demande créée.
