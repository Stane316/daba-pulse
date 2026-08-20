#!/usr/bin/env python3
"""Génère le dataset synthétique DabaPulse v2 (INCREMENT B — 20 août 2026).

Changements vs v1 :
- 5 boutiques × 16 produits × 84 jours = 6 720 lignes (+ entête = 6 721 lignes)
  — inspiré du générateur Product (`product_lead-taff`, seed 42, 6 721 lignes).
- Sortie double : CSV `ventes_stocks.csv` + base SQLite `growth_decision_os.db`
  (tables ventes / boutiques / produits / visibilite / meta).
- Scénario démo préservé à l'identique : B001×P005 stock 8, demande 7 j ≈ 35,
  déficit 27, RaR 486 000 FCFA ; source de réallocation B002×P005 (surplus).
- Nouveaux produits P007-P016 (aviculture) avec demande/stock contrôlés :
  AUCUNE situation ne doit dépasser le scénario démo (486 000) pour préserver
  la narration (B001×P005 reste la situation #1).
- Date de référence : 2026-08-19 (données "fraîches" pour la démo du 20/08).

Les données sont EXPLICITEMENT synthétiques et ne représentent PAS
les opérations réelles de DABA SAS. Reproductible : seed 42.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "sample"
OUT.mkdir(parents=True, exist_ok=True)

RNG = np.random.default_rng(42)

# ---------------------------------------------------------------------------
# Référentiels
# ---------------------------------------------------------------------------

BOUTIQUES = [
    {"id": "B001", "nom": "DABA Plateau", "ville": "Abidjan", "zone": "Centre"},
    {"id": "B002", "nom": "DABA Cocody", "ville": "Abidjan", "zone": "Est"},
    {"id": "B003", "nom": "DABA Yopougon", "ville": "Abidjan", "zone": "Ouest"},
    {"id": "B004", "nom": "DABA Bouaké", "ville": "Bouaké", "zone": "Centre-Nord"},
    {"id": "B005", "nom": "DABA San-Pédro", "ville": "San-Pédro", "zone": "Sud-Ouest"},
]

# id, nom, categorie, prix
PRODUITS = [
    {"id": "P001", "nom": "Poulet prêt à cuire 1,2 kg", "categorie": "Volaille fraîche", "prix": 4500},
    {"id": "P002", "nom": "Poulet découpé familial", "categorie": "Volaille fraîche", "prix": 6200},
    {"id": "P003", "nom": "Œufs plateau x30", "categorie": "Œufs", "prix": 3200},
    {"id": "P004", "nom": "Cuisses de poulet 1 kg", "categorie": "Volaille fraîche", "prix": 4800},
    {"id": "P005", "nom": "Poulet entier premium 1,5 kg", "categorie": "Volaille premium", "prix": 18000},
    {"id": "P006", "nom": "Ailes de poulet 1 kg", "categorie": "Volaille fraîche", "prix": 4100},
    # Nouveaux produits (INCREMENT B) — aviculture / volaille
    {"id": "P007", "nom": "Poulet fumé entier", "categorie": "Volaille transformée", "prix": 9500},
    {"id": "P008", "nom": "Gésiers de poulet 500 g", "categorie": "Volaille fraîche", "prix": 2500},
    {"id": "P009", "nom": "Foies de poulet 500 g", "categorie": "Volaille fraîche", "prix": 2800},
    {"id": "P010", "nom": "Œufs x12", "categorie": "Œufs", "prix": 1400},
    {"id": "P011", "nom": "Œufs de caille x24", "categorie": "Œufs", "prix": 2200},
    {"id": "P012", "nom": "Canard entier", "categorie": "Volaille premium", "prix": 11000},
    {"id": "P013", "nom": "Dinde entière 4 kg", "categorie": "Volaille premium", "prix": 15000},
    {"id": "P014", "nom": "Aliment volaille ponte 25 kg", "categorie": "Aliments", "prix": 12500},
    {"id": "P015", "nom": "Aliment volaille chair 25 kg", "categorie": "Aliments", "prix": 11000},
    {"id": "P016", "nom": "Poussin d'un jour", "categorie": "Élevage", "prix": 900},
]

# Demande journalière moyenne "normale" par produit (hors overrides)
VENTES_BASE = {
    "P001": 3.2, "P002": 2.6, "P003": 3.5, "P004": 2.8, "P005": 1.4, "P006": 2.4,
    "P007": 1.5, "P008": 2.5, "P009": 2.0, "P010": 4.0, "P011": 2.2, "P012": 0.8,
    "P013": 0.7, "P014": 1.2, "P015": 1.3, "P016": 6.0,
}

STOCK_CIBLE = {
    "P001": 35, "P002": 30, "P003": 38, "P004": 30, "P005": 26, "P006": 28,
    "P007": 28, "P008": 30, "P009": 28, "P010": 35, "P011": 30, "P012": 18,
    "P013": 16, "P014": 22, "P015": 22, "P016": 40,
}

# Les grandes boutiques vendent proportionnellement plus
STORE_FACTOR = {"B001": 1.15, "B002": 1.05, "B003": 1.0, "B004": 0.85, "B005": 0.7}

# ---------------------------------------------------------------------------
# Paramètres temporels
# ---------------------------------------------------------------------------

NB_JOURS = 84  # 12 semaines → 5 × 16 × 84 = 6 720 lignes (+ entête = 6 721)
REF_DATE = date(2026, 8, 19)  # données fraîches pour la démo du 20/08
DATE_DEBUT = REF_DATE - timedelta(days=NB_JOURS - 1)

# ---------------------------------------------------------------------------
# Patterns de démo (préservés de la v1)
# ---------------------------------------------------------------------------

# Scénario prioritaire : B001 (Plateau) × P005 (premium) — déficit critique.
# Demande ~5/j (plate) → 35 sur 7 j ; stock 8 → déficit 27 → RaR 486 000 FCFA.
DEMO_OVERRIDE = {
    ("B001", "P005"): {
        "stock_base": 8, "ventes_base": 5.0, "stock_cible": 40,
        "tendance": 1.0, "ventes_flat": True, "delai": 2,
    },
    # Source de réallocation : surplus de stock premium à Cocody
    ("B002", "P005"): {
        "stock_base": 55, "ventes_base": 2.2, "stock_cible": 30, "tendance": 0.95,
    },
    # Situations secondaires conservées (richesse de la démo)
    ("B003", "P001"): {"stock_base": 12, "ventes_base": 4.5, "stock_cible": 35, "tendance": 1.1},
    ("B004", "P002"): {"stock_base": 6, "ventes_base": 3.8, "stock_cible": 28, "tendance": 1.08},
    ("B005", "P003"): {"stock_base": 80, "ventes_base": 1.5, "stock_cible": 40, "tendance": 0.9},
    ("B002", "P001"): {"stock_base": 18, "ventes_base": 5.2, "stock_cible": 40, "tendance": 1.12},
    ("B003", "P005"): {"stock_base": 42, "ventes_base": 1.8, "stock_cible": 25, "tendance": 0.92},
}

# Sécurité premium : stock stable (pas de ramp) pour éviter tout déficit
# sur P005 hors scénario démo (aucune situation ne doit dépasser 486 000).
SAFETY_STOCK = {
    ("B004", "P005"): 30,
    ("B005", "P005"): 26,
}


def _demande(
    b: dict,
    p: dict,
    date_: date,
    noise: float = 0.2,
) -> float:
    """Demande journalière avec saisonnalité week-end (+25 %)."""
    base = VENTES_BASE[p["id"]] * STORE_FACTOR[b["id"]]
    weekend = 1.25 if date_.weekday() >= 5 else 1.0
    return max(0.0, round(base * weekend * (1 + float(RNG.normal(0, noise))), 1))


def generate_sales(days: int = NB_JOURS) -> pd.DataFrame:
    rows: list[dict] = []
    for i in range(days):
        date_ = DATE_DEBUT + timedelta(days=i)
        progress = i / max(days - 1, 1)
        for b in BOUTIQUES:
            for p in PRODUITS:
                key = (b["id"], p["id"])
                ov = DEMO_OVERRIDE.get(key)
                if ov:
                    if ov.get("ventes_flat"):
                        ventes = ov["ventes_base"]
                        stock = round(
                            ov["stock_cible"] * (1 - progress) + ov["stock_base"] * progress
                        )
                    else:
                        weekend = 1.25 if date_.weekday() >= 5 else 1.0
                        ventes = max(
                            0.0,
                            round(
                                ov["ventes_base"] * ov["tendance"] * weekend
                                + float(RNG.normal(0, 0.4)),
                                1,
                            ),
                        )
                        stock = round(
                            ov["stock_cible"] * (1 - progress)
                            + ov["stock_base"] * progress
                            + float(RNG.normal(0, 1.2))
                        )
                    stock_cible = ov["stock_cible"]
                    delai = ov.get("delai", int(RNG.choice([1, 2, 2, 3])))
                elif key in SAFETY_STOCK:
                    ventes = _demande(b, p, date_)
                    stock = SAFETY_STOCK[key] + int(RNG.integers(-2, 4))
                    stock_cible = STOCK_CIBLE[p["id"]]
                    delai = int(RNG.choice([1, 2, 2, 3]))
                else:
                    ventes = _demande(b, p, date_)
                    stock_cible = STOCK_CIBLE[p["id"]]
                    stock = max(0, stock_cible + int(RNG.integers(-4, 6)))
                    delai = int(RNG.choice([1, 2, 2, 3]))

                rows.append(
                    {
                        "date": date_.strftime("%Y-%m-%d"),
                        "boutique_id": b["id"],
                        "produit_id": p["id"],
                        "stock": max(0, stock),
                        "ventes": ventes,
                        "prix_unitaire": p["prix"],
                        "stock_cible": stock_cible,
                        "delai_reappro": delai,
                    }
                )

    df = pd.DataFrame(rows)

    # Force exacte du dernier jour pour les paires de démo (narration stable :
    # mêmes stocks finaux que la v1 → mêmes quantités recommandées).
    for (bid, pid), ov in DEMO_OVERRIDE.items():
        mask = (
            (df["date"] == REF_DATE.isoformat())
            & (df["boutique_id"] == bid)
            & (df["produit_id"] == pid)
        )
        df.loc[mask, "stock"] = ov["stock_base"]
        df.loc[mask, "stock_cible"] = ov["stock_cible"]
        if ov.get("ventes_flat"):
            df.loc[mask, "ventes"] = ov["ventes_base"]

    return df


def generate_visibility() -> dict:
    """Données de visibilité / réputation globales (entreprise)."""
    return {
        "date_reference": REF_DATE.isoformat(),
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
        "version": "2.0.0",
        "nb_lignes": NB_JOURS * len(BOUTIQUES) * len(PRODUITS),
        "nb_jours": NB_JOURS,
        "format": {
            "csv": "ventes_stocks.csv (6 721 lignes avec entête)",
            "sqlite": "growth_decision_os.db (tables ventes/boutiques/produits/visibilite/meta)",
        },
        "seed": 42,
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


def write_sqlite(
    df: pd.DataFrame,
    vis: dict,
    meta: dict,
    db_path: Path = OUT / "growth_decision_os.db",
) -> Path:
    """Écrit la base SQLite du dataset (tables ventes/boutiques/produits/visibilite/meta)."""
    if db_path.exists():
        db_path.unlink()
    con = sqlite3.connect(db_path)
    try:
        con.execute("CREATE TABLE boutiques (id TEXT PRIMARY KEY, nom TEXT, ville TEXT, zone TEXT)")
        con.executemany(
            "INSERT INTO boutiques VALUES (?, ?, ?, ?)",
            [(b["id"], b["nom"], b["ville"], b["zone"]) for b in BOUTIQUES],
        )
        con.execute(
            "CREATE TABLE produits (id TEXT PRIMARY KEY, nom TEXT, categorie TEXT, prix REAL)"
        )
        con.executemany(
            "INSERT INTO produits VALUES (?, ?, ?, ?)",
            [(p["id"], p["nom"], p["categorie"], p["prix"]) for p in PRODUITS],
        )
        con.execute(
            "CREATE TABLE ventes ("
            "date TEXT NOT NULL, boutique_id TEXT NOT NULL, produit_id TEXT NOT NULL, "
            "stock REAL NOT NULL, ventes REAL NOT NULL, prix_unitaire REAL NOT NULL, "
            "stock_cible REAL NOT NULL, delai_reappro INTEGER NOT NULL)"
        )
        con.executemany(
            "INSERT INTO ventes VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (
                    r["date"], r["boutique_id"], r["produit_id"],
                    float(r["stock"]), float(r["ventes"]), float(r["prix_unitaire"]),
                    float(r["stock_cible"]), int(r["delai_reappro"]),
                )
                for r in df.to_dict("records")
            ],
        )
        con.execute(
            "CREATE INDEX idx_ventes_pair ON ventes (boutique_id, produit_id, date)"
        )
        con.execute("CREATE TABLE visibilite (cle TEXT PRIMARY KEY, valeur TEXT)")
        con.executemany(
            "INSERT INTO visibilite VALUES (?, ?)",
            [(k, json.dumps(v, ensure_ascii=False)) for k, v in vis.items()],
        )
        con.execute("CREATE TABLE meta (cle TEXT PRIMARY KEY, valeur TEXT)")
        con.executemany(
            "INSERT INTO meta VALUES (?, ?)",
            [(k, json.dumps(v, ensure_ascii=False)) for k, v in meta.items()],
        )
        con.commit()
    finally:
        con.close()
    return db_path


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

    pd.DataFrame(BOUTIQUES).to_csv(OUT / "boutiques.csv", index=False)
    pd.DataFrame(PRODUITS).to_csv(OUT / "produits.csv", index=False)

    db_path = write_sqlite(df, vis, meta)

    n_lines = sales_path.read_text(encoding="utf-8").count("\n")
    print(f"✓ {sales_path} ({len(df)} lignes + entête = {n_lines} lignes)")
    print(f"✓ {db_path} (tables ventes/boutiques/produits/visibilite/meta)")
    print(f"✓ {OUT / 'visibilite_globale.json'}")
    print(f"✓ {OUT / 'meta.json'}")
    print(
        f"Boutiques: {len(BOUTIQUES)} | Produits: {len(PRODUITS)} | "
        f"Jours: {NB_JOURS} | Période: {DATE_DEBUT} → {REF_DATE}"
    )
    print("Données SYNTHÉTIQUES — ne pas présenter comme données DABA réelles.")


if __name__ == "__main__":
    main()
