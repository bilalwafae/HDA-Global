"""
Crée un client + une demande de TEST pour vérifier tout le flux :
  python manage.py creer_client_test --email votre.adresse@gmail.com [--nom "Votre Nom"]

Ensuite : admin → Demandes de devis → passer le statut à « Acceptée » → le devis est généré
→ ouvrir le devis → « Envoyer au client par email » → le PDF arrive dans la boîte mail.
"""
from django.core.management.base import BaseCommand

from clients.models import Client
from demandes.models import Demande
from services.models import Service


class Command(BaseCommand):
    help = "Crée un client de test (votre email perso) avec une demande prête à être acceptée."

    def add_arguments(self, parser):
        parser.add_argument("--email", required=True, help="Votre adresse email personnelle")
        parser.add_argument("--nom", default="Client Test HDA")
        parser.add_argument("--telephone", default="+212600000000")
        parser.add_argument("--ville", default="Casablanca")

    def handle(self, *args, **o):
        client, cree = Client.objects.get_or_create(
            email=o["email"],
            defaults={"nom_complet": o["nom"], "telephone": o["telephone"], "ville": o["ville"]},
        )
        service = (Service.objects.filter(nom__icontains="Climatisation").first()
                   or Service.objects.first())
        demande = Demande.objects.create(
            client=client, service=service, ville_chantier=o["ville"],
            adresse_chantier="12 rue des Orangers, Maârif, Casablanca",
            surface_m2=85,
            description_besoin="Installation de la climatisation dans un appartement de 85 m2 "
                               "(salon + 3 chambres). Demande de TEST.",
            statut=Demande.STATUT_NOUVELLE,
        )
        self.stdout.write(self.style.SUCCESS(
            f"Client {'créé' if cree else 'existant'} : {client.email} — demande {demande.reference} créée."
        ))
