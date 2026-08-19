# Slide de vision — QR Code intelligent (au-delà du MVP)

**Statut : non implémenté dans ce MVP — vision post-hackathon.**
*(à afficher explicitement sur le slide — ne jamais présenter comme une fonctionnalité déjà construite)*

---

## Titre accroche

> Chaque emballage devient une source de données en temps réel

## Ce que ça débloque, une fois activé

- **Traçabilité produit** — relie chaque unité vendue à son lot, sa boutique, sa date. Enrichit directement le Risk Engine pour distinguer une rupture logistique d'une rupture de demande.
- **Avis clients rattachés au produit exact** (pas juste à la boutique) — améliore la précision du signal Réputation déjà présent dans DabaPulse.
- **Programme de fidélité & réclamations** — nouvelle source de données comportementales, exploitable par le Decision Engine pour des recommandations personnalisées.

## Comment ça s'intègre à l'architecture existante

QR scanné → nouvelle donnée → **même pipeline** (Data Foundation → Risk Detection → Decision Engine) — **aucune refonte nécessaire**, le moteur actuel est déjà conçu pour absorber cette donnée.

---

## Note pour la présentation orale (à dire, pas à écrire sur le slide)

> "On ne le construit pas maintenant parce que ça demande une intégration physique (impression, scan) hors du délai du hackathon — mais l'architecture qu'on vous montre aujourd'hui absorbe cette donnée sans modification, ce qui prouve que le choix technique n'est pas jetable."
