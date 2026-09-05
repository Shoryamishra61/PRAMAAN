export type GateStatus = "PASS" | "REVIEW" | "BLOCK";

export interface QueueItem {
  case_id: string;
  dispute_id: string;
  payment_id: string;
  amount_minor: number;
  currency: string;
  respond_by: string | null;
  raw_reason_code: string | null;
  reason_profile: string;
  processing_status: string;
  gate_status: GateStatus | null;
  primary_reason_code: string | null;
}

export interface QueueResponse {
  items: QueueItem[];
  next_cursor: string | null;
}

export interface EvidenceDocument {
  id: string;
  source_type: string;
  source_system: string | null;
  media_type: string;
  canonical_text: string;
  content_sha256: string;
  captured_at: string | null;
  ingested_at: string;
  is_complete_source: boolean | null;
}

export interface GroundedClaim {
  id: string;
  document_id: string;
  claim_type: string;
  raw_value: string | null;
  amount_minor: number | null;
  currency: string | null;
  refund_reference: string | null;
  modality: string | null;
  source_quote: string;
  span_start: number | null;
  span_end: number | null;
  grounding_status: string;
}

export interface Finding {
  id: string;
  rule_code: string;
  severity: string;
  decision_effect: GateStatus;
  explanation: string;
  structured_refs: string[];
  claim_refs: string[];
}

export interface RefundRecord {
  id: string;
  payment_id: string;
  amount_minor: number;
  currency: string;
  local_status: string;
  reference: string | null;
}

export interface CaseDetail {
  case: QueueItem;
  workflow_status: string;
  payment_snapshot: {
    payment_id: string;
    captured_amount_minor: number | null;
    currency: string | null;
    captured_at: string | null;
    snapshot_complete: boolean;
  } | null;
  refunds: RefundRecord[];
  evidence_documents: EvidenceDocument[];
  grounded_claims: GroundedClaim[];
  findings: Finding[];
  gate_decision: {
    status: GateStatus;
    review_reasons?: unknown;
    [key: string]: unknown;
  } | null;
  audit_events: Array<{
    id: string;
    operator_id: string;
    event_type: string;
    reason_code: string | null;
    note: string | null;
    details: Record<string, unknown>;
    created_at: string;
  }>;
}

async function readJson<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let message = `Local API request failed (${response.status}).`;
    try {
      const payload = (await response.json()) as {
        error?: { message?: unknown };
        detail?: unknown;
      };
      if (typeof payload.error?.message === "string") {
        message = payload.error.message;
      } else if (typeof payload.detail === "string") {
        message = payload.detail;
      } else if (Array.isArray(payload.detail)) {
        const issues = payload.detail
          .map((issue) => {
            if (!issue || typeof issue !== "object") return null;
            const record = issue as { loc?: unknown; msg?: unknown };
            if (typeof record.msg !== "string") return null;
            const field = Array.isArray(record.loc)
              ? record.loc.at(-1)
              : undefined;
            return typeof field === "string"
              ? `${field.replaceAll("_", " ")}: ${record.msg}`
              : record.msg;
          })
          .filter((issue): issue is string => Boolean(issue));
        if (issues.length) message = `Check the input: ${issues.join("; ")}.`;
      }
    } catch {
      // Keep the status-based fallback when an intermediary returns non-JSON.
    }
    throw new Error(message);
  }
  return (await response.json()) as T;
}

