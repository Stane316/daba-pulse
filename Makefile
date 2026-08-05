.PHONY: data backend frontend test install

install:
	python3 -m venv .venv
	.venv/bin/pip install -r backend/requirements.txt
	cd frontend && npm install

data:
	.venv/bin/python scripts/generate_synthetic_data.py

backend:
	DATA_PATH=$(PWD)/data/sample .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --app-dir backend --reload

frontend:
	cd frontend && npm run dev -- --host 0.0.0.0 --port 5173

test:
	cd backend && ../.venv/bin/pytest -q ../tests
	cd frontend && npm run typecheck
