"""Chargement et validation des données synthétiques.

INCREMENT B — support de la base SQLite `growth_decision_os.db` :
- `load()` préfère la base SQLite si présente dans data_path (sinon CSV) ;
- `charger_etat_depuis_sqlite(path)` charge un état PUR (dict) sans toucher
  au singleton — le Risk Engine peut alors évaluer sans état global ;
- `DataStore.from_state(etat)` reconstruit un store depuis un état pur.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from app.core.config import get_settings
from app.models.schemas import DataStatus

_CSV_REQUIRED = [
    "date",
    "boutique_id",
    "produit_id",
    "stock",
    "ventes",
    "prix_unitaire",
    "stock_cible",
    "delai_reappro",
]


class DataStore:
    """In-memory data store loaded from CSV / JSON sample files (ou SQLite)."""

    def __init__(self) -> None:
        self.ventes: pd.DataFrame = pd.DataFrame()
        self.boutiques: dict[str, dict[str, Any]] = {}
        self.produits: dict[str, dict[str, Any]] = {}
        self.visibilite: dict[str, Any] = {}
        self.meta: dict[str, Any] = {}
        self.loaded_at: str | None = None
        self.warnings: list[str] = []
        self._source_label: str = "aucune"
        self._data_type: str = "synthetiques"

    @classmethod
    def from_state(cls, etat: dict[str, Any]) -> "DataStore":
        """Reconstruit un store depuis un état PUR (dict) — aucun accès disque."""
        s = cls()
        s.ventes = etat.get("ventes", pd.DataFrame()).copy()
        s.boutiques = dict(etat.get("boutiques", {}))
        s.produits = dict(etat.get("produits", {}))
        s.visibilite = dict(etat.get("visibilite", {}))
        s.meta = dict(etat.get("meta", {}))
        s._source_label = str(etat.get("_source_label", "etat"))
        s._data_type = str(etat.get("_data_type", "synthetiques"))
        s.warnings = list(etat.get("_warnings", []))
        s.loaded_at = datetime.utcnow().isoformat() + "Z"
        return s

    @property
    def is_loaded(self) -> bool:
        return not self.ventes.empty

    def load(self, data_path: str | Path | None = None) -> DataStatus:
        path = Path(data_path or get_settings().data_path)
        db_file = path / "growth_decision_os.db"
        if db_file.exists():
            return self.load_from_sqlite(path)
        return self.load_from_csv(path)

    # ------------------------------------------------------------------
    # Chargement CSV (voie historique — conservée)
    # ------------------------------------------------------------------

    def load_from_csv(self, path: Path) -> DataStatus:
        self.warnings = []
        self._source_label = str(path)
        self._data_type = "synthetiques"

        ventes_file = path / "ventes_stocks.csv"
        if not ventes_file.exists():
            raise FileNotFoundError(
                f"Dataset introuvable: {ventes_file}. "
                "Exécutez scripts/generate_synthetic_data.py"
            )

        df = pd.read_csv(ventes_file)
        df, warns = self._ingest_ventes(df)
        self.warnings.extend(warns)

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
        self._rebuild_refs_from_ventes()

        return self.status()

    # ------------------------------------------------------------------
    # Chargement SQLite (INCREMENT B — voie préférée quand la base existe)
    # ------------------------------------------------------------------

    def load_from_sqlite(self, path: str | Path | None = None) -> DataStatus:
        """Charge le dataset depuis `growth_decision_os.db` (ou db_path config)."""
        settings = get_settings()
        db_file = Path(
            settings.sqlite_db
            if path is None
            else Path(path) / "growth_decision_os.db"
        )
        self.warnings = []
        self._source_label = f"sqlite:{db_file.name}"
        self._data_type = "synthetiques"

        if not db_file.exists():
            raise FileNotFoundError(
                f"Base SQLite introuvable: {db_file}. "
                "Exécutez scripts/generate_synthetic_data.py"
            )

        con = sqlite3.connect(db_file)
        try:
            df = pd.read_sql_query("SELECT * FROM ventes", con)
            self.boutiques = {
                str(r["id"]): r.to_dict() for _, r in pd.read_sql_query(
                    "SELECT * FROM boutiques", con
                ).iterrows()
            }
            self.produits = {
                str(r["id"]): r.to_dict() for _, r in pd.read_sql_query(
                    "SELECT * FROM produits", con
                ).iterrows()
            }
            self.visibilite = self._read_kv_table(con, "visibilite")
            self.meta = self._read_kv_table(con, "meta")
        finally:
            con.close()

        df, warns = self._ingest_ventes(df)
        self.warnings.extend(warns)
        self.ventes = df.sort_values("date")
        self.loaded_at = datetime.utcnow().isoformat() + "Z"
        self._rebuild_refs_from_ventes()

        return self.status()

    @staticmethod
    def _read_kv_table(con: sqlite3.Connection, table: str) -> dict[str, Any]:
        """Lit une table (cle, valeur JSON) → dict Python."""
        out: dict[str, Any] = {}
        for cle, valeur in con.execute(f"SELECT cle, valeur FROM {table}"):
            try:
                out[cle] = json.loads(valeur)
            except (json.JSONDecodeError, TypeError):
                out[cle] = valeur
        return out

    @staticmethod
    def _ingest_ventes(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
        """Validation + coercition commune CSV / SQLite (pure)."""
        missing = [c for c in _CSV_REQUIRED if c not in df.columns]
        if missing:
            raise ValueError(f"Colonnes manquantes: {missing}")

        df = df.copy()
        df["date"] = pd.to_datetime(df["date"])
        for col in ["stock", "ventes", "prix_unitaire", "stock_cible", "delai_reappro"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        warnings: list[str] = []
        if df[_CSV_REQUIRED[3:]].isna().any().any():
            warnings.append("Valeurs manquantes détectées et interpolées à 0.")
            df = df.fillna(0)

        return df, warnings

    def load_ventes_dataframe(
        self,
        df: pd.DataFrame,
        *,
        source_label: str = "upload.csv",
        extra_warnings: list[str] | None = None,
        data_type: str = "synthetiques",
    ) -> DataStatus:
        """Charge un dataframe ventes déjà validé (import utilisateur)."""
        self.warnings = list(extra_warnings or [])
        self._source_label = source_label
        self._data_type = data_type
        self.ventes = df.sort_values("date").copy()
        self.loaded_at = datetime.utcnow().isoformat() + "Z"
        self._rebuild_refs_from_ventes()
        if not self.visibilite:
            self.visibilite = {
                "date_reference": str(self.ventes["date"].max().date()),
                "recherche_google_jour": 15,
                "note_avis_google": 2.5,
                "nb_avis_google": 3,
                "engagement_reseaux": 0.008,
                "visiteurs_jour": 1200,
                "taux_conversion_global": 0.015,
                "prix_moyen": float(self.ventes["prix_unitaire"].mean()),
                "source": "synthetique_default",
            }
        if not self.meta:
            self.meta = {
                "type": data_type,
                "source": source_label,
                "disclaimer": "Données importées — vérifier la nature synthétique/réelle.",
            }
        return self.status()

    def _rebuild_refs_from_ventes(self) -> None:
        """Met à jour boutiques/produits minimaux à partir des ventes."""
        if self.ventes.empty:
            return
        for bid in self.ventes["boutique_id"].unique():
            bid_s = str(bid)
            if bid_s not in self.boutiques:
                self.boutiques[bid_s] = {
                    "id": bid_s,
                    "nom": bid_s,
                    "ville": "—",
                    "zone": "—",
                }
        for pid in self.ventes["produit_id"].unique():
            pid_s = str(pid)
            if pid_s not in self.produits:
                prix = float(
                    self.ventes.loc[
                        self.ventes["produit_id"] == pid, "prix_unitaire"
                    ].iloc[-1]
                )
                self.produits[pid_s] = {
                    "id": pid_s,
                    "nom": pid_s,
                    "categorie": "import",
                    "prix": prix,
                }

    def preview(self, n: int = 5) -> dict[str, Any]:
        from app.services.csv_import import dataframe_preview

        if self.ventes.empty:
            return dataframe_preview(pd.DataFrame(), n=n)
        return dataframe_preview(self.ventes, n=n)

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

        data_type = getattr(self, "_data_type", "synthetiques")
        source = getattr(self, "_source_label", str(get_settings().data_path))
        base_warnings = list(self.warnings)
        if data_type == "synthetiques":
            base_warnings = base_warnings + [
                "Données synthétiques — ne pas présenter comme données réelles DABA."
            ]

        return DataStatus(
            source=source,
            type=data_type,  # type: ignore[arg-type]
            nb_lignes=len(self.ventes),
            nb_boutiques=int(self.ventes["boutique_id"].nunique()),
            nb_produits=int(self.ventes["produit_id"].nunique()),
            periode_debut=str(self.ventes["date"].min().date()),
            periode_fin=str(self.ventes["date"].max().date()),
            charge_le=self.loaded_at or "",
            valide=True,
            avertissements=base_warnings,
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
        return self.boutiques.get(
            bid, {"id": bid, "nom": bid, "ville": "?", "zone": "?"}
        )

    def produit(self, pid: str) -> dict[str, Any]:
        return self.produits.get(
            pid, {"id": pid, "nom": pid, "categorie": "?", "prix": 0}
        )


def charger_etat_depuis_sqlite(path: str | Path | None = None) -> dict[str, Any]:
    """Charge un état PUR (dict) depuis la base SQLite — aucun singleton touché.

    Port de l'idée Product (`risk_engine.charger_etat_depuis_sqlite`) :
    séparation stricte entre le chargement (impur) et le calcul (pur).
    """
    settings = get_settings()
    db_file = Path(
        settings.sqlite_db if path is None else Path(path) / "growth_decision_os.db"
    )
    if not db_file.exists():
        raise FileNotFoundError(f"Base SQLite introuvable: {db_file}")

    con = sqlite3.connect(db_file)
    try:
        ventes = pd.read_sql_query("SELECT * FROM ventes", con)
        ventes, warns = DataStore._ingest_ventes(ventes)
        boutiques = {
            str(r["id"]): r.to_dict()
            for _, r in pd.read_sql_query("SELECT * FROM boutiques", con).iterrows()
        }
        produits = {
            str(r["id"]): r.to_dict()
            for _, r in pd.read_sql_query("SELECT * FROM produits", con).iterrows()
        }
        visibilite = DataStore._read_kv_table(con, "visibilite")
        meta = DataStore._read_kv_table(con, "meta")
    finally:
        con.close()

    return {
        "ventes": ventes,
        "boutiques": boutiques,
        "produits": produits,
        "visibilite": visibilite,
        "meta": meta,
        "_source_label": f"sqlite:{db_file.name}",
        "_data_type": "synthetiques",
        "_warnings": warns,
    }


# Singleton
store = DataStore()
