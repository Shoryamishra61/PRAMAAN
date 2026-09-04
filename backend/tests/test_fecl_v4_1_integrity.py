from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from app.carve import compile_financial_proof

from . import test_fecl_v4_benchmark as v4_checks

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data/financial-evidence-integrity/v4.1"


def _rows(split: str) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in (DATA / f"{split}.jsonl").read_text(encoding="utf-8").splitlines()
    ]


def test_v41_passes_all_v4_structural_checks() -> None:
    original = v4_checks.DATA
    v4_checks.DATA = DATA
    try:
        v4_checks.test_v4_counts_and_file_hashes_match_manifest()
        v4_checks.test_v4_families_templates_entities_and_pairs_do_not_cross_splits()
        v4_checks.test_v4_pair_repair_targets_the_changed_causal_field()
        v4_checks.test_v4_provenance_hashes_grounding_and_visibility_are_exact()
        v4_checks.test_v4_mcc_annotations_and_oracle_actions_are_bounded()
        v4_checks.test_v4_ood_has_no_forced_financial_label_and_always_reviews()
    finally:
        v4_checks.DATA = original


def test_v41_formal_proof_preserves_outcomes_and_records_annotation_debt() -> None:
    outcome_conflicts: Counter[tuple[str, str, str]] = Counter()
    annotation_conflicts: Counter[tuple[str, str, tuple[str, ...]]] = Counter()
    for split in ("train", "dev", "calibration"):
        for row in _rows(split):
            visible = {item["evidence_id"] for item in row["complete_evidence_inventory"]}
            proof = compile_financial_proof(row, visible)
            expected = "UNSAT" if row["material_contradiction"] else "SAT"
            if proof.status != expected:
                outcome_conflicts[(row["phenomenon"], expected, proof.status)] += 1
            if proof.certificate is None:
                continue
            annotated = row["minimum_contradiction_certificate"]
            certificate_matches = (
                set(proof.certificate.evidence_ids) == set(annotated["evidence_ids"])
                and proof.certificate.invariant_id in annotated["invariant_ids"]
            )
            if not certificate_matches:
                annotation_conflicts[
                    (
                        row["phenomenon"],
                        proof.certificate.invariant_id,
                        tuple(annotated["invariant_ids"]),
                    )
                ] += 1

    # v4.1 is cryptographically frozen and cannot be repaired in place. Its generator changed
    # two causal fields for wrong-order pairs and annotated source disagreement even when the
    # authoritative refund status already proved the conflict. v4.5 corrects these defects.
    assert outcome_conflicts == Counter({("policy_exception", "UNSAT", "SAT"): 57})
    assert annotation_conflicts == Counter(
        {
            (
                "matching_amount_wrong_order",
                "PAYMENT_PARENT_IDENTITY",
                ("ORDER_PAYMENT_IDENTITY",),
            ): 57,
            ("source_disagreement", "REFUND_STATUS", ("SOURCE_STATUS_AGREEMENT",)): 57,
        }
    )


def test_v41_oracle_acquires_only_the_minimal_hidden_requirements() -> None:
    for split in ("train", "dev", "calibration"):
        for row in _rows(split):
            expected = set(row["required_for_resolution"]) - set(row["initial_visible_evidence"])
            acquired = {step["evidence_id"] for step in row["oracle_acquisition_trajectory"]}
            assert acquired == expected
