# RÉFÉRENCES & INSPIRATIONS LOGICIELLES — H.D.A GLOBAL

Conformément à la spécification (`SPEC.md`), ce projet réimplémente de façon originale et propre des concepts observés dans l'écosystème open-source. Aucun code source n'a été copié-collé, garantissant le respect strict des licences et l'intégrité académique du PFE.

---

## 1. Dépôts Analysés et Inspirations

### 1. Invoicerr (`invoicerr-app/invoicerr`)
- **Dépôt** : [https://github.com/invoicerr-app/invoicerr](https://github.com/invoicerr-app/invoicerr)
- **Licence** : GNU AGPL-3.0
- **Concepts retenus** :
  - Cycle de vie des statuts de devis : `Brouillon` (Draft) $\rightarrow$ `Envoyé` (Sent) $\rightarrow$ `Accepté` (Approved) $\rightarrow$ `Refusé` (Rejected).
  - Modélisation relationnelle : Devis (en-tête) avec Lignes d'articles (quantité, désignation, prix unitaire, total).
  - Présentation claire des documents PDF avec logo de l'entreprise, coordonnées et mentions légales.

### 2. Summit (`TWN-Systems/summit`)
- **Dépôt** : [https://github.com/TWN-Systems/summit](https://github.com/TWN-Systems/summit)
- **Licence** : MIT
- **Concepts retenus** :
  - Espace de consultation sécurisé sans mot de passe : génération d'un jeton aléatoire à entropie élevée (`token_suivi` UUID4).
  - Expérience utilisateur fluide où le client consulte l'avancement et télécharge ses documents directement via un lien sécurisé envoyé par email.

### 3. KodLyft FSM (`kodlyft/fsm`)
- **Dépôt** : [https://github.com/kodlyft/fsm](https://github.com/kodlyft/fsm)
- **Licence** : MIT
- **Concepts retenus** :
  - Modèle simplifié de gestion d'interventions sur site (*Field Service Management*) adapté au BTP.
  - Planification d'une intervention rattachée à la demande : date début, date fin, responsable/chef d'équipe, lieu de chantier et notes de suivi.

### 4. QuotePilot (`djm-1/QuotePilot`)
- **Dépôt** : [https://github.com/djm-1/QuotePilot](https://github.com/djm-1/QuotePilot)
- **Licence** : Open source (non spécifiée)
- **Concepts retenus** :
  - Calcul de prix 100 % déterministe et validé côté serveur (Backend) : aucun calcul financier n'est délégué ou pris pour argent comptant depuis le frontend.
  - Calcul rigoureux : $\text{Sous-total HT} = \sum (\text{Quantité} \times \text{Prix unitaire})$, $\text{TVA} = \text{HT} \times \text{Taux}$, $\text{Total TTC} = \text{HT} + \text{TVA}$.

### 5. Ecommdev Platform (`GodOfStrategy/ecommdev-platform`)
- **Dépôt** : Référence conceptuelle citée dans la spécification (dépôt privé ou 404 sur GitHub public).
- **Concepts retenus** :
  - Découpage modulaire canonique d'un projet Django pour la gestion d'entreprise en applications spécialisées et indépendantes.

---

## 2. Présence Web Actuelle de l'Entreprise
- **Site vitrine analysé** : [https://hdaglobal.netlify.app/](https://hdaglobal.netlify.app/)
- **Document source** : Flyer publicitaire officiel `HDA.Fiche-Services.jpeg`
- **Données de marque collectées** :
  - Raison sociale : H.D.A GLOBAL SARL
  - Adresses : Mohammedia (Beni Yakhlef) et Casablanca (11, rue Ahmed Sitou, BD Mohamed V)
  - Téléphone : `+212 661103988`
  - Email : `hda.global82@gmail.com`

