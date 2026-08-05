"""Analytics Engine — indicateurs de demande, stock, tendance."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from app.engines.data_loader import DataStore


def compute_demand_forecast(
    history: pd.DataFrame,
    horizon_jours: int = 7,
) -> dict[str, float]:
    """Estime la demande attendue sur l'horizon à partir de l'historique.

    Méthode explicite :
      moyenne_ventes_7j × facteur_tendance × horizon
    """
    if history.empty:
        return {
            "demande_attendue": 0.0,
            "moyenne_journaliere": 0.0,
            "tendance": 1.0,
            "ventes_7j": 0.0,
        }

    h = history.sort_values("date")
    recent = h.tail(7)
    older = h.tail(14).head(7) if len(h) >= 14 else recent

    moyenne = float(recent["ventes"].mean()) if len(recent) else 0.0
    moyenne_old = float(older["ventes"].mean()) if len(older) else moyenne

    if moyenne_old > 0:
        tendance = float(np.clip(moyenne / moyenne_old, 0.7, 1.5))
    else:
        tendance = 1.0

    # légère correction week-end déjà dans les données
    demande = moyenne * tendance * horizon_jours

    return {
        "demande_attendue": round(demande, 1),
        "moyenne_journaliere": round(moyenne, 2),
        "tendance": round(tendance, 3),
        "ventes_7j": round(float(recent["ventes"].sum()), 1),
    }


def analyze_pair(
    store: DataStore,
    boutique_id: str,
    produit_id: str,
    horizon_jours: int = 7,
) -> dict[str, Any]:
    """Analyse complète d'un couple boutique × produit."""
    snap = store.latest_snapshot()
    row = snap[
        (snap["boutique_id"] == boutique_id) & (snap["produit_id"] == produit_id)
    ]
    if row.empty:
        raise KeyError(f"Pas de données pour {boutique_id}/{produit_id}")

    r = row.iloc[0]
    hist = store.history(boutique_id, produit_id, days=21)
    demand = compute_demand_forecast(hist, horizon_jours)

    stock = float(r["stock"])
    stock_cible = float(r["stock_cible"])
    prix = float(r["prix_unitaire"])
    delai = int(r["delai_reappro"])

    deficit = max(0.0, demand["demande_attendue"] - stock)
    surplus = max(0.0, stock - stock_cible)
    couverture_jours = (
        stock / demand["moyenne_journaliere"]
        if demand["moyenne_journaliere"] > 0
        else 99.0
    )
    ratio_stock_cible = stock / stock_cible if stock_cible > 0 else 1.0

    return {
        "boutique_id": boutique_id,
        "produit_id": produit_id,
        "stock": stock,
        "stock_cible": stock_cible,
        "prix_unitaire": prix,
        "delai_reappro": delai,
        "deficit_potentiel": round(deficit, 1),
        "surplus": round(surplus, 1),
        "couverture_jours": round(couverture_jours, 1),
        "ratio_stock_cible": round(ratio_stock_cible, 3),
        "historique_ventes": [
            {"date": str(d.date()), "ventes": float(v), "stock": float(s)}
            for d, v, s in zip(
                hist["date"], hist["ventes"], hist["stock"], strict=False
            )
        ],
        **demand,
    }


def analyze_all(store: DataStore, horizon_jours: int = 7) -> list[dict[str, Any]]:
    snap = store.latest_snapshot()
    results = []
    for _, row in snap.iterrows():
        results.append(
            analyze_pair(
                store,
                str(row["boutique_id"]),
                str(row["produit_id"]),
                horizon_jours,
            )
        )
    return results


def mini_vue_globale(store: DataStore, analyses: list[dict[str, Any]]) -> dict[str, Any]:
    """Agrégats pour la mini-vue de l'écran Executive."""
    if not analyses:
        return {}

    total_stock = sum(a["stock"] for a in analyses)
    total_demande = sum(a["demande_attendue"] for a in analyses)
    total_deficit = sum(a["deficit_potentiel"] for a in analyses)
    nb_rupture = sum(1 for a in analyses if a["deficit_potentiel"] > 0)
    nb_surstock = sum(1 for a in analyses if a["surplus"] > 5)

    # top boutiques by demand
    by_boutique: dict[str, float] = {}
    for a in analyses:
        by_boutique[a["boutique_id"]] = by_boutique.get(a["boutique_id"], 0) + a[
            "demande_attendue"
        ]

    return {
        "stock_total": round(total_stock, 0),
        "demande_totale": round(total_demande, 0),
        "deficit_total": round(total_deficit, 0),
        "nb_paires_deficit": nb_rupture,
        "nb_paires_surstock": nb_surstock,
        "demande_par_boutique": [
            {
                "boutique_id": bid,
                "nom": store.boutique(bid).get("nom", bid),
                "demande": round(val, 1),
            }
            for bid, val in sorted(
                by_boutique.items(), key=lambda x: x[1], reverse=True
            )
        ],
        "visibilite": {
            "note_google": store.visibilite.get("note_avis_google"),
            "nb_avis": store.visibilite.get("nb_avis_google"),
            "engagement": store.visibilite.get("engagement_reseaux"),
            "visiteurs": store.visibilite.get("visiteurs_jour"),
            "conversion": store.visibilite.get("taux_conversion_global"),
        },
    }
