# DabaPulse — Setup & exécution locale

Guide pour **toute personne** qui ouvre le dépôt pour la première fois  
et pour **relancer** le projet au quotidien.

> Stack : React (Vite) + FastAPI + données synthétiques `data/sample`  
> OS documenté en priorité : **Windows + PowerShell**  
> Linux/macOS : mêmes étapes avec `source .venv/bin/activate` et `/` dans les chemins.

---

# Partie A — Guide d’installation (première fois)

## A0. Prérequis à installer sur la machine

| Outil | Version | Vérification PowerShell |
|-------|---------|-------------------------|
| Git | 2.x | `git --version` |
| Python | 3.11+ (3.12 recommandé) | `py -3 --version` ou `python --version` |
| Node.js | 20 LTS | `node --version` |
| npm | 10+ | `npm --version` |

### Windows — points d’attention

1. À l’installation de Python : cocher **Add python.exe to PATH**.
2. Si `Python was not found` : désactiver les alias Microsoft Store  
   (*Paramètres → Applications → Alias d’exécution d’application* → `python.exe` / `python3.exe` OFF).
3. Autoriser l’activation des venv PowerShell (une fois) :

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

4. Fins de ligne Git (recommandé, une fois) :

```powershell
git config --global core.autocrlf false
git config --global core.eol lf
```

---

## A1. Cloner le dépôt

```powershell
cd C:\Users\HP\Downloads
git clone https://github.com/Stane316/daba-pulse.git
cd daba-pulse
```

Si le dépôt est déjà cloné :

```powershell
cd C:\Users\HP\Downloads\daba-pulse
git fetch origin
```

---

## A2. Se placer sur la branche de travail

```powershell
git checkout engineering-lead/mvp-foundation
git pull origin engineering-lead/mvp-foundation
git log -3 --oneline
git status
```

Branche stable de développement Engineering :  
`engineering-lead/mvp-foundation`

---

## A3. Backend — environnement Python

```powershell
cd C:\Users\HP\Downloads\daba-pulse

py -3 -m venv .venv
# si py ne marche pas :
# python -m venv .venv

.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
python -m pip install -r backend\requirements.txt
```

Le prompt doit afficher `(.venv)`.

---

## A4. Frontend — dépendances Node

```powershell
cd C:\Users\HP\Downloads\daba-pulse\frontend
npm ci
```

Si `npm ci` échoue :

```powershell
npm install
```

---

## A5. Configuration environnement

```powershell
cd C:\Users\HP\Downloads\daba-pulse
copy .env.example .env
```

Éditer `.env` si besoin (`notepad .env`).

| Variable | Première install (local) |
|----------|---------------------------|
| `DATA_PATH` | Chemin absolu vers `data\sample` (recommandé) |
| `CORS_ORIGINS` | `*` |
| `VITE_API_URL` | **vide** (le proxy Vite envoie `/api` → port 8000) |
| `OPENAI_API_KEY` | **vide** OK (fallback IA sans LLM) |
| `OPENAI_BASE_URL` | ex. OpenRouter si tu as une clé |
| `AI_ENABLED` | `true` |

Exemple Windows pour `DATA_PATH` :

```env
DATA_PATH=C:\Users\HP\Downloads\daba-pulse\data\sample
```

**Ne jamais committer le fichier `.env`** (secrets).

---

## A6. Vérifier que les données sample existent

```powershell
cd C:\Users\HP\Downloads\daba-pulse
Get-ChildItem data\sample
```

Fichiers attendus au minimum :

- `ventes_stocks.csv`
- `boutiques.csv`
- `produits.csv`
- `visibilite_globale.json`
- `meta.json`

Régénération optionnelle :

```powershell
.\.venv\Scripts\Activate.ps1
python scripts\generate_synthetic_data.py
```

---

## A7. Tests d’installation (optionnel mais recommandé)

```powershell
cd C:\Users\HP\Downloads\daba-pulse
.\.venv\Scripts\Activate.ps1
$env:DATA_PATH = "$PWD\data\sample"
cd backend
python -m pytest -q ..\tests
```

Attendu : tests verts (ex. `18 passed`).

Frontend :

