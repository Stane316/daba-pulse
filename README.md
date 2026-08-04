Oui. Et je corrige d'abord un point important : **le nom actuel de la plateforme est DabaPulse**, pas Daba Intelligence. Le nom pourra évoluer plus tard, mais le repository doit maintenant refléter ce nom de travail.

J'ai aussi recroisé le README avec le cadrage final de l'équipe : le cœur est bien le **Revenue-at-Risk Decision Engine + Smart Distribution**, avec le Business Twin comme vision long terme, et non un dashboard générique.  La stack recommandée est React/Vite/Tailwind côté frontend, Python/FastAPI côté backend, Pandas/NumPy pour la data, avec Risk Engine, Decision Engine, simulation et couche IA découplée. 

Voici donc le **README.md complet**, prêt à copier-coller.

````markdown
# DabaPulse

> **Turn business signals into decisions. Protect revenue before it's lost.**

DabaPulse est une plateforme d'intelligence décisionnelle conçue dans le cadre de la **Mission 2 — Branding & Growth** du hackathon Startup FairPlay.

Son objectif est de transformer des données opérationnelles en décisions concrètes permettant d'identifier les situations où du revenu est potentiellement exposé, d'estimer cette exposition financière, de recommander une action prioritaire et d'en simuler l'impact avant décision.

Le MVP est conçu autour du cas d'usage **Smart Distribution** appliqué au contexte de DABA SAS.

---

## Table of Contents

