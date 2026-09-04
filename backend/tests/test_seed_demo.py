from __future__ import annotations

from pathlib import Path

import pytest
from app.case_api import get_case, list_cases
from app.config import Settings
from app.database import connect_database
from app.main import create_app
from fastapi.testclient import TestClient

from scripts.seed_demo import seed_demo

REPO_ROOT = Path(__file__).parents[2]


def test_seeded_demo_runs_signed_webhook_to_pass_review_block_workspace(tmp_path: Path) -> None:
    database_path = tmp_path / "demo.sqlite3"

    summary = seed_demo(REPO_ROOT, database_path)

    assert summary.synthetic is True
    assert summary.mode == "offline_replay_precomputed_regex"
    assert [case.signed_webhook_status for case in summary.cases] == [202, 202, 202]
    assert {case.gate_status for case in summary.cases} == {"PASS", "REVIEW", "BLOCK"}
    queue = list_cases(database_path)
    assert {item.gate_status.value for item in queue.items if item.gate_status} == {
        "PASS",
        "REVIEW",
        "BLOCK",
    }
    assert {item.raw_reason_code for item in queue.items} == {
        "raw_demo_refund_pass",
        "raw_demo_refund_review",
        "raw_demo_refund_block",
    }
    with connect_database(database_path) as connection:
        assert connection.execute("SELECT count(*) FROM ingest_events").fetchone()[0] == 3
        assert (
            connection.execute("SELECT count(*) FROM jobs WHERE status = 'COMPLETED'").fetchone()[0]
            == 3
        )

    for seeded in summary.cases:
        detail = get_case(database_path, seeded.case_id)
        assert detail is not None
        assert detail.case.gate_status is not None
        assert detail.case.gate_status.value == seeded.gate_status
        assert detail.payment_snapshot is not None
        assert detail.evidence_documents[0].source_system == "synthetic_fixture"
        for claim in detail.grounded_claims:
            assert claim.span_start is not None and claim.span_end is not None
            text = detail.evidence_documents[0].canonical_text
            assert text[claim.span_start : claim.span_end] == claim.source_quote


def test_seeded_block_case_supports_complete_local_override_path(tmp_path: Path) -> None:
    database_path = tmp_path / "demo.sqlite3"
    summary = seed_demo(REPO_ROOT, database_path)
    block = next(case for case in summary.cases if case.gate_status == "BLOCK")
    client = TestClient(create_app(Settings(database_path=database_path)))
    detail = client.get(f"/api/v1/cases/{block.case_id}").json()
    finding = next(item for item in detail["findings"] if item["decision_effect"] == "BLOCK")

    for source_ref in finding["claim_refs"] + finding["structured_refs"]:
        claim = next((item for item in detail["grounded_claims"] if item["id"] == source_ref), None)
        document_id = claim["document_id"] if claim else "structured_refund_ledger"
        response = client.post(
            f"/api/v1/cases/{block.case_id}/inspect",
            json={"source_ref": source_ref, "document_id": document_id},
        )
        assert response.status_code == 200
        assert response.json()["network_write_performed"] is False

    override = client.post(
        f"/api/v1/cases/{block.case_id}/override",
        json={"reason": "SOURCE_DATA_ERROR", "note": "Synthetic demo override."},
    )
    ready = client.post(f"/api/v1/cases/{block.case_id}/mark-ready")

    assert override.status_code == ready.status_code == 200
    assert override.json()["gate_status"] == "BLOCK"
    assert ready.json()["workflow_status"] == "READY_FOR_CONTEST"
    assert ready.json()["network_write_performed"] is False


def test_seed_refuses_to_overwrite_an_existing_database(tmp_path: Path) -> None:
    database_path = tmp_path / "demo.sqlite3"
    seed_demo(REPO_ROOT, database_path)

    with pytest.raises(FileExistsError, match="Refusing to overwrite"):
        seed_demo(REPO_ROOT, database_path)
