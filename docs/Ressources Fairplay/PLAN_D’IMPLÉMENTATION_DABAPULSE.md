
# DOCUMENT — PLAN D’IMPLÉMENTATION DABAPULSE

## Journée du 18 août 2026 — Refonte, différenciation et préparation à la production

**Projet :** DabaPulse
**Mission :** Mission 2 — Revenue-at-Risk Decision Engine / Smart Distribution
**Rôle :** Engineering Lead
**Branche :** `engineering-lead/mvp-foundation`
**Date :** 18 août 2026
**Objectif de la journée :** transformer la version actuelle en une **expérience décisionnelle démontrable**, visuellement distinctive et techniquement stable.

---

# 1. OBJECTIF GLOBAL DE LA JOURNÉE

Aujourd'hui n'est **pas** une journée destinée à ajouter une multitude de fonctionnalités.

L'objectif est de faire évoluer DabaPulse selon cette logique :

```text
VERSION ACTUELLE
      ↓
Audit
      ↓
Conservation des fondations valides
      ↓
Refonte UX / UI
      ↓
Expérience décisionnelle
      ↓
Motion + storytelling
      ↓
IA contextualisée
      ↓
Validation technique
      ↓
VERSION CANDIDATE
      ↓
Déploiement + tests le 19
```

Le principe directeur est :

> **Ne pas construire davantage. Construire mieux.**

Le cadrage initial indique explicitement que le MVP doit permettre d'importer des données, les valider, détecter les risques, calculer le Revenue-at-Risk, classer les priorités, recommander une action, expliquer cette recommandation, simuler l'avant/après et fournir une assistance IA limitée aux données et résultats calculés. 

Donc chaque modification aujourd'hui doit renforcer **une de ces capacités**.

---

# 2. CONTRAINTE ABSOLUE : NE PAS RÉGRESSER

Avant toute modification :

### Vérifier l'état actuel

```bash
git status
git branch --show-current
git log --oneline -10
```

Puis vérifier que la branche correspond bien à :

```text
engineering-lead/mvp-foundation
```

Avant chaque nouvel incrément :

1. vérifier l'implémentation précédente ;
2. vérifier qu'elle existe réellement dans le workspace ;
3. vérifier les fichiers concernés ;
4. vérifier qu'elle a été poussée sur GitHub ;
5. vérifier que le contenu GitHub correspond réellement au workspace ;
6. seulement ensuite commencer l'incrément suivant.

Cette discipline est particulièrement importante aujourd'hui car nous allons toucher à plusieurs couches simultanément.

---

# 3. PHASE 0 — BASELINE TECHNIQUE

## Priorité : P0 — obligatoire

Avant toute refonte visuelle, établir une photographie technique du projet.

### Vérifications

Frontend :

```bash
npm install
npm run build
npm run lint
```

Puis, selon les scripts réellement présents :

```bash
npm test
```

Backend :

```bash
pip install -r requirements.txt
```

puis lancer les tests disponibles.

Vérifier également :

* variables d'environnement ;
* appels API ;
* routes ;
* endpoints ;
* données simulées ;
* intégration frontend/backend ;
* gestion des erreurs ;
* fallback IA ;
* responsive ;
* console browser ;
* erreurs réseau.

### Livrable

Créer ou mettre à jour un état :

```text
BASELINE — 18/08/2026
```

avec :

| Élément         | État |
| --------------- | ---- |
| Frontend build  | ✅/❌  |
| Backend         | ✅/❌  |
| API             | ✅/❌  |
| Data flow       | ✅/❌  |
| Risk Engine     | ✅/❌  |
| Decision Engine | ✅/❌  |
| Simulation      | ✅/❌  |
| IA              | ✅/❌  |
| Navigation      | ✅/❌  |
| Responsive      | ✅/❌  |

**Ne pas commencer la refonte tant qu'un problème critique de fond n'est pas identifié.**

---

# 4. PHASE 1 — AUDIT DE L'EXPÉRIENCE ACTUELLE

## Priorité : P0

Le problème principal identifié dans notre évolution récente est clair :

