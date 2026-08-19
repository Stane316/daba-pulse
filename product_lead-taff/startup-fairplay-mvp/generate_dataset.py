"""
GROWTH DECISION OS — Générateur de dataset synthétique
========================================================

Génère un dataset cohérent (pas aléatoire uniforme) avec les patterns
volontaires décrits dans le document d'architecture (§3) :

  1. Rupture de stock récurrente sur un produit précis dans une boutique
     précise (Cotonou-Centre / Farine 1kg) — pour démontrer le Risk Engine.
  2. Une boutique surplus sur le même produit (Akpakpa) — pour démontrer
     le transfert recommandé par le simulateur (cf. risk_engine.py/.php).
  3. Une boutique où la réputation chute en même temps que les ventes
     du même produit — pour démontrer le KPI Reputation-Adjusted Demand Risk.
  4. Une saisonnalité simple : hausse le week-end sur certaines catégories.

Sortie : fichiers CSV (un par table du schéma) + une base SQLite déjà
peuplée, prêts à charger directement dans schema.sql.

Reproductible : seed fixe (42).
"""

import csv
import random
import sqlite3
from datetime import date, timedelta
from pathlib import Path

random.seed(42)

OUT_DIR = Path("dataset_output")
OUT_DIR.mkdir(exist_ok=True)

REF_DATE = date(2026, 8, 6)          # aligné sur la démo de risk_engine.py/.php
NB_JOURS = 70                         # 10 semaines
DATE_DEBUT = REF_DATE - timedelta(days=NB_JOURS - 1)

# ------------------------------------------------------------------
# 1. CATÉGORIES
# ------------------------------------------------------------------

CATEGORIES = [
    (1, "Céréales & Farines", "sec"),
    (2, "Boissons", "boisson"),
    (3, "Produits laitiers", "frais"),
    (4, "Épicerie salée", "sec"),
    (5, "Snacks & Biscuits", "sec"),
]

# ------------------------------------------------------------------
# 2. PRODUITS
# id, nom, categorie_id, sous_categorie, prix_unitaire, unite, duree_de_vie_jours, fournisseur_id
# ------------------------------------------------------------------

PRODUITS = [
    (1, "Farine de blé 1kg", 1, "farine", 800.0, "unité", None, 1),
    (2, "Riz local 5kg", 1, "riz", 4200.0, "unité", None, 1),
    (3, "Maïs moulu 1kg", 1, "farine", 650.0, "unité", None, 2),
    (4, "Eau minérale 1.5L", 2, "eau", 400.0, "unité", 365, 3),
    (5, "Jus d'ananas 1L", 2, "jus", 900.0, "unité", 120, 3),
    (6, "Boisson gazeuse 33cl", 2, "soda", 350.0, "unité", 270, 3),
    (7, "Yaourt nature 500g", 3, "yaourt", 700.0, "unité", 14, 4),
    (8, "Lait caillé 1L", 3, "lait", 850.0, "unité", 10, 4),
    (9, "Fromage local 250g", 3, "fromage", 1200.0, "unité", 21, 4),
    (10, "Huile de palme 1L", 4, "huile", 1100.0, "unité", 180, 2),
    (11, "Tomate concentrée 400g", 4, "conserve", 500.0, "unité", 365, 5),
    (12, "Sardines en boîte", 4, "conserve", 600.0, "unité", 365, 5),
    (13, "Cube assaisonnement x50", 4, "épice", 1500.0, "unité", 365, 5),
    (14, "Biscuits sablés 200g", 5, "biscuit", 450.0, "unité", 90, 6),
    (15, "Chips plantain 100g", 5, "chips", 500.0, "unité", 60, 6),
    (16, "Arachides grillées 250g", 5, "snack", 400.0, "unité", 45, 6),
]

# ------------------------------------------------------------------
# 3. BOUTIQUES
# id, nom, ville, zone, type, date_ouverture
# ------------------------------------------------------------------

