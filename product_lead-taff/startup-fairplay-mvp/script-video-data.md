# Script vidéo — partie Data Lead (DabaPulse)

Durée indicative : 60-90 secondes (à ajuster selon le temps total alloué
par l'équipe). Chaque chiffre cité ici vient de la matrice de preuve —
en cas de doute pendant le tournage, se référer à `matrice-de-preuve.md`.

---

## 1. Le rôle (5-10 sec)

> "Je suis responsable de la partie données de DabaPulse : je garantis
> que chaque recommandation affichée à l'écran repose sur un calcul
> vérifiable, pas sur une estimation en l'air."

## 2. Le problème traité (10-15 sec)

> "Le moteur répond à une seule question : quel produit envoyer, en
> quelle quantité, vers quelle boutique, pour réduire le revenu exposé
> par une rupture de stock ou un problème de réputation."

## 3. Démonstration — dans l'ordre à montrer à l'écran

1. **Montrer le badge Data Health en premier** (avant toute recommandation) :
   > "Avant de faire confiance à une recommandation, on regarde d'abord
   > l'état des données : ici, 100% de complétude, 9,9 semaines
   > d'historique. Le statut est affiché honnêtement — s'il se dégrade,
   > le badge le montre."
   *(Dire clairement : "ce dataset est synthétique, généré pour la démonstration" — ne jamais le présenter comme des données réelles de DABA.)*

2. **Montrer une recommandation prioritaire** (ex. Cotonou-Centre / Farine) :
   > "Le moteur détecte ici un risque de rupture avec un Revenue-at-Risk
   > estimé, et un score de confiance décomposé — pas juste un chiffre
   > brut, mais une explication de pourquoi on peut lui faire confiance."

3. **Montrer la suggestion de transfert automatique** :
   > "Il ne se contente pas d'alerter : il propose une action concrète —
   > quelle boutique a un excédent, combien transférer, et pourquoi."

4. **Montrer la simulation AVANT/APRÈS** :
   > "Avant d'agir, on simule : voici l'impact du transfert sur le revenu
   > exposé, avant de prendre la décision réelle."

## 4. Phrase de transparence à ne jamais omettre (5 sec)

> "Ces seuils sont des hypothèses de conception, ajustables — l'étape
> suivante est de les recalibrer sur les données réelles de DABA."

## 5. Clôture (5-10 sec)

> "Résultat : des décisions de distribution basées sur des règles
> explicables, pas sur une boîte noire."

---

## Réponses prêtes si le jury pose une question pendant/après la vidéo

**"D'où viennent vos chiffres ?"**
> "Le dataset actuel est synthétique — généré pour démontrer que le
> moteur fonctionne correctement. Chaque formule (Revenue-at-Risk,
> score de confiance) est documentée dans notre matrice de preuve, avec
> son statut : donnée, hypothèse, ou estimation."

**"Comment on sait que ça marche sur de vraies données DABA ?"**
> "Le moteur est conçu pour être agnostique à la source : il lit un
> format de données standard (boutiques, ventes, stocks, avis). Le
> brancher sur le fichier réel de DABA ne demande pas de réécrire la
> logique, juste de charger les vraies données à la place du dataset
> de démonstration."

**"Le score de confiance, c'est fiable ?"**
> "C'est une estimation transparente basée sur 4 critères pondérés
> (qualité, fraîcheur, stabilité des ventes, profondeur d'historique) —
> on montre toujours sa décomposition, jamais juste un pourcentage nu."

---

## Checklist avant le tournage

- [ ] Le serveur API (`uvicorn api:app`) tourne et répond sur `/docs`
- [ ] `growth_decision_os.db` est bien la dernière version (régénérée le 18 août)
- [ ] Le badge Data Health affiche un statut cohérent (pas "critique")
- [ ] Avoir `matrice-de-preuve.md` ouvert en second écran au cas où une question surgit
