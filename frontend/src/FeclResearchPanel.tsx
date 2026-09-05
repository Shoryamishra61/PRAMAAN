import { useMemo, useState } from "react";
import { ArrowsLeftRight } from "@phosphor-icons/react";

import type { FeclV2Response } from "./api";

const displayName = (value: string) =>
  value
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");

const percent = (value: number) => `${(value * 100).toFixed(1)}%`;

export function FeclResearchPanel({ research }: { research: FeclV2Response }) {
  const modelEntries = Object.entries(research.test.models);
  const [modelId, setModelId] = useState("neuro_symbolic");
  const [caseId, setCaseId] = useState(
    research.test.predictions[0]?.case_id ?? "",
  );
  const model = research.test.models[modelId] ?? modelEntries[0]?.[1];
  const evidence =
    research.test.predictions.find((item) => item.case_id === caseId) ??
    research.test.predictions[0];
  const counterfactual = useMemo(
    () =>
      research.test.predictions.find(
        (item) => item.case_id === evidence?.counterfactual_case_id,
      ),
    [evidence, research.test.predictions],
  );
  if (!model || !evidence) return null;
  const metrics = model.calibrated_metrics;
  const score =
    evidence.calibrated_scores[modelId] ?? evidence.scores[modelId] ?? 0;
  const pairedScore = counterfactual
    ? (counterfactual.calibrated_scores[modelId] ??
      counterfactual.scores[modelId] ??
      0)
    : null;
  const predicted = score >= 0.5;
  const counterfactualStats = research.analysis.counterfactual_pairs[modelId];
  const calibration = research.analysis.calibration_delta[modelId];

  return (
    <section className="fecl-lab" aria-labelledby="fecl-title">
      <div className="fecl-heading">
        <div>
          <h2 id="fecl-title">Holdout evaluation under cross-family shift</h2>
          <p>
            Once-opened holdout evaluation. Authoritative ledger checks retain
            decision authority; switching candidate models changes only the
            research prediction.
          </p>
        </div>
        <div className="fecl-status">
          <span>{research.test.promotion.status.replaceAll("_", " ")}</span>
          <strong className="product-mono">
            {research.test.promotion.selected_runtime}
          </strong>
        </div>
      </div>

      <div className="fecl-controls">
        <label>
          Research model
          <select
            name="research_model"
            autoComplete="off"
            value={modelId}
            onChange={(event) => setModelId(event.target.value)}
          >
            {modelEntries.map(([id]) => (
              <option value={id} key={id}>
                {displayName(id)}
              </option>
            ))}
          </select>
        </label>
        <label>
          Frozen evidence pair
          <select
            name="frozen_evidence_pair"
            autoComplete="off"
            value={caseId}
            onChange={(event) => setCaseId(event.target.value)}
          >
            {research.test.predictions.map((item) => (
              <option value={item.case_id} key={item.case_id}>
                {item.family} · {item.phenomenon} · {item.case_id}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div
        className="fecl-metrics"
        aria-label={`${displayName(modelId)} frozen metrics`}
      >
        <div>
          <span>Precision</span>
          <strong>{percent(metrics.precision)}</strong>
        </div>
        <div>
          <span>Recall</span>
          <strong>{percent(metrics.recall)}</strong>
        </div>
        <div>
          <span>F1</span>
          <strong>{metrics.f1.toFixed(3)}</strong>
        </div>
        <div>
          <span>False PASS</span>
          <strong>{metrics.false_pass}</strong>
        </div>
        <div>
          <span>False BLOCK</span>
          <strong>{metrics.false_block}</strong>
        </div>
        <div>
          <span>Cost / case</span>
          <strong>{metrics.expected_loss_per_case.toFixed(3)}</strong>
        </div>
      </div>

      <div className="fecl-debugger">
        <article className="fecl-evidence">
          <span>01 · EXACT EVIDENCE</span>
          <blockquote>“{evidence.communication}”</blockquote>
          <code>{evidence.case_id}</code>
        </article>
        <article className="fecl-claim">
          <span>02 · AI-DERIVED CLAIM</span>
          <strong>{evidence.semantic_state_prediction.toUpperCase()}</strong>
          <p>
            {displayName(modelId)} · calibrated score {score.toFixed(3)}
          </p>
        </article>
        <article className="fecl-ledger">
          <span>03 · DETERMINISTIC TRUTH</span>
          <strong>{evidence.ledger.status.toUpperCase()}</strong>
          <p>
            {evidence.ledger.currency} {evidence.ledger.amount} ·{" "}
            {evidence.ledger.event_date}
          </p>
        </article>
        <article
          className={predicted ? "fecl-result fecl-block" : "fecl-result"}
        >
          <span>04 · RESEARCH PREDICTION</span>
          <strong>{predicted ? "CONTRADICTION" : "CONSISTENT"}</strong>
          <p>
            {predicted === Boolean(evidence.label)
              ? "MATCHES LABEL"
              : "MODEL ERROR"}
          </p>
        </article>
      </div>

      {counterfactual && (
        <div className="fecl-counterfactual">
          <ArrowsLeftRight size={22} />
          <div>
            <span>CAUSAL COUNTERFACTUAL</span>
            <strong>“{counterfactual.communication}”</strong>
            <small>
              Score {pairedScore?.toFixed(3)} · expected label{" "}
              {counterfactual.label} · same pair {counterfactual.pair_id}
            </small>
          </div>
          <div>
            <span>BOTH CORRECT</span>
            <strong>
              {counterfactualStats
                ? percent(counterfactualStats.both_correct_rate)
                : "n/a"}
            </strong>
            <small>across all frozen pairs</small>
          </div>
        </div>
      )}

      <div className="fecl-safety">
        <div>
          <span>Combined OOD rejection</span>
          <strong>
            {percent(research.test.ood.combined_safe_controller_rejection_rate)}
          </strong>
          <small>
            Learned-only:{" "}
            {percent(research.test.ood.learned_only_rejection_rate)} of{" "}
            {research.test.ood.count}
          </small>
        </div>
        <div>
          <span>Calibration result</span>
          <strong>
            {calibration && calibration.brier_delta > 0
              ? "Brier worsened"
              : "Brier improved"}
          </strong>
          <small>
            {calibration
              ? `ΔBrier ${calibration.brier_delta.toFixed(3)} · ΔECE ${calibration.ece_delta.toFixed(3)}`
              : "not probabilistic"}
          </small>
        </div>
        <div>
          <span>Artifact lineage</span>
          <strong>Generated · no tuning</strong>
          <small className="product-mono">
            {research.test_sha256.slice(0, 16)}…
          </small>
        </div>
      </div>
    </section>
  );
}
