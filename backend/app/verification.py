"""Deterministic structured-state and grounded-claim integrity rules."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.domain import MoneyMinor, require_utc
from app.profile import DEFAULT_PROFILE_ID


class FindingEffect(str, Enum):
    REVIEW = "REVIEW"
    BLOCK = "BLOCK"


class RefundStatus(str, Enum):
    CREATED = "created"
    PENDING = "pending"
    PROCESSED = "processed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class GroundingStatus(str, Enum):
    GROUNDED = "GROUNDED"
    UNGROUNDED = "UNGROUNDED"
    AMBIGUOUS = "AMBIGUOUS"


ClaimType = Literal[
    "refund_requested",
    "refund_promised",
    "refund_approved",
    "refund_claimed_processed",
    "refund_denied",
    "refund_amount",
    "refund_timing_commitment",
    "return_claimed",
    "return_not_received_claim",
    "policy_condition_reference",
]


class RefundRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    payment_id: str = Field(min_length=1)
    amount_minor: MoneyMinor
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    local_status: RefundStatus
    created_at: datetime | None = None
    processed_at: datetime | None = None
    reference: str | None = None

    @field_validator("currency", mode="before")
    @classmethod
    def normalize_currency(cls, value: object) -> object:
        return value.upper() if isinstance(value, str) else value

    @field_validator("created_at", "processed_at")
    @classmethod
    def normalize_timestamp(cls, value: datetime | None) -> datetime | None:
        return require_utc(value) if value is not None else None


class ResolvedClaim(BaseModel):
    """Untrusted extraction after schema validation, with local grounding result."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    document_id: str = Field(min_length=1)
    claim_type: ClaimType
    source_quote: str = Field(min_length=1)
    grounding_status: GroundingStatus
    raw_value: str | None = None
    amount_minor: MoneyMinor | None = None
    currency: str | None = Field(default=None, pattern=r"^[A-Z]{3}$")
    refund_reference: str | None = None

    @field_validator("currency", mode="before")
    @classmethod
    def normalize_currency(cls, value: object) -> object:
        return value.upper() if isinstance(value, str) else value


class VerificationContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    case_id: str = Field(min_length=1)
    reason_profile: str = DEFAULT_PROFILE_ID
    payment_id: str = Field(min_length=1)
    captured_amount_minor: MoneyMinor
    payment_currency: str = Field(pattern=r"^[A-Z]{3}$")
    payment_snapshot_complete: bool
    refund_ledger_complete: bool
    communication_present: bool
    missing_recommended_evidence: tuple[str, ...] = ()
    refunds: tuple[RefundRecord, ...] = ()
    claims: tuple[ResolvedClaim, ...] = ()

    @field_validator("payment_currency", mode="before")
    @classmethod
    def normalize_currency(cls, value: object) -> object:
        return value.upper() if isinstance(value, str) else value


class Finding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    effect: FindingEffect
    summary: str
    evidence_refs: tuple[str, ...]


class VerificationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    findings: tuple[Finding, ...]


def _finding(code: str, effect: FindingEffect, summary: str, *evidence_refs: str) -> Finding:
    return Finding(code=code, effect=effect, summary=summary, evidence_refs=evidence_refs)


def _claim_ref(claim: ResolvedClaim) -> str:
    return f"claim:{claim.id}"


def _refund_ref(refund: RefundRecord) -> str:
    return f"refund:{refund.id}"


def _same_claimed_value(claim: ResolvedClaim, refund: RefundRecord) -> bool:
    if claim.refund_reference is not None and claim.refund_reference != refund.reference:
        return False
    if claim.amount_minor is not None and claim.amount_minor != refund.amount_minor:
        return False
    return claim.currency is None or claim.currency == refund.currency