> DabaPulse risque de ressembler à un dashboard qui affiche des informations.

Or le produit doit raconter :

```text
UNE SITUATION
     ↓
UN RISQUE
     ↓
UN COÛT
     ↓
UNE CAUSE
     ↓
UNE ACTION
     ↓
UNE SIMULATION
     ↓
UNE DÉCISION
```

Le document de cadrage est explicite : le problème n'est pas « DABA a besoin d'un dashboard », mais la difficulté à détecter directement un désalignement et à savoir **quelle action de distribution protège le revenu**. 

### Question à poser à chaque écran

> **Si je retire tous les graphiques de cet écran, est-ce qu'il reste une décision ou une action compréhensible ?**

Si la réponse est non :

**l'écran doit être retravaillé.**

---

# 5. PHASE 2 — RESTRUCTURATION DES SIX ÉCRANS

Le système conserve les six écrans déjà définis.

La direction n'est donc pas :

> « créer six nouvelles pages ».

Elle est :

> **transformer six écrans informatifs en six moments d'une décision.**

La spécification existante définit notamment :

* Écran 01 : problème/priorité ;
* Écran 02 : origine du risque ;
* Écran 03 : action ;
* Écran 04 : simulation ;
* Écran 05 : explication IA ;
* Écran 06 : vision future. 

---

## ÉCRAN 01 — SIGNAL

### Fonction

Faire comprendre immédiatement :

> **« Il se passe quelque chose. »**

Pas :

> « Voici votre dashboard. »

### À montrer

* état global ;
* signal critique ;
* revenu potentiellement exposé ;
* localisation du problème ;
* CTA vers investigation.

### À éviter

* mur de KPI ;
* 10 cartes identiques ;
* tableaux dès l'entrée ;
* sidebar massive ;
* esthétique SaaS générique.

### Direction

Créer une composition plus éditoriale :

```text
                REVENUE AT RISK

             2 480 000 FCFA

      ──────────────────────────

      3 situations nécessitent
      une intervention

             [Investiguer]
```

Le chiffre devient le protagoniste.

---

# 6. ÉCRAN 02 — INVESTIGATION

## Fonction

Répondre à :

> **Pourquoi cette situation est-elle dangereuse ?**

Le système doit progressivement révéler :

```text
Boutique
   ↓
Produit
   ↓
Demande
   ↓
Stock
   ↓
Écart
   ↓
Revenu exposé
```

### Interaction

L'utilisateur doit pouvoir sélectionner une situation.

Puis obtenir :

```text
CE QUI SE PASSE
       ↓
POURQUOI
       ↓
IMPACT
```

### Objectif

Faire ressentir au jury :

> « Le système comprend le problème. »

---

# 7. ÉCRAN 03 — DECISION

C'est probablement **l'écran le plus important du MVP**.

Le moteur doit répondre :

> **Que devons-nous faire maintenant ?**

Le cadrage exige précisément une recommandation d'action et son explication. 

### Exemple

```text
ACTION RECOMMANDÉE

Réallouer 22 unités
de P03

Boutique source
B04

        →

Boutique cible
B01
```

Puis :

```text
Pourquoi ?

• demande supérieure de 31 %
• stock actuel insuffisant
• délai de réapprovisionnement : 2 jours
• revenu exposé : 2,48 M FCFA
```

### CTA principal

```text
SIMULER CETTE ACTION
```

Ce CTA est beaucoup plus important qu'un bouton générique « voir détails ».

---

# 8. ÉCRAN 04 — SIMULATION

## Fonction

Transformer :

> recommandation

en :

> **preuve.**

Le système doit permettre :

```text
AVANT

Stock : 8
Revenue at Risk : 2,48 M


ACTION

+22 unités


APRÈS

Stock : 30
Revenue at Risk : 0,72 M
```

Puis :

```text
REVENU POTENTIELLEMENT PROTÉGÉ

+1,76 M FCFA
```

La spécification prévoit explicitement la simulation avant/après et la visualisation du revenu protégé/récupérable. 

---

# 9. ÉCRAN 05 — IA

## Attention : ne pas transformer DabaPulse en chatbot.

