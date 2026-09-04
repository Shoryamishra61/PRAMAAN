"""Deterministic regex/keyword baseline for diagnostic evaluation."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

from app.extraction import (
    ClaimModality,
    ClaimType,
    ExtractedClaim,
    ExtractionRequest,
    ExtractionResult,
)

BASELINE_ID = "regex-baseline-v1"
SENTENCE_PATTERN = re.compile(r"[^\n.!?]+[.!?]?", re.UNICODE)
INR_VALUE_PATTERN = re.compile(
    r"(?:₹\s*(?:\d{1,3}(?:,\d{2})*,\d{3}|\d{1,3}(?:,\d{3})+|\d+)(?:\.\d{1,2})?"
    r"|INR\s+(?:\d{1,3}(?:,\d{2})*,\d{3}|\d{1,3}(?:,\d{3})+|\d+)(?:\.\d{1,2})?)",
    re.IGNORECASE,
)
REFERENCE_PATTERN = re.compile(
    r"\b(?:reference|ref)\b(?:\s*[:#-]\s*|\s+)([A-Za-z0-9][A-Za-z0-9_-]{1,127})\b",
    re.IGNORECASE,
)
RFC3339_PATTERN = re.compile(r"\b\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2})?(?:Z|[+-]\d{2}:\d{2})\b")


@dataclass(frozen=True)
class PatternRule:
    claim_type: ClaimType
    modality: ClaimModality
    pattern: re.Pattern[str]


RULES = (
    PatternRule(
        ClaimType.REFUND_CLAIMED_PROCESSED,
        ClaimModality.ASSERTION,
        re.compile(
            r"\b(?:refund|credit)\s+(?:was|has been|is)\s+(?:successfully\s+)?processed\b"
            r"|\b(?:we|merchant)\s+(?:have\s+)?processed\b[^.!?\n]*\b(?:refund|credit)\b",
            re.IGNORECASE,
        ),
    ),
    PatternRule(
        ClaimType.REFUND_APPROVED,
        ClaimModality.APPROVAL,
        re.compile(
            r"\b(?:refund|credit)\s+(?:was|has been|is)\s+approved\b"
            r"|\b(?:we|merchant)\s+approved\b[^.!?\n]*\b(?:refund|credit)\b",
            re.IGNORECASE,
        ),
    ),
    PatternRule(
        ClaimType.REFUND_PROMISED,
        ClaimModality.PROMISE,
        re.compile(
            r"\bwe\s+(?:will|shall)\s+(?:issue|process|send|provide)?\s*"
            r"(?:a\s+)?(?:refund|credit)\b"
            r"|\b(?:refund|credit)\s+will\s+be\s+(?:issued|processed|sent|provided)\b",
            re.IGNORECASE,
        ),
    ),
    PatternRule(
        ClaimType.REFUND_DENIED,
        ClaimModality.DENIAL,
        re.compile(
            r"\b(?:refund|credit)\s+(?:was|is|has been)\s+(?:denied|declined|rejected)\b",
            re.IGNORECASE,
        ),
    ),
    PatternRule(
        ClaimType.REFUND_REQUESTED,
        ClaimModality.ASSERTION,
        re.compile(
            r"\b(?:refund|credit)\s+request\s+(?:was\s+)?received\b"
            r"|\b(?:requested|requesting)\s+(?:a\s+)?(?:refund|credit)\b",
            re.IGNORECASE,
        ),
    ),
    PatternRule(
        ClaimType.RETURN_NOT_RECEIVED_CLAIM,
        ClaimModality.DENIAL,
        re.compile(r"\b(?:have|has|had)\s+not\s+received\b[^.!?\n]*\breturn\b", re.IGNORECASE),
    ),
    PatternRule(
        ClaimType.RETURN_CLAIMED,
        ClaimModality.ASSERTION,
        re.compile(r"\b(?:received|accepted)\b[^.!?\n]*\breturn\b", re.IGNORECASE),
    ),
    PatternRule(
        ClaimType.POLICY_CONDITION_REFERENCE,
        ClaimModality.CONDITIONAL,
        re.compile(r"\b(?:under|according to|our)\b[^.!?\n]*\brefund policy\b", re.IGNORECASE),
    ),
)

NEGATED_PROCESSED_PATTERN = re.compile(
    r"\b(?:not|never)\s+(?:been\s+)?processed\b"
    r"|\b(?:have|has|had)\s+not\s+processed\b"
    r"|\bshould\s+have\s+been\s+processed\b",
    re.IGNORECASE,
)
INSTRUCTION_PATTERN = re.compile(
    r"\b(?:ignore|disregard)\b[^.!?\n]*\b(?:instruction|schema|say|output|tool)\b",
    re.IGNORECASE,
)
TIMING_PATTERN = re.compile(
    r"\b(?:within|in)\s+(\d{1,3})\s+(business\s+)?(?:day|days|hour|hours)\b",
    re.IGNORECASE,
)


def _sentences(text: str) -> tuple[str, ...]:
    return tuple(
        sentence
        for match in SENTENCE_PATTERN.finditer(text)
        if (sentence := match.group(0).strip())
    )


def _claim_id(document_id: str, claim_type: ClaimType, quote: str, ordinal: int) -> str:
    digest = hashlib.sha256(
        f"{document_id}\x00{claim_type.value}\x00{quote}\x00{ordinal}".encode()
    ).hexdigest()[:16]
    return f"claim_{digest}"


def _normalize_amount_literal(raw_amount: str) -> str:
    compact = raw_amount.strip()
    if compact.startswith("₹"):
        return "₹" + compact[1:].strip()
    if compact.upper().startswith("INR"):
        return "INR " + compact[3:].strip()
    return compact


def _value(sentence: str) -> tuple[object, str | None, str | None]:
    amount_match = INR_VALUE_PATTERN.search(sentence)
    reference_match = REFERENCE_PATTERN.search(sentence)
    date_match = RFC3339_PATTERN.search(sentence)
    amount = _normalize_amount_literal(amount_match.group(0)) if amount_match else None
    reference = reference_match.group(1) if reference_match else None
    if reference is not None:
        return (
            {"raw_value": amount or "stated", "refund_reference": reference},
            "INR" if amount is not None else None,
            date_match.group(0) if date_match else None,
        )
    return (
        amount or "stated",
        "INR" if amount is not None else None,
        date_match.group(0) if date_match else None,
    )


class RegexBaselineExtractor:
    """Strong deterministic baseline; not represented as a model or AI system."""

    async def extract(self, request: ExtractionRequest) -> ExtractionResult:
        allowed = set(request.allowed_claim_types)
        claims: list[ExtractedClaim] = []
        ordinal = 0
        for sentence in _sentences(request.canonical_text):
            if INSTRUCTION_PATTERN.search(sentence):
                continue
            sentence_has_refund = bool(re.search(r"\b(?:refund|credit)\b", sentence, re.I))
            for rule in RULES:
                if rule.claim_type not in allowed or not rule.pattern.search(sentence):
                    continue
                if (
                    rule.claim_type is ClaimType.REFUND_CLAIMED_PROCESSED
                    and NEGATED_PROCESSED_PATTERN.search(sentence)
                ):
                    continue
                value, currency, raw_date_text = _value(sentence)
                claims.append(
                    ExtractedClaim(
                        claim_id=_claim_id(request.document_id, rule.claim_type, sentence, ordinal),
                        document_id=request.document_id,
                        claim_type=rule.claim_type,
                        quote=sentence,
                        value=value,
                        currency=currency,
                        raw_date_text=raw_date_text,
                        modality=rule.modality,
                    )
                )
                ordinal += 1

            amount_match = INR_VALUE_PATTERN.search(sentence)
            if (
                sentence_has_refund
                and amount_match is not None
                and ClaimType.REFUND_AMOUNT in allowed
            ):
                raw_amount = _normalize_amount_literal(amount_match.group(0))
                claims.append(
                    ExtractedClaim(
                        claim_id=_claim_id(
                            request.document_id,
                            ClaimType.REFUND_AMOUNT,
                            sentence,
                            ordinal,
                        ),
                        document_id=request.document_id,
                        claim_type=ClaimType.REFUND_AMOUNT,
                        quote=sentence,
                        value=raw_amount,
                        currency="INR",
                        modality=ClaimModality.ASSERTION,
                    )
                )
                ordinal += 1

            timing_match = TIMING_PATTERN.search(sentence)
            if (
                sentence_has_refund
                and timing_match is not None
                and ClaimType.REFUND_TIMING_COMMITMENT in allowed
            ):
                claims.append(
                    ExtractedClaim(
                        claim_id=_claim_id(
                            request.document_id,
                            ClaimType.REFUND_TIMING_COMMITMENT,
                            sentence,
                            ordinal,
                        ),
                        document_id=request.document_id,
                        claim_type=ClaimType.REFUND_TIMING_COMMITMENT,
                        quote=sentence,
                        value=timing_match.group(0),
                        modality=ClaimModality.PROMISE,
                    )
                )
                ordinal += 1

        return ExtractionResult(
            extractor_id=BASELINE_ID,
            model_id=None,
            claims=tuple(claims),
        )
