import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import { afterEach, beforeEach, expect, test, vi } from "vitest";

import { App } from "./App";

const queueItem = {
  case_id: "case_block",
  dispute_id: "disp_block",
  payment_id: "pay_block",
  amount_minor: 250000,
  currency: "INR",
  respond_by: "2026-09-01T12:00:00Z",
  raw_reason_code: "raw_refund_reason",
  reason_profile: "refund_not_processed_v1",
  processing_status: "READY",
  gate_status: "BLOCK",
  primary_reason_code: "F_REFUND_AMOUNT_MISMATCH",
};

const caseDetail = {
  case: queueItem,
  workflow_status: "REVIEW_PENDING",
  payment_snapshot: {
    payment_id: "pay_block",
    captured_amount_minor: 250000,
    currency: "INR",
    captured_at: "2026-08-20T10:00:00Z",
    snapshot_complete: true,
  },
  refunds: [
    {
      id: "rfnd_1",
      payment_id: "pay_block",
      amount_minor: 100000,
      currency: "INR",
      local_status: "processed",
      reference: "RF-1",
    },
  ],
  evidence_documents: [
    {
      id: "doc_1",
      source_type: "customer_communication",
      source_system: "synthetic_fixture",
      media_type: "text/plain",
      canonical_text: "Your INR 2,500 refund was processed.",
      content_sha256: "a".repeat(64),
      captured_at: null,
      ingested_at: "2026-08-23T12:00:00Z",
      is_complete_source: true,
    },
  ],
  grounded_claims: [
    {
      id: "claim_1",
      document_id: "doc_1",
      claim_type: "refund_claimed_processed",
      raw_value: "INR 2,500",
      amount_minor: 250000,
      currency: "INR",
      refund_reference: null,
      modality: "assertion",
      source_quote: "Your INR 2,500 refund was processed.",
      span_start: 0,
      span_end: 36,
      grounding_status: "GROUNDED",
    },
  ],
  findings: [
    {
      id: "finding_1",
      rule_code: "F_REFUND_AMOUNT_MISMATCH",
      severity: "material",
      decision_effect: "BLOCK",
      explanation:
        "The grounded processed amount differs from the processed ledger total.",
      structured_refs: ["rfnd_1"],
      claim_refs: ["claim_1"],
    },
  ],
  gate_decision: { status: "BLOCK" },
  audit_events: [],
};