BOUTIQUES = [
    (10, "Boutique Cotonou-Centre", "Cotonou", "Cotonou-Est", "boutique_propre", "2021-03-01"),
    (20, "Boutique Akpakpa", "Cotonou", "Cotonou-Est", "boutique_propre", "2021-09-15"),
    (30, "Boutique Cadjehoun", "Cotonou", "Cotonou-Ouest", "boutique_propre", "2022-01-10"),
    (40, "Boutique Fidjrossè", "Cotonou", "Cotonou-Ouest", "revendeur", "2022-06-20"),
    (50, "Boutique Porto-Novo", "Porto-Novo", "Peripherie", "revendeur", "2023-02-05"),
    (60, "Boutique Calavi", "Abomey-Calavi", "Peripherie", "distributeur", "2023-08-12"),
]

# ------------------------------------------------------------------
# 4. PATTERNS INJECTÉS (les "cas" que la démo doit démontrer)
# ------------------------------------------------------------------

STORE_ID_RUPTURE = 10          # Cotonou-Centre — rupture récurrente
STORE_ID_SURPLUS = 20          # Akpakpa — surplus permettant le transfert
PRODUCT_ID_RUPTURE = 1         # Farine de blé 1kg

STORE_ID_REPUTATION = 40       # Fidjrossè — réputation en chute
PRODUCT_ID_REPUTATION = 7      # Yaourt nature 500g

CATEGORIES_WEEKEND_BOOST = {2, 5}   # Boissons + Snacks : hausse le week-end


def demande_base(product_id: int) -> float:
    """Demande journalière moyenne 'normale' par produit (avant patterns)."""
    base = {
        1: 7.0, 2: 4.0, 3: 5.0, 4: 15.0, 5: 6.0, 6: 10.0,
        7: 8.0, 8: 5.0, 9: 3.0, 10: 4.0, 11: 6.0, 12: 5.0,
        13: 3.0, 14: 9.0, 15: 8.0, 16: 7.0,
    }
    return base.get(product_id, 5.0)


def facteur_boutique(store_id: int) -> float:
    """Les grandes boutiques vendent proportionnellement plus."""
    return {10: 1.3, 20: 1.1, 30: 1.0, 40: 0.8, 50: 0.6, 60: 0.5}.get(store_id, 1.0)


# ------------------------------------------------------------------
# 5. GÉNÉRATION DES VENTES (avec patterns)
# ------------------------------------------------------------------

def generer_ventes():
    ventes = []
    vente_id = 1
    for store_id, *_ in BOUTIQUES:
        for product_id, _, categorie_id, *_ in PRODUITS:
            prix = next(p[4] for p in PRODUITS if p[0] == product_id)
            for i in range(NB_JOURS):
                d = DATE_DEBUT + timedelta(days=i)
                base = demande_base(product_id) * facteur_boutique(store_id)

                # Saisonnalité : +35% le week-end pour certaines catégories
                if d.weekday() >= 5 and categorie_id in CATEGORIES_WEEKEND_BOOST:
                    base *= 1.35

                # Pattern 1 : rupture récurrente — demande en forte hausse sur
                # les 2 dernières semaines à Cotonou-Centre pour la farine
                if store_id == STORE_ID_RUPTURE and product_id == PRODUCT_ID_RUPTURE:
                    if i >= NB_JOURS - 7:
                        base *= 1.8       # semaine finale : demande en forte hausse
                    elif i >= NB_JOURS - 14:
                        base *= 1.3

                # Pattern 3 : réputation en baisse -> les clients achètent
                # de moins en moins ce produit au fil des semaines
                if store_id == STORE_ID_REPUTATION and product_id == PRODUCT_ID_REPUTATION:
                    semaine = i // 7
                    base *= max(0.35, 1.0 - semaine * 0.09)

                quantite = max(0, round(random.gauss(base, base * 0.2)))
                if quantite == 0:
                    continue

                ventes.append({
                    "vente_id": vente_id,
                    "date": d.isoformat(),
                    "store_id": store_id,
                    "product_id": product_id,
                    "quantite": quantite,
                    "prix_unitaire": prix,
                    "canal": random.choices(
                        ["boutique", "en_ligne", "revendeur"], weights=[0.75, 0.15, 0.10]
                    )[0],
                })
                vente_id += 1
    return ventes


# ------------------------------------------------------------------
# 6. GÉNÉRATION DES STOCKS (simulation jour par jour, avec politique de réappro)
# ------------------------------------------------------------------

