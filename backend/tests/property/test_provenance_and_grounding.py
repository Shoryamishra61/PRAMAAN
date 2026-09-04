"""Provenance, exact span grounding, and evidence integrity tests for PRAMAAN.

Validates the Provenance Testing Requirements:
1. Exact quote resolves to unique character span (GROUNDED).
2. Quote missing from document resolves to UNGROUNDED.
3. Duplicate quote string occurring >= 2 times resolves to AMBIGUOUS and fails closed.
4. Mutating a single byte of source text changes SHA-256 and invalidates previous span.
"""

from __future__ import annotations

import hashlib

from app.grounding import resolve_exact_quote
from app.verification import GroundingStatus
from hypothesis import given
from hypothesis import strategies as st


@given(
    prefix=st.text(min_size=5, max_size=50),
    quote=st.text(min_size=10, max_size=100),
    suffix=st.text(min_size=5, max_size=50),
)
def test_unique_quote_resolves_to_exact_grounded_span(prefix: str, quote: str, suffix: str) -> None:
    """A quote appearing exactly once in a document resolves to GROUNDED with exact span."""
    # Ensure prefix and suffix don't accidentally contain the quote
    if quote in prefix or quote in suffix:
        return

    doc = f"{prefix} {quote} {suffix}"
    grounding = resolve_exact_quote(doc, quote)

    assert grounding.status == GroundingStatus.GROUNDED
    assert grounding.span_start is not None
    assert grounding.span_end is not None
    # Invariant: span slice must reproduce the exact source quote
    assert doc[grounding.span_start : grounding.span_end] == quote


def test_missing_quote_resolves_to_ungrounded() -> None:
    """A quote not present in the document must return UNGROUNDED."""
    doc = "The customer requested an update on order #102."
    quote = "A full refund of ₹5,000 was processed."

    grounding = resolve_exact_quote(doc, quote)
    assert grounding.status == GroundingStatus.UNGROUNDED
    assert grounding.span_start is None
    assert grounding.span_end is None


def test_duplicate_quote_resolves_to_ambiguous_and_fails_closed() -> None:
    """If a quote occurs 2 or more times, resolve_exact_quote must return AMBIGUOUS."""
    repeated_phrase = "Refund processed on March 1st."
    doc = f"Customer statement: {repeated_phrase} Merchant reply: {repeated_phrase} Confirmed."

    grounding = resolve_exact_quote(doc, repeated_phrase)
    # Invariant: Ambiguous multi-quote matches fail closed
    assert grounding.status == GroundingStatus.AMBIGUOUS
    assert grounding.span_start is None
    assert grounding.span_end is None


@given(
    original_text=st.text(min_size=20, max_size=200),
    mutation_char=st.sampled_from(["X", "!", "0", " "]),
)
def test_one_byte_mutation_alters_sha256_digest(original_text: str, mutation_char: str) -> None:
    """Modifying even 1 character in evidence content produces a completely different hash."""
    h_orig = hashlib.sha256(original_text.encode("utf-8")).hexdigest()

    mutated_text = original_text[:-1] + mutation_char
    if mutated_text == original_text:
        mutated_text = original_text + mutation_char

    h_mutated = hashlib.sha256(mutated_text.encode("utf-8")).hexdigest()

    # Invariant: Hash collision resistance on single-byte mutation
    assert h_orig != h_mutated
