#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

if [ ! -d "$ROOT/.venv" ]; then
  python3 -m venv "$ROOT/.venv"
  "$ROOT/.venv/bin/pip" install -r "$ROOT/backend/requirements.txt"
fi

if [ ! -f "$ROOT/data/sample/ventes_stocks.csv" ]; then
  "$ROOT/.venv/bin/python" "$ROOT/scripts/generate_synthetic_data.py"
fi

export DATA_PATH="$ROOT/data/sample"
cd "$ROOT/backend"
exec "$ROOT/.venv/bin/uvicorn" app.main:app --host 0.0.0.0 --port 8000 --reload