async function apiFetch(
  input: RequestInfo | URL,
  init?: RequestInit,
): Promise<Response> {
  try {
    return await fetch(input, {
      ...init,
      signal: init?.signal ?? AbortSignal.timeout(10_000),
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === "TimeoutError") {
      throw new Error("The local API did not respond within 10 seconds.", {
        cause: error,
      });
    }
    throw error;
  }
}

export async function fetchQueue(
  gateStatus: string,
  processingStatus: string,
): Promise<QueueResponse> {
  const params = new URLSearchParams();
  if (gateStatus) params.set("gate_status", gateStatus);
  if (processingStatus) params.set("processing_status", processingStatus);
  const query = params.size ? `?${params.toString()}` : "";
  return readJson<QueueResponse>(await apiFetch(`/api/v1/cases${query}`));
}

export async function fetchCase(caseId: string): Promise<CaseDetail> {
  return readJson<CaseDetail>(
    await apiFetch(`/api/v1/cases/${encodeURIComponent(caseId)}`),
  );
}

export interface QueuedReprocess {
  status: "queued";
  job_id: string;
  case_id: string;
  network_write_performed: false;
}

export async function reprocessCase(caseId: string): Promise<QueuedReprocess> {
  return readJson<QueuedReprocess>(
    await apiFetch(`/api/v1/cases/${encodeURIComponent(caseId)}/reprocess`, {
      method: "POST",
    }),
  );
}

export interface LocalWorkflowResult {
  case_id: string;
  workflow_status: string;
  gate_status: GateStatus;
  network_write_performed: false;
}

export async function inspectSource(
  caseId: string,
  sourceRef: string,
  documentId: string,
): Promise<void> {
  await readJson(
    await apiFetch(`/api/v1/cases/${encodeURIComponent(caseId)}/inspect`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ source_ref: sourceRef, document_id: documentId }),
    }),
  );
}

export async function overrideLocalHold(
  caseId: string,
  reason: string,
  note: string,
): Promise<LocalWorkflowResult> {
  return readJson<LocalWorkflowResult>(
    await apiFetch(`/api/v1/cases/${encodeURIComponent(caseId)}/override`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ reason, note: note || null }),
    }),
  );
}

export async function markCaseReady(
  caseId: string,
): Promise<LocalWorkflowResult> {
  return readJson<LocalWorkflowResult>(
    await apiFetch(`/api/v1/cases/${encodeURIComponent(caseId)}/mark-ready`, {
      method: "POST",
    }),
  );
}

export type EvaluationResponse =
  | { status: "NOT_YET_MEASURED" }
  | {
      status: "MEASURED";
      run_id: string;
      created_at: string;
      synthetic_warning: string;
      dataset: {
        dataset_id: string;
        generator_version: string;
        split: "dev" | "holdout";
        synthetic: boolean;
        manifest_sha256: string;
      };
      system: {
        system_version: string;
        extractor_id: string;
        model_id: string | null;
        prompt_version: string;
        claim_schema_version: string;
        config_sha256: string;
        code_commit: string;
      };
      metrics: Record<string, unknown>;
      artifact_sha256: string;
    };

export async function fetchLatestEvaluation(): Promise<EvaluationResponse> {
  return readJson<EvaluationResponse>(
    await apiFetch("/api/v1/evaluation/latest"),
  );
}

export interface SandboxEvaluateRequest {
  raw_reason_code: string;
  payment_amount_inr: string;
  customer_communication: string;
  refund_ledger_complete: boolean;
  refund_status:
    "none" | "created" | "pending" | "processed" | "failed" | "cancelled";
  refund_amount_inr: string | null;
  simulation?: "none" | "model_outage" | "hash_mismatch" | "ocr_corruption";
}

export interface SandboxEvaluateResponse {
  run_id: string;
  request_sha256: string;
  raw_reason_code: string;
  profile_id: "refund_not_processed_v1";
  status: GateStatus;
  semantic_status: "SUCCESS" | "REVIEW";
  claims: Array<{
    claim_id: string;
    claim_type: string;
    source_quote: string;
    span_start: number | null;
    span_end: number | null;
    grounding_status: string;
    amount_minor: number | null;
    currency: string | null;
    normalization_status: string;
  }>;
  findings: Array<{
    code: string;
    effect: "REVIEW" | "BLOCK";
    summary: string;
    evidence_refs: string[];
  }>;
  ledger: {
    payment_id: string;
    payment_amount_minor: number;
    currency: "INR";
    refund_ledger_complete: boolean;
    refund_status: string;
    refund_amount_minor: number | null;
  };
  proof: {
    status: "SAT" | "UNSAT" | "INCOMPLETE";
    constraints: Array<{
      constraint_id: string;
      layer: "INPUT" | "GROUNDING" | "AUTHORITATIVE" | "INVARIANT";
      expression: string;
      state: "SAT" | "UNSAT" | "INCOMPLETE";
    }>;
    certificate: null | {
      solver: "DETERMINISTIC_COMPILER";
      invariant_id: string;
      proof_sha256: string;
      evidence_refs: string[];
      minimal_relative_to_compiled_constraints: true;
    };
    model_override_allowed: false;
  };
  next_evidence?: null | {
    action: "REQUEST_REFUND_EXPORT";
    evidence_id: "refund_state";
    acquisition_cost: 1;
    reason: string;
  };
  comparison?: {
    semantic_output: "GROUNDED_RELATION" | "ABSTAINED";
    deterministic_output: GateStatus;
    relationship: "DIVISION_OF_AUTHORITY" | "SAFE_ABSTENTION";
    uncertainty_basis: "VERIFICATION_COMPLETENESS";
    probability_exposed: false;
  };
  boundary: {
    runtime: "LOCAL_OFFLINE";
    ephemeral: true;
    synthetic_input: true;
    external_api_calls: false;
    razorpay_write_performed: false;
    persisted: false;
    holdout_accessed: false;
    extractor_id: string;
    gate_authority: "DETERMINISTIC_POLICY";
  };
  disclaimer: string;
}

