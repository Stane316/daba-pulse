# Growth Decision OS — Architecture Data (MVP Hackathon)
## Note du Data Lead — première passe technique

Avant les livrables, trois remarques de cadrage en tant que "CDO" de la startup.

### Critique générale de la conception

1. **Le scope est trop large pour un hackathon.** Vous listez 10 chantiers (modèle de données, dictionnaire, dataset, KPI, règles métier, risk engine, simulateur, score de confiance, data health monitor, QR code). Chacun pris seul est raisonnable ; les dix ensemble ne tiennent pas dans un hackathon avec un niveau de qualité démontrable. Je propose de traiter les points 1 à 8 comme le **cœur démontrable**, et de traiter 9 (Data Health Monitor) comme une **version simplifiée** (un badge de qualité, pas un module complet), et 10 (QR code) comme un **paragraphe de vision** dans le pitch, pas une fonctionnalité codée.
2. **"Revenue at Risk" et "score de confiance" sont les deux éléments qui vendent le produit.** Un jury retient un moteur qui chiffre l'argent en jeu et qui sait dire "je suis sûr à 85 %, pas à 99 %". Concentrez l'essentiel du temps d'ingénierie là-dessus plutôt que sur l'exhaustivité du modèle de données.
3. **Le simulateur "3 scénarios automatiques" est ambitieux mais faisable** si le Risk Engine est bien isolé (fonction pure : état → risques). C'est justement pour ça qu'il faut le concevoir comme un moteur stateless dès le départ (voir plus bas), sinon le simulateur devient un cauchemar de duplication de logique.

Le reste du document suit votre plan, avec pour chaque section : la proposition, la justification, les limites, et l'alternative.

---

## 1. Modèle de données

### Choix : modèle relationnel en étoile, pensé "faits + dimensions"

Plutôt qu'un modèle purement transactionnel (type ERP), je structure autour de **tables de faits** (événements mesurables dans le temps) et **tables de dimensions** (référentiels stables). C'est ce qui permet au Risk Engine et au simulateur de raisonner facilement sur des séries temporelles.

**Avantage** : les calculs de KPI (rotation, couverture, RAR) deviennent des agrégations simples sur les faits.
**Limite** : un peu plus de jointures qu'un modèle "CRUD classique". Négligeable au volume d'un MVP.
**Alternative rejetée** : modèle purement normalisé façon logiciel de gestion — plus propre pour de la saisie, plus lourd pour de l'analytique et la simulation.

### Entités

**Dimensions (référentiels)**
- `boutique` (store_id, nom, ville, zone, type, date_ouverture)
- `produit` (product_id, nom, catégorie, sous_catégorie, prix_unitaire, unité, durée_de_vie_jours, fournisseur_id)
- `categorie` (catégorie_id, nom, famille)
- `client` (client_id — si dispo, sinon avis anonymes agrégés par boutique)

**Faits (événements datés)**
- `vente` (vente_id, date, store_id, product_id, quantité, prix_unitaire, montant, canal)
- `stock` (snapshot_id, date, store_id, product_id, quantité_disponible, seuil_min, seuil_max)
- `transfert` (transfert_id, date, store_id_source, store_id_destination, product_id, quantité, statut)
- `avis_client` (avis_id, date, store_id, product_id_optionnel, note, texte, sentiment, canal)
- `historique_rupture` (rupture_id, store_id, product_id, date_debut, date_fin, durée_jours, manque_a_gagner_estime)

**Couche décisionnelle (générée par le moteur, pas saisie)**
- `recommandation` (reco_id, date_génération, type, store_id, product_id, description, revenue_at_risk, score_confiance, priorité, statut)
- `simulation` (simulation_id, date, scénario_nom, paramètres_json, résultats_json, créé_par)

### Relations clés
- `vente`, `stock`, `avis_client`, `transfert` pointent tous vers `boutique` et `produit` (clés étrangères simples).
- `recommandation` référence l'entité concernée (store_id/product_id) et peut référencer une `simulation` d'origine.
- `historique_rupture` est **dérivée** du croisement `stock` + `vente` (rupture = quantité_disponible = 0 alors que la demande existait) — je recommande de la calculer plutôt que de la saisir, pour éviter une source de vérité dupliquée.

**Point de risque identifié** : ne stockez pas la réputation comme un simple champ "note moyenne" sur `



boutique`. Gardez `avis_client` en grain fin (un avis = une ligne) et calculez la moyenne à la volée. Sinon vous perdez la capacité de calculer "tendance sur 7 jours" plus tard, qui est justement ce qui rend une recommandation crédible.

---

## 2. Data Dictionary (extrait représentatif)

