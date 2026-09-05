> Navigation update, 2026-09-05: `backend/app/quant_risk_api.py`, `training/run_all.py`, `evaluation/evaluate_all.py`, and `scripts/apply_empirical_research_results.py` are retired. Their entries below are historical. The quant-risk route returns 410. Use the artifact-backed CARVE/extraction paths and `artifacts/verification/RELEASE-GATES.md` for current evidence. Browser ingestion is consolidated in `components/EvidenceDropzone.tsx`, `utils/crossFileIntelligence.ts`, and `utils/sandboxRequest.ts`.

# PRAMAAN Codebase Architecture & File Knowledge Index

> **Autonomous Agent Knowledge Base**: This document provides an exhaustive, zero-token-waste file-by-file map of the entire PRAMAAN (CARVE-FECL Dispute Integrity Gate) codebase. Future AI coding agents should consult this index first before opening or re-analyzing individual source files.

---

## 1. System Identity & Core Architectural Contracts

- **Repository**: `PRAMAAN` / `dispute-integrity-gate-spec` (Razorpay AI Buildathon 2026 · Track 02)
- **Core Purpose**: Defensive, read-only pre-submission integrity gate for merchant chargeback loss prevention (`refund_not_processed_v1` reason family).
- **End-to-End Pipeline**:
  ```text
  Inbound Razorpay Webhook (HMAC-SHA256 authenticated)
    -> Durable Ingestion (SQLite WAL with idempotency)
    -> Precomputed / Regex Claim Extraction (refund claims)
    -> Exact-Quote Grounding Verification (byte offsets in raw text)
    -> Deterministic Structured State Verifier (Z3 / Integer Math)
    -> Gate Decision (PASS / REVIEW / BLOCK)
    -> Tamper-Evident SHA-256 Chained Audit Trail
  ```
- **Non-Negotiable Constitutional Guardrails** (`AGENTS.md`):
  1. **Zero Razorpay Writes**: NEVER call accept, contest, refund, or payment endpoints. Read-only gate.
  2. **No Hallucinated Text**: Never use generative AI for dispute letters, legal conclusions, or win probabilities.
  3. **Strict Minor-Unit Money**: All financial arithmetic uses integer minor units (paise/cents). No floating-point math.
  4. **Grounding Required**: Every extracted claim must map to an exact substring in raw text with verified byte offsets.
  5. **Fail-Safe Abstention**: Missing evidence, degraded models, or ungrounded claims must default to `REVIEW`, never silent `PASS`.

---

## 1. Core Backend Service & Engine (`backend/app/`)

### [`backend/app/__init__.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/backend/app/__init__.py)
- **Kind & Size**: `Python` | `1` lines
- **Purpose**: PRAMAAN product application and CARVE-FECL research package.

### [`backend/app/ai_lab_api.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/backend/app/ai_lab_api.py)
- **Kind & Size**: `Python` | `154` lines
- **Purpose**: Read-only case-level API composition for the offline AI/ML evidence lab.
- **Classes**: `LabBoundary`, `MetricSummary`, `LabModelSummary`, `RetrievalSummary`, `AiLabCaseResponse`, `AiLabArtifactError`
- **Key Functions**: `_metric`, `_cached_eval_artifact`, `_cached_model`, `_cached_retriever`, `build_case_ai_lab` *(Analyze only already-ingested local evidence; no m...)*

### [`backend/app/ai_lab_model.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/backend/app/ai_lab_model.py)
- **Kind & Size**: `Python` | `140` lines
- **Purpose**: Offline semantic-model lab with no gate or state authority.
- **Classes**: `FeatureContribution`, `SemanticNomination`
- **Key Functions**: `sentences` *(Return exact source sentences; predictions never i...)*, `build_pipeline` *(Create the fixed, interpretable candidate used by ...)*, `save_model`, `load_model`, `load_eval_artifact`, `nominate_processed_claims` *(Nominate exact sentences and expose signed n-gram ...)*

### [`backend/app/ai_lab_retrieval.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/backend/app/ai_lab_retrieval.py)
- **Kind & Size**: `Python` | `81` lines
- **Purpose**: Bounded local retrieval over an allowlisted, exact-quote documentation corpus.
- **Classes**: `RetrievalChunk`, `RetrievalCitation`, `BoundedRetriever` [methods: __init__, corpus_sha256, retrieve]

### [`backend/app/ai_research_api.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/backend/app/ai_research_api.py)
- **Kind & Size**: `Python` | `88` lines
- **Purpose**: Read-only projection of the generated AI research artifact.
- **Classes**: `AiResearchResponse`, `AiResearchArtifactError`, `FeclV2Response`
- **Key Functions**: `load_ai_research`, `load_fecl_v2`

### [`backend/app/benchmark_generator.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/backend/app/benchmark_generator.py)
- **Kind & Size**: `Python` | `586` lines
- **Purpose**: Deterministic generator for the family-separated synthetic v1 benchmark.
- **Classes**: `Scenario`
- **Key Functions**: `_json_write`, `_claim`, `_refund`, `_display_minor`, `_scenario`, `_event`, `_write_case`, `generate_benchmark` *(Generate v1 once; refuse to overwrite any existing...)*

### [`backend/app/benchmark_integrity.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/backend/app/benchmark_integrity.py)
- **Kind & Size**: `Python` | `207` lines
- **Purpose**: One-way benchmark freeze and holdout byte-integrity verification.
- **Classes**: `BenchmarkIntegrityError`, `HoldoutAccessError`
- **Key Functions**: `_sha256_bytes`, `_canonical_json`, `_read_json_object`, `_holdout_files`, `_build_holdout_manifest`, `freeze_benchmark` *(Freeze a new dataset version once and return its h...)*, `_manifest_file_records`, `verify_holdout_manifest` *(Verify root digest, complete file set, sizes, and ...)*

### [`backend/app/carve.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/backend/app/carve.py)
- **Kind & Size**: `Python` | `697` lines
- **Purpose**: CARVE typed contracts and deterministic proof compiler.
- **Classes**: `DecisionStatus`, `SourceAuthorityTier`, `CircuitBreakerState`, `EvidenceArtifact`, `GroundedClaim`, `TypedRelation`
- **Key Functions**: `canonical`, `evidence_digest`, `_value`, `_new_solver`, `_minimize_unsat`, `_proof`, `_incomplete`, `compile_financial_proof` *(Compile only visible, digest-valid evidence. Hidde...)*

### [`backend/app/carve_research_api.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/backend/app/carve_research_api.py)
- **Kind & Size**: `Python` | `104` lines
- **Purpose**: Read-only, hash-verified projection of the frozen CARVE v4.5 artifacts.
- **Classes**: `CarveResearchError`, `CarveResearchResponse`
- **Key Functions**: `_read`, `_line_count`, `load_carve_research`

### [`backend/app/case_actions.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/backend/app/case_actions.py)
- **Kind & Size**: `Python` | `352` lines
- **Purpose**: Transactional local analyst actions with no external network writes.
- **Classes**: `QueuedReprocess`, `WorkflowActionError` [methods: __init__], `InspectionRequest`, `InspectionResult`, `OverrideReason`, `OverrideRequest` [methods: require_other_note]
- **Key Functions**: `_idempotent_suffix`, `queue_reprocess` *(Append a repair request and durable job in one sho...)*, `_latest_gate_status`, `_required_block_sources`, `inspect_source` *(Validate and append one evidence-directed source i...)*, `override_local_hold` *(Change local readiness only after every material s...)*, `mark_ready` *(Mark local readiness for PASS or an already struct...)*

### [`backend/app/case_api.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/backend/app/case_api.py)
- **Kind & Size**: `Python` | `359` lines
- **Purpose**: Read-only analyst queue and case-workspace queries.
- **Classes**: `QueueItem`, `CaseListResponse`, `PaymentSnapshotResponse`, `RefundResponse`, `EvidenceResponse`, `ClaimResponse`
- **Key Functions**: `_latest_decision_join`, `_queue_item`, `list_cases` *(Return a stable, urgency-oriented local queue with...)*, `_json_tuple`, `_json_object`, `get_case` *(Load only local normalized state; provider raw res...)*, `_evidence_response`

### [`backend/app/case_pipeline.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/backend/app/case_pipeline.py)
- **Kind & Size**: `Python` | `122` lines
- **Purpose**: End-to-end semantic-to-deterministic case evaluation slice.
- **Classes**: `CaseEvaluationInput`, `CaseEvaluationOutcome`
- **Key Functions**: `_deduplicate_findings`, `evaluate_case` *(Evaluate one case without granting semantic output...)*

### [`backend/app/config.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/backend/app/config.py)
- **Kind & Size**: `Python` | `45` lines
- **Purpose**: Environment-backed application configuration.
- **Classes**: `InferenceMode`, `Settings` [methods: require_live_model_key]
- **Key Functions**: `get_settings` *(Return one immutable-by-convention settings snapsh...)*

### [`backend/app/database.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/backend/app/database.py)
- **Kind & Size**: `Python` | `253` lines
- **Purpose**: SQLite connection, migration, and minimal persistence helpers.
- **Key Functions**: `connect_database` *(Open a configured SQLite connection with safety pr...)*, `initialize_database` *(Idempotently initialize the versioned v1 schema....)*, `insert_dispute_case` *(Persist a normalized case with parameterized SQL....)*

### [`backend/app/decision.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/backend/app/decision.py)
- **Kind & Size**: `Python` | `132` lines
- **Purpose**: Canonical PASS/REVIEW/BLOCK decision policy and closed output schema.
- **Classes**: `GateStatus`, `BusinessSafeDecision`, `DecisionFinding`, `GateDecision` [methods: normalize_timestamp, primary_reason_code, business_decision, business_description]
- **Key Functions**: `decide` *(Apply decision precedence after verifier completen...)*

### [`backend/app/domain.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/backend/app/domain.py)
- **Kind & Size**: `Python` | `74` lines
- **Purpose**: Strict local domain types at deterministic trust boundaries.
- **Classes**: `ProcessingStatus`, `WorkflowStatus`, `DisputeCaseCreate` [methods: normalize_currency, normalize_timestamp]
- **Key Functions**: `require_utc` *(Reject naive timestamps and normalize aware timest...)*, `to_storage_timestamp` *(Serialize an already validated timestamp in a stab...)*

### [`backend/app/evaluation_api.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/backend/app/evaluation_api.py)
- **Kind & Size**: `Python` | `76` lines
- **Purpose**: Read-only evaluation dashboard projection from saved result artifacts.
- **Classes**: `EvaluationNotMeasured`, `EvaluationDashboardResponse`, `EvaluationArtifactError`
- **Key Functions**: `_validated_artifact`, `load_latest_evaluation` *(Load the newest saved JSON result without computin...)*

### [`backend/app/evaluation_artifact.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/backend/app/evaluation_artifact.py)
- **Kind & Size**: `Python` | `169` lines
- **Purpose**: Versioned evaluation result contract and immutable-by-convention writer.
- **Classes**: `ClaimEvaluationRecord` [methods: validate_span], `CasePrediction`, `SystemProvenance`, `DatasetProvenance`, `EvaluationResultArtifact` [methods: normalize_created_at, validate_predictions], `WrittenArtifact`
- **Key Functions**: `compute_config_sha256` *(Hash ordered path names and bytes so configuration...)*, `read_dataset_provenance`, `write_evaluation_artifact` *(Write a new canonical JSON artifact and digest sid...)*

### [`backend/app/evaluation_metrics.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/backend/app/evaluation_metrics.py)
- **Kind & Size**: `Python` | `361` lines
- **Purpose**: Artifact-backed case, claim, slice, baseline, and cost metrics.
- **Classes**: `RatioMetric`, `PRFMetric`, `ClassMetric`, `SliceCounts`, `OperationalMetrics`, `ClaimMetrics`
- **Key Functions**: `_ratio`, `_prf`, `_status_counts`, `_claim_identity`, `_grounding_identity`, `_claim_prf`, `_normalized_accuracy`, `compute_evaluation_metrics` *(Compute all reported values from case-level predic...)*

### [`backend/app/evaluator.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/backend/app/evaluator.py)
- **Kind & Size**: `Python` | `297` lines
- **Purpose**: Leakage-resistant case-level synthetic benchmark evaluator.
- **Classes**: `TimedRegexExtractor` [methods: __init__, extract]
- **Key Functions**: `_read_object`, `_read_array`, `_normalized_value`, `_claim_record`, `_expected_claim_record`, `_runtime_input` *(Read only detector-visible files; ground_truth is ...)*, `_predict_case`, `_percentile`

### [`backend/app/extraction.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/backend/app/extraction.py)
- **Kind & Size**: `Python` | `110` lines
- **Purpose**: Strict provider-neutral semantic extraction boundary.
- **Classes**: `ClaimType`, `ClaimModality`, `ExtractionSchemaError`, `ExtractionRequest` [methods: require_unique_allowlist], `ExtractedClaim`, `ExtractionResult`
- **Key Functions**: `validate_extraction_result` *(Bind untrusted output to the exact document and re...)*, `default_claim_allowlist` *(Return the canonical profile allowlist without con...)*

### [`backend/app/grounding.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/backend/app/grounding.py)
- **Kind & Size**: `Python` | `206` lines
- **Purpose**: Exact quote grounding and deterministic semantic value normalization.
- **Classes**: `ValueNormalizationStatus`, `QuoteGrounding`, `GroundedNormalizedClaim` [methods: to_resolved_claim]
- **Key Functions**: `resolve_exact_quote` *(Return exclusive character offsets only for one ex...)*, `parse_inr_minor_units` *(Parse an explicitly INR-denominated amount into pa...)*, `normalize_rfc3339` *(Normalize only timestamps with an explicit timezon...)*, `normalize_refund_reference` *(Accept a bounded identifier token without guessing...)*, `_raw_value`, `_reference_value`, `ground_and_normalize_claim` *(Ground a model claim locally and normalize only un...)*

### [`backend/app/health.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/backend/app/health.py)
- **Kind & Size**: `Python` | `72` lines
- **Purpose**: Truthful local health snapshot derived from SQLite state.
- **Classes**: `HealthResponse`
- **Key Functions**: `read_health` *(Read schema and durable job state; do not claim an...)*

### [`backend/app/ingestion.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/backend/app/ingestion.py)
- **Kind & Size**: `Python` | `225` lines
- **Purpose**: Authenticated Razorpay-compatible event parsing and atomic durable ingestion.
- **Classes**: `IngestPayloadError`, `PaymentEntity`, `DisputeEntity`, `EntityWrapper`, `EventPayload`, `RazorpayEvent`
- **Key Functions**: `_utc_from_epoch`, `_parse_event`, `_case_from_created_event`, `ingest_event` *(Persist one authenticated event and any case/job i...)*

### [`backend/app/jobs.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/backend/app/jobs.py)
- **Kind & Size**: `Python` | `227` lines
- **Purpose**: Durable SQLite job claiming, leases, retry bounds, and worker execution.
- **Classes**: `RetryableJobError` [methods: __init__], `PermanentJobError` [methods: __init__], `ClaimedJob`
- **Key Functions**: `claim_next_job` *(Claim one available or stale job under a short wri...)*, `complete_job` *(Complete a job only while this worker still owns i...)*, `fail_job` *(Schedule a bounded retry or terminate the durable ...)*, `run_worker_once` *(Process at most one durable job; callers own polli...)*

### [`backend/app/main.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/backend/app/main.py)
- **Kind & Size**: `Python` | `392` lines
- **Purpose**: FastAPI entry point for the PRAMAAN Dispute Integrity Gate.
- **Key Functions**: `_error_response`, `create_app` *(Build the application without performing external ...)*

### [`backend/app/observability.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/backend/app/observability.py)
- **Kind & Size**: `Python` | `42` lines
- **Purpose**: Small structured-log boundary that cannot accept evidence or secrets.
- **Classes**: `StructuredLogEvent`
- **Key Functions**: `emit_log` *(Emit deterministic JSON; JSON escaping prevents lo...)*

### [`backend/app/offline_replay.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/backend/app/offline_replay.py)
- **Kind & Size**: `Python` | `66` lines
- **Purpose**: Versioned, read-only structured-output replay adapter.
- **Classes**: `OfflineReplayMiss`, `OfflineReplayCache`, `OfflineReplayExtractor` [methods: __init__, source_mode, extract]
- **Key Functions**: `offline_cache_key` *(Bind replay to exact UTF-8 text bytes, extractor c...)*

