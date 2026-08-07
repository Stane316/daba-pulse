# Merge Engineering Lead → `main` — PR groupée INC-04→06

Procédure contrôlée pour intégrer les incréments `HorizonX motion + perf + robustesse` dans `main`.

> **État actuel (2026-08-07) :** `main@cb51cea` contient déjà INC-01/02/03 (CI verte, hardening sécu, deploy). `engineering-lead/mvp-foundation@000e395..` contient 3 commits d'avance :
> - `a699d98 feat(ui): HorizonX-inspired motion and depth`
> - `432ae8e perf(frontend): code-split 662→241kB`
> - `000e395 fix(engineering): harden CSV import/export and reload`
> Soit **10 fichiers, 287 insertions, 33 deletions** (`git diff main..EL --stat`).

## Prérequis (à vérifier AVANT merge)

- [ ] Branche `engineering-lead/mvp-foundation` à jour sur GitHub (`a699d98`, `432ae8e`, `000e395` visibles)
- [ ] `main` à jour (`cb51cea` Merge PR #6)
- [ ] Commit sécurité présent (`SECURITY_NOTES.md` starlette 1.3.1, `dependabot.yml` block router 8.x)
- [ ] `pytest` vert (18, `ruff` 0, `pip-audit` clean)
- [ ] `npm run build` vert (après code-split : `index ~25kB + react ~217kB + charts ~386kB`, `oxlint` 0 errors)
- [ ] Prod vérifiée : `https://dabapulse-api.onrender.com/api/health` 200, `https://dabapulse.netlify.app` sans `Failed to fetch`, `bash scripts/smoke.sh https://dabapulse-api.onrender.com` 14 PASS, `CORS https://dabapulse.netlify.app`
- [ ] Aucun secret dans `git diff main..EL`
- [ ] Working tree clean (`git status`)

### Vérifs rapides (PowerShell)

```powershell
git fetch origin
git checkout engineering-lead/mvp-foundation
git pull origin engineering-lead/mvp-foundation
git log --oneline -n 5  # doit afficher a699d98, 432ae8e, 000e395
git diff origin/main --stat  # 10 files
# Tests
$env:DATA_PATH = "$PWD\data\sample"
cd backend; python -m pytest -q ../tests; cd ..
cd frontend; npm ci; npm run lint; npm run typecheck; npm run build; cd ..
# Smoke prod
bash scripts/smoke.sh https://dabapulse-api.onrender.com
```

## Contenu qui entre dans `main` (cette PR groupée)

**INC-04 feat(ui) — HorizonX motion (sans régression) :**
- `frontend/src/lib/motion.ts` (useCountUp + usePrefersReducedMotion)
- `frontend/src/index.css` (+shimmer, card-hover, btn-shine, prefers-reduced-motion)
- `frontend/src/components/ui.tsx` (Panel card-hover, PrimaryButton shine)
- `frontend/src/screens/SituationScreen.tsx` (hero RaR count-up 486k)

**INC-05 perf — code-split :**
- `frontend/src/App.tsx` (Situation eager, 5 autres `React.lazy` + `Suspense`)
- `frontend/vite.config.ts` (manualChunks react/charts/ui, 661→241kB initial)

**INC-06 fix(engineering) — robustesse démo :**
- `backend/app/services/csv_import.py` (MAX 5MB, utf-8-sig, empty check)
- `backend/app/api/routes.py` (upload 413, reload idempotent)
- `frontend/src/lib/api.ts` (parseError, timeout 15s, blob check)
- `frontend/src/context/PulseContext.tsx` (retry 900ms cold start)
- `frontend/src/screens/SituationScreen.tsx` (pre-checks .csv/empty/5MB)

**Déjà dans `main` (PR #4-6) :** INC-01 Ruff W292, INC-02 hardening sécu, INC-03 deploy (render.yaml, netlify.toml, start-api.sh, smoke.sh)

**Ne prétend pas** inclure Business Twin, CRM, Supabase, etc.

## Titre de PR recommandé

```text
Merge: HorizonX motion + perf code-split + CSV hardening (INC-04→06)
```

Description PR (copie/colle) :

```text
## Summary
- Merge engineering-lead/mvp-foundation (a699d98..000e395) into main
- INC-04 feat(ui): HorizonX-inspired motion (count-up 486k, shine, card-hover, prefers-reduced-motion) — +0.8kB
- INC-05 perf: code-split Decision Theater — index 662kB → 25kB + react 217kB + charts 386kB (initial 241kB, -63%)
- INC-06 fix: harden CSV import/export and reload — 5MB guard, 413, timeout 15s, retry 900ms, friendly missing_columns
- Prod verified: https://dabapulse.netlify.app (CORS https://dabapulse.netlify.app) + https://dabapulse-api.onrender.com 14 PASS

## Test plan
- [x] ruff 0, pip-audit clean, pytest 18
- [x] oxlint 0 errors, tsc 0, build 25kB+react+charts
- [x] bash scripts/smoke.sh https://dabapulse-api.onrender.com → 14 PASS
- [x] https://dabapulse.netlify.app — hero animé, no Failed to fetch, Import CSV .xlsx → message clair

## Risk
Aucun — pure front (lazy/suspense) + guards backend 5MB — aucune route/formule RaR touchée.

## Checklist PR
- [ ] CI DabaPulse verte sur EL
- [ ] Deploy Netlify auto (index 25kB) après merge
- [ ] Smoke prod re-run après merge
```

---

## Option A — Merge via Pull Request (recommandé)

### 1. Ouvrir la PR sur GitHub

1. https://github.com/Stane316/daba-pulse
2. **Compare & pull request**
3. base: **`main`** ← compare: **`engineering-lead/mvp-foundation`**
4. Title: `Merge: HorizonX motion + perf code-split + CSV hardening (INC-04→06)`
5. Body: coller la Description ci-dessus
6. Create pull request
7. Attendre **DabaPulse CI** verte (3 jobs)
8. **Merge pull request** → **Create a merge commit** (préfère merge commit pour garder `a699d98..000e395`)

### 2. Mettre à jour ton clone local après merge UI

```powershell
git fetch origin
git checkout main
git pull origin main
git log --oneline -n 6  # doit afficher Merge PR #7 + a699d98..000e395
git diff main..engineering-lead/mvp-foundation --stat  # doit être vide
```

---

## Option B — Merge en ligne de commande (PowerShell)

> À n’utiliser que si tu es à l’aise et que `main` n’a pas divergé.

```powershell
git fetch origin
git checkout engineering-lead/mvp-foundation
git pull origin engineering-lead/mvp-foundation
git status  # clean

git checkout main
git pull origin main

git merge --no-ff engineering-lead/mvp-foundation -m "Merge: HorizonX motion + perf code-split + CSV hardening (INC-04→06)"

# Re-tests
$env:DATA_PATH = "$PWD\data\sample"
cd backend; python -m pytest -q ../tests; cd ..
cd frontend; npm ci; npm run build; cd ..

git push origin main
git log origin/main -5 --oneline
```

---

## Après merge — checklist

```powershell
git checkout main
git pull origin main
git show origin/main:frontend/src/lib/motion.ts | Select-String "useCountUp"
git show origin/main:frontend/src/App.tsx | Select-String "lazy"
git show origin/main:README.md | Select-String "Déployé"
```

Puis : `bash scripts/smoke.sh https://dabapulse-api.onrender.com` (doit rester 14 PASS) + vérifier `https://dabapulse.netlify.app` (hero animé).

---

## En cas de problème

| Problème | Action |
|----------|--------|
| Conflits sur README / ci.yml | Garder `engineering-lead` pour le produit |
| CI rouge | Ne pas merger ; corriger sur EL puis re-PR |
| main a d’autres commits non liés | Rebase/merge avec l’équipe avant force |
| Oubli de push main | `git push origin main` après tests |

## Ce que ce merge N’EST PAS

- Pas une release Business Twin
- Pas une intégration Supabase obligatoire
- Pas un `npm audit fix --force` (router 8.x reste bloqué)
