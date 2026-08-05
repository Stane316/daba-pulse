# DabaPulse — Notes de sécurité (deps)

Dernière revue Engineering (production readiness).

## Backend (pip)

Pins dans `backend/requirements.txt` :

- `fastapi==0.141.1`
- `starlette==1.0.1` (pin explicite ; `pip-audit` clean avec ce set)
- `python-multipart==0.0.31` (upload CSV)
- `python-dotenv==1.2.2`
- `pytest==9.0.3` (dev/CI)

Relancer après changement :

```bash
pip install -r backend/requirements.txt
pytest -q tests
pip-audit -r backend/requirements.txt   # optionnel
```

## Frontend (npm)

- `react-router` / `react-router-dom` épinglés en **7.18.2**
- `npm audit` peut encore signaler des advisory **high** sur la ligne 7.12–8.x
- Correctif amont `react-router@8.3.0` existe, mais **`react-router-dom@8` n’est pas publié** sur le registry au moment de la revue
- Notre usage = **SPA client** (BrowserRouter), sans RSC / single-fetch server actions

**Risque résiduel accepté pour le hackathon** tant que :

1. pas d’auth/session serveur via React Router actions ;
2. pas de mode RSC ;
3. URLs externes dans la navigation restent contrôlées.

Réévaluer dès publication stable de `react-router-dom@8.x` compatible.

## Secrets

- Aucune clé LLM dans le frontend (`VITE_*` public uniquement)
- Secrets uniquement sur Render (`OPENAI_API_KEY`)
- Jamais de `.env` commité

## CORS

En production, remplacer `CORS_ORIGINS=*` par l’URL Netlify exacte.