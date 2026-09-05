import { useEffect, useMemo, useState } from "react";

import {
  fetchAiLab,
  fetchAiResearch,
  fetchQueue,
  type AiLabResponse,
  type AiResearchResponse,
} from "./api";
import { humanizeToken } from "./format";
import { UnifiedNavigation } from "./components/UnifiedNavigation";
import "./carve-research.css";

const percent = (value: number | undefined) =>
  value === undefined ? "Not measured" : `${(value * 100).toFixed(1)}%`;

export function DecisionEnginePage({
  caseId,
  onBack,
  onWorkspace,
}: {
  caseId: string | null;
  onBack: () => void;
  onWorkspace: () => void;
}) {
  const [lab, setLab] = useState<AiLabResponse | null>(null);
  const [research, setResearch] = useState<AiResearchResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [reload, setReload] = useState(0);
  const [selectedModel, setSelectedModel] = useState("regex");
  const [selectedExample, setSelectedExample] = useState(0);

  useEffect(() => {
    let active = true;
    async function load() {
      try {
        const resolvedCaseId =
          caseId ?? (await fetchQueue("BLOCK", "")).items[0]?.case_id;
        if (!resolvedCaseId)
          throw new Error("No local held case is available for inspection.");
        const [caseResult, researchResult] = await Promise.all([
          fetchAiLab(resolvedCaseId),
          fetchAiResearch(),
        ]);
        if (active) {
          setLab(caseResult);
          setResearch(researchResult);
        }
      } catch (reason: unknown) {
        if (active)
          setError(
            reason instanceof Error
              ? reason.message
              : "Decision engine unavailable.",
          );
      }
    }
    void load();
    return () => {
      active = false;
    };
  }, [caseId, reload]);

  const artifact = research?.artifact;
  const models = useMemo(
    () =>
      artifact
        ? ([
            ["Rules", "regex", artifact.claim_extraction.regex_baseline],
            [
              "TF-IDF logistic",
              "tfidf",
              artifact.claim_extraction.tfidf.combined,
            ],
            [
              "MiniLM + logistic",
              "embedding",
              artifact.claim_extraction.embedding_logistic,
            ],
            ["Fixed ensemble", "ensemble", artifact.claim_extraction.ensemble],
            [
              "XGBoost stack",
              "xgboost",
              artifact.claim_extraction.xgboost_stack,
            ],
            [
              "XGBoost + hard negatives",
              "hard_negative",
              artifact.claim_extraction.xgboost_hard_negative,
            ],
          ] as const)
        : [],
    [artifact],
  );
  const model =
    models.find((candidate) => candidate[1] === selectedModel) ?? models[0];
  const example = artifact?.predictions[selectedExample];
  const score = example
    ? selectedModel === "regex"
      ? example.regex
      : selectedModel === "tfidf"
        ? example.tfidf_combined_probability
        : selectedModel === "embedding"
          ? example.embedding_probability
          : selectedModel === "ensemble"
            ? example.ensemble_probability
            : selectedModel === "hard_negative"
              ? example.xgboost_hard_negative_probability
              : example.xgboost_stack_probability
    : null;

  return (
    <>
      <UnifiedNavigation
        currentRoute="decision-engine"
        onNavigate={(route) => {
          if (route === "workspace") onWorkspace();
          else if (route === "proof") onBack();
          else window.location.href = `/${route}`;
        }}
      />
      <main
        className="research-page decision-page"
        id="decision-main"
        data-tour="decision-engine"
      >
        <button type="button" className="text-button" onClick={onBack}>
          ← Evidence debugger
        </button>
        <header className="page-heading">
          <p className="page-kicker">Decision boundary</p>
          <h1>Why the simpler extractor remains in control</h1>
          <p>
            Inspect the saved model comparison and one exact source example.
            Learned scores remain research evidence; money checks and gate
            decisions stay deterministic.
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
        {(!lab || !artifact) && !error && (
          <p role="status">Loading saved decision evidence…</p>
        )}

        {lab && artifact && model && (
          <>
            <section
              className="research-section"
              aria-labelledby="promotion-title"
            >
              <div className="section-heading">
                <div>
                  <p className="section-index">01</p>
                  <h2 id="promotion-title">Promotion decision</h2>
                </div>
                <p>DEV · generated {artifact.created_at.slice(0, 10)}</p>
              </div>
              <dl className="fact-list">
                <div>
                  <dt>Decision</dt>
                  <dd>{humanizeToken(artifact.promotion.extractor_status)}</dd>
                </div>
                <div>
                  <dt>Runtime extractor</dt>
                  <dd>{artifact.promotion.selected_runtime_extractor}</dd>
                </div>
                <div>
                  <dt>Inspected case</dt>
                  <dd>{lab.case_id}</dd>
                </div>
                <div>
                  <dt>Authority</dt>
                  <dd>Deterministic policy</dd>
                </div>
              </dl>
            </section>

            <section
              className="research-section"
              aria-labelledby="comparison-title"
            >
              <div className="section-heading">
                <div>
                  <p className="section-index">02</p>
                  <h2 id="comparison-title">Leakage-safe comparison</h2>
                </div>
                <p>{artifact.dataset.sentence_examples} sentence examples</p>
              </div>
              <div className="table-scroll">
                <table className="research-table">
                  <thead>
                    <tr>
                      <th>Candidate</th>
                      <th>Precision</th>
                      <th>Recall</th>
                      <th>F1</th>
                      <th>Decision</th>
                    </tr>
                  </thead>
                  <tbody>
                    {models.map(([name, id, candidate]) => (
                      <tr
                        key={id}
                        aria-current={id === "regex" ? "true" : undefined}
                      >
                        <th>{name}</th>
                        <td>{percent(candidate.metrics.precision)}</td>
                        <td>{percent(candidate.metrics.recall)}</td>
                        <td>{percent(candidate.metrics.f1)}</td>
                        <td>{id === "regex" ? "Retained" : "Rejected"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>

            <section
              className="research-section"
              aria-labelledby="example-title"
            >
              <div className="section-heading">
                <div>
                  <p className="section-index">03</p>
                  <h2 id="example-title">Inspect an exact example</h2>
                </div>
                <div className="inline-controls">
                  <label className="compact-control">
                    Model
                    <select
                      value={selectedModel}
                      onChange={(event) => setSelectedModel(event.target.value)}
                    >
                      {models.map(([name, id]) => (
                        <option value={id} key={id}>
                          {name}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label className="compact-control">
                    Case
                    <select
                      value={selectedExample}
                      onChange={(event) =>
                        setSelectedExample(Number(event.target.value))
                      }
                    >
                      {artifact.predictions.slice(0, 40).map((item, index) => (
                        <option value={index} key={item.example_id}>
                          {item.family} · {item.example_id}
                        </option>
                      ))}
                    </select>
                  </label>
                </div>
              </div>
              {example && (
                <div className="evidence-comparison">
                  <div>
                    <h3>Exact source sentence</h3>
                    <blockquote>“{example.text}”</blockquote>
                    <p>{example.example_id}</p>
                  </div>
                  <div>
                    <h3>Observed output</h3>
                    <dl className="compact-facts">
                      <div>
                        <dt>Model</dt>
                        <dd>{model[0]}</dd>
                      </div>
                      <div>
                        <dt>Output</dt>
                        <dd>
                          {(score ?? 0) >= 0.5
                            ? "Processed claim"
                            : "No claim / abstain"}
                        </dd>
                      </div>
                      <div>
                        <dt>Labeled truth</dt>
                        <dd>
                          {example.label
                            ? "Processed claim"
                            : "No processed claim"}
                        </dd>
                      </div>
                      <div>
                        <dt>Agreement</dt>
                        <dd>
                          {Number((score ?? 0) >= 0.5) === example.label
                            ? "Match"
                            : "Error"}
                        </dd>
                      </div>
                    </dl>
                  </div>
                </div>
              )}
              <p className="method-note">
                The score is shown only to reproduce the experiment. It cannot
                change a payment, submit a dispute, or override the
                deterministic gate.
              </p>
            </section>

            <section
              className="research-section limitations"
              aria-labelledby="authority-title"
            >
              <div className="section-heading">
                <div>
                  <p className="section-index">04</p>
                  <h2 id="authority-title">Operational authority</h2>
                </div>
              </div>
              <p>
                Semantic models may nominate an exact quote for inspection.
                Local code verifies grounding, identifiers, currency, integer
                minor units, ledger completeness, and contradictions. A human
                retains the consequential workflow decision.
              </p>
              <button
                className="secondary-button"
                type="button"
                onClick={onWorkspace}
              >
                Open analyst queue
              </button>
            </section>
          </>
        )}
      </main>
    </>
  );
}