export async function evaluateSandbox(
  request: SandboxEvaluateRequest,
): Promise<SandboxEvaluateResponse> {
  return readJson<SandboxEvaluateResponse>(
    await apiFetch("/api/v1/sandbox/evaluate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request),
    }),
  );
}

export interface AiLabResponse {
  case_id: string;
  boundary: {
    runtime: "LOCAL_OFFLINE";
    dataset_split: "DEV";
    synthetic: true;
    holdout_accessed: false;
    external_api_calls: false;
    gate_authority: false;
    probability_exposed: false;
  };
  model: {
    model_id: string;
    architecture: string;
    evaluation: string;
    promotion_status: "PROMOTED" | "NOT_PROMOTED";
    promotion_rule: string;
    selected_extractor: string;
    candidate_metrics: {
      precision: number;
      recall: number;
      f1: number;
      confusion: Record<string, number>;
    };
    comparator_metrics: {
      precision: number;
      recall: number;
      f1: number;
      confusion: Record<string, number>;
    };
    nominations: Array<{
      claim_type: "refund_claimed_processed";
      source_quote: string;
      feature_contributions: Array<{
        feature: string;
        contribution: number;
        direction: "supports" | "opposes";
      }>;
    }>;
  };
  retrieval: {
    method: "LOCAL_TFIDF_EXACT_CITATIONS";
    corpus_sha256: string;
    guidance_only: true;
    citations: Array<{
      rank: number;
      source_path: string;
      section: string;
      exact_excerpt: string;
    }>;
  };
}

export async function fetchAiLab(caseId: string): Promise<AiLabResponse> {
  return readJson<AiLabResponse>(
    await apiFetch(`/api/v1/ai-lab/cases/${encodeURIComponent(caseId)}`),
  );
}

export interface ResearchMetric {
  precision: number;
  recall: number;
  f1: number;
  confusion: Record<"tn" | "fp" | "fn" | "tp", number>;
}

export interface ResearchCandidate {
  status?: string;
  metrics: ResearchMetric;
  exact_quote_grounding_rate?: number;
  calibration?: {
    brier: number;
    ece_5: number;
    nll: number;
    bins: Array<{
      mean_probability: number;
      positive_rate: number;
      count: number;
    }>;
  };
  raw_calibration?: ResearchCandidate["calibration"];
  risk_coverage?: {
    aurc: number;
    points: Array<{ coverage: number; risk: number }>;
  };
  raw_risk_coverage?: ResearchCandidate["risk_coverage"];
  precision_recall_curve?: {
    average_precision: number;
    points: Array<{ precision: number; recall: number }>;
  };
  conformal?: { empirical_coverage: number; abstention_rate: number };
  latency?: { cold_load_ms: number; p50_ms: number; p95_ms: number };
  model_bytes?: number;
  estimated_api_cost_usd?: number;
  ood?: {
    auroc: number;
    ood_rejection_rate: number;
    id_false_reject_rate: number;
    ood_count: number;
  };
  tree_shap?: {
    global_mean_absolute: Array<{ feature: string; mean_abs_shap: number }>;
  };
}

