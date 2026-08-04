# DabaPulse Backend

API FastAPI + moteurs analytiques déterministes.

## Démarrage

```bash
# depuis la racine du repo
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
python scripts/generate_synthetic_data.py

export DATA_PATH="$(pwd)/data/sample"
cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Docs interactives : http://localhost:8000/docs

## Endpoints principaux

| Méthode | Chemin | Description |
|---------|--------|-------------|
| GET | `/api/health` | Santé |
| GET | `/api/executive` | Résumé RaR + situations |
| GET | `/api/situations/{id}` | Détail risque |
| GET | `/api/decisions/{id}` | Recommandation |
| POST | `/api/simulate` | What-if |
| POST | `/api/ai/explain` | Explication (fallback sans LLM) |
| GET | `/api/hypotheses` | Hypothèses versionnées |

## Tests

```bash
cd backend && pytest -q ../tests
```
