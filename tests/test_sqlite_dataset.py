"""Tests INCREMENT B — Dataset SQLite (6 721 lignes) + Risk Engine pure.

Couvre :
- présence de la base SQLite `growth_decision_os.db` et du CSV (6 721 lignes) ;
- chargement via SQLite (DataStore.load préfère la base) ;
- scénario démo préservé : B001×P005 reste la situation #1 (486 000 FCFA) et
  aucune situation ne dépasse ce RaR (garde-fou de la narration démo) ;
- Risk Engine PURE : evaluate_state(charger_etat_depuis_sqlite(...)) donne
  exactement les mêmes résultats que le chemin DataStore (non-régression).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.engines.data_loader import (  # noqa: E402
    DataStore,
    charger_etat_depuis_sqlite,
)
from app.engines.risk_engine import (  # noqa: E402
    build_executive_summary,
    evaluate_state,
)

DATA_PATH = ROOT / "data" / "sample"
DB_FILE = DATA_PATH / "growth_decision_os.db"


# ---------------------------------------------------------------------------
# 1. Dataset — présence, volume, cohérence CSV ↔ SQLite
# ---------------------------------------------------------------------------


def test_sqlite_db_exists():
    assert DB_FILE.exists(), "growth_decision_os.db absent — lancer le générateur"


def test_dataset_volume_6721():
    """5 boutiques × 16 produits × 84 jours = 6 720 lignes + entête = 6 721."""
    lines = (DATA_PATH / "ventes_stocks.csv").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 6721, f"CSV: {len(lines)} lignes (attendu 6721)"
    assert len((DATA_PATH / "produits.csv").read_text(encoding="utf-8").splitlines()) == 17
    assert len((DATA_PATH / "boutiques.csv").read_text(encoding="utf-8").splitlines()) == 6


def test_sqlite_and_csv_same_rows():
    import sqlite3

    con = sqlite3.connect(DB_FILE)
    try:
        nb = con.execute("SELECT COUNT(*) FROM ventes").fetchone()[0]
    finally:
        con.close()
    assert nb == 6720


def test_load_prefers_sqlite():
    s = DataStore()
    s.load(DATA_PATH)
    assert s.is_loaded
    assert "sqlite" in s._source_label
    status = s.status()
    assert status.valide
    assert status.nb_lignes == 6720
    assert status.nb_boutiques == 5
    assert status.nb_produits == 16
    assert status.periode_debut == "2026-05-28"
    assert status.periode_fin == "2026-08-19"


# ---------------------------------------------------------------------------
# 2. Scénario démo préservé (narration non régressive)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def summary():
    s = DataStore()
    s.load(DATA_PATH)
    return build_executive_summary(s)


def test_demo_scenario_is_top_situation(summary):
    top = summary.situations[0]
    assert top.id == "dist-B001-P005", f"Situation #1 changée: {top.id}"
    assert top.stock_disponible == 8
    assert top.demande_attendue == 35
    assert top.deficit_potentiel == 27
    assert top.revenue_at_risk == 486000
    assert top.severite == "critique"


def test_no_situation_exceeds_demo_rar(summary):
    """Garde-fou : le scénario démo doit rester le plus exposé."""
    mx = max(s.revenue_at_risk for s in summary.situations)
    assert mx == 486000, f"Une situation dépasse le scénario démo: {mx}"


def test_decision_source_still_cocody(summary):
    from app.engines.decision_engine import get_decision

    s = DataStore()
    s.load(DATA_PATH)
    dec = get_decision(s, "dist-B001-P005")
    assert dec is not None
    if dec.boutique_source:
        assert dec.boutique_source.id in {"B002", "B003", "B004", "B005"}


# ---------------------------------------------------------------------------
# 3. Risk Engine PURE — evaluate_state == chemin DataStore (non-régression)
# ---------------------------------------------------------------------------


def test_pure_engine_matches_store_path():
    etat = charger_etat_depuis_sqlite(DATA_PATH)
    assert "ventes" in etat and len(etat["ventes"]) == 6720

    s_pure = evaluate_state(etat)
    s_store = build_executive_summary(DataStore.from_state(etat))

    assert s_pure.revenue_at_risk_total == s_store.revenue_at_risk_total
    assert s_pure.revenue_at_risk_distribution == s_store.revenue_at_risk_distribution
    assert s_pure.revenue_at_risk_reputation == s_store.revenue_at_risk_reputation
    assert s_pure.nb_situations_total == s_store.nb_situations_total
    assert [s.id for s in s_pure.situations] == [s.id for s in s_store.situations]
    assert s_pure.revenue_at_risk_total > 0


def test_pure_engine_reputation_unchanged():
    etat = charger_etat_depuis_sqlite(DATA_PATH)
    s = evaluate_state(etat)
    assert s.revenue_at_risk_reputation == 129600
    assert s.donnees_synthetiques is True
