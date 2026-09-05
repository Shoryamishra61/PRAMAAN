"""Unified Research Evaluation Runner for CARVE-FECL.

Executes:
1. Baseline Ladder Validation
2. Formal SMT Verification Checks
3. Causal Minimal-Pair Evaluations
4. Cost and Economics Analysis
5. OOD Robustness Evaluation
6. Architectural Ablation Studies
"""

from __future__ import annotations

import json
from pathlib import Path

from evaluation.ablations import run_ablation_benchmarks
from evaluation.causal_pairs import evaluate_causal_robustness
from evaluation.ood_eval import evaluate_ood_robustness


def run_full_evaluation() -> dict[str, object]:
    results_path = Path(__file__).resolve().parents[1] / "research" / "final_results.json"
    if results_path.exists():
        final_results = json.loads(results_path.read_text(encoding="utf-8"))
    else:
        final_results = {}

    causal = evaluate_causal_robustness()
    ood = evaluate_ood_robustness()
    ablations = run_ablation_benchmarks()

    summary = {
        "evidence_status": "HISTORICAL_ILLUSTRATIVE_NOT_EMPIRICAL",
        "benchmark_id": "DIG-RNP-SYN-V1",
        "causal_minimal_pairs": {
            "sensitivity": causal.counterfactual_sensitivity,
            "nuisance_invariance": causal.nuisance_invariance,
            "repair_validity": causal.repair_validity,
        },
        "ood_detection": {
            "auroc": ood.auroc,
            "aupr": ood.aupr,
            "review_routing_rate": ood.review_routing_rate,
        },
        "ablation_findings": {
            "mcc": ablations.mcc_study["finding"],
            "smt": ablations.formal_smt_study["finding"],
            "calibration": ablations.calibration_study["finding"],
            "voi": ablations.active_acquisition_study["finding"],
        },
        "final_results": final_results,
    }
    return summary


if __name__ == "__main__":
    out = run_full_evaluation()
    print(json.dumps(out, indent=2))
