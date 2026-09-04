"""Automated Quality Assurance for CARVE-FECL Research Evaluation Suite."""

from __future__ import annotations

import json
from pathlib import Path

from evaluation.ablations import run_ablation_benchmarks
from evaluation.causal_pairs import evaluate_causal_robustness
from evaluation.cost_analysis import compute_expected_cost, compute_pareto_frontier
from evaluation.evaluate import run_full_evaluation
from evaluation.ood_eval import evaluate_ood_robustness
from evaluation.subgroup_analysis import evaluate_subgroups

ROOT = Path(__file__).resolve().parents[2]


def test_research_artifacts_exist_and_parse() -> None:
    results_path = ROOT / "research/final_results.json"
    assert results_path.exists()
    data = json.loads(results_path.read_text(encoding="utf-8"))
    assert data["primary_hypothesis_result"]["status"] == "CONFIRMED"
    assert len(data["baseline_ladder"]) >= 6

    protocol_path = ROOT / "research/protocol.md"
    assert protocol_path.exists()

    prior_art_path = ROOT / "research/prior_art_matrix.md"
    assert prior_art_path.exists()

    hypotheses_path = ROOT / "research/hypotheses.md"
    assert hypotheses_path.exists()

    registry_path = ROOT / "research/experiment_registry.jsonl"
    assert registry_path.exists()
    lines = registry_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) >= 6


def test_data_cards_and_manifests_exist() -> None:
    data_card = ROOT / "data/DATA_CARD.md"
    assert data_card.exists()

    generator_cfg = ROOT / "data/generator_config.yaml"
    assert generator_cfg.exists()

    split_manifest = ROOT / "data/split_manifest.json"
    assert split_manifest.exists()
    splits = json.loads(split_manifest.read_text(encoding="utf-8"))["splits"]
    assert "train" in splits
    assert "final_test" in splits


def test_model_card_and_limitations_exist() -> None:
    model_card = ROOT / "docs/MODEL_CARD.md"
    assert model_card.exists()

    limitations = ROOT / "docs/LIMITATIONS.md"
    assert limitations.exists()

    research_report = ROOT / "docs/RESEARCH_REPORT.md"
    assert research_report.exists()


def test_causal_robustness_evaluation() -> None:
    scorecard = evaluate_causal_robustness(limit=10)
    assert scorecard.nuisance_invariance >= 0.90
    assert scorecard.total_pairs_evaluated > 0


def test_cost_analysis_and_pareto() -> None:
    decisions = ["BLOCK"] * 10 + ["REVIEW"] * 20 + ["PASS"] * 30
    truth = [1] * 10 + [1] * 5 + [0] * 15 + [0] * 30
    cost_res = compute_expected_cost(decisions, truth)
    assert cost_res.expected_cost_per_case >= 0.0
    assert 0.0 <= cost_res.coverage <= 1.0

    probs = [0.05, 0.2, 0.45, 0.75, 0.95]
    frontier = compute_pareto_frontier(probs, [0, 0, 1, 1, 1])
    assert len(frontier) > 0


def test_ood_evaluation() -> None:
    res = evaluate_ood_robustness()
    assert res.auroc >= 0.80
    assert res.review_routing_rate >= 0.80


def test_subgroup_analysis() -> None:
    sample_cases = [
        {"amount_minor": 50000, "ledger_complete": True, "decision": "BLOCK", "label": 1},
        {"amount_minor": 499900, "ledger_complete": True, "decision": "PASS", "label": 0},
    ]
    metrics = evaluate_subgroups(sample_cases)
    assert "amount_tiers" in metrics
    assert "evidence_completeness" in metrics


def test_ablation_benchmarks() -> None:
    summary = run_ablation_benchmarks()
    assert "with_mcc_supervision" in summary.mcc_study
    assert "learned_plus_z3 (B9/B10)" in summary.formal_smt_study
    assert "temperature_scaling" in summary.calibration_study
    assert "greedy_voi" in summary.active_acquisition_study


def test_unified_eval_runner() -> None:
    out = run_full_evaluation()
    assert out["benchmark_id"] == "DIG-RNP-SYN-V1"
    assert "causal_minimal_pairs" in out


def test_v2_research_artifacts_and_scaling() -> None:
    curves_path = ROOT / "research/learning_curves.json"
    assert curves_path.exists()
    curves = json.loads(curves_path.read_text(encoding="utf-8"))
    assert "B10" in curves
    assert "B2" in curves
    assert len(curves["B10"]["trajectory"]) == 11

    eff_path = ROOT / "research/sample_efficiency.json"
    assert eff_path.exists()
    eff = json.loads(eff_path.read_text(encoding="utf-8"))
    assert "finding" in eff

    scaling_path = ROOT / "research/data_scaling_fit.json"
    assert scaling_path.exists()


def test_monte_carlo_merchant_economics() -> None:
    mc_path = ROOT / "research/merchant_monte_carlo.json"
    assert mc_path.exists()
    mc = json.loads(mc_path.read_text(encoding="utf-8"))
    assert mc["status"] == "PROJECTED / MODELED MERCHANT ECONOMICS"
    assert mc["projected_net_merchant_edge_inr"]["p50_median"] > 0
    assert mc["probability_net_edge_positive"] >= 0.95


def test_crossgen_and_document_benchmarks() -> None:
    crossgen_path = ROOT / "research/cross_generator_results.json"
    assert crossgen_path.exists()
    cg = json.loads(crossgen_path.read_text(encoding="utf-8"))
    assert cg["sample_size"] == 5000

    doc_path = ROOT / "research/document_benchmarks.json"
    assert doc_path.exists()
    docs = json.loads(doc_path.read_text(encoding="utf-8"))
    assert len(docs["datasets"]) >= 3


def test_human_blind_pack_and_rule_holdout() -> None:
    rule_path = ROOT / "research/rule_holdout.json"
    assert rule_path.exists()
    rule = json.loads(rule_path.read_text(encoding="utf-8"))
    assert rule["formal_smt_rule_re_enabled"]["precision"] == 1.000

    human_manifest = ROOT / "external_validation/blind_manifest.json"
    assert human_manifest.exists()
    hm = json.loads(human_manifest.read_text(encoding="utf-8"))
    assert hm["status"] == "PENDING_EXTERNAL_VALIDATION"
