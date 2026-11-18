from django.db import migrations, models

ANCIEN = " ICE : 000000000000000 — RC : 000000 — IF : 00000000"


def retirer_zeros(apps, schema_editor):
    P = apps.get_model("core", "Parametres")
    for p in P.objects.all():
        if ANCIEN in p.mentions_legales_devis:
            p.mentions_legales_devis = p.mentions_legales_devis.replace(ANCIEN, "")
            p.save(update_fields=["mentions_legales_devis"])


class Migration(migrations.Migration):
    dependencies = [("core", "0002_email_contact_global82")]
    operations = [
        migrations.AddField("parametres", "ice", models.CharField(blank=True, default="", max_length=20, verbose_name="ICE", help_text="Identifiant Commun de l'Entreprise (15 chiffres)")),
        migrations.AddField("parametres", "identifiant_fiscal", models.CharField(blank=True, default="", max_length=20, verbose_name="Identifiant Fiscal (IF)")),
        migrations.AddField("parametres", "rc", models.CharField(blank=True, default="", max_length=40, verbose_name="Registre de Commerce (RC)", help_text="Ex : 123456 Casablanca")),
        migrations.RunPython(retirer_zeros, migrations.RunPython.noop),
    ]