export interface AiResearchResponse {
  artifact_sha256: string;
  generated: true;
  artifact: {
    created_at: string;
    boundary: { split: string; holdout_accessed: false; gate_authority: false };
    dataset: { sentence_examples: number; positive_sentences: number };
    promotion: {
      extractor_status: string;
      selected_runtime_extractor: string;
      nli_status: string;
    };
    claim_extraction: {
      regex_baseline: ResearchCandidate;
      tfidf: Record<"word" | "char" | "combined", ResearchCandidate>;
      embedding_logistic: ResearchCandidate;
      ensemble: ResearchCandidate;
      xgboost_stack: ResearchCandidate;
      xgboost_hard_negative: ResearchCandidate;
    };
    contradiction_detection: {
      literal_baseline: ResearchCandidate;
      cross_encoder: ResearchCandidate & {
        model_id: string;
        threshold_selected_on_calibration: number;
        predictions: Array<{
          id: string;
          label: number;
          prediction: number;
          slice: string;
          contradiction_probability: number;
        }>;
      };
    };
    predictions: Array<{
      example_id: string;
      family: string;
      slice: string;
      text: string;
      label: number;
      regex: number;
      tfidf_combined_probability: number;
      embedding_probability?: number;
      ensemble_probability?: number;
      xgboost_stack_probability?: number;
      xgboost_hard_negative_probability?: number;
    }>;
    feasibility: Record<string, { status: string; reason: string }>;
  };
}

export async function fetchAiResearch(): Promise<AiResearchResponse> {
  return readJson<AiResearchResponse>(await apiFetch("/api/v1/ai-research"));
}

export interface FeclMetricSet {
  precision: number;
  recall: number;
  f1: number;
  pr_auc: number;
  brier: number;
  ece_10: number;
  expected_loss_per_case: number;
  false_pass: number;
  false_block: number;
  confusion: { tp: number; tn: number; fp: number; fn: number };
  pr_curve: Array<{
    precision: number;
    recall: number;
    threshold: number | null;
  }>;
  risk_coverage: Array<{ coverage: number; risk: number; accepted: number }>;
}

export interface CarveMetric {
  precision: number;
  recall: number;
  f1: number;
  pr_auc: number;
  false_pass: number;
  false_block: number;
  false_pass_exposure_minor: number;
  ece_10: number;
  mcc_exact?: number;
}

export interface CarveResearchResponse {
  generated: true;
  benchmark_id: string;
  dev_sha256: string;
  test_sha256: string;
  receipt_sha256: string;
  split_counts: Record<
    "train" | "dev" | "calibration" | "test" | "ood",
    number
  >;
  dev: {
    models: Record<string, CarveMetric | { status: string }>;
    promotion: Record<string, string>;
    relation_extraction: Record<string, { macro_f1: number; micro_f1: number }>;
    calibration: {
      crc: { coverage: number; threshold: number; corrected_risk: number };
      risk_coverage_curve: Array<{
        coverage: number;
        value_weighted_risk: number;
      }>;
    };
    selected_acquisition: AcquisitionMetric;
  };
  test: {
    one_shot_test: true;
    synthetic_only: true;
    models: Record<string, CarveMetric>;
    relation_extraction: Record<string, { macro_f1: number; micro_f1: number }>;
    selective: {
      pass: number;
      review: number;
      block: number;
      autonomous_coverage: number;
      false_pass: number;
    };
    acquisition: AcquisitionMetric[];
    selected_acquisition: AcquisitionMetric;
    ood: { review_rate: number; false_pass: number };
  };
  evidence_case: {
    case_id: string;
    minimal_pair_id: string;
    source_quote: string;
    source_span: [number, number];
    claim_amount_minor: number;
    authoritative_amount_minor: number;
    currency: string;
    dispute_value_minor: number;
    initial_visible_evidence: string[];
    required_for_resolution: string[];
    certificate: {
      invariant_ids: string[];
      evidence_ids: string[];
      solver_expected: string;
    };
    counterfactual_repair: {
      field: string;
      from: number | string | boolean;
      to: number | string | boolean;
    };
  };
}

export interface AcquisitionMetric {
  policy: string;
  acquisition_cost: number;
  acquisitions_per_resolved: number;
  resolved_cases: number;
  false_pass_exposure_minor: number;
  trajectory_exact_match: number;
}

export async function fetchCarveResearch(): Promise<CarveResearchResponse> {
  return readJson<CarveResearchResponse>(
    await apiFetch("/api/v1/research/carve-v4.5"),
  );
}
