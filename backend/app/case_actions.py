"""Transactional local analyst actions with no external network writes."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime
from enum import Enum
from pathlib import Path
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.database import connect_database, initialize_database
from app.domain import require_utc, to_storage_timestamp


class QueuedReprocess(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str = "queued"
    job_id: str
    case_id: str
    network_write_performed: bool = False


class WorkflowActionError(ValueError):
    def __init__(self, code: str, message: str, status_code: int) -> None:
        super().__init__(message)
        self.code = code
        self.status_code = status_code


class InspectionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_ref: str = Field(min_length=1)
    document_id: str = Field(min_length=1)


class InspectionResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str = "inspected"
    case_id: str
    source_ref: str
    document_id: str
    network_write_performed: bool = False


class OverrideReason(str, Enum):
    SOURCE_DATA_ERROR = "SOURCE_DATA_ERROR"
    EVIDENCE_REPAIRED_OUTSIDE_APP = "EVIDENCE_REPAIRED_OUTSIDE_APP"
    KNOWN_BUSINESS_EXCEPTION = "KNOWN_BUSINESS_EXCEPTION"
    DISAGREE_WITH_RULE = "DISAGREE_WITH_RULE"
    OTHER = "OTHER"


class OverrideRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason: OverrideReason
    note: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def require_other_note(self) -> OverrideRequest:
        if self.reason is OverrideReason.OTHER and not (self.note and self.note.strip()):
            raise ValueError("A note is required for OTHER.")
        return self


class LocalWorkflowResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    case_id: str
    workflow_status: str
    gate_status: str
    network_write_performed: bool = False


def _idempotent_suffix(case_id: str, idempotency_key: str) -> str:
    return hashlib.sha256(f"{case_id}\x00{idempotency_key}".encode()).hexdigest()[:32]


def queue_reprocess(
    database_path: Path,
    *,
    case_id: str,
    operator_id: str,
    requested_at: datetime,
    idempotency_key: str | None = None,
) -> QueuedReprocess | None:
    """Append a repair request and durable job in one short local transaction."""
    initialize_database(database_path)
    timestamp = to_storage_timestamp(require_utc(requested_at))
    normalized_key = idempotency_key.strip() if idempotency_key else None
    if idempotency_key is not None and not normalized_key:
        raise ValueError("Idempotency-Key cannot be blank.")
    if not operator_id.strip():
        raise ValueError("Demo operator identity is not configured.")
    suffix = _idempotent_suffix(case_id, normalized_key) if normalized_key else uuid4().hex
    job_id = f"job_reprocess_{suffix}"
    event_id = f"review_reprocess_{suffix}"

    with connect_database(database_path) as connection:
        case = connection.execute(
            "SELECT id FROM dispute_cases WHERE id = ?", (case_id,)
        ).fetchone()
        if case is None:
            return None
        existing = connection.execute("SELECT id FROM jobs WHERE id = ?", (job_id,)).fetchone()
        if existing is not None:
            return QueuedReprocess(job_id=job_id, case_id=case_id)
        connection.execute(
            "INSERT INTO review_events "
            "(id, case_id, operator_id, event_type, reason_code, created_at) "
            "VALUES (?, ?, ?, 'REPAIR_REQUESTED', 'REPROCESS_AFTER_REPAIR', ?)",
            (event_id, case_id, operator_id, timestamp),
        )
        connection.execute(
            "INSERT INTO jobs "
            "(id, case_id, job_type, status, available_at, created_at, updated_at) "
            "VALUES (?, ?, 'PROCESS_CASE', 'PENDING', ?, ?, ?)",
            (job_id, case_id, timestamp, timestamp, timestamp),
        )
        connection.execute(
            "UPDATE dispute_cases SET processing_status = 'QUEUED', "
            "workflow_status = 'REVIEW_PENDING', updated_at = ? WHERE id = ?",
            (timestamp, case_id),
        )
    return QueuedReprocess(job_id=job_id, case_id=case_id)


def _latest_gate_status(connection: sqlite3.Connection, case_id: str) -> str | None:
    row = connection.execute(
        "SELECT status FROM gate_decisions WHERE case_id = ? "
        "ORDER BY created_at DESC, id DESC LIMIT 1",
        (case_id,),
    ).fetchone()
    return str(row["status"]) if row is not None else None


def _required_block_sources(connection: sqlite3.Connection, case_id: str) -> set[str]:
    rows = connection.execute(
        "SELECT structured_refs_json, claim_refs_json FROM findings "
        "WHERE case_id = ? AND decision_effect = 'BLOCK'",
        (case_id,),
    ).fetchall()
    required: set[str] = set()
    for row in rows:
        for field in ("structured_refs_json", "claim_refs_json"):
            value = json.loads(row[field]) if row[field] else []
            if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
                raise WorkflowActionError(
                    "WORKFLOW_SOURCE_STATE_INVALID",
                    "Stored finding source references are invalid.",
                    500,
                )
            required.update(value)
    return required


def inspect_source(
    database_path: Path,
    *,
    case_id: str,
    operator_id: str,
    request: InspectionRequest,
    inspected_at: datetime,
) -> InspectionResult:
    """Validate and append one evidence-directed source inspection."""
    initialize_database(database_path)
    timestamp = to_storage_timestamp(require_utc(inspected_at))
    with connect_database(database_path) as connection:
        gate_status = _latest_gate_status(connection, case_id)
        if gate_status is None:
            raise WorkflowActionError("CASE_NOT_FOUND", "Case was not found.", 404)
        if gate_status != "BLOCK":
            raise WorkflowActionError(
                "INSPECTION_NOT_REQUIRED", "Current gate status is not BLOCK.", 409
            )
        required = _required_block_sources(connection, case_id)
        if request.source_ref not in required:
            raise WorkflowActionError(
                "SOURCE_NOT_REQUIRED", "Source is not cited by a material finding.", 422
            )
        claim = connection.execute(
            "SELECT claims.document_id FROM grounded_claims AS claims "
            "JOIN evidence_documents AS documents ON documents.id = claims.document_id "
            "WHERE claims.id = ? AND documents.case_id = ?",
            (request.source_ref, case_id),
        ).fetchone()
        refund = connection.execute(
            "SELECT id FROM refund_records WHERE id = ? AND case_id = ?",
            (request.source_ref, case_id),
        ).fetchone()
        valid_claim = claim is not None and claim["document_id"] == request.document_id
        valid_refund = refund is not None and request.document_id == "structured_refund_ledger"
        valid_complete_ledger = (
            request.source_ref == "structured_refund_ledger"
            and request.document_id == "structured_refund_ledger"
        )
        if not valid_claim and not valid_refund and not valid_complete_ledger:
            raise WorkflowActionError(
                "SOURCE_BINDING_INVALID",
                "Source reference is not bound to the supplied local document.",
                422,
            )
        existing = connection.execute(
            "SELECT id FROM review_events WHERE case_id = ? AND operator_id = ? "
            "AND event_type = 'SOURCE_INSPECTED' "
            "AND json_extract(details_json, '$.source_ref') = ?",
            (case_id, operator_id, request.source_ref),
        ).fetchone()
        if existing is None:
            connection.execute(
                "INSERT INTO review_events "
                "(id, case_id, operator_id, event_type, details_json, created_at) "
                "VALUES (?, ?, ?, 'SOURCE_INSPECTED', ?, ?)",
                (
                    f"review_inspect_{uuid4().hex}",
                    case_id,
                    operator_id,
                    json.dumps(
                        {
                            "document_id": request.document_id,
                            "source_ref": request.source_ref,
                        },
                        sort_keys=True,
                        separators=(",", ":"),
                    ),
                    timestamp,
                ),
            )
    return InspectionResult(
        case_id=case_id,
        source_ref=request.source_ref,
        document_id=request.document_id,
    )


def override_local_hold(
    database_path: Path,
    *,
    case_id: str,
    operator_id: str,
    request: OverrideRequest,
    overridden_at: datetime,
) -> LocalWorkflowResult:
    """Change local readiness only after every material source was inspected."""
    initialize_database(database_path)
    timestamp = to_storage_timestamp(require_utc(overridden_at))
    with connect_database(database_path) as connection:
        row = connection.execute(
            "SELECT workflow_status FROM dispute_cases WHERE id = ?", (case_id,)
        ).fetchone()
        if row is None:
            raise WorkflowActionError("CASE_NOT_FOUND", "Case was not found.", 404)
        gate_status = _latest_gate_status(connection, case_id)
        if gate_status != "BLOCK":
            raise WorkflowActionError(
                "OVERRIDE_REQUIRES_BLOCK", "Current gate status is not BLOCK.", 409
            )
        required = _required_block_sources(connection, case_id)
        if not required:
            raise WorkflowActionError(
                "OVERRIDE_SOURCES_MISSING", "Material finding has no inspectable sources.", 409
            )
        inspected_rows = connection.execute(
            "SELECT details_json FROM review_events WHERE case_id = ? AND operator_id = ? "
            "AND event_type = 'SOURCE_INSPECTED'",
            (case_id, operator_id),
        ).fetchall()
        inspected: set[str] = set()
        for event in inspected_rows:
            details = json.loads(event["details_json"])
            source_ref = details.get("source_ref") if isinstance(details, dict) else None
            if isinstance(source_ref, str):
                inspected.add(source_ref)
        missing = sorted(required - inspected)
        if missing:
            raise WorkflowActionError(
                "OVERRIDE_INSPECTION_REQUIRED",
                f"Inspect every cited source before override: {', '.join(missing)}",
                409,
            )
        connection.execute(
            "INSERT INTO review_events "
            "(id, case_id, operator_id, event_type, reason_code, note, details_json, created_at) "
            "VALUES (?, ?, ?, 'LOCAL_HOLD_OVERRIDDEN', ?, ?, ?, ?)",
            (
                f"review_override_{uuid4().hex}",
                case_id,
                operator_id,
                request.reason.value,
                request.note.strip() if request.note else None,
                json.dumps({"inspected_source_refs": sorted(required)}, separators=(",", ":")),
                timestamp,
            ),
        )
        connection.execute(
            "UPDATE dispute_cases SET workflow_status = 'READY_WITH_OVERRIDE', updated_at = ? "
            "WHERE id = ?",
            (timestamp, case_id),
        )
    return LocalWorkflowResult(
        case_id=case_id,
        workflow_status="READY_WITH_OVERRIDE",
        gate_status="BLOCK",
    )


def mark_ready(
    database_path: Path,
    *,
    case_id: str,
    operator_id: str,
    marked_at: datetime,
) -> LocalWorkflowResult:
    """Mark local readiness for PASS or an already structured BLOCK override."""
    initialize_database(database_path)
    timestamp = to_storage_timestamp(require_utc(marked_at))
    with connect_database(database_path) as connection:
        case = connection.execute(
            "SELECT workflow_status FROM dispute_cases WHERE id = ?", (case_id,)
        ).fetchone()
        if case is None:
            raise WorkflowActionError("CASE_NOT_FOUND", "Case was not found.", 404)
        gate_status = _latest_gate_status(connection, case_id)
        if gate_status != "PASS" and case["workflow_status"] != "READY_WITH_OVERRIDE":
            raise WorkflowActionError(
                "MARK_READY_PRECONDITION_FAILED",
                "Case requires PASS or a completed local BLOCK override.",
                409,
            )
        connection.execute(
            "INSERT INTO review_events "
            "(id, case_id, operator_id, event_type, created_at) "
            "VALUES (?, ?, ?, 'MARKED_READY', ?)",
            (f"review_ready_{uuid4().hex}", case_id, operator_id, timestamp),
        )
        connection.execute(
            "UPDATE dispute_cases SET workflow_status = 'READY_FOR_CONTEST', updated_at = ? "
            "WHERE id = ?",
            (timestamp, case_id),
        )
    return LocalWorkflowResult(
        case_id=case_id,
        workflow_status="READY_FOR_CONTEST",
        gate_status=gate_status or "REVIEW",
    )
