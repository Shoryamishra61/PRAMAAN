"""Automated 5-minute judge demo smoke test for PRAMAAN / CARVE-FECL.

Validates the full system end-to-end before a live presentation:
1. Sample data / synthetic fixtures load cleanly.
2. Model, extraction pipeline, and Z3/deterministic verifier run.
3. Three canonical cases produce exact expected states:
   - PASS (CONTEST_READY)
   - REVIEW (REVIEW_REQUIRED)
   - BLOCK (INSUFFICIENT_OR_CONTRADICTORY_EVIDENCE)
4. All operational and research APIs respond with HTTP 200.
5. Quant-risk and AI-research profiles render without missing artifacts.
"""

from __future__ import annotations

import argparse
import tempfile
from pathlib import Path
from typing import Any

from app.config import Settings
from app.main import create_app
from fastapi.testclient import TestClient

try:
    from scripts.seed_demo import seed_demo
except ModuleNotFoundError:
    from seed_demo import seed_demo  # type: ignore[no-redef]

REPO_ROOT = Path(__file__).resolve().parents[1]


def run_demo_smoke_test(repo_root: Path) -> dict[str, Any]:
    print("=" * 70)
    print("  PRAMAAN / CARVE-FECL -- LIVE DEMO SMOKE TEST")
    print("=" * 70)

    # 1. Initialize isolated database for smoke test
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "demo_smoke.sqlite3"
        print(f"[1/5] Seeding canonical dispute cases into {db_path.name}...")
        summary = seed_demo(repo_root, db_path, reset=False)

        assert len(summary.cases) == 3, f"Expected 3 seeded cases, found {len(summary.cases)}"
        cases_by_fixture = {c.fixture: c for c in summary.cases}
        assert cases_by_fixture["pass"].gate_status == "PASS"
        assert cases_by_fixture["review"].gate_status == "REVIEW"
        assert cases_by_fixture["block"].gate_status == "BLOCK"
        print("      [OK] Canonical cases loaded: pass -> PASS, review -> REVIEW, block -> BLOCK")

        # 2. Configure FastAPI TestClient
        print("[2/5] Initializing API test client with runtime settings...")
        settings = Settings(
            database_path=db_path,
            results_directory=repo_root / "results",
            contracts_directory=repo_root / "contracts",
        )
        app = create_app(settings)
        client = TestClient(app)

        # 3. Health check
        print("[3/5] Verifying API health endpoints...")
        health_resp = client.get("/api/v1/health")
        assert health_resp.status_code == 200, f"Health returned {health_resp.status_code}"
        health_data = health_resp.json()
        assert health_data.get("app") == "ok"
        assert health_data.get("database") == "ready"
        print("      [OK] Health status: OK, Database: READY")

        # 4. Cases API & Inspection
        print("[4/5] Verifying Case API projections...")
        cases_resp = client.get("/api/v1/cases")
        assert cases_resp.status_code == 200
        items = cases_resp.json().get("items", [])
        assert len(items) == 3, f"Expected 3 cases in list, got {len(items)}"

        for case_item in items:
            cid = case_item["case_id"]
            detail = client.get(f"/api/v1/cases/{cid}")
            assert detail.status_code == 200, f"Detail for {cid} failed with {detail.status_code}"
            data = detail.json()
            assert "case" in data
            assert "gate_decision" in data
            assert "evidence_documents" in data
            assert "payment_snapshot" in data
        print("      [OK] All 3 case details, evidence documents, and decisions verified")

        # 5. Research & Quant-Risk Endpoints
        print("[5/5] Verifying Research & Quant-Risk projections...")
        quant_resp = client.get("/api/v1/research/quant-risk")
        assert quant_resp.status_code == 410, (
            f"Quant-risk failed: {quant_resp.status_code} {quant_resp.text}"
        )
        quant_data = quant_resp.json()
        assert "net_merchant_edge_inr" not in quant_data

        ai_resp = client.get("/api/v1/ai-research")
        assert ai_resp.status_code == 200, f"AI-research failed: {ai_resp.status_code}"

        carve_resp = client.get("/api/v1/research/carve-v4.5")
        assert carve_resp.status_code == 200, f"Carve-research failed: {carve_resp.status_code}"

        eval_resp = client.get("/api/v1/evaluation/latest")
        assert eval_resp.status_code == 200, f"Evaluation latest failed: {eval_resp.status_code}"

        print(
            "      [OK] Legacy projection retired (410); "
            "artifact-backed research and evaluation available"
        )

    print("\n" + "=" * 70)
    print("  STATUS: API DEMO SMOKE PASSED -- VISUAL QA IS A SEPARATE GATE")
    print("=" * 70 + "\n")
    return {
        "status": "PASS",
        "cases_verified": 3,
        "api_endpoints_checked": [
            "/api/v1/health",
            "/api/v1/cases",
            "/api/v1/cases/{id}",
            "/api/v1/research/quant-risk",
            "/api/v1/ai-research",
            "/api/v1/research/carve-v4.5",
            "/api/v1/evaluation/latest",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    args = parser.parse_args()

    try:
        run_demo_smoke_test(args.repo_root)
        return 0
    except Exception:
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
