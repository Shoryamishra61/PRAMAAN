from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from app.config import Settings
from app.database import connect_database, initialize_database, insert_dispute_case
from app.decision import GateDecision, GateStatus
from app.domain import DisputeCaseCreate, ProcessingStatus
from app.main import create_app
from fastapi.testclient import TestClient

NOW = datetime(2026, 8, 23, 12, tzinfo=timezone.utc)


def seed_case(database_path: Path, suffix: str, status: GateStatus, respond_by: str) -> None:
    case_id = f"case_{suffix}"
    payment_id = f"pay_{suffix}"
    initialize_database(database_path)
    with connect_database(database_path) as connection:
        insert_dispute_case(
            connection,
            DisputeCaseCreate(
                id=case_id,
                razorpay_dispute_id=f"disp_{suffix}",
                payment_id=payment_id,
                amount_minor=250_000,
                currency="INR",
                raw_reason_code=f"raw_reason_{suffix}",
                respond_by=datetime.fromisoformat(respond_by.replace("Z", "+00:00")),
                processing_status=ProcessingStatus.READY,
                created_at=NOW,
                updated_at=NOW,
            ),
        )
        decision = GateDecision(
            case_id=case_id,
            status=status,
            findings=(),
            review_reasons=("F_TEST_REVIEW",) if status is GateStatus.REVIEW else (),
            evaluated_at=NOW,
        )
        connection.execute(
            "INSERT INTO gate_decisions "
            "(id, case_id, status, primary_reason_code, engine_version, decision_json, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                f"decision_{suffix}",
                case_id,
                status.value,
                "F_TEST_REVIEW" if status is GateStatus.REVIEW else None,
                decision.engine_version,
                decision.model_dump_json(),
                NOW.isoformat().replace("+00:00", "Z"),
            ),
        )


def client_with_queue(tmp_path: Path) -> tuple[TestClient, Path]:
    database_path = tmp_path / "queue.sqlite3"
    seed_case(database_path, "pass", GateStatus.PASS, "2026-09-03T12:00:00Z")
    seed_case(database_path, "block", GateStatus.BLOCK, "2026-09-02T12:00:00Z")
    seed_case(database_path, "review", GateStatus.REVIEW, "2026-09-01T12:00:00Z")
    return TestClient(create_app(Settings(database_path=database_path))), database_path


def test_queue_filter_treats_sql_injection_text_as_a_parameter(tmp_path: Path) -> None:
    client, database_path = client_with_queue(tmp_path)
    attempted_injection = "refund_not_processed_v1' OR 1=1; DROP TABLE dispute_cases;--"

    response = client.get("/api/v1/cases", params={"reason_profile": attempted_injection})

    assert response.status_code == 200
    assert response.json()["items"] == []
    with connect_database(database_path) as connection:
        assert connection.execute("SELECT count(*) FROM dispute_cases").fetchone()[0] == 3


def test_queue_contract_sort_filters_and_paginates(tmp_path: Path) -> None:
    client, _ = client_with_queue(tmp_path)

    response = client.get("/api/v1/cases")
    assert response.status_code == 200
    assert [item["case_id"] for item in response.json()["items"]] == [
        "case_review",
        "case_block",
        "case_pass",
    ]
    assert response.json()["items"][0]["raw_reason_code"] == "raw_reason_review"

    filtered = client.get("/api/v1/cases", params={"gate_status": "BLOCK"})
    assert [item["case_id"] for item in filtered.json()["items"]] == ["case_block"]

    first_page = client.get("/api/v1/cases", params={"limit": 1}).json()
    second_page = client.get(
        "/api/v1/cases", params={"limit": 1, "cursor": first_page["next_cursor"]}
    ).json()
    assert first_page["items"][0]["case_id"] == "case_review"
    assert second_page["items"][0]["case_id"] == "case_block"


def test_queue_rejects_invalid_filters_and_cursor(tmp_path: Path) -> None:
    client, _ = client_with_queue(tmp_path)

    assert client.get("/api/v1/cases", params={"gate_status": "UNKNOWN"}).status_code == 422
    response = client.get("/api/v1/cases", params={"cursor": "missing"})
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "QUEUE_CURSOR_INVALID"


