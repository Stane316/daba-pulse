"""Export d'un résumé décisionnel traçable (JSON / Markdown)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from app.core.config import HYPOTHESES
from app.engines.data_loader import DataStore
from app.engines.decision_engine import get_decision
from app.engines.risk_engine import get_situation
from app.engines.simulator import simulate


def build_decision_summary(
    store: DataStore,
    situation_id: str,
    quantite: float | None = None,
    format: Literal["json", "markdown"] = "json",
) -> dict[str, Any] | str:
    """Assemble situation + décision + simulation en résumé exportable."""
    situation = get_situation(store, situation_id)
    if not situation:
        raise KeyError(f"Situation introuvable: {situation_id}")

    decision = get_decision(store, situation_id)
    simulation = simulate(store, situation_id, quantite=quantite)

    payload: dict[str, Any] = {
        "titre": "DabaPulse — Résumé décisionnel",
        "genere_le": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "donnees_synthetiques": True,
        "disclaimer": HYPOTHESES["disclaimer"],
        "hypotheses_version": HYPOTHESES["version"],
        "devise": HYPOTHESES["devise"],
        "situation": {
            "id": situation.id,
            "scope": situation.scope,
            "type_risque": situation.type_risque,
            "severite": situation.severite,
            "signal": situation.signal,
            "boutique": situation.boutique.model_dump() if situation.boutique else None,
            "produit": situation.produit.model_dump() if situation.produit else None,
            "horizon_jours": situation.horizon_jours,
            "demande_attendue": situation.demande_attendue,
            "stock_disponible": situation.stock_disponible,
            "deficit_potentiel": situation.deficit_potentiel,
            "prix_unitaire": situation.prix_unitaire,
            "revenue_at_risk": situation.revenue_at_risk,
            "confiance": situation.confiance,
            "niveau_confiance": situation.niveau_confiance,
            "drivers": [d.model_dump() for d in situation.drivers],
            "hypotheses": [h.model_dump() for h in situation.hypotheses],
        },
        "decision": None,
        "simulation": None,
        "synthese": {},
    }

    if decision:
        payload["decision"] = {
            "id": decision.id,
            "type_action": decision.type_action,
            "libelle": decision.libelle,
            "description": decision.description,
            "quantite": decision.quantite,
            "boutique_destination": (
                decision.boutique_destination.model_dump()
                if decision.boutique_destination
                else None
            ),
            "boutique_source": (
                decision.boutique_source.model_dump() if decision.boutique_source else None
            ),
            "score_priorite": decision.score_priorite,
            "confiance": decision.confiance,
            "raisons": decision.raisons,
            "revenue_at_risk_avant": decision.revenue_at_risk_avant,
            "revenu_potentiellement_protege": decision.revenu_potentiellement_protege,
        }

    if simulation:
        payload["simulation"] = {
            "action_libelle": simulation.action_libelle,
            "quantite_simulee": simulation.quantite_simulee,
            "revenue_at_risk_avant": simulation.revenue_at_risk_avant,
            "revenue_at_risk_apres": simulation.revenue_at_risk_apres,
            "revenu_potentiellement_protege": simulation.revenu_potentiellement_protege,
            "disponibilite_avant": simulation.disponibilite_avant,
            "disponibilite_apres": simulation.disponibilite_apres,
            "metriques": [m.model_dump() for m in simulation.metriques],
        }

    rar_avant = situation.revenue_at_risk
    rar_apres = simulation.revenue_at_risk_apres if simulation else rar_avant
    protege = (
        simulation.revenu_potentiellement_protege
        if simulation
        else (decision.revenu_potentiellement_protege if decision else 0)
    )
    payload["synthese"] = {
        "quoi": decision.libelle if decision else situation.signal,
        "ou": (
            (
                decision.boutique_destination.nom
                if decision and decision.boutique_destination
                else None
            )
            or (situation.boutique.nom if situation.boutique else "Global")
        ),
        "combien": decision.quantite if decision else None,
        "revenue_at_risk_avant": rar_avant,
        "revenue_at_risk_apres": rar_apres,
        "revenu_potentiellement_protege": protege,
        "confiance": situation.confiance,
    }

    if format == "markdown":
        return render_markdown(payload)
    return payload


def render_markdown(payload: dict[str, Any]) -> str:
    sit = payload["situation"]
    dec = payload.get("decision") or {}
    sim = payload.get("simulation") or {}
    syn = payload.get("synthese") or {}
    boutique = (sit.get("boutique") or {}).get("nom", "Global")
    produit = (sit.get("produit") or {}).get("nom", "—")

    lines = [
        f"# {payload['titre']}",
        "",
        f"_Généré le {payload['genere_le']}_",
        "",
        "> **Données synthétiques** — estimations illustratives, non des données réelles DABA.",
        "",
        "## Synthèse",
        "",
        f"- **Quoi :** {syn.get('quoi', '—')}",
        f"- **Où :** {syn.get('ou', '—')}",
        f"- **Combien :** {syn.get('combien', '—')}",
        f"- **RaR avant :** {_fcfa(syn.get('revenue_at_risk_avant'))}",
        f"- **RaR après (simulé) :** {_fcfa(syn.get('revenue_at_risk_apres'))}",
        f"- **Revenu potentiellement protégé :** {_fcfa(syn.get('revenu_potentiellement_protege'))}",
        f"- **Confiance :** {syn.get('confiance', '—')}",
        "",
        "## Situation",
        "",
        f"- **ID :** `{sit.get('id')}`",
        f"- **Périmètre :** {sit.get('scope')}",
        f"- **Sévérité :** {sit.get('severite')}",
        f"- **Boutique :** {boutique}",
        f"- **Produit :** {produit}",
        f"- **Signal :** {sit.get('signal')}",
        f"- **Stock :** {sit.get('stock_disponible')}",
        f"- **Demande attendue :** {sit.get('demande_attendue')}",
        f"- **Déficit :** {sit.get('deficit_potentiel')}",
        f"- **Prix unitaire :** {_fcfa(sit.get('prix_unitaire'))}",
        f"- **Revenue-at-Risk :** {_fcfa(sit.get('revenue_at_risk'))}",
        "",
        "### Drivers",
        "",
    ]
    for d in sit.get("drivers") or []:
        lines.append(f"- **{d.get('libelle')}** — {d.get('impact')}")

    if dec:
        lines += [
            "",
            "## Décision recommandée",
            "",
            f"- **Action :** {dec.get('libelle')}",
            f"- **Type :** {dec.get('type_action')}",
            f"- **Quantité :** {dec.get('quantite')}",
            f"- **Score priorité :** {dec.get('score_priorite')}",
            f"- **RaR avant :** {_fcfa(dec.get('revenue_at_risk_avant'))}",
            f"- **Protégé estimé :** {_fcfa(dec.get('revenu_potentiellement_protege'))}",
            "",
            "### Raisons",
            "",
        ]
        for r in dec.get("raisons") or []:
            lines.append(f"- {r}")

    if sim:
        lines += [
            "",
            "## Simulation What-if",
            "",
            f"- **Scénario :** {sim.get('action_libelle')}",
            f"- **Quantité simulée :** {sim.get('quantite_simulee')}",
            f"- **RaR avant → après :** {_fcfa(sim.get('revenue_at_risk_avant'))} → {_fcfa(sim.get('revenue_at_risk_apres'))}",
            f"- **Revenu protégé :** {_fcfa(sim.get('revenu_potentiellement_protege'))}",
            f"- **Disponibilité :** {sim.get('disponibilite_avant')} → {sim.get('disponibilite_apres')}",
            "",
        ]

    lines += [
        "## Avertissement",
        "",
        payload.get("disclaimer", HYPOTHESES["disclaimer"]),
        "",
        f"_Hypothèses moteur v{payload.get('hypotheses_version', '?')} — DabaPulse_",
        "",
    ]
    return "\n".join(lines)


def _fcfa(value: Any) -> str:
    if value is None:
        return "—"
    try:
        return f"{float(value):,.0f} FCFA".replace(",", " ")
    except (TypeError, ValueError):
        return str(value)

