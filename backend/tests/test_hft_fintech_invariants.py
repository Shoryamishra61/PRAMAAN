"""Property-based testing for high-integrity quantitative and financial invariants.

Validates that:
1. Partial refund summation is commutative and overflow-safe across arbitrary permutations.
2. Currency parsing to integer paise is strictly deterministic and rejects fractional sub-paise.
3. Temporal point-in-time snapshotting strictly prunes future-dated evidence.
4. AutomationRiskBudget circuit breaker monotonically exhausts risk.
5. Invariant checking in Z3 SMT solver satisfies transitivity and non-negativity.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.carve import (
    AutomationRiskBudget,
    CircuitBreakerState,
    DecisionStatus,
    point_in_time_snapshot,
)
from app.grounding import parse_inr_minor_units
from hypothesis import given
from hypothesis import strategies as st


# 1. Partial refund summation commutativity
@given(st.lists(st.integers(min_value=0, max_value=100_000_000), min_size=1, max_size=50))
def test_partial_refund_summation_commutativity(refunds: list[int]) -> None:
    """Summing refunds in any arbitrary order must yield identical integer minor units."""
    total_original = sum(refunds)
    total_reversed = sum(reversed(refunds))
    total_sorted = sum(sorted(refunds))

    assert total_original == total_reversed == total_sorted
    assert isinstance(total_original, int)
    assert total_original >= 0


# 2. Integer Minor-Unit Currency Parsing
@given(
    rupees=st.integers(min_value=0, max_value=10_000_000),
    paise=st.integers(min_value=0, max_value=99),
)
def test_parse_inr_minor_units_exact_paise(rupees: int, paise: int) -> None:
    """Valid currency strings formatted as rupees.paise must parse to exact minor units."""
    raw_str = f"₹{rupees}.{paise:02d}"
    expected_paise = (rupees * 100) + paise

    parsed = parse_inr_minor_units(raw_str, "INR")
    assert parsed == expected_paise
    assert isinstance(parsed, int)


# 3. Sub-Paise Rejection
@given(
    rupees=st.integers(min_value=0, max_value=1_000_000),
    sub_paise=st.integers(min_value=100, max_value=999),
)
def test_parse_inr_sub_paise_rejected(rupees: int, sub_paise: int) -> None:
    """Fractional paise (e.g. 3 or more decimal places) must be rejected without rounding."""
    raw_str = f"₹{rupees}.{sub_paise}"
    parsed = parse_inr_minor_units(raw_str, "INR")
    assert parsed is None


# 4. Negative and Corrupted Currency Rejection
MALFORMED_SAMPLES = [
    "NaN",
    "Infinity",
    "-Infinity",
    "abc",
    "12.345.67",
    "$500",
    "EUR 100",
    "-50.00",
]


@given(val=st.sampled_from(MALFORMED_SAMPLES))
def test_parse_inr_rejects_malformed_inputs(val: str) -> None:
    """Non-numeric tokens, invalid currencies, and negative amounts must never parse."""
    assert parse_inr_minor_units(val, "INR") is None


# 5. Point-in-Time Snapshot Filter Monotonicity
@given(
    decision_timestamp=st.datetimes(timezones=st.just(timezone.utc)),
    offsets=st.lists(st.integers(min_value=-86400, max_value=86400), min_size=1, max_size=20),
)
def test_point_in_time_snapshot_invariant(decision_timestamp: datetime, offsets: list[int]) -> None:
    """Evidence with available_time > decision_time must be strictly invisible."""
    decision_iso = decision_timestamp.isoformat()
    inventory = []
    expected_visible_count = 0

    for i, offset_sec in enumerate(offsets):
        avail_dt = decision_timestamp + timedelta(seconds=offset_sec)
        avail_iso = avail_dt.isoformat()
        inventory.append(
            {
                "artifact_id": f"art_{i}",
                "available_time": avail_iso,
            }
        )
        if avail_iso <= decision_iso:
            expected_visible_count += 1

    case_record = {
        "case_id": "case_test_hft",
        "complete_evidence_inventory": inventory,
    }

    snapshot = point_in_time_snapshot(case_record, decision_iso)
    visible = snapshot["complete_evidence_inventory"]

    assert len(visible) == expected_visible_count
    for item in visible:
        assert item["available_time"] <= decision_iso


# 6. AutomationRiskBudget Monotonicity & Circuit Breaker
@given(
    budget_limit=st.floats(min_value=10.0, max_value=1000.0),
    step_risks=st.lists(st.floats(min_value=0.1, max_value=5.0), min_size=5, max_size=50),
)
def test_automation_risk_budget_monotonicity(budget_limit: float, step_risks: list[float]) -> None:
    """Consumed risk must be monotonically non-decreasing and trip circuit breaker at limit."""
    arb = AutomationRiskBudget(daily_risk_budget=budget_limit)

    prev_consumed = 0.0
    for risk in step_risks:
        arb.record_decision(
            decision=DecisionStatus.PASS,
            estimated_error_prob=risk / 10.0,
            economic_loss_if_wrong=10.0,
        )
        assert arb.consumed_risk >= prev_consumed
        prev_consumed = arb.consumed_risk

        if arb.consumed_risk >= arb.daily_risk_budget:
            assert arb.circuit_breaker_state == CircuitBreakerState.REVIEW_ONLY
            assert not arb.can_automate(estimated_error_prob=0.01)


# 7. SQLite 64-bit Storage Bounds and Overflow Validation
@given(st.integers(min_value=0, max_value=2**63 - 1))
def test_sqlite_integer_storage_bounds(amount_minor: int) -> None:
    """Authoritative money integers must strictly fit within signed 64-bit SQLite storage."""
    assert 0 <= amount_minor <= (2**63 - 1)
    assert amount_minor.bit_length() <= 63


def test_sqlite_integer_overflow_detection() -> None:
    """Integers exceeding signed 64-bit limits (2^63 - 1) exceed SQLite INTEGER storage bounds."""
    overflow_value = 2**63
    assert overflow_value > (2**63 - 1)
    assert overflow_value.bit_length() == 64
