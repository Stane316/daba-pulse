#!/usr/bin/env python3
"""Génère le dataset synthétique DabaPulse pour la démonstration.

Les données sont EXPLICITEMENT synthétiques et ne représentent PAS
les opérations réelles de DABA SAS.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "sample"
OUT.mkdir(parents=True, exist_ok=True)

RNG = np.random.default_rng(42)

BOUTIQUES = [
    {"id": "B001", "nom": "DABA Plateau", "ville": "Abidjan", "zone": "Centre"},
    {"id": "B002", "nom": "DABA Cocody", "ville": "Abidjan", "zone": "Est"},
    {"id": "B003", "nom": "DABA Yopougon", "ville": "Abidjan", "zone": "Ouest"},
    {"id": "B004", "nom": "DABA Bouaké", "ville": "Bouaké", "zone": "Centre-Nord"},
    {"id": "B005", "nom": "DABA San-Pédro", "ville": "San-Pédro", "zone": "Sud-Ouest"},
]

PRODUITS = [
    {"id": "P001", "nom": "Poulet prêt à cuire 1,2 kg", "categorie": "Volaille fraîche", "prix": 4500},
    {"id": "P002", "nom": "Poulet découpé familial", "categorie": "Volaille fraîche", "prix": 6200},
    {"id": "P003", "nom": "Œufs plateau x30", "categorie": "Œufs", "prix": 3200},
    {"id": "P004", "nom": "Cuisses de poulet 1 kg", "categorie": "Volaille fraîche", "prix": 4800},
    {"id": "P005", "nom": "Poulet entier premium 1,5 kg", "categorie": "Volaille premium", "prix": 18000},
    {"id": "P006", "nom": "Ailes de poulet 1 kg", "categorie": "Volaille fraîche", "prix": 4100},
]

# Scénario de démo prioritaire : B001 (Plateau) × P005 (premium) — déficit critique
# Demande forte, stock bas → RaR ≈ 486 000 FCFA (27 × 18 000)
DEMO_OVERRIDE = {
    ("B001", "P005"): {
        "stock_base": 8,
        # moyenne journalière ~5 → demande 7j ≈ 35 (scénario cadrage)
        "ventes_base": 5.0,
        "stock_cible": 40,
        "tendance": 1.0,
        "ventes_flat": True,  # historique stable pour coller au scénario démo
    },
    ("B002", "P005"): {
        "stock_base": 55,
        "ventes_base": 2.2,
        "stock_cible": 30,
        "tendance": 0.95,
    },
    ("B003", "P001"): {
        "stock_base": 12,
        "ventes_base": 4.5,
        "stock_cible": 35,
        "tendance": 1.1,
    },
    ("B004", "P002"): {
        "stock_base": 6,
        "ventes_base": 3.8,
        "stock_cible": 28,
        "tendance": 1.08,
    },
    ("B005", "P003"): {
        "stock_base": 80,
        "ventes_base": 1.5,
        "stock_cible": 40,
        "tendance": 0.9,
    },
    ("B002", "P001"): {
        "stock_base": 18,
        "ventes_base": 5.2,
        "stock_cible": 40,
        "tendance": 1.12,
    },
    ("B003", "P005"): {
        "stock_base": 42,
        "ventes_base": 1.8,
        "stock_cible": 25,
        "tendance": 0.92,
    },
}


def generate_sales(days: int = 21, end: datetime | None = None) -> pd.DataFrame:
    end = end or datetime(2026, 8, 4)
    start = end - timedelta(days=days - 1)
    rows: list[dict] = []

    for d in range(days):
        date = start + timedelta(days=d)
        for b in BOUTIQUES:
            for p in PRODUITS:
                key = (b["id"], p["id"])
                ov = DEMO_OVERRIDE.get(key)

                if ov:
                    base_sales = ov["ventes_base"]
                    tendance = ov["tendance"]
                    # progressive stock toward demo snapshot on last day
                    progress = d / max(days - 1, 1)
                    stock = int(
                        round(
                            ov["stock_cible"] * (1 - progress)
                            + ov["stock_base"] * progress
                            + (0 if ov.get("ventes_flat") else RNG.normal(0, 1.2))
                        )
                    )
                    stock_cible = ov["stock_cible"]
                else:
                    base_sales = float(RNG.uniform(1.5, 4.5))
                    tendance = float(RNG.uniform(0.9, 1.1))
                    stock = int(RNG.integers(15, 60))
                    stock_cible = int(RNG.integers(25, 45))

                # weekend bump (désactivé pour paires démo « flat »)
                dow = date.weekday()
                if ov and ov.get("ventes_flat"):
                    weekend = 1.0
                    noise = 0.0
                else:
                    weekend = 1.25 if dow >= 5 else 1.0
                    noise = float(RNG.normal(0, 0.4))
                ventes = max(0, round(base_sales * tendance * weekend + noise, 1))

                # keep stock coherent-ish over time for non-override
                if not ov:
                    stock = max(0, stock - int(ventes * 0.3) + int(RNG.integers(0, 4)))

                rows.append(
                    {
                        "date": date.strftime("%Y-%m-%d"),
                        "boutique_id": b["id"],
                        "produit_id": p["id"],
                        "stock": max(0, stock),
                        "ventes": ventes,
                        "prix_unitaire": p["prix"],
                        "stock_cible": stock_cible,
                        "delai_reappro": int(RNG.choice([1, 2, 2, 3])),
                    }
                )

    # Force exact demo snapshot on last day for B001/P005
    last = end.strftime("%Y-%m-%d")
    df = pd.DataFrame(rows)
    mask = (
        (df["date"] == last)
        & (df["boutique_id"] == "B001")
        & (df["produit_id"] == "P005")
    )
    df.loc[mask, "stock"] = 8
    df.loc[mask, "ventes"] = 5.0
    df.loc[mask, "stock_cible"] = 40
    df.loc[mask, "prix_unitaire"] = 18000
    df.loc[mask, "delai_reappro"] = 2
    # Force entire B001/P005 history to stable 5 u/j for demo clarity
    mask_hist = (df["boutique_id"] == "B001") & (df["produit_id"] == "P005")
    df.loc[mask_hist, "ventes"] = 5.0
    df.loc[mask_hist, "prix_unitaire"] = 18000
    df.loc[mask_hist, "stock_cible"] = 40
    df.loc[mask_hist, "delai_reappro"] = 2

    # Force surplus at B002/P005 (source for reallocation)
    mask2 = (
        (df["date"] == last)
        & (df["boutique_id"] == "B002")
        & (df["produit_id"] == "P005")
    )
    df.loc[mask2, "stock"] = 55
    df.loc[mask2, "ventes"] = 2.0
    df.loc[mask2, "stock_cible"] = 30
    df.loc[mask2, "prix_unitaire"] = 18000

    return df


def generate_visibility() -> dict:
    """Données de visibilité / réputation globales (entreprise)."""
    return {
        "date_reference": "2026-08-04",
        "recherche_google_jour": 15,
        "note_avis_google": 2.5,
        "nb_avis_google": 3,
        "engagement_reseaux": 0.008,  # 0.8 %
        "visiteurs_jour": 1200,
        "taux_conversion_global": 0.015,  # 1.5 %
        "prix_moyen": 18000,
        "followers_reseaux": 2400,
        "posts_30j": 2,
        "mentions_positives_30j": 1,
        "source": "synthetique",
        "disclaimer": (
            "Indicateurs de visibilité synthétiques pour la démonstration. "
            "Ne représentent pas les données réelles de DABA."
        ),
    }


def generate_meta() -> dict:
    return {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "type": "synthetiques",
        "version": "1.0.0",
        "boutiques": BOUTIQUES,
        "produits": PRODUITS,
        "scenario_demo": {
            "prioritaire": {
                "boutique_id": "B001",
                "produit_id": "P005",
                "description": (
                    "DABA Plateau — Poulet entier premium : stock 8, "
                    "demande attendue ~35, déficit 27, RaR ~486 000 FCFA"
                ),
            },
            "source_reallocation": {
                "boutique_id": "B002",
                "produit_id": "P005",
                "description": "DABA Cocody — surplus de stock premium",
            },
        },
        "disclaimer": (
            "Jeu de données 100 % synthétique destiné à la démonstration du MVP "
            "DabaPulse. Aucune donnée opérationnelle réelle de DABA SAS n'est incluse."
        ),
    }


def main() -> None:
    df = generate_sales()
    vis = generate_visibility()
    meta = generate_meta()

    sales_path = OUT / "ventes_stocks.csv"
    df.to_csv(sales_path, index=False)

    with open(OUT / "visibilite_globale.json", "w", encoding="utf-8") as f:
        json.dump(vis, f, ensure_ascii=False, indent=2)

    with open(OUT / "meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    # reference tables
    pd.DataFrame(BOUTIQUES).to_csv(OUT / "boutiques.csv", index=False)
    pd.DataFrame(PRODUITS).to_csv(OUT / "produits.csv", index=False)

    print(f"✓ {sales_path} ({len(df)} lignes)")
    print(f"✓ {OUT / 'visibilite_globale.json'}")
    print(f"✓ {OUT / 'meta.json'}")
    print(f"Boutiques: {len(BOUTIQUES)} | Produits: {len(PRODUITS)}")
    print("Données SYNTHÉTIQUES — ne pas présenter comme données DABA réelles.")


if __name__ == "__main__":
    main()
