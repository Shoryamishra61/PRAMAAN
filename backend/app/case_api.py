"""Read-only analyst queue and case-workspace queries."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import cast

from pydantic import BaseModel, ConfigDict, Field, JsonValue

from app.database import connect_database, initialize_database
from app.decision import GateStatus
from app.domain import ProcessingStatus, WorkflowStatus


class QueueItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    case_id: str
    dispute_id: str
    payment_id: str
    amount_minor: int = Field(ge=0)
    currency: str
    respond_by: str | None
    raw_reason_code: str | None
    reason_profile: str
    processing_status: ProcessingStatus
    gate_status: GateStatus | None
    primary_reason_code: str | None


class CaseListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: tuple[QueueItem, ...]
    next_cursor: str | None


class PaymentSnapshotResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    payment_id: str
    captured_amount_minor: int | None
    currency: str | None
    captured_at: str | None
    snapshot_complete: bool


class RefundResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    payment_id: str
    amount_minor: int = Field(ge=0)
    currency: str
    local_status: str
    created_at: str | None
    processed_at: str | None
    reference: str | None


class EvidenceResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    source_type: str
    source_system: str | None
    media_type: str
    canonical_text: str
    content_sha256: str
    captured_at: str | None
    ingested_at: str
    is_complete_source: bool | None


class ClaimResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    document_id: str
    claim_type: str
    raw_value: str | None
    amount_minor: int | None
    currency: str | None
    refund_reference: str | None
    modality: str | None
    source_quote: str
    span_start: int | None
    span_end: int | None
    grounding_status: str


class FindingResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    rule_code: str
    severity: str
    decision_effect: GateStatus
    explanation: str
    structured_refs: tuple[str, ...]
    claim_refs: tuple[str, ...]


class AuditEventResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    operator_id: str
    event_type: str
    reason_code: str | None
    note: str | None
    details: dict[str, JsonValue]
    created_at: str


class CaseDetailResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    case: QueueItem
    workflow_status: WorkflowStatus
    payment_snapshot: PaymentSnapshotResponse | None
    refunds: tuple[RefundResponse, ...]
    evidence_documents: tuple[EvidenceResponse, ...]
    grounded_claims: tuple[ClaimResponse, ...]
    findings: tuple[FindingResponse, ...]
    gate_decision: dict[str, JsonValue] | None
    audit_events: tuple[AuditEventResponse, ...]


def _latest_decision_join() -> str:
    return """
        LEFT JOIN gate_decisions AS decision
          ON decision.id = (
            SELECT newest.id
              FROM gate_decisions AS newest
             WHERE newest.case_id = cases.id
             ORDER BY newest.created_at DESC, newest.id DESC
             LIMIT 1
          )
    """


def _queue_item(row: sqlite3.Row) -> QueueItem:
    return QueueItem(
        case_id=row["case_id"],
        dispute_id=row["dispute_id"],
        payment_id=row["payment_id"],
        amount_minor=row["amount_minor"],
        currency=row["currency"],
        respond_by=row["respond_by"],
        raw_reason_code=row["raw_reason_code"],
        reason_profile=row["reason_profile"],
        processing_status=row["processing_status"],
        gate_status=row["gate_status"],
        primary_reason_code=row["primary_reason_code"],
    )


def list_cases(
    database_path: Path,
    *,
    gate_status: GateStatus | None = None,
    processing_status: ProcessingStatus | None = None,
    reason_profile: str | None = None,
    limit: int = 50,
    cursor: str | None = None,
) -> CaseListResponse:
    """Return a stable, urgency-oriented local queue with optional filters."""
    initialize_database(database_path)
    conditions: list[str] = []
    parameters: list[object] = []
    if gate_status is not None:
        conditions.append("decision.status = ?")
        parameters.append(gate_status.value)
    if processing_status is not None:
        conditions.append("cases.processing_status = ?")
        parameters.append(processing_status.value)
    if reason_profile is not None:
        conditions.append("cases.reason_profile = ?")
        parameters.append(reason_profile)
    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    query = f"""
        SELECT cases.id AS case_id,
               cases.razorpay_dispute_id AS dispute_id,
               cases.payment_id,
               cases.amount_minor,
               cases.currency,
               cases.respond_by,
               cases.raw_reason_code,
               cases.reason_profile,
               cases.processing_status,
               decision.status AS gate_status,
               decision.primary_reason_code
          FROM dispute_cases AS cases
          {_latest_decision_join()}
          {where}
         ORDER BY CASE decision.status
                    WHEN 'REVIEW' THEN 0
                    WHEN 'BLOCK' THEN 1
                    WHEN 'PASS' THEN 2
                    ELSE 3
                  END,
                  CASE WHEN cases.respond_by IS NULL THEN 1 ELSE 0 END,
                  cases.respond_by ASC,
                  cases.amount_minor DESC,
                  cases.id ASC
    """
    with connect_database(database_path) as connection:
        rows = connection.execute(query, parameters).fetchall()
    if cursor is not None:
        cursor_index = next(
            (index for index, row in enumerate(rows) if row["case_id"] == cursor),
            None,
        )
        if cursor_index is None:
            raise ValueError("Invalid queue cursor.")
        rows = rows[cursor_index + 1 :]
    page = rows[:limit]
    next_cursor = page[-1]["case_id"] if len(rows) > limit else None
    return CaseListResponse(items=tuple(_queue_item(row) for row in page), next_cursor=next_cursor)


def _json_tuple(value: str | None) -> tuple[str, ...]:
    if value is None:
        return ()
    parsed = json.loads(value)
    if not isinstance(parsed, list) or not all(isinstance(item, str) for item in parsed):
        raise ValueError("Expected a JSON array of source identifiers.")
    return tuple(parsed)


def _json_object(value: str | None) -> dict[str, JsonValue]:
    if value is None:
        return {}
    parsed = json.loads(value)
    if not isinstance(parsed, dict):
        raise ValueError("Expected a JSON object.")
    return cast(dict[str, JsonValue], parsed)


def get_case(database_path: Path, case_id: str) -> CaseDetailResponse | None:
    """Load only local normalized state; provider raw responses and secrets are absent."""
    initialize_database(database_path)
    with connect_database(database_path) as connection:
        case_row = connection.execute(
            f"""
            SELECT cases.id AS case_id,
                   cases.razorpay_dispute_id AS dispute_id,
                   cases.payment_id,
                   cases.amount_minor,
                   cases.currency,
                   cases.respond_by,
                   cases.raw_reason_code,
                   cases.reason_profile,
                   cases.processing_status,
                   cases.workflow_status,
                   decision.status AS gate_status,
                   decision.primary_reason_code,
                   decision.decision_json
              FROM dispute_cases AS cases
              {_latest_decision_join()}
             WHERE cases.id = ?
            """,
            (case_id,),
        ).fetchone()
        if case_row is None:
            return None
        payment_row = connection.execute(
            "SELECT payment_id, captured_amount_minor, currency, captured_at, "
            "snapshot_complete FROM payment_snapshots WHERE case_id = ?",
            (case_id,),
        ).fetchone()
        refund_rows = connection.execute(
            "SELECT id, payment_id, amount_minor, currency, local_status, created_at, "
            "processed_at, reference FROM refund_records WHERE case_id = ? ORDER BY id",
            (case_id,),
        ).fetchall()
        evidence_rows = connection.execute(
            "SELECT id, source_type, source_system, media_type, canonical_text, content_sha256, "
            "captured_at, ingested_at, is_complete_source FROM evidence_documents "
            "WHERE case_id = ? ORDER BY ingested_at, id",
            (case_id,),
        ).fetchall()
        claim_rows = connection.execute(
            "SELECT claims.id, claims.document_id, claims.claim_type, claims.raw_value, "
            "claims.amount_minor, claims.currency, claims.refund_reference, claims.modality, "
            "claims.source_quote, claims.span_start, claims.span_end, claims.grounding_status "
            "FROM grounded_claims AS claims JOIN extraction_runs AS runs "
            "ON runs.id = claims.extraction_run_id JOIN evidence_documents AS documents "
            "ON documents.id = claims.document_id WHERE documents.case_id = ? "
            "ORDER BY claims.created_at, claims.id",
            (case_id,),
        ).fetchall()
        finding_rows = connection.execute(
            "SELECT id, rule_code, severity, decision_effect, explanation, "
            "structured_refs_json, claim_refs_json FROM findings "
            "WHERE case_id = ? ORDER BY created_at, id",
            (case_id,),
        ).fetchall()
        audit_rows = connection.execute(
            "SELECT id, operator_id, event_type, reason_code, note, details_json, created_at "
            "FROM review_events WHERE case_id = ? ORDER BY created_at, id",
            (case_id,),
        ).fetchall()

    payment: PaymentSnapshotResponse | None = None
    if payment_row is not None:
        payment_values = dict(payment_row)
        snapshot_complete = bool(payment_values.pop("snapshot_complete"))
        payment = PaymentSnapshotResponse(
            **payment_values,
            snapshot_complete=snapshot_complete,
        )
    findings = tuple(
        FindingResponse(
            id=row["id"],
            rule_code=row["rule_code"],
            severity=row["severity"],
            decision_effect=row["decision_effect"],
            explanation=row["explanation"],
            structured_refs=_json_tuple(row["structured_refs_json"]),
            claim_refs=_json_tuple(row["claim_refs_json"]),
        )
        for row in finding_rows
    )
    decision_json = case_row["decision_json"]
    return CaseDetailResponse(
        case=_queue_item(case_row),
        workflow_status=case_row["workflow_status"],
        payment_snapshot=payment,
        refunds=tuple(RefundResponse.model_validate(dict(row)) for row in refund_rows),
        evidence_documents=tuple(_evidence_response(row) for row in evidence_rows),
        grounded_claims=tuple(ClaimResponse.model_validate(dict(row)) for row in claim_rows),
        findings=findings,
        gate_decision=_json_object(decision_json) if decision_json is not None else None,
        audit_events=tuple(
            AuditEventResponse(
                id=row["id"],
                operator_id=row["operator_id"],
                event_type=row["event_type"],
                reason_code=row["reason_code"],
                note=row["note"],
                details=_json_object(row["details_json"]),
                created_at=row["created_at"],
            )
            for row in audit_rows
        ),
    )


def _evidence_response(row: sqlite3.Row) -> EvidenceResponse:
    values = dict(row)
    complete_value = values.pop("is_complete_source")
    return EvidenceResponse(
        **values,
        is_complete_source=(bool(complete_value) if complete_value is not None else None),
    )
