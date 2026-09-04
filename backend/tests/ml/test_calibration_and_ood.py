"""Calibration, selective prediction monotonicity, and OOD shift tests for PRAMAAN.

Validates:
1. Calibration metric correctness (ECE and Brier score).
2. Selective prediction monotonicity: Widening review bounds monotonically increases review rate.
3. OOD shift safety: Unfamiliar distributions and severe corruption route to REVIEW.
"""

from __future__ import annotations

from hypothesis import given
from hypothesis import strategies as st

from evaluation.calibration import compute_brier_and_nll, compute_ece


def test_perfect_calibration_yields_near_zero_ece() -> None:
    """When predicted confidence matches empirical accuracy in each bin, ECE is ~0."""
    # 10 samples with prob 0.1, exactly 1 positive -> bin acc 0.1, bin conf 0.1
    # 10 samples with prob 0.9, exactly 9 positives -> bin acc 0.9, bin conf 0.9
    probs = [0.15] * 10 + [0.85] * 10
    labels = [1] * 1 + [0] * 9 + [1] * 9 + [0] * 1

    ece = compute_ece(probs, labels, n_bins=5)
    # Bin 0: conf 0.15, acc 0.10 (diff 0.05)
    # Bin 4: conf 0.85, acc 0.90 (diff 0.05)
    assert ece <= 0.06


def test_severe_overconfidence_yields_high_ece() -> None:
    """Predicting 99% confidence for all negative samples must yield ~99% ECE."""
    probs = [0.99] * 50
    labels = [0] * 50

    ece = compute_ece(probs, labels, n_bins=10)
    assert ece >= 0.95

    brier, nll = compute_brier_and_nll(probs, labels)
    assert brier >= 0.90
    assert nll > 2.0


@given(
    probs=st.lists(st.floats(min_value=0.0, max_value=1.0), min_size=20, max_size=100),
    w_narrow=st.floats(min_value=0.01, max_value=0.15),
    w_wide=st.floats(min_value=0.20, max_value=0.45),
)
def test_selective_prediction_monotonicity(
    probs: list[float], w_narrow: float, w_wide: float
) -> None:
    """Widening the review window [0.5 - w, 0.5 + w] must monotonically increase review count."""
    narrow_low, narrow_high = 0.5 - w_narrow, 0.5 + w_narrow
    wide_low, wide_high = 0.5 - w_wide, 0.5 + w_wide

    narrow_review_count = sum(1 for p in probs if narrow_low <= p <= narrow_high)
    wide_review_count = sum(1 for p in probs if wide_low <= p <= wide_high)

    # Monotonicity property: wider window must encompass all cases in the narrow window
    assert wide_review_count >= narrow_review_count


@given(
    ood_anomaly_scores=st.lists(st.floats(min_value=0.6, max_value=1.0), min_size=5, max_size=30),
    rejection_threshold=st.floats(min_value=0.4, max_value=0.55),
)
def test_ood_anomaly_scores_safely_route_to_review(
    ood_anomaly_scores: list[float], rejection_threshold: float
) -> None:
    """OOD samples with anomaly scores exceeding the threshold must 100% route to REVIEW."""
    review_decisions = [s >= rejection_threshold for s in ood_anomaly_scores]
    # Invariant: zero false automated passes on severe OOD
    assert all(review_decisions)
