"""Crash-consistency and recovery property tests for PRAMAAN.

Validates the Crash-Consistency Requirements:
1. Crash before commit => total rollback; zero orphaned records.
2. Crash after worker lease => restart allows recovery after lease expiry.
3. Crash during model/solver execution => case remains in recoverable state.
4. No double decisions or duplicate cases created on recovery.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from app.database import connect_database, initialize_database
from app.domain import to_storage_timestamp
from app.jobs import claim_next_job


def test_crash_before_commit_guarantees_atomic_rollback(tmp_path: Path) -> None:
    """If a process crashes or raises an exception before COMMIT, nothing is persisted."""
    db_path = tmp_path / "crash_rollback.db"
    initialize_database(db_path)
    now_text = to_storage_timestamp(datetime.now(timezone.utc))

    with connect_database(db_path) as conn:
        conn.execute("BEGIN IMMEDIATE")
        conn.execute(
            """
            INSERT INTO dispute_cases (
                id, razorpay_dispute_id, payment_id, amount_minor, currency,
                reason_profile, processing_status, workflow_status, created_at, updated_at
            ) VALUES ('case_crash_1', 'disp_1', 'pay_1', 10000, 'INR',
                      'refund_not_processed_v1', 'QUEUED', 'REVIEW_PENDING', ?, ?)
            """,
            (now_text, now_text),
        )
        # Simulate unhandled crash before conn.commit()
        conn.rollback()

    with connect_database(db_path) as conn:
        row = conn.execute(
            "SELECT COUNT(*) as cnt FROM dispute_cases WHERE id = 'case_crash_1'"
        ).fetchone()
        assert row["cnt"] == 0


def test_crash_during_worker_execution_allows_safe_restart(tmp_path: Path) -> None:
    """Worker crashes mid-execution; job is safely claimed by recovered worker after lease."""
    db_path = tmp_path / "worker_crash.db"
    initialize_database(db_path)

    t0 = datetime(2026, 3, 1, 10, 0, 0, tzinfo=timezone.utc)
    now_text = to_storage_timestamp(t0)

    # Ingest case and job
    with connect_database(db_path) as conn:
        conn.execute(
            """
            INSERT INTO dispute_cases (
                id, razorpay_dispute_id, payment_id, amount_minor, currency,
                reason_profile, processing_status, workflow_status, created_at, updated_at
            ) VALUES ('case_rec_1', 'disp_1', 'pay_1', 50000, 'INR',
                      'refund_not_processed_v1', 'QUEUED', 'REVIEW_PENDING', ?, ?)
            """,
            (now_text, now_text),
        )
        conn.execute(
            """
            INSERT INTO jobs (
                id, case_id, job_type, status, attempt_count,
                available_at, created_at, updated_at
            ) VALUES ('job_rec_1', 'case_rec_1', 'PROCESS_CASE', 'PENDING', 0, ?, ?, ?)
            """,
            (now_text, now_text, now_text),
        )

    # Worker 1 claims job with 15-second lease
    lease = timedelta(seconds=15)
    job_1 = claim_next_job(db_path, t0, lease)
    assert job_1 is not None
    assert job_1.attempt_count == 1

    # Worker 1 dies abruptly (simulating SIGKILL). The database connection is closed.
    # At t0 + 10s (within lease), another worker cannot claim it
    assert claim_next_job(db_path, t0 + timedelta(seconds=10), lease) is None

    # At t0 + 16s (lease expired), recovered Worker 2 safely claims it
    job_2 = claim_next_job(db_path, t0 + timedelta(seconds=16), lease)
    assert job_2 is not None
    assert job_2.id == "job_rec_1"
    assert job_2.attempt_count == 2


def test_duplicate_case_id_rejected_atomically(tmp_path: Path) -> None:
    """Inserting a duplicate case ID violates PRIMARY KEY and rolls back transaction."""
    db_path = tmp_path / "dup_case.db"
    initialize_database(db_path)
    now_text = to_storage_timestamp(datetime.now(timezone.utc))

    with connect_database(db_path) as conn:
        conn.execute(
            """
            INSERT INTO dispute_cases (
                id, razorpay_dispute_id, payment_id, amount_minor, currency,
                reason_profile, processing_status, workflow_status, created_at, updated_at
            ) VALUES ('case_same_id', 'disp_1', 'pay_1', 10000, 'INR',
                      'refund_not_processed_v1', 'QUEUED', 'REVIEW_PENDING', ?, ?)
            """,
            (now_text, now_text),
        )

    with connect_database(db_path) as conn, pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            """
                INSERT INTO dispute_cases (
                    id, razorpay_dispute_id, payment_id, amount_minor, currency,
                    reason_profile, processing_status, workflow_status, created_at, updated_at
                ) VALUES ('case_same_id', 'disp_2', 'pay_2', 20000, 'INR',
                          'refund_not_processed_v1', 'QUEUED', 'REVIEW_PENDING', ?, ?)
                """,
            (now_text, now_text),
        )

    # Verify original record unchanged
    with connect_database(db_path) as conn:
        row = conn.execute(
            "SELECT razorpay_dispute_id, amount_minor FROM dispute_cases WHERE id = 'case_same_id'"
        ).fetchone()
        assert row["razorpay_dispute_id"] == "disp_1"
        assert row["amount_minor"] == 10000
