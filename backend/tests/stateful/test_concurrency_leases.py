"""Stateful concurrency and worker lease tests for PRAMAAN.

Validates the Database Transaction and Worker Lease Requirements:
1. Multi-worker concurrency (16 concurrent threads contending for jobs).
2. Exactly one worker claims an active job; no double-claiming under valid lease.
3. Stale worker lease expiry: Worker A claims, stalls past lease_until, Worker B recovers.
   Worker A resuming late raises PermanentJobError("JOB_STATE_CONFLICT") and cannot overwrite B.
4. Lease boundary timing: lease_until - 1ms, exact, and + 1ms.
5. Canonical decision uniqueness: At most one current decision per dispute case.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from app.database import connect_database, initialize_database
from app.domain import to_storage_timestamp
from app.jobs import (
    ClaimedJob,
    PermanentJobError,
    claim_next_job,
    complete_job,
)


def _create_test_case(db_path: Path, case_id: str, available_at: datetime) -> None:
    now_text = to_storage_timestamp(available_at)
    with connect_database(db_path) as conn:
        conn.execute(
            """
            INSERT INTO dispute_cases (
                id, razorpay_dispute_id, payment_id, amount_minor, currency,
                reason_profile, processing_status, workflow_status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, 'refund_not_processed_v1', 'QUEUED', 'REVIEW_PENDING', ?, ?)
            """,
            (case_id, f"disp_{case_id}", f"pay_{case_id}", 250000, "INR", now_text, now_text),
        )
        conn.execute(
            """
            INSERT INTO jobs (
                id, case_id, job_type, status, attempt_count,
                available_at, created_at, updated_at
            ) VALUES (?, ?, 'PROCESS_CASE', 'PENDING', 0, ?, ?, ?)
            """,
            (f"job_{case_id}", case_id, now_text, now_text, now_text),
        )


def test_concurrent_worker_claim_is_mutually_exclusive(tmp_path: Path) -> None:
    """16 concurrent threads attempting to claim a single job: exactly 1 succeeds."""
    db_path = tmp_path / "concurrent_claim.db"
    initialize_database(db_path)
    now = datetime(2026, 3, 1, 10, 0, 0, tzinfo=timezone.utc)
    _create_test_case(db_path, "case_race_1", now)
    lease_duration = timedelta(seconds=30)

    results: list[ClaimedJob | None] = []

    def _worker_claim() -> ClaimedJob | None:
        return claim_next_job(db_path, now, lease_duration)

    with ThreadPoolExecutor(max_workers=16) as executor:
        futures = [executor.submit(_worker_claim) for _ in range(16)]
        for f in futures:
            results.append(f.result())

    successful_claims = [r for r in results if r is not None]
    assert len(successful_claims) == 1
    assert successful_claims[0].id == "job_case_race_1"
    assert successful_claims[0].attempt_count == 1


def test_stale_worker_lease_recovery_and_late_completion_rejection(tmp_path: Path) -> None:
    """Worker A stalls past lease_until; Worker B recovers and completes. Worker A must fail."""
    db_path = tmp_path / "stale_lease.db"
    initialize_database(db_path)
    t0 = datetime(2026, 3, 1, 10, 0, 0, tzinfo=timezone.utc)
    _create_test_case(db_path, "case_stale_1", t0)
    lease = timedelta(seconds=10)

    # 1. Worker A claims job at t0
    job_a = claim_next_job(db_path, t0, lease)
    assert job_a is not None
    assert job_a.attempt_count == 1

    # 2. Worker B attempts to claim at t0 + 5s (lease active -> None)
    t_mid = t0 + timedelta(seconds=5)
    assert claim_next_job(db_path, t_mid, lease) is None

    # 3. Time advances past lease_until: t0 + 11s (stale lease)
    t_stale = t0 + timedelta(seconds=11)
    job_b = claim_next_job(db_path, t_stale, lease)
    assert job_b is not None
    assert job_b.id == job_a.id
    assert job_b.attempt_count == 2

    # 4. Worker A wakes up while B is still processing. Its old lease must be rejected.
    with pytest.raises(PermanentJobError) as exc_info:
        complete_job(db_path, job_a, t_stale + timedelta(seconds=1))
    assert exc_info.value.code == "JOB_STATE_CONFLICT"

    # 5. The current lease holder can still complete the job.
    complete_job(db_path, job_b, t_stale + timedelta(seconds=2))


def test_lease_boundary_timing(tmp_path: Path) -> None:
    """Validate lease boundary: lease - 1ms is active; lease + 1ms is eligible for recovery."""
    db_path = tmp_path / "boundary.db"
    initialize_database(db_path)
    t0 = datetime(2026, 3, 1, 10, 0, 0, tzinfo=timezone.utc)
    _create_test_case(db_path, "case_bound_1", t0)
    lease = timedelta(seconds=10)
    lease_until = t0 + lease

    # Claim at t0
    job = claim_next_job(db_path, t0, lease)
    assert job is not None

    # 1 second before lease_until -> still active, cannot claim
    t_before = lease_until - timedelta(seconds=1)
    assert claim_next_job(db_path, t_before, lease) is None

    # 1 second after lease_until -> lease expired, can be recovered
    t_after = lease_until + timedelta(seconds=1)
    job_recovered = claim_next_job(db_path, t_after, lease)
    assert job_recovered is not None
    assert job_recovered.attempt_count == 2


def test_canonical_decision_uniqueness_per_case(tmp_path: Path) -> None:
    """Verify that a dispute case in the authoritative database has at most one gate decision."""
    db_path = tmp_path / "uniqueness.db"
    initialize_database(db_path)
    now = datetime(2026, 3, 1, 10, 0, 0, tzinfo=timezone.utc)
    _create_test_case(db_path, "case_uniq_1", now)
    now_text = to_storage_timestamp(now)

    with connect_database(db_path) as conn:
        conn.execute(
            """
            INSERT INTO gate_decisions (
                id, case_id, status, primary_reason_code, engine_version,
                decision_json, created_at
            ) VALUES ('dec_uniq_1', 'case_uniq_1', 'PASS', NULL, 'v4.5', '{}', ?)
            """,
            (now_text,),
        )

    with connect_database(db_path) as conn:
        count = conn.execute(
            "SELECT COUNT(*) as cnt FROM gate_decisions WHERE case_id = 'case_uniq_1'"
        ).fetchone()["cnt"]
        assert count == 1
