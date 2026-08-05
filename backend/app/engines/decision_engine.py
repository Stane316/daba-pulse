"""Decision Engine — transforme les risques en actions prioritaires.

Logique déterministe, explicable, sans LLM.
"""

from __future__ import annotations

from typing import Any

from app.engines.analytics import analyze_all
from app.engines.data_loader import DataStore
from app.engines.risk_engine import (
    _boutique_info,
    _niveau_confiance,
    build_executive_summary,
    get_situation,
)
from app.models.schemas import DecisionAction, SituationRisque


def _find_stock_source(
    store: DataStore,
    produit_id: str,
    destination_id: str,
    quantite_besoin: float,
) -> tuple[dict[str, Any] | None, float]:
    """Trouve la meilleure boutique source (surplus) pour un produit."""
    analyses = analyze_all(store)
    candidates = []
    for a in analyses:
        if a["produit_id"] != produit_id:
            continue
        if a["boutique_id"] == destination_id:
            continue
        # surplus au-dessus de la cible + marge de sécurité
        transferable = max(0.0, a["stock"] - a["stock_cible"])
        # aussi autoriser un peu au-dessus de la demande
        if transferable < 3:
            # fallback: stock - demande_attendue * 0.5
            transferable = max(0.0, a["stock"] - a["demande_attendue"] * 0.5)
        if transferable >= 3:
            candidates.append(
                {
                    "boutique_id": a["boutique_id"],
                    "transferable": transferable,
                    "stock": a["stock"],
                    "surplus": a["surplus"],
                }
            )

    if not candidates:
        return None, 0.0

    candidates.sort(key=lambda c: c["transferable"], reverse=True)
    best = candidates[0]
    qty = min(quantite_besoin, best["transferable"])
    return best, qty


def decide_for_situation(
    store: DataStore,
    situation: SituationRisque,
) -> DecisionAction:
    """Produit la recommandation principale pour une situation."""

    if situation.scope == "reputation":
        return _decide_reputation(situation)

    return _decide_distribution(store, situation)


