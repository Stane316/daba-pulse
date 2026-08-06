"""Application configuration and calculation hypotheses (versioned)."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

HYPOTHESES = {
    "version": "1.0.0",
    "horizon_jours": 7,
    "demande_methode": "moyenne_ventes_7j × facteur_tendance × facteur_saison",
    "deficit_formule": "max(0, demande_attendue - stock_disponible)",
    "rar_distribution_formule": "deficit_potentiel × prix_unitaire_net",
    "rar_reputation_formule": "visiteurs × taux_conversion × prix_moyen × facteur_risque",
    "facteurs_risque_reputation": {
        "note_google_lt_3_5": 0.20,
        "engagement_lt_1pct": 0.10,
        "absence_avis": 0.15,
        "faible_visibilite": 0.10,
    },
    "seuil_note_google_critique": 3.5,
    "seuil_engagement_faible": 0.01,
    "seuil_conversion_faible": 0.02,
    "seuil_visibilite_faible": 30,
    "seuil_rupture_stock_ratio": 0.4,
    "seuil_surstock_ratio": 1.8,
    "confiance_base": 0.72,
    "devise": "FCFA",
    "donnees_type": "synthetiques",
    "disclaimer": (
        "Les chiffres présentés sont des estimations illustratives fondées sur "
        "des données synthétiques. Ils ne constituent pas des données réelles de DABA "
        "ni des prédictions financières certaines."
    ),
}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: str = "*"
    data_path: str = str(Path(__file__).resolve().parents[3] / "data" / "sample")
    api_json_logs: bool = False

    openai_api_key: str = ""
    openai_base_url: str = "https://openrouter.ai/api/v1"
    openai_model: str = "openai/gpt-4o-mini"
    ai_enabled: bool = True

    @property
    def origins(self) -> list[str]:
        raw = self.cors_origins.strip()
        if raw == "*":
            return ["*"]
        return [o.strip() for o in raw.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
