# DABAPULSE — PROJECT HANDOVER & CONTINUITY REPORT

**Date du rapport :** 2026-08-05 (timezone Africa/Lagos / session agent)  
**Auteur :** Audit de continuité (lecture seule du produit ; ce document est le livrable)  
**Source de vérité Git inspectée :** `https://github.com/Stane316/daba-pulse.git`  
**SHA `origin/main` inspecté :** `d1e73bb` — *Merge pull request #3 from Stane316/engineering-lead/mvp-foundation*  
**SHA `origin/engineering-lead/mvp-foundation` inspecté :** `182347e` — *fix(ci): stop backend CI failures on Ruff W292 newlines*  
**Clone de vérification :** `/tmp/dabapulse-handover` (branche `main` @ `d1e73bb`)

---

## 1. Executive Summary

DabaPulse est un **MVP de moteur décisionnel Revenue-at-Risk / Smart Distribution** pour le contexte DABA SAS (agroalimentaire / aviculture), développé dans le hackathon **Startup FairPlay — Mission 2 Brand & Growth**.

### Ce qui est CONFIRMÉ (preuves repository + exécution locale)

| Élément | Preuve |
|---------|--------|
| Produit vertical slice présent sur **`main`** | Arbre Git 84 fichiers ; engines, API, 6 écrans, data sample, deploy configs |
| Scénario démo B001×P005 | Stock **8**, demande **35**, déficit **27**, RaR **486 000 FCFA** (exécuté) |
| Simulation +30 u. | RaR **0**, protégé **486 000** (exécuté) |
| pytest | **18 passed** (exécuté sur clone `main`) |
| Frontend build | **SUCCESS** `npm run build` (exécuté) |
| pip-audit sur `requirements.txt` | **No known vulnerabilities found** (exécuté) |
| LLM optionnel + fallback | `ai_layer.explain` → `fallback=True` sans clé (exécuté) |
| Secrets réels dans Git | **Aucun détecté** (scan filenames + patterns) |
| Merge Engineering → main | PR **#1** et PR **#3** **MERGED** |

### Ce qui BLOQUE encore la “production readiness”

| Élément | Preuve |
|---------|--------|
| **CI Backend rouge sur `main`** | Run `31047894070` : step **Run Ruff** = failure ; pytest n’est pas la cause |
| **W292 toujours actif** | `backend/ruff.toml` sur `main` : `ignore = ["E501"]` seulement (pas `W292`) |
| **Newlines manquantes** | Fichiers sans `\n` final : `main.py`, `config.py`, `data_loader.py`, `services/__init__.py`, `csv_import.py` (+ export selon état) |
| **Commit CI “fix W292” incomplet** | `182347e` ajoute surtout une **ligne vide** dans `ruff.toml`, **pas** `ignore = ["W292"]` ; ne corrige pas tous les EOF |
| **Déploiement live Netlify/Render** | **NON VÉRIFIÉ** (configs présentes, aucune URL prod confirmée dans le repo) |
| **Dependabot PR #2** | OPEN : bump `react-router` 8.3.0 — **risqué** (`react-router-dom@8` souvent absent/incomplet) |

### Statut global

**🟡 MVP FONCTIONNEL LOCALEMENT / MERGÉ DANS MAIN — CI BACKEND NON VERTE — DEPLOY CLOUD NON VÉRIFIÉ**

---

## 2. Project Identity

| Champ | Valeur | Source |
|-------|--------|--------|
| Nom | **DabaPulse** | README.md, code, docs |
| Hackathon | Startup FairPlay | README.md |
| Mission | Mission 2 — Brand & Growth | README.md, PDF cadrage |
| Entreprise cible | DABA SAS (aviculture / distribution) | README, docs |
| MVP | Revenue-at-Risk Decision Engine + Smart Distribution | README §4, §23 |
| Vision LT | Business Twin / Growth Decision OS | README §15, PDF |
| Tagline | *Turn business signals into decisions. Protect revenue before it's lost.* | README |
| Licence | **NON définive** dans README §25 | README |

**Document de cadrage présent :**  
`docs/Mission_2_Cadrage_Finale_Miseàjour.pdf`  

**Document demandé parfois sous le nom** `Mission_2_Cadrage_Final_avec_Chapitre9.docx` :  
**ABSENT du repository** (seul le PDF “Finale_Miseàjour” + `Rôles.docx` sont dans `docs/`).

---

## 3. Strategic Context

### Problème (confirmé documentation)

DABA peut avoir produits, stocks, points de vente et historique de ventes **sans mécanisme direct** pour :

1. détecter un désalignement demande/stock/distribution (et signaux réputation dans le cadrage élargi) ;
2. estimer le **revenu exposé** ;
3. recommander **quoi / où / combien** ;
4. simuler l’impact avant d’agir.

### Ce que le MVP n’est PAS (documenté)

Pas un simple dashboard, chatbot, CRM, marketplace, marketing automation, Business Twin complet (README §14, PDF hors-MVP).

### Boucle de valeur

```text
SIGNAL → RISQUE → VALEUR ÉCONOMIQUE → DÉCISION → SIMULATION → IMPACT
```

---

## 4. Current MVP

### Périmètre fonctionnel retenu

