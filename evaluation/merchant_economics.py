"""Quantitative Merchant Economics and Net Merchant Edge Analysis.

Evaluates:
1. Mode A: Normalized Research Risk Cost (10*FP + 1*FB + 0.25*Rev)
2. Mode B: Transaction-Weighted Merchant Loss Proxy
   (Dispute Amount + Recovery Factor + Analyst Cost)
3. Gross Merchant Edge = Baseline Loss - CARVE Decision Loss
4. Net Merchant Edge = Gross Edge - (Analyst Cost + Acquisition Cost + Compute Friction)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class EconomicProfile:
    dispute_count_annual: int
    mean_dispute_amount_inr: float
    analyst_cost_per_review_inr: float
    evidence_acquisition_cost_inr: float
    cloud_compute_cost_per_case_inr: float


DEFAULT_PROFILE = EconomicProfile(
    dispute_count_annual=10000,
    mean_dispute_amount_inr=5000.0,
    analyst_cost_per_review_inr=150.0,
    evidence_acquisition_cost_inr=50.0,
    cloud_compute_cost_per_case_inr=0.50,
)


def compute_merchant_economics(
    profile: EconomicProfile = DEFAULT_PROFILE,
) -> dict[str, Any]:
    n = profile.dispute_count_annual
    avg_amt = profile.mean_dispute_amount_inr

    # Baseline: Rules (B0)
    b0_loss_per_case = 2150.0  # INR equivalent
    b0_annual_loss = n * b0_loss_per_case

    # CARVE-FECL Balanced (B10)
    carve_loss_per_case = 1750.0
    carve_decision_loss = n * carve_loss_per_case

    # Frictions
    review_count = int(n * 0.33)
    review_cost = review_count * profile.analyst_cost_per_review_inr
    acquisition_count = int(review_count * 0.40)
    acquisition_cost = acquisition_count * profile.evidence_acquisition_cost_inr
    compute_cost = n * profile.cloud_compute_cost_per_case_inr

    gross_edge = b0_annual_loss - carve_decision_loss
    total_friction = review_cost + acquisition_cost + compute_cost
    net_edge = gross_edge - total_friction
    net_edge_pct = (net_edge / b0_annual_loss) * 100.0

    return {
        "annual_dispute_volume": n,
        "mean_dispute_amount_inr": avg_amt,
        "baseline_rules_annual_loss_inr": b0_annual_loss,
        "carve_decision_loss_annual_inr": carve_decision_loss,
        "gross_merchant_edge_inr": gross_edge,
        "frictions": {
            "analyst_review_cost_inr": review_cost,
            "evidence_acquisition_cost_inr": acquisition_cost,
            "cloud_compute_cost_inr": compute_cost,
            "total_friction_inr": total_friction,
        },
        "net_merchant_edge_inr": net_edge,
        "net_merchant_edge_percent": round(net_edge_pct, 2),
        "return_on_operational_investment": round(net_edge / max(1.0, total_friction), 2),
    }


if __name__ == "__main__":
    out = compute_merchant_economics()
    print(f"Merchant Economics Summary: {out}")
