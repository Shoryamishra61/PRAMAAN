from __future__ import annotations

from app.carve_research_api import load_carve_research
from app.main import app
from fastapi.testclient import TestClient


def test_carve_research_is_bound_to_one_shot_receipt() -> None:
    result = load_carve_research()
    assert result.generated is True
    assert result.benchmark_id == "DIG-FECL-BENCH-v4.5"
    assert result.split_counts == {
        "train": 1200,
        "dev": 320,
        "calibration": 320,
        "test": 480,
        "ood": 160,
    }
    assert result.test["one_shot_test"] is True
    assert result.test["models"]["formal_proof"]["mcc_exact"] == 1.0
    assert result.evidence_case["certificate"]["solver_expected"] == "UNSAT"


def test_carve_research_endpoint() -> None:
    response = TestClient(app).get("/api/v1/research/carve-v4.5")
    assert response.status_code == 200
    assert response.json()["test"]["synthetic_only"] is True


def test_quant_risk_endpoint() -> None:
    response = TestClient(app).get("/api/v1/research/quant-risk")
    assert response.status_code == 200
    data = response.json()
    assert data["benchmark_id"] == "DIG-RNP-SYN-V1"
    assert data["circuit_breaker_state"] == "AUTOMATION_ENABLED"
    assert len(data["baseline_ladder"]) >= 7
    assert data["merchant_economics"]["net_merchant_edge_inr"] == 3434000.0
    b10_tail = next(m for m in data["tail_risk"]["models"] if m["model_id"] == "B10")
    assert b10_tail["cvar_99"] == 3.75
