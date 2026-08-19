"""
GROWTH DECISION OS / DabaPulse — API FastAPI
==============================================

Expose risk_engine.py au frontend React. N'implémente AUCUNE logique
métier ici — ce fichier ne fait que charger l'état depuis la base et
appeler les fonctions de risk_engine.py. Toute règle métier reste dans
risk_engine.py (source unique de vérité).

Lancement local :
    pip install fastapi uvicorn --break-system-packages
    uvicorn api:app --reload --port 8000

Puis ouvrir http://127.0.0.1:8000/docs pour tester interactivement
(Swagger UI généré automatiquement par FastAPI).

Variable d'environnement optionnelle :
    DABAPULSE_DB_PATH  -> chemin vers growth_decision_os.db
                           (par défaut : dataset_output/growth_decision_os.db)
"""

import os
from datetime import date
from functools import lru_cache

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from risk_engine import (
    charger_etat_depuis_sqlite,
    generer_rapport,
    _finaliser_rapport,
    simuler,
    simuler_trois_scenarios,
    evaluer_sante_donnees,
)

DB_PATH = os.environ.get("DABAPULSE_DB_PATH", "dataset_output/growth_decision_os.db")

app = FastAPI(
    title="DabaPulse — Risk Engine API",
    description="Expose le Revenue-at-Risk Decision Engine (détection, simulation) au frontend.",
    version="0.1.0",
)

# CORS ouvert en développement (React tourne sur un port différent de l'API).
# À restreindre à l'URL de prod (Netlify) avant le dépôt final.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ------------------------------------------------------------------
# Chargement de l'état — mis en cache pour éviter de relire la base
# à chaque requête. /admin/reload-cache permet de forcer un rechargement
# après une régénération du dataset.
# ------------------------------------------------------------------

@lru_cache(maxsize=1)
def _etat_cache():
    return charger_etat_depuis_sqlite(DB_PATH)


def _date_reference(etat):
    return max(date.fromisoformat(v["date"]) for v in etat["ventes"])


# ------------------------------------------------------------------
# Schémas de requête (validation automatique par Pydantic/FastAPI)
# ------------------------------------------------------------------

class ActionTransfert(BaseModel):
    store_source: int
    store_destination: int
    product_id: int
    quantite: int


# ------------------------------------------------------------------
# Endpoints
# ------------------------------------------------------------------

@app.get("/api/health")
def health():
    """Vérifie que l'API répond et que la base est lisible."""
    try:
        etat = _etat_cache()
        return {
            "statut": "ok",
            "db_path": DB_PATH,
            "nb_ventes": len(etat["ventes"]),
            "nb_boutiques": len(etat["boutiques"]),
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Base illisible : {e}")


@app.post("/api/admin/reload-cache")
def reload_cache():
    """À appeler après une régénération du dataset (generate_dataset.py + load_dataset.py)."""
    _etat_cache.cache_clear()
    etat = _etat_cache()
    return {"statut": "cache rechargé", "nb_ventes": len(etat["ventes"])}


@app.get("/api/data-health")
def data_health():
    """
    Badge de statut global du dataset — Écran 'Executive Situation'.
    À afficher AVANT toute recommandation, pour que le jury voie tout de
    suite si les données sont fraîches/complètes ou non.
    """
    etat = _etat_cache()
    ref_date = _date_reference(etat)
    return evaluer_sante_donnees(etat, ref_date, type_donnees="synthetique")


@app.get("/api/rapport")
def rapport():
    """
    Endpoint principal — Écran 'Risk Investigation' / 'Decision Engine'.
    Retourne toutes les recommandations, triées par Revenue-at-Risk décroissant,
    avec le statut des données (synthétique/réel) toujours visible.
    """
    etat = _etat_cache()
    ref_date = _date_reference(etat)
    return _finaliser_rapport(generer_rapport(etat, ref_date, type_donnees="synthetique"))


@app.get("/api/rapport/{store_id}/{product_id}")
def rapport_detail(store_id: int, product_id: int):
    """Détail d'une recommandation précise — Écran 'Risk Investigation'."""
    rapport_complet = rapport()
    for r in rapport_complet["recommandations"]:
        if r["store_id"] == store_id and r["product_id"] == product_id:
            return r
    raise HTTPException(status_code=404, detail="Aucun risque détecté pour ce couple boutique/produit.")


@app.post("/api/simulation")
def simulation(action: ActionTransfert):
    """
    Écran 'What-if Simulator' — un scénario manuel.
    Retourne l'état AVANT/APRÈS (Revenue-at-Risk, nombre de risques) pour
    l'action de transfert proposée par le frontend.
    """
    etat = _etat_cache()
    ref_date = _date_reference(etat)
    action_dict = {"type": "transfert", **action.model_dump()}
    resultat = simuler(action_dict, etat, ref_date)
    resultat["type"] = "transfert"
    return resultat


@app.post("/api/simulation/scenarios")
def simulation_scenarios(action: ActionTransfert):
    """
    Écran 'What-if Simulator' — les 3 scénarios automatiques
    (prudent / équilibré / agressif), dérivés de l'action de base fournie.
    """
    etat = _etat_cache()
    ref_date = _date_reference(etat)
    action_dict = {"type": "transfert", **action.model_dump()}
    resultats = simuler_trois_scenarios(action_dict, etat, ref_date)
    return {
        nom: {k: v for k, v in res.items() if k != "risques_apres"}
        for nom, res in resultats.items()
    }


@app.get("/api/boutiques")
def boutiques():
    """Référentiel boutiques — pour peupler les filtres/menus du frontend."""
    etat = _etat_cache()
    return [{"store_id": sid, **infos} for sid, infos in etat["boutiques"].items()]


@app.get("/api/produits")
def produits():
    """Référentiel produits — pour peupler les filtres/menus du frontend."""
    etat = _etat_cache()
    return [{"product_id": pid, **infos} for pid, infos in etat["produits"].items()]
