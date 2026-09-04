"""Build every numeric paper table/macro/card from frozen FECL artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper"
TEST_PATH = ROOT / "artifacts/ml/fecl-v2-test.json"
DEV_PATH = ROOT / "artifacts/ml/fecl-v2-dev.json"
ANALYSIS_PATH = ROOT / "artifacts/ml/fecl-v2-analysis.json"
FREEZE_PATH = ROOT / "artifacts/ml/fecl-v2-freeze.json"
V1_HOLDOUT_PATH = ROOT / "artifacts/ml/ai-research-study-v1-holdout.json"
V1_AUDIT_PATH = ROOT / "artifacts/ml/ai-research-study-v1-holdout-grounding-audit.json"

MODEL_NAMES = {
    "literal_rules": "Literal relation rules",
    "communication_tfidf": "Communication TF--IDF",
    "pair_tfidf": "Pair-text TF--IDF",
    "communication_embedding": "MiniLM communication",
    "relational_embedding": "MiniLM relation vector",
    "neuro_symbolic": "Neuro-symbolic relation",
    "neuro_symbolic_no_money": "Neuro-symbolic without money edges",
    "relational_xgboost": "Relation XGBoost",
    "relational_mlp": "Relation MLP (5-seed ensemble)",
}


def read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def latex_escape(value: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(character, character) for character in value)


def main_results(test: dict[str, Any]) -> str:
    rows = []
    for name in MODEL_NAMES:
        details = test["models"][name]
        values = details.get("calibrated_metrics", details["metrics"])
        rows.append(
            " & ".join(
                [
                    MODEL_NAMES[name],
                    f"{values['precision']:.3f}",
                    f"{values['recall']:.3f}",
                    f"{values['f1']:.3f}",
                    f"{values['pr_auc']:.3f}",
                    str(values["false_pass"]),
                    str(values["false_block"]),
                    f"{values['expected_loss_per_case']:.3f}",
                ]
            )
            + r" \\"
        )
    return "\n".join(rows) + "\n\\bottomrule"


def slice_results(analysis: dict[str, Any]) -> str:
    rows = []
    for family, details in analysis["slices"]["family"].items():
        values = details["neuro_symbolic"]
        rows.append(
            f"{latex_escape(family)} & {values['count']} & {values['precision']:.3f} & "
            f"{values['recall']:.3f} & {values['f1']:.3f} & {values['false_pass']} & "
            f"{values['false_block']} \\\\"
        )
    return "\n".join(rows) + "\n\\bottomrule"


def calibration_results(test: dict[str, Any], analysis: dict[str, Any]) -> str:
    rows = []
    for name, delta in analysis["calibration_delta"].items():
        raw = test["models"][name]["metrics"]
        calibrated = test["models"][name]["calibrated_metrics"]
        rows.append(
            f"{MODEL_NAMES[name]} & {raw['brier']:.3f} & {calibrated['brier']:.3f} & "
            f"{raw['ece_10']:.3f} & {calibrated['ece_10']:.3f} & {delta['f1_delta']:+.3f} \\\\"
        )
    return "\n".join(rows) + "\n\\bottomrule"


def error_examples(analysis: dict[str, Any]) -> str:
    errors = analysis["errors"]["neuro_symbolic"]
    rows = []
    for kind, key in (("False PASS", "example_false_pass"), ("False BLOCK", "example_false_block")):
        for row in errors[key][:2]:
            ledger = row["ledger"]
            rows.append(
                f"\\noindent\\textbf{{{kind} --- {latex_escape(row['family'])}.}} "
                f"``{latex_escape(row['communication'])}'' "
                f"Ledger: \\texttt{{{latex_escape(ledger['status'])}/"
                f"{ledger['currency']} {ledger['amount']}}}; score {row['score']:.3f}.\\par"
            )
    return "\n\\smallskip\n".join(rows)


def macros(test: dict[str, Any], analysis: dict[str, Any], v1: dict[str, Any]) -> str:
    neuro = test["models"]["neuro_symbolic"]["calibrated_metrics"]
    rules = test["models"]["literal_rules"]["metrics"]
    pair = test["models"]["pair_tfidf"]["calibrated_metrics"]
    stats = test["statistical_tests"]["neuro_symbolic"]
    counterfactual = analysis["counterfactual_pairs"]["neuro_symbolic"]
    v1_regex = v1["claim_extraction"]["regex_baseline"]["metrics"]
    v1_tfidf = v1["claim_extraction"]["tfidf_combined"]["metrics"]
    return "\n".join(
        [
            rf"\newcommand{{\TrainCases}}{{{test['dataset']['train_cases']}}}",
            rf"\newcommand{{\TestCases}}{{{test['dataset']['evaluation_cases']}}}",
            rf"\newcommand{{\OODCases}}{{{test['ood']['count']}}}",
            rf"\newcommand{{\RulesFOne}}{{{rules['f1']:.3f}}}",
            rf"\newcommand{{\PairFOne}}{{{pair['f1']:.3f}}}",
            rf"\newcommand{{\NeuroFOne}}{{{neuro['f1']:.3f}}}",
            rf"\newcommand{{\NeuroPrecision}}{{{neuro['precision']:.3f}}}",
            rf"\newcommand{{\NeuroRecall}}{{{neuro['recall']:.3f}}}",
            rf"\newcommand{{\RulesFalsePass}}{{{rules['false_pass']}}}",
            rf"\newcommand{{\NeuroFalsePass}}{{{neuro['false_pass']}}}",
            rf"\newcommand{{\NeuroFalseBlock}}{{{neuro['false_block']}}}",
            rf"\newcommand{{\McNemarP}}{{{stats['vs_literal_mcnemar']['exact_two_sided_p']:.4f}}}",
            rf"\newcommand{{\BootstrapLow}}{{{stats['vs_literal_bootstrap']['ci95'][0]:.3f}}}",
            rf"\newcommand{{\BootstrapHigh}}{{{stats['vs_literal_bootstrap']['ci95'][1]:.3f}}}",
            rf"\newcommand{{\OODCombined}}{{{test['ood']['combined_safe_controller_rejection_rate']:.3f}}}",
            rf"\newcommand{{\OODLearned}}{{{test['ood']['learned_only_rejection_rate']:.3f}}}",
            rf"\newcommand{{\PairBothCorrect}}{{{counterfactual['both_correct_rate']:.3f}}}",
            rf"\newcommand{{\VOneRulesFOne}}{{{v1_regex['f1']:.3f}}}",
            rf"\newcommand{{\VOneTfidfFOne}}{{{v1_tfidf['f1']:.3f}}}",
        ]
    )


def dataset_card(test: dict[str, Any], frozen: dict[str, Any]) -> str:
    return f"""# DIG-FECL-SYN-v2 dataset card