def generer_stocks(ventes):
    ventes_par_jour = {}
    for v in ventes:
        cle = (v["date"], v["store_id"], v["product_id"])
        ventes_par_jour[cle] = ventes_par_jour.get(cle, 0) + v["quantite"]

    stocks = []
    snapshot_id = 1

    for store_id, *_ in BOUTIQUES:
        for product_id, *_ in PRODUITS:
            base = demande_base(product_id) * facteur_boutique(store_id)
            seuil_min = max(5, round(base * 4))     # ~4 jours de couverture minimum visé
            seuil_max = seuil_min * 3
            stock_courant = seuil_max

            # Pattern 2 : Akpakpa est volontairement en surplus permanent sur la farine
            if store_id == STORE_ID_SURPLUS and product_id == PRODUCT_ID_RUPTURE:
                stock_courant = 200
                seuil_min = 30

            for i in range(NB_JOURS):
                d = DATE_DEBUT + timedelta(days=i)
                vendu = ventes_par_jour.get((d.isoformat(), store_id, product_id), 0)
                stock_courant = max(0, stock_courant - vendu)

                # Politique de réapprovisionnement "normale" : dès qu'on repasse
                # sous le seuil, on recomplète au seuil_max le lendemain — SAUF
                # pour le cas volontairement cassé (rupture récurrente à démontrer)
                est_cas_rupture = (store_id == STORE_ID_RUPTURE and product_id == PRODUCT_ID_RUPTURE)
                if stock_courant < seuil_min and not est_cas_rupture:
                    stock_courant = seuil_max
                elif stock_courant < seuil_min and est_cas_rupture and i < NB_JOURS - 10:
                    # réappro partiel et tardif avant la période de démo finale
                    stock_courant += round(seuil_min * 0.6)

                stocks.append({
                    "snapshot_id": snapshot_id,
                    "date": d.isoformat(),
                    "store_id": store_id,
                    "product_id": product_id,
                    "quantite_disponible": stock_courant,
                    "seuil_min": seuil_min,
                    "seuil_max": seuil_max,
                })
                snapshot_id += 1

    return stocks


# ------------------------------------------------------------------
# 7. GÉNÉRATION DES AVIS CLIENTS
# ------------------------------------------------------------------

COMMENTAIRES_POSITIFS = [
    "Très bon accueil, produit frais.", "Rapide et bien organisé.",
    "Je recommande cette boutique.", "Bon rapport qualité-prix.",
]
COMMENTAIRES_NEUTRES = [
    "Correct, rien à signaler.", "Boutique standard.", "Sans plus.",
]
COMMENTAIRES_NEGATIFS = [
    "Produit périmé reçu.", "Rupture de stock fréquente.",
    "Accueil peu agréable.", "Qualité en baisse ces derniers temps.",
]


