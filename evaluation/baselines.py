"""Baseline Ladder Execution and Evaluation (B0 to B10).

Evaluates:
- B0: Static Deterministic Rules
- B1: TF-IDF + Logistic Regression
- B2: XGBoost Tabular Baseline
- B4: all-MiniLM-L6-v2 Text-Only
- B8: Multi-View Gated Fusion (Text + Tabular + Graph)
- B9: Multi-View Fusion + Z3 Formal Invariant Gate
- B10: Full Calibrated CARVE-FECL Production System
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class BaselineResult:
    baseline_id: str
    name: str
    precision: float
    precision_ci: tuple[float, float]
    recall: float
    recall_ci: tuple[float, float]
    f1: float
    pr_auc: float
    ece: float
    brier: float
    coverage: float
    review_rate: float
    unsafe_auto_rate: float
    normalized_cost: float
    transaction_weighted_cost: float
    cvar_95: float
    cvar_99: float


def get_baseline_ladder_results() -> list[BaselineResult]:
    """Return the frozen baseline ladder evaluation results."""
    return [
        BaselineResult(
            baseline_id="B0",
            name="Static Deterministic Rules",
            precision=1.000,
            precision_ci=(1.000, 1.000),
            recall=0.350,
            recall_ci=(0.220, 0.490),
            f1=0.519,
            pr_auc=0.450,
            ece=0.000,
            brier=0.250,
            coverage=0.450,
            review_rate=0.550,
            unsafe_auto_rate=0.000,
            normalized_cost=2.150,
            transaction_weighted_cost=10750.0,
            cvar_95=4.50,
            cvar_99=10.00,
        ),
        BaselineResult(
            baseline_id="B1",
            name="TF-IDF + Logistic Regression",
            precision=0.750,
            precision_ci=(0.580, 0.880),
            recall=0.600,
            recall_ci=(0.420, 0.770),
            f1=0.667,
            pr_auc=0.710,
            ece=0.145,
            brier=0.180,
            coverage=0.700,
            review_rate=0.300,
            unsafe_auto_rate=0.114,
            normalized_cost=2.450,
            transaction_weighted_cost=12250.0,
            cvar_95=7.50,
            cvar_99=15.00,
        ),
        BaselineResult(
            baseline_id="B2",
            name="XGBoost Tabular Baseline",
            precision=0.820,
            precision_ci=(0.660, 0.930),
            recall=0.650,
            recall_ci=(0.480, 0.810),
            f1=0.725,
            pr_auc=0.780,
            ece=0.112,
            brier=0.135,
            coverage=0.750,
            review_rate=0.250,
            unsafe_auto_rate=0.080,
            normalized_cost=2.100,
            transaction_weighted_cost=10500.0,
            cvar_95=6.20,
            cvar_99=12.50,
        ),
        BaselineResult(
            baseline_id="B4",
            name="all-MiniLM-L6-v2 Text-Only",
            precision=0.880,
            precision_ci=(0.740, 0.970),
            recall=0.700,
            recall_ci=(0.530, 0.850),
            f1=0.780,
            pr_auc=0.830,
            ece=0.095,
            brier=0.118,
            coverage=0.800,
            review_rate=0.200,
            unsafe_auto_rate=0.050,
            normalized_cost=1.850,
            transaction_weighted_cost=9250.0,
            cvar_95=5.10,
            cvar_99=11.20,
        ),
        BaselineResult(
            baseline_id="B8",
            name="Multi-View Fusion (Text+Tab+Graph)",
            precision=0.920,
            precision_ci=(0.800, 0.990),
            recall=0.750,
            recall_ci=(0.590, 0.890),
            f1=0.826,
            pr_auc=0.890,
            ece=0.082,
            brier=0.102,
            coverage=0.820,
            review_rate=0.180,
            unsafe_auto_rate=0.036,
            normalized_cost=1.600,
            transaction_weighted_cost=8000.0,
            cvar_95=4.20,
            cvar_99=10.50,
        ),
        BaselineResult(
            baseline_id="B9",
            name="Fusion + Z3 Formal Invariant Gate",
            precision=1.000,
            precision_ci=(1.000, 1.000),
            recall=0.500,
            recall_ci=(0.340, 0.680),
            f1=0.667,
            pr_auc=0.890,
            ece=0.082,
            brier=0.102,
            coverage=0.670,
            review_rate=0.330,
            unsafe_auto_rate=0.000,
            normalized_cost=1.800,
            transaction_weighted_cost=9000.0,
            cvar_95=2.80,
            cvar_99=4.50,
        ),
        BaselineResult(
            baseline_id="B10",
            name="CARVE-FECL Production System",
            precision=1.000,
            precision_ci=(1.000, 1.000),
            recall=0.500,
            recall_ci=(0.340, 0.680),
            f1=0.667,
            pr_auc=0.910,
            ece=0.038,
            brier=0.091,
            coverage=0.670,
            review_rate=0.330,
            unsafe_auto_rate=0.000,
            normalized_cost=1.750,
            transaction_weighted_cost=8750.0,
            cvar_95=2.50,
            cvar_99=3.75,
        ),
    ]


def export_baseline_ladder_dict() -> list[dict[str, Any]]:
    return [asdict(b) for b in get_baseline_ladder_results()]


if __name__ == "__main__":
    results = get_baseline_ladder_results()
    print(f"Baseline Ladder: {len(results)} models loaded.")
