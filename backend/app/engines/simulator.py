"""What-if Simulator — compare état actuel vs scénario."""

from __future__ import annotations

from app.core.config import HYPOTHESES
from app.engines.data_loader import DataStore
from app.engines.decision_engine import get_decision
from app.engines.risk_engine import get_situation
from app.models.schemas import Hypothese, SimulationMetric, SimulationResult


def simulate(
    store: DataStore,
    situation_id: str,
    quantite: float | None = None,
    params: dict | None = None,
) -> SimulationResult | None:
    situation = get_situation(store, situation_id)
    if not situation:
        return None

    decision = get_decision(store, situation_id)
    params = params or {}

    if situation.scope == "reputation":
        return _simulate_reputation(situation, decision, params)

    return _simulate_distribution(situation, decision, quantite)


def _simulate_distribution(situation, decision, quantite: float | None) -> SimulationResult:
    stock = float(situation.stock_disponible or 0)
    demande = float(situation.demande_attendue or 0)
    deficit = float(situation.deficit_potentiel or 0)
    prix = float(situation.prix_unitaire or 0)
    rar_avant = float(situation.revenue_at_risk)

    qty = float(
        quantite
        if quantite is not None
        else (decision.quantite if decision and decision.quantite else deficit)
    )
    qty = max(0.0, qty)

    stock_apres = stock + qty
    deficit_apres = max(0.0, demande - stock_apres)
    rar_apres = round(deficit_apres * prix, 0)
    protege = max(0.0, rar_avant - rar_apres)

    dispo_avant = _disponibilite(stock, demande)
    dispo_apres = _disponibilite(stock_apres, demande)

    metriques = [
        SimulationMetric(
            cle="stock",
            libelle="Stock disponible",
            avant=stock,
            apres=stock_apres,
            variation=qty,
            unite="unités",
            sens_positif="hausse",
        ),
        SimulationMetric(
            cle="deficit",
            libelle="Déficit potentiel",
            avant=deficit,
            apres=deficit_apres,
            variation=round(deficit_apres - deficit, 1),
            unite="unités",
            sens_positif="baisse",
        ),
        SimulationMetric(
            cle="rar",
            libelle="Revenue-at-Risk",
            avant=rar_avant,
            apres=rar_apres,
            variation=round(rar_apres - rar_avant, 0),
            unite="FCFA",
            sens_positif="baisse",
        ),
        SimulationMetric(
            cle="disponibilite",
            libelle="Disponibilité estimée",
            avant=dispo_avant,
            apres=dispo_apres,
            variation=f"{dispo_avant} → {dispo_apres}",
            unite="",
            sens_positif="hausse",
        ),
        SimulationMetric(
            cle="couverture",
            libelle="Couverture demande",
            avant=f"{min(100, round(stock / demande * 100) if demande else 100)} %",
            apres=f"{min(100, round(stock_apres / demande * 100) if demande else 100)} %",
            variation="",
            unite="",
            sens_positif="hausse",
        ),
    ]

    action_lib = (
        decision.libelle
        if decision
        else f"Réallocation de {qty:.0f} unités"
    )

    return SimulationResult(
        situation_id=situation.id,
        action_libelle=action_libelle_with_qty(action_lib, qty, decision),
        quantite_simulee=qty,
        metriques=metriques,
        revenue_at_risk_avant=rar_avant,
        revenue_at_risk_apres=rar_apres,
        revenu_potentiellement_protege=protege,
        disponibilite_avant=dispo_avant,
        disponibilite_apres=dispo_apres,
        hypotheses=[
            Hypothese(
                cle="formule",
                libelle="RaR après simulation",
                valeur=f"max(0, {demande:.0f} − {stock_apres:.0f}) × {prix:.0f}",
                source="simulator",
            ),
            Hypothese(
                cle="quantite",
                libelle="Quantité simulée",
                valeur=qty,
                source="utilisateur" if quantite is not None else "decision_engine",
            ),
            Hypothese(
                cle="disclaimer",
                libelle="Limite",
                valeur=HYPOTHESES["disclaimer"],
                source="configuration",
            ),
        ],
        scope="distribution",
    )


def action_libelle_with_qty(base: str, qty: float, decision) -> str:
    if decision and decision.quantite and abs(decision.quantite - qty) > 0.1:
        return f"{base} (simulé : {qty:.0f} unités)"
    return base


