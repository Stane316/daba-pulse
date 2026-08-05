"""Tests API — export décisionnel + import CSV (EL-01 / EL-02)."""

from __future__ import annotations

import io
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.engines.data_loader import store  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(scope="module")
def client() -> TestClient:
    data_path = ROOT / "data" / "sample"
    store.load(data_path)
    return TestClient(app)


def test_health(client: TestClient):
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["data_loaded"] is True


def test_export_decision_json(client: TestClient):
    r = client.get("/api/export/decision/dist-B001-P005?format=json")
    assert r.status_code == 200
    assert "attachment" in r.headers.get("content-disposition", "")
    data = r.json()
    assert data["donnees_synthetiques"] is True
    assert data["situation"]["id"] == "dist-B001-P005"
    assert data["situation"]["revenue_at_risk"] == 486000.0
    assert data["decision"] is not None
    assert data["simulation"] is not None
    assert data["synthese"]["revenu_potentiellement_protege"] >= 0
    assert "disclaimer" in data


def test_export_decision_markdown(client: TestClient):
    r = client.get("/api/export/decision/dist-B001-P005?format=markdown")
    assert r.status_code == 200
    text = r.text
    assert "DabaPulse" in text
    assert "synthétiques" in text.lower() or "Données" in text


def test_export_post_with_quantite(client: TestClient):
    r = client.post(
        "/api/export/decision",
        json={
            "situation_id": "dist-B001-P005",
            "quantite": 30,
            "format": "json",
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["simulation"]["quantite_simulee"] == 30
    assert data["simulation"]["revenue_at_risk_apres"] == 0
    assert data["simulation"]["revenu_potentiellement_protege"] == 486000.0


def test_export_unknown_situation(client: TestClient):
    r = client.get("/api/export/decision/does-not-exist")
    assert r.status_code == 404


def test_data_preview(client: TestClient):
    r = client.get("/api/data/preview?n=3")
    assert r.status_code == 200
    body = r.json()
    assert body["nb_lignes"] > 0
    assert len(body["sample_rows"]) <= 3
    assert "date" in body["columns"]


def test_upload_csv_valid(client: TestClient):
    sample = (ROOT / "data" / "sample" / "ventes_stocks.csv").read_text(encoding="utf-8")
    lines = sample.strip().splitlines()
    mini = "\n".join(lines[:20]) + "\n"
    files = {"file": ("test_upload.csv", io.BytesIO(mini.encode("utf-8")), "text/csv")}
    r = client.post("/api/data/upload", files=files)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"]["valide"] is True
    assert body["status"]["nb_lignes"] >= 1
    assert "upload:test_upload.csv" in body["status"]["source"]

    r2 = client.get("/api/executive")
    assert r2.status_code == 200
    assert r2.json()["nb_situations_total"] >= 1

    store.load(ROOT / "data" / "sample")


def test_upload_csv_missing_columns(client: TestClient):
    bad = "date,boutique_id,stock\n2026-08-01,B001,5\n"
    files = {"file": ("bad.csv", io.BytesIO(bad.encode("utf-8")), "text/csv")}
    r = client.post("/api/data/upload", files=files)
    assert r.status_code == 400
    detail = r.json()["detail"]
    assert "missing_columns" in detail or "message" in detail


def test_upload_rejects_non_csv(client: TestClient):
    files = {"file": ("note.txt", io.BytesIO(b"hello"), "text/plain")}
    r = client.post("/api/data/upload", files=files)
    assert r.status_code == 400