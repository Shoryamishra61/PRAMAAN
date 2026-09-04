"""Authenticated Razorpay-compatible event parsing and atomic durable ingestion."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.database import connect_database, initialize_database, insert_dispute_case
from app.domain import DisputeCaseCreate, ProcessingStatus

SUPPORTED_EVENT = "payment.dispute.created"


class IngestPayloadError(ValueError):
    code = "INGEST_PAYLOAD_INVALID"


class PaymentEntity(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str = Field(min_length=1)
    entity: Literal["payment"]
    amount: int = Field(strict=True, ge=0)
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    created_at: int | None = Field(default=None, strict=True, ge=0)


class DisputeEntity(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str = Field(min_length=1)
    entity: Literal["dispute"]
    payment_id: str = Field(min_length=1)
    amount: int = Field(strict=True, ge=0)
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    reason_code: str | None = None
    reason_description: str | None = None
    respond_by: int | None = Field(default=None, strict=True, ge=0)
    status: str | None = None
    phase: str | None = None
    created_at: int = Field(strict=True, ge=0)


class EntityWrapper(BaseModel):
    model_config = ConfigDict(extra="allow")

    entity: dict[str, Any]


class EventPayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    payment: EntityWrapper
    dispute: EntityWrapper


class RazorpayEvent(BaseModel):
    model_config = ConfigDict(extra="allow")

    entity: Literal["event"]
    account_id: str | None = None
    event: str = Field(min_length=1)
    contains: tuple[str, ...] = ()
    payload: EventPayload | None = None
    created_at: int | None = Field(default=None, strict=True, ge=0)


class IngestResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["accepted"] = "accepted"
    event_id: str
    case_id: str | None
    correlation_id: str
    duplicate: bool
    processing_scheduled: bool


def _utc_from_epoch(value: int | None) -> datetime | None:
    return datetime.fromtimestamp(value, timezone.utc) if value is not None else None


def _parse_event(raw_body: bytes) -> RazorpayEvent:
    try:
        payload = json.loads(raw_body)
        return RazorpayEvent.model_validate(payload)
    except (json.JSONDecodeError, UnicodeDecodeError, ValidationError) as error:
        raise IngestPayloadError("Webhook payload validation failed.") from error


def _case_from_created_event(event: RazorpayEvent, now: datetime) -> DisputeCaseCreate:
    if event.payload is None:
        raise IngestPayloadError("Created dispute event is missing payload entities.")
    try:
        payment = PaymentEntity.model_validate(event.payload.payment.entity)
        dispute = DisputeEntity.model_validate(event.payload.dispute.entity)
    except ValidationError as error:
        raise IngestPayloadError("Created dispute entity validation failed.") from error

    if payment.id != dispute.payment_id:
        raise IngestPayloadError("Dispute payment identifier does not match payload payment.")
    if payment.currency != dispute.currency:
        raise IngestPayloadError("Dispute currency does not match payload payment.")

    return DisputeCaseCreate(
        id=f"case_{dispute.id}",
        razorpay_dispute_id=dispute.id,
        payment_id=dispute.payment_id,
        amount_minor=dispute.amount,
        currency=dispute.currency,
        raw_reason_code=dispute.reason_code,
        reason_description=dispute.reason_description,
        respond_by=_utc_from_epoch(dispute.respond_by),
        razorpay_status=dispute.status,
        razorpay_phase=dispute.phase,
        processing_status=ProcessingStatus.QUEUED,
        created_at=_utc_from_epoch(dispute.created_at) or now,
        updated_at=now,
    )


def ingest_event(
    database_path: Path,
    raw_body: bytes,
    razorpay_event_id: str,
    correlation_id: str,
    received_at: datetime,
) -> IngestResult:
    """Persist one authenticated event and any case/job in one SQLite transaction."""
    if not razorpay_event_id.strip():
        raise IngestPayloadError("Razorpay event ID is required.")
    event = _parse_event(raw_body)
    received_at_utc = received_at.astimezone(timezone.utc)
    case = (
        _case_from_created_event(event, received_at_utc) if event.event == SUPPORTED_EVENT else None
    )
    case_id = case.id if case is not None else None
    body_sha256 = hashlib.sha256(raw_body).hexdigest()
    event_created_at = _utc_from_epoch(event.created_at)
    timestamp = received_at_utc.isoformat().replace("+00:00", "Z")

    initialize_database(database_path)
    with connect_database(database_path) as connection:
        try:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                """
                INSERT INTO ingest_events (
                    razorpay_event_id, event_name, account_id, body_sha256,
                    received_at, event_created_at, case_id, correlation_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    razorpay_event_id,
                    event.event,
                    event.account_id,
                    body_sha256,
                    timestamp,
                    (
                        event_created_at.isoformat().replace("+00:00", "Z")
                        if event_created_at is not None
                        else None
                    ),
                    case_id,
                    correlation_id,
                ),
            )

            processing_scheduled = False
            if case is not None:
                existing_case = connection.execute(
                    "SELECT id FROM dispute_cases WHERE razorpay_dispute_id = ?",
                    (case.razorpay_dispute_id,),
                ).fetchone()
                if existing_case is None:
                    insert_dispute_case(connection, case)
                else:
                    case_id = str(existing_case["id"])

                cursor = connection.execute(
                    """
                    INSERT OR IGNORE INTO jobs (
                        id, case_id, job_type, status, available_at, created_at, updated_at
                    ) VALUES (?, ?, ?, 'PENDING', ?, ?, ?)
                    """,
                    (
                        f"job_ingest_{case_id}",
                        case_id,
                        "PROCESS_CASE",
                        timestamp,
                        timestamp,
                        timestamp,
                    ),
                )
                processing_scheduled = cursor.rowcount == 1
            connection.commit()
        except sqlite3.IntegrityError:
            connection.rollback()
            existing = connection.execute(
                "SELECT case_id FROM ingest_events WHERE razorpay_event_id = ?",
                (razorpay_event_id,),
            ).fetchone()
            if existing is None:
                raise
            return IngestResult(
                event_id=razorpay_event_id,
                case_id=existing["case_id"],
                correlation_id=correlation_id,
                duplicate=True,
                processing_scheduled=False,
            )

    return IngestResult(
        event_id=razorpay_event_id,
        case_id=case_id,
        correlation_id=correlation_id,
        duplicate=False,
        processing_scheduled=processing_scheduled,
    )
