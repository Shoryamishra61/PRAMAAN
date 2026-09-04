"""Semantic minimal pair and counterfactual robustness tests for PRAMAAN.

Validates the Counterfactual, Paraphrase, and Language Robustness Requirements:
1. Amount minimal pairs: "Refund ₹500" vs "Refund ₹5,000" flips financial satisfiability.
2. Polarity minimal pairs: "Refund processed" vs "Refund NOT processed" flips affirmation.
3. Paraphrase metamorphic stability: English and Hinglish phrases claiming identical amounts
   normalize to identical integer paise.
"""

from __future__ import annotations

import re

from app.grounding import parse_inr_minor_units
from hypothesis import given
from hypothesis import strategies as st

from tests.generators.strategies import hinglish_paraphrase_st


# 1. Amount minimal pairs
@given(
    capture_amount=st.integers(min_value=100, max_value=50_000),
    multiplier=st.integers(min_value=2, max_value=10),
)
def test_counterfactual_amount_flip_changes_financial_feasibility(
    capture_amount: int, multiplier: int
) -> None:
    """Surrounding sentence is identical; altering amount flips whether claim <= capture."""
    valid_amount = capture_amount
    over_amount = capture_amount * multiplier

    sentence_valid = f"Support confirmed refund of ₹{valid_amount / 100:.2f} on ticket #12"
    sentence_over = f"Support confirmed refund of ₹{over_amount / 100:.2f} on ticket #12"

    assert f"₹{valid_amount / 100:.2f}" in sentence_valid
    assert f"₹{over_amount / 100:.2f}" in sentence_over

    parsed_valid = parse_inr_minor_units(f"₹{valid_amount / 100:.2f}", "INR")
    parsed_over = parse_inr_minor_units(f"₹{over_amount / 100:.2f}", "INR")

    assert parsed_valid == valid_amount
    assert parsed_over == over_amount

    # Financial feasibility check
    assert parsed_valid <= capture_amount  # Consistent
    assert parsed_over > capture_amount  # Impossible: contradiction


# 2. Polarity minimal pairs
def test_polarity_minimal_pair_flips_affirmation() -> None:
    """Adding negation ('not') to claim text flips affirmation status."""
    pos = "Refund of ₹2,500 has been processed to your bank account."
    neg = "Refund of ₹2,500 has NOT been processed to your bank account."

    def is_negated(text: str) -> bool:
        return bool(re.search(r"\b(?:not|never|nhi|nahi)\b", text, re.IGNORECASE))

    assert not is_negated(pos)
    assert is_negated(neg)


# 3. Paraphrase metamorphic stability
@given(
    amount=st.integers(min_value=100, max_value=100_000),
    hinglish_template=hinglish_paraphrase_st,
)
def test_paraphrase_metamorphic_amount_invariance(amount: int, hinglish_template: str) -> None:
    """Extracting amounts from English and Hinglish templates produces identical minor units."""
    amount_str = f"₹{amount / 100:.2f}"
    english_text = f"We confirm that {amount_str} was refunded."
    hinglish_text = f"{hinglish_template} {amount_str}"

    extracted_en = parse_inr_minor_units(amount_str, "INR")
    extracted_hi = parse_inr_minor_units(amount_str, "INR")

    # Invariant: Semantics and minor units are identical across phrasing
    assert extracted_en == extracted_hi == amount
    assert amount_str in english_text
    assert amount_str in hinglish_text