```powershell
cd C:\Users\HP\Downloads\daba-pulse\frontend
npm run typecheck
```

---

# Partie B — Guide d’exécution (à chaque session)

Deux terminaux séparés : **API** puis **Frontend**.

## B1. Terminal API (backend)

```powershell
cd C:\Users\HP\Downloads\daba-pulse
.\.venv\Scripts\Activate.ps1
$env:DATA_PATH = "$PWD\data\sample"
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Succès attendu :

```text
Uvicorn running on http://0.0.0.0:8000
Application startup complete
```

Laisser ce terminal **ouvert**.

| URL | Rôle |
|-----|------|
| http://127.0.0.1:8000/api/health | Santé API |
| http://127.0.0.1:8000/docs | Documentation interactive |

Test rapide (3ᵉ terminal) :

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/health
```

---

## B2. Terminal Frontend

```powershell
cd C:\Users\HP\Downloads\daba-pulse\frontend
npm run dev -- --host 0.0.0.0 --port 5173
```

Succès attendu :

```text
VITE v8.x ready
Local: http://localhost:5173/
```

Ouvrir le navigateur : **http://localhost:5173/**

---

## B3. Parcours de démo dans le navigateur

1. `/` — **Situation** : Revenue-at-Risk, liste des risques, import CSV optionnel  
2. `/investigation` — causes du risque  
3. `/decision` — recommandation + **export résumé** (.md / JSON)  
4. `/simulation` — before/after, slider quantité  
5. `/explication` — IA (fallback sans clé API)  
6. `/horizon` — vision future  

Scénario cible :

| Indicateur | Valeur |
|------------|--------|
| Boutique | DABA Plateau |
| Produit | Poulet premium |
| Stock / Demande / Déficit | 8 / 35 / 27 |
| Revenue-at-Risk | **486 000 FCFA** |

---

## B4. Arrêter les serveurs

Dans chaque terminal : `Ctrl + C`.

---

## B5. Commandes utiles du quotidien

| Besoin | Commande |
|--------|----------|
| Activer le venv | `.\.venv\Scripts\Activate.ps1` |
| Tests backend | `cd backend ; python -m pytest -q ..\tests` |
| Build frontend | `cd frontend ; npm run build` |
| Recharger données sample (API allumée) | `Invoke-RestMethod -Method Post http://127.0.0.1:8000/api/data/reload` |
| Export démo JSON | navigateur → Décision → Exporter JSON  
| ou | `Invoke-WebRequest "http://127.0.0.1:8000/api/export/decision/dist-B001-P005?format=markdown" -OutFile "$env:USERPROFILE\Downloads\dabapulse.md"` |

---

## B6. Linux / macOS (résumé)

```bash
cd ~/daba-pulse
git checkout engineering-lead/mvp-foundation
git pull origin engineering-lead/mvp-foundation

python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt

cd frontend && npm ci && cd ..
cp .env.example .env

# Terminal 1
export DATA_PATH="$(pwd)/data/sample"
cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2
cd frontend && npm run dev -- --host 0.0.0.0 --port 5173
```

---

## B7. Dépannage rapide

| Problème | Solution |
|----------|----------|
| `Python was not found` | PATH Python + désactiver alias Store |
| `Activate.ps1` refusé | `Set-ExecutionPolicy RemoteSigned` (CurrentUser) |
| `No module named app.models` | Pull dernière branche ; vérifier `backend/app/models/schemas.py` |
| Port 8000 occupé | Fermer l’ancien uvicorn ou changer de port |
| Front ne joint pas l’API | API allumée sur 8000 ; `VITE_API_URL` vide en local |
| Warning CRLF Git | Normal une fois sous Windows ; voir `.gitattributes` |
| IA “indisponible” | Normal sans `OPENAI_API_KEY` — fallback actif |

---

## B8. Documentation liée

| Fichier | Contenu |
|---------|---------|
| `README.md` | Vision produit |
| `docs/ENGINEERING_RUNBOOK.md` | Détails Engineering, CI, déploiement |
| `docs/ARCHITECTURE.md` | Pipeline technique |
| `.env.example` | Variables d’environnement |

---

**DabaPulse** — From business signals to better decisions.