def test_case_workspace_returns_normalized_sources_and_no_provider_response(
    tmp_path: Path,
) -> None:
    client, database_path = client_with_queue(tmp_path)
    text = "Your INR 2,500 refund was processed."
    with connect_database(database_path) as connection:
        connection.execute(
            "INSERT INTO payment_snapshots "
            "(case_id, payment_id, captured_amount_minor, currency, captured_at, "
            "snapshot_complete) VALUES (?, ?, ?, ?, ?, ?)",
            ("case_block", "pay_block", 250_000, "INR", "2026-08-20T10:00:00Z", 1),
        )
        connection.execute(
            "INSERT INTO refund_records "
            "(id, case_id, payment_id, amount_minor, currency, local_status, reference) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("rfnd_block", "case_block", "pay_block", 100_000, "INR", "processed", "RF-1"),
        )
        connection.execute(
            "INSERT INTO evidence_documents "
            "(id, case_id, source_type, source_system, media_type, canonical_text, "
            "content_sha256, ingested_at, is_complete_source) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "doc_block",
                "case_block",
                "customer_communication",
                "synthetic_fixture",
                "text/plain",
                text,
                hashlib.sha256(text.encode()).hexdigest(),
                "2026-08-23T12:00:00Z",
                1,
            ),
        )
        connection.execute(
            "INSERT INTO extraction_runs "
            "(id, document_id, extractor_id, prompt_version, schema_version, request_hash, "
            "status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "run_block",
                "doc_block",
                "regex-baseline-v1",
                "not-applicable-regex-v1",
                "1.0",
                "request_hash",
                "COMPLETED",
                "2026-08-23T12:00:00Z",
            ),
        )
        connection.execute(
            "INSERT INTO grounded_claims "
            "(id, extraction_run_id, document_id, claim_type, raw_value, amount_minor, "
            "currency, source_quote, span_start, span_end, grounding_status, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "claim_block",
                "run_block",
                "doc_block",
                "refund_claimed_processed",
                "INR 2,500",
                250_000,
                "INR",
                text,
                0,
                len(text),
                "GROUNDED",
                "2026-08-23T12:00:00Z",
            ),
        )
        connection.execute(
            "INSERT INTO findings "
            "(id, case_id, rule_code, severity, decision_effect, explanation, "
            "structured_refs_json, claim_refs_json, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "finding_block",
                "case_block",
                "F_REFUND_AMOUNT_MISMATCH",
                "material",
                "BLOCK",
                "The grounded processed amount differs from the processed ledger total.",
                json.dumps(["rfnd_block"]),
                json.dumps(["claim_block"]),
                "2026-08-23T12:00:00Z",
            ),
        )
        connection.execute(
            "INSERT INTO review_events "
            "(id, case_id, operator_id, event_type, details_json, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                "audit_block",
                "case_block",
                "demo_operator",
                "SOURCE_INSPECTED",
                json.dumps({"document_id": "doc_block"}),
                "2026-08-23T12:05:00Z",
            ),
        )

    response = client.get("/api/v1/cases/case_block")
    assert response.status_code == 200
    payload = response.json()
    assert payload["case"]["dispute_id"] == "disp_block"
    assert payload["payment_snapshot"]["captured_amount_minor"] == 250_000
    assert payload["refunds"][0]["reference"] == "RF-1"
    assert payload["evidence_documents"][0]["canonical_text"] == text
    assert payload["grounded_claims"][0]["span_end"] == len(text)
    assert payload["findings"][0]["claim_refs"] == ["claim_block"]
    assert payload["gate_decision"]["status"] == "BLOCK"
    assert payload["audit_events"][0]["operator_id"] == "demo_operator"
    assert "provider" not in response.text.lower()
    assert "secret" not in response.text.lower()

    premature = client.post(
        "/api/v1/cases/case_block/override",
        json={"reason": "SOURCE_DATA_ERROR", "note": None},
    )
    assert premature.status_code == 409
    assert premature.json()["error"]["code"] == "OVERRIDE_INSPECTION_REQUIRED"

    claim_inspection = client.post(
        "/api/v1/cases/case_block/inspect",
        json={"source_ref": "claim_block", "document_id": "doc_block"},
    )
    refund_inspection = client.post(
        "/api/v1/cases/case_block/inspect",
        json={"source_ref": "rfnd_block", "document_id": "structured_refund_ledger"},
    )
    assert claim_inspection.json()["network_write_performed"] is False
    assert refund_inspection.json()["network_write_performed"] is False

    overridden = client.post(
        "/api/v1/cases/case_block/override",
        json={"reason": "SOURCE_DATA_ERROR", "note": "Fixture ledger repaired externally."},
    )
    assert overridden.status_code == 200
    assert overridden.json() == {
        "case_id": "case_block",
        "workflow_status": "READY_WITH_OVERRIDE",
        "gate_status": "BLOCK",
        "network_write_performed": False,
    }
    ready = client.post("/api/v1/cases/case_block/mark-ready")
    assert ready.json()["workflow_status"] == "READY_FOR_CONTEST"
    assert ready.json()["network_write_performed"] is False

    with connect_database(database_path) as connection:
        assert (
            connection.execute(
                "SELECT status FROM gate_decisions WHERE case_id = ?", ("case_block",)
            ).fetchone()["status"]
            == "BLOCK"
        )
        assert (
            connection.execute(
                "SELECT workflow_status FROM dispute_cases WHERE id = ?", ("case_block",)
            ).fetchone()["workflow_status"]
            == "READY_FOR_CONTEST"
        )
        event_types = [
            row["event_type"]
            for row in connection.execute(
                "SELECT event_type FROM review_events WHERE case_id = ? ORDER BY created_at, id",
                ("case_block",),
            ).fetchall()
        ]
    assert event_types.count("SOURCE_INSPECTED") == 3
    assert "LOCAL_HOLD_OVERRIDDEN" in event_types
    assert "MARKED_READY" in event_types


