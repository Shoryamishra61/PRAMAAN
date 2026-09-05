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


def test_retired_quant_risk_endpoint_cannot_serve_fabricated_metrics() -> None:
    response = TestClient(app).get("/api/v1/research/quant-risk")
    assert response.status_code == 410
    assert "RESEARCH_PROJECTION_RETIRED" in response.text
    assert "net_merchant_edge_inr" not in response.text
    assert "daily_risk_budget_consumed_pct" not in response.text
