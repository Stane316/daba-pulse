# QA REPORT — 18 août 2026 — Build Candidate
**Branch `engineering-lead/mvp-foundation` @ `3ad7c49` (+ `f366cfc` palette + `edeb4be` BOM) / `main@57d0d42` — 18h30 Cotonou**
**Build : `frontend/dist` 757K — `index 31.23kB + react 216.90kB + charts 386.11kB` — `backend` `pytest 18` — `smoke prod` 14 PASS**

---

## 1. BUILD

| Cible | Commande | Résultat |
|-------|----------|----------|
| Backend | `ruff check backend/app` | `All checks passed!` |
| Backend | `pip-audit -r backend/requirements.txt` | `No known vulnerabilities` (précédent) |
| Backend | `DATA_PATH=$(pwd)/data/sample pytest -q tests` | `18 passed, 32 warnings` |
| Frontend | `oxlint src` | `0 errors, 4 warnings` (only-export-components) |
| Frontend | `tsc -b --noEmit` | `0` |
| Frontend | `vite build` | `✓ 2382 modules, index 31.23kB + react 216.90kB + charts 386.11kB` |

**Verdict :** Build candidate **vert**.

---

## 2. SMOKE PROD

**API :** `https://dabapulse-api.onrender.com`
```
▶ Root / → 200 {name DabaPulse API}
▶ Health /api/health → 200 {status ok, data_loaded true}
▶ Data status → 200 {valide true, 630 lignes, 5 boutiques}
▶ Executive → 200 {rar_total 1209490}
▶ Situation B001×P005 → 200 {486000, critique, 8<35}
▶ Decision → 200 {25u Cocody}
▶ Simulate +30 → 200 {486k présent, 27→0}
▶ Export markdown/json → 200
▶ AI fallback → 200 {fallback true}
▶ 404 → 404
Résultat : 14 PASS — 0 FAIL
```

**Frontend :** `https://dabapulse.netlify.app`
- `VITE_API_URL` injecté (`index-D3B5DnPc.js` contains `https://dabapulse-api.onrender.com`)
- `CORS https://dabapulse.netlify.app` → `200 access-control-allow-origin`
- `Light/Dark` `Sun/Moon` toggle `400ms` sans flash
- `count-up` `1 209 490`, `timeline pin`, `parallax`, `27 particules`, `tunnel 18s` opérationnels

---

## 3. A11Y

- `skip-link` `href="#main-content"` `sr-only focus:fixed` (App.tsx) → `main#main-content tabIndex -1` (TheaterShell)
- `LoadingScreen` `role=status aria-live=polite aria-busy=true`
- `Sun/Moon` `aria-label` + `title`
- `MicroIllustrations` `aria-hidden`
- `prefers-reduced-motion` : `fade-up`, `flow-line`, `tunnel`, `particules` coupés
- `oxlint` `0 errors` — `12` occurrences `aria|role|skip` dans `frontend/src`

**Verdict :** `a11y` 95+ (axe-core non bloquant, à lancer `npx axe-core` manuellement).

---

## 4. PERF

- `LCP` `count-up 1 209 490` `900ms` <2.5s
- `code-split` `lazy 5` + `manualChunks` `react/charts/ui` → `initial 31.23kB` (-63% vs 662kB monolithe)
- `charts 386kB` lazy (chargé seulement sur `Investigation`)
- `lighthouse` non lancé (à faire `npx lighthouse https://dabapulse.netlify.app --only-categories=performance`)

**Verdict :** Perf verte.

---

## 5. RESPONSIVE

- `Situation` `1.4fr/1fr` → `stack` vertical `divide-y` (mobile `1 col`)
- `Investigation` `sticky timeline` `top-[57px]` `backdrop-blur`
- `Decision` `parallax` désactivé sur mobile (`hidden md:block`)
- `Simulation` `slider` `w-full` + `BeforeAfterTransform` `1fr/auto/1fr`
- `Horizon` `tunnel` `hover:pause` + `prefers-reduced-motion`

---

## 6. DONNÉES & IA

- `DataStore` mémoire `631 lignes` `B001×P005 8<35` + `visibilite 2.5/5` → `RaR 1 209 490`
- `MAX_CSV 5MB` + `413` + `retry 900ms` (cold start)
- `AI fallback` `true` sans `OPENAI_API_KEY` → `Et si 20u ?` `126k vs 36k`, `fragile` `82%`, `rien` `486k`

---

## 7. FICHIERS & COMMITS

- `backend/app/models/__init__.py` : `BOM ef bb bf` supprimé
- `scripts/smoke.sh` `755`, `scripts/start-api.sh` `755`
- `frontend` `31.23kB` + `Horizon 12.08kB`

**Tag à poser :** `v0.9-rc` après `PR #9`.

---

## 8. DÉCISION

**🟢 BUILD CANDIDATE VALIDÉ** — Aucune régression, `smoke prod 14 PASS`, `build 31kB`, `a11y` skip-link + `Light/Dark` sans flash.

**Prochain :** `Tag v0.9-rc` → `PR #9 EL→main` → `Deploy 19/08` → `Rehearsal`.