| Capacité | Dans le code ? | Preuve |
|----------|----------------|--------|
| Dataset synthétique | 🟢 | `data/sample/*` |
| Validation / load data | 🟢 | `data_loader.py` |
| Analytics demande/stock | 🟢 | `analytics.py` |
| Risk + RaR distribution & réputation | 🟢 | `risk_engine.py` + smoke 486k / 129600 rep |
| Decision Engine | 🟢 | `decision_engine.py` + réallocation Cocody |
| What-if Simulator | 🟢 | `simulator.py` + API `/simulate` |
| FastAPI | 🟢 | `main.py` + `routes.py` |
| React 6 écrans | 🟢 | `frontend/src/screens/*` + `App.tsx` |
| AI explanation + fallback | 🟢 | `ai_layer.py` |
| Export décisionnel | 🟢 | `export_summary.py` + UI Decision |
| Import CSV | 🟢 | `csv_import.py` + UI Situation |
| Config deploy Netlify/Render | 🟢 fichiers | `netlify.toml`, `render.yaml` |
| Deploy cloud live | ⚪ NON VÉRIFIÉ | pas d’URL prod confirmée |
| PostgreSQL / Supabase | 🔴 non utilisé dans le code app | aucun import app |

### Scénario de démonstration (vérifié par exécution)

| Indicateur | Valeur mesurée |
|------------|----------------|
| Situation | `dist-B001-P005` (DABA Plateau × Poulet premium) |
| Stock | 8 |
| Demande 7j | 35 |
| Déficit | 27 |
| RaR | **486 000 FCFA** |
| Sévérité | critique |
| Décision | réallocation **25** u. depuis **DABA Cocody** |
| Simu +30 | RaR 486 000 → **0**, protégé **486 000** |
| RaR total portfolio | **1 209 490** (dist 1 079 890 + rep 129 600) |
| Nb situations | 12 |

---

## 5. Architecture

### Pipeline réel (confirmé code)

```text
data/sample (CSV/JSON synthétiques)
    → DataStore.load / upload CSV (data_loader + csv_import)
    → analytics (demande, tendance, couverture)
    → risk_engine (rupture, surstock, réputation + RaR)
    → decision_engine (réallocation / réappro / actions réputation)
    → simulator (what-if)
    → FastAPI (/api/*)
    → React Decision Theater (6 routes)
    → ai_layer (LLM optionnel OpenAI-compatible + fallback déterministe)
```

### Principes respectés (preuves)

| Principe | Statut | Preuve |
|----------|--------|--------|
| Logique métier hors React | 🟢 | calculs dans `backend/app/engines/*` |
| Front consomme API | 🟢 | `frontend/src/lib/api.ts` |
| IA découplée des calculs | 🟢 | engines sans LLM ; AI lit résultats |
| Hypothèses versionnées | 🟢 | `HYPOTHESES` dans `core/config.py` |
| Données synthétiques signalées | 🟢 | disclaimer + badge UI + meta.json |

### Architecture cible vs réelle

| Cible docs | Réel |
|------------|------|
| React+Vite+Tailwind+Recharts | 🟢 |
| FastAPI+Pandas+NumPy | 🟢 |
| PostgreSQL/Supabase | 🔴 non branché (fichiers mémoire) |
| Netlify + Render | 🟢 configs ; ⚪ live NON VÉRIFIÉ |

---

## 6. Technical Stack

### Confirmé dans le repository (`main` @ `d1e73bb`)

| Couche | Technologie | Versions / notes |
|--------|-------------|------------------|
| Frontend | React | ^19.2.8 |
| | Vite | ^8.2.0 |
| | Tailwind | ^4.3.3 (`@tailwindcss/vite`) |
| | react-router-dom | **7.18.2** (pin exact) |
| | Recharts | ^3.10.1 |
| | TypeScript | ~6.0.2 |
| | Lint | oxlint |
| Backend | FastAPI | **0.141.1** |
| | Starlette | **1.3.1** (pin) |
| | Uvicorn | 0.34.3 |
| | Pandas / NumPy | 2.2.3 / 2.2.1 |
| | Pydantic / settings | 2.10.4 / 2.7.0 |
| | python-multipart | 0.0.31 |
| | httpx | 0.28.1 |
| Tests | pytest | 9.0.3 |
| Quality | ruff | 0.8.4 |
| Monorepo npm | `package.json` racine | scripts proxy → `frontend/` |
| Deploy | render.yaml, netlify.toml, start-api.sh | présents |

### npm audit (exécuté, omit dev)

- **2 high** sur `react-router` 7.12–8.2 (CSRF RSC advisory).  
- Fix amont `react-router@8.3.0` existe ; **`react-router-dom@8` non publié** de façon utilisable au moment des essais antérieurs.  
- Usage app = **SPA client** (BrowserRouter) — risque documenté dans `docs/SECURITY_NOTES.md`.

### pip-audit (exécuté sur requirements.txt)

- **No known vulnerabilities found**

---

## 7. Repository Structure

### Arbre principal (84 fichiers trackés sur `main`)

