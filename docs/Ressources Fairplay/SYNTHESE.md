# SYNTHESE RESSOURCES FAIRPLAY — DABAPULSE
**Niveau A/B/C — 18 août 2026 — Engineering Lead — Branch `engineering-lead/mvp-foundation`**

> **Objectif :** Rendre les 5 ressources Fairplay (692K) exploitables par `Data Lead` et `AI Lead` sans développer de CRM ou d'IoT. 1 page = 1 vérité traçable.

---

## 1. TABLE NIVEAU A/B/C

| Décision Produit | Niveau | Source | Preuve | Alimente |
|------------------|--------|--------|--------|----------|
| DABA a 5 points de vente (B001-B005) | **A** | `Audit Digital` + `meta.json` | `boutiques.csv` 5 lignes | Smart Distribution |
| Demande/stock désalignés → 486k | **A** + **B** | `ventes_stocks.csv` 631 lignes + `risk_engine.py:27×18000` | `B001 8<35` | Risk Engine |
| RaR réputation `0.40` = 129 600 | **A** | `Audit Digital` 7 menaces + `visibilite_globale.json` (note 2.5, 3 avis, engagement 0.8%) | `1200×0.015×18000×0.40` | `risk_engine.py:visibilite` |
| Simulation `8→38` | **A** | Cadrage What-if | `simulator.py` | Preuve avant/après |
| Suivi commercial à améliorer | **A jaune** | `Audit Digital` `CRM 1/4` | `Base clients 1.5/4` | **Hors MVP** |
| Chaîne du froid critique | **A** | `Audit Énergétique` 1/5 | `délai 3j` | `couverture_jours` (hypothèse) |

**Règle :** `A` (doc) + `B` (proto) = fait ; `C` (décision) = interprétation — jamais présenter `hypothèse` comme `fait DABA`.

---

## 2. AUDIT DIGITAL — 7 MENACES → RA RÉPUTATION

**Fait :** `31.5/96 FAIBLE` (24 critères) — `Invisibilité` 0/4 (pas de site), `Friction` WhatsApp perso, `Érosion` FB 1.5/4, `Vitesse` pub 0/4, `Identité` logo 2/4, `Actif` base 1.5/4, `Traçabilité` QR. **Concurrent :** DABA `✗ site` vs NGA `✓ nga-togo.com` + `Coq Halal` vs Midoum `✓`.

**→ RaR réputation :** `note 2.5 (<3.5)` `0.20` + `engagement 0.8% (<1%)` `0.10` + `absence avis 3` `0.15` + `visibilité 15/j (<30)` `0.10` = **cumul 0.40** → `129 600` (vérifié `smoke.sh`).

**Ne pas développer :** `CRM HubSpot` proposé Table 0 → **hors MVP** (cadrage p.12).

---

## 3. AUDIT ÉNERGÉTIQUE — 20 265 691 kWh → COUVERTURE

**Fait :** `61% Abattoir 12 499 90 + 28% Ferme 5 783 10 + 10% Gaz 1 982 68` + **12 critères 0-2/5** (0 ≥4/5, 8/10 à 0/1) : `Smart metering 0/5 INEXISTANT`, `Isolation 2/5`, `Ventilateurs 1/5 CRITIQUE` etc. **Verdict CRITIQUE**.

**→ DabaPulse :** `stock_cible` / `delai_reappro` (`schemas.py`) + `couverture_jours` = `stock/demande` (hypothèse `saisie différée 3j`). **Ne pas ajouter** `IoT LoRaWAN` (Budget `Équipements Prototypage` hors MVP) — ordre de grandeur `ROI <6 mois` = **hypothèse norme**, pas mesure DABA.

---

## 4. CE QUE DABAPULSE UTILISE / N'UTILISE PAS

| Ressource | Utilisé dans MVP | Hors MVP (vision) |
|-----------|------------------|-------------------|
| `Audit Digital` 7 menaces | `visibilite_globale.json` + `RaR 0.40` | `Site vitrine SEO`, `WhatsApp Business API`, `CRM` |
| `Audit Énergétique` 20M kWh | `delai_reappro` `couverture` | `Smart metering`, `Solaire BLUEN`, `ISO 50001` |
| `Budget` template | — | `Growth Lead` pricing |
| `Plan 18/08` refonte | `6 écrans` `Signal→Impact` | `Business Twin` |

**Check 18/08 :** `6 écrans fonctionnels ✓`, `risque 486k ✓`, `IA fallback ✓`, `Light/Dark ✓`, `tunnel 18s ✓` — **prêt pour `19/08 DEPLOY`**.

---

## 5. LIEN VERS LE CODE

- `HYPOTHESES 1.0.0` (`backend/app/core/config.py`) — versionnées
- `visibilite_globale.json` (`note 2.5, nb_avis 3, engagement 0.008, visiteurs 1200`)
- `risk_engine.py` `facteur_risque 0.40`
- `Document d'équipe §1` `Niveau A/B/C`