| Variable | Table | Description | Type | Unité | Source | Fréquence MAJ |
|---|---|---|---|---|---|---|
| `store_id` | boutique | Identifiant unique boutique | string (PK) | — | interne | statique |
| `stock_disponible` | stock | Quantité en stock à la date du snapshot | integer | unités | ERP DABA / simulé | quotidienne |
| `seuil_min` | stock | Seuil déclenchant une alerte de rupture | integer | unités | règle métier | à la config |
| `quantite_vendue` | vente | Quantité vendue sur la transaction | integer | unités | caisse / simulé | temps réel / quotidienne |
| `note` | avis_client | Note laissée par le client | integer | /5 | plateforme avis | à chaque avis |
| `sentiment` | avis_client | Polarité du texte de l'avis | enum (positif/neutre/négatif) | — | calculé (NLP simple) | à chaque avis |
| `revenue_at_risk` | recommandation | Revenu estimé menacé si aucune action n'est prise | decimal | FCFA | calculé (Risk Engine) | à chaque génération |
| `score_confiance` | recommandation | Fiabilité estimée de la recommandation | decimal | % | calculé | à chaque génération |

Le dictionnaire complet doit suivre ce même gabarit pour chaque champ des 9 tables — c'est un travail mécanique une fois le modèle validé, je peux le générer intégralement dès que vous validez le schéma ci-dessus.

---

## 3. Dataset synthétique — méthode de génération

**Principe** : ne générez pas un dataset aléatoire uniforme. Un jury/juré technique repère immédiatement un dataset sans structure. Injectez des **patterns volontaires** que votre moteur doit être capable de détecter :

- 2-3 boutiques "à risque" avec rupture de stock récurrente sur un produit précis
- 1 boutique avec une baisse de réputation corrélée à une baisse de ventes (démontre le lien Réputation → Distribution)
- Saisonnalité simple (ex. hausse le week-end)
- Au moins un cas où un transfert entre boutiques aurait clairement évité une rupture — c'est le cas que votre démo va montrer avec le simulateur

**Volumétrie raisonnable pour un MVP démontrable** : 5-8 boutiques, 15-25 produits, 8-12 semaines de ventes journalières, avis clients sur la même période (10-30 par boutique). Ça reste largement gérable en SQLite/CSV et suffisant pour que les KPI aient du sens statistique.

---

## 4. KPI

**Distribution**
- Revenue at Risk (RAR) — revenu menacé par les ruptures prévues
- Taux de rupture = jours en rupture / jours total
- Rotation des stocks = ventes / stock moyen
- Couverture de stock = stock disponible / vente moyenne journalière (en jours)
- Disponibilité produit = 1 − taux de rupture

**Réputation**
- Note moyenne (glissante 7/30 jours, pas seulement globale)
- Volume d'avis
- % avis négatifs
- Temps de réponse moyen (si applicable)

**KPI supplémentaires proposés**
- **Reputation-Adjusted Demand Risk** : croise une baisse de note avec une baisse de vente sur le même produit/boutique — c'est le KPI qui matérialise le lien entre vos deux axes, et c'est différenciant par rapport à un dashboard classique.
- **Stockout Recovery Time** : temps moyen entre détection de rupture et réapprovisionnement effectif — utile pour prioriser.
- **Transfer Efficiency Score** : revenu protégé par transfert / coût logistique estimé du transfert — évite de recommander des transferts qui coûtent plus cher qu'ils ne rapportent.

---

## 5. Règles métier (moteur à base de règles, pas de ML pour le MVP)

Je déconseille du machine learning pour le hackathon : pas assez de données historiques réelles, et un moteur à règles est **explicable par construction**, ce qui correspond à votre exigence n°5 ("expliquer les recommandations"). Le ML devient pertinent pour DABA 360 (v2), une fois qu'il y a un vrai historique.

Structure de règle recommandée (format condition → conséquence → action, avec poids) :

```
RÈGLE : rupture_imminente_forte_vente
SI stock_disponible < seuil_min
ET vente_moyenne_7j > vente_moyenne_30j * 1.2
ALORS niveau_risque = "élevé"
ET revenue_at_risk = vente_moyenne_7j * prix_unitaire * jours_avant_rupture_estimee
ACTION recommandée = "transfert_prioritaire" SI une boutique voisine a un surplus
       SINON "réapprovisionnement_urgent"
```

Autres règles à inclure : rupture silencieuse (stock bas mais vente stable — priorité moindre), sur-stock (rotation trop faible — capital immobilisé), alerte réputation (chute de note + baisse de vente simultanée), transfert non rentable (coût transfert > gain estimé → ne pas recommander même si le stock le permettrait).