C'est une erreur stratégique.

L'IA doit être :

> **le copilote explicatif du moteur décisionnel.**

Pas :

> un ChatGPT intégré dans l'application.

Le cadrage exige que l'assistant soit limité aux données et résultats calculés. 

### Exemple

Utilisateur :

> Pourquoi cette boutique ?

IA :

```text
Cette boutique est prioritaire pour trois raisons :

1. sa demande augmente de 31 % ;
2. son stock actuel couvre seulement X jours ;
3. le revenu exposé est supérieur aux autres
   points de vente.

La recommandation du moteur est donc...
```

---

# 10. AJOUT IMPORTANT : LE MODE « CHALLENGE »

C'est une évolution particulièrement intéressante de la conception.

L'utilisateur doit pouvoir demander :

> « Et si je ne fais rien ? »

ou :

> « Pourquoi 22 unités et pas 15 ? »

ou :

> « Quelle différence si je fais 30 ? »

ou :

> « Quelle hypothèse influence le plus cette décision ? »

L'IA ne décide donc pas seule.

Elle fonctionne ainsi :

```text
MOTEUR ANALYTIQUE
       ↓
RECOMMANDATION
       ↓
IA EXPLIQUE
       ↓
UTILISATEUR CHALLENGE
       ↓
SIMULATION / DONNÉES
       ↓
UTILISATEUR DÉCIDE
```

Cela renforce considérablement le positionnement décisionnel.

---

# 11. ÉCRAN 06 — GROWTH HORIZON

Cet écran doit rester secondaire.

Le document de cadrage précise que le Business Twin et les extensions Growth sont des visions futures, pas le cœur du MVP. 

Donc :

### Aujourd'hui

```text
PROTECT REVENUE
```

### Demain

```text
GROW REVENUE
```

Présenter :

* demande ;
* clients ;
* partenariats ;
* croissance ;
* mémoire décisionnelle ;
* Business Twin.

Mais avec une mention claire :

> **VISION — FUTURE**

---

# 12. PHASE 3 — NOUVELLE DIRECTION VISUELLE

## Priorité : P0

La direction visuelle doit sortir du :

> Dashboard SaaS générique.

Elle doit devenir :

> **Decision Intelligence Interface.**

---

# 13. PRINCIPLE VISUEL

Inspirations à étudier :

### HorizonX

HorizonX met actuellement en avant des expériences très différentes : interfaces immersives, WebGL, storytelling cinématique, interfaces analytiques B2B et systèmes de design complets. ([HorizonX][1])

Particulièrement intéressants pour DabaPulse :

* **NOLITH Freight Intelligence Hero** ;
* **Mosk**, concept B2B analytics ;
* **KUKA Immersive Robotics** ;
* **Hand Prosthesis Simulator** ;
* **MORPHO WebGL**.

([HorizonX][1])

L'idée à retenir n'est pas de copier ces interfaces.

C'est :

> **prendre leurs mécanismes de composition et les traduire dans notre problème métier.**

---

# 14. GODLY

Godly doit servir de bibliothèque de recherche pour :

* typographie ;
* composition ;
* navigation ;
* motion ;
* storytelling ;
* hiérarchie ;
* transitions.

La plateforme se présente précisément comme une galerie de sites créatifs et de références d'interactions réelles. ([Uwarp][2])

### Règle

Ne pas demander :

> « Trouve-moi un joli dashboard. »

Mais :

> « Trouve-moi des interfaces qui transforment une grande quantité d'informations en expérience narrative et décisionnelle. »

---

# 15. ANIME.JS

Anime.js peut être utilisé pour :

* micro-interactions ;
* transitions ;
* stagger ;
* apparition progressive ;
* animations de chiffres ;
* morphing SVG ;
* timelines ;
* transitions entre états.

La documentation actuelle couvre notamment animation, timeline, SVG, texte, événements et WAAPI. ([animejs.com][3])

### Important

Le motion doit être :

> **fonctionnel avant d'être décoratif.**

Exemple :

Le chiffre :

```text
2 480 000 FCFA
```

ne doit pas simplement apparaître.

Il peut évoluer depuis :

