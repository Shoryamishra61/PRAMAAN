"""Exact quote grounding and deterministic semantic value normalization."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from enum import Enum

from pydantic import BaseModel, ConfigDict

from app.extraction import ClaimType, ExtractedClaim
from app.verification import GroundingStatus, ResolvedClaim

INR_AMOUNT_PATTERN = re.compile(
    r"^\s*(?:(?P<symbol>₹)|(?P<code>INR)\s*)?"
    r"(?P<amount>(?:\d{1,3}(?:,\d{2})*,\d{3}|\d{1,3}(?:,\d{3})+|\d+)(?:\.\d{1,2})?)\s*$",
    re.IGNORECASE,
)
REFERENCE_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$")


class ValueNormalizationStatus(str, Enum):
    RESOLVED = "RESOLVED"
    UNRESOLVED = "UNRESOLVED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class QuoteGrounding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: GroundingStatus
    span_start: int | None = None
    span_end: int | None = None


class GroundedNormalizedClaim(BaseModel):
    model_config = ConfigDict(extra="forbid")

    claim_id: str
    document_id: str
    claim_type: ClaimType
    source_quote: str
    span_start: int | None
    span_end: int | None
    grounding_status: GroundingStatus
    raw_value: str | None
    amount_minor: int | None
    currency: str | None
    normalized_timestamp: datetime | None
    refund_reference: str | None
    normalization_status: ValueNormalizationStatus
    normalization_errors: tuple[str, ...]

    def to_resolved_claim(self) -> ResolvedClaim:
        """Drop non-policy metadata while preserving the local grounding decision."""
        return ResolvedClaim(
            id=self.claim_id,
            document_id=self.document_id,
            claim_type=self.claim_type.value,
            source_quote=self.source_quote,
            grounding_status=self.grounding_status,
            raw_value=self.raw_value,
            amount_minor=self.amount_minor,
            currency=self.currency,
            refund_reference=self.refund_reference,
        )


def resolve_exact_quote(canonical_text: str, source_quote: str) -> QuoteGrounding:
    """Return exclusive character offsets only for one exact substring match."""
    first = canonical_text.find(source_quote)
    if first < 0:
        return QuoteGrounding(status=GroundingStatus.UNGROUNDED)
    second = canonical_text.find(source_quote, first + 1)
    if second >= 0:
        return QuoteGrounding(status=GroundingStatus.AMBIGUOUS)
    return QuoteGrounding(
        status=GroundingStatus.GROUNDED,
        span_start=first,
        span_end=first + len(source_quote),
    )


def parse_inr_minor_units(raw_value: str, currency: str | None) -> int | None:
    """Parse an explicitly INR-denominated amount into paise using Decimal."""
    match = INR_AMOUNT_PATTERN.fullmatch(raw_value)
    if match is None:
        return None
    explicit_inr = match.group("symbol") is not None or match.group("code") is not None
    normalized_currency = currency.upper() if currency is not None else None
    if normalized_currency not in {None, "INR"}:
        return None
    if normalized_currency is None and not explicit_inr:
        return None
    try:
        amount = Decimal(match.group("amount").replace(",", ""))
    except InvalidOperation:
        return None
    minor = amount * 100
    if minor != minor.to_integral_value() or amount < 0:
        return None
    return int(minor)


def normalize_rfc3339(raw_date_text: str) -> datetime | None:
    """Normalize only timestamps with an explicit timezone; do not guess dates."""
    candidate = raw_date_text.strip()
    if candidate.endswith("Z"):
        candidate = candidate[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError:
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return None
    return parsed.astimezone(timezone.utc)


def normalize_refund_reference(raw_reference: str | None) -> str | None:
    """Accept a bounded identifier token without guessing through prose."""
    if raw_reference is None:
        return None
    candidate = raw_reference.strip()
    return candidate if REFERENCE_PATTERN.fullmatch(candidate) else None


def _raw_value(claim: ExtractedClaim) -> str | None:
    if isinstance(claim.value, (str, int, float, bool)):
        return str(claim.value)
    if isinstance(claim.value, dict):
        candidate = claim.value.get("raw_value", claim.value.get("raw"))
        return str(candidate) if isinstance(candidate, (str, int, float, bool)) else None
    return None


def _reference_value(claim: ExtractedClaim) -> str | None:
    if not isinstance(claim.value, dict):
        return None
    candidate = claim.value.get("refund_reference")
    return candidate if isinstance(candidate, str) else None


def ground_and_normalize_claim(
    claim: ExtractedClaim, canonical_text: str
) -> GroundedNormalizedClaim:
    """Ground a model claim locally and normalize only unambiguous typed values."""
    grounding = resolve_exact_quote(canonical_text, claim.quote)
    raw_value = _raw_value(claim)
    amount_minor: int | None = None
    normalized_timestamp: datetime | None = None
    errors: list[str] = []
    normalization_applicable = False

    if claim.claim_type is ClaimType.REFUND_AMOUNT:
        normalization_applicable = True
        if raw_value is not None:
            amount_minor = parse_inr_minor_units(raw_value, claim.currency)
        if amount_minor is None:
            errors.append("AMOUNT_UNRESOLVED")
    elif raw_value is not None and (
        raw_value.strip().startswith("₹") or raw_value.strip().upper().startswith("INR")
    ):
        normalization_applicable = True
        amount_minor = parse_inr_minor_units(raw_value, claim.currency)
        if amount_minor is None:
            errors.append("AMOUNT_UNRESOLVED")

    if claim.raw_date_text is not None:
        normalization_applicable = True
        normalized_timestamp = normalize_rfc3339(claim.raw_date_text)
        if normalized_timestamp is None:
            errors.append("DATE_UNRESOLVED")

    raw_reference = _reference_value(claim)
    refund_reference = normalize_refund_reference(raw_reference)
    if raw_reference is not None:
        normalization_applicable = True
        if refund_reference is None:
            errors.append("REFERENCE_UNRESOLVED")

    normalization_status = (
        ValueNormalizationStatus.UNRESOLVED
        if errors
        else (
            ValueNormalizationStatus.RESOLVED
            if normalization_applicable
            else ValueNormalizationStatus.NOT_APPLICABLE
        )
    )
    return GroundedNormalizedClaim(
        claim_id=claim.claim_id,
        document_id=claim.document_id,
        claim_type=claim.claim_type,
        source_quote=claim.quote,
        span_start=grounding.span_start,
        span_end=grounding.span_end,
        grounding_status=grounding.status,
        raw_value=raw_value,
        amount_minor=amount_minor,
        currency=claim.currency,
        normalized_timestamp=normalized_timestamp,
        refund_reference=refund_reference,
        normalization_status=normalization_status,
        normalization_errors=tuple(errors),
    )
