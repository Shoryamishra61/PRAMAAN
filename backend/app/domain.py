"""Strict local domain types at deterministic trust boundaries."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProcessingStatus(str, Enum):
    RECEIVED = "RECEIVED"
    VALIDATED = "VALIDATED"
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    READY = "READY"
    RETRYABLE_ERROR = "RETRYABLE_ERROR"
    FAILED = "FAILED"


class WorkflowStatus(str, Enum):
    REVIEW_PENDING = "REVIEW_PENDING"
    READY_WITH_OVERRIDE = "READY_WITH_OVERRIDE"
    READY_FOR_CONTEST = "READY_FOR_CONTEST"


MoneyMinor = Annotated[int, Field(strict=True, ge=0)]


def require_utc(value: datetime) -> datetime:
    """Reject naive timestamps and normalize aware timestamps to UTC."""
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timestamp must include a timezone")
    return value.astimezone(timezone.utc)


class DisputeCaseCreate(BaseModel):
    """Normalized dispute fields safe to persist in the local case aggregate."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    razorpay_dispute_id: str = Field(min_length=1)
    payment_id: str = Field(min_length=1)
    amount_minor: MoneyMinor
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    raw_reason_code: str | None = None
    reason_description: str | None = None
    reason_profile: str = Field(default="refund_not_processed_v1")
    respond_by: datetime | None = None
    razorpay_status: str | None = None
    razorpay_phase: str | None = None
    processing_status: ProcessingStatus = ProcessingStatus.RECEIVED
    workflow_status: WorkflowStatus = WorkflowStatus.REVIEW_PENDING
    created_at: datetime
    updated_at: datetime

    @field_validator("currency", mode="before")
    @classmethod
    def normalize_currency(cls, value: object) -> object:
        return value.upper() if isinstance(value, str) else value

    @field_validator("respond_by", "created_at", "updated_at")
    @classmethod
    def normalize_timestamp(cls, value: datetime | None) -> datetime | None:
        return require_utc(value) if value is not None else None


def to_storage_timestamp(value: datetime | None) -> str | None:
    """Serialize an already validated timestamp in a stable UTC form."""
    if value is None:
        return None
    return require_utc(value).isoformat().replace("+00:00", "Z")
