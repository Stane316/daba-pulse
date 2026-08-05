# DabaPulse — Engineering Runbook

Guide de lancement, tests et déploiement pour l’Engineering Lead.

## 1. Prérequis

| Outil | Version |
|-------|---------|
| Git | 2.x |
| Python | 3.11+ (3.12 recommandé) |
| Node.js | 20 LTS |
| npm | 10+ |

Windows : PowerShell. Ne pas coller de syntaxe bash (`&&`, `test -f`) sans adaptation.

```powershell
git config --global core.autocrlf false
git config --global core.eol lf
```

## 2. Récupérer le code

```powershell
cd C:\Users\HP\Downloads\daba-pulse
git fetch origin
git checkout engineering-lead/mvp-foundation
git pull --ff-only origin engineering-lead/mvp-foundation
```

## 3. Installation

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt

cd frontend
npm ci
cd ..
```

## 4. Configuration

```powershell
copy .env.example .env
# Éditer .env si besoin — ne jamais committer .env
```

Variables importantes :

| Variable | Rôle |
|----------|------|
| `DATA_PATH` | Chemin vers `data/sample` |
| `CORS_ORIGINS` | `*` en local ; origines Netlify en prod |
| `OPENAI_API_KEY` | Optionnel (OpenRouter / Grok) |
| `OPENAI_BASE_URL` | Défaut OpenRouter |
| `VITE_API_URL` | Vide en local (proxy Vite) ; URL Render en prod |
| `API_JSON_LOGS` | `true` pour logs request id |

Sans clé AI : l’écran Explication utilise le **fallback déterministe**.

## 5. Lancer

Terminal 1 — API :

```powershell
.\.venv\Scripts\Activate.ps1
$env:DATA_PATH = "$PWD\data\sample"
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Terminal 2 — Frontend :

```powershell
cd frontend
npm run dev -- --host 0.0.0.0 --port 5173
```

| URL | Rôle |
|-----|------|
| http://localhost:5173 | UI |
| http://localhost:8000/api/health | Health |
| http://localhost:8000/docs | OpenAPI |

## 6. Tests rapides

```powershell
.\.venv\Scripts\Activate.ps1
cd backend
python -m pytest -q ..\tests
# attendu : 18 passed (ou plus)

cd ..\frontend
npm run typecheck
npm run build
```

Scénario démo :

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/situations/dist-B001-P005
# stock 8, demande 35, déficit 27, RaR 486000
```

## 7. Fonctionnalités Engineering livrées

| Feature | Où |
|---------|-----|
| Export résumé | Décision → boutons Export ; `GET /api/export/decision/{id}` |
| Import CSV | Situation → Importer CSV ; `POST /api/data/upload` |
| Recharger sample | Situation → Recharger le sample |
| Erreurs JSON | `detail` + `type` + `path` |
| Request id | Header réponse `X-Request-Id` |

## 8. Déploiement cible (EL-D)

| Couche | Outil |
|--------|-------|
| Frontend | **Netlify** — build `frontend`, publish `dist`, env `VITE_API_URL` |
| Backend | **Render** — root `backend` ou monorepo, start `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| Data | Bundler `data/sample` avec le service API |
| AI | Secret `OPENAI_API_KEY` sur Render |
| CORS | `CORS_ORIGINS=https://ton-site.netlify.app` |

Supabase : optionnel post-MVP (persistance), pas requis pour la démo fichier.

## 9. CI

Workflow `.github/workflows/ci.yml` :

- push/PR sur `main`, `develop`, `engineering-lead/**`, `feature/**`, `fix/**`
- frontend : lint, typecheck, build
- backend : ruff + pytest (avec `DATA_PATH`)
- security : pas de `.env` commité ; `backend/app/models` présent

## 10. Dépannage

| Symptôme | Action |
|----------|--------|
| `No module named app.models` | Pull packaging ; vérifier `backend/app/models/schemas.py` |
| Warning CRLF | `.gitattributes` + `core.autocrlf false` |
| CORS en prod | Fixer `CORS_ORIGINS` à l’URL Netlify |
| IA indisponible | Normal sans clé — fallback actif |
| Upload casse le scénario 486k | Bouton « Recharger le sample » |

## 11. Contacts rôles

| Sujet | Owner |
|-------|--------|
| Formules RaR / dataset | Data Lead |
| Prompts LLM | AI Lead |
| Copy / parcours jury | Product Lead |
| API, CI, deploy | **Engineering Lead** |