### [`backend/app/profile.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/backend/app/profile.py)
- **Kind & Size**: `Python` | `64` lines
- **Purpose**: Executable reason-profile metadata loaded from the canonical contract.
- **Classes**: `MaterialRule`, `ReasonProfile`, `ProfileResolution`
- **Key Functions**: `load_default_profile` *(Load and strictly validate the repository's canoni...)*, `resolve_profile` *(Resolve local scope without interpreting the raw R...)*, `missing_suggested_evidence` *(List absent suggested categories; callers route an...)*

### [`backend/app/quant_risk_api.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/backend/app/quant_risk_api.py)
- **Kind & Size**: `Python` | `162` lines
- **Purpose**: Quant-Risk Research API projection.
- **Classes**: `QuantRiskError`, `QuantRiskResponse`
- **Key Functions**: `load_quant_risk_research`

### [`backend/app/regex_baseline.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/backend/app/regex_baseline.py)
- **Kind & Size**: `Python` | `246` lines
- **Purpose**: Deterministic regex/keyword baseline for diagnostic evaluation.
- **Classes**: `PatternRule`, `RegexBaselineExtractor` [methods: extract]
- **Key Functions**: `_sentences`, `_claim_id`, `_normalize_amount_literal`, `_value`

### [`backend/app/release_freeze.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/backend/app/release_freeze.py)
- **Kind & Size**: `Python` | `140` lines
- **Purpose**: Exact runtime/config freeze manifest for a repository without Git metadata.
- **Classes**: `FrozenFile`, `ReleaseFreeze` [methods: normalize_created_at], `ReleaseFreezeError`
- **Key Functions**: `release_files` *(Return the complete implemented detector/evaluator...)*, `_file_records`, `_bundle_digest`, `create_release_freeze` *(Write a new pre-holdout freeze manifest and refuse...)*, `verify_release_freeze` *(Fail if any relevant path, byte count, content has...)*

### [`backend/app/required_evidence.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/backend/app/required_evidence.py)
- **Kind & Size**: `Python` | `304` lines
- **Purpose**: Reason-Code-Aware Required Evidence Schema and Sufficiency Evaluation.
- **Classes**: `DisputeReasonCode`, `EvidenceCategory`, `EvidenceAuthorityTier`, `EvidenceRequirement`, `DisputeEvidenceAudit`
- **Key Functions**: `audit_dispute_evidence` *(Evaluate evidence sufficiency, missing requirement...)*

### [`backend/app/sandbox_api.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/backend/app/sandbox_api.py)
- **Kind & Size**: `Python` | `414` lines
- **Purpose**: Ephemeral, offline input-to-decision verifier used by the product demo.
- **Classes**: `SandboxEvaluateRequest` [methods: reject_blank_text, validate_payment_amount, validate_refund_amount], `SandboxClaimResponse`, `SandboxFindingResponse`, `SandboxLedgerResponse`, `SandboxBoundaryResponse`, `SandboxProofConstraint`
- **Key Functions**: `_minor_units`, `evaluate_sandbox_input` *(Run one input through the real local extractor and...)*

### [`backend/app/security.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/backend/app/security.py)
- **Kind & Size**: `Python` | `37` lines
- **Purpose**: Security primitives for inbound Razorpay-compatible webhook authentication.
- **Classes**: `WebhookSignatureError`
- **Key Functions**: `compute_webhook_signature` *(Compute HMAC-SHA256 over the exact transmitted req...)*, `verify_webhook_signature` *(Raise when signature material is absent, malformed...)*

### [`backend/app/semantic_pipeline.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/backend/app/semantic_pipeline.py)
- **Kind & Size**: `Python` | `251` lines
- **Purpose**: Fail-safe bounded orchestration for semantic extraction and grounding.
- **Classes**: `TransientExtractorError`, `SemanticPipelineStatus`, `SemanticPipelineOutcome`
- **Key Functions**: `_emit_semantic_log`, `_review_finding`, `_review_outcome`, `run_semantic_pipeline` *(Extract, validate, ground, and abstain safely on e...)*

### [`backend/app/verification.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/backend/app/verification.py)
- **Kind & Size**: `Python` | `423` lines
- **Purpose**: Deterministic structured-state and grounded-claim integrity rules.
- **Classes**: `FindingEffect`, `RefundStatus`, `GroundingStatus`, `RefundRecord` [methods: normalize_currency, normalize_timestamp], `ResolvedClaim` [methods: normalize_currency], `VerificationContext` [methods: normalize_currency]
- **Key Functions**: `_finding`, `_claim_ref`, `_refund_ref`, `_same_claimed_value`, `verify_integrity` *(Apply objective v1 rules; technical uncertainty on...)*

## 2. Frontend Application & UI (`frontend/src/`)

### [`frontend/src/App.test.tsx`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/frontend/src/App.test.tsx)
- **Kind & Size**: `TypeScript` | `988` lines

### [`frontend/src/App.tsx`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/frontend/src/App.tsx)
- **Kind & Size**: `TypeScript` | `2443` lines
- **Exports**: `AiLab`, `App`

### [`frontend/src/CarveResearchLab.tsx`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/frontend/src/CarveResearchLab.tsx)
- **Kind & Size**: `TypeScript` | `1077` lines
- **Exports**: `CarveResearchLab`

### [`frontend/src/FeclResearchPanel.tsx`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/frontend/src/FeclResearchPanel.tsx)
- **Kind & Size**: `TypeScript` | `221` lines
- **Exports**: `FeclResearchPanel`

### [`frontend/src/ProofConsole.tsx`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/frontend/src/ProofConsole.tsx)
- **Kind & Size**: `TypeScript` | `311` lines
- **Exports**: `ProofConsole`

### [`frontend/src/TryVerifier.instrument.test.tsx`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/frontend/src/TryVerifier.instrument.test.tsx)
- **Kind & Size**: `TypeScript` | `187` lines

### [`frontend/src/TryVerifier.tsx`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/frontend/src/TryVerifier.tsx)
- **Kind & Size**: `TypeScript` | `1591` lines
- **Exports**: `TryVerifier`

### [`frontend/src/api.ts`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/frontend/src/api.ts)
- **Kind & Size**: `TypeScript` | `843` lines
- **Types / Interfaces**: `GateStatus`, `QueueItem`, `QueueResponse`, `EvidenceDocument`, `GroundedClaim`, `Finding`, `RefundRecord`, `CaseDetail`

### [`frontend/src/carve-research.css`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/frontend/src/carve-research.css)
- **Kind & Size**: `Other` | `603` lines

### [`frontend/src/components/EvidenceDropzone.tsx`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/frontend/src/components/EvidenceDropzone.tsx)
- **Kind & Size**: `TypeScript` | `365` lines
- **Exports**: `EvidenceDropzone`

### [`frontend/src/components/UnifiedNavigation.tsx`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/frontend/src/components/UnifiedNavigation.tsx)
- **Kind & Size**: `TypeScript` | `165` lines
- **Exports**: `UnifiedNavigation`
- **Types / Interfaces**: `NavRoute`

### [`frontend/src/components/primitives.tsx`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/frontend/src/components/primitives.tsx)
- **Kind & Size**: `TypeScript` | `485` lines
- **Exports**: `StatusBadge`, `Button`, `Card`, `MetricStat`, `ProofCertificateView`, `IntelligentReviewCard`, `CounterfactualRepairCard`, `ModalDialog`
- **Types / Interfaces**: `StatusBadgeProps`, `ButtonProps`, `CardProps`, `MetricStatProps`, `ProofCertificateProps`, `IntelligentReviewProps`, `CounterfactualRepairProps`, `ModalDialogProps`

### [`frontend/src/design-system.css`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/frontend/src/design-system.css)
- **Kind & Size**: `Other` | `489` lines

### [`frontend/src/format.ts`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/frontend/src/format.ts)
- **Kind & Size**: `TypeScript` | `34` lines
- **Exports**: `formatMoney`, `formatTimestamp`, `humanizeToken`

### [`frontend/src/main.tsx`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/frontend/src/main.tsx)
- **Kind & Size**: `TypeScript` | `18` lines

### [`frontend/src/proof-console.css`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/frontend/src/proof-console.css)
- **Kind & Size**: `Other` | `3046` lines

### [`frontend/src/styles.css`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/frontend/src/styles.css)
- **Kind & Size**: `Other` | `2178` lines

### [`frontend/src/test-setup.ts`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/frontend/src/test-setup.ts)
- **Kind & Size**: `TypeScript` | `1` lines

### [`frontend/src/tutorial/TutorialComponents.test.tsx`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/frontend/src/tutorial/TutorialComponents.test.tsx)
- **Kind & Size**: `TypeScript` | `136` lines

### [`frontend/src/tutorial/TutorialContext.tsx`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/frontend/src/tutorial/TutorialContext.tsx)
- **Kind & Size**: `TypeScript` | `548` lines
- **Exports**: `TutorialProvider`

### [`frontend/src/tutorial/TutorialSpotlight.tsx`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/frontend/src/tutorial/TutorialSpotlight.tsx)
- **Kind & Size**: `TypeScript` | `68` lines
- **Exports**: `TutorialSpotlight`

### [`frontend/src/tutorial/TutorialTooltip.tsx`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/frontend/src/tutorial/TutorialTooltip.tsx)
- **Kind & Size**: `TypeScript` | `450` lines
- **Exports**: `TutorialTooltip`

### [`frontend/src/tutorial/index.ts`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/frontend/src/tutorial/index.ts)
- **Kind & Size**: `TypeScript` | `6` lines

### [`frontend/src/tutorial/tutorialEngine.test.ts`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/frontend/src/tutorial/tutorialEngine.test.ts)
- **Kind & Size**: `TypeScript` | `92` lines

### [`frontend/src/tutorial/tutorialEngine.ts`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/frontend/src/tutorial/tutorialEngine.ts)
- **Kind & Size**: `TypeScript` | `373` lines
- **Exports**: `TUTORIAL_STORAGE_KEY`, `TUTORIAL_SESSION_KEY`, `TUTORIAL_ANALYTICS_KEY`, `TARGET_RESOLUTION_TIMEOUT_MS`, `TOUR_TARGETS`, `TUTORIAL_STEPS`, `WORKFLOW_STEP_COUNT`, `transitionTourStatus`, `workflowNumberForIndex`, `tourPanelCoordinates`

### [`frontend/src/tutorial/types.ts`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/frontend/src/tutorial/types.ts)
- **Kind & Size**: `TypeScript` | `77` lines
- **Types / Interfaces**: `RequiredActionType`, `TourMachineStatus`, `TourMachineEvent`, `TourPanelSize`, `TourPlacement`, `ResolvedTourPlacement`, `TourTargetStatus`, `TutorialAppContext`

### [`frontend/src/tutorial/useTutorial.ts`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/frontend/src/tutorial/useTutorial.ts)
- **Kind & Size**: `TypeScript` | `105` lines
- **Exports**: `defaultAppContext`, `TutorialContext`, `TutorialActionsContext`, `useTutorial`, `useTutorialActions`
- **Types / Interfaces**: `TutorialActionsValue`, `TutorialContextValue`

### [`frontend/src/utils/crossFileIntelligence.test.ts`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/frontend/src/utils/crossFileIntelligence.test.ts)
- **Kind & Size**: `TypeScript` | `250` lines

### [`frontend/src/utils/crossFileIntelligence.ts`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/frontend/src/utils/crossFileIntelligence.ts)
- **Kind & Size**: `TypeScript` | `469` lines
- **Purpose**: Cross-File Evidence Ingestion and Synthesis Engine
- **Exports**: `parseMoneyMinorUnits`, `detectFileType`, `parseCsvRows`, `analyzeCrossFileEvidence`, `detectCrossFileAnomalies`
- **Types / Interfaces**: `FileType`, `IngestionStatus`, `ExtractedCaseFacts`, `EvidenceFileRecord`, `CrossFileAnomaly`, `CrossFileAnalysisResult`

### [`frontend/src/vite-env.d.ts`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/frontend/src/vite-env.d.ts)
- **Kind & Size**: `TypeScript` | `1` lines
- **Purpose**: <reference types="vite/client" />

## 3. Frontend Build & Configuration (`frontend/`)

### [`frontend/.prettierignore`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/frontend/.prettierignore)
- **Kind & Size**: `Other` | `4` lines

### [`frontend/eslint.config.js`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/frontend/eslint.config.js)
- **Kind & Size**: `TypeScript` | `28` lines

### [`frontend/index.html`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/frontend/index.html)
- **Kind & Size**: `Other` | `13` lines

### [`frontend/package-lock.json`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/frontend/package-lock.json)
- **Kind & Size**: `Other` | `3839` lines

### [`frontend/package.json`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/frontend/package.json)
- **Kind & Size**: `Other` | `37` lines

### [`frontend/public/samples/adversarial.json`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/frontend/public/samples/adversarial.json)
- **Kind & Size**: `Other` | `15` lines

### [`frontend/public/samples/carve-sample-bundles.zip`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/frontend/public/samples/carve-sample-bundles.zip)
- **Kind & Size**: `Other` | `73` lines

### [`frontend/public/samples/contradiction.json`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/frontend/public/samples/contradiction.json)
- **Kind & Size**: `Other` | `15` lines

### [`frontend/public/samples/hinglish.json`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/frontend/public/samples/hinglish.json)
- **Kind & Size**: `Other` | `15` lines

### [`frontend/public/samples/manifest.json`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/frontend/public/samples/manifest.json)
- **Kind & Size**: `Other` | `13` lines

### [`frontend/public/samples/missing-evidence.json`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/frontend/public/samples/missing-evidence.json)
- **Kind & Size**: `Other` | `15` lines

### [`frontend/public/samples/normal.json`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/frontend/public/samples/normal.json)
- **Kind & Size**: `Other` | `15` lines

### [`frontend/public/samples/ood.json`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/frontend/public/samples/ood.json)
- **Kind & Size**: `Other` | `15` lines

### [`frontend/tsconfig.app.json`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/frontend/tsconfig.app.json)
- **Kind & Size**: `Other` | `21` lines

### [`frontend/tsconfig.json`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/frontend/tsconfig.json)
- **Kind & Size**: `Other` | `7` lines

### [`frontend/tsconfig.node.json`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/frontend/tsconfig.node.json)
- **Kind & Size**: `Other` | `10` lines

### [`frontend/vite.config.ts`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/frontend/vite.config.ts)
- **Kind & Size**: `TypeScript` | `21` lines

## 4. Machine Learning & Neural Models (`training/`)

### [`training/__init__.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/training/__init__.py)
- **Kind & Size**: `Python` | `1` lines
- **Purpose**: Training package for CARVE-FECL Quant-Risk AI.

### [`training/carve_pytorch_model.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/training/carve_pytorch_model.py)
- **Kind & Size**: `Python` | `137` lines
- **Purpose**: PyTorch Architecture for CARVE-FECL Multi-View Gated Fusion.
- **Classes**: `CarveMultiViewNet` [methods: __init__, forward]
- **Key Functions**: `compute_model_parameter_hash` *(Compute deterministic SHA-256 hash of all model pa...)*, `compute_model_parameter_norm` *(Compute total L2 norm across all model parameters....)*, `count_trainable_parameters` *(Count total trainable parameters in PyTorch model....)*

### [`training/falsification_smoke_test.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/training/falsification_smoke_test.py)
- **Kind & Size**: `Python` | `335` lines
- **Purpose**: Falsification Smoke Test: Rigorous Proof of Real PyTorch Gradient Descent.
- **Key Functions**: `extract_features_from_cases` *(Deterministically extracts multi-view tensors from...)*, `run_falsification_smoke_test`

### [`training/run_all.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/training/run_all.py)
- **Kind & Size**: `Python` | `116` lines
- **Purpose**: Master training orchestrator for FECL-Bench V2 models.
- **Key Functions**: `run_training_pipeline`

### [`training/run_comprehensive_empirical_audit.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/training/run_comprehensive_empirical_audit.py)
- **Kind & Size**: `Python` | `697` lines
- **Purpose**: Comprehensive Empirical Audit and Hardening Engine for CARVE-FECL.
- **Key Functions**: `wilson_score_interval` *(Exact Wilson score binomial confidence interval....)*, `extract_features_matrix` *(Deterministically extracts multi-view features wit...)*, `compute_loss` *(Computes expected asymmetric merchant loss....)*, `evaluate_decision_array` *(Detailed evaluation metrics from decision array....)*, `run_comprehensive_audit`

### [`training/run_empirical_study.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/training/run_empirical_study.py)
- **Kind & Size**: `Python` | `495` lines
- **Purpose**: Comprehensive Empirical Study Runner for FECL-Bench.
- **Key Functions**: `wilson_score_interval` *(Compute exact Wilson score confidence interval for...)*, `extract_features_matrix` *(Deterministically extracts multi-view feature matr...)*, `compute_metrics_from_decisions` *(Compute financial loss, CVaR, precision, recall, a...)*, `execute_study`

### [`training/save_five_seed_checkpoints.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/training/save_five_seed_checkpoints.py)
- **Kind & Size**: `Python` | `300` lines
- **Purpose**: Generate and cryptographically register per-seed PyTorch checkpoints and raw predictions.
- **Key Functions**: `sha256_file`, `extract_features`, `compute_loss`, `execute_five_seed_registration`

### [`training/verify_gpu.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/training/verify_gpu.py)
- **Kind & Size**: `Python` | `83` lines
- **Purpose**: Verify PyTorch GPU Support and Hardware Capabilities.
- **Key Functions**: `verify_gpu_environment`

## 5. Empirical Evaluation & Cost Economics (`evaluation/`)

### [`evaluation/__init__.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/evaluation/__init__.py)
- **Kind & Size**: `Python` | `1` lines
- **Purpose**: Evaluation and benchmarking package for CARVE-FECL.

### [`evaluation/ablations.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/evaluation/ablations.py)
- **Kind & Size**: `Python` | `123` lines
- **Purpose**: Architectural Ablations and Component Verification.
- **Classes**: `AblationStudySummary`
- **Key Functions**: `run_ablation_benchmarks`

### [`evaluation/attribution.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/evaluation/attribution.py)
- **Kind & Size**: `Python` | `77` lines
- **Purpose**: Performance Attribution and Merchant Loss Decomposition.
- **Classes**: `LossAttributionItem`
- **Key Functions**: `compute_loss_attribution`, `summarize_loss_attribution`

### [`evaluation/baselines.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/evaluation/baselines.py)
- **Kind & Size**: `Python` | `185` lines
- **Purpose**: Baseline Ladder Execution and Evaluation (B0 to B10).
- **Classes**: `BaselineResult`
- **Key Functions**: `get_baseline_ladder_results` *(Return the frozen baseline ladder evaluation resul...)*, `export_baseline_ladder_dict`

### [`evaluation/calibration.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/evaluation/calibration.py)
- **Kind & Size**: `Python` | `122` lines
- **Purpose**: Uncertainty Calibration, Expected Calibration Error (ECE), and Brier Score.
- **Classes**: `CalibrationMethodResult`
- **Key Functions**: `compute_ece` *(Compute Expected Calibration Error with equal-widt...)*, `compute_brier_and_nll` *(Compute Brier score and Negative Log Likelihood....)*, `run_calibration_study`, `summarize_calibration`

### [`evaluation/causal_pairs.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/evaluation/causal_pairs.py)
- **Kind & Size**: `Python` | `124` lines
- **Purpose**: Causal Minimal-Pair and Counterfactual Robustness Evaluation.
- **Classes**: `CausalScorecard`
- **Key Functions**: `_rows`, `_all_evidence`, `evaluate_causal_robustness`

### [`evaluation/cost_analysis.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/evaluation/cost_analysis.py)
- **Kind & Size**: `Python` | `111` lines
- **Purpose**: Merchant Economics and Cost-Sensitive Decision Optimization.
- **Classes**: `PolicyCostResult`
- **Key Functions**: `compute_expected_cost`, `compute_pareto_frontier` *(Compute (coverage, unsafe_pass_rate, expected_cost...)*

### [`evaluation/cross_generator.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/evaluation/cross_generator.py)
- **Kind & Size**: `Python` | `121` lines
- **Purpose**: FECL-CROSSGEN-5K Cross-Generator Syntactic Challenge Evaluation.
- **Key Functions**: `evaluate_cross_generator`

### [`evaluation/disagreement_analysis.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/evaluation/disagreement_analysis.py)
- **Kind & Size**: `Python` | `82` lines
- **Purpose**: Neural-Symbolic Disagreement and B8 vs. B10 Root-Cause Analysis.
- **Classes**: `DisagreementAnalysisResult`
- **Key Functions**: `run_disagreement_analysis`, `summarize_disagreement`

### [`evaluation/document_benchmarks.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/evaluation/document_benchmarks.py)
- **Kind & Size**: `Python` | `122` lines
- **Purpose**: Document evidence robustness evaluation across Tier C public benchmarks.
- **Key Functions**: `evaluate_document_benchmarks`

### [`evaluation/evaluate.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/evaluation/evaluate.py)
- **Kind & Size**: `Python` | `58` lines
- **Purpose**: Unified Research Evaluation Runner for CARVE-FECL.
- **Key Functions**: `run_full_evaluation`

### [`evaluation/evaluate_all.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/evaluation/evaluate_all.py)
- **Kind & Size**: `Python` | `275` lines
- **Purpose**: Master Quant-Risk Research Evaluation Suite for CARVE-FECL.
- **Key Functions**: `run_complete_evaluation_suite`, `main`

### [`evaluation/evidence_value.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/evaluation/evidence_value.py)
- **Kind & Size**: `Python` | `128` lines
- **Purpose**: Marginal Evidence Value and Sequential Active Acquisition (VOI).
- **Classes**: `SourceAlphaResult`, `AcquisitionPolicyResult`
- **Key Functions**: `evaluate_evidence_sources`, `evaluate_acquisition_policies`, `summarize_evidence_value`

### [`evaluation/externality.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/evaluation/externality.py)
- **Kind & Size**: `Python` | `195` lines
- **Purpose**: Comprehensive Externality Matrix Evaluation across all partitions.
- **Key Functions**: `evaluate_externality_matrix`

### [`evaluation/learning_curves.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/evaluation/learning_curves.py)
- **Kind & Size**: `Python` | `212` lines
- **Purpose**: Learning curves and sample-efficiency analysis for FECL-Bench V2.
- **Key Functions**: `compute_learning_curves` *(Generates empirical learning curves across sample ...)*, `compute_sample_efficiency` *(Calculates N_required(model, L*) for target risk l...)*, `run_learning_curve_analysis`

### [`evaluation/mechanism_holdout.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/evaluation/mechanism_holdout.py)
- **Kind & Size**: `Python` | `105` lines
- **Purpose**: Causal Mechanism Holdout Benchmark.
- **Classes**: `MechanismHoldoutResult`
- **Key Functions**: `run_mechanism_holdout_evaluation`, `summarize_mechanism_holdout`

### [`evaluation/merchant_economics.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/evaluation/merchant_economics.py)
- **Kind & Size**: `Python` | `81` lines
- **Purpose**: Quantitative Merchant Economics and Net Merchant Edge Analysis.
- **Classes**: `EconomicProfile`
- **Key Functions**: `compute_merchant_economics`

### [`evaluation/merchant_monte_carlo.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/evaluation/merchant_monte_carlo.py)
- **Kind & Size**: `Python` | `130` lines
- **Purpose**: Monte Carlo simulation of projected merchant economics.
- **Key Functions**: `run_merchant_monte_carlo`

### [`evaluation/ood_eval.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/evaluation/ood_eval.py)
- **Kind & Size**: `Python` | `78` lines
- **Purpose**: Out-of-Distribution (OOD) Detection and Open-Set Robustness Evaluation.
- **Classes**: `OodEvaluationResult`
- **Key Functions**: `compute_roc_pr_metrics` *(Compute AUROC, AUPR, and FPR@95TPR via rank statis...)*, `evaluate_ood_robustness`

### [`evaluation/policy_frontier.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/evaluation/policy_frontier.py)
- **Kind & Size**: `Python` | `125` lines
- **Purpose**: Risk-Coverage Pareto Frontier and Operational Policy Presets.
- **Classes**: `PolicyPreset`
- **Key Functions**: `get_policy_presets`, `generate_policy_frontier_artifact`

### [`evaluation/regime_eval.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/evaluation/regime_eval.py)
- **Kind & Size**: `Python` | `99` lines
- **Purpose**: Operational Regime Detection and Edge Decay Monitoring.
- **Classes**: `RegimeMetrics`
- **Key Functions**: `evaluate_operational_regimes`, `summarize_regimes`

### [`evaluation/rule_holdout.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/evaluation/rule_holdout.py)
- **Kind & Size**: `Python` | `77` lines
- **Purpose**: Rule-Holdout Experiment: Separating Learned Induction from Formal SMT Solving.
- **Key Functions**: `evaluate_rule_holdout`

### [`evaluation/semantic_minimal_pairs.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/evaluation/semantic_minimal_pairs.py)
- **Kind & Size**: `Python` | `83` lines
- **Purpose**: Semantic Minimal-Pair Stress Benchmark for Financial Claim Induction.
- **Classes**: `SemanticPairResult`
- **Key Functions**: `run_semantic_minimal_pairs` *(Execute semantic minimal pair evaluation on the co...)*, `summarize_semantic_pairs`

### [`evaluation/shift_eval.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/evaluation/shift_eval.py)
- **Kind & Size**: `Python` | `107` lines
- **Purpose**: Distribution Shift, Non-Stationarity, and Semantic Stress Evaluation.
- **Classes**: `ShiftScenarioResult`
- **Key Functions**: `run_shift_evaluation`, `summarize_shift_evaluation`

### [`evaluation/stress_test.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/evaluation/stress_test.py)
- **Kind & Size**: `Python` | `103` lines
- **Purpose**: Severe Defense-Only Stress Testing and Circuit Breaker Verification.
- **Classes**: `StressScenarioReport`
- **Key Functions**: `run_stress_test_suite`, `summarize_stress_tests`

### [`evaluation/subgroup_analysis.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/evaluation/subgroup_analysis.py)
- **Kind & Size**: `Python` | `107` lines
- **Purpose**: Group-Conditional Risk and Subgroup Robustness Analysis.
- **Classes**: `SubgroupMetric`
- **Key Functions**: `evaluate_subgroups` *(Partition cases by amount bucket and completeness,...)*

### [`evaluation/tail_risk.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/evaluation/tail_risk.py)
- **Kind & Size**: `Python` | `115` lines
- **Purpose**: Tail Risk and Value-at-Risk (VaR / CVaR) Evaluation.
- **Classes**: `TailRiskMetrics`
- **Key Functions**: `compute_var_cvar` *(Compute empirical VaR and CVaR (Expected Shortfall...)*, `get_tail_risk_benchmarks`, `summarize_tail_risk`

### [`evaluation/temporal_backtest.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/evaluation/temporal_backtest.py)
- **Kind & Size**: `Python` | `116` lines
- **Purpose**: Temporal Walk-Forward Backtest and Point-in-Time Correctness Evaluation.
- **Classes**: `WalkForwardFoldResult`
- **Key Functions**: `run_temporal_backtest`, `summarize_temporal_backtest`

## 6. Data Pipeline & SCM Generators (`data_pipeline/`)

### [`data_pipeline/__init__.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/data_pipeline/__init__.py)
- **Kind & Size**: `Python` | `1` lines
- **Purpose**: Data pipeline package for FECL-Bench V2.

### [`data_pipeline/fecl_scm_v2.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/data_pipeline/fecl_scm_v2.py)
- **Kind & Size**: `Python` | `277` lines
- **Purpose**: FECL-SCM-V2: Structural Causal Simulator for Chargeback Evidence Consistency.
- **Classes**: `FinancialLifecycleState`, `FeclScmV2Simulator` [methods: __init__, sample_case, _render_customer_text]
- **Key Functions**: `generate_partition_metadata` *(Generates the split metadata manifest for the 120,...)*

### [`data_pipeline/prepare_all.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/data_pipeline/prepare_all.py)
- **Kind & Size**: `Python` | `50` lines
- **Purpose**: Data pipeline orchestrator: prepares manifests and validates all 4 benchmark tiers.
- **Key Functions**: `prepare_all_data`

## 7. External Validation Suite (`external_validation/`)

### [`external_validation/ANNOTATOR_GUIDE.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/external_validation/ANNOTATOR_GUIDE.md)
- **Kind & Size**: `Doc` | `21` lines
- **Purpose**: Annotator Guidelines: Independent Dispute Verification — **Standard:** Section 60–62 of Final Directive

### [`external_validation/AUTHOR_GUIDE.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/external_validation/AUTHOR_GUIDE.md)
- **Kind & Size**: `Doc` | `46` lines
- **Purpose**: Author Guidelines: External Independent Blind Challenge Pack — **Standard:** Section 26 of Final Directive

### [`external_validation/adjudication_protocol.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/external_validation/adjudication_protocol.md)
- **Kind & Size**: `Doc` | `23` lines
- **Purpose**: Adjudication Protocol: Resolving Annotator Disagreements — **Standard:** Section 60–62 of Final Directive

### [`external_validation/annotation_schema.json`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/external_validation/annotation_schema.json)
- **Kind & Size**: `Contract` | `35` lines
- **Purpose**: Human Blind Challenge Annotation Schema

### [`external_validation/blind_manifest.json`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/external_validation/blind_manifest.json)
- **Kind & Size**: `Other` | `25` lines

### [`external_validation/case_schema.json`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/external_validation/case_schema.json)
- **Kind & Size**: `Contract` | `63` lines
- **Purpose**: Human Blind Challenge Case Schema

### [`external_validation/evaluate_external.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/external_validation/evaluate_external.py)
- **Kind & Size**: `Python` | `41` lines
- **Purpose**: Evaluation runner for external challenge sets.
- **Key Functions**: `evaluate_external_challenges`

### [`external_validation/inter_annotator_agreement.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/external_validation/inter_annotator_agreement.py)
- **Kind & Size**: `Python` | `54` lines
- **Purpose**: Inter-annotator agreement computation for human-blind challenge cases.
- **Key Functions**: `compute_cohens_kappa`, `evaluate_agreement_file`

## 8. Backend Testing & Verification Suite (`backend/tests/`)

### [`backend/tests/__init__.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/backend/tests/__init__.py)
- **Kind & Size**: `Python` | `1` lines
- **Purpose**: Backend test package for stable type-checker module discovery.

### [`backend/tests/adversarial/__init__.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/backend/tests/adversarial/__init__.py)
- **Kind & Size**: `Python` | `1` lines
- **Purpose**: Adversarial judge test cases designed to stress-test PRAMAAN invariants.

### [`backend/tests/adversarial/test_adversarial_judge_cases.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/backend/tests/adversarial/test_adversarial_judge_cases.py)
- **Kind & Size**: `Python` | `357` lines
- **Purpose**: Adversarial judge test cases specified in Section 62 of the Master Directive.
- **Key Functions**: `test_adversarial_1_beautifully_worded_false_claim` *(Eloquent and authoritative-sounding claim with zer...)*, `test_adversarial_2_poorly_worded_true_claim` *(Broken English with slang/typos matching ledger re...)*, `test_adversarial_3_correct_amount_wrong_currency` *(Claim amount matches captured integer, but currenc...)*, `test_adversarial_4_correct_amount_wrong_arn_reference` *(Claim matches amount, but references an ARN absent...)*, `test_adversarial_5_partial_refunds_summing_correctly` *(Multiple partial refunds summing exactly to captur...)*, `test_adversarial_6_duplicate_refund_rows_trigger_review` *(Duplicate refund record rows must be caught and fa...)*, `test_adversarial_7_future_settlement_evidence_pruned` *(Evidence dated after decision point-in-time snapsh...)*, `test_adversarial_8_missing_capture_fails_to_review` *(Missing payment capture snapshot cannot be certifi...)*

### [`backend/tests/chaos/__init__.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/backend/tests/chaos/__init__.py)
- **Kind & Size**: `Python` | `1` lines
- **Purpose**: Chaos and fault injection testing package.

### [`backend/tests/chaos/test_chaos_fault_injection.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/backend/tests/chaos/test_chaos_fault_injection.py)
- **Kind & Size**: `Python` | `188` lines
- **Purpose**: Chaos and fault injection tests for PRAMAAN.
- **Classes**: `TimingOutExtractor` [methods: extract], `CrashingExtractor` [methods: extract]
- **Key Functions**: `test_solver_model_timeout_fails_closed_to_review` *(Safety Invariant: Technical timeout must never pro...)*, `test_crashed_extractor_in_case_pipeline_fails_closed` *(Case evaluation under model/extractor crash routes...)*, `test_checkpoint_corruption_fails_verification` *(Modifying one byte in a frozen release manifest mu...)*, `test_circuit_breaker_transitions_under_load_and_risk` *(Risk-budget exhaustion drives circuit breaker from...)*

### [`backend/tests/generators/__init__.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/backend/tests/generators/__init__.py)
- **Kind & Size**: `Python` | `7` lines
- **Purpose**: PRAMAAN / CARVE-FECL Test Generation Engine.

### [`backend/tests/generators/strategies.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/backend/tests/generators/strategies.py)
- **Kind & Size**: `Python` | `208` lines
- **Purpose**: Reusable, composable Hypothesis strategies for the PRAMAAN test generation engine.
- **Key Functions**: `_utc_iso`, `corrupt_text`, `razorpay_webhook_payload_st`

### [`backend/tests/ml/__init__.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/backend/tests/ml/__init__.py)
- **Kind & Size**: `Python` | `3` lines
- **Purpose**: AI/ML research integrity, calibration, and anti-leakage test modules for PRAMAAN.

### [`backend/tests/ml/test_calibration_and_ood.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/backend/tests/ml/test_calibration_and_ood.py)
- **Kind & Size**: `Python` | `72` lines
- **Purpose**: Calibration, selective prediction monotonicity, and OOD shift tests for PRAMAAN.
- **Key Functions**: `test_perfect_calibration_yields_near_zero_ece` *(When predicted confidence matches empirical accura...)*, `test_severe_overconfidence_yields_high_ece` *(Predicting 99% confidence for all negative samples...)*, `test_selective_prediction_monotonicity` *(Widening the review window [0.5 - w, 0.5 + w] must...)*, `test_ood_anomaly_scores_safely_route_to_review` *(OOD samples with anomaly scores exceeding the thre...)*

### [`backend/tests/ml/test_counterfactual_minimal_pairs.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/backend/tests/ml/test_counterfactual_minimal_pairs.py)
- **Kind & Size**: `Python` | `80` lines
- **Purpose**: Semantic minimal pair and counterfactual robustness tests for PRAMAAN.
- **Key Functions**: `test_counterfactual_amount_flip_changes_financial_feasibility` *(Surrounding sentence is identical; altering amount...)*, `test_polarity_minimal_pair_flips_affirmation` *(Adding negation ('not') to claim text flips affirm...)*, `test_paraphrase_metamorphic_amount_invariance` *(Extracting amounts from English and Hinglish templ...)*

### [`backend/tests/ml/test_data_split_integrity.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/backend/tests/ml/test_data_split_integrity.py)
- **Kind & Size**: `Python` | `95` lines
- **Purpose**: Data split integrity and checkpoint reproducibility tests for PRAMAAN.
- **Key Functions**: `_load_ids`, `test_data_splits_are_strictly_disjoint` *(Case identifiers across train, dev, calibration, a...)*, `test_data_manifest_counts_match_disk_files` *(Split manifest counts must match file record count...)*, `test_checkpoint_reproducibility_smoke` *(Verify that checkpoint manifest contains valid SHA...)*

### [`backend/tests/ml/test_ml_leakage.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/backend/tests/ml/test_ml_leakage.py)
- **Kind & Size**: `Python` | `97` lines
- **Purpose**: AI/ML Research Integrity & Label Leakage Prevention Tests for PRAMAAN.
- **Key Functions**: `test_no_forbidden_target_tokens_in_feature_manifests` *(Feature names and metadata must never include targ...)*, `test_data_splits_contain_no_leaked_target_column_in_features` *(Verify that dataset splits do not expose the targe...)*, `test_single_feature_shortcut_probes_below_suspicion_threshold` *(Verify that no single numerical feature acts as a ...)*

### [`backend/tests/property/__init__.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/backend/tests/property/__init__.py)
- **Kind & Size**: `Python` | `3` lines
- **Purpose**: Property-based invariant testing modules for PRAMAAN / CARVE-FECL.

### [`backend/tests/property/test_money_properties.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/backend/tests/property/test_money_properties.py)
- **Kind & Size**: `Python` | `203` lines
- **Purpose**: Generative property-based testing for financial money invariants in PRAMAAN.
- **Key Functions**: `_dev_rows`, `test_refund_summation_ordering_independence` *(Summing arbitrary refund partitions must yield ide...)*, `test_parse_format_roundtrip_fidelity` *(Formatting an exact rupee/paise value and parsing ...)*, `test_duplicate_refund_id_does_not_increase_settled` *(Feeding duplicate refund records with the same ID ...)*, `test_over_refund_triggers_formal_contradiction` *(When settled refunds exceed captured payment, Z3 c...)*, `test_currency_mismatch_never_contest_ready` *(A claim in USD/EUR against an INR payment must nev...)*, `test_malformed_currency_strings_rejected` *(Sub-paise, negative, NaN, Inf, and malformed input...)*, `test_amount_fits_within_sqlite_signed_64bit_bounds` *(All generated money minor quantities must fit in a...)*

### [`backend/tests/property/test_provenance_and_grounding.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/backend/tests/property/test_provenance_and_grounding.py)
- **Kind & Size**: `Python` | `79` lines
- **Purpose**: Provenance, exact span grounding, and evidence integrity tests for PRAMAAN.
- **Key Functions**: `test_unique_quote_resolves_to_exact_grounded_span` *(A quote appearing exactly once in a document resol...)*, `test_missing_quote_resolves_to_ungrounded` *(A quote not present in the document must return UN...)*, `test_duplicate_quote_resolves_to_ambiguous_and_fails_closed` *(If a quote occurs 2 or more times, resolve_exact_q...)*, `test_one_byte_mutation_alters_sha256_digest` *(Modifying even 1 character in evidence content pro...)*

### [`backend/tests/property/test_required_evidence_powerset.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/backend/tests/property/test_required_evidence_powerset.py)
- **Kind & Size**: `Python` | `99` lines
- **Purpose**: Required-evidence powerset testing for PRAMAAN.
- **Key Functions**: `_build_context`, `test_required_evidence_all_subsets_fail_closed_unless_complete` *(Test all 2^3 = 8 subsets of {payment_snapshot, ref...)*

### [`backend/tests/property/test_temporal_properties.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/backend/tests/property/test_temporal_properties.py)
- **Kind & Size**: `Python` | `170` lines
- **Purpose**: Generative property-based testing for temporal invariants in PRAMAAN.
- **Key Functions**: `_sample_row_with_evidence`, `test_point_in_time_isolation_prunes_future_evidence` *(Evidence available in the future relative to decis...)*, `test_adding_future_evidence_preserves_historical_snapshot` *(Appending future-dated evidence to an inventory mu...)*, `test_timezone_offsets_normalize_to_utc` *(Timestamps formatted with IST offset (+05:30) must...)*, `test_point_in_time_comparison_uses_instants_not_iso_text_order`, `test_refund_before_capture_ordering_invariant` *(A refund timestamp strictly before payment capture...)*

### [`backend/tests/property/test_z3_differential_oracle.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/backend/tests/property/test_z3_differential_oracle.py)
- **Kind & Size**: `Python` | `127` lines
- **Purpose**: Differential testing: Independent Python oracle vs Z3 SMT solver in PRAMAAN.
- **Key Functions**: `python_financial_oracle` *(Independent pure-Python oracle for financial ledge...)*, `z3_financial_verifier` *(Microsoft Z3 QF_LIA solver verification of identic...)*, `test_differential_oracle_matches_z3_solver` *(The independent Python oracle and the Z3 SMT solve...)*, `test_smt_solver_timeout_fails_closed` *(Artificially timed-out solver must report non-SAT ...)*

### [`backend/tests/security/__init__.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/backend/tests/security/__init__.py)
- **Kind & Size**: `Python` | `3` lines
- **Purpose**: Security, adversarial input, and injection testing modules for PRAMAAN.

### [`backend/tests/security/test_security_adversarial.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/backend/tests/security/test_security_adversarial.py)
- **Kind & Size**: `Python` | `131` lines
- **Purpose**: Security, payload injection, HMAC tampering, and secret isolation tests for PRAMAAN.
- **Key Functions**: `test_malicious_payloads_remain_inert_text` *(Document text containing injections must be treate...)*, `test_hmac_tampering_is_strictly_rejected` *(Modifying 1 byte, adding whitespace, or using wron...)*, `test_structured_log_events_never_leak_secrets` *(Logs must not serialize webhook secrets, credentia...)*, `test_path_traversal_and_malicious_filenames_handled_safely` *(Malicious or unicode file identifiers must not esc...)*

### [`backend/tests/stateful/__init__.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/backend/tests/stateful/__init__.py)
- **Kind & Size**: `Python` | `3` lines
- **Purpose**: Stateful and concurrency testing modules for PRAMAAN / CARVE-FECL.

### [`backend/tests/stateful/test_concurrency_leases.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/backend/tests/stateful/test_concurrency_leases.py)
- **Kind & Size**: `Python` | `156` lines
- **Purpose**: Stateful concurrency and worker lease tests for PRAMAAN.
- **Key Functions**: `_create_test_case`, `test_concurrent_worker_claim_is_mutually_exclusive` *(16 concurrent threads attempting to claim a single...)*, `test_stale_worker_lease_recovery_and_late_completion_rejection` *(Worker A stalls past lease_until; Worker B recover...)*, `test_lease_boundary_timing` *(Validate lease boundary: lease - 1ms is active; le...)*, `test_canonical_decision_uniqueness_per_case` *(Verify that a dispute case in the authoritative da...)*

### [`backend/tests/stateful/test_crash_consistency.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/backend/tests/stateful/test_crash_consistency.py)
- **Kind & Size**: `Python` | `133` lines
- **Purpose**: Crash-consistency and recovery property tests for PRAMAAN.
- **Key Functions**: `test_crash_before_commit_guarantees_atomic_rollback` *(If a process crashes or raises an exception before...)*, `test_crash_during_worker_execution_allows_safe_restart` *(Worker crashes mid-execution; job is safely claime...)*, `test_duplicate_case_id_rejected_atomically` *(Inserting a duplicate case ID violates PRIMARY KEY...)*

### [`backend/tests/stateful/test_state_machine.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/backend/tests/stateful/test_state_machine.py)
- **Kind & Size**: `Python` | `154` lines
- **Purpose**: Hypothesis RuleBasedStateMachine tests for dispute lifecycles and state transitions in PRAMAAN.
- **Classes**: `LifecycleState`, `SimulatedCase`, `DisputeLifecycleStateMachine` [methods: __init__, create_case, queue_case, attach_evidence_and_evaluate]

### [`backend/tests/test_ai_lab_api.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/backend/tests/test_ai_lab_api.py)
- **Kind & Size**: `Python` | `95` lines
- **Key Functions**: `_detail`, `test_case_ai_lab_is_offline_explainable_and_advisory`

### [`backend/tests/test_ai_lab_model.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/backend/tests/test_ai_lab_model.py)
- **Kind & Size**: `Python` | `69` lines
- **Key Functions**: `test_trainer_rejects_holdout_before_reading_it`, `test_dev_ablation_is_artifact_backed_and_does_not_promote_weaker_model`, `test_inference_nominates_exact_quote_and_features_without_probability`, `test_bounded_retrieval_returns_exact_allowlisted_citations`

### [`backend/tests/test_ai_research_api.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/backend/tests/test_ai_research_api.py)
- **Kind & Size**: `Python` | `56` lines
- **Key Functions**: `test_ai_research_reads_generated_dev_artifact`, `test_ai_research_rejects_holdout_projection`, `test_fecl_v2_reads_frozen_generated_artifacts`, `test_fecl_v2_rejects_unbound_analysis`

### [`backend/tests/test_ai_research_study.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/backend/tests/test_ai_research_study.py)
- **Kind & Size**: `Python` | `70` lines
- **Key Functions**: `test_sentence_dataset_matches_inference_granularity_and_exact_quotes`, `test_calibration_and_selective_metrics_are_computed_from_predictions`, `test_literal_contradiction_baseline_is_not_a_strawman`, `test_dev_study_is_artifact_ready_and_cannot_change_runtime_selection`, `test_challenge_dataset_is_versioned_and_split_before_model_execution`

### [`backend/tests/test_benchmark_generator.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/backend/tests/test_benchmark_generator.py)
- **Kind & Size**: `Python` | `141` lines
- **Key Functions**: `read_json`, `tree_digest`, `case_paths`, `generated_root`, `test_generator_is_reproducible_and_family_separated`, `test_labels_are_balanced_for_diagnostic_not_prevalence_claims`, `test_runtime_bundle_excludes_family_and_ground_truth_labels`, `test_required_hard_negative_and_adversarial_families_exist`

### [`backend/tests/test_benchmark_integrity.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/backend/tests/test_benchmark_integrity.py)
- **Kind & Size**: `Python` | `63` lines
- **Key Functions**: `frozen_dataset`, `test_freeze_writes_manifest_hashes_and_is_one_way`, `test_dev_is_default_and_does_not_require_confirmation`, `test_holdout_requires_explicit_confirmation`, `test_verifier_detects_holdout_file_changes`

### [`backend/tests/test_carve_proof.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/backend/tests/test_carve_proof.py)
- **Kind & Size**: `Python` | `158` lines
- **Key Functions**: `_rows`, `_all_evidence`, `test_proof_compiler_matches_every_train_dev_and_calibration_label`, `test_initially_incomplete_case_fails_closed_with_specific_evidence`, `test_model_score_cannot_override_formal_contradiction`, `test_corrupt_evidence_hash_routes_to_review`, `test_ood_and_missing_authoritative_state_route_to_review`, `test_point_in_time_snapshot_filters_future_evidence`

### [`backend/tests/test_carve_research_api.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/backend/tests/test_carve_research_api.py)
- **Kind & Size**: `Python` | `39` lines
- **Key Functions**: `test_carve_research_is_bound_to_one_shot_receipt`, `test_carve_research_endpoint`, `test_quant_risk_endpoint`

### [`backend/tests/test_case_api.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/backend/tests/test_case_api.py)
- **Kind & Size**: `Python` | `386` lines
- **Key Functions**: `seed_case`, `client_with_queue`, `test_queue_filter_treats_sql_injection_text_as_a_parameter`, `test_queue_contract_sort_filters_and_paginates`, `test_queue_rejects_invalid_filters_and_cursor`, `test_case_workspace_returns_normalized_sources_and_no_provider_response`, `test_case_workspace_returns_not_found_envelope`, `test_reprocess_after_repair_queues_durable_local_job_and_audit`

### [`backend/tests/test_case_pipeline.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/backend/tests/test_case_pipeline.py)
- **Kind & Size**: `Python` | `119` lines
- **Key Functions**: `read_json`, `load_fixture`, `test_seeded_golden_cases_match_expected_gate_state`, `test_extractor_outage_is_review_and_never_pass`, `test_ambiguous_grounding_is_review_and_never_block`, `test_future_refund_promise_with_no_ledger_match_reviews_not_blocks`, `test_missing_communication_skips_extraction_and_routes_to_review`

### [`backend/tests/test_config.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/backend/tests/test_config.py)
- **Kind & Size**: `Python` | `20` lines
- **Key Functions**: `test_defaults_use_offline_replay_without_external_inference`, `test_live_mode_requires_model_key`

### [`backend/tests/test_database.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/backend/tests/test_database.py)
- **Kind & Size**: `Python` | `142` lines
- **Key Functions**: `build_case`, `test_schema_enables_wal_foreign_keys_and_required_indexes`, `test_normalized_case_preserves_raw_reason_and_utc_timestamp`, `test_domain_rejects_float_money_and_naive_timestamp`, `test_database_constraints_reject_invalid_money_and_orphans`, `test_job_is_durable_across_connections`

### [`backend/tests/test_decision.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/backend/tests/test_decision.py)
- **Kind & Size**: `Python` | `92` lines
- **Key Functions**: `finding`, `decision_for`, `test_no_findings_is_pass_with_canonical_boundary_copy`, `test_review_finding_cannot_pass`, `test_verified_material_conflict_blocks_and_remains_local_language`, `test_decision_serialization_matches_closed_json_schema`, `test_any_review_only_result_never_passes`

### [`backend/tests/test_demo_fixtures.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/backend/tests/test_demo_fixtures.py)
- **Kind & Size**: `Python` | `66` lines
- **Key Functions**: `read_json`, `test_demo_fixture_uses_documented_event_shape_and_preserves_raw_reason`, `test_demo_fixtures_cover_all_gate_states_without_holdout_data`, `test_structured_fixture_relationships_are_internally_valid`

### [`backend/tests/test_demo_script.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/backend/tests/test_demo_script.py)
- **Kind & Size**: `Python` | `59` lines
- **Key Functions**: `_seconds`, `_timeline`, `test_demo_timelines_are_contiguous_and_exact`, `test_pitch_discloses_saved_metrics_and_boundaries`

### [`backend/tests/test_evaluation_api.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/backend/tests/test_evaluation_api.py)
- **Kind & Size**: `Python` | `98` lines
- **Key Functions**: `saved_run`, `test_evaluation_endpoint_says_not_measured_when_no_artifact`, `test_evaluation_endpoint_projects_newest_saved_artifact_only`, `test_evaluation_endpoint_rejects_tampered_saved_artifact`

### [`backend/tests/test_evaluation_artifact.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/backend/tests/test_evaluation_artifact.py)
- **Kind & Size**: `Python` | `111` lines
- **Key Functions**: `artifact`, `test_writer_records_provenance_and_matches_json_schema`, `test_writer_digest_matches_exact_saved_bytes_and_refuses_overwrite`, `test_config_hash_changes_with_bytes_and_is_order_independent`, `test_contract_rejects_duplicate_case_ids_and_naive_timestamp`, `test_run_id_cannot_escape_output_directory`

### [`backend/tests/test_evaluation_metrics.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/backend/tests/test_evaluation_metrics.py)
- **Kind & Size**: `Python` | `152` lines
- **Key Functions**: `claim`, `sample_predictions`, `test_gate_counts_ratios_confusion_and_slices_are_computed`, `test_claim_metrics_use_exact_type_quote_span_and_normalized_values`, `test_cost_sensitivity_uses_visible_unitless_inputs`, `test_baseline_delta_is_derived_from_same_metric_contract`, `test_perfect_predictions_are_permutation_invariant`

### [`backend/tests/test_evaluator.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/backend/tests/test_evaluator.py)
- **Kind & Size**: `Python` | `70` lines
- **Key Functions**: `test_dev_evaluator_writes_only_computed_case_level_metrics`, `test_holdout_evaluator_refuses_access_before_release_freeze`, `test_release_freeze_detects_manifest_tampering`

### [`backend/tests/test_extraction.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/backend/tests/test_extraction.py)
- **Kind & Size**: `Python` | `143` lines
- **Key Functions**: `request`, `result`, `test_claim_serialization_matches_closed_contract`, `test_authority_confidence_offsets_and_tools_are_rejected`, `test_result_is_bound_to_document_and_request_allowlist`, `test_request_rejects_duplicate_or_empty_allowlist`, `test_request_allows_only_v1_text_and_json_media_types`, `test_protocol_accepts_bounded_extractor_without_extra_authority`

### [`backend/tests/test_failure_demo.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/backend/tests/test_failure_demo.py)
- **Kind & Size**: `Python` | `27` lines
- **Key Functions**: `test_injected_outage_reviews_then_offline_replay_recovers`

### [`backend/tests/test_fecl_v2_artifacts.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/backend/tests/test_fecl_v2_artifacts.py)
- **Kind & Size**: `Python` | `98` lines
- **Key Functions**: `_rows`, `_sha256`, `test_fecl_v2_manifest_hashes_and_family_isolation`, `test_fecl_v2_minimal_pairs_are_balanced_and_change_one_material_claim`, `test_fecl_v2_dev_artifact_is_generated_and_cannot_change_runtime`, `test_fecl_v2_test_matches_freeze_and_keeps_research_winner_out_of_runtime`, `test_fecl_v2_posthoc_analysis_is_bound_to_test_without_tuning`

### [`backend/tests/test_fecl_v4_1_integrity.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/backend/tests/test_fecl_v4_1_integrity.py)
- **Kind & Size**: `Python` | `84` lines
- **Key Functions**: `_rows`, `test_v41_passes_all_v4_structural_checks`, `test_v41_formal_proof_preserves_outcomes_and_records_annotation_debt`, `test_v41_oracle_acquires_only_the_minimal_hidden_requirements`

### [`backend/tests/test_fecl_v4_2_integrity.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/backend/tests/test_fecl_v4_2_integrity.py)
- **Kind & Size**: `Python` | `69` lines
- **Key Functions**: `_rows`, `test_manifest_hashes_and_family_isolation`, `test_label_blind_proof_on_non_test_protocol_splits`, `test_initial_state_never_unsafe_passes`, `test_single_causal_pair_corrections`

### [`backend/tests/test_fecl_v4_benchmark.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/backend/tests/test_fecl_v4_benchmark.py)
- **Kind & Size**: `Python` | `130` lines
- **Key Functions**: `_json`, `_rows`, `_sha`, `_canonical`, `test_v4_counts_and_file_hashes_match_manifest`, `test_v4_families_templates_entities_and_pairs_do_not_cross_splits`, `test_v4_pair_repair_targets_the_changed_causal_field`, `test_v4_provenance_hashes_grounding_and_visibility_are_exact`

### [`backend/tests/test_grounding.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/backend/tests/test_grounding.py)
- **Kind & Size**: `Python` | `125` lines
- **Key Functions**: `extracted_claim`, `test_unique_exact_quote_resolves_exclusive_character_span`, `test_missing_or_whitespace_changed_quote_is_ungrounded`, `test_repeated_exact_quote_is_ambiguous`, `test_money_normalization_is_inr_only_and_integer_minor_units`, `test_integer_rupee_amount_round_trips_to_exact_paise`, `test_timestamp_requires_explicit_timezone_and_normalizes_utc`, `test_reference_normalization_never_extracts_from_prose`

### [`backend/tests/test_health.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/backend/tests/test_health.py)
- **Kind & Size**: `Python` | `86` lines
- **Key Functions**: `test_health_reports_real_database_and_worker_state_without_secrets`, `test_health_worker_status_is_derived_from_durable_queue`, `test_health_degrades_when_database_path_is_unusable`

### [`backend/tests/test_hft_fintech_invariants.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/backend/tests/test_hft_fintech_invariants.py)
- **Kind & Size**: `Python` | `157` lines
- **Purpose**: Property-based testing for high-integrity quantitative and financial invariants.
- **Key Functions**: `test_partial_refund_summation_commutativity` *(Summing refunds in any arbitrary order must yield ...)*, `test_parse_inr_minor_units_exact_paise` *(Valid currency strings formatted as rupees.paise m...)*, `test_parse_inr_sub_paise_rejected` *(Fractional paise (e.g. 3 or more decimal places) m...)*, `test_parse_inr_rejects_malformed_inputs` *(Non-numeric tokens, invalid currencies, and negati...)*, `test_point_in_time_snapshot_invariant` *(Evidence with available_time > decision_time must ...)*, `test_automation_risk_budget_monotonicity` *(Consumed risk must be monotonically non-decreasing...)*, `test_sqlite_integer_storage_bounds` *(Authoritative money integers must strictly fit wit...)*, `test_sqlite_integer_overflow_detection` *(Integers exceeding signed 64-bit limits (2^63 - 1)...)*

### [`backend/tests/test_ingestion.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/backend/tests/test_ingestion.py)
- **Kind & Size**: `Python` | `164` lines
- **Key Functions**: `client_for`, `headers`, `test_authenticated_created_event_persists_event_case_and_job_atomically`, `test_duplicate_event_id_is_safe_and_creates_no_second_logical_job`, `test_forward_compatible_extra_fields_are_tolerated`, `test_documented_non_mvp_event_is_persisted_without_business_job`, `test_signature_rejection_happens_before_payload_parsing`, `test_missing_event_id_is_rejected_after_valid_authentication`

### [`backend/tests/test_jobs.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/backend/tests/test_jobs.py)
- **Kind & Size**: `Python` | `160` lines
- **Key Functions**: `seed_job`, `job_row`, `test_live_lease_prevents_second_claim`, `test_stale_processing_job_is_reclaimed_after_worker_restart`, `test_successful_worker_completes_job_once`, `test_transient_failure_retries_only_to_bound`, `test_permanent_failure_is_not_retried`, `test_worker_failure_log_contains_ids_and_safe_failure_code`

### [`backend/tests/test_no_razorpay_writes.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/backend/tests/test_no_razorpay_writes.py)
- **Kind & Size**: `Python` | `45` lines
- **Key Functions**: `test_static_runtime_boundary_has_no_razorpay_write_client_or_endpoint`, `test_http_surface_contains_only_inbound_webhook_and_local_workflow_routes`

### [`backend/tests/test_observability.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/backend/tests/test_observability.py)
- **Kind & Size**: `Python` | `85` lines
- **Key Functions**: `test_structured_log_schema_rejects_evidence_prompt_and_secret_fields`, `test_structured_log_is_single_line_json_with_only_allowlisted_metadata`, `test_provider_failure_logs_only_hash_and_safe_metadata`

### [`backend/tests/test_offline_replay.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/backend/tests/test_offline_replay.py)
- **Kind & Size**: `Python` | `147` lines
- **Key Functions**: `config_hash`, `write_cache`, `read_json`, `test_offline_replay_has_same_grounding_and_policy_path_as_regex`, `test_missing_replay_entry_routes_to_review_without_fallback`, `test_committed_cache_is_strict_and_covers_three_demo_documents`, `test_cache_key_changes_with_prompt_version`, `test_cache_schema_rejects_unknown_fields_and_versions`

### [`backend/tests/test_profile.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/backend/tests/test_profile.py)
- **Kind & Size**: `Python` | `55` lines
- **Key Functions**: `test_canonical_profile_loads_with_suggested_evidence_semantics`, `test_missing_suggested_evidence_is_exposed_for_review`, `test_unsupported_local_profile_resolves_out_of_scope`, `test_raw_reason_code_is_not_used_as_local_profile`

### [`backend/tests/test_regex_baseline.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/backend/tests/test_regex_baseline.py)
- **Kind & Size**: `Python` | `96` lines
- **Key Functions**: `extract`, `test_processed_claim_amount_and_reference_use_exact_sentence`, `test_declared_hard_negatives_do_not_emit_processed_claim`, `test_request_received_is_requested_not_approved_or_processed`, `test_partial_refund_amount_is_preserved_without_full_inference`, `test_request_allowlist_is_enforced`, `test_baseline_uses_same_grounding_pipeline`

### [`backend/tests/test_registry.json`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/backend/tests/test_registry.json)
- **Kind & Size**: `Other` | `195` lines

### [`backend/tests/test_required_evidence.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/backend/tests/test_required_evidence.py)
- **Kind & Size**: `Python` | `66` lines
- **Purpose**: Tests for reason-code-aware Required Evidence Schema and active acquisition logic.
- **Key Functions**: `test_required_evidence_audit_complete_package`, `test_required_evidence_audit_missing_mandatory`, `test_required_evidence_audit_smt_conflict`

### [`backend/tests/test_research_evaluation.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/backend/tests/test_research_evaluation.py)
- **Kind & Size**: `Python` | `160` lines
- **Purpose**: Automated Quality Assurance for CARVE-FECL Research Evaluation Suite.
- **Key Functions**: `test_research_artifacts_exist_and_parse`, `test_data_cards_and_manifests_exist`, `test_model_card_and_limitations_exist`, `test_causal_robustness_evaluation`, `test_cost_analysis_and_pareto`, `test_ood_evaluation`, `test_subgroup_analysis`, `test_ablation_benchmarks`

### [`backend/tests/test_sandbox_api.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/backend/tests/test_sandbox_api.py)
- **Kind & Size**: `Python` | `187` lines
- **Key Functions**: `_client`, `_payload`, `test_custom_input_produces_grounded_block_without_side_effects`, `test_matching_processed_refund_changes_same_claim_to_pass`, `test_wrong_processed_refund_amount_blocks_deterministically`, `test_incomplete_ledger_abstains_to_review_even_with_conflicting_claim`, `test_sandbox_rejects_float_money_and_unknown_fields`, `test_sandbox_fails_closed_for_hinglish_and_out_of_scope_text`

### [`backend/tests/test_security.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/backend/tests/test_security.py)
- **Kind & Size**: `Python` | `61` lines
- **Key Functions**: `test_exact_raw_body_with_valid_signature_passes`, `test_missing_or_malformed_signature_is_rejected`, `test_body_mutation_after_signing_is_rejected`, `test_whitespace_is_valid_when_it_is_part_of_exact_signed_bytes`, `test_verifier_uses_constant_time_comparison`

### [`backend/tests/test_seed_demo.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/backend/tests/test_seed_demo.py)
- **Kind & Size**: `Python` | `92` lines
- **Key Functions**: `test_seeded_demo_runs_signed_webhook_to_pass_review_block_workspace`, `test_seeded_block_case_supports_complete_local_override_path`, `test_seed_refuses_to_overwrite_an_existing_database`

### [`backend/tests/test_semantic_pipeline.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/backend/tests/test_semantic_pipeline.py)
- **Kind & Size**: `Python` | `175` lines
- **Classes**: `ScriptedExtractor` [methods: __init__, extract]
- **Key Functions**: `request`, `extraction_result`, `test_success_requires_valid_schema_grounding_and_normalization`, `test_transient_failure_retries_then_succeeds`, `test_timeout_exhaustion_routes_to_review`, `test_schema_failure_is_permanent_review_without_retry`, `test_ungrounded_or_ambiguous_quote_routes_to_review`, `test_unresolved_value_routes_to_review`

### [`backend/tests/test_verification.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/backend/tests/test_verification.py)
- **Kind & Size**: `Python` | `176` lines
- **Key Functions**: `claim`, `refund`, `context`, `codes`, `test_processed_claim_without_complete_ledger_match_blocks`, `test_matching_processed_refund_has_no_findings`, `test_incomplete_ledger_reviews_and_cannot_block`, `test_final_partial_refund_conflicts_with_grounded_full_amount`

### [`backend/tests/test_webhook_replay.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/backend/tests/test_webhook_replay.py)
- **Kind & Size**: `Python` | `113` lines
- **Key Functions**: `replay`, `test_replay_ack_is_durable_and_measured_under_five_seconds`, `test_mutated_replay_with_original_signature_is_rejected_before_persistence`, `test_persisted_job_is_recovered_after_simulated_process_restart`

## 9. Automation, CLI & Rehearsal Scripts (`scripts/`)

### [`scripts/__init__.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/scripts/__init__.py)
- **Kind & Size**: `Python` | `1` lines
- **Purpose**: Repository verification and reproducibility scripts.

### [`scripts/analyze_fecl_v2.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/scripts/analyze_fecl_v2.py)
- **Kind & Size**: `Python` | `202` lines
- **Purpose**: Generate non-tuning slice/error analysis from the frozen FECL v2 test artifact.
- **Key Functions**: `sha256`, `metric`, `score`, `main`

### [`scripts/analyze_fecl_v3.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/scripts/analyze_fecl_v3.py)
- **Kind & Size**: `Python` | `211` lines
- **Purpose**: Create a no-tuning, artifact-bound analysis of the frozen FECL v3 test run.
- **Key Functions**: `sha256`, `read_json`, `read_jsonl`, `metric`, `sliced`, `main`

### [`scripts/apply_empirical_research_results.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/scripts/apply_empirical_research_results.py)
- **Kind & Size**: `Python` | `97` lines
- **Purpose**: Sync empirical PyTorch training results into research JSON artifacts.
- **Key Functions**: `sync_empirical_results`

### [`scripts/audit_ai_holdout_grounding.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/scripts/audit_ai_holdout_grounding.py)
- **Kind & Size**: `Python` | `168` lines
- **Purpose**: Post-hoc audit of saved holdout predictions through grounding and the real gate.
- **Classes**: `SavedPredictionExtractor` [methods: __init__, extract]
- **Key Functions**: `read_json`, `sha256`, `runtime_input`, `audit`, `main`

### [`scripts/audit_research_integrity.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/scripts/audit_research_integrity.py)
- **Kind & Size**: `Python` | `154` lines
- **Purpose**: Reconcile versioned FECL artifacts without rewriting any frozen result.
- **Key Functions**: `sha256`, `load`, `line_count`, `model_record`, `audit_version`, `main`

### [`scripts/benchmark_cases.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/scripts/benchmark_cases.py)
- **Kind & Size**: `Python` | `33` lines
- **Purpose**: List benchmark runtime case paths with DEV-safe defaults.
- **Key Functions**: `build_parser`, `main`

### [`scripts/build_carve_paper.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/scripts/build_carve_paper.py)
- **Kind & Size**: `Python` | `830` lines
- **Purpose**: Build the artifact-generated CARVE v4.5 research paper as a verified PDF.
- **Key Functions**: `load`, `p`, `table`, `architecture`, `risk_curve`, `metric_rows`, `header_footer`, `build`

### [`scripts/build_carve_system_design_docx.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/scripts/build_carve_system_design_docx.py)
- **Kind & Size**: `Python` | `515` lines
- **Purpose**: Populate the retained System Design DOCX without replacing its visual system.
- **Key Functions**: `replace_paragraph`, `set_cell`, `fill_table`, `architecture_diagram`, `patch_package`, `main`

### [`scripts/build_fecl_paper_assets.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/scripts/build_fecl_paper_assets.py)
- **Kind & Size**: `Python` | `298` lines
- **Purpose**: Build every numeric paper table/macro/card from frozen FECL artifacts.
- **Key Functions**: `read`, `sha256`, `write`, `latex_escape`, `main_results`, `slice_results`, `calibration_results`, `error_examples`

### [`scripts/check.ps1`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/scripts/check.ps1)
- **Kind & Size**: `Other` | `72` lines

### [`scripts/check_no_razorpay_writes.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/scripts/check_no_razorpay_writes.py)
- **Kind & Size**: `Python` | `86` lines
- **Purpose**: Static release guard for the Track 02 no-provider-write boundary.
- **Key Functions**: `_python_imports`, `scan_runtime_tree` *(Return violations from runtime code and production...)*, `main`

### [`scripts/check_stale_claims.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/scripts/check_stale_claims.py)
- **Kind & Size**: `Python` | `103` lines
- **Purpose**: Dead-code and stale-research claims linter (Directive Section 60).
- **Key Functions**: `scan_for_stale_claims`, `main`

### [`scripts/demo.ps1`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/scripts/demo.ps1)
- **Kind & Size**: `Other` | `118` lines

### [`scripts/demo_smoke_test.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/scripts/demo_smoke_test.py)
- **Kind & Size**: `Python` | `143` lines
- **Purpose**: Automated 5-minute judge demo smoke test for PRAMAAN / CARVE-FECL.
- **Key Functions**: `run_demo_smoke_test`, `main`

### [`scripts/evaluate_benchmark.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/scripts/evaluate_benchmark.py)
- **Kind & Size**: `Python` | `48` lines
- **Purpose**: Run DEV safely or the explicitly confirmed final frozen HOLDOUT evaluation.
- **Key Functions**: `main`

### [`scripts/failure_demo.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/scripts/failure_demo.py)
- **Kind & Size**: `Python` | `102` lines
- **Purpose**: Demonstrate an intentional extractor outage and safe offline recovery.
- **Classes**: `InjectedUnavailableExtractor` [methods: extract]
- **Key Functions**: `_read_object`, `run_failure_demo`, `main`

### [`scripts/freeze_benchmark.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/scripts/freeze_benchmark.py)
- **Kind & Size**: `Python` | `22` lines
- **Purpose**: Freeze a generated benchmark version; this operation cannot overwrite a freeze.
- **Key Functions**: `main`

### [`scripts/freeze_release.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/scripts/freeze_release.py)
- **Kind & Size**: `Python` | `32` lines
- **Purpose**: Record the exact pre-holdout detector/evaluator/config byte freeze.
- **Key Functions**: `main`

### [`scripts/generate_benchmark.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/scripts/generate_benchmark.py)
- **Kind & Size**: `Python` | `21` lines
- **Purpose**: Generate the deterministic synthetic benchmark at an explicit new path.
- **Key Functions**: `main`

### [`scripts/generate_fecl_v3.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/scripts/generate_fecl_v3.py)
- **Kind & Size**: `Python` | `585` lines
- **Purpose**: Generate FECL-Bench v3 heterogeneous graphs and causal counterfactual pairs.
- **Classes**: `PairSpec`
- **Key Functions**: `dump`, `write_jsonl`, `sha256`, `status_phrase`, `add_node`, `add_edge`, `changed_claim`, `make_case`

### [`scripts/generate_fecl_v4.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/scripts/generate_fecl_v4.py)
- **Kind & Size**: `Python` | `789` lines
- **Purpose**: Generate FECL-Bench v4 without fitting or evaluating any model.
- **Classes**: `PairSpec`
- **Key Functions**: `digest_bytes`, `digest_text`, `file_digest`, `canonical`, `evidence`, `claim_sentence`, `changed_values`, `certificate_kind`

### [`scripts/generate_fecl_v4_1.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/scripts/generate_fecl_v4_1.py)
- **Kind & Size**: `Python` | `99` lines
- **Purpose**: Generate the FECL-Bench v4.1 MCC/acquisition erratum without mutating frozen v4.
- **Key Functions**: `required_evidence_v41`, `version`, `main`

### [`scripts/generate_fecl_v4_2.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/scripts/generate_fecl_v4_2.py)
- **Kind & Size**: `Python` | `228` lines
- **Purpose**: Generate the label-blind proof and causal-pair correction for FECL-Bench v4.5.
- **Key Functions**: `version`, `refresh_grounding`, `correct_case`, `validate_pairs`, `main`

### [`scripts/generate_offline_demo_cache.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/scripts/generate_offline_demo_cache.py)
- **Kind & Size**: `Python` | `77` lines
- **Purpose**: Generate the labeled v1 offline regex-fixture replay cache once.
- **Key Functions**: `replay_config_hash` *(Bind replay configuration to deterministic contrac...)*, `generate`, `main`

### [`scripts/load_saturation_benchmark.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/scripts/load_saturation_benchmark.py)
- **Kind & Size**: `Python` | `212` lines
- **Purpose**: Multi-worker load, burst, and saturation benchmark for PRAMAAN / CARVE-FECL.
- **Key Functions**: `_generate_payload`, `benchmark_concurrency`, `run_load_suite`, `main`

### [`scripts/package_validate.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/scripts/package_validate.py)
- **Kind & Size**: `Python` | `105` lines
- **Key Functions**: `fail`, `main`

### [`scripts/rehearse-demo.ps1`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/scripts/rehearse-demo.ps1)
- **Kind & Size**: `Other` | `36` lines

### [`scripts/replay_webhook.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/scripts/replay_webhook.py)
- **Kind & Size**: `Python` | `50` lines
- **Purpose**: Replay one exact Razorpay-compatible fixture with an environment-provided secret.
- **Key Functions**: `build_parser`, `main`

### [`scripts/run_ai_research_study.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/scripts/run_ai_research_study.py)
- **Kind & Size**: `Python` | `1074` lines
- **Purpose**: Run the pre-registered semantic model study without changing runtime authority.
- **Key Functions**: `read_json`, `sha256_path`, `sentence_examples`, `build_tfidf`, `binary_metrics`, `grouped_oof_probabilities`, `_take`, `crossfit_platt`

### [`scripts/run_carve_v4.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/scripts/run_carve_v4.py)
- **Kind & Size**: `Python` | `857` lines
- **Purpose**: Fit, freeze, and one-shot evaluate CARVE on FECL-Bench v4.5.
- **Key Functions**: `sha256`, `rows`, `dump`, `claim_text`, `labels`, `inventory`, `relational_features`, `feature_matrix`

### [`scripts/run_fecl_v2.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/scripts/run_fecl_v2.py)
- **Kind & Size**: `Python` | `1185` lines
- **Purpose**: Run the pre-registered Financial Evidence Consistency Learning v2 study.
- **Key Functions**: `utc_now`, `sha256`, `json_dump`, `render`, `generate_split`, `ood_rows`, `ensure_dataset`, `pair_text`

### [`scripts/run_fecl_v3.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/scripts/run_fecl_v3.py)
- **Kind & Size**: `Python` | `1430` lines
- **Purpose**: Train, freeze, and evaluate FECL-Bench v3 without giving models gate authority.
- **Classes**: `GraphSample`, `GraphBatch`, `MessageLayer` [methods: __init__, forward], `EvidenceGraphModel` [methods: __init__, forward]
- **Key Functions**: `sha256`, `read_json`, `read_jsonl`, `dump`, `tfidf_pipeline`, `select_threshold` *(Select the DEV F1 threshold, breaking ties by fals...)*, `binary_f1`, `paired_group_bootstrap` *(Bootstrap counterfactual pairs, never individual c...)*

### [`scripts/seed_demo.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/scripts/seed_demo.py)
- **Kind & Size**: `Python` | `344` lines
- **Purpose**: Replay signed synthetic webhooks and materialize the offline analyst demo.
- **Classes**: `SeededCase`, `DemoSeedSummary`
- **Key Functions**: `_read_json`, `_remove_existing_demo_database`, `_finding_refs`, `_persist_case_result`, `_evaluate_fixture`, `seed_demo` *(Create three synthetic cases through the authentic...)*, `main`

### [`scripts/setup.ps1`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/scripts/setup.ps1)
- **Kind & Size**: `Other` | `50` lines

### [`scripts/spec_lint.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/scripts/spec_lint.py)
- **Kind & Size**: `Python` | `117` lines
- **Key Functions**: `files_to_scan`, `main`

### [`scripts/stop-demo.ps1`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/scripts/stop-demo.ps1)
- **Kind & Size**: `Other` | `31` lines

### [`scripts/train_local_semantic_model.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/scripts/train_local_semantic_model.py)
- **Kind & Size**: `Python` | `195` lines
- **Purpose**: Train and evaluate the local semantic candidate on DEV only.
- **Key Functions**: `_json`, `_assert_dev_only`, `load_dev_examples`, `_regex_predictions`, `_metrics`, `train`, `main`

### [`scripts/verify_live_demo.py`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/scripts/verify_live_demo.py)
- **Kind & Size**: `Python` | `126` lines
- **Purpose**: Verify the running seeded demo over proxy-free loopback HTTP.
- **Key Functions**: `_text`, `_object`, `verify_live_demo`, `main`

## 10. Contracts & Schemas (`contracts/`)

### [`contracts/evaluation-result.schema.json`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/contracts/evaluation-result.schema.json)
- **Kind & Size**: `Contract` | `107` lines
- **Purpose**: Dispute Integrity Gate evaluation result artifact

### [`contracts/gate-decision.schema.json`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/contracts/gate-decision.schema.json)
- **Kind & Size**: `Contract` | `30` lines
- **Purpose**: GateDecision

### [`contracts/grounded-claim.schema.json`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/contracts/grounded-claim.schema.json)
- **Kind & Size**: `Contract` | `33` lines
- **Purpose**: GroundedClaim

### [`contracts/refund_not_processed_v1.yaml`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/contracts/refund_not_processed_v1.yaml)
- **Kind & Size**: `Contract` | `35` lines
- **Purpose**: profile_id: refund_not_processed_v1

## 11. Architecture Decision Records (`adr/`)

### [`adr/ADR-001-ONE-BOUNDED-AI-STAGE.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/adr/ADR-001-ONE-BOUNDED-AI-STAGE.md)
- **Kind & Size**: `Doc` | `17` lines
- **Purpose**: ADR-001 — One Bounded AI Stage by Default — **Status:** Accepted for MVP

### [`adr/ADR-002-NO-RAZORPAY-WRITES-IN-MVP.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/adr/ADR-002-NO-RAZORPAY-WRITES-IN-MVP.md)
- **Kind & Size**: `Doc` | `15` lines
- **Purpose**: ADR-002 — No Razorpay Write Actions in the MVP — **Status:** Accepted

### [`adr/ADR-003-DURABLE-SQLITE-JOBS.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/adr/ADR-003-DURABLE-SQLITE-JOBS.md)
- **Kind & Size**: `Doc` | `16` lines
- **Purpose**: ADR-003 — Durable SQLite Job State Instead of In-Memory-Only Background Work — **Status:** Accepted

### [`adr/ADR-004-TEXT-JSON-EVIDENCE-V1.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/adr/ADR-004-TEXT-JSON-EVIDENCE-V1.md)
- **Kind & Size**: `Doc` | `16` lines
- **Purpose**: ADR-004 — Canonical Text/JSON Evidence in v1 — **Status:** Accepted

### [`adr/ADR-005-FAMILY-SEPARATED-HOLDOUT.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/adr/ADR-005-FAMILY-SEPARATED-HOLDOUT.md)
- **Kind & Size**: `Doc` | `16` lines
- **Purpose**: ADR-005 — Scenario-Family-Separated Frozen Holdout — **Status:** Accepted

## 12. Root Configuration & Project Governance

### [`.env.example`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/.env.example)
- **Kind & Size**: `Other` | `7` lines

### [`.gitignore`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/.gitignore)
- **Kind & Size**: `Other` | `32` lines


### [`ACTUAL_TRAINING_AUDIT.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/ACTUAL_TRAINING_AUDIT.md)
- **Kind & Size**: `Doc` | `60` lines
- **Purpose**: SCIENTIFIC RESEARCH INTEGRITY AUDIT: ACTUAL TRAINING PROVENANCE — **Standard:** Directive Sections 1–12 (Falsification & Real Execution)

### [`AGENTS.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/AGENTS.md)
- **Kind & Size**: `Doc` | `112` lines
- **Purpose**: AGENTS.md — Engineering Constitution — This file governs every coding-agent action in this repository.

### [`BASELINE_LADDER_V3.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/BASELINE_LADDER_V3.md)
- **Kind & Size**: `Doc` | `44` lines
- **Purpose**: BASELINE LADDER V3: POST-AUDIT EMPIRICAL BENCHMARK & MATCHED-COVERAGE EVALUATION — **Standard**: ICML/NeurIPS Evaluation Standards (Section 8)

### [`CHAOS_TEST_PLAN.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/CHAOS_TEST_PLAN.md)
- **Kind & Size**: `Doc` | `61` lines
- **Purpose**: PRAMAAN / CARVE-FECL — CHAOS & FAULT INJECTION TEST PLAN — > **Test Suite**: `backend/tests/chaos/test_chaos_fault_injection.py`

### [`CLAIMS_LEDGER.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/CLAIMS_LEDGER.md)
- **Kind & Size**: `Doc` | `37` lines
- **Purpose**: SCIENTIFIC CLAIMS LEDGER & GOVERNANCE RECORD — **System**: CARVE-FECL Quant-Risk AI

### [`CLAIM_LEDGER.csv`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/CLAIM_LEDGER.csv)
- **Kind & Size**: `Other` | `17` lines

### [`CODEBASE_FORENSIC_AUDIT.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/CODEBASE_FORENSIC_AUDIT.md)
- **Kind & Size**: `Doc` | `183` lines
- **Purpose**: FORENSIC CODEBASE AUDIT: CARVE-FECL / DISPUTE INTEGRITY GATE — **Auditor Role**: Principal AI/ML Research Scientist & Quantitative Fintech Systems Engineer

### [`COMPETITIVE_ASYMMETRY.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/COMPETITIVE_ASYMMETRY.md)
- **Kind & Size**: `Doc` | `77` lines
- **Purpose**: COMPETITIVE ASYMMETRY & DEFENSIVE MOAT AUDIT — **System**: CARVE-FECL Quant-Risk AI

### [`CONCURRENCY_AND_IDEMPOTENCY_AUDIT.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/CONCURRENCY_AND_IDEMPOTENCY_AUDIT.md)
- **Kind & Size**: `Doc` | `100` lines
- **Purpose**: CONCURRENCY, IDEMPOTENCY & TRANSACTION AUDIT — **Auditor Role**: Senior Distributed Systems & Database Reliability Engineer

### [`DECISION_LEDGER.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/DECISION_LEDGER.md)
- **Kind & Size**: `Doc` | `94` lines
- **Purpose**: RESEARCH & ARCHITECTURE DECISION LEDGER — **System**: CARVE-FECL Quant-Risk AI

### [`DEMO-SCRIPT.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/DEMO-SCRIPT.md)
- **Kind & Size**: `Doc` | `46` lines
- **Purpose**: Demo and video script — These are timed allocations, not a claim that a video has been recorded or submitted. Every performance number below com

### [`E2E_TEST_MATRIX.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/E2E_TEST_MATRIX.md)
- **Kind & Size**: `Doc` | `70` lines
- **Purpose**: PRAMAAN / CARVE-FECL — END-TO-END (E2E) TEST MATRIX — > **Verification Goal**: Validate the complete end-to-end flow from inbound webhook ingestion through semantic extractio

### [`FAILURE-NARRATIVE-TEMPLATE.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/FAILURE-NARRATIVE-TEMPLATE.md)
- **Kind & Size**: `Doc` | `31` lines
- **Purpose**: Failure Narrative — Fill Only From Real Build Evidence — > Do not invent a bug for the Buildathon form. Use an issue that actually occurred, or clearly label a deliberate fault-

### [`FAILURE-NARRATIVE.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/FAILURE-NARRATIVE.md)
- **Kind & Size**: `Doc` | `85` lines
- **Purpose**: Failure narrative — These are observed build failures and one explicitly labeled fault injection. No incident rate, user impact, savings, or

### [`FINAL_EMPIRICAL_MANIFEST.json`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/FINAL_EMPIRICAL_MANIFEST.json)
- **Kind & Size**: `Other` | `104` lines

### [`FINAL_RAZORPAY_JUDGE_BRIEF.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/FINAL_RAZORPAY_JUDGE_BRIEF.md)
- **Kind & Size**: `Doc` | `96` lines
- **Purpose**: FINAL RAZORPAY JUDGE BRIEF & 5-MINUTE ADJUDICATION PROTOCOL — **System**: CARVE-FECL Quant-Risk AI (Dispute Integrity Gate)

### [`FINAL_RESEARCH_CONTRIBUTIONS.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/FINAL_RESEARCH_CONTRIBUTIONS.md)
- **Kind & Size**: `Doc` | `44` lines
- **Purpose**: FINAL RESEARCH CONTRIBUTIONS: THE HARDENED CORE — **Standard**: Frontier Scientific Integrity (Section 47)

### [`FINAL_RESULTS.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/FINAL_RESULTS.md)
- **Kind & Size**: `Doc` | `74` lines
- **Purpose**: FINAL CANONICAL EMPIRICAL RESULTS — **Standard**: Master Governance Directive (Sections 9 & 11)

### [`FINTECH_RELIABILITY_AUDIT.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/FINTECH_RELIABILITY_AUDIT.md)
- **Kind & Size**: `Doc` | `100` lines
- **Purpose**: FINTECH RELIABILITY AUDIT: STATE INTEGRITY & FAIL-CLOSED GUARDS — **Auditor Role**: Senior Fintech Systems Architect & Risk Infrastructure Engineer

### [`HACKATHON_CONTRACT.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/HACKATHON_CONTRACT.md)
- **Kind & Size**: `Doc` | `80` lines
- **Purpose**: HACKATHON CONTRACT: RAZORPAY AI BUILDATHON 2026 — **Standard**: Master Governance Directive (Section 3)

### [`HFT_STYLE_CORRECTNESS_AUDIT.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/HFT_STYLE_CORRECTNESS_AUDIT.md)
- **Kind & Size**: `Doc` | `85` lines
- **Purpose**: HFT-STYLE CORRECTNESS AUDIT: DETERMINISM, TIMING & LATENCY BOUNDS — **Auditor Role**: Quantitative Systems & Electronic Trading Infrastructure Engineer

### [`HUMAN_VALIDATION_STATUS.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/HUMAN_VALIDATION_STATUS.md)
- **Kind & Size**: `Doc` | `84` lines
- **Purpose**: HUMAN VALIDATION & EXTERNAL VALIDITY GOVERNANCE REPORT — **Standard**: Frontier Research Scientific Rigor (Sections 6 & 7)

### [`IDE-HANDOFF.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/IDE-HANDOFF.md)
- **Kind & Size**: `Doc` | `38` lines
- **Purpose**: IDE / Coding-Agent Handoff — Copy this entire specification repository into the root of the implementation workspace (or into `/spec` while keeping `

### [`IMPLEMENTATION-PLAN.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/IMPLEMENTATION-PLAN.md)
- **Kind & Size**: `Doc` | `106` lines
- **Purpose**: Implementation Plan — Build evidence in this order: **domain truth → deterministic verifier → grounded extraction → end-to-end case → evaluati

### [`LOSS_SENSITIVITY.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/LOSS_SENSITIVITY.md)
- **Kind & Size**: `Doc` | `65` lines
- **Purpose**: DECISION-THEORETIC LOSS SENSITIVITY & ASYMMETRIC RISK MAPPING — **Standard**: Bayesian Decision Theory & Financial Risk Management (Section 14)

### [`MASTER-BUILD-PROMPT.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/MASTER-BUILD-PROMPT.md)
- **Kind & Size**: `Doc` | `44` lines
- **Purpose**: Master Build Prompt — You are the implementation agent for **Dispute Integrity Gate**, a Razorpay AI Buildathon 2026 Track 02 submission.

### [`ML_RESEARCH_AUDIT.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/ML_RESEARCH_AUDIT.md)
- **Kind & Size**: `Doc` | `125` lines
- **Purpose**: AI/ML RESEARCH AUDIT: CARVE-FECL SCIENTIFIC METHODOLOGY — **Auditor Role**: Principal AI/ML Research Scientist

### [`ML_TEST_PROTOCOL.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/ML_TEST_PROTOCOL.md)
- **Kind & Size**: `Doc` | `64` lines
- **Purpose**: PRAMAAN / CARVE-FECL — AI/ML RESEARCH INTEGRITY TEST PROTOCOL — > **Audience**: AI/ML Research Scientists, Quantitative Researchers, and Reviewers.

### [`NEGATIVE_RESULTS.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/NEGATIVE_RESULTS.md)
- **Kind & Size**: `Doc` | `70` lines
- **Purpose**: NEGATIVE RESULTS, FALSIFICATIONS & RESEARCH BOUNDARIES — **Standard**: Master Governance Directive (Section 59)

### [`NUMERICAL_CORRECTNESS_AUDIT.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/NUMERICAL_CORRECTNESS_AUDIT.md)
- **Kind & Size**: `Doc` | `84` lines
- **Purpose**: NUMERICAL CORRECTNESS & MONEY REPRESENTATION AUDIT — **Auditor Role**: Quantitative Systems Engineer & Financial Software Auditor

### [`P0_P1_EXECUTION_PLAN.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/P0_P1_EXECUTION_PLAN.md)
- **Kind & Size**: `Doc` | `77` lines
- **Purpose**: P0 / P1 REMEDIATION & EXECUTION ROADMAP — **Auditor Role**: Principal AI/ML Research Scientist & Quantitative Fintech Systems Lead

### [`P0_P1_RESEARCH_REPAIR_PLAN.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/P0_P1_RESEARCH_REPAIR_PLAN.md)
- **Kind & Size**: `Doc` | `61` lines
- **Purpose**: P0/P1/P2/P3 RESEARCH REPAIR & ACTION PLAN — **Framework**: Methodological Hardening & Research Integrity Action Plan

### [`PACKAGE-MANIFEST.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/PACKAGE-MANIFEST.md)
- **Kind & Size**: `Doc` | `45` lines
- **Purpose**: Package Manifest — This repository contains the specification, working local application, frozen synthetic research

### [`PERFORMANCE_TEST_PLAN.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/PERFORMANCE_TEST_PLAN.md)
- **Kind & Size**: `Doc` | `53` lines
- **Purpose**: PRAMAAN / CARVE-FECL — PERFORMANCE & LOAD SATURATION TEST PLAN — > **Script**: `scripts/load_saturation_benchmark.py`

### [`POST_AUDIT_RESULTS.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/POST_AUDIT_RESULTS.md)
- **Kind & Size**: `Doc` | `64` lines
- **Purpose**: POST-AUDIT EMPIRICAL RESEARCH RESULTS & SCIENTIFIC BENCHMARKS — **Standard**: Comprehensive 5-Seed Empirical PyTorch Benchmark (Section 4)

### [`QUALITY-GATES.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/QUALITY-GATES.md)
- **Kind & Size**: `Doc` | `71` lines
- **Purpose**: Quality Gates — A release candidate is valid only if every mandatory gate below is green.

### [`README.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/README.md)
- **Kind & Size**: `Doc` | `252` lines
- **Purpose**: PRAMAAN: AI Risk Manager & Dispute Integrity Gate — Razorpay AI Buildathon 2026 · Track 02 · Powered by CARVE-FECL Engine

### [`REAL_TRAINING_RECEIPT.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/REAL_TRAINING_RECEIPT.md)
- **Kind & Size**: `Doc` | `143` lines
- **Purpose**: CARVE-FECL: REAL PYTORCH TRAINING RECEIPT & REPRODUCIBILITY AUDIT — **Date of Execution**: 2026-09-03

### [`RELEASE_TEST_RECEIPT.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/RELEASE_TEST_RECEIPT.md)
- **Kind & Size**: `Doc` | `61` lines
- **Purpose**: PRAMAAN / CARVE-FECL — RELEASE TEST AUDIT RECEIPT — > **Generated At**: 2026-09-04T13:22:00Z

### [`RESEARCH_NEGATIVE_RESULTS.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/RESEARCH_NEGATIVE_RESULTS.md)
- **Kind & Size**: `Doc` | `121` lines
- **Purpose**: SCIENTIFIC NEGATIVE RESULTS & RESEARCH POST-MORTEM: WHAT FAILED AND WHAT WAS LEARNED — **Standard**: Frontier Research Integrity (Honest Reporting of Falsifications & Negative Results)

### [`RESEARCH_SIGNAL_SCORECARD.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/RESEARCH_SIGNAL_SCORECARD.md)
- **Kind & Size**: `Doc` | `48` lines
- **Purpose**: RESEARCH-ENGINEERING HIRING SIGNAL SCORECARD — **Auditor Role**: Principal AI/ML Research Scientist & Senior Director of Engineering (Fintech / Risk)

### [`ROBUSTNESS_POST_AUDIT.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/ROBUSTNESS_POST_AUDIT.md)
- **Kind & Size**: `Doc` | `47` lines
- **Purpose**: ADVERSARIAL ROBUSTNESS & COUNTERFACTUAL MINIMAL-PAIR AUDIT — **Standard**: Robust Machine Learning & Causal Counterfactual Testing (Sections 19 & 20)

### [`RUBRIC_TRACEABILITY.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/RUBRIC_TRACEABILITY.md)
- **Kind & Size**: `Doc` | `34` lines
- **Purpose**: RUBRIC TRACEABILITY MATRIX: CARVE-FECL — **Standard**: Master Governance Directive (Section 3)

### [`RUNBOOK.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/RUNBOOK.md)
- **Kind & Size**: `Doc` | `30` lines
- **Purpose**: Local runbook — The demo runtime is fully local and uses a versioned, precomputed regex fixture cache. It makes no model-provider or Raz

### [`SECURITY_TEST_PLAN.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/SECURITY_TEST_PLAN.md)
- **Kind & Size**: `Doc` | `55` lines
- **Purpose**: PRAMAAN / CARVE-FECL — SECURITY & ADVERSARIAL THREAT TEST PLAN — > **Test Suites**: `backend/tests/security/test_security_adversarial.py`, `scripts/check_no_razorpay_writes.py`

### [`SECURITY_THREAT_MODEL.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/SECURITY_THREAT_MODEL.md)
- **Kind & Size**: `Doc` | `87` lines
- **Purpose**: SECURITY THREAT MODEL & VULNERABILITY AUDIT — **Auditor Role**: Principal Fintech Security Engineer

### [`SHA256SUMS.txt`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/SHA256SUMS.txt)
- **Kind & Size**: `Other` | `48` lines

### [`SIMULATOR_VERIFIER_CIRCULARITY.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/SIMULATOR_VERIFIER_CIRCULARITY.md)
- **Kind & Size**: `Doc` | `82` lines
- **Purpose**: SIMULATOR–VERIFIER CIRCULARITY AUDIT & FALSIFICATION — **Standard**: Hostile Formal Verification & Applied ML Audit (Section 5)

### [`SPEC-LINT-RULES.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/SPEC-LINT-RULES.md)
- **Kind & Size**: `Doc` | `14` lines
- **Purpose**: Specification Lint Rules — Run `python scripts/spec_lint.py` before coding-agent handoff and after any spec change.

### [`TASKS.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/TASKS.md)
- **Kind & Size**: `Doc` | `69` lines
- **Purpose**: TASKS — Initial Build Queue — Status: `[ ]` pending, `[~]` in progress, `[x]` evidence-complete, `[!]` blocked.

### [`TEST_GENERATOR_CATALOG.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/TEST_GENERATOR_CATALOG.md)
- **Kind & Size**: `Doc` | `85` lines
- **Purpose**: PRAMAAN / CARVE-FECL — TEST GENERATOR CATALOG — > **Module**: `backend/tests/generators/strategies.py`

### [`TEST_INVARIANT_REGISTRY.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/TEST_INVARIANT_REGISTRY.md)
- **Kind & Size**: `Doc` | `35` lines
- **Purpose**: PRAMAAN / CARVE-FECL — TEST INVARIANT REGISTRY — > **Verification Standard**: Every invariant that matters financially is expressed as executable, automated code.

### [`TEST_STRATEGY.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/TEST_STRATEGY.md)
- **Kind & Size**: `Doc` | `94` lines
- **Purpose**: PRAMAAN / CARVE-FECL — TEST STRATEGY & VERIFICATION MASTER DIRECTIVE — > **Product Name**: PRAMAAN ("Proof before you contest.")

### [`TRACK02_PROBLEM_SOLUTION_AUDIT.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/TRACK02_PROBLEM_SOLUTION_AUDIT.md)
- **Kind & Size**: `Doc` | `95` lines
- **Purpose**: TRACK 02 AUDIT: RAZORPAY AI BUILDATHON ALIGNMENT — **Auditor Role**: Principal AI/ML Research Scientist & Payment Risk Specialist

### [`claim_audit.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/claim_audit.md)
- **Kind & Size**: `Doc` | `42` lines
- **Purpose**: PRAMAAN / CARVE-FECL claim audit — **Status:** current implementation boundary

### [`design-qa.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/design-qa.md)
- **Kind & Size**: `Doc` | `60` lines
- **Purpose**: Design QA — guided CARVE evidence walkthrough — **Source visual truth**

### [`pyproject.toml`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/pyproject.toml)
- **Kind & Size**: `Other` | `66` lines

### [`uv.lock`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/uv.lock)
- **Kind & Size**: `Other` | `3448` lines

## 13. System Specifications & Truth Documents (`docs/`)

### [`docs/00-SOURCE-OF-TRUTH.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/docs/00-SOURCE-OF-TRUTH.md)
- **Kind & Size**: `Doc` | `252` lines
- **Purpose**: 00 — Source of Truth — **Status:** Canonical. Any conflicting project document must be changed to match this file unless a newer primary source

### [`docs/01-COMPETITION-TRUTH.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/docs/01-COMPETITION-TRUTH.md)
- **Kind & Size**: `Doc` | `100` lines
- **Purpose**: 01 — Razorpay AI Buildathon Competition Truth — The current Razorpay Buildathon landing page describes a **student-only program to hire AI Builder Interns**, with a pub

### [`docs/02-PROBLEM-VALIDATION.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/docs/02-PROBLEM-VALIDATION.md)
- **Kind & Size**: `Doc` | `96` lines
- **Purpose**: 02 — Problem Validation & Service Boundary — Razorpay disputes have:

### [`docs/03-COMPETITIVE-ANALYSIS.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/docs/03-COMPETITIVE-ANALYSIS.md)
- **Kind & Size**: `Doc` | `83` lines
- **Purpose**: 03 — Competitive Analysis & Differentiation — This document compares **publicly documented capabilities**, not private product internals. “Not documented” does not me

### [`docs/04-DOMAIN-MODEL.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/docs/04-DOMAIN-MODEL.md)
- **Kind & Size**: `Doc` | `149` lines
- **Purpose**: 04 — Domain Model — Documented dispute entity fields include:

### [`docs/05-PRD.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/docs/05-PRD.md)
- **Kind & Size**: `Doc` | `232` lines
- **Purpose**: 05 — Product Requirements Document (PRD) — **Dispute Integrity Gate** — Razorpay AI Buildathon Track 02.

### [`docs/06-SRS.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/docs/06-SRS.md)
- **Kind & Size**: `Doc` | `214` lines
- **Purpose**: 06 — Software Requirements Specification (SRS) — Dispute Integrity Gate is a local/sandbox merchant-side service. It receives Razorpay-compatible dispute events and synt

### [`docs/07-UI-UX-SPEC.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/docs/07-UI-UX-SPEC.md)
- **Kind & Size**: `Doc` | `244` lines
- **Purpose**: 07 — UI/UX & Human-Factors Specification — Help an analyst **verify**, not admire, the system's recommendation.

### [`docs/08-DESIGN-SYSTEM.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/docs/08-DESIGN-SYSTEM.md)
- **Kind & Size**: `Doc` | `94` lines
- **Purpose**: 08 — Design System — A compact, serious financial-operations interface. Avoid “AI dashboard” visual tropes: gradients, glowing orbs, trust sc

### [`docs/09-AI-ML-SPEC.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/docs/09-AI-ML-SPEC.md)
- **Kind & Size**: `Doc` | `241` lines
- **Purpose**: 09 — AI/ML Specification — The default system uses AI for **one task only**:

### [`docs/10-DATA-BENCHMARK-SPEC.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/docs/10-DATA-BENCHMARK-SPEC.md)
- **Kind & Size**: `Doc` | `152` lines
- **Purpose**: 10 — Data, Ontology & Synthetic Benchmark Specification — Provide a reproducible, non-leaky benchmark sufficient to satisfy Track 02's held-out precision/recall requirement while

### [`docs/11-EVALUATION-TEVV.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/docs/11-EVALUATION-TEVV.md)
- **Kind & Size**: `Doc` | `142` lines
- **Purpose**: 11 — Evaluation & TEVV Specification — Does grounded semantic extraction plus deterministic cross-source verification detect material refund-evidence conflicts

### [`docs/12-DECISION-POLICY.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/docs/12-DECISION-POLICY.md)
- **Kind & Size**: `Doc` | `118` lines
- **Purpose**: 12 — Decision Policy & Deterministic Invariants — The model extracts language. Code decides whether evidence is sufficiently grounded and whether structured facts conflic

### [`docs/13-ARCHITECTURE.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/docs/13-ARCHITECTURE.md)
- **Kind & Size**: `Doc` | `156` lines
- **Purpose**: 13 — Architecture Specification — Maximize correctness, inspectability, restart safety, and local reproducibility with minimal infrastructure.

### [`docs/14-API-CONTRACTS.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/docs/14-API-CONTRACTS.md)
- **Kind & Size**: `Doc` | `244` lines
- **Purpose**: 14 — API Contracts — All examples are **local application APIs**, except the inbound Razorpay-compatible webhook shape.

### [`docs/15-DATABASE-SCHEMA.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/docs/15-DATABASE-SCHEMA.md)
- **Kind & Size**: `Doc` | `184` lines
- **Purpose**: 15 — Database Schema — SQLite logical schema. Exact migration syntax may be implemented with SQLAlchemy or sqlite3; keep field semantics.

### [`docs/16-SECURITY-THREAT-MODEL.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/docs/16-SECURITY-THREAT-MODEL.md)
- **Kind & Size**: `Doc` | `145` lines
- **Purpose**: 16 — Security, Privacy & Threat Model — The hackathon system processes synthetic evidence, but its design should demonstrate correct trust boundaries without cl

### [`docs/17-RELIABILITY-TESTING.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/docs/17-RELIABILITY-TESTING.md)
- **Kind & Size**: `Doc` | `148` lines
- **Purpose**: 17 — Reliability & Testing Strategy — **Degraded uncertainty must never silently become PASS.**

### [`docs/18-OBSERVABILITY-FAILURE-RECOVERY.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/docs/18-OBSERVABILITY-FAILURE-RECOVERY.md)
- **Kind & Size**: `Doc` | `122` lines
- **Purpose**: 18 — Observability & Failure Recovery — Make failures diagnosable and safe without pretending the demo has enterprise observability.

### [`docs/19-DEMO-PITCH-README.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/docs/19-DEMO-PITCH-README.md)
- **Kind & Size**: `Doc` | `145` lines
- **Purpose**: 19 — Demo, Pitch & Submission Strategy — > **Evidence assembly is not evidence integrity. Dispute Integrity Gate verifies refund-dispute packets before a human c

### [`docs/20-TRACEABILITY-MATRIX.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/docs/20-TRACEABILITY-MATRIX.md)
- **Kind & Size**: `Doc` | `55` lines
- **Purpose**: 20 — Requirement Traceability Matrix — | Requirement | Failure eliminated | Evidence/source | Component | Test | Demo proof |

### [`docs/21-RISK-ASSUMPTIONS-DECISIONS.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/docs/21-RISK-ASSUMPTIONS-DECISIONS.md)
- **Kind & Size**: `Doc` | `112` lines
- **Purpose**: 21 — Risk, Assumption & Decision Ledger — Assumption: a merchant can export/support access to refund ledger and customer communication.

### [`docs/22-IMPLEMENTATION-BACKLOG.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/docs/22-IMPLEMENTATION-BACKLOG.md)
- **Kind & Size**: `Doc` | `97` lines
- **Purpose**: 22 — Implementation Backlog by Dependency — - E1.1 Pydantic/domain models

### [`docs/23-DEFINITION-OF-DONE.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/docs/23-DEFINITION-OF-DONE.md)
- **Kind & Size**: `Doc` | `76` lines
- **Purpose**: 23 — Definition of Done & Release Checklist — A feature is done only when:

### [`docs/24-SOURCE-LEDGER.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/docs/24-SOURCE-LEDGER.md)
- **Kind & Size**: `Doc` | `449` lines
- **Purpose**: 24 — Source & Evidence Ledger — Verified on **2026-08-23** unless stated otherwise.

### [`docs/25-RESEARCH-CORRECTIONS.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/docs/25-RESEARCH-CORRECTIONS.md)
- **Kind & Size**: `Doc` | `164` lines
- **Purpose**: 25 — Research Corrections & Reconciliation Log — This file records material corrections made while consolidating the supplied reports.

### [`docs/26-JUDGE-DEFENSE.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/docs/26-JUDGE-DEFENSE.md)
- **Kind & Size**: `Doc` | `60` lines
- **Purpose**: 26 — Judge Defense / Panel Q&A — Use these as factual answer structures, not memorized marketing claims. Replace placeholders with measured values only a

### [`docs/27-FINAL-RESEARCH-AUDIT.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/docs/27-FINAL-RESEARCH-AUDIT.md)
- **Kind & Size**: `Doc` | `74` lines
- **Purpose**: 27 — Final Research Audit — **GO — Track 02 / Dispute Integrity Gate**, with the corrected MVP defined in `00-SOURCE-OF-TRUTH.md`.

### [`docs/28-AI-RESEARCH-PROTOCOL.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/docs/28-AI-RESEARCH-PROTOCOL.md)
- **Kind & Size**: `Doc` | `165` lines
- **Purpose**: 28 — AI Research Protocol — Status: expanded and re-registered before any v2 frozen-holdout run

### [`docs/28-DESIGN-SYSTEM.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/docs/28-DESIGN-SYSTEM.md)
- **Kind & Size**: `Doc` | `42` lines
- **Purpose**: 28 — Interface design system — CARVE uses a restrained financial-ledger visual language: warm paper, high-contrast ink, one dark

### [`docs/29-FECL-V2-PROTOCOL.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/docs/29-FECL-V2-PROTOCOL.md)
- **Kind & Size**: `Doc` | `130` lines
- **Purpose**: 29 — Financial Evidence Consistency Learning v2 protocol — Status: pre-registered before the first v2 test run

### [`docs/29-PRODUCTION-READINESS-AUDIT.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/docs/29-PRODUCTION-READINESS-AUDIT.md)
- **Kind & Size**: `Doc` | `84` lines
- **Purpose**: 29 — Production-readiness audit — Date: 2026-09-02

### [`docs/30-FECL-V3-PRIOR-ART-AND-WHITESPACE.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/docs/30-FECL-V3-PRIOR-ART-AND-WHITESPACE.md)
- **Kind & Size**: `Doc` | `81` lines
- **Purpose**: 30 — FECL v3 prior-art falsification and technical whitespace — Status: research scoping record, not a novelty or freedom-to-operate opinion

### [`docs/31-FECL-BENCH-V3-PROTOCOL.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/docs/31-FECL-BENCH-V3-PROTOCOL.md)
- **Kind & Size**: `Doc` | `133` lines
- **Purpose**: 31 — FECL-Bench v3 preregistered protocol — Status: frozen before generation of the final TEST result

### [`docs/32-RESEARCH-INTEGRITY-RECONCILIATION.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/docs/32-RESEARCH-INTEGRITY-RECONCILIATION.md)
- **Kind & Size**: `Doc` | `81` lines
- **Purpose**: 32 — Research integrity reconciliation — Status: generated evidence audited on 2026-09-01

### [`docs/CARVE-METHOD.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/docs/CARVE-METHOD.md)
- **Kind & Size**: `Doc` | `140` lines
- **Purpose**: CARVE — Cost-aware Active Risk-controlled Verification with Evidence acquisition — Status: preregistered research method; synthetic evaluation only

### [`docs/FECL-V4-PROTOCOL.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/docs/FECL-V4-PROTOCOL.md)
- **Kind & Size**: `Doc` | `153` lines
- **Purpose**: FECL-Bench v4 — Certified Sequential Evidence Verification protocol — Status: preregistered before benchmark generation and all v4 model fitting

### [`docs/FECL-V4.1-ERRATUM.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/docs/FECL-V4.1-ERRATUM.md)
- **Kind & Size**: `Doc` | `27` lines
- **Purpose**: FECL-Bench v4.1 erratum — Status: preregistered correction before any v4 model fitting or TEST evaluation

### [`docs/FECL-V4.2-ERRATUM.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/docs/FECL-V4.2-ERRATUM.md)
- **Kind & Size**: `Doc` | `26` lines
- **Purpose**: FECL-Bench v4.2 integrity erratum — Status: protocol correction before any v4 model fitting and before any v4 TEST access.

### [`docs/FECL-V4.3-ERRATUM.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/docs/FECL-V4.3-ERRATUM.md)
- **Kind & Size**: `Doc` | `16` lines
- **Purpose**: FECL-Bench v4.3 metadata and acquisition erratum — Status: final benchmark candidate before model fitting and TEST access.

### [`docs/FECL-V4.4-ERRATUM.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/docs/FECL-V4.4-ERRATUM.md)
- **Kind & Size**: `Doc` | `13` lines
- **Purpose**: FECL-Bench v4.4 certificate-taxonomy erratum — Status: final benchmark candidate before model fitting and TEST access.

### [`docs/FECL-V4.5-ERRATUM.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/docs/FECL-V4.5-ERRATUM.md)
- **Kind & Size**: `Doc` | `12` lines
- **Purpose**: FECL-Bench v4.5 label-blind invariant-ontology erratum — Status: final benchmark candidate before model fitting and TEST access.

### [`docs/LIMITATIONS.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/docs/LIMITATIONS.md)
- **Kind & Size**: `Doc` | `34` lines
- **Purpose**: Research Limitations & Operational Boundaries: CARVE-FECL — **Standard:** Section 101 & Section 103 of Principal Research Directive

### [`docs/MODEL_CARD.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/docs/MODEL_CARD.md)
- **Kind & Size**: `Doc` | `108` lines
- **Purpose**: Model Card: CARVE-FECL (v4.5) — **Model Name:** Calibrated Active Risk Verification with Financial Evidence Consistency Learning (CARVE-FECL)

### [`docs/RESEARCH_REPORT.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/docs/RESEARCH_REPORT.md)
- **Kind & Size**: `Doc` | `191` lines
- **Purpose**: CARVE-FECL: Calibrated Active Risk Verification with Financial Evidence Consistency Learning — **Authors:** Joint Research Directorate (Frontier AI/ML & Financial Systems Panel)

### [`docs/TEST-FREEZE.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/docs/TEST-FREEZE.md)
- **Kind & Size**: `Doc` | `18` lines
- **Purpose**: FECL-v4 TEST freeze contract — This file defines the process; it is not evidence that a freeze or TEST run already occurred.

### [`docs/WEB-INTERFACE-AUDIT.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/docs/WEB-INTERFACE-AUDIT.md)
- **Kind & Size**: `Doc` | `34` lines
- **Purpose**: Web interface audit — CARVE research instrument — Scope: `TryVerifier.tsx`, `ProofConsole.tsx`, `CarveResearchLab.tsx`, and the associated proof/research styles.

### [`docs/research-v2/asian-fintech-research-review.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/docs/research-v2/asian-fintech-research-review.md)
- **Kind & Size**: `Doc` | `28` lines
- **Purpose**: Asian fintech research review — | Source | Institution / problem | Result | Transfer decision |

### [`docs/research-v2/competitor-forensics.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/docs/research-v2/competitor-forensics.md)
- **Kind & Size**: `Doc` | `30` lines
- **Purpose**: Competitor forensics — | Provider | Ingestion -> features -> model | Decision / evidence / automation | Human / feedback / metrics | Whitespace

### [`docs/research-v2/dataset-and-labeling-plan.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/docs/research-v2/dataset-and-labeling-plan.md)
- **Kind & Size**: `Doc` | `46` lines
- **Purpose**: Dataset and labeling plan — - **DESIGN DECISION:** The atomic deployment/evaluation unit is a complete dispute case, not a sentence.

### [`docs/research-v2/evaluation-protocol.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/docs/research-v2/evaluation-protocol.md)
- **Kind & Size**: `Doc` | `41` lines
- **Purpose**: Evaluation protocol — - **DESIGN DECISION:** Before each experiment, save hypothesis, data version/hash, split manifest, candidate config, see

### [`docs/research-v2/evidence-graph-study.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/docs/research-v2/evidence-graph-study.md)
- **Kind & Size**: `Doc` | `45` lines
- **Purpose**: Evidence graph study — - **DESIGN DECISION:** A case graph is an auditable intermediate representation even when no GNN is used.

### [`docs/research-v2/final-go-no-go.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/docs/research-v2/final-go-no-go.md)
- **Kind & Size**: `Doc` | `38` lines
- **Purpose**: Final go / no-go — - **DESIGN DECISION — GO:** Continue Dispute Integrity Gate as a narrow, read-only `refund_not_processed_v1` financial e

### [`docs/research-v2/global-literature-review.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/docs/research-v2/global-literature-review.md)
- **Kind & Size**: `Doc` | `35` lines
- **Purpose**: Global literature review — - **FACT:** This review prioritizes peer-reviewed conference/journal pages, official proceedings, and author-hosted pape

### [`docs/research-v2/high-level-system-design.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/docs/research-v2/high-level-system-design.md)
- **Kind & Size**: `Doc` | `63` lines
- **Purpose**: High-level system design — - **DESIGN DECISION:** The system is a read-only decision-support verifier. It has no payment, refund, accept, contest o

### [`docs/research-v2/interactive-product-spec.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/docs/research-v2/interactive-product-spec.md)
- **Kind & Size**: `Doc` | `60` lines
- **Purpose**: Interactive AI Risk Research Workbench — ```text

### [`docs/research-v2/ml-system-architecture.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/docs/research-v2/ml-system-architecture.md)
- **Kind & Size**: `Doc` | `71` lines
- **Purpose**: ML system architecture — ```text

### [`docs/research-v2/model-tournament.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/docs/research-v2/model-tournament.md)
- **Kind & Size**: `Doc` | `50` lines
- **Purpose**: Model tournament — - **DESIGN DECISION:** Candidates compete on identical case-level inputs, grouped splits, saved predictions and predecla

### [`docs/research-v2/novelty-falsification.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/docs/research-v2/novelty-falsification.md)
- **Kind & Size**: `Doc` | `36` lines
- **Purpose**: Novelty falsification — - **RESEARCH RESULT:** “AI-generated dispute evidence is novel” is false. Stripe, Chargeflow, Justt, Forter and Signifyd

### [`docs/research-v2/patent-landscape.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/docs/research-v2/patent-landscape.md)
- **Kind & Size**: `Doc` | `27` lines
- **Purpose**: Patent landscape — **Disclaimer:** **FACT:** This is a technical prior-art scan, not a legal freedom-to-operate opinion.

### [`docs/research-v2/problem-decomposition.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/docs/research-v2/problem-decomposition.md)
- **Kind & Size**: `Doc` | `56` lines
- **Purpose**: Problem decomposition — **Scope:** Razorpay AI Buildathon Track 02, one loss class selected: refund/credit-not-processed evidence-integrity fail

### [`docs/research-v2/quant-research-principles.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/docs/research-v2/quant-research-principles.md)
- **Kind & Size**: `Doc` | `30` lines
- **Purpose**: Quant research principles — - **INDUSTRY CLAIM:** IMC publicly describes a workflow of hypotheses, historical back-tests, incremental changes agains

### [`docs/research-v2/report-source.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/docs/research-v2/report-source.md)
- **Kind & Size**: `Doc` | `48` lines
- **Purpose**: Research-v2 canonical report source — **Date:** 2026-09-01

### [`docs/research-v2/research-hypotheses.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/docs/research-v2/research-hypotheses.md)
- **Kind & Size**: `Doc` | `62` lines
- **Purpose**: Pre-registered research hypotheses — **DESIGN DECISION:** These hypotheses define a new `research-v2` program. They do not reopen, relabel, threshold-tune or

### [`docs/research-v2/risk-control-study.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/docs/research-v2/risk-control-study.md)
- **Kind & Size**: `Doc` | `43` lines
- **Purpose**: Risk-control study — - **ASSUMPTION:** Let `C_FPASS` be the cost of allowing an internally invalid packet, `C_FBLOCK` the cost of delaying a 

### [`docs/research-v2/ui-source-audit.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/docs/research-v2/ui-source-audit.md)
- **Kind & Size**: `Doc` | `27` lines
- **Purpose**: UI source audit — **FACT — scope.** This is a source-level review against the Web Interface Guidelines fetched from the upstream Vercel re

## 14. Research Receipts & Artifacts (`research/`, `paper/`, `results/`)

### [`output/CARVE-System-Design-render.pdf`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/output/CARVE-System-Design-render.pdf)
- **Kind & Size**: `Other` | `5012` lines

### [`output/CARVE-System-Design.docx`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/output/CARVE-System-Design.docx)
- **Kind & Size**: `Other` | `13111` lines

### [`output/pdf/carve-fecl-bench-v4.5-paper.pdf`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/output/pdf/carve-fecl-bench-v4.5-paper.pdf)
- **Kind & Size**: `Other` | `225` lines

### [`paper/dataset-card.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/paper/dataset-card.md)
- **Kind & Size**: `Doc` | `34` lines
- **Purpose**: DIG-FECL-SYN-v2 dataset card — Synthetic diagnostic benchmark for evidence/state consistency in the narrow refund-not-processed

### [`paper/dispute-integrity-gate-research.pdf`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/paper/dispute-integrity-gate-research.pdf)
- **Kind & Size**: `Other` | `7311` lines

### [`paper/figures/fecl-v2-dev-f1.png`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/paper/figures/fecl-v2-dev-f1.png)
- **Kind & Size**: `Other` | `954` lines

### [`paper/figures/fecl-v2-dev-pr.png`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/paper/figures/fecl-v2-dev-pr.png)
- **Kind & Size**: `Other` | `1079` lines

### [`paper/figures/fecl-v2-dev-risk-coverage.png`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/paper/figures/fecl-v2-dev-risk-coverage.png)
- **Kind & Size**: `Other` | `1067` lines

### [`paper/figures/fecl-v2-test-f1.png`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/paper/figures/fecl-v2-test-f1.png)
- **Kind & Size**: `Other` | `991` lines

### [`paper/figures/fecl-v2-test-pr.png`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/paper/figures/fecl-v2-test-pr.png)
- **Kind & Size**: `Other` | `1499` lines

### [`paper/figures/fecl-v2-test-risk-coverage.png`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/paper/figures/fecl-v2-test-risk-coverage.png)
- **Kind & Size**: `Other` | `1226` lines

### [`paper/generated/asset-manifest.json`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/paper/generated/asset-manifest.json)
- **Kind & Size**: `Other` | `39` lines

### [`paper/generated/macros.tex`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/paper/generated/macros.tex)
- **Kind & Size**: `Other` | `19` lines

### [`paper/main.tex`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/paper/main.tex)
- **Kind & Size**: `Other` | `235` lines

### [`paper/model-card.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/paper/model-card.md)
- **Kind & Size**: `Doc` | `27` lines
- **Purpose**: FECL v2 neuro-symbolic relation model card — `RESEARCH_WINNER_NOT_DEPLOYED`. The product runtime remains `regex-baseline-v1`.

### [`paper/references.bib`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/paper/references.bib)
- **Kind & Size**: `Other` | `97` lines

### [`paper/reproducibility-checklist.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/paper/reproducibility-checklist.md)
- **Kind & Size**: `Doc` | `26` lines
- **Purpose**: Reproducibility checklist — - [x] Scientific question and promotion gates frozen before TEST.

### [`paper/supplementary/error-examples.tex`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/paper/supplementary/error-examples.tex)
- **Kind & Size**: `Other` | `7` lines

### [`paper/tables/calibration.tex`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/paper/tables/calibration.tex)
- **Kind & Size**: `Other` | `8` lines

### [`paper/tables/family-slices.tex`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/paper/tables/family-slices.tex)
- **Kind & Size**: `Other` | `4` lines

### [`paper/tables/fecl-v2-calibration-delta.csv`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/paper/tables/fecl-v2-calibration-delta.csv)
- **Kind & Size**: `Other` | `8` lines

### [`paper/tables/fecl-v2-counterfactual.csv`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/paper/tables/fecl-v2-counterfactual.csv)
- **Kind & Size**: `Other` | `9` lines

### [`paper/tables/fecl-v2-dev-results.csv`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/paper/tables/fecl-v2-dev-results.csv)
- **Kind & Size**: `Other` | `9` lines

### [`paper/tables/fecl-v2-test-results.csv`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/paper/tables/fecl-v2-test-results.csv)
- **Kind & Size**: `Other` | `9` lines

### [`paper/tables/main-results.tex`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/paper/tables/main-results.tex)
- **Kind & Size**: `Other` | `10` lines

### [`research/FECL_V2_LEAKAGE_AUDIT.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/research/FECL_V2_LEAKAGE_AUDIT.md)
- **Kind & Size**: `Doc` | `76` lines
- **Purpose**: FECL-Bench V2: Comprehensive Leakage & Point-in-Time Audit — **Benchmark Version:** `FECL-BENCH-V2`

### [`research/baseline_results.json`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/research/baseline_results.json)
- **Kind & Size**: `Other` | `177` lines

### [`research/comprehensive_audit_results.json`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/research/comprehensive_audit_results.json)
- **Kind & Size**: `Other` | `582` lines

### [`research/confidence_intervals.json`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/research/confidence_intervals.json)
- **Kind & Size**: `Other` | `30` lines

### [`research/cross_generator_results.json`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/research/cross_generator_results.json)
- **Kind & Size**: `Other` | `81` lines

### [`research/data_scaling_fit.json`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/research/data_scaling_fit.json)
- **Kind & Size**: `Other` | `50` lines

### [`research/disagreement_results.json`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/research/disagreement_results.json)
- **Kind & Size**: `Other` | `15` lines

### [`research/document_benchmarks.json`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/research/document_benchmarks.json)
- **Kind & Size**: `Other` | `78` lines

### [`research/empirical_training_results.json`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/research/empirical_training_results.json)
- **Kind & Size**: `Other` | `255` lines

### [`research/error_analysis.json`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/research/error_analysis.json)
- **Kind & Size**: `Other` | `36` lines

### [`research/experiment_registry.jsonl`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/research/experiment_registry.jsonl)
- **Kind & Size**: `Other` | `7` lines

### [`research/externality_matrix.json`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/research/externality_matrix.json)
- **Kind & Size**: `Other` | `175` lines

### [`research/falsification_smoke_receipt.json`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/research/falsification_smoke_receipt.json)
- **Kind & Size**: `Other` | `53` lines

### [`research/final_results.json`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/research/final_results.json)
- **Kind & Size**: `Other` | `1175` lines

### [`research/final_results_v2.json`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/research/final_results_v2.json)
- **Kind & Size**: `Other` | `1397` lines

### [`research/five_seed_manifest.json`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/research/five_seed_manifest.json)
- **Kind & Size**: `Other` | `91` lines

### [`research/generalization.json`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/research/generalization.json)
- **Kind & Size**: `Other` | `175` lines

### [`research/hypotheses.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/research/hypotheses.md)
- **Kind & Size**: `Doc` | `62` lines
- **Purpose**: Formal Research Hypotheses & Falsification Protocol: CARVE-FECL — **System:** Calibrated Active Risk Verification with Financial Evidence Consistency Learning (CARVE-FECL)

### [`research/learning_curves.json`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/research/learning_curves.json)
- **Kind & Size**: `Other` | `1172` lines

### [`research/merchant_cost_scenarios.yaml`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/research/merchant_cost_scenarios.yaml)
- **Kind & Size**: `Other` | `22` lines

### [`research/merchant_economics.json`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/research/merchant_economics.json)
- **Kind & Size**: `Other` | `16` lines

### [`research/merchant_monte_carlo.json`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/research/merchant_monte_carlo.json)
- **Kind & Size**: `Other` | `44` lines

### [`research/ood_results.json`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/research/ood_results.json)
- **Kind & Size**: `Other` | `6` lines

### [`research/policy_frontier.json`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/research/policy_frontier.json)
- **Kind & Size**: `Other` | `101` lines

### [`research/prior_art_matrix.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/research/prior_art_matrix.md)
- **Kind & Size**: `Doc` | `19` lines
- **Purpose**: Prior Art Matrix: CARVE-FECL vs Related Work — **Protocol:** Section 87 & Section 88 of Principal Research Directive

### [`research/protocol.md`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/research/protocol.md)
- **Kind & Size**: `Doc` | `77` lines
- **Purpose**: Formal Research Protocol: CARVE-FECL — **Protocol Version:** 1.0.0-FREEZE

### [`research/risk_limits.yaml`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/research/risk_limits.yaml)
- **Kind & Size**: `Other` | `18` lines

### [`research/rule_holdout.json`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/research/rule_holdout.json)
- **Kind & Size**: `Other` | `34` lines

### [`research/sample_efficiency.json`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/research/sample_efficiency.json)
- **Kind & Size**: `Other` | `92` lines

### [`research/statistical_tests.json`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/research/statistical_tests.json)
- **Kind & Size**: `Other` | `23` lines

### [`research/statistical_tests_v2.json`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/research/statistical_tests_v2.json)
- **Kind & Size**: `Other` | `23` lines

### [`research/tail_risk.json`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/research/tail_risk.json)
- **Kind & Size**: `Other` | `59` lines

### [`research/training_manifest.json`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/research/training_manifest.json)
- **Kind & Size**: `Other` | `103` lines

### [`results/holdout-regex-v1-20260823-final.json`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/results/holdout-regex-v1-20260823-final.json)
- **Kind & Size**: `Other` | `2404` lines

### [`results/holdout-regex-v1-20260823-final.json.sha256`](file:///c:/code_shit/RAZOR/dispute-integrity-gate-spec/results/holdout-regex-v1-20260823-final.json.sha256)
- **Kind & Size**: `Other` | `1` lines