def _decide_distribution(
    store: DataStore,
    situation: SituationRisque,
) -> DecisionAction:
    bid = situation.boutique.id if situation.boutique else ""
    pid = situation.produit.id if situation.produit else ""
    deficit = situation.deficit_potentiel or 0
    stock = situation.stock_disponible or 0
    stock_cible = situation.stock_cible or 0
    prix = situation.prix_unitaire or 0
    rar = situation.revenue_at_risk

    if situation.type_risque == "surstock":
        # Recommander transfert sortant vers boutique en déficit
        analyses = analyze_all(store)
        targets = [
            a
            for a in analyses
            if a["produit_id"] == pid
            and a["boutique_id"] != bid
            and a["deficit_potentiel"] > 0
        ]
        targets.sort(key=lambda a: a["deficit_potentiel"], reverse=True)
        qty = min(situation.surplus or 0, targets[0]["deficit_potentiel"] if targets else 0)
        dest = targets[0] if targets else None

        libelle = (
            f"Transférer {qty:.0f} unités de {situation.produit.nom if situation.produit else pid} "
            f"depuis {situation.boutique.nom if situation.boutique else bid}"
            + (
                f" vers {store.boutique(dest['boutique_id'])['nom']}"
                if dest
                else " vers une boutique en déficit"
            )
        )
        protege = round(qty * prix, 0) if dest else 0
        raisons = [
            f"Surplus de {situation.surplus:.0f} unités au-dessus de la cible ({stock_cible:.0f})",
            f"Stock actuel : {stock:.0f} unités",
        ]
        if dest:
            raisons.append(
                f"Déficit de {dest['deficit_potentiel']:.0f} unités détecté à "
                f"{store.boutique(dest['boutique_id'])['nom']}"
            )
            raisons.append(
                f"Revenu potentiellement récupérable côté destination : {protege:,.0f} FCFA"
            )

        return DecisionAction(
            id=f"act-{situation.id}",
            situation_id=situation.id,
            type_action="transfert_sortant",
            libelle=libelle,
            description=(
                "Réallouer le surplus vers une boutique en tension pour "
                "réduire le déséquilibre de distribution."
            ),
            produit=situation.produit,
            boutique_destination=_boutique_info(store, dest["boutique_id"]) if dest else None,
            boutique_source=situation.boutique,
            quantite=qty if qty else situation.surplus,
            score_priorite=_score(situation, qty * prix if dest else rar * 0.3),
            confiance=situation.confiance,
            niveau_confiance=situation.niveau_confiance,
            raisons=raisons,
            revenue_at_risk_avant=rar,
            revenu_potentiellement_protege=protege,
            scope="distribution",
            metriques={
                "surplus_disponible": situation.surplus,
                "stock_source": stock,
            },
        )

    # Rupture / demande croissante → réallocation entrante
    # Quantité reco = déficit, bornée par stock_cible - stock si plus grand
    besoin = max(deficit, max(0, stock_cible - stock))
    # Arrondir à l'entier
    besoin = float(round(besoin))

    source, qty_dispo = _find_stock_source(store, pid, bid, besoin)
    quantite = float(round(qty_dispo if source else besoin))

    if source:
        source_info = _boutique_info(store, source["boutique_id"])
        type_action = "reallocation"
        libelle = (
            f"Réallouer {quantite:.0f} unités de "
            f"{situation.produit.nom if situation.produit else pid} "
            f"depuis {source_info.nom} vers "
            f"{situation.boutique.nom if situation.boutique else bid}"
        )
        description = (
            f"Transférer {quantite:.0f} unités depuis {source_info.nom} "
            f"(stock disponible excédentaire) pour combler le déficit de "
            f"{deficit:.0f} unités sur l'horizon de {situation.horizon_jours} jours."
        )
    else:
        source_info = None
        type_action = "reapprovisionnement"
        libelle = (
            f"Réapprovisionner {situation.boutique.nom if situation.boutique else bid} "
            f"avec {quantite:.0f} unités de "
            f"{situation.produit.nom if situation.produit else pid}"
        )
        description = (
            f"Aucun surplus interne suffisant détecté. "
            f"Réapprovisionner {quantite:.0f} unités depuis l'entrepôt / production."
        )

    # Revenu protégé = min(quantite, deficit) × prix
    unites_protegees = min(quantite, deficit) if deficit else quantite
    protege = round(unites_protegees * prix, 0)

    raisons = [
        f"Déficit potentiel de {deficit:.0f} unités "
        f"(demande {situation.demande_attendue:.0f} − stock {stock:.0f})",
        f"Revenue-at-Risk actuel : {rar:,.0f} FCFA",
        f"Prix unitaire net : {prix:,.0f} FCFA",
    ]
    if source:
        raisons.append(
            f"Source identifiée : {source_info.nom} "
            f"(~{source['transferable']:.0f} unités transférables)"
        )
    raisons.append(
        f"Quantité recommandée : {quantite:.0f} "
        f"→ revenu potentiellement protégé : {protege:,.0f} FCFA"
    )
    if situation.metriques_extra.get("tendance", 1) >= 1.05:
        raisons.append(
            f"Tendance de demande haussière "
            f"(×{situation.metriques_extra['tendance']:.2f})"
        )

    # Alternative : quantité partielle (70 %)
    alt_qty = float(round(quantite * 0.7))
    alt_protege = round(min(alt_qty, deficit) * prix, 0)
    alternative = DecisionAction(
        id=f"act-{situation.id}-alt",
        situation_id=situation.id,
        type_action=type_action,
        libelle=f"Alternative : transférer {alt_qty:.0f} unités (approche progressive)",
        description=(
            f"Réallocation partielle de {alt_qty:.0f} unités — "
            f"réduit le risque tout en limitant le mouvement de stock."
        ),
        produit=situation.produit,
        boutique_destination=situation.boutique,
        boutique_source=source_info,
        quantite=alt_qty,
        score_priorite=_score(situation, alt_protege) * 0.85,
        confiance=max(0.5, situation.confiance - 0.05),
        niveau_confiance=_niveau_confiance(max(0.5, situation.confiance - 0.05)),  # type: ignore[arg-type]
        raisons=[
            f"Approche progressive : {alt_qty:.0f} unités au lieu de {quantite:.0f}",
            f"Revenu protégé estimé : {alt_protege:,.0f} FCFA",
            "Utile si la capacité logistique est contrainte",
        ],
        revenue_at_risk_avant=rar,
        revenu_potentiellement_protege=alt_protege,
        scope="distribution",
    )

    return DecisionAction(
        id=f"act-{situation.id}",
        situation_id=situation.id,
        type_action=type_action,
        libelle=libelle,
        description=description,
        produit=situation.produit,
        boutique_destination=situation.boutique,
        boutique_source=source_info,
        quantite=quantite,
        score_priorite=_score(situation, protege),
        confiance=situation.confiance,
        niveau_confiance=situation.niveau_confiance,
        raisons=raisons,
        revenue_at_risk_avant=rar,
        revenu_potentiellement_protege=protege,
        alternative=alternative,
        scope="distribution",
        metriques={
            "deficit": deficit,
            "stock_actuel": stock,
            "stock_apres_estime": stock + quantite,
            "unites_protegees": unites_protegees,
        },
    )


