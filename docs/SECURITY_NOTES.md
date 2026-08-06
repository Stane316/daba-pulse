# DabaPulse — Notes de sécurité (deps)

Dernière revue Engineering : **2026-08-06** (branch `engineering-lead/mvp-foundation` @ `96d7bf1` + INC-01).

## Backend (pip)

Pins dans `backend/requirements.txt` (vérifié `pip-audit` le **2026-08-06** : **No known vulnerabilities found**) :

- `fastapi==0.141.1`
- `starlette==1.3.1` (pin explicite ; `pip-audit` clean avec ce set — corrige l'ancienne note 1.0.1)
- `uvicorn[standard]==0.34.3`
- `pandas==2.2.3` / `numpy==2.2.1`
- `pydantic==2.10.4` / `pydantic-settings==2.7.0`
- `python-multipart==0.0.31` (upload CSV)
- `httpx==0.28.1`
- `python-dotenv==1.2.2`
- `pytest==9.0.3` (dev/CI) / `ruff==0.8.4`

Relancer après changement :

```bash
pip install -r backend/requirements.txt
DATA_PATH=$(pwd)/data/sample pytest -q tests
pip-audit -r backend/requirements.txt
```

CI backend exécute `ruff check app` **et** `pip-audit` (non-bloquant, rapport en log).

## Frontend (npm)

- `react-router` / `react-router-dom` épinglés en **7.18.2** (exact, dans `frontend/package.json`)
- `npm audit --omit=dev` au **2026-08-06** : **2 high** — advisory `GHSA-qwww-vcr4-c8h2` sur `react-router 7.12.0 - 8.2.0` (RSC Mode CSRF Bypass)
- Correctif amont `react-router@8.3.0` existe, mais **`react-router-dom@8` n’est pas publié** de façon exploitable sur le registry au moment de la revue (vérifié 06/08). `npm audit fix --force` proposerait `7.11.0` (downgrade majeur, breaking).
- Notre usage = **SPA client** (`BrowserRouter` dans `App.tsx`), sans RSC / single-fetch server actions / `createSingleFetch` — surface d'attaque RSC non exposée.

**Risque résiduel accepté pour le hackathon** tant que :

1. pas d’auth/session serveur via React Router actions ;
2. pas de mode RSC ;
3. URLs externes dans la navigation restent contrôlées.

Réévaluer dès publication stable de `react-router-dom@8.x` compatible. CI frontend exécute `npm audit` en **non-bloquant** (warning, pas d'échec).

### Dependabot — PR #2 bloqueur

- **PR #2** `dependabot/npm_and_yarn/frontend/react-router-8.3.0` → `ee8a491` **DOIT RESTER OUVERTE ET NON MERGÉE** sans validation manuelle complète (`npm ci && npm run build && npm run typecheck` + test parcours 6 écrans).
- Raison : `react-router@8.3.0` sans `react-router-dom@8` casse le build Vite (module manquant). Un merge auto casserait `main`.
- **Politique** (voir `.github/dependabot.yml`) : pas d'auto-merge ; le label `dependencies` exige revue Engineering Lead ; les bumps majeurs `react-router` sont en `ignore` jusqu'à `react-router-dom@8` stable.

## Secrets

- Aucune clé LLM dans le frontend (`VITE_*` public uniquement — seul `VITE_API_URL` est injecté au build Netlify)
- Secrets uniquement sur Render (`OPENAI_API_KEY` via `sync: false` dans `render.yaml`, jamais dans Git)
- Jamais de `.env` commité — CI `security` bloque tout `.env*` / `*.pem` / `*.key` / `*.p12` / `*.pfx`
- `.env.example` = placeholders vides uniquement (vérifié)

## CORS

- Local / dev : `CORS_ORIGINS=*` (autorisé)
- **Production :** remplacer par l’URL Netlify exacte (`https://<site>.netlify.app`) dans Render → Environment → `CORS_ORIGINS`. Redéployer Render. Voir `docs/DEPLOY.md` §3.
- Le code `backend/app/main.py` gère déjà `allow_credentials = origins != ["*"]` (pas de `*` avec credentials).

## Vérifications avant chaque PR vers `main`

- [ ] `pip-audit -r backend/requirements.txt` → clean
- [ ] `npm audit --omit=dev` → 2 high connues documentées ci-dessus, pas d'autre high/critical
- [ ] Aucun secret dans `git diff origin/main`
- [ ] `CORS_ORIGINS` prod restreint si deploy live
- [ ] PR Dependabot `react-router` non mergée sans validation build
