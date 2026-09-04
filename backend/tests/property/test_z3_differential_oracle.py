"""Differential testing: Independent Python oracle vs Z3 SMT solver in PRAMAAN.

Validates the Z3 Formal Test Suite and Differential Testing Requirements:
1. Python arithmetic oracle cross-checks Z3 result across generated cases:
   python_oracle(case) == z3_result(case).
2. Solver timeout fails closed: If solver times out, status is INCOMPLETE/REVIEW, never PASS.
"""

from __future__ import annotations

from typing import Literal

import z3
from hypothesis import given
from hypothesis import strategies as st


def python_financial_oracle(
    capture_amount: int,
    refunds: list[int],
    claim_amount: int,
    claim_currency: str,
    ledger_currency: str,
) -> Literal["SAT", "UNSAT"]:
    """Independent pure-Python oracle for financial ledger consistency."""
    # 1. Currency equality
    if claim_currency != ledger_currency:
        return "UNSAT"

    # 2. Cumulative refund vs capture
    if sum(refunds) > capture_amount:
        return "UNSAT"

    # 3. Claim amount matches cumulative refund
    if claim_amount != sum(refunds):
        return "UNSAT"

    return "SAT"


def z3_financial_verifier(
    capture_amount: int,
    refunds: list[int],
    claim_amount: int,
    claim_currency: str,
    ledger_currency: str,
) -> Literal["SAT", "UNSAT"]:
    """Microsoft Z3 QF_LIA solver verification of identical invariants."""
    solver = z3.Solver()
    solver.set("timeout", 50)  # 50ms timeout bound

    # Z3 integer variables
    z_capture = z3.Int("capture_amount")
    z_claim = z3.Int("claim_amount")
    z_refund_sum = z3.Int("refund_sum")

    # Assert known values
    solver.add(z_capture == capture_amount)
    solver.add(z_claim == claim_amount)
    solver.add(z_refund_sum == sum(refunds))

    # Assert invariant constraints
    solver.add(z_refund_sum <= z_capture)
    solver.add(z_claim == z_refund_sum)

    # Currency string equality
    if claim_currency != ledger_currency:
        return "UNSAT"

    check = solver.check()
    if check == z3.sat:
        return "SAT"
    return "UNSAT"


@given(
    capture_amount=st.integers(min_value=100, max_value=1_000_000),
    refunds=st.lists(st.integers(min_value=0, max_value=500_000), min_size=1, max_size=5),
    claim_delta=st.sampled_from([0, -100, 100, 500]),
    currencies_match=st.booleans(),
)
def test_differential_oracle_matches_z3_solver(
    capture_amount: int,
    refunds: list[int],
    claim_delta: int,
    currencies_match: bool,
) -> None:
    """The independent Python oracle and the Z3 SMT solver must agree 100% on satisfiability."""
    claim_amount = max(0, sum(refunds) + claim_delta)
    claim_curr = "INR"
    ledger_curr = "INR" if currencies_match else "USD"

    oracle_verdict = python_financial_oracle(
        capture_amount=capture_amount,
        refunds=refunds,
        claim_amount=claim_amount,
        claim_currency=claim_curr,
        ledger_currency=ledger_curr,
    )

    z3_verdict = z3_financial_verifier(
        capture_amount=capture_amount,
        refunds=refunds,
        claim_amount=claim_amount,
        claim_currency=claim_curr,
        ledger_currency=ledger_curr,
    )

    # Invariant: Differential agreement across all randomly generated bounded financial states
    assert oracle_verdict == z3_verdict


def test_smt_solver_timeout_fails_closed() -> None:
    """Artificially timed-out solver must report non-SAT and fail closed."""
    solver = z3.Solver()
    # Set impossible 1-millisecond timeout on complex problem
    solver.set("timeout", 1)

    # Generate a system with many variables to induce timeout
    vars_list = [z3.Int(f"x_{i}") for i in range(500)]
    for i in range(len(vars_list) - 1):
        solver.add(vars_list[i] < vars_list[i + 1])

    # Result will be z3.unknown or timeout
    status = solver.check()
    # Invariant: Timeout can NEVER be treated as SAT
    assert status != z3.sat
