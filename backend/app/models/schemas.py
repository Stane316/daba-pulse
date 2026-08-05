"""Pydantic schemas for API responses."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

RiskType = Literal[
    "rupture_stock",
    "surstock",
    "demande_croissante",
    "desalignement",
    "reputation_note",
    "reputation_engagement",
    "reputation_avis",
    "reputation_visibilite",
    "reputation_conversion",
]

Severity = Literal["critique", "eleve", "modere", "faible"]
ConfidenceLevel = Literal["eleve", "moyen", "faible"]


class BoutiqueInfo(BaseModel):
    id: str
    nom: str
    ville: str
    zone: str


class ProduitInfo(BaseModel):
    id: str
    nom: str
    categorie: str
    unite: str = "unité"
    prix_unitaire: float


class Hypothese(BaseModel):
    cle: str
    libelle: str
    valeur: Any
    source: str = "configuration"


class RiskDriver(BaseModel):
    code: str
    libelle: str
    impact: str
    poids: float = Field(ge=0, le=1)


class SituationRisque(BaseModel):
    id: str
    type_risque: RiskType
    severite: Severity
    boutique: Optional[BoutiqueInfo] = None
    produit: Optional[ProduitInfo] = None
    signal: str
    horizon_jours: int = 7
    demande_attendue: Optional[float] = None
    stock_disponible: Optional[float] = None
    stock_cible: Optional[float] = None
    deficit_potentiel: Optional[float] = None
    surplus: Optional[float] = None
    prix_unitaire: Optional[float] = None
    revenue_at_risk: float
    confiance: float = Field(ge=0, le=1)
    niveau_confiance: ConfidenceLevel
    drivers: list[RiskDriver] = []
    hypotheses: list[Hypothese] = []
    priorite: int = 0
    scope: Literal["distribution", "reputation"] = "distribution"
    metriques_extra: dict[str, Any] = {}


class ExecutiveSummary(BaseModel):
    revenue_at_risk_total: float
    revenue_at_risk_distribution: float
    revenue_at_risk_reputation: float
    nb_situations_critiques: int
    nb_situations_total: int
    situations: list[SituationRisque]
    devise: str = "FCFA"
    donnees_synthetiques: bool = True
    disclaimer: str
    hypotheses_version: str
    date_analyse: str
    mini_vue: dict[str, Any] = {}


class DecisionAction(BaseModel):
    id: str
    situation_id: str
    type_action: str
    libelle: str
    description: str
    produit: Optional[ProduitInfo] = None
    boutique_destination: Optional[BoutiqueInfo] = None
    boutique_source: Optional[BoutiqueInfo] = None
    quantite: Optional[float] = None
    score_priorite: float
    confiance: float
    niveau_confiance: ConfidenceLevel
    raisons: list[str]
    revenue_at_risk_avant: float
    revenu_potentiellement_protege: float
    alternative: Optional["DecisionAction"] = None
    metriques: dict[str, Any] = {}
    scope: Literal["distribution", "reputation"] = "distribution"


class SimulationRequest(BaseModel):
    situation_id: str
    quantite: Optional[float] = None
    action_id: Optional[str] = None
    params: dict[str, Any] = {}


class SimulationMetric(BaseModel):
    cle: str
    libelle: str
    avant: Any
    apres: Any
    variation: Any
    unite: str = ""
    sens_positif: Literal["hausse", "baisse", "neutre"] = "neutre"


class SimulationResult(BaseModel):
    situation_id: str
    action_libelle: str
    quantite_simulee: Optional[float] = None
    metriques: list[SimulationMetric]
    revenue_at_risk_avant: float
    revenue_at_risk_apres: float
    revenu_potentiellement_protege: float
    disponibilite_avant: str
    disponibilite_apres: str
    hypotheses: list[Hypothese] = []
    scope: Literal["distribution", "reputation"] = "distribution"


class AIExplainRequest(BaseModel):
    situation_id: Optional[str] = None
    question: Optional[str] = None
    mode: Literal["resume", "qa"] = "resume"


class AIExplainResponse(BaseModel):
    situation: str
    facteurs: list[str]
    decision: str
    impact: str
    reponse: str
    sources: list[str]
    fallback: bool = False
    model: Optional[str] = None


class DataStatus(BaseModel):
    source: str
    type: Literal["synthetiques", "reelles"] = "synthetiques"
    nb_lignes: int
    nb_boutiques: int
    nb_produits: int
    periode_debut: str
    periode_fin: str
    charge_le: str
    valide: bool = True
    avertissements: list[str] = []


class HealthResponse(BaseModel):
    status: str
    version: str
    ai_available: bool
    data_loaded: bool


class DataPreview(BaseModel):
    columns: list[str]
    sample_rows: list[dict[str, Any]]
    nb_lignes: int
    nb_boutiques: int
    nb_produits: int
    periode_debut: str | None = None
    periode_fin: str | None = None
    source: str | None = None
    type: Literal["synthetiques", "reelles"] | None = None
    avertissements: list[str] = []


class ExportRequest(BaseModel):
    situation_id: str
    quantite: float | None = None
    format: Literal["json", "markdown"] = "json"


class UploadResult(BaseModel):
    status: DataStatus
    preview: DataPreview
    message: str