```text
0
↓
...
↓
2 480 000
```

pour matérialiser l'exposition financière.

---

# 16. MOTIONSITES + AUTRES RÉFÉRENCES

La recherche doit servir à identifier :

* transitions ;
* scroll narratives ;
* cinématique ;
* interactions data-driven ;
* composition asymétrique ;
* storytelling ;
* micro-interactions ;
* visualisation dynamique.

Mais il faut appliquer une règle :

> **aucune animation ne doit exister uniquement parce qu'elle est belle.**

Elle doit :

1. attirer l'attention ;
2. expliquer ;
3. guider ;
4. contextualiser ;
5. confirmer ;
6. matérialiser un changement.

---

# 17. PHASE 4 — SYSTÈME DE MOTION

Créer une logique cohérente :

```text
ENTER
↓
DISCOVER
↓
FOCUS
↓
DECIDE
↓
SIMULATE
↓
CONFIRM
```

### Exemple

Lorsqu'on sélectionne une boutique :

```text
boutique
    ↓
focus
    ↓
produit
    ↓
risque
    ↓
revenue-at-risk
```

Les éléments ne doivent pas simplement « apparaître ».

Ils doivent **se révéler dans l'ordre logique de la décision**.

---

# 18. PHASE 5 — DATA-DRIVEN MOTION

C'est l'une des meilleures pistes de différenciation.

Les animations doivent dépendre des données.

Exemple :

### Risque faible

Animation légère.

### Risque moyen

Accentuation.

### Risque critique

Signal visuel plus fort.

Ainsi :

```text
DATA
 ↓
STATE
 ↓
VISUAL BEHAVIOUR
```

et non :

```text
ANIMATION
 ↓
DATA
```

Cela donne une interface qui semble réellement **vivante parce qu'elle réagit au système décisionnel**.

---

# 19. PHASE 6 — MICRO-ILLUSTRATIONS

Ta précédente idée est pertinente mais doit rester extrêmement contrôlée.

Le but n'est pas d'ajouter des dessins partout.

Créer plutôt une **signature visuelle métier**.

Exemples :

### Distribution

Une micro-illustration :

```text
B04 ───────────→ B01
       22 unités
```

### Stock

Petites représentations de cartons/produits.

### Flux

Petits marqueurs de déplacement.

### Simulation

Un mouvement visuel avant/après.

### Intelligence

Une représentation abstraite du raisonnement.

Cela permettra de rendre DabaPulse identifiable sans transformer l'application en illustration-heavy.

---

# 20. PHASE 7 — PALETTE CLAIRE + SOMBRE

Le système doit supporter :

```text
LIGHT
   ↕
DARK
```

mais sans créer deux produits différents.

Il faut définir des **tokens sémantiques** :

```text
--background
--surface
--text-primary
--text-secondary
--border
--accent
--risk
--warning
--success
--intelligence
```

Ainsi le changement de thème se fait au niveau des tokens.

Pas :

> changer manuellement chaque composant.

---

# 21. PHASE 8 — ARCHITECTURE FRONTEND

Avant d'ajouter des composants :

identifier :

```text
pages/
components/
layouts/
hooks/
services/
data/
styles/
```

Puis vérifier que :

* la logique métier n'est pas dans les composants UI ;
* les données ne sont pas dupliquées ;
* les composants sont réutilisables ;
* les animations ne sont pas dispersées ;
* les appels API sont centralisés.

Le principe du cadrage reste de séparer interface, calculs, règles métier et simulation. 

---

# 22. PHASE 9 — BACKEND / API

## Ne pas reconstruire le backend sans nécessité.

Vérifier plutôt :

```text
Frontend
   ↓
API
   ↓
Data
   ↓
Analytics
   ↓
Risk Engine
   ↓
Decision Engine
   ↓
Simulation
   ↓
AI
```

L'architecture cible prévoit précisément cette séparation et demande que l'IA ne bloque pas les calculs analytiques. 

---

# 23. PHASE 10 — IA : ARCHITECTURE À VERROUILLER

Le pipeline doit être :