beforeEach(() => {
  vi.stubGlobal(
    "fetch",
    vi.fn((input: string | URL | Request) => {
      const url = String(input);
      const payload = url.endsWith("/case_block")
        ? caseDetail
        : { items: [queueItem], next_cursor: null };
      return Promise.resolve(
        new Response(JSON.stringify(payload), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      );
    }),
  );
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

test("opens on the evidence debugger, exercises safe break cases, repairs the ledger, and loads generated evaluation", async () => {
  const proofEvaluation = {
    status: "MEASURED",
    run_id: "holdout-final",
    created_at: "2026-08-23T12:00:00Z",
    synthetic_warning: "Synthetic benchmark performance.",
    dataset: {
      dataset_id: "DIG-RNP-SYN-v1",
      generator_version: "1.0.0",
      split: "holdout",
      synthetic: true,
      manifest_sha256: "b".repeat(64),
    },
    system: {
      system_version: "deterministic-v1",
      extractor_id: "regex-baseline-v1",
      model_id: null,
      prompt_version: "not-applicable-regex-v1",
      claim_schema_version: "1.0",
      config_sha256: "a".repeat(64),
      code_commit: "UNAVAILABLE_NOT_A_GIT_REPOSITORY",
    },
    metrics: {
      material_conflict: {
        precision: { numerator: 10, denominator: 10, value: 1 },
        recall: { numerator: 10, denominator: 20, value: 0.5 },
        f1: 0.6667,
      },
      operational: {
        review_rate: { numerator: 20, denominator: 60, value: 1 / 3 },
        auto_decision_coverage: {
          numerator: 40,
          denominator: 60,
          value: 2 / 3,
        },
        false_pass_block_cases: 10,
        false_block_nonblock_cases: 0,
      },
      confusion_matrix: {
        BLOCK: { BLOCK: 10, PASS: 10, REVIEW: 0 },
        PASS: { BLOCK: 0, PASS: 20, REVIEW: 0 },
        REVIEW: { BLOCK: 0, PASS: 0, REVIEW: 20 },
      },
    },
    artifact_sha256: "c".repeat(64),
  };
  const proofLab = {
    case_id: "case_block",
    boundary: {
      runtime: "LOCAL_OFFLINE",
      dataset_split: "DEV",
      synthetic: true,
      holdout_accessed: false,
      external_api_calls: false,
      gate_authority: false,
      probability_exposed: false,
    },
    model: {
      model_id: "local-tfidf-logreg-processed-v1",
      architecture: "word+character TF-IDF with logistic regression",
      evaluation: "5-fold scenario-family-grouped out-of-fold predictions",
      promotion_status: "NOT_PROMOTED",
      promotion_rule:
        "candidate F1 must exceed regex F1 without reducing precision",
      selected_extractor: "regex-baseline-v1",
      candidate_metrics: {
        precision: 0.813953,
        recall: 0.972222,
        f1: 0.886076,
        confusion: { tn: 32, fp: 16, fn: 2, tp: 70 },
      },
      comparator_metrics: {
        precision: 1,
        recall: 1,
        f1: 1,
        confusion: { tn: 48, fp: 0, fn: 0, tp: 72 },
      },
      nominations: [
        {
          claim_type: "refund_claimed_processed",
          source_quote: "Your INR 2,500 refund was processed.",
          feature_contributions: [
            {
              feature: "word__processed",
              contribution: 0.4,
              direction: "supports",
            },
          ],
        },
      ],
    },
    retrieval: {
      method: "LOCAL_TFIDF_EXACT_CITATIONS",
      corpus_sha256: "d".repeat(64),
      guidance_only: true,
      citations: [],
    },
  };
  vi.stubGlobal(
    "fetch",
    vi.fn((input: string | URL | Request, init?: RequestInit) => {
      const url = String(input);
      let payload: object;
      if (url.endsWith("/sandbox/evaluate")) {
        const request = JSON.parse(String(init?.body)) as {
          raw_reason_code: string;
          payment_amount_inr: string;
          customer_communication: string;
          refund_ledger_complete: boolean;
          refund_status: string;
          refund_amount_inr: string | null;
          simulation?: string;
        };
        if (request.payment_amount_inr === "4999.999") {
          return Promise.resolve(
            new Response(JSON.stringify({ detail: "invalid money" }), {
              status: 422,
            }),
          );
        }
        const contradictory =
          request.customer_communication.includes("have not processed");
        const status =
          request.simulation === "model_outage" ||
          contradictory ||
          !request.refund_ledger_complete
            ? "REVIEW"
            : request.refund_status === "processed" &&
                request.refund_amount_inr === request.payment_amount_inr
              ? "PASS"
              : "BLOCK";
        const finding =
          status === "PASS"
            ? []
            : [
                {
                  code:
                    status === "REVIEW"
                      ? request.simulation === "model_outage"
                        ? "F_MODEL_UNAVAILABLE"
                        : contradictory
                          ? "F_CONTRADICTORY_COMMUNICATION"
                          : "F_STRUCTURED_STATE_INCOMPLETE"
                      : request.refund_status === "processed"
                        ? "F_REFUND_AMOUNT_MISMATCH"
                        : "F_REFUND_CLAIM_NO_LEDGER_MATCH",
                  effect: status,
                  summary:
                    status === "REVIEW"
                      ? "Trusted payment or refund state is incomplete."
                      : "Grounded communication says a refund was processed, but the complete ledger has no match.",
                  evidence_refs: ["claim:claim_custom"],
                },
              ];
        payload = {
          run_id: "sandbox_custom",
          request_sha256: "a".repeat(64),
          raw_reason_code: request.raw_reason_code,
          profile_id: "refund_not_processed_v1",
          status,
          semantic_status: "SUCCESS",
          claims: [
            {
              claim_id: "claim_custom",
              claim_type: "refund_claimed_processed",
              source_quote: "Your refund of INR 4,999 was processed.",
              span_start: 0,
              span_end: 36,
              grounding_status: "GROUNDED",
              amount_minor: 499900,
              currency: "INR",
              normalization_status: "RESOLVED",
            },
          ],
          findings: finding,
          ledger: {
            payment_id: "pay_custom",
            payment_amount_minor: 499900,
            currency: "INR",
            refund_ledger_complete: request.refund_ledger_complete,
            refund_status: request.refund_status,
            refund_amount_minor: request.refund_amount_inr
              ? Number(request.refund_amount_inr) * 100
              : null,
          },
          proof: {
            status:
              status === "BLOCK"
                ? "UNSAT"
                : status === "REVIEW"
                  ? "INCOMPLETE"
                  : "SAT",
            constraints: [
              {
                constraint_id: "C_SUPPORTED_FACTS_CONSISTENT",
                layer: "INVARIANT",
                expression:
                  "grounded refund claim agrees with authoritative refund state",
                state:
                  status === "BLOCK"
                    ? "UNSAT"
                    : status === "REVIEW"
                      ? "INCOMPLETE"
                      : "SAT",
              },
            ],
            certificate: null,
            model_override_allowed: false,
          },
          next_evidence:
            status === "REVIEW"
              ? {
                  action: "REQUEST_REFUND_EXPORT",
                  evidence_id: "refund_state",
                  acquisition_cost: 1,
                  reason:
                    "A complete authoritative refund export is the minimum evidence needed.",
                }
              : null,
          comparison: {
            semantic_output: "GROUNDED_RELATION",
            deterministic_output: status,
            relationship:
              status === "REVIEW" ? "SAFE_ABSTENTION" : "DIVISION_OF_AUTHORITY",
            uncertainty_basis: "VERIFICATION_COMPLETENESS",
            probability_exposed: false,
          },
          boundary: {
            runtime: "LOCAL_OFFLINE",
            ephemeral: true,
            synthetic_input: true,
            external_api_calls: false,
            razorpay_write_performed: false,
            persisted: false,
            holdout_accessed: false,
            extractor_id: "regex-baseline-v1",
            gate_authority: "DETERMINISTIC_POLICY",
          },
          disclaimer: "Decision support only.",
        };
      } else if (url.endsWith("/evaluation/latest")) {
        payload = proofEvaluation;
      } else if (url.includes("/ai-lab/")) {
        payload = proofLab;
      } else if (url.endsWith("/case_block")) {
        payload = caseDetail;
      } else {
        payload = { items: [queueItem], next_cursor: null };
      }
      return Promise.resolve(
        new Response(JSON.stringify(payload), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      );
    }),
  );
  render(<App />);

  expect(
    screen.getByRole("heading", {
      name: "See exactly why a dispute case is safe or flagged.",
    }),
  ).toBeVisible();
  expect(
    screen.getByRole("button", { name: /Wrong refund amount/ }),
  ).toHaveAttribute("aria-pressed", "true");
  fireEvent.click(screen.getByRole("button", { name: "Check this case" }));
  expect(
    await screen.findByRole("heading", {
      name: "Understand the customer’s claim",
    }),
  ).toBeVisible();
  fireEvent.click(screen.getByRole("button", { name: /See the decision/ }));
  expect(screen.getByText(/Expected BLOCK; observed BLOCK/)).toBeVisible();
  fireEvent.click(screen.getByRole("button", { name: "Try another case" }));
  fireEvent.click(screen.getByRole("button", { name: /Missing ledger entry/ }));
  fireEvent.click(screen.getByRole("button", { name: "Check this case" }));
  await screen.findByRole("heading", {
    name: "Understand the customer’s claim",
  });
  fireEvent.click(screen.getByRole("button", { name: /See the decision/ }));
  expect(
    await screen.findByText(/Expected REVIEW; observed REVIEW/),
  ).toBeVisible();
  fireEvent.click(
    screen.getByRole("button", {
      name: "Simulate repaired ledger & rerun",
    }),
  );
  expect(
    (await screen.findAllByText("Refund amount does not match"))[0],
  ).toBeVisible();
  expect(
    screen.getByText("BLOCK", { selector: ".decision-summary > span" }),
  ).toBeVisible();
  expect(
    screen.queryByText("Inspect the contradiction certificate"),
  ).not.toBeInTheDocument();

  fireEvent.click(screen.getByRole("button", { name: "Try another case" }));
  fireEvent.click(screen.getByRole("button", { name: /Malformed evidence/ }));
  fireEvent.click(screen.getByRole("button", { name: "Check this case" }));
  expect(
    await screen.findByText(
      /Payment amounts can have at most 2 decimal places/,
    ),
  ).toBeVisible();

  fireEvent.click(screen.getByRole("button", { name: "Generated evaluation" }));
  expect(
    await screen.findByRole("heading", {
      name: "Held-out evaluation",
    }),
  ).toBeVisible();
  expect(screen.getByText("50.0%")).toBeVisible();
  expect(screen.getByText("Regex-Baseline-V1")).toBeVisible();
  expect(
    screen.getByText(
      "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
    ),
  ).toBeVisible();
});

test("shows the generated DEV tournament and exact evidence switching", async () => {
  const labResponse = {
    case_id: "case_block",
    boundary: {
      runtime: "LOCAL_OFFLINE",
      dataset_split: "DEV",
      synthetic: true,
      holdout_accessed: false,
      external_api_calls: false,
      gate_authority: false,
      probability_exposed: false,
    },
    model: {
      model_id: "local-tfidf-logreg-processed-v1",
      architecture:
        "word+character TF-IDF with class-weighted logistic regression",
      evaluation: "5-fold scenario-family-grouped out-of-fold predictions",
      promotion_status: "NOT_PROMOTED",
      promotion_rule:
        "candidate F1 must exceed regex F1 without reducing precision",
      selected_extractor: "regex-baseline-v1",
      candidate_metrics: {
        precision: 0.813953,
        recall: 0.972222,
        f1: 0.886076,
        confusion: { tn: 32, fp: 16, fn: 2, tp: 70 },
      },
      comparator_metrics: {
        precision: 1,
        recall: 1,
        f1: 1,
        confusion: { tn: 48, fp: 0, fn: 0, tp: 72 },
      },
      nominations: [
        {
          claim_type: "refund_claimed_processed",
          source_quote: "Your INR 2,500 refund was processed.",
          feature_contributions: [
            {
              feature: "word__processed",
              contribution: 0.4,
              direction: "supports",
            },
          ],
        },
      ],
    },
    retrieval: {
      method: "LOCAL_TFIDF_EXACT_CITATIONS",
      corpus_sha256: "b".repeat(64),
      guidance_only: true,
      citations: [
        {
          rank: 1,
          source_path: "docs/00-SOURCE-OF-TRUTH.md",
          section: "Gate status semantics / REVIEW",
          exact_excerpt: "REVIEW is the universal fail-safe for uncertainty.",
        },
      ],
    },
  };
  const metric = (precision: number, recall: number, f1: number) => ({
    metrics: {
      precision,
      recall,
      f1,
      confusion: { tn: 461, fp: 2, fn: 0, tp: 70 },
    },
    calibration: {
      brier: 0.06,
      ece_5: 0.04,
      nll: 0.25,
      bins: [{ mean_probability: 0.1, positive_rate: 0.05, count: 100 }],
    },
    risk_coverage: { aurc: 0.04, points: [{ coverage: 0.8, risk: 0.02 }] },
    precision_recall_curve: {
      average_precision: 0.9,
      points: [{ precision: 0.9, recall: 0.8 }],
    },
  });
  const researchResponse = {
    artifact_sha256: "d".repeat(64),
    generated: true,
    artifact: {
      created_at: "2026-09-01T00:00:00Z",
      boundary: {
        split: "DEV_GROUPED_OOF",
        holdout_accessed: false,
        gate_authority: false,
      },
      dataset: { sentence_examples: 533, positive_sentences: 70 },
      promotion: {
        extractor_status: "NOT_PROMOTED",
        selected_runtime_extractor: "regex-baseline-v1",
        nli_status: "RETAINED_EXPERIMENTAL",
      },
      claim_extraction: {
        regex_baseline: metric(0.972222, 1, 0.985915),
        tfidf: {
          word: metric(0.64, 0.69, 0.66),
          char: metric(0.63, 0.86, 0.73),
          combined: metric(0.64, 0.69, 0.66),
        },
        embedding_logistic: metric(0.73, 0.91, 0.81),
        ensemble: metric(0.73, 0.91, 0.81),
        xgboost_stack: {
          ...metric(0.972222, 1, 0.985915),
          tree_shap: {
            global_mean_absolute: [
              { feature: "regex_nomination", mean_abs_shap: 3.06 },
            ],
          },
        },
        xgboost_hard_negative: metric(0.972222, 1, 0.985915),
      },
      contradiction_detection: {
        literal_baseline: metric(1, 0.4, 0.571429),
        cross_encoder: {
          ...metric(1, 0.6, 0.75),
          model_id: "cross-encoder/nli-MiniLM2-L6-H768",
          threshold_selected_on_calibration: 0.98,
          predictions: [],
        },
      },
      predictions: [
        {
          example_id: "case_dev_001:sentence:0",
          family: "matching_processed",
          slice: "claimed_processed_match",
          text: "Your INR 2,500 refund was processed.",
          label: 1,
          regex: 1,
          tfidf_combined_probability: 0.8,
          embedding_probability: 0.9,
          ensemble_probability: 0.85,
          xgboost_stack_probability: 0.99,
          xgboost_hard_negative_probability: 0.99,
        },
      ],
      feasibility: {
        constrained_llm_extraction: {
          status: "NOT_RUN",
          reason: "No CPU-feasible constrained model cleared the precondition.",
        },
      },
    },
  };
  vi.stubGlobal(
    "fetch",
    vi.fn((input: string | URL | Request) => {
      const url = String(input);
      const payload = url.endsWith("/ai-research")
        ? researchResponse
        : url.includes("/ai-lab/")
          ? labResponse
          : { items: [queueItem], next_cursor: null };
      return Promise.resolve(
        new Response(JSON.stringify(payload), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      );
    }),
  );

  render(<App initialRoute="ai" />);
  expect(
    await screen.findByRole("heading", {
      name: "Decision Engine",
    }),
  ).toBeVisible();
  expect(screen.getByRole("heading", { name: "NOT PROMOTED" })).toBeVisible();
  expect(screen.getByText("regex_nomination")).toBeVisible();
  expect(screen.getByText(/Your INR 2,500 refund was processed/)).toBeVisible();
  expect(screen.getByRole("heading", { name: /Same evidence/ })).toBeVisible();
  expect(screen.queryByText(/model confidence/i)).not.toBeInTheDocument();
});

test("loads the local queue and complete case workspace", async () => {
  render(<App initialRoute="workspace" />);

  expect(
    screen.getByRole("heading", { name: "Dispute Integrity Gate" }),
  ).toBeInTheDocument();
  expect(screen.getByText("OFFLINE REPLAY · PRECOMPUTED REGEX")).toBeVisible();
  const queue = await screen.findByRole("region", { name: "Case queue" });
  expect(
    within(queue).getByRole("button", { name: /case_block/i }),
  ).toBeVisible();
  expect(within(queue).getByText("raw_refund_reason")).toBeVisible();
  expect(
    await screen.findByRole("heading", { name: "case_block" }),
  ).toBeVisible();
  expect(screen.getByText("LOCAL HOLD")).toBeVisible();
  expect(
    screen.getAllByText("Your INR 2,500 refund was processed.").length,
  ).toBeGreaterThanOrEqual(1);
  expect(screen.getAllByText("F_REFUND_AMOUNT_MISMATCH")).toHaveLength(2);
  expect(
    screen.getByText(
      "No accept, contest, refund, or payment write is available.",
    ),
  ).toBeVisible();
  expect(
    screen.getByText("Decision support only: not a win prediction."),
  ).toBeVisible();
  await waitFor(() => expect(fetch).toHaveBeenCalledTimes(2));
});

test("shows an API-backed empty queue state", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(() =>
      Promise.resolve(
        new Response(JSON.stringify({ items: [], next_cursor: null }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      ),
    ),
  );
  render(<App initialRoute="workspace" />);

  expect(
    await screen.findByText("No cases match the current local filters."),
  ).toBeVisible();
  expect(
    screen.queryByRole("heading", { name: "Evidence" }),
  ).not.toBeInTheDocument();
});

test("moves focus to the backend-grounded exact source span", async () => {
  render(<App initialRoute="workspace" />);
  await screen.findByRole("heading", { name: "case_block" });

  fireEvent.click(
    screen.getByRole("button", {
      name: "Show exact source for refund claimed processed",
    }),
  );

  const highlight = screen.getByTestId("source-highlight");
  expect(highlight).toHaveTextContent("Your INR 2,500 refund was processed.");
  await waitFor(() => expect(highlight).toHaveFocus());
  expect(screen.getByRole("status")).toHaveTextContent(
    "Focused exact source quote for refund claimed processed.",
  );
});

test("names the REVIEW reason and queues recovery through the local API", async () => {
  const reviewItem = {
    ...queueItem,
    case_id: "case_review",
    dispute_id: "disp_review",
    gate_status: "REVIEW",
    primary_reason_code: "F_MODEL_UNAVAILABLE",
  };
  const reviewDetail = {
    ...caseDetail,
    case: reviewItem,
    findings: [],
    gate_decision: {
      status: "REVIEW",
      review_reasons: ["F_MODEL_UNAVAILABLE"],
    },
  };
  vi.stubGlobal(
    "fetch",
    vi.fn((input: string | URL | Request, init?: RequestInit) => {
      const url = String(input);
      const payload =
        init?.method === "POST"
          ? {
              status: "queued",
              job_id: "job_reprocess_1",
              case_id: "case_review",
              network_write_performed: false,
            }
          : url.endsWith("/case_review")
            ? reviewDetail
            : { items: [reviewItem], next_cursor: null };
      return Promise.resolve(
        new Response(JSON.stringify(payload), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      );
    }),
  );
  render(<App initialRoute="workspace" />);

  expect(
    await screen.findByText("The semantic extractor was unavailable."),
  ).toBeVisible();
  expect(
    screen.getByText(
      "Restore the configured extractor or offline replay, then reprocess.",
    ),
  ).toBeVisible();
  fireEvent.click(
    screen.getByRole("button", { name: "Reprocess after repair" }),
  );

  expect(
    await screen.findByText(
      "Queued local reprocess job job_reprocess_1. No network write was performed.",
    ),
  ).toBeVisible();
  await waitFor(() => expect(fetch).toHaveBeenCalledTimes(3));
});

test("forces cited-source inspection before a structured local BLOCK override", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn((input: string | URL | Request, init?: RequestInit) => {
      const url = String(input);
      let payload: object;
      if (url.endsWith("/inspect")) {
        payload = { status: "inspected", network_write_performed: false };
      } else if (url.endsWith("/override")) {
        payload = {
          case_id: "case_block",
          workflow_status: "READY_WITH_OVERRIDE",
          gate_status: "BLOCK",
          network_write_performed: false,
        };
      } else if (url.endsWith("/mark-ready")) {
        payload = {
          case_id: "case_block",
          workflow_status: "READY_FOR_CONTEST",
          gate_status: "BLOCK",
          network_write_performed: false,
        };
      } else if (url.endsWith("/case_block")) {
        payload = caseDetail;
      } else {
        payload = { items: [queueItem], next_cursor: null };
      }
      expect(init?.method ?? "GET").toMatch(/GET|POST/);
      return Promise.resolve(
        new Response(JSON.stringify(payload), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      );
    }),
  );
  render(<App initialRoute="workspace" />);
  await screen.findByRole("heading", { name: "case_block" });

  fireEvent.click(screen.getByRole("button", { name: "Override local hold" }));
  const dialog = screen.getByRole("dialog", { name: "Override local hold" });
  await waitFor(() =>
    expect(
      within(dialog).getByRole("heading", { name: "Override local hold" }),
    ).toHaveFocus(),
  );
  expect(
    within(dialog).getByRole("button", { name: "Record local override" }),
  ).toBeDisabled();

  fireEvent.click(
    within(dialog).getAllByRole("button", { name: "Open and acknowledge" })[0],
  );
  await waitFor(() =>
    expect(
      within(dialog).getAllByRole("button", { name: "✓ Inspected" }),
    ).toHaveLength(1),
  );
  fireEvent.click(
    within(dialog).getByRole("button", { name: "Open and acknowledge" }),
  );
  await waitFor(() =>
    expect(
      within(dialog).getAllByRole("button", { name: "✓ Inspected" }),
    ).toHaveLength(2),
  );
  fireEvent.change(within(dialog).getByLabelText("Override reason"), {
    target: { value: "SOURCE_DATA_ERROR" },
  });
  fireEvent.click(
    within(dialog).getByLabelText(
      "This changes only the local readiness state",
    ),
  );
  fireEvent.click(
    within(dialog).getByRole("button", { name: "Record local override" }),
  );

  expect(
    await screen.findByText(
      "Local hold override recorded. Historical BLOCK remains unchanged.",
    ),
  ).toBeVisible();
  expect(screen.getByText("LOCAL HOLD")).toBeVisible();
  fireEvent.click(
    screen.getByRole("button", { name: "Mark ready for contest (local only)" }),
  );
  expect(
    await screen.findByText(
      "Marked ready in local workflow. No network write was performed.",
    ),
  ).toBeVisible();
  await waitFor(() => expect(fetch).toHaveBeenCalledTimes(6));
});

test("closes the override dialog with Escape and restores trigger focus", async () => {
  render(<App initialRoute="workspace" />);
  await screen.findByRole("heading", { name: "case_block" });
  const trigger = screen.getByRole("button", { name: "Override local hold" });

  fireEvent.click(trigger);
  const dialog = screen.getByRole("dialog", { name: "Override local hold" });
  await waitFor(() =>
    expect(
      within(dialog).getByRole("heading", { name: "Override local hold" }),
    ).toHaveFocus(),
  );
  fireEvent.keyDown(screen.getByRole("presentation"), { key: "Escape" });

  await waitFor(() => expect(trigger).toHaveFocus());
  expect(
    screen.queryByRole("dialog", { name: "Override local hold" }),
  ).not.toBeInTheDocument();
});

test("traps Tab focus inside the override dialog", async () => {
  render(<App initialRoute="workspace" />);
  await screen.findByRole("heading", { name: "case_block" });
  fireEvent.click(screen.getByRole("button", { name: "Override local hold" }));
  const dialog = screen.getByRole("dialog", { name: "Override local hold" });
  const backdrop = screen.getByRole("presentation");
  const close = within(dialog).getByRole("button", {
    name: "Close override dialog",
  });
  const cancel = within(dialog).getByRole("button", { name: "Cancel" });

  close.focus();
  fireEvent.keyDown(backdrop, { key: "Tab", shiftKey: true });
  expect(cancel).toHaveFocus();

  fireEvent.keyDown(backdrop, { key: "Tab" });
  expect(close).toHaveFocus();
});

test("shows NOT YET MEASURED instead of placeholder evaluation values", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn((input: string | URL | Request) => {
      const url = String(input);
      const payload = url.endsWith("/evaluation/latest")
        ? { status: "NOT_YET_MEASURED" }
        : url.endsWith("/case_block")
          ? caseDetail
          : { items: [queueItem], next_cursor: null };
      return Promise.resolve(
        new Response(JSON.stringify(payload), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      );
    }),
  );
  render(<App initialRoute="workspace" />);

  fireEvent.click(screen.getByRole("button", { name: "Evaluation" }));

  expect(
    await screen.findByRole("heading", { name: "NOT YET MEASURED" }),
  ).toBeVisible();
  expect(
    screen.getByText(
      "No saved, digest-verified result artifact is available. No performance values are shown.",
    ),
  ).toBeVisible();
});

test("renders measured values and provenance only from the saved artifact response", async () => {
  const evaluation = {
    status: "MEASURED",
    run_id: "fixture-run",
    created_at: "2026-08-23T12:00:00Z",
    synthetic_warning:
      "Synthetic, class-balanced diagnostic benchmark; not production prevalence or outcome evidence.",
    dataset: {
      dataset_id: "DIG-RNP-SYN-v1",
      generator_version: "1.0.0",
      split: "dev",
      synthetic: true,
      manifest_sha256: "b".repeat(64),
    },
    system: {
      system_version: "deterministic-v1",
      extractor_id: "regex-baseline-v1",
      model_id: null,
      prompt_version: "not-applicable-regex-v1",
      claim_schema_version: "1.0",
      config_sha256: "a".repeat(64),
      code_commit: "UNAVAILABLE_NOT_A_GIT_REPOSITORY",
    },
    metrics: {
      material_conflict: {
        precision: { numerator: 1, denominator: 1, value: 1 },
        recall: { numerator: 1, denominator: 1, value: 1 },
        f1: 1,
      },
      operational: {
        review_rate: { numerator: 0, denominator: 1, value: 0 },
        auto_decision_coverage: { numerator: 1, denominator: 1, value: 1 },
        false_pass_block_cases: 0,
        false_block_nonblock_cases: 0,
      },
      claims: {
        micro: { f1: 1 },
        exact_grounding_rate: { numerator: 1, denominator: 1, value: 1 },
      },
      confusion_matrix: { BLOCK: { BLOCK: 1 } },
      slices: { "test-fixture": { total: 1, correct: 1 } },
      baseline_delta: { material_f1: 0 },
      cost_sensitivity: [{ label: "fixture", total_cost: 0 }],
    },
    artifact_sha256: "c".repeat(64),
  };
  vi.stubGlobal(
    "fetch",
    vi.fn((input: string | URL | Request) => {
      const url = String(input);
      const payload = url.endsWith("/evaluation/latest")
        ? evaluation
        : url.endsWith("/case_block")
          ? caseDetail
          : { items: [queueItem], next_cursor: null };
      return Promise.resolve(
        new Response(JSON.stringify(payload), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      );
    }),
  );
  render(<App initialRoute="workspace" />);

  fireEvent.click(screen.getByRole("button", { name: "Evaluation" }));

  expect(
    await screen.findByRole("heading", { name: "Evaluation · fixture-run" }),
  ).toBeVisible();
  expect(screen.getByText("DIG-RNP-SYN-v1 · DEV")).toBeVisible();
  expect(screen.getAllByText("100.0% (1/1)").length).toBeGreaterThanOrEqual(1);
  expect(screen.getByText("UNAVAILABLE_NOT_A_GIT_REPOSITORY")).toBeVisible();
  expect(screen.getByText(/not production prevalence/)).toBeVisible();
});
