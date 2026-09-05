"""Durable SQLite job claiming, leases, retry bounds, and worker execution."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from datetime import datetime, timedelta
from pathlib import Path
from time import perf_counter

from pydantic import BaseModel, ConfigDict

from app.database import connect_database
from app.domain import require_utc, to_storage_timestamp
from app.observability import StructuredLogEvent, emit_log


class RetryableJobError(RuntimeError):
    """A transient processing failure eligible for bounded retry."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


class PermanentJobError(RuntimeError):
    """A processing failure that retrying cannot repair."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


class ClaimedJob(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    case_id: str
    job_type: str
    attempt_count: int
    lease_until: datetime


JobHandler = Callable[[ClaimedJob], Awaitable[None]]


def claim_next_job(
    database_path: Path, now: datetime, lease_duration: timedelta
) -> ClaimedJob | None:
    """Claim one available or stale job under a short write transaction."""
    now_utc = require_utc(now)
    lease_until = now_utc + lease_duration
    now_text = to_storage_timestamp(now_utc)
    lease_text = to_storage_timestamp(lease_until)

    with connect_database(database_path) as connection:
        connection.execute("BEGIN IMMEDIATE")
        row = connection.execute(
            """
            SELECT id, case_id, job_type, attempt_count
            FROM jobs
            WHERE (
                status IN ('PENDING', 'RETRYABLE_ERROR') AND available_at <= ?
            ) OR (
                status = 'PROCESSING' AND lease_until IS NOT NULL AND lease_until <= ?
            )
            ORDER BY available_at, created_at, id
            LIMIT 1
            """,
            (now_text, now_text),
        ).fetchone()
        if row is None:
            connection.commit()
            return None

        attempt_count = int(row["attempt_count"]) + 1
        connection.execute(
            """
            UPDATE jobs
            SET status = 'PROCESSING', attempt_count = ?, lease_until = ?, updated_at = ?
            WHERE id = ?
            """,
            (attempt_count, lease_text, now_text, row["id"]),
        )
        connection.commit()
        return ClaimedJob(
            id=row["id"],
            case_id=row["case_id"],
            job_type=row["job_type"],
            attempt_count=attempt_count,
            lease_until=lease_until,
        )


def complete_job(database_path: Path, job: ClaimedJob, now: datetime) -> None:
    """Complete a job only while this worker still owns its exact lease."""
    with connect_database(database_path) as connection:
        cursor = connection.execute(
            """
            UPDATE jobs
            SET status = 'COMPLETED', lease_until = NULL, last_error_code = NULL, updated_at = ?
            WHERE id = ? AND status = 'PROCESSING' AND lease_until = ?
            """,
            (
                to_storage_timestamp(require_utc(now)),
                job.id,
                to_storage_timestamp(job.lease_until),
            ),
        )
        if cursor.rowcount != 1:
            raise PermanentJobError("JOB_STATE_CONFLICT")


def fail_job(
    database_path: Path,
    job: ClaimedJob,
    error_code: str,
    transient: bool,
    now: datetime,
    max_attempts: int,
    retry_delay: timedelta,
) -> None:
    """Schedule a bounded retry or terminate the durable job."""
    now_utc = require_utc(now)
    should_retry = transient and job.attempt_count < max_attempts
    status = "RETRYABLE_ERROR" if should_retry else "FAILED"
    available_at = now_utc + retry_delay if should_retry else now_utc
    with connect_database(database_path) as connection:
        cursor = connection.execute(
            """
            UPDATE jobs
            SET status = ?, available_at = ?, lease_until = NULL,
                last_error_code = ?, updated_at = ?
            WHERE id = ? AND status = 'PROCESSING' AND lease_until = ?
            """,
            (
                status,
                to_storage_timestamp(available_at),
                error_code,
                to_storage_timestamp(now_utc),
                job.id,
                to_storage_timestamp(job.lease_until),
            ),
        )
        if cursor.rowcount != 1:
            raise PermanentJobError("JOB_STATE_CONFLICT")


async def run_worker_once(
    database_path: Path,
    handler: JobHandler,
    now: datetime,
    *,
    lease_duration: timedelta = timedelta(seconds=30),
    retry_delay: timedelta = timedelta(seconds=1),
    max_attempts: int = 3,
) -> ClaimedJob | None:
    """Process at most one durable job; callers own polling cadence."""
    job = claim_next_job(database_path, now, lease_duration)
    if job is None:
        return None
    started = perf_counter()
    emit_log(
        StructuredLogEvent(
            module="worker",
            action="job.claimed",
            case_id=job.case_id,
            job_id=job.id,
            status="PROCESSING",
        )
    )
    try:
        await handler(job)
    except RetryableJobError as error:
        fail_job(
            database_path,
            job,
            error.code,
            True,
            now,
            max_attempts,
            retry_delay,
        )
        emit_log(
            StructuredLogEvent(
                module="worker",
                action="job.failure",
                case_id=job.case_id,
                job_id=job.id,
                status=("RETRYABLE_ERROR" if job.attempt_count < max_attempts else "FAILED"),
                latency_ms=int((perf_counter() - started) * 1000),
                failure_class=error.code,
            )
        )
    except PermanentJobError as error:
        fail_job(
            database_path,
            job,
            error.code,
            False,
            now,
            max_attempts,
            retry_delay,
        )
        emit_log(
            StructuredLogEvent(
                module="worker",
                action="job.failure",
                case_id=job.case_id,
                job_id=job.id,
                status="FAILED",
                latency_ms=int((perf_counter() - started) * 1000),
                failure_class=error.code,
            )
        )
    else:
        complete_job(database_path, job, now)
        emit_log(
            StructuredLogEvent(
                module="worker",
                action="job.completed",
                case_id=job.case_id,
                job_id=job.id,
                status="COMPLETED",
                latency_ms=int((perf_counter() - started) * 1000),
            )
        )
    return job
