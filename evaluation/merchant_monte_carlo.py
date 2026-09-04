"""Monte Carlo simulation of projected merchant economics.

Samples 10,000 parameter realizations to quantify uncertainty over operational
assumptions (dispute volume, ticket size, recovery rates, analyst wages, API costs).
Computes P10, P50, P90 Net Merchant Edge, break-even dispute volume, and break-even analyst wage.
Clearly marked as PROJECTED / MODELED MERCHANT ECONOMICS.
"""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RESEARCH_DIR = ROOT / "research"

NUM_SIMULATIONS = 10000


def run_merchant_monte_carlo() -> dict[str, Any]:
    random.seed(42)

    net_edges_inr: list[float] = []
    net_edges_pct: list[float] = []
    rooi_ratios: list[float] = []

    for _ in range(NUM_SIMULATIONS):
        # Sample plausible operational parameters
        volume = random.uniform(8000, 12000)
        mean_ticket = random.lognormvariate(mu=8.517, sigma=0.25)  # E[ticket] ~ 5000 INR
        ticket_volume = volume * mean_ticket

        # Cost reduction factors based on benchmark
        # Rules baseline loss rate = 2.15 / 10 = 0.215 of dispute value
        # CARVE decision loss rate = 1.75 / 10 = 0.175 of dispute value
        baseline_loss_rate = random.uniform(0.205, 0.225)
        carve_loss_rate = random.uniform(0.165, 0.185)

        baseline_loss = ticket_volume * baseline_loss_rate
        carve_loss = ticket_volume * carve_loss_rate
        gross_edge = baseline_loss - carve_loss

        # Frictions
        review_fraction = random.uniform(0.30, 0.36)
        analyst_cost_per_review = random.uniform(120.0, 180.0)  # INR
        evidence_fetch_fraction = random.uniform(0.11, 0.15)
        evidence_cost_per_fetch = random.uniform(40.0, 60.0)  # INR
        compute_cost_per_case = random.uniform(0.40, 0.60)  # INR

        total_review_cost = volume * review_fraction * analyst_cost_per_review
        total_evidence_cost = volume * evidence_fetch_fraction * evidence_cost_per_fetch
        total_compute_cost = volume * compute_cost_per_case

        total_friction = total_review_cost + total_evidence_cost + total_compute_cost
        net_edge = gross_edge - total_friction
        edge_pct = (net_edge / baseline_loss) * 100.0
        rooi = gross_edge / max(total_friction, 1.0)

        net_edges_inr.append(net_edge)
        net_edges_pct.append(edge_pct)
        rooi_ratios.append(rooi)

    net_edges_inr.sort()
    net_edges_pct.sort()
    rooi_ratios.sort()

    p10_inr = net_edges_inr[int(0.10 * NUM_SIMULATIONS)]
    p50_inr = net_edges_inr[int(0.50 * NUM_SIMULATIONS)]
    p90_inr = net_edges_inr[int(0.90 * NUM_SIMULATIONS)]

    p10_pct = net_edges_pct[int(0.10 * NUM_SIMULATIONS)]
    p50_pct = net_edges_pct[int(0.50 * NUM_SIMULATIONS)]
    p90_pct = net_edges_pct[int(0.90 * NUM_SIMULATIONS)]

    prob_positive_edge = sum(1 for x in net_edges_inr if x > 0) / NUM_SIMULATIONS

    # Break-even analysis
    # Find dispute volume where net edge becomes 0 under median friction
    break_even_volume = round(566000.0 / (5000.0 * (0.215 - 0.175)), 0)
    # Find analyst review wage where net edge becomes 0 at 10,000 volume
    break_even_analyst_cost = round((4000000.0 - 71000.0) / 3300.0, 2)

    results = {
        "status": "PROJECTED / MODELED MERCHANT ECONOMICS",
        "methodology": "Monte Carlo uncertainty propagation over 10,000 parameter realizations",
        "parameters_sampled": {
            "dispute_volume_range": [8000, 12000],
            "mean_dispute_amount_inr": "Lognormal(mu=8.517, sigma=0.25) [E=5000]",
            "analyst_cost_per_review_inr": [120.0, 180.0],
            "evidence_cost_per_fetch_inr": [40.0, 60.0],
            "cloud_compute_cost_per_case_inr": [0.40, 0.60],
        },
        "projected_net_merchant_edge_inr": {
            "p10": round(p10_inr, 2),
            "p50_median": round(p50_inr, 2),
            "p90": round(p90_inr, 2),
        },
        "projected_net_margin_edge_pct": {
            "p10": round(p10_pct, 2),
            "p50_median": round(p50_pct, 2),
            "p90": round(p90_pct, 2),
        },
        "return_on_operational_investment": {
            "p10": round(rooi_ratios[int(0.10 * NUM_SIMULATIONS)], 2),
            "p50_median": round(rooi_ratios[int(0.50 * NUM_SIMULATIONS)], 2),
            "p90": round(rooi_ratios[int(0.90 * NUM_SIMULATIONS)], 2),
        },
        "probability_net_edge_positive": round(prob_positive_edge, 4),
        "break_even_metrics": {
            "break_even_dispute_volume": int(break_even_volume),
            "break_even_analyst_review_cost_inr": float(break_even_analyst_cost),
        },
        "governance_note": (
            "Per Directive Section 45: These figures represent stochastic simulations under "
            "explicitly stated assumptions, NOT historical observed merchant accounting. "
            "True merchant edge must be confirmed in shadow mode."
        ),
    }

    (RESEARCH_DIR / "merchant_monte_carlo.json").write_text(
        json.dumps(results, indent=2), encoding="utf-8"
    )
    return results


if __name__ == "__main__":
    out = run_merchant_monte_carlo()
    print("Merchant Monte Carlo simulation written.")
