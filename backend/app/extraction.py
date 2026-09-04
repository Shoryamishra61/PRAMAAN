"""Strict provider-neutral semantic extraction boundary."""

from __future__ import annotations

from enum import Enum
from typing import Literal, Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field, JsonValue, model_validator

from app.profile import DEFAULT_PROFILE_ID

PROMPT_VERSION = "refund-claims-v1"
CLAIM_SCHEMA_VERSION = "grounded-claim-v1"


class ClaimType(str, Enum):
    REFUND_REQUESTED = "refund_requested"
    REFUND_PROMISED = "refund_promised"
    REFUND_APPROVED = "refund_approved"
    REFUND_CLAIMED_PROCESSED = "refund_claimed_processed"
    REFUND_DENIED = "refund_denied"
    REFUND_AMOUNT = "refund_amount"
    REFUND_TIMING_COMMITMENT = "refund_timing_commitment"
    RETURN_CLAIMED = "return_claimed"
    RETURN_NOT_RECEIVED_CLAIM = "return_not_received_claim"
    POLICY_CONDITION_REFERENCE = "policy_condition_reference"


class ClaimModality(str, Enum):
    ASSERTION = "assertion"
    PROMISE = "promise"
    APPROVAL = "approval"
    DENIAL = "denial"
    CONDITIONAL = "conditional"


class ExtractionSchemaError(ValueError):
    code = "JOB_PERMANENT_SCHEMA_ERROR"


class ExtractionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_id: str = Field(min_length=1)
    document_type: Literal["text/plain", "application/json"]
    canonical_text: str = Field(min_length=1)
    allowed_claim_types: tuple[ClaimType, ...]
    reason_profile_id: Literal["refund_not_processed_v1"] = "refund_not_processed_v1"

    @model_validator(mode="after")
    def require_unique_allowlist(self) -> ExtractionRequest:
        if not self.allowed_claim_types:
            raise ValueError("allowed_claim_types must not be empty")
        if len(self.allowed_claim_types) != len(set(self.allowed_claim_types)):
            raise ValueError("allowed_claim_types must be unique")
        return self


class ExtractedClaim(BaseModel):
    """Matches contracts/grounded-claim.schema.json exactly."""

    model_config = ConfigDict(extra="forbid")

    claim_id: str = Field(min_length=1)
    document_id: str = Field(min_length=1)
    claim_type: ClaimType
    quote: str = Field(min_length=1)
    value: JsonValue
    currency: str | None = Field(default=None, pattern=r"^[A-Z]{3}$")
    raw_date_text: str | None = None
    modality: ClaimModality | None = None
    subject_ref: str | None = None


class ExtractionResult(BaseModel):
    """Backend-owned run metadata plus untrusted schema-validated claims."""

    model_config = ConfigDict(extra="forbid")

    extractor_id: str = Field(min_length=1)
    model_id: str | None = None
    prompt_version: str = PROMPT_VERSION
    schema_version: str = CLAIM_SCHEMA_VERSION
    claims: tuple[ExtractedClaim, ...]


@runtime_checkable
class SemanticExtractor(Protocol):
    """One bounded operation: text to typed claims, with no action authority."""

    async def extract(self, request: ExtractionRequest) -> ExtractionResult: ...


def validate_extraction_result(
    request: ExtractionRequest, result: ExtractionResult
) -> ExtractionResult:
    """Bind untrusted output to the exact document and request allowlist."""
    allowed = set(request.allowed_claim_types)
    for claim in result.claims:
        if claim.document_id != request.document_id:
            raise ExtractionSchemaError("Claim document_id does not match request.")
        if claim.claim_type not in allowed:
            raise ExtractionSchemaError("Claim type is outside the request allowlist.")
    return result


def default_claim_allowlist() -> tuple[ClaimType, ...]:
    """Return the canonical profile allowlist without consulting raw reason codes."""
    assert DEFAULT_PROFILE_ID == "refund_not_processed_v1"
    return tuple(ClaimType)