```text
daba-pulse/
├── .github/workflows/ci.yml
├── .env.example
├── .gitattributes
├── .gitignore
├── Makefile
├── package.json                 # monorepo npm proxy
├── setup.md                     # install + run local
├── render.yaml
├── netlify.toml
├── README.md
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/routes.py
│   │   ├── core/config.py
│   │   ├── engines/             # analytics, risk, decision, simulator, ai, data_loader
│   │   ├── models/schemas.py
│   │   └── services/            # csv_import, export_summary
│   ├── requirements.txt
│   ├── ruff.toml
│   ├── pytest.ini
│   └── runtime.txt
├── frontend/
│   ├── src/screens/             # 6 écrans
│   ├── src/components/
│   ├── src/context/PulseContext.tsx
│   ├── src/lib/api.ts
│   └── package.json
├── data/sample/                 # CSV/JSON synthétiques
├── docs/                        # cadrage + runbooks
├── scripts/
└── tests/
```

### Rôles des dossiers clés

| Chemin | Rôle |
|--------|------|
| `backend/app/engines/` | Cœur métier déterministe |
| `backend/app/api/` | Surface HTTP |
| `backend/app/services/` | Export / import (orchestration légère) |
| `frontend/src/screens/` | Parcours Decision Theater |
| `data/sample/` | Démo sans données DABA réelles |
| `docs/` | Cadrage + ops Engineering |
| `tests/` | Engines + API export/import |

---

## 8. Current Implementation Status

### Chaîne MVP (preuves)

| Étape | Existe | Fonctionnelle (local) | Connectée | Testée |
|-------|--------|------------------------|-----------|--------|
| CSV / sample | 🟢 | 🟢 | 🟢 | 🟢 |
| Validation | 🟢 | 🟢 | 🟢 | 🟢 partiel |
| Analytics | 🟢 | 🟢 | 🟢 | via engines |
| Risk Engine | 🟢 | 🟢 | 🟢 | 🟢 |
| Revenue-at-Risk | 🟢 | 🟢 | 🟢 | 🟢 |
| Decision Engine | 🟢 | 🟢 | 🟢 | 🟢 |
| Simulation | 🟢 | 🟢 | 🟢 | 🟢 |
| API | 🟢 | 🟢 | 🟢 | 🟢 |
| Dashboard React | 🟢 | 🟢 build | 🟢 | 🟡 pas e2e |
| AI Explanation | 🟢 | 🟢 fallback | 🟢 | 🟡 fallback testé ; LLM live NON VÉRIFIÉ |
| Export | 🟢 | 🟢 | 🟢 | 🟢 |
| Import CSV | 🟢 | 🟢 | 🟢 | 🟢 |
| CI GitHub | 🟢 config | 🔴 Backend Ruff fail | — | runs failure confirmés |
| Deploy live | 🟢 fichiers | ⚪ NON VÉRIFIÉ | — | — |

### Pourcentages justifiés (ordre de grandeur)

| Domaine | % | Justification |
|---------|---|---------------|
| Architecture | **90%** | Pipeline complet en code ; DB optionnelle absente volontairement |
| Backend | **90%** | API + engines + services |
| Frontend | **85%** | 6 écrans + wiring ; polish/e2e limités |
| Data | **85%** | Sample cohérent + upload |
| Risk Engine | **90%** | Dist + réputation + smoke 486k |
| Decision Engine | **85%** | Règles + alternative |
| Simulation | **90%** | Avant/après + quantité |
| IA | **75%** | Fallback solide ; LLM dépend clé prod |
| Tests | **70%** | 18 tests utiles ; pas e2e UI |
| Sécurité | **65%** | Secrets OK, pip-audit OK, CI rouge, npm high, CORS `*` |
| Documentation | **80%** | setup, deploy, runbook, security, merge |
| Déploiement | **40%** | Configs prêtes ; **live NON VÉRIFIÉ** ; CI bloque confiance merge |

---

## 9. Feature Inventory

| Fonctionnalité | État | Preuve | Fichiers | Tests | Risques |
|----------------|------|--------|----------|-------|---------|
| Import CSV | 🟢 | UI + API | `csv_import.py`, `routes.py`, `SituationScreen.tsx` | test_upload_* | validation colonnes stricte |
| Validation data | 🟢 | load + upload | `data_loader.py` | test_data_loaded | upload en mémoire only |
| Aperçu dataset | 🟢 | `/api/data/preview` | routes + data_loader.preview | test_data_preview | UI aperçu limitée |
| Dashboard / Situation | 🟢 | `/` | SituationScreen, PulseContext | build | — |
| Détection risques | 🟢 | risk_engine | risk_engine.py | test_engines | — |
| RaR | 🟢 | formule + smoke | risk_engine, config HYPOTHESES | test + smoke | réputation ≠ table pédagogique 64.8k |
| Classement | 🟢 | priorite/sévérité | risk_engine, executive | — | — |
| Recommandation | 🟢 | decision_engine | decision_engine.py | test_decision_* | — |
| Explication quanti | 🟢 | raisons/drivers | decision + investigation UI | — | — |
| Simulation What-if | 🟢 | simulator + UI | simulator, SimulationScreen | test_simulation_* | — |
| Revenu protégé | 🟢 | simu/decision | multiple | smoke | estimation non garantie |
| Assistant IA | 🟢 fallback | ai_layer + ExplanationScreen | explain fallback | LLM live NON VÉRIFIÉ |
| Export décisionnel | 🟢 | export service + UI | export_summary, DecisionScreen | test_export_* | — |
| API complète | 🟢 | routes listées §16 | routes.py | test_api_* | — |
| Intégration FE/BE | 🟢 | api.ts + proxy Vite | vite.config.ts | build | VITE_API_URL requis en prod |
| Sécurité deps | 🟡 | pip clean ; npm high router | requirements, package.json | audits | router residual |
| CI | 🔴 | Run Ruff fail | ci.yml, ruff.toml | GHA | **P0** |
| Deploy Netlify/Render | 🟠 configs only | render.yaml, netlify.toml | — | live NON VÉRIFIÉ |
| PostgreSQL | 🔴 / ⚪ doc only | non dans code app | — | — |