**Limite assumée à annoncer au jury** : les seuils (seuil_min, facteur 1.2, etc.) sont pour l'instant fixés manuellement par produit/catégorie. C'est acceptable pour un MVP ; en V2 ils devraient devenir adaptatifs (moyenne mobile + écart-type plutôt que constante).

---

## 6. Risk Engine — logique

Concevez-le comme une **fonction pure et stateless** : `evaluer_risques(etat_donnees) → liste_recommandations`. C'est le choix le plus important du projet techniquement, parce que c'est ce qui permet au simulateur de réutiliser exactement le même moteur sans dupliquer la logique.

```
Entrées : ventes récentes, stocks actuels, seuils, avis récents
Étapes :
  1. Calculer les KPI par (boutique, produit)
  2. Évaluer chaque règle métier → génère 0..n signaux de risque
  3. Agréger les signaux par (boutique, produit) → niveau de risque global
  4. Calculer revenue_at_risk pour chaque risque identifié
  5. Générer une recommandation avec priorité = f(revenue_at_risk, score_confiance)
  6. Calculer le score de confiance (voir section 8)
Sortie : liste de recommandations triées par priorité
```

---

## 7. Simulateur

Parce que le Risk Engine est stateless, le simulateur devient trivial en principe : **appliquer une modification hypothétique à une copie de l'état des données, puis rappeler `evaluer_risques()`** sur ce nouvel état et comparer au résultat "avant".

```
simuler(action, etat_actuel):
  etat_hypothetique = appliquer(action, copie(etat_actuel))
  risques_avant = evaluer_risques(etat_actuel)
  risques_apres = evaluer_risques(etat_hypothetique)
  retourner diff(risques_avant, risques_apres)  # RAR protégé, risques résiduels, etc.
```

Pour les 3 scénarios automatiques (prudent/équilibré/agressif), faites-les varier sur un seul paramètre pour rester lisible en démo : la **quantité transférée** (ex. 50%, 100%, 150% du besoin calculé) ou l'**agressivité des seuils**. Ne complexifiez pas avec plusieurs dimensions à la fois — ce serait difficile à expliquer à l'oral en 3 minutes de pitch.

---

## 8. Score de confiance

Proposition de formule simple, transparente (donc "explicable" — cohérent avec votre exigence) :

```
score_confiance = pondération(
    qualité_données   : % de champs non manquants sur l'entité concernée,
    fraîcheur         : décroissance selon l'ancienneté du dernier snapshot,
    stabilité_ventes  : inverse du coefficient de variation des ventes récentes,
    profondeur_historique : nombre de semaines de données disponibles, plafonné
)
```

Pondération suggérée pour démarrer (à ajuster) : qualité 30%, fraîcheur 20%, stabilité 30%, historique 20%. **Affichez la décomposition**, pas seulement le pourcentage final — "92% de confiance parce que : données fraîches, ventes stables, mais historique court" est bien plus convaincant en démo qu'un chiffre nu.

---

## 9. Data Health Monitor (version MVP)

Pour le hackathon, limitez-vous à un **badge de statut par boutique/produit** plutôt qu'un module séparé : % de complétude, date de dernière mise à jour, nombre de semaines d'historique disponibles. C'est en réalité un sous-produit direct du calcul du score de confiance (section 8) — ne développez pas deux systèmes différents pour la même information.

---

## 10. QR Code intelligent — exploitation par le Decision Engine (vision, pas code)

Les données collectées via le QR code alimenteraient trois flux distincts vers le moteur :
- **Traçabilité** → enrichit `historique_rupture` et la fiabilité du lien production → point de vente (utile pour distinguer rupture logistique vs rupture de demande).
- **Avis/réclamations scannés** → alimente directement `avis_client`, avec un avantage : le sentiment est rattaché à un produit et un lot précis, pas seulement à une boutique — ça affine nettement le KPI Réputation.
- **Fidélité/comportement d'achat** → nouvelle dimension `client` exploitable pour un futur module de prévision de demande personnalisée (hors scope MVP).

À mentionner au jury comme "roadmap", sans l'implémenter.

---

## Ce que je recommande de coder en priorité pour la démo (ordre)

1. Dataset synthétique avec patterns volontaires
2. Modèle de données (tables Distribution + Réputation)
3. KPI de base + Risk Engine (règles Distribution d'abord, Réputation ensuite)
4. Revenue at Risk + score de confiance
5. Simulateur (au moins 1 scénario manuel, puis les 3 automatiques si le temps le permet)
6. Badge Data Health simplifié
7. QR code : slide de vision uniquement

Dites-moi lequel de ces blocs vous voulez qu'on détaille en premier — je peux descendre au niveau SQL (schéma de tables + contraintes) ou écrire le pseudocode/Python du Risk Engine directement.