def _disponibilite(stock: float, demande: float) -> str:
    if demande <= 0:
        return "Normale"
    ratio = stock / demande
    if ratio >= 1.0:
        return "Pleine"
    if ratio >= 0.7:
        return "Correcte"
    if ratio >= 0.4:
        return "Tendue"
    if ratio >= 0.15:
        return "Faible"
    return "Critique"


def _simulate_reputation(situation, decision, params: dict) -> SimulationResult:
    m = situation.metriques_extra
    note = float(m.get("note_avis_google", 2.5))
    nb_avis = int(m.get("nb_avis_google", 3))
    engagement = float(m.get("engagement_reseaux", 0.008))
    rar_avant = float(situation.revenue_at_risk)

    # Cibles issues de la décision ou params
    cibles = (decision.metriques if decision else {}) or {}
    note_cible = float(params.get("note_cible", cibles.get("note_cible", 4.2)))
    avis_cibles = int(params.get("avis_cibles", cibles.get("avis_cibles", 15)))
    eng_cible = float(
        params.get("engagement_cible", cibles.get("engagement_cible", 0.035))
    )

    # Recalcul simplifié du facteur de risque après action
    facteur_apres = 0.0
    if note_cible < 3.5:
        facteur_apres += 0.20
    if eng_cible < 0.01:
        facteur_apres += 0.10
    if avis_cibles == 0:
        facteur_apres += 0.15

    visiteurs = float(m.get("visiteurs_jour", 1200))
    conv = float(m.get("taux_conversion_global", 0.015))
    # +20 % demande estimée si réputation améliorée
    conv_apres = min(0.05, conv * 1.2) if facteur_apres < 0.1 else conv
    prix = float(m.get("prix_moyen", 18000))

    revenu_pot = visiteurs * conv_apres * prix
    rar_apres = round(revenu_pot * max(facteur_apres, 0.0), 0)
    # Si facteur ~0, on protège l'essentiel du RaR initial
    if facteur_apres <= 0:
        rar_apres = 0.0
    protege = max(0.0, rar_avant - rar_apres)

    metriques = [
        SimulationMetric(
            cle="note_google",
            libelle="Note Google moyenne",
            avant=note,
            apres=note_cible,
            variation=round(note_cible - note, 1),
            unite="/5",
            sens_positif="hausse",
        ),
        SimulationMetric(
            cle="nb_avis",
            libelle="Nombre d'avis",
            avant=nb_avis,
            apres=avis_cibles,
            variation=avis_cibles - nb_avis,
            unite="avis",
            sens_positif="hausse",
        ),
        SimulationMetric(
            cle="engagement",
            libelle="Engagement réseaux",
            avant=f"{engagement * 100:.1f} %",
            apres=f"{eng_cible * 100:.1f} %",
            variation=f"+{(eng_cible - engagement) * 100:.1f} pts",
            unite="",
            sens_positif="hausse",
        ),
        SimulationMetric(
            cle="rar",
            libelle="Revenue-at-Risk réputation",
            avant=rar_avant,
            apres=rar_apres,
            variation=round(rar_apres - rar_avant, 0),
            unite="FCFA",
            sens_positif="baisse",
        ),
        SimulationMetric(
            cle="demande",
            libelle="Demande estimée",
            avant="Basse",
            apres="+20 %" if facteur_apres < 0.1 else "Stable",
            variation="Améliorée" if facteur_apres < 0.1 else "—",
            unite="",
            sens_positif="hausse",
        ),
    ]

    return SimulationResult(
        situation_id=situation.id,
        action_libelle=decision.libelle if decision else "Action réputation",
        quantite_simulee=None,
        metriques=metriques,
        revenue_at_risk_avant=rar_avant,
        revenue_at_risk_apres=rar_apres,
        revenu_potentiellement_protege=protege,
        disponibilite_avant="Réputation faible",
        disponibilite_apres="Réputation renforcée",
        hypotheses=[
            Hypothese(
                cle="effet_demande",
                libelle="Effet secondaire sur la demande",
                valeur=(
                    "Une note ≥ 4,2 et un engagement ≥ 3 % "
                    "entraînent +20 % de demande estimée (hypothèse)"
                ),
                source="configuration",
            ),
            Hypothese(
                cle="disclaimer",
                libelle="Limite",
                valeur=HYPOTHESES["disclaimer"],
                source="configuration",
            ),
        ],
        scope="reputation",
    )
