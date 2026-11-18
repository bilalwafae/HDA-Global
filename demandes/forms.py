"""
Formulaire de demande de devis public.
Inclut le honeypot anti-spam et la validation côté serveur.
"""
from django import forms
from services.models import Service


# Liste complète des villes marocaines, regroupées par région administrative.
# Format à optgroups (compatible ChoiceField) : ("Région", [("valeur", "Libellé"), ...])
VILLES_MAROC = [
    ("Grand Casablanca & Settat", [
        ("Casablanca", "Casablanca"),
        ("Mohammedia", "Mohammedia"),
        ("Beni Yakhlef", "Beni Yakhlef"),
        ("Bouskoura", "Bouskoura"),
        ("Dar Bouazza", "Dar Bouazza"),
        ("El Jadida", "El Jadida"),
        ("Azemmour", "Azemmour"),
        ("Sidi Bennour", "Sidi Bennour"),
        ("Oualidia", "Oualidia"),
        ("Khemis Zemamra", "Khemis Zemamra"),
        ("Berrechid", "Berrechid"),
        ("Settat", "Settat"),
        ("Benslimane", "Benslimane"),
        ("Had Soualem", "Had Soualem"),
        ("Mediouna", "Mediouna"),
        ("Tit Mellil", "Tit Mellil"),
        ("Nouaceur", "Nouaceur"),
        ("Ain Harrouda", "Ain Harrouda"),
    ]),
    ("Rabat - Salé - Kénitra", [
        ("Rabat", "Rabat"),
        ("Salé", "Salé"),
        ("Témara", "Témara"),
        ("Harhoura", "Harhoura"),
        ("Skhirat", "Skhirat"),
        ("Kénitra", "Kénitra"),
        ("Mehdia", "Mehdia"),
        ("Sidi Slimane", "Sidi Slimane"),
        ("Sidi Kacem", "Sidi Kacem"),
        ("Mechra Bel Ksiri", "Mechra Bel Ksiri"),
        ("Khémisset", "Khémisset"),
        ("Rommani", "Rommani"),
        ("Tiflet", "Tiflet"),
    ]),
    ("Tanger - Tétouan - Al Hoceïma", [
        ("Tanger", "Tanger"),
        ("Tétouan", "Tétouan"),
        ("Al Hoceima", "Al Hoceima"),
        ("Larache", "Larache"),
        ("Ksar El Kébir", "Ksar El Kébir"),
        ("Chefchaouen", "Chefchaouen"),
        ("Asilah", "Asilah"),
        ("Fnideq", "Fnideq"),
        ("Martil", "Martil"),
        ("Mdiq", "Mdiq"),
        ("Oued Laou", "Oued Laou"),
        ("Imzouren", "Imzouren"),
        ("Targuist", "Targuist"),
    ]),
    ("Fès - Meknès", [
        ("Fès", "Fès"),
        ("Meknès", "Meknès"),
        ("Ifrane", "Ifrane"),
        ("Sefrou", "Sefrou"),
        ("Azrou", "Azrou"),
        ("Moulay Idriss Zerhoun", "Moulay Idriss Zerhoun"),
        ("Imouzzer Kandar", "Imouzzer Kandar"),
        ("Sidi Harazem", "Sidi Harazem"),
        ("Bhalil", "Bhalil"),
    ]),
    ("L'Oriental", [
        ("Oujda", "Oujda"),
        ("Nador", "Nador"),
        ("Saïdia", "Saïdia"),
        ("Berkane", "Berkane"),
        ("Taourirt", "Taourirt"),
        ("Taza", "Taza"),
        ("Guercif", "Guercif"),
        ("Jerada", "Jerada"),
        ("Driouch", "Driouch"),
        ("Al Aroui", "Al Aroui"),
        ("Midar", "Midar"),
        ("Ahfir", "Ahfir"),
        ("Figuig", "Figuig"),
        ("Bouarfa", "Bouarfa"),
    ]),
    ("Béni Mellal - Khénifra", [
        ("Béni Mellal", "Béni Mellal"),
        ("Khénifra", "Khénifra"),
        ("Khouribga", "Khouribga"),
        ("Fkih Ben Salah", "Fkih Ben Salah"),
        ("Kasba Tadla", "Kasba Tadla"),
        ("Oued Zem", "Oued Zem"),
        ("Azilal", "Azilal"),
        ("Mrirt", "Mrirt"),
        ("El Ksiba", "El Ksiba"),
    ]),
    ("Marrakech - Safi", [
        ("Marrakech", "Marrakech"),
        ("Safi", "Safi"),
        ("Essaouira", "Essaouira"),
        ("Youssoufia", "Youssoufia"),
        ("El Kelaâ des Sraghna", "El Kelaâ des Sraghna"),
        ("Benguerir", "Benguerir"),
        ("Chichaoua", "Chichaoua"),
        ("Demnate", "Demnate"),
        ("Aït Ourir", "Aït Ourir"),
        ("Tahannaout", "Tahannaout"),
        ("Sidi Rahal", "Sidi Rahal"),
        ("Asni", "Asni"),
        ("Amizmiz", "Amizmiz"),
    ]),
    ("Drâa - Tafilalet", [
        ("Errachidia", "Errachidia"),
        ("Ouarzazate", "Ouarzazate"),
        ("Zagora", "Zagora"),
        ("Tinghir", "Tinghir"),
        ("Midelt", "Midelt"),
        ("Rissani", "Rissani"),
        ("Merzouga", "Merzouga"),
        ("Boumalne Dadès", "Boumalne Dadès"),
        ("Kelaat M'Gouna", "Kelaat M'Gouna"),
        ("Skoura", "Skoura"),
        ("Goulmima", "Goulmima"),
        ("Agdz", "Agdz"),
        ("Tinejdad", "Tinejdad"),
    ]),
    ("Souss - Massa", [
        ("Agadir", "Agadir"),
        ("Inezgane", "Inezgane"),
        ("Aït Melloul", "Aït Melloul"),
        ("Taroudant", "Taroudant"),
        ("Tiznit", "Tiznit"),
        ("Oulad Teïma", "Oulad Teïma"),
        ("Dcheira El Jihadia", "Dcheira El Jihadia"),
        ("Biougra", "Biougra"),
        ("Tata", "Tata"),
    ]),
    ("Guelmim - Oued Noun", [
        ("Guelmim", "Guelmim"),
        ("Tan-Tan", "Tan-Tan"),
        ("Sidi Ifni", "Sidi Ifni"),
    ]),
    ("Laâyoune - Sakia El Hamra", [
        ("Laâyoune", "Laâyoune"),
        ("Boujdour", "Boujdour"),
        ("Es-Smara", "Es-Smara"),
        ("Tarfaya", "Tarfaya"),
    ]),
    ("Dakhla - Oued Ed Dahab", [
        ("Dakhla", "Dakhla"),
        ("Aousserd", "Aousserd"),
    ]),
    ("Autre", [
        ("Autre", "Autre (précisez dans l'adresse)"),
    ]),
]

