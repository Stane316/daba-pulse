"""DabaPulse FastAPI application."""

from __future__ import annotations

import logging
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app import __version__
from app.api.routes import router
from app.core.config import get_settings
from app.engines.data_loader import store

logger = logging.getLogger("dabapulse.api")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings = get_settings()
    data_path = Path(settings.data_path)
    if not data_path.exists():
        alt = Path(__file__).resolve().parents[2] / "data" / "sample"
        if alt.exists():
            # mutate cached settings path for this process
            object.__setattr__(settings, "data_path", str(alt))
            data_path = alt
    try:
        store.load(str(data_path))
        print(f"[DabaPulse] Data loaded from {data_path}")
    except Exception as exc:
        print(f"[DabaPulse] WARNING: could not load data: {exc}")
    yield


app = FastAPI(
    title="DabaPulse API",
    description=(
        "Revenue-at-Risk Decision Engine — Smart Distribution MVP. "
        "Données synthétiques pour démonstration."
    ),
    version=__version__,
    lifespan=lifespan,
)

settings = get_settings()

# CORS: if credentials + specific origins, avoid allow_origins=["*"]
_origins = settings.origins
_allow_credentials = _origins != ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    """Attach request id + optional structured timing logs (EL-06)."""
    request_id = request.headers.get("x-request-id") or str(uuid.uuid4())[:8]
    start = time.perf_counter()
    response = None
    try:
        response = await call_next(request)
        return response
    finally:
        duration_ms = (time.perf_counter() - start) * 1000
        status = getattr(response, "status_code", 500)
        if response is not None:
            response.headers["X-Request-Id"] = request_id
        if settings.api_json_logs:
            logger.info(
                "request method=%s path=%s status=%s duration_ms=%.1f request_id=%s",
                request.method,
                request.url.path,
                status,
                duration_ms,
                request_id,
            )


app.include_router(router, prefix="/api")


@app.get("/")
def root():
    return {
        "name": "DabaPulse API",
        "version": __version__,
        "docs": "/docs",
        "health": "/api/health",
        "message": "From business signals to better decisions.",
    }


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "type": "HTTPException",
            "path": str(request.url.path),
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "detail": exc.errors(),
            "type": "RequestValidationError",
            "path": str(request.url.path),
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    # Log full exception server-side; never leak internals to clients in production.
    logger.exception("Unhandled error on %s", request.url.path)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Erreur interne du serveur.",
            "type": "InternalServerError",
            "path": str(request.url.path),
        },
    )


if __name__ == "__main__":
    import uvicorn

    s = get_settings()
    uvicorn.run(
        "app.main:app",
        host=s.api_host,
        port=s.api_port,
        reload=True,
    )
