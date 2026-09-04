from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from app.database import connect_database, initialize_database, insert_dispute_case
from app.domain import DisputeCaseCreate
from pydantic import ValidationError


def build_case(**overrides: object) -> DisputeCaseCreate:
    values: dict[str, object] = {
        "id": "case_001",
        "razorpay_dispute_id": "disp_001",
        "payment_id": "pay_001",
        "amount_minor": 250_000,
        "currency": "inr",
        "raw_reason_code": "merchant-raw-reason",
        "created_at": datetime(2026, 8, 23, 10, tzinfo=timezone(timedelta(hours=5, minutes=30))),
        "updated_at": datetime(2026, 8, 23, 10, tzinfo=timezone.utc),
    }
    values.update(overrides)
    return DisputeCaseCreate.model_validate(values)


def test_schema_enables_wal_foreign_keys_and_required_indexes(tmp_path: Path) -> None:
    database_path = tmp_path / "dig.sqlite3"

    initialize_database(database_path)
    initialize_database(database_path)

    with connect_database(database_path) as connection:
        tables = {
            row["name"]
            for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
        }
        indexes = {
            row["name"]
            for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'index'")
        }
        assert connection.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
        assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        assert {
            "ingest_events",
            "dispute_cases",
            "payment_snapshots",
            "refund_records",
            "evidence_documents",
            "extraction_runs",
            "grounded_claims",
            "findings",
            "gate_decisions",
            "jobs",
            "review_events",
            "evaluation_runs",
        } <= tables
        assert {
            "idx_refund_records_case_id",
            "idx_refund_records_payment_id",
            "idx_jobs_status_available_at",
        } <= indexes
        assert connection.execute("SELECT count(*) FROM schema_migrations").fetchone()[0] == 1


def test_normalized_case_preserves_raw_reason_and_utc_timestamp(tmp_path: Path) -> None:
    database_path = tmp_path / "dig.sqlite3"
    initialize_database(database_path)
    case = build_case()

    with connect_database(database_path) as connection:
        insert_dispute_case(connection, case)
        row = connection.execute("SELECT * FROM dispute_cases WHERE id = ?", (case.id,)).fetchone()

    assert row is not None
    assert row["raw_reason_code"] == "merchant-raw-reason"
    assert row["reason_profile"] == "refund_not_processed_v1"
    assert row["currency"] == "INR"
    assert row["created_at"] == "2026-08-23T04:30:00Z"


def test_domain_rejects_float_money_and_naive_timestamp() -> None:
    with pytest.raises(ValidationError, match="valid integer"):
        build_case(amount_minor=2500.5)

    with pytest.raises(ValidationError, match="timezone"):
        build_case(created_at=datetime(2026, 8, 23, 10))


def test_database_constraints_reject_invalid_money_and_orphans(tmp_path: Path) -> None:
    database_path = tmp_path / "dig.sqlite3"
    initialize_database(database_path)

    with connect_database(database_path) as connection:
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO refund_records
                    (id, case_id, payment_id, amount_minor, currency, local_status)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                ("rfnd_bad", "missing_case", "pay_001", 100, "INR", "processed"),
            )

        case = build_case()
        insert_dispute_case(connection, case)
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO refund_records
                    (id, case_id, payment_id, amount_minor, currency, local_status)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                ("rfnd_float", case.id, case.payment_id, 1.5, "INR", "processed"),
            )


def test_job_is_durable_across_connections(tmp_path: Path) -> None:
    database_path = tmp_path / "dig.sqlite3"
    initialize_database(database_path)
    case = build_case()
    timestamp = "2026-08-23T05:00:00Z"

    with connect_database(database_path) as connection:
        insert_dispute_case(connection, case)
        connection.execute(
            """
            INSERT INTO jobs (
                id, case_id, job_type, status, available_at, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            ("job_001", case.id, "PROCESS_CASE", "PENDING", timestamp, timestamp, timestamp),
        )

    with connect_database(database_path) as connection:
        row = connection.execute(
            "SELECT status, attempt_count FROM jobs WHERE id = ?", ("job_001",)
        ).fetchone()

    assert row is not None
    assert dict(row) == {"status": "PENDING", "attempt_count": 0}
