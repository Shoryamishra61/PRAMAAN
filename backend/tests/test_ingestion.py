from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, cast

from app.config import Settings
from app.database import connect_database
from app.main import create_app
from app.security import compute_webhook_signature
from fastapi.testclient import TestClient
from pydantic import SecretStr

FIXTURE_PATH = Path(__file__).parents[2] / "data" / "demo" / "pass" / "razorpay_event.json"
SECRET = "synthetic-test-webhook-secret"


def client_for(database_path: Path) -> TestClient:
    settings = Settings(database_path=database_path, webhook_secret=SecretStr(SECRET))
    return TestClient(create_app(settings))


def headers(raw_body: bytes, event_id: str | None = "evt_demo_001") -> dict[str, str]:
    result = {
        "Content-Type": "application/json",
        "X-Razorpay-Signature": compute_webhook_signature(raw_body, SECRET.encode("utf-8")),
    }
    if event_id is not None:
        result["x-razorpay-event-id"] = event_id
    return result


def test_authenticated_created_event_persists_event_case_and_job_atomically(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "dig.sqlite3"
    raw_body = FIXTURE_PATH.read_bytes()

    response = client_for(database_path).post(
        "/api/v1/webhooks/razorpay", content=raw_body, headers=headers(raw_body)
    )

    assert response.status_code == 202
    payload = response.json()
    assert payload["status"] == "accepted"
    assert payload["duplicate"] is False
    assert payload["processing_scheduled"] is True
    assert payload["case_id"] == "case_disp_demo_pass"
    with connect_database(database_path) as connection:
        event = connection.execute("SELECT * FROM ingest_events").fetchone()
        case = connection.execute("SELECT * FROM dispute_cases").fetchone()
        job = connection.execute("SELECT * FROM jobs").fetchone()

    assert event is not None and case is not None and job is not None
    assert event["body_sha256"] == hashlib.sha256(raw_body).hexdigest()
    assert case["raw_reason_code"] == "raw_demo_refund_pass"
    assert case["reason_profile"] == "refund_not_processed_v1"
    assert job["status"] == "PENDING"
    assert job["case_id"] == case["id"]


def test_duplicate_event_id_is_safe_and_creates_no_second_logical_job(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "dig.sqlite3"
    raw_body = FIXTURE_PATH.read_bytes()
    client = client_for(database_path)

    first = client.post("/api/v1/webhooks/razorpay", content=raw_body, headers=headers(raw_body))
    duplicate = client.post(
        "/api/v1/webhooks/razorpay", content=raw_body, headers=headers(raw_body)
    )

    assert first.status_code == duplicate.status_code == 202
    assert duplicate.json()["duplicate"] is True
    assert duplicate.json()["processing_scheduled"] is False
    with connect_database(database_path) as connection:
        assert connection.execute("SELECT count(*) FROM ingest_events").fetchone()[0] == 1
        assert connection.execute("SELECT count(*) FROM dispute_cases").fetchone()[0] == 1
        assert connection.execute("SELECT count(*) FROM jobs").fetchone()[0] == 1


def test_forward_compatible_extra_fields_are_tolerated(tmp_path: Path) -> None:
    database_path = tmp_path / "dig.sqlite3"
    raw = cast(dict[str, Any], json.loads(FIXTURE_PATH.read_text(encoding="utf-8")))
    raw["future_root_field"] = {"version": 2}
    raw["payload"]["dispute"]["entity"]["future_dispute_field"] = "preserved-safely"
    raw_body = json.dumps(raw, separators=(",", ":"), ensure_ascii=False).encode("utf-8")

    response = client_for(database_path).post(
        "/api/v1/webhooks/razorpay",
        content=raw_body,
        headers=headers(raw_body, "evt_future_fields"),
    )

    assert response.status_code == 202
    assert response.json()["processing_scheduled"] is True


def test_documented_non_mvp_event_is_persisted_without_business_job(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "dig.sqlite3"
    raw = cast(dict[str, Any], json.loads(FIXTURE_PATH.read_text(encoding="utf-8")))
    raw["event"] = "payment.dispute.action_required"
    raw_body = json.dumps(raw, separators=(",", ":")).encode("utf-8")

    response = client_for(database_path).post(
        "/api/v1/webhooks/razorpay",
        content=raw_body,
        headers=headers(raw_body, "evt_action_required"),
    )

    assert response.status_code == 202
    assert response.json()["case_id"] is None
    assert response.json()["processing_scheduled"] is False
    with connect_database(database_path) as connection:
        assert connection.execute("SELECT count(*) FROM ingest_events").fetchone()[0] == 1
        assert connection.execute("SELECT count(*) FROM dispute_cases").fetchone()[0] == 0
        assert connection.execute("SELECT count(*) FROM jobs").fetchone()[0] == 0


def test_signature_rejection_happens_before_payload_parsing(tmp_path: Path) -> None:
    raw_body = b"not-json"
    request_headers = headers(raw_body)
    request_headers["X-Razorpay-Signature"] = "0" * 64

    response = client_for(tmp_path / "dig.sqlite3").post(
        "/api/v1/webhooks/razorpay", content=raw_body, headers=request_headers
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INGEST_SIGNATURE_INVALID"


def test_missing_event_id_is_rejected_after_valid_authentication(tmp_path: Path) -> None:
    raw_body = FIXTURE_PATH.read_bytes()

    response = client_for(tmp_path / "dig.sqlite3").post(
        "/api/v1/webhooks/razorpay",
        content=raw_body,
        headers=headers(raw_body, event_id=None),
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INGEST_EVENT_ID_MISSING"


def test_oversized_webhook_is_rejected_before_authentication_or_persistence(
    tmp_path: Path,
) -> None:
    raw_body = b"{" + (b"x" * 1_000_000) + b"}"
    database_path = tmp_path / "dig.sqlite3"

    response = client_for(database_path).post(
        "/api/v1/webhooks/razorpay",
        content=raw_body,
        headers=headers(raw_body, "evt_oversized"),
    )

    assert response.status_code == 413
    assert response.json()["error"]["code"] == "INGEST_PAYLOAD_TOO_LARGE"
    assert not database_path.exists()
