from __future__ import annotations

import statistics
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from app.config import Settings
from app.database import connect_database
from app.jobs import ClaimedJob, claim_next_job, run_worker_once
from app.main import create_app
from app.security import compute_webhook_signature
from fastapi.testclient import TestClient
from pydantic import SecretStr

FIXTURE_PATH = Path(__file__).parents[2] / "data" / "demo" / "pass" / "razorpay_event.json"
SECRET = "synthetic-test-webhook-secret"
NOW = datetime(2026, 8, 23, 10, tzinfo=timezone.utc)


def replay(
    client: TestClient,
    raw_body: bytes,
    event_id: str,
    signature: str | None = None,
) -> tuple[int, float]:
    started = time.perf_counter()
    response = client.post(
        "/api/v1/webhooks/razorpay",
        content=raw_body,
        headers={
            "Content-Type": "application/json",
            "X-Razorpay-Signature": signature
            or compute_webhook_signature(raw_body, SECRET.encode("utf-8")),
            "x-razorpay-event-id": event_id,
        },
    )
    return response.status_code, time.perf_counter() - started


def test_replay_ack_is_durable_and_measured_under_five_seconds(tmp_path: Path) -> None:
    database_path = tmp_path / "dig.sqlite3"
    client = TestClient(
        create_app(Settings(database_path=database_path, webhook_secret=SecretStr(SECRET)))
    )
    raw_body = FIXTURE_PATH.read_bytes()
    durations: list[float] = []

    for index in range(10):
        status, duration = replay(client, raw_body, f"evt_latency_{index}")
        assert status == 202
        durations.append(duration)

    p95_seconds = statistics.quantiles(durations, n=100, method="inclusive")[94]
    assert p95_seconds < 5.0
    with connect_database(database_path) as connection:
        assert connection.execute("SELECT count(*) FROM ingest_events").fetchone()[0] == 10
        assert connection.execute("SELECT count(*) FROM dispute_cases").fetchone()[0] == 1
        assert connection.execute("SELECT count(*) FROM jobs").fetchone()[0] == 1


def test_mutated_replay_with_original_signature_is_rejected_before_persistence(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "dig.sqlite3"
    client = TestClient(
        create_app(Settings(database_path=database_path, webhook_secret=SecretStr(SECRET)))
    )
    original = FIXTURE_PATH.read_bytes()
    mutated = original.replace(b"250000", b"250001", 1)
    original_signature = compute_webhook_signature(original, SECRET.encode("utf-8"))

    status, _ = replay(client, mutated, "evt_mutated", original_signature)

    assert status == 401
    assert not database_path.exists()


@pytest.mark.asyncio
async def test_persisted_job_is_recovered_after_simulated_process_restart(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "dig.sqlite3"
    client = TestClient(
        create_app(Settings(database_path=database_path, webhook_secret=SecretStr(SECRET)))
    )
    raw_body = FIXTURE_PATH.read_bytes()
    status, _ = replay(client, raw_body, "evt_restart")
    assert status == 202

    claim_time = datetime.now(timezone.utc) + timedelta(seconds=1)
    crashed_claim = claim_next_job(database_path, claim_time, timedelta(seconds=1))
    assert crashed_claim is not None
    handled: list[str] = []

    async def restarted_handler(job: ClaimedJob) -> None:
        handled.append(job.id)

    restarted_claim = await run_worker_once(
        database_path,
        restarted_handler,
        claim_time + timedelta(seconds=2),
        lease_duration=timedelta(seconds=1),
    )

    assert restarted_claim is not None
    assert restarted_claim.id == crashed_claim.id
    assert restarted_claim.attempt_count == 2
    assert handled == [crashed_claim.id]
    with connect_database(database_path) as connection:
        row = connection.execute("SELECT status FROM jobs").fetchone()
    assert row is not None and row["status"] == "COMPLETED"
