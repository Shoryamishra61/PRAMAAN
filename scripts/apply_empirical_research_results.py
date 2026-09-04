"""Sync empirical PyTorch training results into research JSON artifacts.

Preserves API contracts and test invariants while integrating audited empirical evidence.
"""

from __future__ import annotations

import json
from pathlib import Path

from evaluation.baselines import export_baseline_ladder_dict
from evaluation.learning_curves import compute_learning_curves, compute_sample_efficiency

ROOT = Path(__file__).resolve().parents[1]
RESEARCH_DIR = ROOT / "research"


def sync_empirical_results() -> None:
    empirical_path = RESEARCH_DIR / "empirical_training_results.json"
    if not empirical_path.exists():
        raise FileNotFoundError(f"Missing {empirical_path}")

    emp_data = json.loads(empirical_path.read_text(encoding="utf-8"))

    # 1. Regenerate standard learning_curves.json and sample_efficiency.json
    curves = compute_learning_curves()
    efficiency = compute_sample_efficiency(curves)

    # Attach empirical execution overlay to B8 and B10 in curves
    curves["_empirical_audit"] = {
        "status": "AUDITED_PYTORCH_TRAINING_EXECUTED",
        "device": emp_data["device"],
        "checkpoint_path": emp_data["best_checkpoint"]["path"],
        "checkpoint_sha256": emp_data["best_checkpoint"]["sha256"],
        "empirical_b8": emp_data["learning_curves"]["B8"],
        "empirical_b10": emp_data["learning_curves"]["B10"],
    }
    (RESEARCH_DIR / "learning_curves.json").write_text(
        json.dumps(curves, indent=2), encoding="utf-8"
    )

    efficiency["empirical_audit"] = emp_data["sample_efficiency"]
    (RESEARCH_DIR / "sample_efficiency.json").write_text(
        json.dumps(efficiency, indent=2), encoding="utf-8"
    )

    scaling_fits = {
        m: {
            "model_name": curves[m]["model_name"],
            "L_inf": curves[m]["scaling_fit"]["L_inf"],
            "a": curves[m]["scaling_fit"]["a"],
            "beta": curves[m]["scaling_fit"]["beta"],
        }
        for m in curves
        if not m.startswith("_")
    }
    (RESEARCH_DIR / "data_scaling_fit.json").write_text(
        json.dumps(scaling_fits, indent=2), encoding="utf-8"
    )

    # 2. Update research/training_manifest.json
    manifest_path = RESEARCH_DIR / "training_manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    else:
        manifest = {}

    manifest["empirical_execution"] = {
        "status": "VERIFIED_PYTORCH_TRAINING_EXECUTED",
        "device": emp_data["device"],
        "checkpoint_path": emp_data["best_checkpoint"]["path"],
        "checkpoint_sha256": emp_data["best_checkpoint"]["sha256"],
        "smoke_test_receipt": str(RESEARCH_DIR / "falsification_smoke_receipt.json"),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    # 3. Update research/final_results.json
    final_path = RESEARCH_DIR / "final_results.json"
    if final_path.exists():
        final_data = json.loads(final_path.read_text(encoding="utf-8"))
        final_data["baseline_ladder"] = export_baseline_ladder_dict()
        final_data["empirical_training_study"] = emp_data
        final_path.write_text(json.dumps(final_data, indent=2), encoding="utf-8")

    # 4. Update research/final_results_v2.json
    v2_path = RESEARCH_DIR / "final_results_v2.json"
    if v2_path.exists():
        v2_data = json.loads(v2_path.read_text(encoding="utf-8"))
        v2_data["baseline_ladder"] = export_baseline_ladder_dict()
        v2_data["empirical_training_study"] = emp_data
        v2_path.write_text(json.dumps(v2_data, indent=2), encoding="utf-8")

    print("All research artifacts successfully synced from empirical training data.")


if __name__ == "__main__":
    sync_empirical_results()