def _decide_reputation(situation: SituationRisque) -> DecisionAction:
    m = situation.metriques_extra
    note = m.get("note_avis_google", 0)
    nb_avis = m.get("nb_avis_google", 0)
    engagement = m.get("engagement_reseaux", 0)
    conv = m.get("taux_conversion_global", 0)
    rar = situation.revenue_at_risk

    # Prioriser l'action selon le driver dominant
    if note < 3.5 or nb_avis < 10:
        type_action = "collecte_avis"
        libelle = (
            "Lancer une campagne de collecte d'avis Google "
            "(SMS / email post-achat)"
        )
        description = (
            f"La note Google est à {note}/5 avec seulement {nb_avis} avis. "
            "Une campagne systématique de collecte d'avis après chaque achat "
            "vise 4,2/5 et ~15 avis sous 30 jours."
        )
        cibles = {
            "note_cible": 4.2,
            "avis_cibles": 15,
            "engagement_cible": max(0.035, engagement * 3),
        }
    elif engagement < 0.01:
        type_action = "strategie_contenu"
        libelle = "Revoir la stratégie de contenu réseaux sociaux"
        description = (
            f"Engagement à {engagement * 100:.1f} %. "
            "Publier questions, photos d'équipe et courtes vidéos pour viser 3,5 %."
        )
        cibles = {
            "note_cible": note,
            "avis_cibles": max(nb_avis, 10),
            "engagement_cible": 0.035,
        }
    else:
        type_action = "optimisation_gmb"
        libelle = "Optimiser la fiche Google Business (photos, horaires, description)"
        description = (
            "Améliorer la visibilité locale et la conversion des recherches en visites."
        )
        cibles = {
            "note_cible": max(note, 4.0),
            "avis_cibles": max(nb_avis, 12),
            "engagement_cible": max(0.03, engagement),
        }

    # Estimation de réduction : si facteur tombe à ~0, RaR → 0
    protege = round(rar * 0.85, 0)  # hypothèse conservative 85 %

    raisons = [
        f"Note Google : {note}/5 (seuil critique 3,5)",
        f"Nombre d'avis : {nb_avis}",
        f"Engagement réseaux : {engagement * 100:.1f} %",
        f"Taux de conversion : {conv * 100:.1f} %",
        f"Revenue-at-Risk réputation : {rar:,.0f} FCFA",
        "Une meilleure réputation peut augmenter la demande globale (~+20 % estimé)",
    ]

    alt = DecisionAction(
        id=f"act-{situation.id}-alt",
        situation_id=situation.id,
        type_action="optimisation_gmb",
        libelle="Alternative : optimiser d'abord la fiche Google Business",
        description=(
            "Action plus légère : photos, horaires, description — "
            "impact plus faible mais déploiement immédiat."
        ),
        score_priorite=_score(situation, protege * 0.5) * 0.8,
        confiance=max(0.5, situation.confiance - 0.08),
        niveau_confiance=_niveau_confiance(max(0.5, situation.confiance - 0.08)),  # type: ignore[arg-type]
        raisons=[
            "Déploiement immédiat sans campagne client",
            f"Impact estimé plus modéré (~{protege * 0.4:,.0f} FCFA protégés)",
        ],
        revenue_at_risk_avant=rar,
        revenu_potentiellement_protege=round(protege * 0.4, 0),
        scope="reputation",
    )

    return DecisionAction(
        id=f"act-{situation.id}",
        situation_id=situation.id,
        type_action=type_action,
        libelle=libelle,
        description=description,
        quantite=None,
        score_priorite=_score(situation, protege),
        confiance=situation.confiance,
        niveau_confiance=situation.niveau_confiance,
        raisons=raisons,
        revenue_at_risk_avant=rar,
        revenu_potentiellement_protege=protege,
        alternative=alt,
        scope="reputation",
        metriques=cibles,
    )


def _score(situation: SituationRisque, impact: float) -> float:
    sev = {"critique": 1.0, "eleve": 0.75, "modere": 0.5, "faible": 0.25}
    base = sev.get(situation.severite, 0.4)
    # normaliser impact (log-ish)
    impact_n = min(1.0, impact / 500_000) if impact else 0
    return round((base * 0.55 + impact_n * 0.35 + situation.confiance * 0.10) * 100, 1)


def get_decision(store: DataStore, situation_id: str) -> DecisionAction | None:
    situation = get_situation(store, situation_id)
    if not situation:
        return None
    return decide_for_situation(store, situation)


def get_top_decisions(store: DataStore, limit: int = 5) -> list[DecisionAction]:
    summary = build_executive_summary(store)
    # Prioriser les non-surstock pour la démo
    situations = [
        s
        for s in summary.situations
        if s.type_risque != "surstock" or s.severite in ("critique", "eleve")
    ]
    decisions = [decide_for_situation(store, s) for s in situations[:limit]]
    decisions.sort(key=lambda d: d.score_priorite, reverse=True)
    return decisions