```text
USER QUESTION
      ↓
CONTEXT BUILDER
      ↓
KNOWN DATA
      ↓
ANALYTICAL RESULTS
      ↓
LLM
      ↓
EXPLANATION
      ↓
USER CHALLENGE
```

Le LLM ne doit jamais inventer :

* stock ;
* ventes ;
* revenu ;
* risque ;
* recommandations numériques.

Ces informations viennent du moteur.

---

# 24. PHASE 11 — « CHALLENGE ENGINE »

À implémenter si le backend actuel permet raisonnablement de le faire aujourd'hui.

Sinon, préparer son architecture.

Exemples de questions supportées :

```text
Pourquoi cette boutique ?
```

```text
Pourquoi 22 unités ?
```

```text
Que se passe-t-il si j'envoie 15 ?
```

```text
Que se passe-t-il si je n'interviens pas ?
```

```text
Quelle hypothèse influence le plus le résultat ?
```

```text
Quelle autre action est possible ?
```

Cela transforme l'IA de :

> générateur d'explications

en :

> **interface conversationnelle de stress-test de décision.**

---

# 25. PHASE 12 — SCÉNARIO DE DÉMONSTRATION

Le scénario recommandé reste :

```text
PROBLÈME
 ↓
RISQUE
 ↓
COÛT
 ↓
CAUSE
 ↓
ACTION
 ↓
SIMULATION
 ↓
QUESTION IA
 ↓
CHALLENGE
 ↓
DÉCISION
```

Le cadrage existant recommande déjà une démonstration en 3–5 minutes suivant cette logique. 

---

# 26. CE QU'IL NE FAUT PAS FAIRE AUJOURD'HUI

### ❌ Ne pas créer :

* CRM ;
* WhatsApp automation complète ;
* marketplace ;
* Business Twin complet ;
* multi-agent ;
* prédiction longue durée ;
* intégrations multiples DABA ;
* fonctionnalités marketing complètes.

Ces éléments sont explicitement hors MVP. 

### ❌ Ne pas ajouter :

* 20 nouveaux graphiques ;
* 10 nouvelles pages ;
* 15 nouvelles animations ;
* des fonctionnalités uniquement pour « faire premium ».

---

# 27. PRIORITÉS D'IMPLÉMENTATION DU 18 AOÛT

Voici l'ordre que je recommande.

| Priorité | Travail             | Objectif                         |
| -------- | ------------------- | -------------------------------- |
| P0       | Baseline technique  | garantir la stabilité            |
| P0       | Audit des 6 écrans  | supprimer le caractère dashboard |
| P0       | Refonte écran 01    | impact immédiat                  |
| P0       | Refonte écran 02    | compréhension                    |
| P0       | Refonte écran 03    | décision                         |
| P0       | Refonte écran 04    | preuve                           |
| P0       | Refonte écran 05    | IA contextualisée                |
| P1       | Écran 06            | vision                           |
| P1       | Design tokens       | cohérence                        |
| P1       | Light/Dark          | finition produit                 |
| P1       | Motion system       | immersion                        |
| P1       | Data-driven motion  | différenciation                  |
| P1       | Micro-illustrations | identité                         |
| P1       | Challenge IA        | profondeur                       |
| P0       | QA                  | stabilité                        |
| P0       | Build final         | préparation déploiement          |

---

# 28. PLAN HORAIRE DU 18 AOÛT

## 10h00 → 11h00

### Stabilisation

* Git ;
* build ;
* tests ;
* API ;
* console ;
* environnement.

---

## 11h00 → 12h30

### Audit UX/UI

Revoir les six écrans.

Identifier :

```text
KEEP
REWORK
REMOVE
CREATE
```

---

## 12h30 → 15h00

### Refonte du cœur

Priorité absolue :

**Écran 01 → 02 → 03 → 04**

C'est le cœur de la démonstration.

---

## 15h00 → 16h30

### IA + Challenge

* explications ;
* questions ;
* simulation ;
* contextualisation ;
* fallback.

---

## 16h30 → 18h00

### Direction visuelle

* palette ;
* light/dark ;
* typography ;
* spacing ;
* surfaces ;
* visual hierarchy.

