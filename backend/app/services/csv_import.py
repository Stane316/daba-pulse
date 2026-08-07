"""Import et validation CSV pour le pipeline Data Foundation."""

from __future__ import annotations

import io
from typing import Any

import pandas as pd

REQUIRED_VENTES_COLUMNS = [
    "date",
    "boutique_id",
    "produit_id",
    "stock",
    "ventes",
    "prix_unitaire",
    "stock_cible",
    "delai_reappro",
]


class CsvValidationError(ValueError):
    """Erreur de validation CSV avec détails structurés."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.details = details or {}


MAX_CSV_BYTES = 5 * 1024 * 1024  # 5 MB — garde-fous démo (Render free tier)


def parse_ventes_csv(content: bytes | str) -> tuple[pd.DataFrame, list[str]]:
    """Parse et valide un CSV ventes/stocks."""
    warnings: list[str] = []
    # Garde-fous taille (évite OOM sur Render)
    if isinstance(content, bytes) and len(content) > MAX_CSV_BYTES:
        raise CsvValidationError(
            f"Fichier trop volumineux ({len(content) // 1024} Ko). Limite {MAX_CSV_BYTES // 1024} Ko.",
            {"nb_lignes": 0, "taille_bytes": len(content)},
        )
    try:
        if isinstance(content, bytes):
            text = content.decode("utf-8-sig")
        else:
            text = content
        if not text.strip():
            raise CsvValidationError("Le fichier CSV est vide.", {"nb_lignes": 0})
        df = pd.read_csv(io.StringIO(text))
    except UnicodeDecodeError as exc:
        raise CsvValidationError(
            "Encodage invalide. Utilisez UTF-8.",
            {"error": str(exc)},
        ) from exc
    except Exception as exc:
        raise CsvValidationError(
            f"CSV illisible: {exc}",
            {"error": str(exc)},
        ) from exc

    if df.empty:
        raise CsvValidationError("Le fichier CSV est vide.", {"nb_lignes": 0})

    df.columns = [str(c).strip() for c in df.columns]
    missing = [c for c in REQUIRED_VENTES_COLUMNS if c not in df.columns]
    if missing:
        raise CsvValidationError(
            "Colonnes obligatoires manquantes.",
            {
                "missing_columns": missing,
                "received_columns": list(df.columns),
                "required_columns": REQUIRED_VENTES_COLUMNS,
            },
        )

    df = df[REQUIRED_VENTES_COLUMNS].copy()
    try:
        df["date"] = pd.to_datetime(df["date"], errors="raise")
    except Exception as exc:
        raise CsvValidationError(
            "Colonne date invalide. Format attendu: YYYY-MM-DD.",
            {"error": str(exc)},
        ) from exc

    for col in ["stock", "ventes", "prix_unitaire", "stock_cible", "delai_reappro"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    null_counts = df[REQUIRED_VENTES_COLUMNS[3:]].isna().sum()
    if null_counts.any():
        warnings.append(
            "Valeurs non numériques détectées et remplacées par 0: "
            + ", ".join(
                f"{c}={int(null_counts[c])}"
                for c in null_counts.index
                if null_counts[c] > 0
            )
        )
        df = df.fillna(0)

    if (df["stock"] < 0).any() or (df["ventes"] < 0).any():
        warnings.append("Valeurs négatives détectées (conservées pour traçabilité).")

    if df["boutique_id"].nunique() < 1 or df["produit_id"].nunique() < 1:
        raise CsvValidationError(
            "Au moins une boutique et un produit sont requis.",
            {
                "nb_boutiques": int(df["boutique_id"].nunique()),
                "nb_produits": int(df["produit_id"].nunique()),
            },
        )

    df = df.sort_values("date")
    warnings.append(
        "Import utilisateur — vérifier que les données ne sont pas présentées "
        "comme données opérationnelles DABA non validées."
    )
    return df, warnings


def dataframe_preview(df: pd.DataFrame, n: int = 5) -> dict[str, Any]:
    """Aperçu JSON-serializable d'un dataframe ventes."""
    if df.empty:
        return {
            "columns": REQUIRED_VENTES_COLUMNS,
            "sample_rows": [],
            "nb_lignes": 0,
            "nb_boutiques": 0,
            "nb_produits": 0,
        }

    sample = df.head(n).copy()
    sample["date"] = sample["date"].dt.strftime("%Y-%m-%d")
    rows = sample.to_dict(orient="records")
    return {
        "columns": list(df.columns),
        "sample_rows": rows,
        "nb_lignes": int(len(df)),
        "nb_boutiques": int(df["boutique_id"].nunique()),
        "nb_produits": int(df["produit_id"].nunique()),
        "periode_debut": str(df["date"].min().date()),
        "periode_fin": str(df["date"].max().date()),
    }
