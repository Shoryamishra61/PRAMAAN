from __future__ import annotations

from datetime import datetime, timezone

import pytest
from app.extraction import ExtractedClaim
from app.grounding import (
    ValueNormalizationStatus,
    ground_and_normalize_claim,
    normalize_refund_reference,
    normalize_rfc3339,
    parse_inr_minor_units,
    resolve_exact_quote,
)
from app.verification import GroundingStatus
from hypothesis import given
from hypothesis import strategies as st


def extracted_claim(**overrides: object) -> ExtractedClaim:
    values: dict[str, object] = {
        "claim_id": "claim_1",
        "document_id": "doc_1",
        "claim_type": "refund_amount",
        "quote": "Your ₹2,500 refund was processed.",
        "value": "₹2,500",
        "currency": "INR",
        "modality": "assertion",
    }
    values.update(overrides)
    return ExtractedClaim.model_validate(values)


def test_unique_exact_quote_resolves_exclusive_character_span() -> None:
    text = "Context. Your ₹2,500 refund was processed. End."
    quote = "Your ₹2,500 refund was processed."

    grounding = resolve_exact_quote(text, quote)

    assert grounding.status is GroundingStatus.GROUNDED
    assert grounding.span_start is not None and grounding.span_end is not None
    assert text[grounding.span_start : grounding.span_end] == quote


def test_missing_or_whitespace_changed_quote_is_ungrounded() -> None:
    grounding = resolve_exact_quote(
        "Your ₹2,500 refund was processed.",
        "Your  ₹2,500 refund was processed.",
    )

    assert grounding.status is GroundingStatus.UNGROUNDED
    assert grounding.span_start is grounding.span_end is None


def test_repeated_exact_quote_is_ambiguous() -> None:
    quote = "Refund request received."

    grounding = resolve_exact_quote(f"{quote} Later: {quote}", quote)

    assert grounding.status is GroundingStatus.AMBIGUOUS
    assert grounding.span_start is grounding.span_end is None


@pytest.mark.parametrize(
    ("raw_value", "currency", "expected"),
    [
        ("₹2,500", None, 250_000),
        ("INR 2500.00", "INR", 250_000),
        ("₹2,50,000.25", "INR", 25_000_025),
        ("2500", "INR", 250_000),
        ("2500", None, None),
        ("USD 10.00", "USD", None),
        ("₹1.001", "INR", None),
        ("₹-1", "INR", None),
    ],
)
def test_money_normalization_is_inr_only_and_integer_minor_units(
    raw_value: str, currency: str | None, expected: int | None
) -> None:
    assert parse_inr_minor_units(raw_value, currency) == expected


@given(st.integers(min_value=0, max_value=10_000_000))
def test_integer_rupee_amount_round_trips_to_exact_paise(rupees: int) -> None:
    assert parse_inr_minor_units(f"INR {rupees}", "INR") == rupees * 100


def test_timestamp_requires_explicit_timezone_and_normalizes_utc() -> None:
    assert normalize_rfc3339("2026-08-10T15:30:00+05:30") == datetime(
        2026, 8, 10, 10, tzinfo=timezone.utc
    )
    assert normalize_rfc3339("2026-08-10T15:30:00") is None
    assert normalize_rfc3339("Aug 10") is None


@pytest.mark.parametrize(
    ("value", "expected"),
    [("RF-101", "RF-101"), (" rfnd_123 ", "rfnd_123"), ("RF 101", None), (None, None)],
)
def test_reference_normalization_never_extracts_from_prose(
    value: str | None, expected: str | None
) -> None:
    assert normalize_refund_reference(value) == expected


def test_grounded_claim_maps_to_verifier_without_model_offsets() -> None:
    quote = "Your ₹2,500 refund was processed."
    grounded = ground_and_normalize_claim(extracted_claim(), f"Prefix. {quote}")
    resolved = grounded.to_resolved_claim()

    assert grounded.grounding_status is GroundingStatus.GROUNDED
    assert grounded.amount_minor == 250_000
    assert grounded.normalization_status is ValueNormalizationStatus.RESOLVED
    assert resolved.amount_minor == 250_000
    assert resolved.source_quote == quote


def test_ambiguous_amount_or_date_is_explicitly_unresolved() -> None:
    grounded = ground_and_normalize_claim(
        extracted_claim(value="about 2500", raw_date_text="Aug 10"),
        "Your ₹2,500 refund was processed.",
    )

    assert grounded.normalization_status is ValueNormalizationStatus.UNRESOLVED
    assert grounded.normalization_errors == ("AMOUNT_UNRESOLVED", "DATE_UNRESOLVED")
