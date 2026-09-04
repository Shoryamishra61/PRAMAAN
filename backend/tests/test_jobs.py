from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from app.database import connect_database, initialize_database, insert_dispute_case
from app.domain import DisputeCaseCreate
from app.jobs import (
    ClaimedJob,
    PermanentJobError,
    RetryableJobError,
    claim_next_job,
    run_worker_once,
)

NOW = datetime(2026, 8, 23, 10, tzinfo=timezone.utc)


def seed_job(database_path: Path) -> None:
    initialize_database(database_path)
    case = DisputeCaseCreate(
        id="case_jobs",
        razorpay_dispute_id="disp_jobs",
        payment_id="pay_jobs",
        amount_minor=100,
        currency="INR",
        created_at=NOW,
        updated_at=NOW,
    )
    timestamp = "2026-08-23T10:00:00Z"
    with connect_database(database_path) as connection:
        insert_dispute_case(connection, case)
        connection.execute(
            """
            INSERT INTO jobs (
                id, case_id, job_type, status, available_at, created_at, updated_at
            ) VALUES (?, ?, ?, 'PENDING', ?, ?, ?)
            """,
            ("job_1", case.id, "PROCESS_CASE", timestamp, timestamp, timestamp),
        )


def job_row(database_path: Path) -> dict[str, object]:
    with connect_database(database_path) as connection:
        row = connection.execute("SELECT * FROM jobs WHERE id = ?", ("job_1",)).fetchone()
    assert row is not None
    return dict(row)


def test_live_lease_prevents_second_claim(tmp_path: Path) -> None:
    database_path = tmp_path / "dig.sqlite3"
    seed_job(database_path)

    first = claim_next_job(database_path, NOW, timedelta(seconds=30))
    second = claim_next_job(database_path, NOW + timedelta(seconds=1), timedelta(seconds=30))

    assert first is not None
    assert first.attempt_count == 1
    assert second is None


def test_stale_processing_job_is_reclaimed_after_worker_restart(tmp_path: Path) -> None:
    database_path = tmp_path / "dig.sqlite3"
    seed_job(database_path)
    crashed_claim = claim_next_job(database_path, NOW, timedelta(seconds=5))

    restarted_claim = claim_next_job(
        database_path, NOW + timedelta(seconds=6), timedelta(seconds=5)
    )

    assert crashed_claim is not None and restarted_claim is not None
    assert restarted_claim.id == crashed_claim.id
    assert restarted_claim.attempt_count == 2


@pytest.mark.asyncio
async def test_successful_worker_completes_job_once(tmp_path: Path) -> None:
    database_path = tmp_path / "dig.sqlite3"
    seed_job(database_path)
    handled: list[str] = []

    async def handler(job: ClaimedJob) -> None:
        handled.append(job.id)

    first = await run_worker_once(database_path, handler, NOW)
    second = await run_worker_once(database_path, handler, NOW + timedelta(seconds=1))

    assert first is not None
    assert second is None
    assert handled == ["job_1"]
    assert job_row(database_path)["status"] == "COMPLETED"


@pytest.mark.asyncio
async def test_transient_failure_retries_only_to_bound(tmp_path: Path) -> None:
    database_path = tmp_path / "dig.sqlite3"
    seed_job(database_path)

    async def transient_failure(_: ClaimedJob) -> None:
        raise RetryableJobError("JOB_TRANSIENT_PROVIDER_ERROR")

    for attempt in range(3):
        await run_worker_once(
            database_path,
            transient_failure,
            NOW + timedelta(seconds=attempt),
            retry_delay=timedelta(seconds=1),
            max_attempts=3,
        )

    row = job_row(database_path)
    assert row["attempt_count"] == 3
    assert row["status"] == "FAILED"
    assert row["last_error_code"] == "JOB_TRANSIENT_PROVIDER_ERROR"


@pytest.mark.asyncio
async def test_permanent_failure_is_not_retried(tmp_path: Path) -> None:
    database_path = tmp_path / "dig.sqlite3"
    seed_job(database_path)

    async def permanent_failure(_: ClaimedJob) -> None:
        raise PermanentJobError("SYSTEM_INTERNAL_ERROR")

    await run_worker_once(database_path, permanent_failure, NOW)
    second = await run_worker_once(database_path, permanent_failure, NOW + timedelta(seconds=1))

    assert second is None
    row = job_row(database_path)
    assert row["attempt_count"] == 1
    assert row["status"] == "FAILED"


@pytest.mark.asyncio
async def test_worker_failure_log_contains_ids_and_safe_failure_code(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    database_path = tmp_path / "dig.sqlite3"
    seed_job(database_path)

    async def permanent_failure(_: ClaimedJob) -> None:
        raise PermanentJobError("JOB_PERMANENT_SCHEMA_ERROR")

    caplog.set_level(logging.INFO, logger="dispute_integrity_gate")
    await run_worker_once(database_path, permanent_failure, NOW)

    payloads = [json.loads(record.message) for record in caplog.records]
    assert payloads[-1] == {
        "action": "job.failure",
        "case_id": "case_jobs",
        "failure_class": "JOB_PERMANENT_SCHEMA_ERROR",
        "job_id": "job_1",
        "latency_ms": payloads[-1]["latency_ms"],
        "module": "worker",
        "status": "FAILED",
    }
    assert isinstance(payloads[-1]["latency_ms"], int)
