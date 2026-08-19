# Données synthétiques de démonstration

> ⚠️ **Ces fichiers sont 100 % synthétiques.**  
> Ils ne représentent **pas** les opérations réelles de DABA SAS.

## Contenu (INCREMENT B — 20 août 2026)

| Fichier | Description |
|---------|-------------|
| `growth_decision_os.db` | **Base SQLite** du dataset (chargée en priorité par l'API) — tables `ventes` (6 720 lignes), `boutiques`, `produits`, `visibilite`, `meta` |
| `ventes_stocks.csv` | Historique ventes / stocks — **6 721 lignes** (5 boutiques × 16 produits × 84 jours, seed 42) |
| `boutiques.csv` | Référentiel points de vente (B001–B005) |
| `produits.csv` | Référentiel produits avicoles (P001–P016) |
| `visibilite_globale.json` | Indicateurs réputation / visibilité entreprise |
| `meta.json` | Métadonnées + scénario de démo + format (CSV/SQLite) |

**Volume :** 6 720 lignes d'historique — 5 boutiques × 16 produits × 84 jours (28/05 → 19/08/2026), générées avec `seed 42` (reproductible).

## Scénario prioritaire (préservé)

- **Boutique** : DABA Plateau (`B001`)
- **Produit** : Poulet entier premium 1,5 kg (`P005`)
- **Stock** : 8 · **Demande 7j** : 35 · **Déficit** : 27
- **RaR** : 27 × 18 000 = **486 000 FCFA** (situation #1 — aucune autre ne la dépasse)
- **Source de réallocation** : DABA Cocody (`B002`, surplus 25 u → recommandation 25 u)

## Régénération

```bash
python scripts/generate_synthetic_data.py
```

Régénère les CSV + la base SQLite (identique : seed 42).
