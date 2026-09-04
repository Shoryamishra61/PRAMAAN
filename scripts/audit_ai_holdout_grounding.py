"""Post-hoc audit of saved holdout predictions through grounding and the real gate."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.case_pipeline import CaseEvaluationInput, evaluate_case
from app.extraction import (
    ClaimModality,
    ClaimType,
    ExtractedClaim,
    ExtractionRequest,
    ExtractionResult,
)
from app.grounding import resolve_exact_quote
from app.verification import RefundRecord

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "data/benchmark/v1/holdout"
HOLDOUT_ARTIFACT = ROOT / "artifacts/ml/ai-research-study-v1-holdout.json"
OUTPUT = ROOT / "artifacts/ml/ai-research-study-v1-holdout-grounding-audit.json"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class SavedPredictionExtractor:
    def __init__(self, candidate: str, rows: dict[str, list[dict[str, Any]]]) -> None:
        self.candidate = candidate
        self.rows = rows

    async def extract(self, request: ExtractionRequest) -> ExtractionResult:
        case_id = request.document_id.removeprefix("doc_")
        claims = []
        for index, row in enumerate(self.rows.get(case_id, [])):
            probability = row[self.candidate]
            if probability is None or float(probability) < 0.5:
                continue
            claims.append(
                ExtractedClaim(
                    claim_id=f"audit_{case_id}_{index}",
                    document_id=request.document_id,
                    claim_type=ClaimType.REFUND_CLAIMED_PROCESSED,
                    quote=str(row["text"]),
                    value=None,
                    modality=ClaimModality.ASSERTION,
                )
            )
        return ExtractionResult(
            extractor_id=f"saved-{self.candidate}",
            model_id="post-hoc-saved-prediction-audit",
            claims=tuple(claims),
        )


def runtime_input(case_root: Path) -> CaseEvaluationInput:
    manifest = read_json(case_root / "manifest.json")
    payment = read_json(case_root / "payment_snapshot.json")
    ledger = read_json(case_root / "refunds.json")
    evidence = (case_root / "evidence/customer_communication.txt").read_text(encoding="utf-8")
    return CaseEvaluationInput(
        case_id=manifest["case_id"],
        reason_profile=manifest["reason_profile"],
        payment_id=payment["payment_id"],
        captured_amount_minor=payment["captured_amount_minor"],
        payment_currency=payment["currency"],
        payment_snapshot_complete=payment["snapshot_complete"],
        refund_ledger_complete=ledger["ledger_complete"],
        document_id=manifest["document_id"],
        canonical_text=evidence.strip(),
        input_supported=manifest["input_supported"],
        refunds=tuple(RefundRecord.model_validate(record) for record in ledger["records"]),
    )


async def audit() -> dict[str, Any]:
    frozen = read_json(HOLDOUT_ARTIFACT)
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in frozen["predictions"]:
        grouped[row["case_id"]].append(row)
    candidates = {
        "regex": "regex",
        "tfidf": "tfidf_probability",
        "embedding": "embedding_probability",
    }
    result: dict[str, Any] = {}
    for name, field in candidates.items():
        extractor = SavedPredictionExtractor(field, grouped)
        grounding = Counter()
        gate_confusion = Counter()
        cases = []
        for case_root in sorted(path for path in DATASET.iterdir() if path.is_dir()):
            request = runtime_input(case_root)
            for row in grouped[request.case_id]:
                probability = row[field]
                if probability is not None and float(probability) >= 0.5:
                    grounding[
                        resolve_exact_quote(request.canonical_text, row["text"]).status.value
                    ] += 1
            outcome = await evaluate_case(
                request, extractor, datetime(2026, 9, 1, tzinfo=timezone.utc)
            )
            expected = read_json(case_root / "ground_truth/gate_label.json")["status"]
            observed = outcome.decision.status.value
            gate_confusion[f"{expected}->{observed}"] += 1
            cases.append(
                {
                    "case_id": request.case_id,
                    "expected": expected,
                    "observed": observed,
                    "finding_codes": [finding.code for finding in outcome.verification.findings],
                    "review_reasons": list(outcome.decision.review_reasons),
                }
            )
        accepted = sum(grounding.values())
        result[name] = {
            "saved_score_field": field,
            "threshold": 0.5,
            "grounding_counts": dict(sorted(grounding.items())),
            "unique_grounding_rate": (
                round(grounding["GROUNDED"] / accepted, 6) if accepted else None
            ),
            "gate_confusion": dict(sorted(gate_confusion.items())),
            "false_pass": sum(
                1 for row in cases if row["observed"] == "PASS" and row["expected"] != "PASS"
            ),
            "false_block": sum(
                1 for row in cases if row["observed"] == "BLOCK" and row["expected"] != "BLOCK"
            ),
            "cases": cases,
        }
    return {
        "artifact_version": "ai-research-study-v1-posthoc-grounding-audit",
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "post_hoc": True,
        "tuning_performed": False,
        "source_holdout_artifact_sha256": sha256(HOLDOUT_ARTIFACT),
        "audit_script_sha256": sha256(Path(__file__)),
        "candidates": result,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--confirm-posthoc", action="store_true")
    args = parser.parse_args()
    if not args.confirm_posthoc:
        raise SystemExit("Refusing post-hoc holdout audit without --confirm-posthoc")
    artifact = asyncio.run(audit())
    OUTPUT.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"artifact": OUTPUT.relative_to(ROOT).as_posix()}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
