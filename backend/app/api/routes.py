"""API routes DabaPulse."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app import __version__
from app.core.config import HYPOTHESES, get_settings
from app.engines.ai_layer import explain
from app.engines.data_loader import store
from app.engines.decision_engine import get_decision, get_top_decisions
from app.engines.risk_engine import build_executive_summary, get_situation
from app.engines.simulator import simulate
from app.models.schemas import (
    AIExplainRequest,
    AIExplainResponse,
    DataStatus,
    DecisionAction,
    ExecutiveSummary,
    HealthResponse,
    SimulationRequest,
    SimulationResult,
    SituationRisque,
)

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        status="ok",
        version=__version__,
        ai_available=bool(settings.ai_enabled and settings.openai_api_key),
        data_loaded=store.is_loaded,
    )


@router.get("/data/status", response_model=DataStatus)
def data_status() -> DataStatus:
    if not store.is_loaded:
        try:
            return store.load()
        except Exception as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
    return store.status()


@router.post("/data/reload", response_model=DataStatus)
def data_reload() -> DataStatus:
    try:
        return store.load()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/executive", response_model=ExecutiveSummary)
def executive() -> ExecutiveSummary:
    _ensure_data()
    return build_executive_summary(store)


@router.get("/situations", response_model=list[SituationRisque])
def list_situations(
    scope: str | None = Query(default=None, pattern="^(distribution|reputation)$"),
    severite: str | None = None,
) -> list[SituationRisque]:
    _ensure_data()
    summary = build_executive_summary(store)
    items = summary.situations
    if scope:
        items = [s for s in items if s.scope == scope]
    if severite:
        items = [s for s in items if s.severite == severite]
    return items


@router.get("/situations/{situation_id}", response_model=SituationRisque)
def situation_detail(situation_id: str) -> SituationRisque:
    _ensure_data()
    sit = get_situation(store, situation_id)
    if not sit:
        raise HTTPException(status_code=404, detail="Situation introuvable")
    return sit


@router.get("/decisions", response_model=list[DecisionAction])
def list_decisions(limit: int = Query(default=5, ge=1, le=20)) -> list[DecisionAction]:
    _ensure_data()
    return get_top_decisions(store, limit=limit)


@router.get("/decisions/{situation_id}", response_model=DecisionAction)
def decision_for_situation(situation_id: str) -> DecisionAction:
    _ensure_data()
    dec = get_decision(store, situation_id)
    if not dec:
        raise HTTPException(status_code=404, detail="Décision introuvable")
    return dec


@router.post("/simulate", response_model=SimulationResult)
def run_simulation(body: SimulationRequest) -> SimulationResult:
    _ensure_data()
    result = simulate(
        store,
        body.situation_id,
        quantite=body.quantite,
        params=body.params,
    )
    if not result:
        raise HTTPException(status_code=404, detail="Situation introuvable")
    return result


@router.get("/simulate/{situation_id}", response_model=SimulationResult)
def run_simulation_get(
    situation_id: str,
    quantite: float | None = None,
) -> SimulationResult:
    _ensure_data()
    result = simulate(store, situation_id, quantite=quantite)
    if not result:
        raise HTTPException(status_code=404, detail="Situation introuvable")
    return result


@router.post("/ai/explain", response_model=AIExplainResponse)
async def ai_explain(body: AIExplainRequest) -> AIExplainResponse:
    _ensure_data()
    return await explain(
        store,
        situation_id=body.situation_id,
        question=body.question,
        mode=body.mode,
    )


@router.get("/ai/explain/{situation_id}", response_model=AIExplainResponse)
async def ai_explain_get(
    situation_id: str,
    question: str | None = None,
) -> AIExplainResponse:
    _ensure_data()
    return await explain(
        store,
        situation_id=situation_id,
        question=question,
        mode="qa" if question else "resume",
    )


@router.get("/hypotheses")
def hypotheses() -> dict:
    return HYPOTHESES


@router.get("/meta")
def meta() -> dict:
    _ensure_data()
    return {
        "meta": store.meta,
        "visibilite": store.visibilite,
        "boutiques": list(store.boutiques.values()),
        "produits": list(store.produits.values()),
        "data": store.status().model_dump(),
    }


def _ensure_data() -> None:
    if not store.is_loaded:
        try:
            store.load()
        except Exception as exc:
            raise HTTPException(
                status_code=503,
                detail=f"Données indisponibles: {exc}",
            ) from exc