---

## 18h00 → 20h00

### Motion + storytelling

* transitions ;
* data-driven motion ;
* micro-interactions ;
* micro-illustrations.

---

## 20h00 → 21h00

### Écran 06

Vision future.

---

## 21h00 → 22h30

### QA

Tester :

* navigation ;
* responsive ;
* données ;
* simulation ;
* IA ;
* erreurs ;
* loading ;
* empty states ;
* theme switch.

---

## 22h30 → 23h30

### Build candidate

```bash
npm run build
```

Tests finaux.

Correction des erreurs critiques.

---

## 23h30 → 00h00

### Git checkpoint

Créer le checkpoint de fin de journée.

---

# 29. CHECKPOINT DE FIN DE JOURNÉE

À la fin du 18 août, on doit pouvoir dire :

### Produit

* [ ] six écrans fonctionnels ;
* [ ] parcours décisionnel complet ;
* [ ] aucune page purement décorative ;
* [ ] aucune sensation de dashboard générique.

### Data

* [ ] risque calculé ;
* [ ] Revenue-at-Risk ;
* [ ] recommandation ;
* [ ] simulation.

### IA

* [ ] explication ;
* [ ] données sources ;
* [ ] challenge ;
* [ ] fallback.

### Design

* [ ] direction visuelle cohérente ;
* [ ] light mode ;
* [ ] dark mode ;
* [ ] motion ;
* [ ] micro-interactions ;
* [ ] identité métier.

### Engineering

* [ ] build ;
* [ ] tests ;
* [ ] API ;
* [ ] aucune régression critique ;
* [ ] environnement propre.

---

# 30. PHASE DU 19 AOÛT

Demain ne doit **pas** devenir une nouvelle journée de développement créatif.

Elle devient :

```text
DEPLOY
 ↓
TEST
 ↓
FIX
 ↓
VERIFY
 ↓
REHEARSE
```

### Render

Backend.

### Netlify

Frontend.

### Tests

* production ;
* API ;
* CORS ;
* variables ;
* IA ;
* navigation ;
* responsive ;
* simulation.

Puis seulement :

> corrections critiques.

---

# 31. RÈGLE DU 19 AOÛT

À partir du moment où nous avons une :

# VERSION CANDIDATE

on ne cherche plus :

> « Qu'est-ce qu'on pourrait encore ajouter ? »

On cherche :

> **« Qu'est-ce qui pourrait nous faire perdre des points ? »**

C'est une différence fondamentale.

---

# 32. LE CRITÈRE DE FIN DU 18 AOÛT

La journée est considérée comme réussie si DabaPulse peut faire vivre au jury cette phrase :

> **« Voici où DABA risque de perdre de l'argent. »**

Puis :

> **« Voici pourquoi. »**

Puis :

> **« Voici ce que nous recommandons. »**

Puis :

> **« Voici ce qui se passe si vous le faites. »**

Puis :

> **« Maintenant, challengez la décision. »**

Et enfin :

> **« Voici le revenu que cette décision peut protéger. »**

C'est cela qui doit être au centre de toute la refonte.

---

## 33. RÉFÉRENCES DE DESIGN À FOURNIR À L'IA DE DÉVELOPPEMENT

Je recommande de joindre au plan :

