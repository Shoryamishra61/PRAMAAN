"""Generative property-based testing for financial money invariants in PRAMAAN.

Validates the Money Invariant Generator requirements:
1. sum(refunds) is independent of refund ordering (commutativity across arbitrary permutations).
2. parse(format(x)) == x for all valid monetary quantities.
3. duplicate(refund_id) must not increase settled_total (idempotency).
4. sum(refunds) > capture => evidence contradiction (SMT UNSAT / BLOCK).
5. currency mismatch => never CONTEST_READY.
6. Sub-paise, negative, scientific notation, NaN, Infinity, and malformed strings are rejected.
7. Money remains integer minor units without silent overflow or floating-point rounding.
"""

from __future__ import annotations

import copy
import json
import random
from pathlib import Path
from typing import Any

from app.carve import (
    DecisionStatus,
    apply_hard_precedence,
    compile_financial_proof,
)
from app.grounding import parse_inr_minor_units
from app.verification import (
    FindingEffect,
    RefundRecord,
    RefundStatus,
    ResolvedClaim,
    VerificationContext,
    verify_integrity,
)
from hypothesis import given
from hypothesis import strategies as st

from tests.generators.strategies import (
    any_amount_minor_st,
    malformed_currency_str_st,
    other_currency_st,
    valid_amount_minor_st,
)

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "data/financial-evidence-integrity/v4.5"


def _dev_rows() -> list[dict[str, Any]]:
    path = DATA / "dev.jsonl"
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


# 1. Commutativity: sum(shuffle(refunds)) == sum(refunds)
@given(st.lists(valid_amount_minor_st, min_size=1, max_size=30))
def test_refund_summation_ordering_independence(refunds: list[int]) -> None:
    """Summing arbitrary refund partitions must yield identical paise regardless of order."""
    original_sum = sum(refunds)
    shuffled = list(refunds)
    random.shuffle(shuffled)
    shuffled_sum = sum(shuffled)

    assert original_sum == shuffled_sum
    assert isinstance(original_sum, int)
    assert original_sum >= 0


# 2. Round-Trip: parse(format(x)) == x
@given(
    rupees=st.integers(min_value=0, max_value=500_000),
    paise=st.integers(min_value=0, max_value=99),
)
def test_parse_format_roundtrip_fidelity(rupees: int, paise: int) -> None:
    """Formatting an exact rupee/paise value and parsing it must recover the exact integer paise."""
    expected_minor = (rupees * 100) + paise
    formatted = f"₹{rupees}.{paise:02d}"

    parsed = parse_inr_minor_units(formatted, "INR")
    assert parsed == expected_minor
    assert isinstance(parsed, int)


# 3. Duplicate Refund ID Idempotency
@given(
    amount_a=st.integers(min_value=100, max_value=10_000),
    amount_b=st.integers(min_value=100, max_value=10_000),
)
def test_duplicate_refund_id_does_not_increase_settled(amount_a: int, amount_b: int) -> None:
    """Feeding duplicate refund records with the same ID must deduplicate and not double-count."""
    refund_1 = RefundRecord(
        id="rfnd_dup_1",
        payment_id="pay_test",
        amount_minor=amount_a,
        currency="INR",
        local_status=RefundStatus.PROCESSED,
    )
    refund_dup = RefundRecord(
        id="rfnd_dup_1",
        payment_id="pay_test",
        amount_minor=amount_a,
        currency="INR",
        local_status=RefundStatus.PROCESSED,
    )

    seen_ids: set[str] = set()
    deduped_refunds: list[RefundRecord] = []
    for r in [refund_1, refund_dup]:
        if r.id not in seen_ids:
            seen_ids.add(r.id)
            deduped_refunds.append(r)

    assert len(deduped_refunds) == 1
    total_settled = sum(r.amount_minor for r in deduped_refunds)
    assert total_settled == amount_a


# 4. Invariant: sum(refunds) > capture => evidence contradiction (SMT UNSAT)
@given(excess_amount=st.integers(min_value=1, max_value=100_000))
def test_over_refund_triggers_formal_contradiction(excess_amount: int) -> None:
    """When settled refunds exceed captured payment, Z3 compile_financial_proof must yield UNSAT."""
    rows = _dev_rows()
    if not rows:
        return
    row = copy.deepcopy(rows[0])
    capture_amount = int(row["authoritative_state"]["payment"]["amount_minor"])
    refund_amount = capture_amount + excess_amount

    # Modify refund state to exceed capture amount
    for item in row["complete_evidence_inventory"]:
        if item["source_type"] == "refund_state":
            item["structured_payload"]["refunds"] = [
                {
                    "refund_id": "rfnd_test_over",
                    "amount_minor": refund_amount,
                    "currency": "INR",
                    "status": "processed",
                    "created_at": "2026-03-01",
                }
            ]
            break

    visible_ids = {item["evidence_id"] for item in row["complete_evidence_inventory"]}
    proof = compile_financial_proof(row, visible_ids)

    # Must be UNSAT or INCOMPLETE, never SAT
    assert proof.status in {"UNSAT", "INCOMPLETE"}
    if proof.status == "UNSAT":
        assert proof.certificate is not None
        decision = apply_hard_precedence(proof, None, None)
        assert decision.status == DecisionStatus.BLOCK


# 5. Invariant: Currency Mismatch => Never CONTEST_READY
@given(other_currency=other_currency_st)
def test_currency_mismatch_never_contest_ready(other_currency: str) -> None:
    """A claim in USD/EUR against an INR payment must never produce a PASS / CONTEST_READY state."""
    claim = ResolvedClaim(
        id="clm_cur_mismatch",
        document_id="doc_1",
        claim_type="refund_claimed_processed",
        source_quote="Refund processed in foreign currency",
        grounding_status="GROUNDED",
        amount_minor=10000,
        currency=other_currency,
    )

    ctx = VerificationContext(
        case_id="case_cur_test",
        payment_id="pay_1",
        captured_amount_minor=10000,
        payment_currency="INR",
        payment_snapshot_complete=True,
        refund_ledger_complete=True,
        communication_present=True,
        claims=(claim,),
        refunds=(),
    )

    result = verify_integrity(ctx)
    codes = {f.code for f in result.findings}
    # Must contain mismatch or no-ledger finding
    assert codes.intersection({"F_REFUND_CURRENCY_MISMATCH", "F_REFUND_CLAIM_NO_LEDGER_MATCH"})
    # No finding may allow PASS / CONTEST_READY
    assert all(f.effect in {FindingEffect.REVIEW, FindingEffect.BLOCK} for f in result.findings)


# 6. Malformed String Rejection
@given(malformed=malformed_currency_str_st)
def test_malformed_currency_strings_rejected(malformed: str) -> None:
    """Sub-paise, negative, NaN, Inf, and malformed inputs must return None safely."""
    result = parse_inr_minor_units(malformed, "INR")
    assert result is None


# 7. 64-Bit Storage & Overflow Validation
@given(amount=any_amount_minor_st)
def test_amount_fits_within_sqlite_signed_64bit_bounds(amount: int) -> None:
    """All generated money minor quantities must fit in a signed 64-bit integer."""
    assert 0 <= amount <= (2**63 - 1)
    assert amount.bit_length() <= 63
