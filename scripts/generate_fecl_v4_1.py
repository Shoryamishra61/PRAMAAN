"""Generate the FECL-Bench v4.1 MCC/acquisition erratum without mutating frozen v4."""

from __future__ import annotations

import argparse
import json
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import generate_fecl_v4 as v4

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "data/financial-evidence-integrity/v4.1"
ERRATUM = ROOT / "docs/FECL-V4.1-ERRATUM.md"


def required_evidence_v41(phenomenon: str) -> list[str]:
    mapping = {
        "amount_mismatch": ["refund_state"],
        "one_rupee_boundary": ["refund_state"],
        "partial_refund": ["refund_state"],
        "cumulative_refund": ["refund_state"],
        "currency_mismatch": ["refund_state"],
        "wrong_rrn": ["rrn_linkage"],
        "wrong_arn_utr": ["completion_reference"],
        "refund_reference_mismatch": ["refund_state"],
        "wrong_parent_payment": ["refund_state"],
        "matching_amount_wrong_order": ["order_record"],
        "temporal_contradiction": ["refund_state"],
        "promised_not_due_vs_overdue": ["refund_state"],
        "stale_refund_state": ["refund_state"],
        "source_disagreement": ["refund_state"],
        "policy_exception": ["refund_policy"],
        "negation": ["refund_state"],
    }
    return mapping[phenomenon]


def version(value: Any) -> Any:
    if isinstance(value, str):
        return value.replace("DIG-FECL-BENCH-v4", "DIG-FECL-BENCH-v4.1").replace("v4-", "v4.1-")
    if isinstance(value, list):
        return [version(item) for item in value]
    if isinstance(value, dict):
        return {key: version(item) for key, item in value.items()}
    return value


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    if args.output.exists() and any(args.output.iterdir()):
        raise RuntimeError(f"Refusing to overwrite non-empty benchmark directory: {args.output}")
    args.output.mkdir(parents=True, exist_ok=True)
    v4.required_evidence = required_evidence_v41
    rng = random.Random(v4.SEED)
    generated: dict[str, list[dict[str, Any]]] = {}
    validation = {}
    for split in ("train", "dev", "calibration", "test"):
        generated[split] = version(v4.generate_split(split, v4.COUNTS[split], rng))
        validation[split] = v4.validate_split(generated[split], split, v4.COUNTS[split])
    generated["ood"] = version(v4.generate_ood(v4.COUNTS["ood"]))
    validation["ood"] = v4.validate_split(generated["ood"], "ood", v4.COUNTS["ood"])

    paths = {}
    for split, rows in generated.items():
        path = args.output / f"{split}.jsonl"
        v4.write_jsonl(path, rows)
        paths[split] = path
    manifest = {
        "benchmark_id": "DIG-FECL-BENCH-v4.1",
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "generator_seed": v4.SEED,
        "synthetic": True,
        "production_prevalence": False,
        "counts": v4.COUNTS,
        "families": v4.FAMILIES,
        "phenomena": v4.PHENOMENA,
        "evidence_costs": v4.EVIDENCE_COSTS,
        "validation": validation,
        "hashes": {split: v4.file_digest(path) for split, path in paths.items()},
        "protocol": "docs/FECL-V4-PROTOCOL.md + docs/FECL-V4.1-ERRATUM.md",
        "protocol_sha256": v4.file_digest(ROOT / "docs/FECL-V4-PROTOCOL.md"),
        "erratum_sha256": v4.file_digest(ERRATUM),
        "supersedes": "DIG-FECL-BENCH-v4",
        "models_fitted_before_correction": False,
        "test_evaluated_before_correction": False,
    }
    (args.output / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