- [1. Vision](#1-vision)
- [2. Le problème](#2-le-problème)
- [3. La solution](#3-la-solution)
- [4. Le cœur du MVP](#4-le-cœur-du-mvp)
- [5. Revenue-at-Risk](#5-revenue-at-risk)
- [6. Fonctionnement](#6-fonctionnement)
- [7. Architecture](#7-architecture)
- [8. Stack technique](#8-stack-technique)
- [9. Fonctionnalités du MVP](#9-fonctionnalités-du-mvp)
- [10. Parcours de démonstration](#10-parcours-de-démonstration)
- [11. Les six écrans](#11-les-six-écrans)
- [12. Données](#12-données)
- [13. Rôle de l'IA](#13-rôle-de-lia)
- [14. Ce qui n'est pas dans le MVP](#14-ce-qui-nest-pas-dans-le-mvp)
- [15. Vision long terme](#15-vision-long-terme)
- [16. Organisation de l'équipe](#16-organisation-de-léquipe)
- [17. Workflow Git](#17-workflow-git)
- [18. Structure du repository](#18-structure-du-repository)
- [19. Roadmap](#19-roadmap)
- [20. Principes de développement](#20-principes-de-développement)
- [21. Limites et transparence](#21-limites-et-transparence)
- [22. Documentation](#22-documentation)
- [23. Statut du projet](#23-statut-du-projet)
- [24. Équipe](#24-équipe)
- [25. Licence](#25-licence)

---

# 1. Vision

Les entreprises disposent souvent de nombreuses données :

- ventes ;
- stocks ;
- produits ;
- points de vente ;
- disponibilité ;
- prix ;
- historique des transactions.

Mais disposer de données ne signifie pas nécessairement savoir **quoi décider**.

DabaPulse part d'une idée simple :

> **Un système de pilotage utile ne doit pas seulement montrer ce qui se passe. Il doit aider à comprendre ce qui risque de coûter de l'argent, décider quoi faire et mesurer l'impact de cette décision.**

La boucle fondamentale du produit est :

```text
DONNÉES
   ↓
OBSERVER
   ↓
COMPRENDRE
   ↓
DÉCIDER
   ↓
AGIR
   ↓
MESURER
   ↓
APPRENDRE
````

Le MVP se concentre volontairement sur une partie précise de cette boucle afin de démontrer une valeur économique claire.

---

# 2. Le problème

Le problème ciblé par le MVP n'est pas :

> « DABA a besoin d'un dashboard. »

Il n'est pas non plus :

> « DABA a besoin d'une IA. »

Le problème est opérationnel et économique :

> **Une entreprise peut disposer de produits, de stocks, de points de vente et d'historique de ventes sans disposer d'un mécanisme suffisamment direct pour détecter une situation de désalignement et déterminer quelle action de distribution permettrait de protéger le revenu.**

Le MVP cherche donc à répondre à une question précise :

> **Quel produit doit être envoyé, dans quelle quantité, vers quel point de vente et à quel moment afin de réduire le revenu actuellement exposé ?**

Cette question constitue le cœur du cas d'usage **Smart Distribution**.

---

# 3. La solution

DabaPulse est un moteur d'intelligence décisionnelle qui :

1. collecte et valide les données disponibles ;
2. analyse les ventes, stocks et disponibilités ;
3. détecte les situations présentant un risque ;
4. estime le revenu potentiellement exposé ;
5. identifie les situations prioritaires ;
6. recommande une action ;
7. explique quantitativement cette recommandation ;
8. permet de tester cette décision dans un scénario hypothétique ;
9. estime le revenu potentiellement protégé ;
10. fournit une explication en langage naturel lorsque la couche IA est disponible.

En une phrase :

> **DabaPulse identifie où une entreprise risque de perdre du revenu, explique pourquoi, recommande quoi faire et permet de simuler l'impact avant d'agir.**

---

# 4. Le cœur du MVP

Le MVP est construit autour de :

```text
Smart Distribution
        +
Revenue-at-Risk
        +
Decision Engine
        +
What-if Simulation
```

Le système ne cherche donc pas à construire une plateforme exhaustive.

Il cherche à démontrer une transformation précise :

```text
Signal opérationnel
        ↓
Risque financier
        ↓
Décision
        ↓
Simulation
        ↓
Impact économique
```

### Principe central

> **Un dashboard montre le problème. DabaPulse estime ce qu'il peut coûter et aide à décider quoi faire.**

---

# 5. Revenue-at-Risk

Le **Revenue-at-Risk** constitue l'un des éléments centraux du MVP.

Il représente une estimation du revenu potentiellement exposé lorsqu'une situation opérationnelle peut empêcher une vente attendue.

Exemple illustratif :

```text
Demande attendue        : 35 unités
Stock disponible        : 8 unités
Déficit potentiel       : 27 unités
Prix unitaire net       : 18 000 FCFA

Revenue-at-Risk estimé
= 27 × 18 000
= 486 000 FCFA
```

> Les chiffres ci-dessus sont uniquement illustratifs et ne représentent pas des données réelles de DABA.

Le système doit également conserver les hypothèses utilisées dans le calcul.

L'objectif n'est pas de produire un chiffre spectaculaire.

L'objectif est de produire un chiffre :

* traçable ;
* explicable ;
* reproductible ;
* associé à des données ;
* associé à un niveau de confiance.

---

# 6. Fonctionnement

Le pipeline principal de DabaPulse est :

```text
CSV / données simulées
        ↓
Data Validation
        ↓
Analytics Engine
        ↓
Risk Engine
        ↓
Revenue-at-Risk
        ↓
Decision Engine
        ↓
What-if Simulator
        ↓
FastAPI
        ↓
React Dashboard
        ↓
AI Explanation Layer
```

Chaque couche possède une responsabilité distincte.

---

## 6.1 Data Validation

Cette couche :

* importe les données ;
* vérifie les colonnes ;
* détecte les valeurs manquantes ;
* vérifie les types ;
* contrôle les incohérences ;
* prépare les données pour l'analyse.

---

## 6.2 Analytics Engine

Cette couche calcule les indicateurs nécessaires :

* ventes ;
* stock ;
* demande ;
* disponibilité ;
* déficit ;
* valorisation ;
* tendances utiles au MVP.

---

## 6.3 Risk Engine

Le Risk Engine détecte notamment :

* risques de rupture ;
* stock insuffisant ;
* surstock ;
* demande forte ;
* demande croissante ;
* désalignements entre demande et disponibilité.

Il transforme ces signaux en situations de risque exploitables.

---

## 6.4 Revenue-at-Risk Engine

Le moteur estime la valeur financière associée à chaque situation de risque.

Le résultat doit toujours être relié à :

* une situation ;
* un produit ;
* un point de vente ;
* une hypothèse ;
* des données ;
* un niveau de confiance.

---

## 6.5 Decision Engine

Le Decision Engine transforme les risques en actions prioritaires.

Il répond notamment à :

* **quoi ?**
* **où ?**
* **combien ?**
* **pourquoi ?**
* **avec quel niveau de confiance ?**

Il classe les actions selon leur priorité.

---

## 6.6 What-if Simulator

Le simulateur permet de tester une décision avant de la considérer comme appliquée.

Exemple :

```text
AVANT

Stock : 8
Déficit potentiel : 27
Revenue-at-Risk : 486 000 FCFA
```

Puis :

```text
SCÉNARIO

Réallocation : +30 unités
```

Et enfin :

```text
APRÈS

Stock : 38
Déficit potentiel : 0
Revenue-at-Risk : réduit / supprimé
Revenu potentiellement protégé : calculé
```

Le simulateur ne prétend pas prédire parfaitement le futur.

Il permet d'examiner les conséquences d'une hypothèse donnée.

---

# 7. Architecture

## Architecture cible

```text
┌───────────────────────────────┐
│       Data Sources            │
│ CSV / Synthetic Data / Future │
│ DABA Data                     │
└───────────────┬───────────────┘
                │
                ▼
┌───────────────────────────────┐
│       Data Validation         │
└───────────────┬───────────────┘
                │
                ▼
┌───────────────────────────────┐
│       Analytics Engine        │
└───────────────┬───────────────┘
                │
                ▼
┌───────────────────────────────┐
│         Risk Engine           │
└───────────────┬───────────────┘
                │
                ▼
┌───────────────────────────────┐
│      Revenue-at-Risk          │
└───────────────┬───────────────┘
                │
                ▼
┌───────────────────────────────┐
│       Decision Engine         │
└───────────────┬───────────────┘
                │
                ▼
┌───────────────────────────────┐
│      What-if Simulator        │
└───────────────┬───────────────┘
                │
                ▼
┌───────────────────────────────┐
│          FastAPI              │
└───────────────┬───────────────┘
                │
                ▼
┌───────────────────────────────┐
│       React Dashboard         │
└───────────────┬───────────────┘
                │
                ▼
┌───────────────────────────────┐
│     AI Explanation Layer      │
└───────────────────────────────┘
```

---

## Principe architectural majeur

La logique métier ne doit pas être placée dans le frontend.

Le système doit séparer :

```text
Interface
   ≠
API
   ≠
Business Logic
   ≠
Analytics
   ≠
Simulation
   ≠
AI
```

L'IA doit également être découplée du moteur analytique.

Une absence ou une panne du modèle de langage ne doit pas empêcher :

* le calcul du Revenue-at-Risk ;
* la détection du risque ;
* le classement ;
* la recommandation ;
* la simulation.

---

# 8. Stack technique

| Couche           | Technologie                 | Rôle                          |
| ---------------- | --------------------------- | ----------------------------- |
| Frontend         | React                       | Interface utilisateur         |
| Build            | Vite                        | Développement et build        |
| Styling          | Tailwind CSS                | Interface                     |
| Backend          | Python                      | Logique serveur               |
| API              | FastAPI                     | API et orchestration          |
| Data             | Pandas                      | Manipulation des données      |
| Numerical        | NumPy                       | Calculs numériques            |
| Database         | PostgreSQL / Supabase       | Stockage structuré            |
| Risk Engine      | Python                      | Détection des risques         |
| Decision Engine  | Python                      | Classement et recommandations |
| Simulation       | Python                      | What-if                       |
| AI Layer         | LLM compatible API          | Explication et Q&A            |
| Charts           | Recharts ou équivalent      | Visualisation                 |
| Tests            | pytest                      | Validation                    |
| Versioning       | Git + GitHub                | Collaboration                 |
| Front deployment | Netlify / Vercel            | Déploiement                   |
| API deployment   | Render / Railway / Supabase | Déploiement backend           |

> Cette stack constitue une architecture de réalisation recommandée. Elle ne doit pas être interprétée comme une stack officiellement imposée par le hackathon.

---

# 9. Fonctionnalités du MVP

Le MVP doit permettre :

### Données

* [x] Importer un dataset CSV
* [x] Valider les données
* [x] Afficher un aperçu
* [x] Fonctionner avec des données synthétiques

### Analyse

* [ ] Analyser ventes et stocks
* [ ] Détecter les ruptures potentielles
* [ ] Détecter les situations de surstock
* [ ] Détecter les demandes fortes ou croissantes
* [ ] Identifier les désalignements

### Revenue-at-Risk

* [ ] Calculer le revenu exposé
* [ ] Afficher les hypothèses
* [ ] Associer un niveau de confiance
* [ ] Prioriser les situations

### Décision

* [ ] Recommander une action
* [ ] Identifier le produit
* [ ] Identifier le point de vente
* [ ] Déterminer une quantité
* [ ] Expliquer la priorité
* [ ] Proposer éventuellement une alternative

### Simulation

* [ ] Modifier une quantité
* [ ] Tester un scénario
* [ ] Comparer avant / après
* [ ] Mesurer la variation du risque
* [ ] Estimer le revenu potentiellement protégé

### IA

* [ ] Expliquer une recommandation
* [ ] Répondre aux questions sur les résultats
* [ ] Comparer des scénarios
* [ ] Générer un résumé décisionnel

### Export

* [ ] Exporter un résumé décisionnel lorsque disponible

---

# 10. Parcours de démonstration

La démonstration doit raconter une histoire.

Elle ne doit pas être une visite aléatoire du dashboard.

Le scénario principal est :

```text
SITUATION
   ↓
RISQUE
   ↓
COÛT
   ↓
DÉCISION
   ↓
SIMULATION
   ↓
IMPACT
   ↓
VISION
```

### Scénario

1. Plusieurs boutiques et produits sont affichés.
2. Le système identifie une situation critique.
3. Une boutique présente une demande forte alors que son stock devient insuffisant.
4. DabaPulse calcule le Revenue-at-Risk.
5. Le système explique les facteurs responsables du risque.
6. Le Decision Engine recommande une réallocation.
7. Le responsable teste cette décision.
8. Le simulateur compare la situation avant et après.
9. Le système estime le revenu potentiellement protégé.
10. La couche IA explique la décision.
11. La démonstration se termine par la vision Growth / Business Twin.

---

# 11. Les six écrans

Les six écrans constituent un parcours narratif :

```text
Situation
   ↓
Investigation
   ↓
Decision
   ↓
Simulation
   ↓
AI Explanation
   ↓
Growth Horizon
```

---

## Écran 01 — Executive Situation

### Question

> **Où DABA risque-t-elle de perdre du revenu maintenant ?**

### Objectif

Donner immédiatement au décideur une vision de la situation.

### Contenu

* Revenue-at-Risk total ;
* nombre de situations critiques ;
* liste priorisée ;
* boutique ;
* produit ;
* signal ;
* revenu exposé ;
* niveau de confiance ;
* mini-vue demande / stock / distribution / revenu ;
* filtres ;
* accès à l'investigation.

Les données synthétiques doivent être identifiées discrètement.

---

## Écran 02 — Risk Investigation

### Question

> **Pourquoi cette situation est-elle critique ?**

### Objectif

Transformer le signal en problème compréhensible.

### Contenu

* boutique ;
* produit ;
* horizon ;
* demande attendue ;
* stock disponible ;
* déficit potentiel ;
* prix net ;
* Revenue-at-Risk ;
* drivers du risque ;
* hypothèses ;
* niveau de confiance.

Le décideur doit pouvoir comprendre le risque sans connaître l'architecture technique.

---

## Écran 03 — Decision Engine

### Question

> **Que devons-nous faire ?**

### Objectif

Transformer l'analyse en action.

### Contenu

* action recommandée ;
* produit ;
* boutique ;
* quantité ;
* source potentielle du stock ;
* score de priorité ;
* niveau de confiance ;
* raisons quantitatives ;
* Revenue-at-Risk avant ;
* revenu potentiellement protégé après ;
* alternative éventuelle.

---

## Écran 04 — What-if Simulator

### Question

> **Que se passe-t-il si j'applique cette décision ?**

### Objectif

Produire la preuve avant / après.

### Contenu

* scénario initial ;
* scénario recommandé ;
* stock ;
* déficit potentiel ;
* Revenue-at-Risk ;
* disponibilité ;
* variation ;
* revenu potentiellement protégé ;
* hypothèses.

### Interaction

L'utilisateur peut :

* modifier une quantité ;
* tester un scénario ;
* comparer les résultats ;
* réinitialiser.

---

## Écran 05 — AI Decision Explanation

### Question

> **Explique-moi pourquoi cette décision est recommandée.**

### Objectif

Montrer une IA réellement utile.

L'IA doit expliquer les résultats produits par le moteur.

Elle ne doit pas inventer les données.

### Exemples de questions

```text
Pourquoi cette boutique ?

Pourquoi cette quantité ?

Quels facteurs expliquent le risque ?

Que se passe-t-il si je réduis la quantité ?

Quel revenu est potentiellement protégé ?
```

La réponse doit être reliée aux données et résultats calculés.

---

## Écran 06 — Growth Horizon

### Question

> **Que peut devenir ce moteur pour DABA demain ?**

Cet écran représente la vision future.

Il ne doit pas être présenté comme faisant partie du cœur du MVP.

### Vision

```text
TODAY
Protect Revenue

        ↓

TOMORROW
Grow Revenue
```

Le moteur pourrait progressivement couvrir :

* distribution ;
* demande ;
* produits ;
* clients ;
* partenariats ;
* acquisition ;
* conversion ;
* décisions exécutives ;
* mémoire de croissance.

### Vision Business Twin

À long terme :

```text
Business Data
     ↓
Observe
     ↓
Understand
     ↓
Decide
     ↓
Act
     ↓
Measure
     ↓
Learn
     ↓
Business Memory
```

---

# 12. Données

Le MVP doit fonctionner avec des données synthétiques lorsque les données réelles de DABA ne sont pas disponibles.

### Schéma minimal

| Champ           | Exemple      | Utilisation               |
| --------------- | ------------ | ------------------------- |
| `date`          | `2026-08-04` | Temporalité               |
| `boutique_id`   | `B001`       | Point de vente            |
| `produit_id`    | `P012`       | Produit                   |
| `stock`         | `8`          | Disponibilité             |
| `ventes`        | `15`         | Historique                |
| `prix_unitaire` | `18000`      | Valorisation              |
| `stock_cible`   | `30`         | Référence                 |
| `delai_reappro` | `2`          | Contrainte opérationnelle |

Des champs supplémentaires peuvent être ajoutés uniquement lorsqu'ils améliorent réellement la décision.

Le MVP ne doit pas devenir un projet de data warehouse.

---

# 13. Rôle de l'IA

L'IA constitue une **couche d'explication et d'interaction**, pas le moteur mathématique du produit.

## L'IA peut

* interpréter les signaux calculés ;
* expliquer une recommandation ;
* répondre aux questions du responsable ;
* comparer des scénarios ;
* produire un résumé décisionnel ;
* faciliter l'interprétation des résultats.

## L'IA ne doit pas

* inventer des chiffres ;
* calculer le Revenue-at-Risk à la place du moteur ;
* inventer des données DABA ;
* produire une recommandation sans justification ;
* présenter des hypothèses comme des faits ;
* créer une dépendance critique au LLM.

### Principe

```text
Moteur analytique
      ↓
Résultats vérifiés
      ↓
IA
      ↓
Explication
```

et non :

```text
IA
 ↓
Chiffres
 ↓
Décision
```

---

# 14. Ce qui n'est pas dans le MVP

Afin d'éviter le scope creep, les fonctionnalités suivantes restent hors périmètre du MVP :

* CRM complet ;
* automatisation WhatsApp complète ;
* refonte complète de marque ;
* marketing automation complet ;
* marketplace ;
* gestion complète de la production ;
* Business Twin complet ;
* système multi-agent autonome complexe ;
* prédiction long terme non validée ;
* intégrations multiples avec les systèmes internes de DABA.

Ces éléments peuvent être évoqués dans la vision future lorsqu'ils renforcent le récit produit, mais ils ne doivent pas détourner l'équipe du MVP.

---

# 15. Vision long terme

Le MVP constitue le premier module d'une infrastructure d'intelligence décisionnelle plus large.

### Phase 1 — Smart Distribution Intelligence

* stocks ;
* ventes ;
* disponibilité ;
* réallocation.

### Phase 2 — Demand & Product Intelligence

* prévision de demande ;
* produits ;
* saisonnalité.

### Phase 3 — Customer & Partnership Intelligence

* valeur client ;
* fidélité ;
* partenaires.

### Phase 4 — Growth & Conversion Intelligence

* acquisition ;
* conversion ;
* campagnes.

### Phase 5 — Executive Copilot

Interaction stratégique en langage naturel.

### Phase 6 — Growth Memory / Business Twin

Mémoire des :

* décisions ;
* résultats ;
* erreurs ;
* succès ;
* apprentissages.

---

## Revenue Growth Ecosystem

À plus long terme, DabaPulse pourrait également alimenter un écosystème de croissance autour de DABA :

* Ferme Expérience ;
* Media Partnership Engine ;
* DABA Academy ;
* DABA Club ;
* QR Code Marketing.

Ces axes constituent une vision d'extension et non des fonctionnalités du MVP actuel.

---

# 16. Organisation de l'équipe

L'équipe fonctionne avec cinq fonctions principales et un contributor polyvalent.

| Rôle                 | Responsabilités                                               |
| -------------------- | ------------------------------------------------------------- |
| **Engineering Lead** | Architecture, backend, intégration, Git, déploiement, qualité |
| **AI Lead**          | LLM, prompts, explications, guardrails, tests IA              |
| **Product Lead**     | Problème, scope, UX, priorités, coordination                  |
| **Growth Lead**      | KPI, ROI, logique de valeur, pitch, réplication               |
| **Data Lead**        | Dataset, validation, EDA, métriques, Risk Engine, simulation  |
| **Contributor**      | Renfort du lead le plus chargé, tests, QA, documentation      |

### Règle

> **Chaque tâche possède un owner unique**, même lorsque plusieurs membres contribuent.

---

# 17. Workflow Git

La branche `main` représente la version stable.

Aucun développement direct ne doit être effectué sur `main`.

### Workflow

```text
main
 │
 ├── feature/...
 ├── fix/...
 ├── data/...
 ├── ai/...
 ├── ui/...
 └── docs/...
       │
       ▼
    Pull Request
       │
       ▼
     Review
       │
       ▼
      Tests
       │
       ▼
      Merge
       │
       ▼
      main
```

### Branch naming

Exemples :

```text
feature/revenue-at-risk
feature/decision-engine
feature/what-if-simulator
feature/ai-explanation
feature/executive-screen
data/synthetic-dataset
ui/risk-investigation
fix/revenue-calculation
docs/setup
```

### Commit convention

```text
feat:
fix:
refactor:
docs:
test:
data:
ui:
chore:
```

Exemples :

```text
feat: add revenue at risk calculation

feat: implement decision ranking

data: add synthetic distribution dataset

ui: implement risk investigation screen

test: validate risk engine

fix: correct stock deficit calculation
```

---

# 18. Structure du repository

```text
daba-pulse/
│
├── .github/
│   ├── workflows/
│   │   └── ci.yml
│   │
│   └── pull_request_template.md
│
├── backend/
│
├── frontend/
│
├── data/
│   └── sample/
│
├── docs/
│
├── tests/
│
├── scripts/
│
├── .env.example
├── .gitignore
└── README.md
```

La structure pourra évoluer si nécessaire pendant le développement, mais toute évolution doit servir l'architecture du produit.

---

# 19. Roadmap

Le hackathon se déroule sur une fenêtre très courte.

La priorité est donc de construire une **vertical slice complète** avant d'ajouter des fonctionnalités secondaires.

## 4 août — Fondation

### Engineering

* repository ;
* architecture ;
* FastAPI skeleton ;
* environnement.

### AI

* choix du modèle ;
* prompts v0.

### Product

* cahier des charges ;
* user flow.

### Growth

* KPI ;
* ROI ;
* narration business.

### Data

* schéma dataset ;
* génération des données synthétiques.

---

## 5 août — Data + moteur analytique

### Engineering

* endpoints data.

### AI

* prototype d'explication.

### Product

* validation UX.

### Growth

* définition Revenue-at-Risk.

### Data

* EDA ;
* Risk Engine v0.

---

## 6 août — Decision Engine

### Engineering

* intégration backend.

### AI

* Q&A sur les résultats.

### Product

* review du parcours.

### Growth

* scoring des actions.

### Data

* Decision Engine ;
* simulation v0.

---

## 7 août — Vertical Slice

Objectif :

> avoir une première version complète de bout en bout.

```text
Data
 ↓
Risk
 ↓
Revenue-at-Risk
 ↓
Decision
 ↓
Simulation
 ↓
API
 ↓
Frontend
```

---

## 8 août — Différenciation + démonstration

* stabilisation ;
* UX polish ;
* explications IA finales ;
* scénario business ;
* ROI ;
* storytelling ;
* cas de démonstration ;
* tests ;
* corrections.

---

## 9 août — Finalisation

* déploiement ;
* tests ;
* fallback IA ;
* pitch ;
* cahier des charges ;
* business model ;
* validation KPI ;
* documentation ;
* répétition.

---

## 10 août — Soumission

Aucune nouvelle fonctionnalité critique.

Uniquement :

* vérification ;
* soumission ;
* backup ;
* répétition ;
* présentation.

---

# 20. Principes de développement

## 20.1 Profondeur avant largeur

Le projet ne cherche pas à présenter 30 fonctionnalités.

Il cherche à rendre **un problème très bien résolu**.

---

## 20.2 Chaque fonctionnalité doit répondre à un problème

Avant d'ajouter une fonctionnalité :

> Quel problème résout-elle ?

Si la réponse n'est pas claire :

> elle n'entre probablement pas dans le MVP.

---

## 20.3 La décision est plus importante que le dashboard

Le dashboard est une interface.

Le véritable produit est :

```text
Risk
 ↓
Revenue-at-Risk
 ↓
Decision
 ↓
Simulation
```

---

## 20.4 Les chiffres doivent être explicables

Toute valeur importante doit pouvoir répondre à :

* d'où vient-elle ?
* quelles données l'ont produite ?
* quelles hypothèses ont été utilisées ?
* quel est le niveau de confiance ?

---

## 20.5 Les données synthétiques doivent être honnêtes

Les données synthétiques sont nécessaires pour permettre le développement lorsque les données internes ne sont pas disponibles.

Elles ne doivent jamais être présentées comme des données réelles de DABA.

---

## 20.6 L'IA ne doit pas être un gadget

L'IA doit rendre les résultats plus accessibles et exploitables.

Elle ne doit pas remplacer les calculs déterministes.

---

## 20.7 Éviter le dashboard SaaS générique

DabaPulse ne doit pas ressembler à :

* un template administratif ;
* un dashboard KPI générique ;
* un chatbot posé au-dessus de quelques graphiques ;
* une interface « AI-generated » standardisée.

Le design doit servir la narration :

```text
Voici le risque.
       ↓
Voici ce qu'il coûte.
       ↓
Voici pourquoi.
       ↓
Voici quoi faire.
       ↓
Voici ce que cela change.
```

---

# 21. Limites et transparence

DabaPulse est développé dans le contexte d'un hackathon.

Certaines hypothèses concernant les opérations de DABA peuvent donc ne pas être confirmées par des données internes.

Lorsque les données réelles ne sont pas disponibles :

* les données synthétiques sont explicitement signalées ;
* les hypothèses sont affichées ;
* les résultats sont présentés comme illustratifs ;
* aucune affirmation non vérifiée concernant DABA ne doit être présentée comme un fait.

Le système doit être capable d'accueillir ultérieurement des données réelles sans modifier fondamentalement son architecture.

---

# 22. Documentation

Le dossier `/docs` contient les documents de référence du projet.

Il peut notamment contenir :

```text
docs/
│
├── mission-2-cadrage/
├── product/
├── architecture/
├── ux/
├── data/
├── ai/
└── team/
```

Les documents de référence doivent permettre de comprendre :

* le problème ;
* la solution ;
* l'architecture ;
* les hypothèses ;
* les rôles ;
* les décisions ;
* les limites ;
* la roadmap.

Le code reste la source de vérité pour le comportement réellement implémenté.

---

# 23. Statut du projet

**Status: In active development**

### Current phase

```text
Architecture
    ↓
Implementation
    ↓
Validation
    ↓
Demonstration
    ↓
Submission
```

### MVP retenu

**Revenue-at-Risk Decision Engine**

### Cas d'utilisation

**Smart Distribution**

### Vision long terme

**Business Twin / Growth Decision OS**

---

# 24. Équipe

## Mission 2 — Branding & Growth

### Startup FairPlay Hackathon

| Membre   | Rôle                         |
| -------- | ---------------------------- |
| Mauricia | Product / Project Leadership |
| Stane    | Engineering / Strategy       |
| Xavy     | Growth                       |
| Evrard   | Product / Vision             |
| Mael     | Contributor                  |
| [Nom]    | Contributor                  |

> Cette section sera complétée et ajustée avec les noms et responsabilités définitifs de l'équipe.

---

# 25. Licence

La licence du repository sera définie après vérification des règles du hackathon et des contraintes de propriété intellectuelle applicables au projet.

Aucune licence permissive n'est ajoutée par défaut tant que ce point n'est pas confirmé.

---

## Final Principle

DabaPulse n'est pas conçu pour montrer combien de fonctionnalités une équipe peut développer en quelques jours.

Il est conçu pour démontrer une idée beaucoup plus simple :

> **Transformer un signal business en risque mesurable, transformer ce risque en décision et montrer économiquement ce que cette décision peut changer.**

```text
OBSERVE
   ↓
UNDERSTAND
   ↓
DECIDE
   ↓
SIMULATE
   ↓
MEASURE
   ↓
LEARN
```

**DabaPulse — From business signals to better decisions.**

```