Légende : 🟢 terminé vérifié · 🟡 à valider · 🟠 partiel · 🔴 non · ⚪ documenté non implémenté

---

## 10. Data Layer

### Emplacement

`data/sample/`

| Fichier | Rôle |
|---------|------|
| `ventes_stocks.csv` | Historique ventes/stocks (schéma MVP) |
| `boutiques.csv` | Référentiel boutiques |
| `produits.csv` | Référentiel produits |
| `visibilite_globale.json` | Signaux réputation/visibilité |
| `meta.json` | Métadonnées + scénario démo + disclaimer |
| `README.md` | Doc sample |

### Schéma CSV (vérifié header)

```text
date,boutique_id,produit_id,stock,ventes,prix_unitaire,stock_cible,delai_reappro
```

### Nature des données

- **Type :** synthétiques (`meta.json` `"type": "synthetiques"`)  
- **Génération :** `scripts/generate_synthetic_data.py`  
- **Données réelles DABA :** **absentes** (et doivent le rester hors process validé)  
- **Runtime :** chargement mémoire (`DataStore`) ; upload remplace le store en RAM (pas de persistance disque durable)

### Boutiques démo (meta)

B001 Plateau, B002 Cocody, B003 Yopougon, B004 Bouaké, B005 San-Pédro (Abidjan / intérieur).

---

## 11. Revenue-at-Risk Engine

### Fichier principal

`backend/app/engines/risk_engine.py`  
Hypothèses : `backend/app/core/config.py` → `HYPOTHESES`

### Distribution (confirmé code)

```text
deficit = max(0, demande_attendue - stock)
RaR = round(deficit * prix_unitaire, 0)
```

Demande via `analytics.compute_demand_forecast` (moyenne 7j × tendance × horizon).

### Surstock (confirmé)

```text
RaR_surstock ≈ surplus × prix × 0.15
```

### Réputation (confirmé)

```text
revenu_jour = visiteurs × conversion × prix_moyen
RaR_rep = round(revenu_jour × max(facteur, 0.05), 0)
```

Facteurs cumulés (config) : note&lt;3.5 → 0.20 ; engagement&lt;1% → 0.10 ; absence avis → 0.15 ; faible visibilité → 0.10.

**Écart documenté historiquement :** exemple pédagogique cadrage parfois **64 800** (facteur 0.20 seul) ; code actuel smoke → **129 600** (facteurs cumulés).  
Ne pas présenter 64 800 comme sortie code sans recalibrage Data Lead.

### Exposition

- `GET /api/executive` → totaux + liste situations  
- `GET /api/situations/{id}`  
- UI Situation / Investigation  

---

## 12. Decision Engine

### Fichier

`backend/app/engines/decision_engine.py`

### Comportements confirmés

| Type risque | Action typique |
|-------------|----------------|
| Rupture / demande croissante | `reallocation` si source surplus, sinon `reapprovisionnement` |
| Surstock | `transfert_sortant` |
| Réputation | `collecte_avis` / `strategie_contenu` / `optimisation_gmb` |

### Démo vérifiée

- Action : **reallocation**  
- Quantité : **25**  
- Source : **DABA Cocody**  
- Protégé estimé décision : **450 000** (sur qty reco 25 ; simu 30 → 486 000)

### Traçabilité

Champ `raisons[]`, scores `score_priorite`, `alternative` optionnelle, confiance héritée situation.

---

## 13. Simulation Engine

### Fichier

`backend/app/engines/simulator.py`  
API : `POST/GET /api/simulate`  
UI : `SimulationScreen.tsx` (slider quantité)

### État : 🟢 fonctionnelle (local)

Variables : notamment **quantité** simulée (distribution).  
Sorties : stock/déficit/RaR avant-après, disponibilité, revenu protégé, hypothèses.

---

## 14. AI Layer

### Fichier

`backend/app/engines/ai_layer.py`  
API : `POST/GET /api/ai/explain`  
UI : `ExplanationScreen.tsx`

### Provider

- Compatible **OpenAI Chat Completions**  
- Défaut config : OpenRouter base URL + modèle `openai/gpt-4o-mini`  
- Variables : `OPENAI_API_KEY`, `OPENAI_BASE_URL`, `OPENAI_MODEL`, `AI_ENABLED`

### Règles confirmées code

- Ne calcule pas le RaR  
- Prompt : n’invente pas de chiffres hors contexte JSON engines  
- **Fallback déterministe** si pas de clé / erreur réseau  

### LLM live en production

**NON VÉRIFIÉ** (dépend secret Render / clé locale).

---

## 15. Frontend

### Framework & structure

- React 19 + Vite 8 + TS + Tailwind 4  
- State : `PulseContext` charge executive/decision/simulation  
- API client : `src/lib/api.ts` (`VITE_API_URL` ou relatif + proxy dev)

### Six écrans (confirmés)

