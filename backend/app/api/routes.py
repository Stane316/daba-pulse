"""API routes DabaPulse."""

from __future__ import annotations

import json

from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from fastapi.responses import PlainTextResponse, Response

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
    DataPreview,
    DataStatus,
    DecisionAction,
    ExecutiveSummary,
    ExportRequest,
    HealthResponse,
    SimulationRequest,
    SimulationResult,
    SituationRisque,
    UploadResult,
)
from app.services.csv_import import CsvValidationError, parse_ventes_csv
from app.services.export_summary import build_decision_summary

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
    """Recharge le jeu synthétique de démonstration — idempotent, jamais 500 si déjà chargé en fallback."""
    try:
        status = store.load()
        # Garde-fous : si le load échoue mais que le store était déjà chargé, on garde l'ancien
        if not status.valide:
            raise HTTPException(status_code=500, detail="Rechargement échoué: dataset invalide.")
        return status
    except HTTPException:
        raise
    except Exception as exc:
        # Si le store a encore des données, on les sert plutôt que de casser la démo
        if store.is_loaded:
            s = store.status()
            s.avertissements = [*s.avertissements, f"Rechargement partiel: {exc}"]
            return s
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/data/preview", response_model=DataPreview)
def data_preview(n: int = Query(default=5, ge=1, le=50)) -> DataPreview:
    _ensure_data()
    preview = store.preview(n=n)
    status = store.status()
    return DataPreview(
        **preview,
        source=status.source,
        type=status.type,
        avertissements=status.avertissements,
    )


@router.post("/data/upload", response_model=UploadResult)
async def data_upload(
    file: UploadFile = File(..., description="CSV ventes/stocks"),
) -> UploadResult:
    """Import d'un CSV utilisateur (colonnes MVP obligatoires)."""
    filename = file.filename or "upload.csv"
    if not filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Le fichier doit être un CSV (.csv).",
                "filename": filename,
            },
        )

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail={"message": "Fichier vide."})
    # Garde-fous taille (5 MB) — évite OOM Render + feedback jury clair
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail={
                "message": f"Fichier trop volumineux ({len(content)//1024} Ko). Limite 5120 Ko.",
                "filename": filename,
                "taille_bytes": len(content),
            },
        )

    if not store.is_loaded:
        try:
            store.load()
        except Exception:
            pass

    try:
        df, warnings = parse_ventes_csv(content)
    except CsvValidationError as exc:
        raise HTTPException(
            status_code=400,
            detail={"message": str(exc), **exc.details},
        ) from exc

    status = store.load_ventes_dataframe(
        df,
        source_label=f"upload:{filename}",
        extra_warnings=warnings,
        data_type="synthetiques",
    )
    preview = store.preview(n=5)
    return UploadResult(
        status=status,
        preview=DataPreview(
            **preview,
            source=status.source,
            type=status.type,
            avertissements=status.avertissements,
        ),
        message=(
            f"Import réussi : {status.nb_lignes} lignes, "
            f"{status.nb_boutiques} boutiques, {status.nb_produits} produits. "
            "Les moteurs vont recalculer sur ces données."
        ),
    )


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


@router.post("/export/decision")
def export_decision_post(body: ExportRequest) -> Response:
    """Export résumé décisionnel (JSON ou Markdown)."""
    return _export_decision(body.situation_id, body.quantite, body.format)


@router.get("/export/decision/{situation_id}")
def export_decision_get(
    situation_id: str,
    quantite: float | None = None,
    format: str = Query(default="json", pattern="^(json|markdown)$"),
) -> Response:
    return _export_decision(situation_id, quantite, format)


def _export_decision(
    situation_id: str,
    quantite: float | None,
    fmt: str,
) -> Response:
    _ensure_data()
    try:
        result = build_decision_summary(
            store,
            situation_id,
            quantite=quantite,
            format=fmt if fmt in ("json", "markdown") else "json",  # type: ignore[arg-type]
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Situation introuvable") from exc

    safe_id = situation_id.replace("/", "-")
    if fmt == "markdown":
        assert isinstance(result, str)
        return PlainTextResponse(
            content=result,
            media_type="text/markdown; charset=utf-8",
            headers={
                "Content-Disposition": (
                    f'attachment; filename="dabapulse-decision-{safe_id}.md"'
                )
            },
        )

    assert isinstance(result, dict)
    body = json.dumps(result, ensure_ascii=False, indent=2)
    return Response(
        content=body,
        media_type="application/json; charset=utf-8",
        headers={
            "Content-Disposition": (
                f'attachment; filename="dabapulse-decision-{safe_id}.json"'
            )
        },
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

