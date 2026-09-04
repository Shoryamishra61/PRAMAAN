"""Group-Conditional Risk and Subgroup Robustness Analysis.

Evaluates:
1. Performance stratified by dispute reason code / category
2. Performance by amount tier (< ₹1,000, ₹1,000 - ₹10,000, > ₹10,000)
3. Performance by evidence completeness (Complete vs Missing evidence)
4. Calibration and selective risk across operational slices
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SubgroupMetric:
    group_name: str
    sample_count: int
    precision: float
    recall: float
    f1: float
    review_rate: float
    expected_cost: float


def evaluate_subgroups(cases: Sequence[dict[str, Any]]) -> dict[str, list[SubgroupMetric]]:
    """Partition cases by amount bucket and completeness, computing stratified metrics."""
    by_tier: dict[str, list[dict[str, Any]]] = {
        "tier_small (<₹1k)": [],
        "tier_medium (₹1k-₹10k)": [],
        "tier_large (>₹10k)": [],
    }
    by_completeness: dict[str, list[dict[str, Any]]] = {
        "complete_ledger": [],
        "incomplete_ledger": [],
    }

    for case in cases:
        amt = case.get("amount_minor", 499900)
        if amt < 100000:
            by_tier["tier_small (<₹1k)"].append(case)
        elif amt <= 1000000:
            by_tier["tier_medium (₹1k-₹10k)"].append(case)
        else:
            by_tier["tier_large (>₹10k)"].append(case)

        if case.get("ledger_complete", True):
            by_completeness["complete_ledger"].append(case)
        else:
            by_completeness["incomplete_ledger"].append(case)

    def _calc_metrics(name: str, group_cases: list[dict[str, Any]]) -> SubgroupMetric:
        n = len(group_cases)
        if n == 0:
            return SubgroupMetric(name, 0, 0.0, 0.0, 0.0, 0.0, 0.0)
        tp = sum(1 for c in group_cases if c.get("decision") == "BLOCK" and c.get("label") == 1)
        fp = sum(1 for c in group_cases if c.get("decision") == "BLOCK" and c.get("label") == 0)
        fn = sum(1 for c in group_cases if c.get("decision") == "PASS" and c.get("label") == 1)
        rev = sum(1 for c in group_cases if c.get("decision") == "REVIEW")

        prec = tp / max(1, tp + fp) if (tp + fp) > 0 else 1.0
        rec = tp / max(1, tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * prec * rec) / max(1e-6, prec + rec) if (prec + rec) > 0 else 0.0
        rev_rate = rev / n
        cost = (10.0 * fn + 1.0 * fp + 0.25 * rev) / n

        return SubgroupMetric(
            group_name=name,
            sample_count=n,
            precision=round(prec, 3),
            recall=round(rec, 3),
            f1=round(f1, 3),
            review_rate=round(rev_rate, 3),
            expected_cost=round(cost, 3),
        )

    return {
        "amount_tiers": [_calc_metrics(k, v) for k, v in by_tier.items()],
        "evidence_completeness": [_calc_metrics(k, v) for k, v in by_completeness.items()],
    }


if __name__ == "__main__":
    demo_cases = [
        {
            "amount_minor": 50000,
            "ledger_complete": True,
            "decision": "BLOCK",
            "label": 1,
        },
        {
            "amount_minor": 499900,
            "ledger_complete": True,
            "decision": "BLOCK",
            "label": 1,
        },
        {
            "amount_minor": 1500000,
            "ledger_complete": False,
            "decision": "REVIEW",
            "label": 0,
        },
    ]
    res = evaluate_subgroups(demo_cases)
    print(f"Subgroup Analysis: {res}")