| Route | Écran | Fichier |
|-------|-------|---------|
| `/` | Situation exécutive + import CSV | `SituationScreen.tsx` |
| `/investigation` | Investigation risque | `InvestigationScreen.tsx` |
| `/decision` | Decision Engine + export | `DecisionScreen.tsx` |
| `/simulation` | What-if | `SimulationScreen.tsx` |
| `/explication` | IA | `ExplanationScreen.tsx` |
| `/horizon` | Vision | `HorizonScreen.tsx` |

Shell : `TheaterShell.tsx` (parcours scènes, pas navbar SaaS générique).

### Build

`npm run build` → **SUCCESS** (exécuté).  
Bundle JS ~662 KB (warning taille — non bloquant démo).

### UX notes

- UI en français  
- Badge données synthétiques  
- Design palette charcoal/petrol/amber/risk (index.css)

---

## 16. Backend / API

### Entrypoint

`backend/app/main.py` → `app`  
Start prod : `scripts/start-api.sh` → `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### Endpoints (confirmés)

| Méthode | Path |
|---------|------|
| GET | `/api/health` |
| GET/POST | `/api/data/status`, `/reload`, `/preview`, `/upload` |
| GET | `/api/executive` |
| GET | `/api/situations`, `/situations/{id}` |
| GET | `/api/decisions`, `/decisions/{id}` |
| GET/POST | `/api/simulate` |
| GET/POST | `/api/ai/explain` |
| GET/POST | `/api/export/decision` |
| GET | `/api/hypotheses`, `/api/meta` |

### Sécurité API (confirmé code)

- CORS via `CORS_ORIGINS` (défaut `*`)  
- Handlers 404/422 structurés  
- 500 générique : `"Erreur interne du serveur."`  
- Header `X-Request-Id`  
- Upload CSV validé (colonnes obligatoires)

---

## 17. Testing

| Suite | Fichier | Contenu | Exécuté |
|-------|---------|---------|---------|
| Engines | `tests/test_engines.py` | data, executive, demo 486k, decision, simu | 🟢  inclus dans 18 |
| API export/import | `tests/test_api_export_import.py` | health, export, upload, preview | 🟢 |
| E2E navigateur | — | absent | 🔴 |
| CI GitHub Backend | Actions | **Ruff fail** | 🔴 confirmé API jobs |

**Commande vérifiée :**

```bash
DATA_PATH=<repo>/data/sample pytest -q tests
# 18 passed, 1 warning (Starlette/httpx TestClient deprecation)
```

---

## 18. Security

| Sujet | Niveau | Détail | Statut |
|-------|--------|--------|--------|
| Secrets dans Git | — | Aucun secret réel détecté | 🟢 |
| `.env` gitignore | — | présent | 🟢 |
| Clé LLM front | — | seulement `VITE_API_URL` | 🟢 |
| pip-audit requirements | — | clean | 🟢 |
| npm audit react-router | **ÉLEVÉ** | 2 high ; pin 7.18.2 ; dom@8 non trivial | 🟡 accepté hackathon documenté |
| CORS `*` | **MOYEN** | OK local ; restreindre en prod | 🟡 |
| CI Ruff W292 | **ÉLEVÉ** (bloque confiance merge/CI) | newlines + ignore manquant sur tip | 🔴 ouvert |
| Upload multipart | **MOYEN** | validé ; pas d’auth | 🟡 MVP |
| Dependabot RR 8.3 PR#2 | **ÉLEVÉ** si mergé aveugle | peut casser build | 🔴 ne pas merger sans validation |
| Auth utilisateurs | — | absente (MVP démo) | ⚪ attendu hackathon |

---

## 19. Environment Variables & Secrets

| Variable | Côté | Secret ? | Obligatoire prod | Usage |
|----------|------|----------|------------------|--------|
| `VITE_API_URL` | Netlify / front build | Non | **Oui** en prod | Base URL API |
| `DATA_PATH` | Render / backend | Non | Oui | Chemin dataset |
| `CORS_ORIGINS` | Render | Non | Oui (restreint) | CORS |
| `OPENAI_API_KEY` | Render only | **Oui** | Non (fallback) | LLM |
| `OPENAI_BASE_URL` | Render | Non | Non | Provider |
| `OPENAI_MODEL` | Render | Non | Non | Modèle |
| `AI_ENABLED` | Render | Non | Non | Active LLM |
| `API_JSON_LOGS` | Render | Non | Non | Logs |
| `API_HOST` / `API_PORT` | local | Non | Non | Dev ; Render injecte `PORT` |

**Règle :** jamais de clé LLM dans Netlify / bundle front.

`.env.example` : placeholders vides uniquement (vérifié).

---

## 20. Git & Branch Strategy

### Branches (confirmées GitHub)

| Branche | SHA tip | Rôle |
|---------|---------|------|
| **`main`** | `d1e73bb` | Production Git (MVP mergé) |
| **`engineering-lead/mvp-foundation`** | `182347e` | Branche de travail Engineering Lead |
| `dependabot/npm_and_yarn/frontend/react-router-8.3.0` | `ee8a491` | PR #2 OPEN — **ne pas merger sans revue** |
| `arena/019fce79-…` | session agent locale sale possible | **Ne plus utiliser** pour le produit |

### Pull requests

| PR | Titre | État |
|----|-------|------|
| #1 | Merge Engineering foundation MVP | **MERGED** |
| #3 | fix CI Ruff W292 | **MERGED** |
| #2 | dependabot react-router 8.3.0 | **OPEN** |

### Workflow de collaboration (règle projet)

```text
IA workspace → edit réel → test → expliquer fichiers → commandes git
→ Engineering Lead : add / commit / push / PR / merge
→ IA ne push pas sans instruction explicite
```

### Problème récurrent observé (historique session)

- Annonces “fix CI” parfois **incompletes** sur GitHub (newline only / ruff.toml sans `W292` ignore).  
- Workspace agent parfois **désynchronisé** (branche arena dirty).  
- **Source de vérité :** GitHub `main` / `engineering-lead/mvp-foundation`, pas l’état sale d’un sandbox.

### Convention commits

Préfixe observés : `feat:`, `fix:`, `docs:`, `chore:`, `data:`.  
Certains messages bruités (`SituationScreen|Importer...`) — dette process.

---

## 21. Deployment

### Fichiers présents (confirmés)

| Fichier | Rôle |
|---------|------|
| `render.yaml` | Blueprint API |
| `scripts/start-api.sh` | `uvicorn app.main:app` + DATA_PATH |
| `netlify.toml` | base `frontend`, `npm ci && npm run build`, publish `dist` |
| `frontend/public/_redirects` | SPA |
| `docs/DEPLOY.md` | Procédure |
| `setup.md` | Local install/run |

### Live production

| Question | Réponse |
|----------|---------|
| Site Netlify en ligne ? | **NON VÉRIFIÉ** |
| API Render en ligne ? | **NON VÉRIFIÉ** |
| Variables prod configurées ? | **NON VÉRIFIÉ** |

### Ordre déploy recommandé (doc)

1. Render API  
2. Noter URL  
3. Netlify + `VITE_API_URL`  
4. `CORS_ORIGINS` = URL Netlify  
5. Smoke  

### CI vs deploy

Même si le code tourne en local, **CI Backend rouge** sur `main` (Run Ruff) — à corriger **avant** de considérer la qualité “production-ready”.

---

## 22. Documentation

| Document | Objectif | Statut |
|----------|----------|--------|
| `README.md` | Vision produit complète | 🟢 pertinent ; checklist features partiellement obsolète vs code |
| `docs/Mission_2_Cadrage_Finale_Miseàjour.pdf` | Cadrage MVP | 🟢 source vérité fonctionnelle présente |
| `docs/Rôles.docx` | Rôles équipe | 🟢 |
| `docs/ARCHITECTURE.md` | Pipeline technique | 🟢 |
| `setup.md` | Install + run local | 🟢 |
| `docs/DEPLOY.md` | Netlify/Render | 🟢 |
| `docs/ENGINEERING_RUNBOOK.md` | Ops EL | 🟢 |
| `docs/MERGE_TO_MAIN.md` | Merge procedure | 🟢 |
| `docs/SECURITY_NOTES.md` | Deps/security | 🟢 (vérifier alignement pins à chaque release) |
| `Mission_2_…Chapitre9.docx` | — | 🔴 **ABSENT** |
| `13_AI_INSTRUCTIONS.md` | — | 🔴 **ABSENT** |

**Potentiellement obsolète :** cases à cocher README §9 (certaines encore `[ ]` alors que code existe).

---

## 23. Decisions Already Made

| Décision | Pourquoi | Alternatives écartées | Conséquence | Statut |
|----------|----------|----------------------|-------------|--------|
| Architecture A — RaR Decision Engine | Valeur éco + démo + faisabilité | Chatbot, CRM, plateforme large | Focus Smart Distribution | 🟢 actif |
| Business Twin = vision LT | Hors délai MVP | Twin complet maintenant | Écran Horizon seulement | 🟢 |
| IA découplée | Fiabilité calculs | LLM calcule RaR | Fallback sans clé | 🟢 |
| Données synthétiques | Pas de data DABA réelle | Attendre data réelle | Disclaimer obligatoire | 🟢 |
| Monorepo FE/BE | Simplicité hackathon | Multi-repo | package.json racine proxy | 🟢 |
| Netlify + Render | Familiers EL + fit FastAPI | Vercel only, etc. | configs versionnées | 🟢 configs |
| Pas de Postgres MVP | YAGNI démo | Supabase day-1 | DataStore mémoire | 🟢 |
| Engineering Lead contrôle Git push | Intégrité repo | IA push autonome | Workflow commandes pour humain | 🟢 |
| Visibility/Reputation dans RaR | Cadrage Branding | Distribution only | `visibilite_globale.json` + RaR rep | 🟢 code |

---

## 24. Abandoned / Out-of-Scope Ideas (MVP)

Ne **pas** réintroduire comme MVP sans décision explicite :

- CRM complet  
- WhatsApp automation complète  
- Marketing automation complet  
- Marketplace  
- Gestion production complète  
- Business Twin complet  
- Multi-agent autonome  
- Prédiction long terme non validée  
- Intégrations multiples systèmes DABA  
- Refonte de marque comme livrable  

Ces sujets peuvent rester **vision / pitch Horizon**.

---

## 25. Long-Term Vision

Documenté README §15 / PDF :

1. Smart Distribution (MVP)  
2. Demand & Product Intelligence  
3. Customer & Partnership Intelligence  
4. Growth & Conversion Intelligence  
5. Executive Copilot  
6. Growth Memory / Business Twin  

Écosystème croissance (Ferme Expérience, Media Partners, Academy, Club, QR) = post-MVP pitch.

---

## 26. Technical Debt

| ID | Dette | Priorité |
|----|-------|----------|
| TD-01 | CI Ruff W292 : fix incomplet sur tip (ignore manquant + EOF incomplets) | **P0** |
| TD-02 | npm `react-router` high advisories ; pas de dom@8 stable | P1 |
| TD-03 | CORS `*` par défaut prod | P1 avant expose public |
| TD-04 | Bundle JS ~662KB | P2 |
| TD-05 | Pas d’e2e UI | P2 |
| TD-06 | Upload non persisté | P2 |
| TD-07 | Messages commit bruités / process agent désync | P2 |
| TD-08 | README checkboxes pas à jour | P2 |
| TD-09 | Starlette TestClient deprecation warning | P3 |
| TD-10 | Dependabot PR#2 dangereuse si merge auto | P0 process |

---

## 27. Known Problems

### P0 — CI Backend rouge (CONFIRMÉ)

- **Preuve GHA** run `31047894070` sur `main` : failed step **Run Ruff**  
- **Preuve locale** clone `main` : Ruff W292 sur plusieurs fichiers ; pytest 18 OK  
- **Preuve git** : `182347e` n’ajoute **pas** `W292` dans `ignore` (seulement ligne vide) ; plusieurs fichiers **sans** newline finale encore  

### P1 — Deploy live non fait / non vérifié

Configs OK ; URLs prod **NON VÉRIFIÉES**.

### P1 — npm router residual risk

Documenté ; SPA only.

### P2 — RaR réputation vs chiffre pédagogique 64 800

Code cumule facteurs → smoke **129 600**.

### Process

- Ne pas coder depuis workspace agent sur branche `arena/*` dirty.  
- Toujours prouver diff **substantiel vs whitespace**.  
- Toujours vérifier GitHub après push annoncé.

---

## 28. Remaining Work

| ID | Tâche | Priorité | Rôle | Dépendance | État |
|----|-------|----------|------|------------|------|
| T01 | Fix définitif CI Ruff (EOF all files **ou** `ignore = [E501, W292]`) sur **main** + EL | P0 | Engineering | — | 🔴 ouvert (preuves) |
| T02 | Push + confirmer CI verte Backend+Summary | P0 | Engineering | T01 | 🔴 |
| T03 | Ne pas merger Dependabot RR 8.3 sans validation build | P0 | Engineering | — | 🟡 PR open |
| T04 | Deploy Render API | P1 | Engineering | T02 | ⚪ |
| T05 | Deploy Netlify + `VITE_API_URL` | P1 | Engineering | T04 | ⚪ |
| T06 | CORS restreint URL Netlify | P1 | Engineering | T05 | ⚪ |
| T07 | Smoke prod (health, 486k, export, simu, AI fallback) | P1 | Engineering+Product | T05 | ⚪ |
| T08 | Optionnel clé OpenRouter sur Render | P2 | Engineering+AI | T04 | ⚪ |
| T09 | E2E minimal / align README checkboxes | P2 | Engineering/Product | T02 | ⚪ |
| T10 | Calibrage RaR réputation si pitch exige 64.8k | P2 | Data+Engineering | décision produit | ⚪ |
| T11 | Postgres/Supabase | P3/Future | Engineering | post-MVP | ⚪ |
| T12 | Modules Growth/Twin | Future | Product/Growth | post-MVP | ⚪ |

### NEXT — IMMÉDIAT

1. **T01–T02** : CI verte sur `main` (vrai fix W292).  

### NEXT — APRÈS VALIDATION CI

2. **T04–T07** : Render → Netlify → smoke.  

### FUTURE — APRÈS MVP

3. Twin, Growth intelligence, DB, e2e large, router v8 quand `react-router-dom@8` viable.

---

## 29. Engineering Lead Priorities

### P0

1. **Débloquer CI Backend**  
   - **Objectif :** `ruff check app` exit 0 sur GHA  
   - **Fichiers :** tous `backend/app/**/*.py` sans newline EOF ; **et/ou** `backend/ruff.toml` → `ignore = ["E501", "W292"]`  
   - **Validation :** Actions Backend 🟢 + Summary 🟢 sur `main`  
   - **Attention :** le commit `182347e` **n’a pas suffi** (prouvé)

2. **Geler Dependabot PR#2** jusqu’à test manuel build

### P1

3. Deploy Render (`docs/DEPLOY.md`)  
4. Deploy Netlify + env  
5. CORS + smoke démo jury  

### P2

6. Documentation README sync  
7. Observabilité / perf bundle  
8. Tests e2e légers  

### Hors scope immédiat

- Nouvelles features métier  
- Business Twin  
- CRM / WhatsApp / marketplace  

---

## 30. Immediate Next Action

**PROCHAINE ACTION IMMÉDIATE :**

> Sur la branche de travail Engineering (`engineering-lead/mvp-foundation` puis `main`), **corriger définitivement l’échec CI “Run Ruff”** en (1) ajoutant les newlines EOF manquantes sur **tous** les modules Python listés par Ruff **et** (2) ajoutant `W292` à `ignore` dans `backend/ruff.toml` pour stabiliser, puis **pousser**, **vérifier Actions vertes**, ensuite seulement Deploy Render/Netlify.

Ne pas commencer le deploy cloud tant que Backend CI est rouge (sauf décision explicite d’ignorer CI).

---

## 31. Project Continuity Rules

1. **Ne pas inventer** — marquer NON VÉRIFIÉ.  
2. **Preuve fichier** — une implémentation = diff réel (distinguer substantiel vs whitespace).  
3. **Source de vérité Git** = GitHub `main` / `engineering-lead/mvp-foundation`, pas un sandbox arena sale.  
4. **Engineering Lead** contrôle `git push` / merge / secrets cloud.  
5. **IA workspace** : edit → test → expliquer → donner commandes → attendre validation.  
6. **Pas de push IA** sans ordre explicite.  
7. **Après push annoncé** : vérifier `git show origin/...:path` contenu, pas seulement le message.  
8. **MVP chain** avant polish P3.  
9. **IA ≠ calcul RaR**.  
10. **Données synthétiques** toujours labelisées.  
11. **Une unité traçable** à la fois (IMPLEMENTATION #N).  
12. **STOP** si secret, régression critique, écart cadrage majeur.

---

## 32. Context for the Next AI

Tu travailles sur **DabaPulse**, monorepo GitHub `Stane316/daba-pulse`.

**Produit :** MVP Revenue-at-Risk Decision Engine (Smart Distribution) pour DABA SAS.  
**Utilisateur :** Engineering Lead (architecture, backend, Git, deploy, qualité).  
**Branches :**  
- prod Git : **`main`** (`d1e73bb` au moment de ce rapport)  
- travail EL : **`engineering-lead/mvp-foundation`** (`182347e`)  

**Déjà livré et vérifié localement :** data synthétique, risk/RaR (démo 486k), decision, simulation, FastAPI, React 6 écrans, AI fallback, export, import CSV, configs Netlify/Render, docs setup/deploy/merge/security.

**Bloquant actuel :** GitHub Actions **Backend / Run Ruff** échoue encore sur W292 malgré merges de “fix CI” ; pytest passe (18). Deploy cloud **non vérifié**.

**Interdit MVP :** CRM, WhatsApp automation, marketplace, Business Twin complet, multi-agent, etc.

**Workflow :** modifications réelles dans workspace → tests → rapport fichiers → commandes git pour l’humain → pas de push autonome → vérifier GitHub après push.

**Prochaine tâche :** fix CI Ruff définitif → CI verte → Render → Netlify → smoke prod.

Lis d’abord : `README.md`, `setup.md`, `docs/DEPLOY.md`, `docs/MERGE_TO_MAIN.md`, `docs/SECURITY_NOTES.md`, `docs/Mission_2_Cadrage_Finale_Miseàjour.pdf`, ce handover.

---

## 33. Reusable Handover Prompt

```text
Tu reprends le développement du projet DabaPulse (GitHub Stane316/daba-pulse).

