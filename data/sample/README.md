# Données synthétiques de démonstration

> ⚠️ **Ces fichiers sont 100 % synthétiques.**  
> Ils ne représentent **pas** les opérations réelles de DABA SAS.

## Contenu

| Fichier | Description |
|---------|-------------|
| `ventes_stocks.csv` | Historique ventes / stocks (5 boutiques × 6 produits × 21 j) |
| `boutiques.csv` | Référentiel points de vente |
| `produits.csv` | Référentiel produits avicoles |
| `visibilite_globale.json` | Indicateurs réputation / visibilité entreprise |
| `meta.json` | Métadonnées + scénario de démo |

## Scénario prioritaire

- **Boutique** : DABA Plateau (`B001`)
- **Produit** : Poulet entier premium 1,5 kg (`P005`)
- **Stock** : 8 · **Demande 7j** : 35 · **Déficit** : 27
- **RaR** : 27 × 18 000 = **486 000 FCFA**
- **Source de réallocation** : DABA Cocody (`B002`, surplus)

## Régénération

```bash
python scripts/generate_synthetic_data.py
```
