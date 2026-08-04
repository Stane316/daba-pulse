# Architecture DabaPulse

## Pipeline

```text
CSV synthétique
    → Data Validation
    → Analytics Engine
    → Risk Engine
    → Revenue-at-Risk
    → Decision Engine
    → What-if Simulator
    → FastAPI
    → React Decision Theater
    → AI Explanation Layer (optionnel)
```

## Backend (`backend/app`)

| Module | Rôle |
|--------|------|
| `engines/data_loader.py` | Charge CSV/JSON, valide, expose le store |
| `engines/analytics.py` | Demande, tendance, couverture, mini-vue |
| `engines/risk_engine.py` | Détection risques + calcul RaR |
| `engines/decision_engine.py` | Recommandations déterministes |
| `engines/simulator.py` | Comparaison avant / après |
| `engines/ai_layer.py` | Explication + Q&A (fallback sans LLM) |
| `api/routes.py` | Endpoints REST |
| `core/config.py` | Settings + hypothèses versionnées |

## Frontend (`frontend/src`)

Six scènes du Decision Theater :

1. Situation exécutive
2. Investigation du risque
3. Decision Engine
4. What-if Simulator
5. Explication IA
6. Growth Horizon

La logique métier reste côté backend. Le frontend consomme `/api/*`.

## Formules

### Distribution

```text
RaR = max(0, demande_attendue − stock) × prix_unitaire
```

### Réputation

```text
RaR = visiteurs × conversion × prix_moyen × horizon × facteur_risque
```

Facteurs (cumulatifs) : note < 3,5 → 0,20 ; engagement < 1 % → 0,10 ; absence d'avis → 0,15 ; faible visibilité → 0,10.

## Données

Jeu **100 % synthétique** dans `data/sample/`.  
Ne jamais présenter comme données réelles DABA.

Régénération :

```bash
python scripts/generate_synthetic_data.py
```