Lis obligatoirement :
- docs/PROJECT_HANDOVER_CONTINUITY_REPORT.md (ce handover)
- README.md, setup.md, docs/DEPLOY.md, docs/MERGE_TO_MAIN.md, docs/SECURITY_NOTES.md
- docs/Mission_2_Cadrage_Finale_Miseàjour.pdf

Règles :
1. Ne recommence pas le projet. Vérifie d’abord l’état réel GitHub (main + engineering-lead/mvp-foundation).
2. Ne déclare rien “implémenté” sans preuve fichier/diff/test.
3. Distingue changements substantiels vs whitespace.
4. L’utilisateur est Engineering Lead : tu proposes les commandes git ; tu ne push pas sans ordre.
5. MVP = RaR + Decision + What-if + AI explanation + Smart Distribution. Pas de CRM/Twin/marketplace.
6. IA ne calcule pas le RaR ; fallback sans LLM obligatoire.
7. Une implémentation = une unité traçable (objectif, fichiers, tests, commandes git, prochaine action).

État connu au handover :
- MVP code mergé dans main, scénario 8/35/27/486000 OK en local, pytest 18 OK, front build OK.
- CI Backend encore rouge (Ruff W292). Deploy Netlify/Render non vérifié live.
- Prochaine action : fix CI définitif puis deploy.

