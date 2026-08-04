"""Chargement et validation des données synthétiques."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from app.core.config import get_settings
from app.models.schemas import DataStatus


class DataStore:
    """In-memory data store loaded from CSV / JSON sample files."""

    def __init__(self) -> None:
        self.ventes: pd.DataFrame = pd.DataFrame()
        self.boutiques: dict[str, dict[str, Any]] = {}
        self.produits: dict[str, dict[str, Any]] = {}
        self.visibilite: dict[str, Any] = {}
        self.meta: dict[str, Any] = {}
        self.loaded_at: str | None = None
        self.warnings: list[str] = []

    @property
    def is_loaded(self) -> bool:
        return not self.ventes.empty

    def load(self, data_path: str | Path | None = None) -> DataStatus:
        path = Path(data_path or get_settings().data_path)
        self.warnings = []

        ventes_file = path / "ventes_stocks.csv"
        if not ventes_file.exists():
            raise FileNotFoundError(
                f"Dataset introuvable: {ventes_file}. "
                "Exécutez scripts/generate_synthetic_data.py"
            )

        df = pd.read_csv(ventes_file)
        required = [
            "date",
            "boutique_id",
            "produit_id",
            "stock",
            "ventes",
            "prix_unitaire",
            "stock_cible",
            "delai_reappro",
        ]
        missing = [c for c in required if c not in df.columns]
        if missing:
            raise ValueError(f"Colonnes manquantes: {missing}")

        df["date"] = pd.to_datetime(df["date"])
        for col in ["stock", "ventes", "prix_unitaire", "stock_cible", "delai_reappro"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        if df[required[3:]].isna().any().any():
            self.warnings.append("Valeurs manquantes détectées et interpolées à 0.")
            df = df.fillna(0)

        self.ventes = df.sort_values("date")

        boutiques_df = pd.read_csv(path / "boutiques.csv")
        self.boutiques = {r["id"]: r.to_dict() for _, r in boutiques_df.iterrows()}

        produits_df = pd.read_csv(path / "produits.csv")
        self.produits = {r["id"]: r.to_dict() for _, r in produits_df.iterrows()}

        with open(path / "visibilite_globale.json", encoding="utf-8") as f:
            self.visibilite = json.load(f)

        with open(path / "meta.json", encoding="utf-8") as f:
            self.meta = json.load(f)

        self.loaded_at = datetime.utcnow().isoformat() + "Z"

        return self.status()

    def status(self) -> DataStatus:
        if self.ventes.empty:
            return DataStatus(
                source="aucune",
                type="synthetiques",
                nb_lignes=0,
                nb_boutiques=0,
                nb_produits=0,
                periode_debut="",
                periode_fin="",
                charge_le="",
                valide=False,
                avertissements=["Aucune donnée chargée"],
            )

        return DataStatus(
            source=str(get_settings().data_path),
            type="synthetiques",
            nb_lignes=len(self.ventes),
            nb_boutiques=self.ventes["boutique_id"].nunique(),
            nb_produits=self.ventes["produit_id"].nunique(),
            periode_debut=str(self.ventes["date"].min().date()),
            periode_fin=str(self.ventes["date"].max().date()),
            charge_le=self.loaded_at or "",
            valide=True,
            avertissements=self.warnings
            + [
                "Données synthétiques — ne pas présenter comme données réelles DABA."
            ],
        )

    def latest_snapshot(self) -> pd.DataFrame:
        """Dernier état stock par boutique × produit."""
        if self.ventes.empty:
            return pd.DataFrame()
        last_date = self.ventes["date"].max()
        return self.ventes[self.ventes["date"] == last_date].copy()

    def history(self, boutique_id: str, produit_id: str, days: int = 14) -> pd.DataFrame:
        df = self.ventes[
            (self.ventes["boutique_id"] == boutique_id)
            & (self.ventes["produit_id"] == produit_id)
        ].copy()
        return df.sort_values("date").tail(days)

    def boutique(self, bid: str) -> dict[str, Any]:
        return self.boutiques.get(bid, {"id": bid, "nom": bid, "ville": "?", "zone": "?"})

    def produit(self, pid: str) -> dict[str, Any]:
        return self.produits.get(
            pid, {"id": pid, "nom": pid, "categorie": "?", "prix": 0}
        )


# Singleton
store = DataStore()
