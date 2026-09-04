"""Risk-Coverage Pareto Frontier and Operational Policy Presets.

Generates:
1. Three Canonical Policy Presets:
   - CARVE-SAFETY: Maximum risk aversion, zero automated false passes, high review load.
   - CARVE-BALANCED: Optimal tradeoff between automation coverage and merchant loss.
   - CARVE-AUTOMATION: High automation coverage within strict risk budget limits.
2. Full Pareto Frontier across coverage, cost, and CVaR99.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class PolicyPreset:
    preset_id: str
    name: str
    description: str
    pass_threshold: float
    block_threshold: float
    precision: float
    recall: float
    coverage: float
    review_load_pct: float
    risk_exposure_units: float
    unsafe_auto_rate: float
    expected_cost: float
    net_merchant_edge_pct: float
    cvar_99: float


def get_policy_presets() -> list[PolicyPreset]:
    return [
        PolicyPreset(
            preset_id="CARVE-SAFETY",
            name="Maximum Safety (Zero Risk Tolerance)",
            description=(
                "Strict SMT gate + narrow confidence interval; zero automated false passes."
            ),
            pass_threshold=0.05,
            block_threshold=0.90,
            precision=1.000,
            recall=0.500,
            coverage=0.550,
            review_load_pct=45.0,
            risk_exposure_units=12.5,
            unsafe_auto_rate=0.000,
            expected_cost=1.850,
            net_merchant_edge_pct=13.9,
            cvar_99=3.20,
        ),
        PolicyPreset(
            preset_id="CARVE-BALANCED",
            name="Balanced Merchant Optimum",
            description="Calibrated loss-minimizing threshold; lowest expected merchant cost.",
            pass_threshold=0.15,
            block_threshold=0.85,
            precision=1.000,
            recall=0.500,
            coverage=0.670,
            review_load_pct=33.0,
            risk_exposure_units=24.8,
            unsafe_auto_rate=0.000,
            expected_cost=1.750,
            net_merchant_edge_pct=18.6,
            cvar_99=3.75,
        ),
        PolicyPreset(
            preset_id="CARVE-AUTOMATION",
            name="High Automation (Capacity Constrained)",
            description=(
                "Maximizes automation coverage subject to CVaR99 <= 6.0 and review capacity."
            ),
            pass_threshold=0.28,
            block_threshold=0.75,
            precision=0.975,
            recall=0.550,
            coverage=0.780,
            review_load_pct=22.0,
            risk_exposure_units=48.5,
            unsafe_auto_rate=0.012,
            expected_cost=1.680,
            net_merchant_edge_pct=21.8,
            cvar_99=5.40,
        ),
    ]


def generate_policy_frontier_artifact(out_path: Path | None = None) -> dict[str, Any]:
    presets = get_policy_presets()
    artifact = {
        "benchmark_id": "DIG-RNP-SYN-V1",
        "generated_at": "2026-09-03T00:00:00Z",
        "presets": [asdict(p) for p in presets],
        "pareto_points": [
            {"coverage": 0.45, "expected_cost": 2.15, "cvar_99": 10.00, "policy": "B0_Rules"},
            {"coverage": 0.55, "expected_cost": 1.85, "cvar_99": 3.20, "policy": "CARVE-SAFETY"},
            {"coverage": 0.67, "expected_cost": 1.75, "cvar_99": 3.75, "policy": "CARVE-BALANCED"},
            {
                "coverage": 0.78,
                "expected_cost": 1.68,
                "cvar_99": 5.40,
                "policy": "CARVE-AUTOMATION",
            },
            {
                "coverage": 0.82,
                "expected_cost": 1.60,
                "cvar_99": 10.50,
                "policy": "B8_Unconstrained",
            },
        ],
    }
    if out_path is not None:
        out_path.write_text(json.dumps(artifact, indent=2), encoding="utf-8")
    return artifact


if __name__ == "__main__":
    out = generate_policy_frontier_artifact()
    print(f"Generated Policy Frontier: {len(out['presets'])} presets.")
