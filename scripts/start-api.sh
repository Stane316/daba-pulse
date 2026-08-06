#!/usr/bin/env bash
# DabaPulse FastAPI — démarrage local ou Render.
# Gère DATA_PATH (dataset synthétique), PYTHONPATH et PORT (injecté par Render).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export DATA_PATH="${DATA_PATH:-$ROOT/data/sample}"
export PYTHONPATH="${ROOT}/backend${PYTHONPATH:+:$PYTHONPATH}"

# Fallback si DATA_PATH pointe vers un chemin invalide (ex: variable Render mal configurée)
if [ ! -d "$DATA_PATH" ]; then
  if [ -d "$ROOT/data/sample" ]; then
    echo "[DabaPulse] WARN: DATA_PATH=$DATA_PATH introuvable → fallback $ROOT/data/sample" >&2
    export DATA_PATH="$ROOT/data/sample"
  else
    echo "[DabaPulse] ERROR: DATA_PATH introuvable ($DATA_PATH) et $ROOT/data/sample absent" >&2
    ls -la "$ROOT/data" 2>&1 | head -n 20 >&2 || true
  fi
fi

if [ ! -f "$DATA_PATH/ventes_stocks.csv" ]; then
  echo "[DabaPulse] ERROR: ventes_stocks.csv manquant dans DATA_PATH=$DATA_PATH" >&2
  ls -la "$DATA_PATH" 2>&1 | head -n 20 >&2 || true
  echo "[DabaPulse] HINT: vérifie render.yaml DATA_PATH=/opt/render/project/src/data/sample" >&2
fi

cd "$ROOT/backend"
PORT="${PORT:-8000}"

echo "[DabaPulse] Starting API on 0.0.0.0:$PORT — DATA_PATH=$DATA_PATH — CORS_ORIGINS=${CORS_ORIGINS:-*}" >&2
echo "[DabaPulse] Health: http://0.0.0.0:$PORT/api/health — Docs: http://0.0.0.0:$PORT/docs" >&2

exec python -m uvicorn app.main:app --host 0.0.0.0 --port "$PORT"