TYPES_FICHIERS_AUTORISES = [
    "image/jpeg", "image/png", "image/webp",
    "application/pdf",
]
TAILLE_MAX_FICHIER = 10 * 1024 * 1024  # 10 Mo


class MultipleFileInput(forms.FileInput):
    allow_multiple_selected = True


class DemandeDevisForm(forms.Form):
    """Formulaire public de demande de devis."""

    # ---- Informations du demandeur ----
    nom_complet = forms.CharField(
        max_length=200,
        label="Nom complet *",
        widget=forms.TextInput(attrs={"placeholder": "Votre nom et prénom"}),
    )
    email = forms.EmailField(
        label="Email *",
        widget=forms.EmailInput(attrs={"placeholder": "votre@email.com"}),
    )
    telephone = forms.CharField(
        max_length=20,
        label="Téléphone *",
        widget=forms.TextInput(attrs={"placeholder": "+212 6XX XXX XXX"}),
    )

    # ---- Service demandé ----
    service = forms.ModelChoiceField(
        queryset=Service.objects.filter(actif=True).order_by("ordre_affichage"),
        label="Type de prestation *",
        empty_label="— Sélectionner un service —",
        required=True,
    )

    # ---- Localisation du chantier ----
    ville_chantier = forms.ChoiceField(
        choices=VILLES_MAROC,
        label="Ville du chantier *",
        required=True,
    )
    adresse_chantier = forms.CharField(
        label="Adresse complète du chantier *",
        widget=forms.Textarea(attrs={
            "rows": 2,
            "placeholder": "Numéro, rue, quartier, commune...",
        }),
    )

    # ---- Détails de la demande ----
    date_souhaitee = forms.DateField(
        label="Date souhaitée d'intervention",
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    surface_m2 = forms.DecimalField(
        label="Surface estimée (m²)",
        required=False,
        min_value=0,
        decimal_places=1,
        widget=forms.NumberInput(attrs={"placeholder": "Ex : 45.5"}),
    )
    description_besoin = forms.CharField(
        label="Description du projet *",
        widget=forms.Textarea(attrs={
            "rows": 5,
            "placeholder": (
                "Décrivez votre projet avec le maximum de détails : "
                "nature des travaux, contraintes d'accès, matériaux souhaités..."
            ),
        }),
    )

    # ---- Pièces jointes ----
    photos = forms.FileField(
        label="Photos du chantier (optionnel)",
        required=False,
        widget=MultipleFileInput(attrs={"accept": "image/*,.pdf"}),
    )

    # ---- Honeypot anti-spam (champ caché que les bots remplissent) ----
    website = forms.CharField(
        required=False,
        widget=forms.HiddenInput(),
        label="",  # Invisible pour les humains
    )

    def clean_website(self):
        """Détecte les soumissions de bots via le champ honeypot."""
        website = self.cleaned_data.get("website", "")
        if website:
            raise forms.ValidationError("Soumission suspecte détectée.")
        return website

    def clean_telephone(self):
        tel = self.cleaned_data.get("telephone", "").strip()
        # Retirer les espaces pour la validation
        tel_clean = tel.replace(" ", "").replace("-", "")
        if len(tel_clean) < 8:
            raise forms.ValidationError("Numéro de téléphone invalide (minimum 8 chiffres).")
        return tel

    def clean_ville_chantier(self):
        ville = self.cleaned_data.get("ville_chantier", "")
        if not ville:
            raise forms.ValidationError("Veuillez sélectionner une ville.")
        return ville

    def clean_description_besoin(self):
        desc = self.cleaned_data.get("description_besoin", "").strip()
        if len(desc) < 20:
            raise forms.ValidationError(
                "Description trop courte. Veuillez donner plus de détails sur votre projet."
            )
        return desc