def test_case_workspace_returns_not_found_envelope(tmp_path: Path) -> None:
    client, _ = client_with_queue(tmp_path)
    response = client.get("/api/v1/cases/missing")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "CASE_NOT_FOUND"


def test_reprocess_after_repair_queues_durable_local_job_and_audit(tmp_path: Path) -> None:
    client, database_path = client_with_queue(tmp_path)

    response = client.post(
        "/api/v1/cases/case_review/reprocess",
        headers={"Idempotency-Key": "repair-cycle-1"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "queued"
    assert response.json()["network_write_performed"] is False
    with connect_database(database_path) as connection:
        job = connection.execute(
            "SELECT case_id, status, job_type FROM jobs WHERE id = ?",
            (response.json()["job_id"],),
        ).fetchone()
        event = connection.execute(
            "SELECT operator_id, event_type, reason_code FROM review_events "
            "WHERE case_id = ? AND event_type = 'REPAIR_REQUESTED'",
            ("case_review",),
        ).fetchone()
        case = connection.execute(
            "SELECT processing_status, workflow_status FROM dispute_cases WHERE id = ?",
            ("case_review",),
        ).fetchone()
    assert dict(job) == {
        "case_id": "case_review",
        "status": "PENDING",
        "job_type": "PROCESS_CASE",
    }
    assert dict(event) == {
        "operator_id": "demo_operator",
        "event_type": "REPAIR_REQUESTED",
        "reason_code": "REPROCESS_AFTER_REPAIR",
    }
    assert dict(case) == {
        "processing_status": "QUEUED",
        "workflow_status": "REVIEW_PENDING",
    }


def test_reprocess_idempotency_key_creates_one_logical_job(tmp_path: Path) -> None:
    client, database_path = client_with_queue(tmp_path)
    headers = {"Idempotency-Key": "same-repair"}

    first = client.post("/api/v1/cases/case_review/reprocess", headers=headers)
    second = client.post("/api/v1/cases/case_review/reprocess", headers=headers)

    assert first.json()["job_id"] == second.json()["job_id"]
    with connect_database(database_path) as connection:
        assert (
            connection.execute(
                "SELECT count(*) FROM jobs WHERE case_id = ?", ("case_review",)
            ).fetchone()[0]
            == 1
        )
        assert (
            connection.execute(
                "SELECT count(*) FROM review_events WHERE case_id = ?", ("case_review",)
            ).fetchone()[0]
            == 1
        )


def test_reprocess_missing_case_and_blank_key_are_rejected(tmp_path: Path) -> None:
    client, _ = client_with_queue(tmp_path)

    missing = client.post("/api/v1/cases/missing/reprocess")
    blank = client.post("/api/v1/cases/case_review/reprocess", headers={"Idempotency-Key": " "})

    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "CASE_NOT_FOUND"
    assert blank.status_code == 400
    assert blank.json()["error"]["code"] == "REPROCESS_REQUEST_INVALID"


def test_mark_ready_allows_pass_but_rejects_review_and_other_without_note(
    tmp_path: Path,
) -> None:
    client, _ = client_with_queue(tmp_path)

    passed = client.post("/api/v1/cases/case_pass/mark-ready")
    reviewed = client.post("/api/v1/cases/case_review/mark-ready")
    invalid_other = client.post(
        "/api/v1/cases/case_block/override", json={"reason": "OTHER", "note": " "}
    )

    assert passed.status_code == 200
    assert passed.json()["workflow_status"] == "READY_FOR_CONTEST"
    assert passed.json()["network_write_performed"] is False
    assert reviewed.status_code == 409
    assert reviewed.json()["error"]["code"] == "MARK_READY_PRECONDITION_FAILED"
    assert invalid_other.status_code == 422
