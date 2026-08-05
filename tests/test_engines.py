"""Tests des moteurs analytiques DabaPulse."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.engines.data_loader import DataStore  # noqa: E402
from app.engines.decision_engine import get_decision, get_top_decisions  # noqa: E402
from app.engines.risk_engine import build_executive_summary  # noqa: E402
from app.engines.simulator import simulate  # noqa: E402


@pytest.fixture(scope="module")
def store() -> DataStore:
    data_path = ROOT / "data" / "sample"
    if not (data_path / "ventes_stocks.csv").exists():
        # generate
        sys.path.insert(0, str(ROOT / "scripts"))
        from generate_synthetic_data import main as gen

        gen()
    s = DataStore()
    s.load(data_path)
    return s


def test_data_loaded(store: DataStore):
    assert store.is_loaded
    assert len(store.ventes) > 0
    assert len(store.boutiques) >= 5
    status = store.status()
    assert status.valide
    assert status.type == "synthetiques"


def test_executive_summary(store: DataStore):
    summary = build_executive_summary(store)
    assert summary.revenue_at_risk_total > 0
    assert summary.nb_situations_total > 0
    assert summary.donnees_synthetiques is True
    assert any(s.severite == "critique" for s in summary.situations)


def test_demo_scenario_plateau_premium(store: DataStore):
    """Scénario démo : B001 × P005 doit être critique avec ~486k RaR."""
    summary = build_executive_summary(store)
    target = next(
        (
            s
            for s in summary.situations
            if s.boutique
            and s.boutique.id == "B001"
            and s.produit
            and s.produit.id == "P005"
        ),
        None,
    )
    assert target is not None, "Situation B001/P005 absente"
    assert target.stock_disponible == 8
    assert target.deficit_potentiel is not None and target.deficit_potentiel >= 20
    assert target.revenue_at_risk >= 300_000
    assert target.severite in ("critique", "eleve")


def test_reputation_risk(store: DataStore):
    summary = build_executive_summary(store)
    rep = [s for s in summary.situations if s.scope == "reputation"]
    assert len(rep) >= 1
    assert rep[0].revenue_at_risk > 0


def test_decision_engine(store: DataStore):
    decisions = get_top_decisions(store, limit=3)
    assert len(decisions) >= 1
    top = decisions[0]
    assert top.libelle
    assert top.score_priorite > 0
    assert top.revenu_potentiellement_protege >= 0
    assert len(top.raisons) >= 1


def test_decision_reallocation_has_source(store: DataStore):
    summary = build_executive_summary(store)
    sit = next(
        s
        for s in summary.situations
        if s.boutique
        and s.boutique.id == "B001"
        and s.produit
        and s.produit.id == "P005"
    )
    dec = get_decision(store, sit.id)
    assert dec is not None
    assert dec.quantite and dec.quantite > 0
    # Prefer source from Cocody surplus
    if dec.boutique_source:
        assert dec.boutique_source.id in {"B002", "B003", "B004", "B005"}


def test_simulation_reduces_rar(store: DataStore):
    summary = build_executive_summary(store)
    sit = next(s for s in summary.situations if s.scope == "distribution" and s.deficit_potentiel)
    result = simulate(store, sit.id)
    assert result is not None
    assert result.revenue_at_risk_apres <= result.revenue_at_risk_avant
    assert result.revenu_potentiellement_protege >= 0


def test_simulation_custom_quantity(store: DataStore):
    summary = build_executive_summary(store)
    sit = next(
        s
        for s in summary.situations
        if s.boutique and s.boutique.id == "B001" and s.produit and s.produit.id == "P005"
    )
    result = simulate(store, sit.id, quantite=30)
    assert result is not None
    assert result.quantite_simulee == 30
    # 8 + 30 = 38 >= demande ~35 → déficit ~0
    deficit_m = next(m for m in result.metriques if m.cle == "deficit")
    assert float(deficit_m.apres) <= 5
    assert result.revenu_potentiellement_protege >= 400_000


def test_rar_formula_traceable(store: DataStore):
    summary = build_executive_summary(store)
    sit = next(s for s in summary.situations if s.scope == "distribution" and s.deficit_potentiel)
    expected = round((sit.deficit_potentiel or 0) * (sit.prix_unitaire or 0), 0)
    assert sit.revenue_at_risk == expected