def verify_integrity(context: VerificationContext) -> VerificationResult:
    """Apply objective v1 rules; technical uncertainty only emits REVIEW."""
    findings: list[Finding] = []

    if context.reason_profile != DEFAULT_PROFILE_ID:
        return VerificationResult(
            findings=(
                _finding(
                    "F_SOURCE_UNSUPPORTED",
                    FindingEffect.REVIEW,
                    "The case is outside the refund_not_processed_v1 profile.",
                    f"case:{context.case_id}",
                ),
            )
        )

    if not context.communication_present:
        findings.append(
            _finding(
                "F_EVIDENCE_RECOMMENDED_MISSING",
                FindingEffect.REVIEW,
                "Customer refund communication is absent.",
                f"case:{context.case_id}",
            )
        )

    if context.missing_recommended_evidence:
        findings.append(
            _finding(
                "F_EVIDENCE_RECOMMENDED_MISSING",
                FindingEffect.REVIEW,
                "Suggested evidence is missing: " + ", ".join(context.missing_recommended_evidence),
                f"case:{context.case_id}",
            )
        )

    trusted_state_complete = context.payment_snapshot_complete and context.refund_ledger_complete
    if not trusted_state_complete:
        findings.append(
            _finding(
                "F_STRUCTURED_STATE_INCOMPLETE",
                FindingEffect.REVIEW,
                "Trusted payment or refund state is incomplete.",
                f"payment:{context.payment_id}",
            )
        )

    refund_ids = [refund.id for refund in context.refunds]
    structured_state_valid = len(refund_ids) == len(set(refund_ids))
    if not structured_state_valid:
        findings.append(
            _finding(
                "F_STRUCTURED_STATE_INCOMPLETE",
                FindingEffect.REVIEW,
                "Duplicate refund identifiers make structured state invalid.",
                f"payment:{context.payment_id}",
            )
        )

    if any(refund.amount_minor > context.captured_amount_minor for refund in context.refunds):
        structured_state_valid = False
        findings.append(
            _finding(
                "F_STRUCTURED_STATE_INCOMPLETE",
                FindingEffect.REVIEW,
                "A refund amount exceeds the captured payment amount.",
                f"payment:{context.payment_id}",
            )
        )

    processed_total = sum(
        refund.amount_minor
        for refund in context.refunds
        if refund.local_status is RefundStatus.PROCESSED
    )
    if processed_total > context.captured_amount_minor:
        structured_state_valid = False
        findings.append(
            _finding(
                "F_STRUCTURED_STATE_INCOMPLETE",
                FindingEffect.REVIEW,
                "Processed refund total exceeds the captured payment amount.",
                f"payment:{context.payment_id}",
            )
        )

    for claim in context.claims:
        if claim.grounding_status is not GroundingStatus.GROUNDED:
            findings.append(
                _finding(
                    "F_SOURCE_UNGROUNDED",
                    FindingEffect.REVIEW,
                    "A decision-relevant semantic claim is not uniquely grounded.",
                    _claim_ref(claim),
                    f"document:{claim.document_id}",
                )
            )
        elif claim.claim_type == "policy_condition_reference":
            findings.append(
                _finding(
                    "F_SOURCE_UNSUPPORTED",
                    FindingEffect.REVIEW,
                    "Policy prose requires human interpretation in v1.",
                    _claim_ref(claim),
                )
            )

    if not (trusted_state_complete and structured_state_valid):
        return VerificationResult(findings=tuple(findings))

    pending = [
        refund
        for refund in context.refunds
        if refund.local_status in {RefundStatus.CREATED, RefundStatus.PENDING}
    ]
    if pending:
        findings.append(
            _finding(
                "F_STRUCTURED_STATE_INCOMPLETE",
                FindingEffect.REVIEW,
                "A matching refund is not yet in a final state.",
                *(_refund_ref(refund) for refund in pending),
            )
        )

    final_refunds = [
        refund
        for refund in context.refunds
        if refund.local_status
        in {RefundStatus.PROCESSED, RefundStatus.FAILED, RefundStatus.CANCELLED}
    ]
    processed = [
        refund for refund in final_refunds if refund.local_status is RefundStatus.PROCESSED
    ]

    for refund in final_refunds:
        if refund.payment_id != context.payment_id:
            findings.append(
                _finding(
                    "F_REFUND_REFERENCE_PAYMENT_MISMATCH",
                    FindingEffect.BLOCK,
                    "Final refund evidence references a different payment.",
                    _refund_ref(refund),
                    f"payment:{context.payment_id}",
                )
            )
        elif refund.currency != context.payment_currency:
            findings.append(
                _finding(
                    "F_REFUND_CURRENCY_MISMATCH",
                    FindingEffect.BLOCK,
                    "Final refund currency differs from the disputed payment currency.",
                    _refund_ref(refund),
                    f"payment:{context.payment_id}",
                )
            )

    for claim in context.claims:
        if claim.grounding_status is not GroundingStatus.GROUNDED:
            continue
        if claim.claim_type == "refund_promised" and not processed:
            findings.append(
                _finding(
                    "F_STRUCTURED_STATE_INCOMPLETE",
                    FindingEffect.REVIEW,
                    "A future refund promise cannot be treated as already due "
                    "without resolved timing.",
                    _claim_ref(claim),
                )
            )
            continue
        if claim.claim_type == "return_not_received_claim":
            findings.append(
                _finding(
                    "F_SOURCE_UNSUPPORTED",
                    FindingEffect.REVIEW,
                    "A customer non-receipt assertion requires contextual review.",
                    _claim_ref(claim),
                )
            )
            continue
        if claim.claim_type not in {"refund_claimed_processed", "refund_approved"}:
            continue

        same_payment = [
            refund for refund in final_refunds if refund.payment_id == context.payment_id
        ]
        same_reference = [
            refund
            for refund in same_payment
            if claim.refund_reference is None or refund.reference == claim.refund_reference
        ]

        pending_matches = [
            refund
            for refund in pending
            if refund.payment_id == context.payment_id and _same_claimed_value(claim, refund)
        ]
        if pending_matches:
            continue

        if claim.currency is not None:
            currency_mismatches = [
                refund
                for refund in same_reference
                if refund.local_status is RefundStatus.PROCESSED
                and refund.currency != claim.currency
            ]
            if currency_mismatches:
                findings.append(
                    _finding(
                        "F_REFUND_CURRENCY_MISMATCH",
                        FindingEffect.BLOCK,
                        "Grounded refund claim currency differs from final refund evidence.",
                        _claim_ref(claim),
                        *(_refund_ref(refund) for refund in currency_mismatches),
                    )
                )
                continue

        terminal_failures = [
            refund
            for refund in same_reference
            if refund.local_status in {RefundStatus.FAILED, RefundStatus.CANCELLED}
            and (claim.amount_minor is None or claim.amount_minor == refund.amount_minor)
        ]
        if claim.claim_type == "refund_claimed_processed" and terminal_failures:
            findings.append(
                _finding(
                    "F_REFUND_FINAL_STATUS_CONFLICT",
                    FindingEffect.BLOCK,
                    "Grounded communication says processed, but matching refund state "
                    "is final and not processed.",
                    _claim_ref(claim),
                    *(_refund_ref(refund) for refund in terminal_failures),
                )
            )
            continue

        processed_matches = [refund for refund in processed if _same_claimed_value(claim, refund)]
        if processed_matches:
            continue

        if (
            claim.amount_minor == context.captured_amount_minor
            and claim.refund_reference is None
            and processed
        ):
            comparable = [
                refund
                for refund in processed
                if refund.payment_id == context.payment_id
                and (claim.currency is None or refund.currency == claim.currency)
            ]
            processed_total = sum(refund.amount_minor for refund in comparable)
            if processed_total == claim.amount_minor:
                continue
            if processed_total != claim.amount_minor:
                findings.append(
                    _finding(
                        "F_REFUND_AMOUNT_MISMATCH",
                        FindingEffect.BLOCK,
                        "Grounded full-refund amount differs from final processed refund total.",
                        _claim_ref(claim),
                        *(_refund_ref(refund) for refund in comparable),
                    )
                )
                continue

        if claim.claim_type == "refund_claimed_processed":
            findings.append(
                _finding(
                    "F_REFUND_CLAIM_NO_LEDGER_MATCH",
                    FindingEffect.BLOCK,
                    "Grounded communication says a refund was processed, but the complete "
                    "ledger has no match.",
                    _claim_ref(claim),
                    f"payment:{context.payment_id}",
                )
            )

    return VerificationResult(findings=tuple(findings))
