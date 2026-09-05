import { useEffect, useState } from "react";
import { ChartLine, Flask } from "@phosphor-icons/react";
import { fetchLatestEvaluation, type EvaluationResponse } from "./api";
import { TryVerifier } from "./TryVerifier";
import { humanizeToken as readable } from "./format";
import {
  UnifiedNavigation,
  type NavRoute,
} from "./components/UnifiedNavigation";
import { useTutorialActions } from "./tutorial";
import "./proof-console.css";

type View = "debugger" | "evaluation";
type Ratio = { numerator: number; denominator: number; value: number };
type Metrics = {
  material_conflict?: { precision?: Ratio; recall?: Ratio; f1?: number };
  operational?: {
    false_pass_block_cases?: number;
    false_block_nonblock_cases?: number;
    review_rate?: Ratio;
    auto_decision_coverage?: Ratio;
  };
  confusion_matrix?: Record<string, Record<string, number>>;
  slices?: Record<string, { total?: number; correct?: number }>;
  baseline_comparison?: Record<string, unknown>;
};

function percent(value: number | undefined): string {
  return value === undefined ? "N/A" : `${(value * 100).toFixed(1)}%`;
}

function ratio(value: Ratio | undefined): string {
  return value ? `${value.numerator}/${value.denominator}` : "N/A";
}