## Summary

Synthetic diagnostic benchmark for evidence/state consistency in the narrow refund-not-processed
domain. It contains {test["dataset"]["train_cases"]} training, 256 development,
{test["dataset"]["evaluation_cases"]} frozen test, and {test["ood"]["count"]} OOD cases. Every
in-distribution case belongs to a minimal pair that shares authoritative state while one material
claim changes.

## Intended use

- research on semantic-state extraction, relational representations, selective prediction and
  deterministic reconciliation;
- regression testing of a defense-only evidence debugger.

## Prohibited claims

The dataset does not estimate production prevalence, dispute win rate, fraud, legal correctness,
merchant savings or real customer behavior. It must not train autonomous payment/dispute actions.

## Splits and leakage controls

- Train families: formal, support, portal, terse, Hinglish-train.
- DEV families: narrative, passive.
- Frozen test families: indirect, temporal, Hinglish-holdout.
- Test SHA-256: `{frozen["test_sha256"]}`.
- Dataset manifest SHA-256: `{frozen["dataset_manifest_sha256"]}`.

## Known limitations

Template-generated language, balanced labels, fixed graph topology, single-event temporal state,
canonical text/JSON only, and no merchant/issuer outcome labels. Results are synthetic benchmark
results only.
"""


def model_card(test: dict[str, Any]) -> str:
    neuro = test["models"]["neuro_symbolic"]
    calibrated = neuro["calibrated_metrics"]
    return f"""# FECL v2 neuro-symbolic relation model card

## Status

