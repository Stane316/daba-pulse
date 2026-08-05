# DabaPulse — Déploiement (EL-D)

Cible hackathon :

| Couche | Plateforme | Rôle |
|--------|------------|------|
| Frontend | **Netlify** | UI Decision Theater |
| Backend | **Render** | FastAPI + engines + `data/sample` |
| DB | — | Non requis (CSV en mémoire) |
| IA | Secret Render | OpenRouter / Grok optionnel |

```text
Navigateur
  → Netlify (React build)
      → VITE_API_URL
          → Render (uvicorn /api/*)
              → data/sample
```

Fichiers de config versionnés :

- `render.yaml` — blueprint API
- `netlify.toml` — build front + SPA redirects
- `scripts/start-api.sh` — démarrage API monorepo
- `frontend/public/_redirects` — fallback routes React

---

## Ordre recommandé

1. Déployer **Render (API)** en premier  
2. Noter l’URL API (`https://….onrender.com`)  
3. Déployer **Netlify (front)** avec `VITE_API_URL`  
4. Restreindre `CORS_ORIGINS` sur Render à l’URL Netlify  

---

## 1. Render — API

### Option A — Blueprint (`render.yaml`)

1. https://dashboard.render.com → **New** → **Blueprint**  
2. Connecter le repo `Stane316/daba-pulse`  
3. Branche : `engineering-lead/mvp-foundation` (ou `main` après merge)  
4. Appliquer le blueprint `render.yaml`  
5. Dans **Environment**, renseigner si besoin :
   - `OPENAI_API_KEY` (secret, optionnel)
   - `CORS_ORIGINS` = `*` au premier jet, puis URL Netlify

### Option B — Web Service manuel

| Champ | Valeur |
|-------|--------|
| Runtime | Python 3 |
| Branch | `engineering-lead/mvp-foundation` |
| Root Directory | *(vide = racine monorepo)* |
| Build Command | `pip install -r backend/requirements.txt` |
| Start Command | `bash scripts/start-api.sh` |
| Health Check Path | `/api/health` |

### Variables d’environnement Render

| Key | Exemple |
|-----|---------|
| `DATA_PATH` | `/opt/render/project/src/data/sample` |
| `CORS_ORIGINS` | `https://ton-site.netlify.app` |
| `AI_ENABLED` | `true` |
| `OPENAI_API_KEY` | *(secret optionnel)* |
| `OPENAI_BASE_URL` | `https://openrouter.ai/api/v1` |
| `OPENAI_MODEL` | `openai/gpt-4o-mini` |
| `API_JSON_LOGS` | `true` |
| `PORT` | fourni automatiquement par Render |

### Vérifications API

```text
GET https://<api>.onrender.com/api/health
→ {"status":"ok", ...}

GET https://<api>.onrender.com/api/situations/dist-B001-P005
→ stock 8, demande 35, déficit 27, RaR 486000

GET https://<api>.onrender.com/docs
```

**Note free tier :** le service peut s’endormir après inactivité (~50 s au réveil).

---

## 2. Netlify — Frontend

1. https://app.netlify.com → **Add new site** → **Import from Git**  
2. Repo `Stane316/daba-pulse`  
3. Branch : `engineering-lead/mvp-foundation`  
4. Netlify lit `netlify.toml` :

| Champ | Valeur (déjà dans netlify.toml) |
|-------|----------------------------------|
| Base directory | `frontend` |
| Build command | `npm ci && npm run build` |
| Publish directory | `dist` |

### Variable d’environnement Netlify (obligatoire pour la prod)

| Key | Value |
|-----|--------|
| `VITE_API_URL` | `https://<ton-api>.onrender.com` **sans** `/` final |

> `VITE_*` est injecté **au build**. Après chaque changement de `VITE_API_URL`, **relancer un deploy**.

### Vérifications front

- Ouvrir `https://<site>.netlify.app`  
- Parcours 6 écrans  
- Export décision (Décision → Exporter)  
- Network : appels vers l’URL Render, pas `localhost`

---

## 3. CORS (après les deux URLs connues)

Sur Render, remplacer :

```env
CORS_ORIGINS=*
```

par :

```env
CORS_ORIGINS=https://ton-site.netlify.app,https://deploy-preview-*.netlify.app
```

(Render n’accepte pas toujours les wildcards : liste les URLs exactes de preview si besoin, ou garde `*` le temps du hackathon.)

Redéployer / restart le service API.

---

## 4. Checklist go-live démo

- [ ] `GET /api/health` → ok sur Render  
- [ ] Scénario B001/P005 → 486 000 FCFA  
- [ ] Front Netlify charge sans erreur console CORS  
- [ ] Simulation + export fonctionnent  
- [ ] Badge « Données synthétiques » visible  
- [ ] Sans clé AI : explication fallback OK  
- [ ] (Optionnel) clé OpenRouter sur Render pour LLM  

---

## 5. Dépannage deploy

| Symptôme | Cause probable | Action |
|----------|----------------|--------|
| Front appelle `localhost:8000` | `VITE_API_URL` non défini au build | Set env + **Clear cache & deploy** Netlify |
| CORS error navigateur | `CORS_ORIGINS` ≠ URL Netlify | Corriger env Render + restart |
| API 503 data | `DATA_PATH` incorrect | Vérifier path sample sur Render logs |
| 404 sur refresh d’une route | SPA redirect manquant | `netlify.toml` + `_redirects` |
| Cold start long | Free tier sleep | Ouvrir `/api/health` 1 min avant le pitch |

---

## 6. Commandes Git liées au déploiement

Les fichiers de config sont versionnés. Après modification :

```powershell
git add render.yaml netlify.toml scripts/start-api.sh frontend/public/_redirects docs/DEPLOY.md
git commit -m "chore(deploy): add Render + Netlify configuration"
git push origin engineering-lead/mvp-foundation
```

Puis redéployer / laisser l’auto-deploy Git se déclencher.