"""Tests INC-20 — classification d'intention (7 intentions) + 4 blocs challengeables.

Couvre :
- classify_intent() : mapping question → intention (+ quantité extraite) ;
- /api/ai/explain : 4 blocs Faits / Hypothèses / Interprétation / Incertitude
  présents, champs historiques toujours peuplés (rétro-compatibilité).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.engines.ai_layer import IntentType, classify_intent  # noqa: E402
from app.engines.data_loader import store  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(scope="module")
def client() -> TestClient:
    data_path = ROOT / "data" / "sample"
    store.load(data_path)
    return TestClient(app)


# ---------------------------------------------------------------------------
# 1. Classification d'intention (déterministe, sans LLM)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("question", "expected_intent", "expected_q"),
    [
        ("Et si on envoyait 20 unités ?", IntentType.COMPARE, 20),
        ("Et si on n'agit pas ?", IntentType.CHALLENGE, None),
        ("Quelle hypothèse est la plus fragile ?", IntentType.LIMITS, None),
        ("Quelles sont les limites de cette recommandation ?", IntentType.LIMITS, None),
        ("Pourquoi cette quantité ?", IntentType.JUSTIFY, None),
        ("Justifie cette décision", IntentType.JUSTIFY, None),
        ("Y a-t-il une autre option ?", IntentType.ALTERNATIVE, None),
        ("Résume en 3 phrases", IntentType.RESUME, None),
        ("Pourquoi cette boutique ?", IntentType.EXPLAIN, None),
        ("Quels facteurs expliquent le risque ?", IntentType.EXPLAIN, None),
        ("Que se passe-t-il si je réduis la quantité ?", IntentType.COMPARE, None),
    ],
)
def test_classify_intent(question: str, expected_intent: IntentType, expected_q: int | None):
    intent, params = classify_intent(question)
    assert intent is expected_intent
    assert params["quantite"] == expected_q


def test_classify_extracts_quantity_only_when_number_present():
    intent, params = classify_intent("Et si on envoyait 20 unités ?")
    assert intent is IntentType.COMPARE
    assert params["quantite"] == 20
    intent2, params2 = classify_intent("Et si on réduisait la quantité ?")
    assert intent2 is IntentType.COMPARE  # "réduire" → COMPARE
    assert params2["quantite"] is None


# ---------------------------------------------------------------------------
# 2. API — 4 blocs Faits / Hypothèses / Interprétation / Incertitude
# ---------------------------------------------------------------------------


def test_explain_returns_four_blocks(client: TestClient):
    r = client.post(
        "/api/ai/explain",
        json={
            "situation_id": "dist-B001-P005",
            "question": "Et si on envoyait 20 unités ?",
            "mode": "qa",
        },
    )
    assert r.status_code == 200
    body = r.json()
    # 4 blocs INC-20
    assert body["faits"], "bloc Faits vide"
    assert body["hypotheses"], "bloc Hypothèses vide"
    assert body["interpretation"], "bloc Interprétation vide"
    assert body["incertitude"], "bloc Incertitude vide"
    assert body["intention"] == "COMPARE"
    # Scénario chiffré présent dans les faits (comparaison déterministe)
    assert any("Scénario 20 u" in f for f in body["faits"])
    assert any("protégé" in f for f in body["faits"])
    # Champs historiques toujours peuplés (rétro-compat)
    assert body["situation"]
    assert body["facteurs"]
    assert body["decision"]
    assert body["impact"]
    assert body["fallback"] is True


def test_explain_limits_blocks(client: TestClient):
    r = client.post(
        "/api/ai/explain",
        json={
            "situation_id": "dist-B001-P005",
            "question": "Quelle hypothèse est la plus fragile ?",
            "mode": "qa",
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["intention"] == "LIMITS"
    assert any("demande" in i.lower() for i in body["incertitude"])
    assert "fragile" in body["reponse"].lower() or "hypothèse" in body["reponse"].lower()


def test_explain_no_action_challenge(client: TestClient):
    r = client.post(
        "/api/ai/explain",
        json={
            "situation_id": "dist-B001-P005",
            "question": "Et si on n'agit pas ?",
            "mode": "qa",
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["intention"] == "CHALLENGE"
    assert "aucune action" in body["reponse"].lower()
    assert "486" in body["reponse"] or "486,000" in body["reponse"]


def test_explain_default_resume_has_blocks(client: TestClient):
    r = client.post(
        "/api/ai/explain",
        json={"situation_id": "dist-B001-P005", "mode": "resume"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["faits"]
    assert body["hypotheses"]
    assert body["interpretation"]
    assert body["incertitude"]
    assert body["intention"] == "EXPLAIN"
    assert body["fallback"] is True