`RESEARCH_WINNER_NOT_DEPLOYED`. The product runtime remains `regex-baseline-v1`.

## Architecture

Pinned MiniLM semantic-state representation, a train-only semantic-state classifier, typed relation
edges to authoritative status, deterministic amount/currency equality features, and a calibrated
logistic relation head. The model never performs money arithmetic or final PASS/REVIEW/BLOCK policy.

## Frozen synthetic test

- Precision: {calibrated["precision"]:.6f}
- Recall: {calibrated["recall"]:.6f}
- F1: {calibrated["f1"]:.6f}
- PR-AUC: {calibrated["pr_auc"]:.6f}
- False PASS: {calibrated["false_pass"]}
- False BLOCK: {calibrated["false_block"]}
- Expected illustrative loss/case: {calibrated["expected_loss_per_case"]:.6f}

## Safety and limitations

Only grounded semantic-state features may be learned. Missing/ambiguous/OOD/model failure routes to
REVIEW. Platt scaling worsened Brier/ECE under wording-family shift. Hinglish-holdout remains the
weakest slice. No real merchant validation exists; deployment is prohibited.
"""


def checklist(paths: dict[str, str]) -> str:
    return f"""# Reproducibility checklist

- [x] Scientific question and promotion gates frozen before TEST.
- [x] Template-family-isolated train/DEV/TEST splits.
- [x] Minimal-pair counterfactual cases and explicit OOD set.
- [x] Deterministic seed `20260901`.
- [x] Pinned MiniLM model and revision.
- [x] Per-example raw and DEV-calibrated scores saved.
- [x] Confusion, PR-AUC, calibration, selective-risk and cost metrics saved.
- [x] Exact McNemar and 2,000-sample paired bootstrap reported.
- [x] Five MLP seeds reported separately.
- [x] Generated tables/plots derived from artifacts.
- [x] v1 frozen holdout not read by the v2 runner.
- [x] Runtime authority unchanged.
- [ ] Real merchant data validation (not available).
- [ ] Independent human annotation agreement (not available).
- [ ] External replication (not yet performed).

## Artifact hashes

{chr(10).join(f"- `{name}`: `{digest}`" for name, digest in paths.items())}
"""


def main() -> int:
    test = read(TEST_PATH)
    dev = read(DEV_PATH)
    analysis = read(ANALYSIS_PATH)
    frozen = read(FREEZE_PATH)
    v1 = read(V1_HOLDOUT_PATH)
    v1_audit = read(V1_AUDIT_PATH)
    write(PAPER / "generated/macros.tex", macros(test, analysis, v1))
    write(PAPER / "tables/main-results.tex", main_results(test))
    write(PAPER / "tables/family-slices.tex", slice_results(analysis))
    write(PAPER / "tables/calibration.tex", calibration_results(test, analysis))
    write(PAPER / "supplementary/error-examples.tex", error_examples(analysis))
    write(PAPER / "dataset-card.md", dataset_card(test, frozen))
    write(PAPER / "model-card.md", model_card(test))
    hashes = {
        "FECL v2 DEV": sha256(DEV_PATH),
        "FECL v2 freeze": sha256(FREEZE_PATH),
        "FECL v2 TEST": sha256(TEST_PATH),
        "FECL v2 post-hoc analysis": sha256(ANALYSIS_PATH),
        "v1 frozen holdout": sha256(V1_HOLDOUT_PATH),
        "v1 grounding audit": sha256(V1_AUDIT_PATH),
    }
    write(PAPER / "reproducibility-checklist.md", checklist(hashes))
    manifest = {
        "artifact_version": "fecl-paper-assets-v1",
        "inputs": hashes,
        "outputs": {
            path.relative_to(ROOT).as_posix(): sha256(path)
            for path in sorted((PAPER / "tables").glob("*"))
            if path.is_file()
        },
        "boundary": {
            "synthetic": True,
            "production_validated": False,
            "runtime_changed": False,
        },
        "dev_promotion": dev["promotion"],
        "test_promotion": test["promotion"],
        "v1_posthoc": v1_audit["post_hoc"],
    }
    write(PAPER / "generated/asset-manifest.json", json.dumps(manifest, indent=2, sort_keys=True))
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
