"""
Moteur de calcul financier des devis H.D.A GLOBAL.
Inspiré de l'algorithme de QuotePilot (djm-1/QuotePilot) — réimplémenté originalement.

Règle fondamentale : TOUS les calculs financiers se font exclusivement côté serveur
en utilisant le type Decimal avec arrondi ROUND_HALF_UP.
Aucun calcul n'est délégué au frontend.
"""
from decimal import Decimal, ROUND_HALF_UP


def arrondir_monnaie(valeur) -> Decimal:
    """
    Arrondit une valeur monétaire à 2 décimales (centimes).
    Utilise ROUND_HALF_UP conforme aux pratiques commerciales marocaines.
    """
    return Decimal(str(valeur)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calculer_total_ligne(quantite, prix_unitaire_ht) -> Decimal:
    """
    Calcule le montant HT d'une ligne de devis.

    Formule : Total Ligne HT = Quantité × Prix Unitaire HT
    """
    return arrondir_monnaie(Decimal(str(quantite)) * Decimal(str(prix_unitaire_ht)))


def calculer_totaux(lignes, taux_tva) -> dict:
    """
    Version PURE du calcul des totaux (sans accès à la base de données).

    Args:
        lignes : itérable de tuples/dicts/objets avec (quantite, prix_unitaire_ht)
                 — chaque élément peut être :
                    - un tuple (quantite, prix_unitaire_ht)
                    - un dictionnaire {"quantite": ..., "prix_unitaire_ht": ...}
                    - un objet avec les attributs quantite / prix_unitaire_ht
        taux_tva : taux de TVA en pourcentage (ex. Decimal("20.00"))

    Returns:
        dict : {"lignes": [Decimal(x) * ...], "sous_total_ht": ..., "montant_tva": ..., "total_ttc": ...}
        Chaque entrée "lignes" est le Total Ligne HT correspondant, déjà arrondi.
    """
    totaux_lignes = []
    sous_total_ht = Decimal("0.00")

    for ligne in lignes:
        if isinstance(ligne, (tuple, list)):
            quantite, prix_unitaire_ht = ligne
        elif isinstance(ligne, dict):
            quantite = ligne["quantite"]
            prix_unitaire_ht = ligne["prix_unitaire_ht"]
        else:
            quantite = ligne.quantite
            prix_unitaire_ht = ligne.prix_unitaire_ht

        total = calculer_total_ligne(quantite, prix_unitaire_ht)
        totaux_lignes.append(total)
        sous_total_ht += total

    taux = Decimal(str(taux_tva))
    montant_tva = arrondir_monnaie(sous_total_ht * taux / Decimal("100"))
    total_ttc = arrondir_monnaie(sous_total_ht + montant_tva)

    return {
        "lignes": totaux_lignes,
        "sous_total_ht": arrondir_monnaie(sous_total_ht),
        "montant_tva": montant_tva,
        "total_ttc": total_ttc,
    }


def recalculer_devis(devis) -> "Devis":
    """
    Recalcule l'intégralité des totaux d'un devis depuis ses lignes.
    Toujours appelé après chaque ajout/modification/suppression d'une ligne.

    Formules :
        Sous-total HT = Σ (Quantité × Prix Unitaire HT) pour chaque ligne
        Montant TVA   = Sous-total HT × (Taux TVA / 100)
        Total TTC     = Sous-total HT + Montant TVA
    """
    sous_total_ht = Decimal("0.00")

    # Recalculer chaque ligne individuellement
    for ligne in devis.lignes.all():
        ligne.total_ligne_ht = calculer_total_ligne(ligne.quantite, ligne.prix_unitaire_ht)
        ligne.save(update_fields=["total_ligne_ht"])
        sous_total_ht += ligne.total_ligne_ht

    taux_tva = Decimal(str(devis.taux_tva))
    montant_tva = arrondir_monnaie(sous_total_ht * taux_tva / Decimal("100"))
    total_ttc = arrondir_monnaie(sous_total_ht + montant_tva)

    devis.sous_total_ht = arrondir_monnaie(sous_total_ht)
    devis.montant_tva = montant_tva
    devis.total_ttc = total_ttc
    devis.save(update_fields=["sous_total_ht", "montant_tva", "total_ttc", "updated_at"])

    return devis

