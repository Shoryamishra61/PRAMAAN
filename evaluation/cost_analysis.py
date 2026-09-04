"""Merchant Economics and Cost-Sensitive Decision Optimization.

Calculates:
1. Expected Merchant Cost under asymmetric loss: L(d, y) = 10*FP + 1*FB + 0.25*Rev
2. Pareto Frontier: Automation Coverage vs. Unsafe PASS rate
3. Economic savings across baseline ladder
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class PolicyCostResult:
    expected_cost_per_case: float
    total_cost: float
    coverage: float
    unsafe_pass_rate: float
    review_rate: float
    cost_reduction_vs_rules_pct: float


def compute_expected_cost(
    decisions: Sequence[str],  # "PASS", "REVIEW", "BLOCK"
    ground_truth: Sequence[int],  # 1 = contradictory/invalid, 0 = consistent
    cost_unsafe_pass: float = 10.0,
    cost_false_block: float = 1.0,
    cost_review: float = 0.25,
) -> PolicyCostResult:
    n = len(decisions)
    if n == 0:
        return PolicyCostResult(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)

    total_cost = 0.0
    automated_count = 0
    unsafe_pass_count = 0
    review_count = 0

    for d, y in zip(decisions, ground_truth, strict=True):
        if d == "PASS":
            automated_count += 1
            if y == 1:  # Material contradiction passed automatically!
                total_cost += cost_unsafe_pass
                unsafe_pass_count += 1
        elif d == "BLOCK":
            automated_count += 1
            if y == 0:  # Consistent case falsely blocked!
                total_cost += cost_false_block
        elif d == "REVIEW":
            review_count += 1
            total_cost += cost_review

    expected_cost = total_cost / n
    coverage = automated_count / n
    unsafe_pass_rate = unsafe_pass_count / max(1, automated_count)
    review_rate = review_count / n

    # Benchmark against static rules (assumed default cost 2.15)
    rules_cost = 2.15
    savings_pct = max(0.0, ((rules_cost - expected_cost) / rules_cost) * 100.0)

    return PolicyCostResult(
        expected_cost_per_case=round(expected_cost, 4),
        total_cost=round(total_cost, 2),
        coverage=round(coverage, 4),
        unsafe_pass_rate=round(unsafe_pass_rate, 4),
        review_rate=round(review_rate, 4),
        cost_reduction_vs_rules_pct=round(savings_pct, 2),
    )


def compute_pareto_frontier(
    probabilities: Sequence[float],
    ground_truth: Sequence[int],
    pass_thresholds: Sequence[float] = (0.1, 0.2, 0.3, 0.4, 0.5),
    block_thresholds: Sequence[float] = (0.6, 0.7, 0.8, 0.9),
) -> list[dict[str, float]]:
    """Compute (coverage, unsafe_pass_rate, expected_cost) points for Pareto analysis."""
    frontier = []
    for t_pass in pass_thresholds:
        for t_block in block_thresholds:
            if t_pass >= t_block:
                continue
            decisions = []
            for p in probabilities:
                if p <= t_pass:
                    decisions.append("PASS")
                elif p >= t_block:
                    decisions.append("BLOCK")
                else:
                    decisions.append("REVIEW")
            res = compute_expected_cost(decisions, ground_truth)
            frontier.append(
                {
                    "t_pass": t_pass,
                    "t_block": t_block,
                    "coverage": res.coverage,
                    "unsafe_pass_rate": res.unsafe_pass_rate,
                    "expected_cost": res.expected_cost_per_case,
                }
            )
    return sorted(frontier, key=lambda x: (x["expected_cost"], -x["coverage"]))


if __name__ == "__main__":
    demo_d = ["BLOCK"] * 10 + ["REVIEW"] * 20 + ["PASS"] * 30
    demo_y = [1] * 10 + [1] * 5 + [0] * 15 + [0] * 30
    res = compute_expected_cost(demo_d, demo_y)
    print(f"Sample Cost Analysis: {res}")
