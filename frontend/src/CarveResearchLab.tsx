import { useEffect, useMemo, useState } from "react";

import {
  fetchCarveResearch,
  type CarveMetric,
  type CarveResearchResponse,
} from "./api";
import { formatMoney, humanizeToken } from "./format";
import { UnifiedNavigation } from "./components/UnifiedNavigation";
import "./carve-research.css";

const percent = (value: number) => `${(value * 100).toFixed(1)}%`;
const isMetric = (
  value: CarveMetric | { status: string },
): value is CarveMetric => "f1" in value;
const hashPreview = (value: string) =>
  `${value.slice(0, 12)}…${value.slice(-8)}`;

export function CarveResearchLab({ onBack }: { onBack: () => void }) {
  const [research, setResearch] = useState<CarveResearchResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [reload, setReload] = useState(0);
  const [modelId, setModelId] = useState("");
  const [showRepair, setShowRepair] = useState(false);

  useEffect(() => {
    let active = true;
    fetchCarveResearch()
      .then((value) => active && setResearch(value))
      .catch((reason: unknown) => {
        if (active)
          setError(
            reason instanceof Error
              ? reason.message
              : "Saved research artifact unavailable.",
          );
      });
    return () => {
      active = false;
    };
  }, [reload]);

  const models = useMemo(
    () =>
      Object.entries(research?.test.models ?? {}).filter(
        (entry): entry is [string, CarveMetric] => isMetric(entry[1]),
      ),
    [research],
  );
  const selected = models.find(([id]) => id === modelId) ?? models[0];

  return (
    <>
      <UnifiedNavigation
        currentRoute="research"
        onNavigate={(route) => {
          if (route === "proof") onBack();
          else window.location.href = `/${route}`;
        }}
      />
      <main className="research-page" id="research-main">
        <button type="button" className="text-button" onClick={onBack}>
          ← Evidence debugger
        </button>
        <header className="page-heading">
          <p className="page-kicker">Saved synthetic research</p>
          <h1>What was tested, retained, and rejected</h1>
          <p>
            This page reads hash-verified CARVE v4.5 artifacts. It reports model
            behavior on synthetic data and does not estimate merchant savings or
            production performance.
          </p>
        </header>

        {error && (
          <div className="inline-error" role="alert">
            <p>{error}</p>
            <button
              type="button"
              onClick={() => {
                setError(null);
                setReload((value) => value + 1);
              }}
            >
              Retry
            </button>
          </div>
        )}
        {!research && !error && <p role="status">Verifying saved artifacts…</p>}

        {research && selected && (
          <>
            <section
              className="research-section"
              aria-labelledby="boundary-title"
            >
              <div className="section-heading">
                <div>
                  <p className="section-index">01</p>
                  <h2 id="boundary-title">Evaluation boundary</h2>
                </div>
                <p>Frozen synthetic TEST · executed once</p>
              </div>
              <dl className="fact-list fact-list-five">
                {Object.entries(research.split_counts).map(([split, count]) => (
                  <div key={split}>
                    <dt>{humanizeToken(split)}</dt>
                    <dd>{count.toLocaleString()}</dd>
                  </div>
                ))}
              </dl>
              <details className="plain-details">
                <summary>Artifact provenance</summary>
                <dl className="provenance-list">
                  <div>
                    <dt>Benchmark</dt>
                    <dd>{research.benchmark_id}</dd>
                  </div>
                  <div>
                    <dt>DEV SHA-256</dt>
                    <dd title={research.dev_sha256}>
                      {hashPreview(research.dev_sha256)}
                    </dd>
                  </div>
                  <div>
                    <dt>TEST SHA-256</dt>
                    <dd title={research.test_sha256}>
                      {hashPreview(research.test_sha256)}
                    </dd>
                  </div>
                  <div>
                    <dt>Receipt SHA-256</dt>
                    <dd title={research.receipt_sha256}>
                      {hashPreview(research.receipt_sha256)}
                    </dd>
                  </div>
                </dl>
              </details>
            </section>

            <section
              className="research-section"
              aria-labelledby="models-title"
            >
              <div className="section-heading">
                <div>
                  <p className="section-index">02</p>
                  <h2 id="models-title">Model comparison</h2>
                </div>
                <label className="compact-control">
                  Inspect model
                  <select
                    value={selected[0]}
                    onChange={(event) => setModelId(event.target.value)}
                  >
                    {models.map(([id]) => (
                      <option key={id} value={id}>
                        {humanizeToken(id)}
                      </option>
                    ))}
                  </select>
                </label>
              </div>
              <div className="table-scroll">
                <table className="research-table">
                  <thead>
                    <tr>
                      <th>Candidate</th>
                      <th>Precision</th>
                      <th>Recall</th>
                      <th>F1</th>
                      <th>False pass</th>
                      <th>False block</th>
                    </tr>
                  </thead>
                  <tbody>
                    {models.map(([id, metric]) => (
                      <tr
                        key={id}
                        aria-current={id === selected[0] ? "true" : undefined}
                      >
                        <th>{humanizeToken(id)}</th>
                        <td>{percent(metric.precision)}</td>
                        <td>{percent(metric.recall)}</td>
                        <td>{metric.f1.toFixed(3)}</td>
                        <td>{metric.false_pass}</td>
                        <td>{metric.false_block}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <dl className="fact-list selected-model-summary">
                <div>
                  <dt>Selected</dt>
                  <dd>{humanizeToken(selected[0])}</dd>
                </div>
                <div>
                  <dt>PR AUC</dt>
                  <dd>{selected[1].pr_auc.toFixed(3)}</dd>
                </div>
                <div>
                  <dt>Calibration error</dt>
                  <dd>{selected[1].ece_10.toFixed(3)}</dd>
                </div>
                <div>
                  <dt>False-pass exposure</dt>
                  <dd>
                    {formatMoney(selected[1].false_pass_exposure_minor, "INR")}
                  </dd>
                </div>
              </dl>
              <p className="method-note">
                Exposure is a synthetic benchmark quantity. It is not observed
                loss, forecast revenue, or a production savings claim.
              </p>
            </section>

            <section className="research-section" aria-labelledby="case-title">
              <div className="section-heading">
                <div>
                  <p className="section-index">03</p>
                  <h2 id="case-title">One inspectable decision</h2>
                </div>
                <p>{research.evidence_case.case_id}</p>
              </div>
              <div className="evidence-comparison">
                <div>
                  <h3>Extracted source</h3>
                  <blockquote>
                    “{research.evidence_case.source_quote}”
                  </blockquote>
                  <p>
                    Exact span {research.evidence_case.source_span[0]}–
                    {research.evidence_case.source_span[1]}
                  </p>
                </div>
                <div>
                  <h3>Trusted state</h3>
                  <dl className="compact-facts">
                    <div>
                      <dt>Claimed</dt>
                      <dd>
                        {formatMoney(
                          research.evidence_case.claim_amount_minor,
                          research.evidence_case.currency,
                        )}
                      </dd>
                    </div>
                    <div>
                      <dt>Ledger</dt>
                      <dd>
                        {formatMoney(
                          research.evidence_case.authoritative_amount_minor,
                          research.evidence_case.currency,
                        )}
                      </dd>
                    </div>
                    <div>
                      <dt>Solver</dt>
                      <dd>
                        {research.evidence_case.certificate.solver_expected}
                      </dd>
                    </div>
                  </dl>
                </div>
              </div>
              <button
                type="button"
                className="secondary-button"
                aria-expanded={showRepair}
                onClick={() => setShowRepair((value) => !value)}
              >
                {showRepair ? "Hide repair" : "Show counterfactual repair"}
              </button>
              {showRepair && (
                <dl className="repair-diff">
                  <div>
                    <dt>Field</dt>
                    <dd>
                      {humanizeToken(
                        research.evidence_case.counterfactual_repair.field,
                      )}
                    </dd>
                  </div>
                  <div>
                    <dt>Observed</dt>
                    <dd>
                      {String(
                        research.evidence_case.counterfactual_repair.from,
                      )}
                    </dd>
                  </div>
                  <div>
                    <dt>Repaired</dt>
                    <dd>
                      {String(research.evidence_case.counterfactual_repair.to)}
                    </dd>
                  </div>
                </dl>
              )}
            </section>

            <section
              className="research-section limitations"
              aria-labelledby="limits-title"
            >
              <div className="section-heading">
                <div>
                  <p className="section-index">04</p>
                  <h2 id="limits-title">What this does not prove</h2>
                </div>
              </div>
              <p>
                The artifacts use synthetic cases. They do not validate live
                Razorpay traffic, issuer outcomes, production prevalence, or
                actual merchant loss. Learned candidates do not control money,
                submission, authorization, or final policy decisions.
              </p>
            </section>
          </>
        )}
      </main>
    </>
  );
}
