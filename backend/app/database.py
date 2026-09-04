"""SQLite connection, migration, and minimal persistence helpers.

# ponytail: SQLite WAL intentionally limits this implementation to a single-node deployment.
# Replace the repository layer with PostgreSQL before multi-node horizontal scaling.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from app.domain import DisputeCaseCreate, to_storage_timestamp

SCHEMA_VERSION = 1

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ingest_events (
    razorpay_event_id TEXT PRIMARY KEY,
    event_name TEXT NOT NULL,
    account_id TEXT,
    body_sha256 TEXT NOT NULL,
    received_at TEXT NOT NULL,
    event_created_at TEXT,
    case_id TEXT,
    correlation_id TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS dispute_cases (
    id TEXT PRIMARY KEY,
    razorpay_dispute_id TEXT UNIQUE,
    payment_id TEXT NOT NULL,
    amount_minor INTEGER NOT NULL CHECK (typeof(amount_minor) = 'integer' AND amount_minor >= 0),
    currency TEXT NOT NULL CHECK (currency = upper(currency) AND length(currency) = 3),
    raw_reason_code TEXT,
    reason_description TEXT,
    reason_profile TEXT NOT NULL CHECK (reason_profile = 'refund_not_processed_v1'),
    respond_by TEXT,
    razorpay_status TEXT,
    razorpay_phase TEXT,
    processing_status TEXT NOT NULL CHECK (processing_status IN (
        'RECEIVED', 'VALIDATED', 'QUEUED', 'PROCESSING', 'READY', 'RETRYABLE_ERROR', 'FAILED'
    )),
    workflow_status TEXT NOT NULL CHECK (workflow_status IN (
        'REVIEW_PENDING', 'READY_WITH_OVERRIDE', 'READY_FOR_CONTEST'
    )),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS payment_snapshots (
    case_id TEXT PRIMARY KEY REFERENCES dispute_cases(id),
    payment_id TEXT NOT NULL,
    captured_amount_minor INTEGER CHECK (
        captured_amount_minor IS NULL OR
        (typeof(captured_amount_minor) = 'integer' AND captured_amount_minor >= 0)
    ),
    currency TEXT CHECK (currency IS NULL OR (currency = upper(currency) AND length(currency) = 3)),
    captured_at TEXT,
    snapshot_complete INTEGER NOT NULL CHECK (snapshot_complete IN (0, 1)),
    snapshot_json TEXT
);

CREATE TABLE IF NOT EXISTS refund_records (
    id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL REFERENCES dispute_cases(id),
    payment_id TEXT NOT NULL,
    amount_minor INTEGER NOT NULL CHECK (typeof(amount_minor) = 'integer' AND amount_minor >= 0),
    currency TEXT NOT NULL CHECK (currency = upper(currency) AND length(currency) = 3),
    local_status TEXT NOT NULL CHECK (local_status IN (
        'created', 'pending', 'processed', 'failed', 'cancelled'
    )),
    created_at TEXT,
    processed_at TEXT,
    reference TEXT
);
CREATE INDEX IF NOT EXISTS idx_refund_records_case_id ON refund_records(case_id);
CREATE INDEX IF NOT EXISTS idx_refund_records_payment_id ON refund_records(payment_id);

CREATE TABLE IF NOT EXISTS evidence_documents (
    id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL REFERENCES dispute_cases(id),
    source_type TEXT NOT NULL,
    source_system TEXT,
    media_type TEXT NOT NULL CHECK (media_type IN ('text/plain', 'application/json')),
    canonical_text TEXT NOT NULL,
    content_sha256 TEXT NOT NULL,
    captured_at TEXT,
    ingested_at TEXT NOT NULL,
    is_complete_source INTEGER CHECK (is_complete_source IN (0, 1)),
    metadata_json TEXT
);

CREATE TABLE IF NOT EXISTS extraction_runs (
    id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL REFERENCES evidence_documents(id),
    extractor_id TEXT NOT NULL,
    model_id TEXT,
    prompt_version TEXT NOT NULL,
    schema_version TEXT NOT NULL,
    request_hash TEXT NOT NULL,
    status TEXT NOT NULL,
    latency_ms INTEGER CHECK (latency_ms IS NULL OR latency_ms >= 0),
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_extraction_runs_request_hash ON extraction_runs(request_hash);

CREATE TABLE IF NOT EXISTS grounded_claims (
    id TEXT PRIMARY KEY,
    extraction_run_id TEXT NOT NULL REFERENCES extraction_runs(id),
    document_id TEXT NOT NULL REFERENCES evidence_documents(id),
    claim_type TEXT NOT NULL,
    subject TEXT,
    raw_value TEXT,
    amount_minor INTEGER CHECK (
        amount_minor IS NULL OR (typeof(amount_minor) = 'integer' AND amount_minor >= 0)
    ),
    currency TEXT CHECK (currency IS NULL OR (currency = upper(currency) AND length(currency) = 3)),
    date_text TEXT,
    normalized_timestamp TEXT,
    refund_reference TEXT,
    modality TEXT,
    source_quote TEXT NOT NULL,
    span_start INTEGER CHECK (span_start IS NULL OR span_start >= 0),
    span_end INTEGER CHECK (span_end IS NULL OR span_end >= 0),
    grounding_status TEXT NOT NULL CHECK (grounding_status IN (
        'GROUNDED', 'UNGROUNDED', 'AMBIGUOUS'
    )),
    created_at TEXT NOT NULL,
    CHECK (span_start IS NULL OR span_end IS NULL OR span_end >= span_start)
);

CREATE TABLE IF NOT EXISTS findings (
    id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL REFERENCES dispute_cases(id),
    rule_code TEXT NOT NULL,
    severity TEXT NOT NULL,
    decision_effect TEXT NOT NULL CHECK (decision_effect IN ('PASS', 'REVIEW', 'BLOCK')),
    explanation TEXT NOT NULL,
    structured_refs_json TEXT,
    claim_refs_json TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS gate_decisions (
    id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL REFERENCES dispute_cases(id),
    status TEXT NOT NULL CHECK (status IN ('PASS', 'REVIEW', 'BLOCK')),
    primary_reason_code TEXT,
    engine_version TEXT NOT NULL,
    decision_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_gate_decisions_case_created ON gate_decisions(case_id, created_at);

CREATE TABLE IF NOT EXISTS jobs (
    id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL REFERENCES dispute_cases(id),
    job_type TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN (
        'PENDING', 'PROCESSING', 'RETRYABLE_ERROR', 'COMPLETED', 'FAILED'
    )),
    attempt_count INTEGER NOT NULL DEFAULT 0 CHECK (attempt_count >= 0),
    available_at TEXT NOT NULL,
    lease_until TEXT,
    last_error_code TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_jobs_status_available_at ON jobs(status, available_at);

CREATE TABLE IF NOT EXISTS review_events (
    id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL REFERENCES dispute_cases(id),
    operator_id TEXT NOT NULL,
    event_type TEXT NOT NULL CHECK (event_type IN (
        'SOURCE_INSPECTED', 'REPAIR_REQUESTED', 'LOCAL_HOLD_OVERRIDDEN',
        'MARKED_READY', 'RETURNED_TO_REVIEW'
    )),
    reason_code TEXT,
    note TEXT,
    details_json TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS evaluation_runs (
    id TEXT PRIMARY KEY,
    dataset_id TEXT NOT NULL,
    dataset_manifest_hash TEXT NOT NULL,
    system_config_hash TEXT NOT NULL,
    split TEXT NOT NULL CHECK (split IN ('dev', 'holdout')),
    artifact_path TEXT NOT NULL,
    artifact_sha256 TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""


def connect_database(path: Path) -> sqlite3.Connection:
    """Open a configured SQLite connection with safety pragmas enabled."""
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=5.0)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 5000")
    connection.execute("PRAGMA journal_mode = WAL")
    return connection


def initialize_database(path: Path) -> None:
    """Idempotently initialize the versioned v1 schema."""
    with connect_database(path) as connection:
        connection.executescript(SCHEMA_SQL)
        connection.execute(
            "INSERT OR IGNORE INTO schema_migrations(version, applied_at) "
            "VALUES (?, strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))",
            (SCHEMA_VERSION,),
        )


def insert_dispute_case(connection: sqlite3.Connection, case: DisputeCaseCreate) -> None:
    """Persist a normalized case with parameterized SQL."""
    connection.execute(
        """
        INSERT INTO dispute_cases (
            id, razorpay_dispute_id, payment_id, amount_minor, currency,
            raw_reason_code, reason_description, reason_profile, respond_by,
            razorpay_status, razorpay_phase, processing_status, workflow_status,
            created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            case.id,
            case.razorpay_dispute_id,
            case.payment_id,
            case.amount_minor,
            case.currency,
            case.raw_reason_code,
            case.reason_description,
            case.reason_profile,
            to_storage_timestamp(case.respond_by),
            case.razorpay_status,
            case.razorpay_phase,
            case.processing_status.value,
            case.workflow_status.value,
            to_storage_timestamp(case.created_at),
            to_storage_timestamp(case.updated_at),
        ),
    )