def generer_avis():
    avis = []
    avis_id = 1
    for store_id, *_ in BOUTIQUES:
        nb_avis_jours = random.sample(range(NB_JOURS), k=min(NB_JOURS, random.randint(15, 30)))
        for i in nb_avis_jours:
            d = DATE_DEBUT + timedelta(days=i)
            product_id = random.choice([p[0] for p in PRODUITS]) if random.random() > 0.3 else None

            # Pattern 3 : Fidjrossè -> note qui se dégrade semaine après semaine
            # sur le produit concerné (et légèrement en général)
            if store_id == STORE_ID_REPUTATION:
                semaine = i // 7
                if product_id == PRODUCT_ID_REPUTATION or (product_id is None and random.random() < 0.5):
                    note = max(1, round(random.gauss(4.5 - semaine * 0.35, 0.6)))
                else:
                    note = max(1, min(5, round(random.gauss(4.0, 0.7))))
            else:
                note = max(1, min(5, round(random.gauss(4.2, 0.8))))

            if note >= 4:
                sentiment, texte = "positif", random.choice(COMMENTAIRES_POSITIFS)
            elif note == 3:
                sentiment, texte = "neutre", random.choice(COMMENTAIRES_NEUTRES)
            else:
                sentiment, texte = "negatif", random.choice(COMMENTAIRES_NEGATIFS)

            avis.append({
                "avis_id": avis_id,
                "date": d.isoformat(),
                "store_id": store_id,
                "product_id": product_id if product_id is not None else "",
                "note": min(5, note),
                "texte": texte,
                "sentiment": sentiment,
                "canal": random.choices(
                    ["application", "site", "qr_code", "guichet"], weights=[0.4, 0.2, 0.15, 0.25]
                )[0],
            })
            avis_id += 1
    # Injection dédiée : garantit des avis RÉCENTS et SPÉCIFIQUES au produit
    # concerné pour la boutique à réputation en baisse. Sans ça, l'assignation
    # aléatoire du product_id peut laisser trop peu (voire aucun) avis proche
    # de la date de référence pour ce produit précis -> signal non détectable.
    for i in range(NB_JOURS - 21, NB_JOURS, 4):  # un avis tous les ~4 jours sur les 3 dernières semaines
        semaine = i // 7
        d = DATE_DEBUT + timedelta(days=i)
        note = max(1, round(random.gauss(4.3 - semaine * 0.4, 0.4)))
        sentiment = "positif" if note >= 4 else ("neutre" if note == 3 else "negatif")
        texte = (random.choice(COMMENTAIRES_POSITIFS) if sentiment == "positif"
                  else random.choice(COMMENTAIRES_NEUTRES) if sentiment == "neutre"
                  else random.choice(COMMENTAIRES_NEGATIFS))
        avis.append({
            "avis_id": avis_id,
            "date": d.isoformat(),
            "store_id": STORE_ID_REPUTATION,
            "product_id": PRODUCT_ID_REPUTATION,
            "note": min(5, note),
            "texte": texte,
            "sentiment": sentiment,
            "canal": random.choices(
                ["application", "site", "qr_code", "guichet"], weights=[0.4, 0.2, 0.15, 0.25]
            )[0],
        })
        avis_id += 1

    return avis


# ------------------------------------------------------------------
# 8. ÉCRITURE DES CSV
# ------------------------------------------------------------------

def ecrire_csv(nom_fichier, lignes, colonnes):
    chemin = OUT_DIR / nom_fichier
    with open(chemin, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=colonnes)
        writer.writeheader()
        for ligne in lignes:
            writer.writerow(ligne)
    return chemin


def main():
    ventes = generer_ventes()
    stocks = generer_stocks(ventes)
    avis = generer_avis()

    ecrire_csv("categorie.csv",
               [{"categorie_id": c[0], "nom": c[1], "famille": c[2]} for c in CATEGORIES],
               ["categorie_id", "nom", "famille"])

    ecrire_csv("produit.csv",
               [{"product_id": p[0], "nom": p[1], "categorie_id": p[2], "sous_categorie": p[3],
                 "prix_unitaire": p[4], "unite": p[5], "duree_de_vie_jours": p[6] or "",
                 "fournisseur_id": p[7]} for p in PRODUITS],
               ["product_id", "nom", "categorie_id", "sous_categorie", "prix_unitaire",
                "unite", "duree_de_vie_jours", "fournisseur_id"])

    ecrire_csv("boutique.csv",
               [{"store_id": b[0], "nom": b[1], "ville": b[2], "zone": b[3], "type": b[4],
                 "date_ouverture": b[5], "actif": 1} for b in BOUTIQUES],
               ["store_id", "nom", "ville", "zone", "type", "date_ouverture", "actif"])

    ecrire_csv("vente.csv", ventes,
               ["vente_id", "date", "store_id", "product_id", "quantite", "prix_unitaire", "canal"])

    ecrire_csv("stock.csv", stocks,
               ["snapshot_id", "date", "store_id", "product_id", "quantite_disponible",
                "seuil_min", "seuil_max"])

    ecrire_csv("avis_client.csv", avis,
               ["avis_id", "date", "store_id", "product_id", "note", "texte", "sentiment", "canal"])

    print(f"Ventes générées   : {len(ventes)}")
    print(f"Snapshots stock   : {len(stocks)}")
    print(f"Avis générés      : {len(avis)}")

    return ventes, stocks, avis


if __name__ == "__main__":
    main()