* [HorizonX](https://horizonx.so/?utm_source=chatgpt.com) — référence principale pour les expériences immersives, les systèmes UI et les interfaces B2B sophistiquées. ([HorizonX][1])
* [HorizonX Explore](https://horizonx.so/explore?utm_source=chatgpt.com) — pour explorer spécifiquement les catégories UI/UX, Code, Design Systems et les exemples de composants. ([HorizonX][4])
* [Godly Design](https://godly.design/?utm_source=chatgpt.com) — référence pour la recherche d'interactions, de composition et de détails visuels. ([Godly — Web Design Inspiration][5])
* [Anime.js Documentation](https://animejs.com/documentation/?utm_source=chatgpt.com) — référence technique pour les animations, timelines, SVG, texte et interactions. ([animejs.com][3])

Pour **Motionsites.ai** et **Blink.com**, je ne les utiliserais pas comme sources de vérité tant que leur contenu précis n'est pas vérifiable depuis la recherche actuelle. L'IA pourra néanmoins les analyser directement si son environnement lui donne accès à ces URLs.

---

# 34. DIRECTIVE FINALE POUR L'IA DE DÉVELOPPEMENT

Le document doit être interprété ainsi :

> **Tu n'es pas chargé de rendre DabaPulse simplement plus beau.**
>
> Tu dois transformer une interface actuellement trop proche d'un dashboard en une **expérience de décision business**.
>
> Tu dois conserver les fondations techniques valides.
>
> Tu dois respecter le périmètre du MVP.
>
> Tu peux remettre en question une décision visuelle ou technique lorsqu'une meilleure solution existe.
>
> Tu peux proposer une nouvelle composition, une nouvelle palette, une nouvelle interaction ou une nouvelle animation si elle sert mieux le produit.
>
> Mais tu ne dois jamais ajouter une fonctionnalité uniquement parce qu'elle est impressionnante.
>
> **L'originalité doit venir de l'adaptation au problème métier, pas de l'accumulation d'effets.**

---

## 35. LIVRABLES ATTENDUS DE L'IA À CHAQUE INCRÉMENT

À chaque incrément, elle doit obligatoirement produire :

### 1. Vérification précédente

```text
Implémentation précédente :
État GitHub :
Fichiers vérifiés :
Correspondance workspace/GitHub :
```

### 2. Fichiers modifiés

```text
frontend/src/...
frontend/src/...
backend/...
```

### 3. Pour chaque fichier

```text
AVANT
→ problème

APRÈS
→ solution

POURQUOI
→ choix technique
```

### 4. Validation

```text
Build :
Tests :
Lint :
Régression :
```

### 5. Git

```bash
git status
git add ...
git commit -m "..."
git push origin engineerwith-lead/mvp-foundation
```

### 6. Prochaine étape

```text
Incrément terminé : X

Prochain incrément : Y

Objectif :
...
```

Cette discipline évite exactement le problème que nous avons identifié auparavant : modifier conceptuellement une fonctionnalité sans que les fichiers correspondants soient réellement modifiés dans le workspace.

---

# 36. VERDICT STRATÉGIQUE

Je ne recommande **pas** une reconstruction complète de DabaPulse depuis zéro.

Je recommande une :

# **REFONTE CIBLÉE DU VERTICAL SLICE**

On conserve :

* architecture ;
* backend ;
* moteurs ;
* données ;
* simulation ;
* API ;
* logique métier valide.

On refond prioritairement :

* composition ;
* hiérarchie ;
* storytelling ;
* navigation ;
* visualisation ;
* motion ;
* IA ;
* identité visuelle ;
* expérience de décision.

Le cadrage technique nous donne déjà une base suffisamment solide : séparation des responsabilités, moteur analytique indépendant de l'IA, données synthétiques, simulation et recommandation explicable. 

**La vraie bataille du 18 août est donc l'expression de cette architecture.**

DabaPulse ne doit plus donner l'impression de dire :

> « Voici vos données. »

Il doit donner l'impression de dire :

> **« Voici le risque. Voici ce qu'il vous coûte. Voici pourquoi il existe. Voici ce que vous pouvez faire. Voyons ce qui se passe si vous le faites. »**

C'est cette transformation que je placerais au centre de toute la journée du 18.

[1]: https://horizonx.so/?utm_source=chatgpt.com "HorizonX — UI Kits, Components & Figma Templates for Vibecoding"
[2]: https://www.uwarp.design/godly?utm_source=chatgpt.com "Godly Web Design Inspiration"
[3]: https://animejs.com/documentation/?utm_source=chatgpt.com "Documentation | Anime.js | JavaScript Animation Engine"
[4]: https://horizonx.so/explore?utm_source=chatgpt.com "Explore UI Kits, Components & Figma Templates · HorizonX"
[5]: https://godly.design/?utm_source=chatgpt.com "Godly Design – Astronomically Good Websites, Logos, OG Images & App Icons Inspiration"
