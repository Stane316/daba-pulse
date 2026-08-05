# Merge Engineering Lead → `main`

Procédure contrôlée pour intégrer le MVP DabaPulse dans `main`.

## Prérequis (à vérifier AVANT merge)

- [ ] Branche `engineering-lead/mvp-foundation` à jour sur GitHub
- [ ] Commit sécurité présent (`package.json` racine, requirements hardenés, `SECURITY_NOTES.md`)
- [ ] `pytest` vert (18+)
- [ ] `npm run build` vert (depuis `frontend/` **ou** racine)
- [ ] Aucun secret dans le dépôt
- [ ] Working tree clean

### Vérifs rapides (PowerShell)

```powershell
cd C:\Users\HP\Downloads\daba-pulse
git fetch origin
git checkout engineering-lead/mvp-foundation
git pull origin engineering-lead/mvp-foundation
git status
git log -3 --oneline

# Contenu sécurité
git show HEAD:package.json | Select-Object -First 5
git show HEAD:backend/requirements.txt
git show HEAD:backend/app/main.py | Select-String "Erreur interne"

# Tests
.\.venv\Scripts\Activate.ps1
$env:DATA_PATH = "$PWD\data\sample"
cd backend
python -m pytest -q ..\tests
cd ..\frontend
npm ci
npm run build
```

## Contenu qui entre dans `main`

MVP complet sur `engineering-lead/mvp-foundation` :

- Backend FastAPI + engines (risk, decision, sim, AI fallback)
- Frontend Decision Theater (6 écrans)
- Export / import CSV
- Dataset synthétique
- setup.md, DEPLOY.md, runbook, security notes
- Config Render + Netlify
- CI élargie

**Ne prétend pas** inclure Business Twin, CRM, marketplace, etc.

## Titre de merge recommandé

```text
Merge: Engineering foundation — Revenue-at-Risk MVP production readiness
```

Description PR (si tu utilises une PR) :

```text
## Summary
- Merge engineering-lead/mvp-foundation into main
- DabaPulse MVP: RaR + Decision Engine + What-if + AI explanation
- Deploy configs (Render API + Netlify front)
- Hardened deps + monorepo npm entrypoint

## Test plan
- [ ] pytest (backend)
- [ ] npm run build (frontend)
- [ ] /api/health + scenario B001/P005 = 486000 FCFA
```

---

## Option A — Merge via Pull Request (recommandé)

### 1. Ouvrir la PR sur GitHub

1. https://github.com/Stane316/daba-pulse  
2. **Compare & pull request**  
3. base: **`main`** ← compare: **`engineering-lead/mvp-foundation`**  
4. Title: `Merge: Engineering foundation — Revenue-at-Risk MVP production readiness`  
5. Create pull request  
6. Attendre CI verte (si activée)  
7. **Merge pull request** (Create a merge commit ou Squash — préfère **merge commit** pour garder l’historique Engineering)

### 2. Mettre à jour ton clone local après merge UI

```powershell
cd C:\Users\HP\Downloads\daba-pulse
git fetch origin
git checkout main
git pull origin main
git log -5 --oneline
git status
```

Attendu : `main` pointe sur un merge qui contient le MVP (plus seulement `df79214`).

---

## Option B — Merge en ligne de commande (PowerShell)

> À n’utiliser que si tu es à l’aise et que `main` n’a pas divergé avec du travail concurrent.

```powershell
cd C:\Users\HP\Downloads\daba-pulse

git fetch origin

# 1) Branche Engineering propre
git checkout engineering-lead/mvp-foundation
git pull origin engineering-lead/mvp-foundation
git status
# working tree DOIT être clean

# 2) Mettre main à jour
git checkout main
git pull origin main

# 3) Merge
git merge --no-ff engineering-lead/mvp-foundation -m "Merge: Engineering foundation — Revenue-at-Risk MVP production readiness"

# 4) Si conflits : résoudre, git add <files>, git commit

# 5) Re-tests sur main
.\.venv\Scripts\Activate.ps1
$env:DATA_PATH = "$PWD\data\sample"
cd backend
python -m pytest -q ..\tests
cd ..\frontend
npm ci
npm run build
cd ..

# 6) Push main (TOI uniquement)
git push origin main

# 7) Vérification
git fetch origin
git log origin/main -5 --oneline
git ls-tree -r --name-only origin/main | Select-String "setup.md|render.yaml|netlify.toml|risk_engine|SituationScreen"
```

---

## Après merge — checklist

```powershell
git checkout main
git pull origin main

# Doit exister sur origin/main :
git show origin/main:setup.md | Measure-Object -Character
git show origin/main:backend/app/engines/risk_engine.py | Select-Object -First 3
git show origin/main:package.json
```

Puis seulement :

1. Deploy **Render** (API) — voir `docs/DEPLOY.md`  
2. Deploy **Netlify** (front) avec `VITE_API_URL`  
3. CORS Render → URL Netlify  
4. Smoke prod  

---

## En cas de problème

| Problème | Action |
|----------|--------|
| Conflits sur README / .gitignore / ci.yml | Garder la version Engineering Lead pour le produit ; relire manuellement |
| CI rouge | Ne pas merger ; corriger sur EL puis re-PR |
| main a d’autres commits non liés | Rebase/merge avec l’équipe avant force |
| Oubli de push main | `git push origin main` après tests locaux |

---

## Ce que ce merge N’EST PAS

- Pas une release Business Twin  
- Pas une intégration Supabase obligatoire  
- Pas une garantie « zero CVE npm » (router résiduel documenté)  