Avant de coder : git fetch, checkout engineering-lead/mvp-foundation, git status, reproduire ruff/pytest comme GitHub Actions, puis corriger uniquement le bloquant P0.
```

---

## 34. Final Project Status

| Dimension | Statut |
|-----------|--------|
| **Code MVP** | 🟢 Présent sur `main`, démo locale OK |
| **Qualité CI** | 🔴 Backend Ruff fail sur `main` (confirmé) |
| **Sécurité secrets** | 🟢 Pas de secret réel dans Git |
| **Sécurité deps** | 🟡 pip clean ; npm router high résiduel |
| **Documentation ops** | 🟢 setup/deploy/merge présents |
| **Deploy production** | ⚪ NON VÉRIFIÉ |
| **Prêt jury local** | 🟢 si run via `setup.md` |
| **Prêt jury cloud** | 🟡 après CI verte + Render/Netlify + smoke |
| **Prêt “prod enterprise”** | 🔴 non (auth, DB, CVE npm, hardening) |

### Phrase de passation

> **DabaPulse a un MVP décisionnel complet et démontrable en local, déjà fusionné dans `main`, mais la CI backend échoue encore sur Ruff (newlines), et le déploiement Netlify/Render n’est pas vérifié. La reprise doit d’abord verdir la CI, puis déployer, sans élargir le scope MVP.**

---
