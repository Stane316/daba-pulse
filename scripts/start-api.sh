#!/usr/bin/env bash
# Start DabaPulse FastAPI (local or Render).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export DATA_PATH="${DATA_PATH:-$ROOT/data/sample}"
export PYTHONPATH="${ROOT}/backend${PYTHONPATH:+:$PYTHONPATH}"

# Resolve sample data if DATA_PATH is wrong/relative on the host
if [ ! -d "$DATA_PATH" ]; then
  if [ -d "$ROOT/data/sample" ]; then
    export DATA_PATH="$ROOT/data/sample"
  fi
fi

cd "$ROOT/backend"
PORT="${PORT:-8000}"
exec python -m uvicorn app.main:app --host 0.0.0.0 --port "$PORT"