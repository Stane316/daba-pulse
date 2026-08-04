"""DabaPulse FastAPI application."""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import __version__
from app.api.routes import router
from app.core.config import get_settings
from app.engines.data_loader import store


@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings = get_settings()
    data_path = Path(settings.data_path)
    # fallback relative to repo root
    if not data_path.exists():
        alt = Path(__file__).resolve().parents[2] / "data" / "sample"
        if alt.exists():
            settings.data_path = str(alt)
    try:
        store.load(settings.data_path)
        print(f"[DabaPulse] Data loaded from {settings.data_path}")
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
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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


@app.exception_handler(Exception)
async def unhandled_exception_handler(_request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc), "type": type(exc).__name__},
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