export function ProofConsole({
  onNavigate,
}: {
  onNavigate?: (route: string) => void;
} = {}) {
  const tutorial = useTutorialActions();

  const [view, setView] = useState<View>(() =>
    new URLSearchParams(window.location.search).get("view") === "evaluation"
      ? "evaluation"
      : "debugger",
  );

  const updateAppContext = tutorial?.updateAppContext;

  useEffect(() => {
    updateAppContext?.({
      evaluationView: view,
      activeTab: view,
    });
  }, [updateAppContext, view]);

  const [evaluation, setEvaluation] = useState<EvaluationResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [reload, setReload] = useState(0);

  useEffect(() => {
    if (view !== "evaluation" || evaluation) return;

    let active = true;
    fetchLatestEvaluation()
      .then((value) => {
        if (active) setEvaluation(value);
      })
      .catch((reason: unknown) => {
        if (active) {
          setError(
            reason instanceof Error
              ? reason.message
              : "Evaluation artifact unavailable.",
          );
        }
      });
    return () => {
      active = false;
    };
  }, [view, evaluation, reload]);

  const metrics =
    evaluation?.status === "MEASURED" ? (evaluation.metrics as Metrics) : null;
  const precision = metrics?.material_conflict?.precision;
  const recall = metrics?.material_conflict?.recall;
  const operational = metrics?.operational;
  const knownSlice = metrics?.slices?.partial_full_amount;

  function switchView(next: View) {
    setView(next);
    const url = new URL(window.location.href);
    if (next === "evaluation") url.searchParams.set("view", next);
    else url.searchParams.delete("view");
    window.history.replaceState({}, "", url);
  }
  function handleNav(
    route: NavRoute,
    nextView?: "debugger" | "evaluation" | "cases",
  ) {
    if (route === "evaluation" || nextView === "evaluation") {
      switchView("evaluation");
      return;
    }
    if (route === "proof" && (!nextView || nextView === "debugger")) {
      switchView("debugger");
      return;
    }
    if (onNavigate) {
      onNavigate(route);
    } else {
      const paths: Record<string, string> = {
        proof: "/proof",
        workspace: "/workspace",
        evaluation: "/proof?view=evaluation",
        research: "/research",
        "decision-engine": "/decision-engine",
        ai: "/decision-engine",
      };
      window.location.href = paths[route] ?? "/proof";
    }
  }

  return (
    <div className="proof-shell">
      <a className="skip-link" href="#proof-main">
        Skip to main content
      </a>
      <UnifiedNavigation
        currentRoute="proof"
        currentView={view}
        onNavigate={handleNav}
      />

      <main id="proof-main">
        {view === "debugger" ? (
          <TryVerifier />
        ) : (
          <section
            className="evaluation-page"
            aria-labelledby="evaluation-title"
          >
            <header>
              <p className="eyebrow">ARTIFACT-BACKED EVALUATION</p>
              <h1 id="evaluation-title">Held-out evaluation</h1>
              <p>
                Inspect measured conflict detection, false holds and missed
                conflicts. Results come from saved synthetic benchmark
                predictions; they do not measure merchant outcomes.
              </p>
            </header>

            {error && (
              <div className="safe-error" role="alert">
                <span>{error}</span>
                <button
                  type="button"
                  onClick={() => {
                    setError(null);
                    setReload((value) => value + 1);
                  }}
                >
                  Try again
                </button>
              </div>
            )}
            {!evaluation && !error && (
              <div className="evaluation-loading">
                Loading verified artifact…
              </div>
            )}
            {evaluation?.status === "NOT_YET_MEASURED" && (
              <div className="not-measured">
                <Flask aria-hidden="true" />
                <strong>NOT YET MEASURED</strong>
                <p>
                  Generate and save an evaluation artifact before publishing any
                  metric.
                </p>
              </div>
            )}
            {evaluation?.status === "MEASURED" && metrics && (
              <>
                <div className="synthetic-warning">
                  <Flask aria-hidden="true" />
                  <div>
                    <strong>Saved synthetic holdout</strong>
                    <p>{evaluation.synthetic_warning}</p>
                    <p>
                      These metrics describe the saved baseline, not the
                      repaired current runtime. Current changes have DEV
                      regression evidence only.
                    </p>
                  </div>
                </div>
                <section
                  className="metric-grid"
                  data-tour="metrics-summary"
                  aria-label="Measured conflict performance"
                >
                  <article>
                    <span>PRECISION</span>
                    <strong>{percent(precision?.value)}</strong>
                    <small>{ratio(precision)} verified BLOCK predictions</small>
                  </article>
                  <article>
                    <span>RECALL</span>
                    <strong>{percent(recall?.value)}</strong>
                    <small>{ratio(recall)} material conflicts caught</small>
                  </article>
                  <article>
                    <span>F1</span>
                    <strong>
                      {metrics.material_conflict?.f1?.toFixed(3) ?? "N/A"}
                    </strong>
                    <small>Harmonic mean, generated</small>
                  </article>
                  <article>
                    <span>FALSE PASS</span>
                    <strong>
                      {operational?.false_pass_block_cases ?? "0"}
                    </strong>
                    <small>Material conflicts missed</small>
                  </article>
                  <article>
                    <span>FALSE BLOCK</span>
                    <strong>
                      {operational?.false_block_nonblock_cases ?? "0"}
                    </strong>
                    <small>Non-block cases blocked</small>
                  </article>
                  <article>
                    <span>REVIEW RATE</span>
                    <strong>{percent(operational?.review_rate?.value)}</strong>
                    <small>
                      {ratio(operational?.review_rate)} cases routed to human
                      review
                    </small>
                  </article>
                </section>

                <section className="baseline-panel">
                  <div>
                    <ChartLine aria-hidden="true" />
                    <h2>Rules-only baseline is the selected system</h2>
                  </div>
                  <p>
                    The bounded B0 extractor remains selected. A model is not
                    promoted merely for sounding more intelligent; it must
                    improve measured safety on frozen data.
                  </p>
                  <dl>
                    <div>
                      <dt>Extractor</dt>
                      <dd>{readable(evaluation.system.extractor_id)}</dd>
                    </div>
                    <div>
                      <dt>Model</dt>
                      <dd>{readable(evaluation.system.model_id)}</dd>
                    </div>
                    <div>
                      <dt>Dataset</dt>
                      <dd>{readable(evaluation.dataset.dataset_id)}</dd>
                    </div>
                    <div>
                      <dt>Split</dt>
                      <dd>{evaluation.dataset.split.toUpperCase()}</dd>
                    </div>
                  </dl>
                </section>

                <section className="known-limit">
                  <span>KNOWN FAILURE SLICE</span>
                  <h2>Partial-vs-full refund language</h2>
                  <strong>
                    {knownSlice
                      ? `${knownSlice.correct ?? 0}/${knownSlice.total ?? 0} correct`
                      : "Not present in artifact"}
                  </strong>
                  <p>
                    This limitation stays visible because a clean aggregate can
                    conceal a costly semantic miss.
                  </p>
                </section>

                <footer className="artifact-proof">
                  <div>
                    <span>RUN</span>
                    <code>{evaluation.run_id}</code>
                  </div>
                  <div>
                    <span>DATASET SHA-256</span>
                    <code>{evaluation.dataset.manifest_sha256}</code>
                  </div>
                  <div>
                    <span>ARTIFACT SHA-256</span>
                    <code>{evaluation.artifact_sha256}</code>
                  </div>
                </footer>
              </>
            )}
          </section>
        )}
      </main>

      <footer className="proof-footer">
        <span>PASS ≠ dispute win · BLOCK ≠ legal verdict</span>
        <span>
          Semantic extraction supports · deterministic code verifies · humans
          retain financial authority
        </span>
      </footer>
    </div>
  );
}
