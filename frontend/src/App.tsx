import { useEffect, useRef, useState } from "react";
import {
  ArrowLeft,
  ArrowRight,
  ArrowsLeftRight,
  Check,
  CheckCircle,
  Quotes,
  ShieldCheck,
  UserCheck,
  WarningOctagon,
  WebhooksLogo,
} from "@phosphor-icons/react";

import {
  fetchCase,
  fetchLatestEvaluation,
  fetchQueue,
  inspectSource,
  markCaseReady,
  overrideLocalHold,
  reprocessCase,
} from "./api";
import type {
  CaseDetail,
  EvaluationResponse,
  GateStatus,
  QueueItem,
} from "./api";
import { ProofConsole } from "./ProofConsole";
import { CarveResearchLab } from "./CarveResearchLab";
import { DecisionEnginePage } from "./DecisionEnginePage";
import { formatMoney, formatTimestamp as displayTimestamp } from "./format";
import { UnifiedNavigation } from "./components/UnifiedNavigation";
import {
  TutorialProvider,
  TutorialSpotlight,
  TutorialTooltip,
} from "./tutorial";

const statusCopy: Record<GateStatus, { label: string; summary: string }> = {
  PASS: {
    label: "GATE CLEAR",
    summary:
      "No supported integrity issue was detected in the evidence available to this verifier.",
  },
  REVIEW: {
    label: "REVIEW REQUIRED",
    summary: "Evidence could not be verified safely. Review the stated reason.",
  },
  BLOCK: {
    label: "LOCAL HOLD",
    summary:
      "A material evidence inconsistency was verified. Review the cited sources before marking this case ready.",
  },
};

const reviewReasonCopy: Record<string, { title: string; action: string }> = {
  F_EVIDENCE_RECOMMENDED_MISSING: {
    title: "Recommended evidence is missing.",
    action: "Add or repair the expected local evidence, then reprocess.",
  },
  F_MODEL_UNAVAILABLE: {
    title: "The semantic extractor was unavailable.",
    action:
      "Restore the configured extractor or offline replay, then reprocess.",
  },
  F_SOURCE_UNGROUNDED: {
    title: "A semantic quote could not be grounded exactly.",
    action: "Inspect the source text or repair the extraction, then reprocess.",
  },
  F_STRUCTURED_STATE_INCOMPLETE: {
    title: "Trusted payment or refund state is incomplete.",
    action: "Repair the local snapshot or ledger export, then reprocess.",
  },
  F_SOURCE_UNSUPPORTED: {
    title: "The evidence input is unsupported in v1.",
    action: "Provide canonical English text or JSON evidence, then reprocess.",
  },
};

function StatusBadge({ status }: { status: GateStatus | null }) {
  if (!status) return <span className="status status-pending">○ PENDING</span>;
  const icon = status === "PASS" ? "✓" : status === "REVIEW" ? "!" : "×";
  return (
    <span
      className={`status status-${status.toLowerCase()}`}
    >{`${icon} ${status}`}</span>
  );
}

function QueueTable({
  items,
  selectedId,
  onSelect,
}: {
  items: QueueItem[];
  selectedId: string | null;
  onSelect: (caseId: string) => void;
}) {
  return (
    <div className="table-scroll">
      <table>
        <thead>
          <tr>
            <th scope="col">Case / dispute</th>
            <th scope="col">Amount</th>
            <th scope="col">Respond by</th>
            <th scope="col">Raw reason</th>
            <th scope="col">Processing</th>
            <th scope="col">Gate</th>
            <th scope="col">Primary reason</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr key={item.case_id} data-selected={item.case_id === selectedId}>
              <td>
                <button
                  className="case-link"
                  onClick={() => onSelect(item.case_id)}
                >
                  <strong>{item.case_id}</strong>
                  <span>{item.dispute_id}</span>
                </button>
              </td>
              <td className="money">
                {formatMoney(item.amount_minor, item.currency)}
              </td>
              <td>{displayTimestamp(item.respond_by)}</td>
              <td className="code">{item.raw_reason_code ?? "None"}</td>
              <td>{item.processing_status}</td>
              <td>
                <StatusBadge status={item.gate_status} />
              </td>
              <td className="code">{item.primary_reason_code ?? "None"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function LocalWorkflowActions({
  detail,
  onShowClaim,
}: {
  detail: CaseDetail;
  onShowClaim: (claimId: string) => void;
}) {
  const [dialogOpen, setDialogOpen] = useState(false);
  const [inspected, setInspected] = useState<Set<string>>(
    () =>
      new Set(
        detail.audit_events
          .filter((event) => event.event_type === "SOURCE_INSPECTED")
          .map((event) => event.details.source_ref)
          .filter((source): source is string => typeof source === "string"),
      ),
  );
  const [reason, setReason] = useState("");
  const [note, setNote] = useState("");
  const [confirmed, setConfirmed] = useState(false);
  const [busy, setBusy] = useState(false);
  const [workflowStatus, setWorkflowStatus] = useState(detail.workflow_status);
  const [message, setMessage] = useState<string | null>(null);
  const dialogHeadingRef = useRef<HTMLHeadingElement | null>(null);
  const dialogRef = useRef<HTMLElement | null>(null);
  const triggerRef = useRef<HTMLButtonElement | null>(null);
  const requiredRefs = Array.from(
    new Set(
      detail.findings
        .filter((finding) => finding.decision_effect === "BLOCK")
        .flatMap((finding) => [
          ...finding.claim_refs,
          ...finding.structured_refs,
        ]),
    ),
  );
  const allInspected =
    requiredRefs.length > 0 &&
    requiredRefs.every((source) => inspected.has(source));
  const canOverride =
    allInspected &&
    Boolean(reason) &&
    confirmed &&
    (reason !== "OTHER" || Boolean(note.trim()));

  useEffect(() => {
    if (dialogOpen) dialogHeadingRef.current?.focus();
  }, [dialogOpen]);

  function closeDialog() {
    setDialogOpen(false);
    window.setTimeout(() => triggerRef.current?.focus(), 0);
  }

  function keepFocusInDialog(event: React.KeyboardEvent<HTMLDivElement>) {
    if (event.key === "Escape") {
      closeDialog();
      return;
    }
    if (event.key !== "Tab" || !dialogRef.current) return;
    const focusable = Array.from(
      dialogRef.current.querySelectorAll<HTMLElement>(
        'button:not([disabled]), select:not([disabled]), textarea:not([disabled]), input:not([disabled]), [tabindex]:not([tabindex="-1"])',
      ),
    );
    const first = focusable.at(0);
    const last = focusable.at(-1);
    if (!first || !last) return;
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  }

  async function recordInspection(sourceRef: string) {
    const claim = detail.grounded_claims.find((item) => item.id === sourceRef);
    if (claim) onShowClaim(claim.id);
    setBusy(true);
    setMessage(null);
    try {
      await inspectSource(
        detail.case.case_id,
        sourceRef,
        claim?.document_id ?? "structured_refund_ledger",
      );
      setInspected((current) => new Set([...current, sourceRef]));
    } catch (failure: unknown) {
      setMessage(
        failure instanceof Error
          ? failure.message
          : "Inspection could not be recorded.",
      );
    } finally {
      setBusy(false);
    }
  }

  async function submitOverride() {
    setBusy(true);
    setMessage(null);
    try {
      const result = await overrideLocalHold(detail.case.case_id, reason, note);
      setWorkflowStatus(result.workflow_status);
      setMessage(
        "Local hold override recorded. Historical BLOCK remains unchanged.",
      );
      closeDialog();
    } catch (failure: unknown) {
      setMessage(
        failure instanceof Error
          ? failure.message
          : "Override could not be recorded.",
      );
    } finally {
      setBusy(false);
    }
  }

  async function markReady() {
    setBusy(true);
    setMessage(null);
    try {
      const result = await markCaseReady(detail.case.case_id);
      setWorkflowStatus(result.workflow_status);
      setMessage(
        "Marked ready in local workflow. No network write was performed.",
      );
    } catch (failure: unknown) {
      setMessage(
        failure instanceof Error
          ? failure.message
          : "Local readiness update failed.",
      );
    } finally {
      setBusy(false);
    }
  }

  const mayMarkReady =
    detail.case.gate_status === "PASS" ||
    workflowStatus === "READY_WITH_OVERRIDE";
  return (
    <section
      className="workflow-actions"
      aria-labelledby="workflow-actions-title"
    >
      <h4 id="workflow-actions-title">Local workflow</h4>
      <p>
        Current state: <strong>{workflowStatus}</strong>
      </p>
      {detail.case.gate_status === "BLOCK" &&
        workflowStatus === "REVIEW_PENDING" && (
          <button
            ref={triggerRef}
            className="secondary-action"
            onClick={() => setDialogOpen(true)}
          >
            Override local hold
          </button>
        )}
      {mayMarkReady && workflowStatus !== "READY_FOR_CONTEST" && (
        <button
          className="primary-action"
          disabled={busy}
          onClick={() => void markReady()}
        >
          Mark ready for contest (local only)
        </button>
      )}
      {message && <p role="status">{message}</p>}

      {dialogOpen && (
        <div
          className="modal-backdrop"
          role="presentation"
          onKeyDown={keepFocusInDialog}
        >
          <section
            ref={dialogRef}
            className="override-dialog"
            role="dialog"
            aria-modal="true"
            aria-labelledby="override-title"
          >
            <div className="dialog-header">
              <h2 id="override-title" ref={dialogHeadingRef} tabIndex={-1}>
                Override local hold
              </h2>
              <button
                type="button"
                aria-label="Close override dialog"
                onClick={closeDialog}
              >
                ×
              </button>
            </div>
            <p>
              The material finding remains in history. Inspect every cited
              source before changing local readiness.
            </p>
            <h3>Sources requiring inspection</h3>
            <ul className="inspection-list">
              {requiredRefs.map((sourceRef) => {
                const claim = detail.grounded_claims.find(
                  (item) => item.id === sourceRef,
                );
                const isInspected = inspected.has(sourceRef);
                return (
                  <li key={sourceRef}>
                    <span>
                      <strong>
                        {claim
                          ? "Communication claim"
                          : sourceRef === "structured_refund_ledger"
                            ? "Structured refund ledger"
                            : "Structured refund record"}
                      </strong>
                      <code>{sourceRef}</code>
                    </span>
                    <button
                      type="button"
                      disabled={busy || isInspected}
                      onClick={() => void recordInspection(sourceRef)}
                    >
                      {isInspected ? "✓ Inspected" : "Open and acknowledge"}
                    </button>
                  </li>
                );
              })}
            </ul>
            <label>
              Override reason
              <select
                name="override_reason"
                autoComplete="off"
                value={reason}
                onChange={(event) => setReason(event.target.value)}
              >
                <option value="">Select a reason</option>
                <option value="SOURCE_DATA_ERROR">Source data error</option>
                <option value="EVIDENCE_REPAIRED_OUTSIDE_APP">
                  Evidence repaired outside app
                </option>
                <option value="KNOWN_BUSINESS_EXCEPTION">
                  Known business exception
                </option>
                <option value="DISAGREE_WITH_RULE">Disagree with rule</option>
                <option value="OTHER">Other</option>
              </select>
            </label>
            <label>
              Note {reason === "OTHER" ? "(required)" : "(optional)"}
              <textarea
                name="override_note"
                autoComplete="off"
                value={note}
                maxLength={500}
                onChange={(event) => setNote(event.target.value)}
              />
            </label>
            <label className="confirmation">
              <input
                name="local_readiness_confirmation"
                type="checkbox"
                checked={confirmed}
                onChange={(event) => setConfirmed(event.target.checked)}
              />
              This changes only the local readiness state
            </label>
            <div className="dialog-actions">
              <button
                type="button"
                className="secondary-action"
                onClick={closeDialog}
              >
                Cancel
              </button>
              <button
                type="button"
                className="primary-action"
                disabled={busy || !canOverride}
                onClick={() => void submitOverride()}
              >
                Record local override
              </button>
            </div>
          </section>
        </div>
      )}
    </section>
  );
}

function CaseWorkspace({ detail }: { detail: CaseDetail }) {
  const status = detail.case.gate_status;
  const copy = status ? statusCopy[status] : null;
  const [selectedClaimId, setSelectedClaimId] = useState<string | null>(null);
  const highlightRef = useRef<HTMLElement | null>(null);
  const selectedClaim = detail.grounded_claims.find(
    (claim) => claim.id === selectedClaimId,
  );
  const [reprocessing, setReprocessing] = useState(false);
  const [reprocessMessage, setReprocessMessage] = useState<string | null>(null);
  const reviewReasons = Array.isArray(detail.gate_decision?.review_reasons)
    ? detail.gate_decision.review_reasons.filter(
        (reason): reason is string => typeof reason === "string",
      )
    : [];

  async function requestReprocess() {
    setReprocessing(true);
    setReprocessMessage(null);
    try {
      const queued = await reprocessCase(detail.case.case_id);
      setReprocessMessage(
        `Queued local reprocess job ${queued.job_id}. No network write was performed.`,
      );
    } catch (reason: unknown) {
      setReprocessMessage(
        reason instanceof Error ? reason.message : "Reprocess request failed.",
      );
    } finally {
      setReprocessing(false);
    }
  }

  useEffect(() => {
    if (selectedClaimId) highlightRef.current?.focus();
  }, [selectedClaimId]);

  function sourceText(documentId: string, canonicalText: string) {
    if (
      !selectedClaim ||
      selectedClaim.document_id !== documentId ||
      selectedClaim.span_start === null ||
      selectedClaim.span_end === null ||
      selectedClaim.span_start < 0 ||
      selectedClaim.span_end <= selectedClaim.span_start ||
      selectedClaim.span_end > canonicalText.length
    ) {
      return canonicalText;
    }
    return (
      <>
        {canonicalText.slice(0, selectedClaim.span_start)}
        <mark ref={highlightRef} tabIndex={-1} data-testid="source-highlight">
          {canonicalText.slice(
            selectedClaim.span_start,
            selectedClaim.span_end,
          )}
        </mark>
        {canonicalText.slice(selectedClaim.span_end)}
      </>
    );
  }
  return (
    <section className="workspace" aria-labelledby="workspace-title">
      <header className="case-header">
        <div>
          <p className="section-kicker">
            Selected case · {detail.case.dispute_id}
          </p>
          <h2 id="workspace-title">{detail.case.case_id}</h2>
        </div>
        <div className="gate-summary">
          <StatusBadge status={status} />
          <strong>{copy?.label ?? "PROCESSING"}</strong>
          <span>
            {copy?.summary ?? "A gate decision is not available yet."}
          </span>
        </div>
        <p className="boundary">Decision support only: not a win prediction.</p>
      </header>

      <div className="workspace-grid">
        <aside className="case-context" aria-label="Case context">
          <h3>Case context</h3>
          <dl>
            <div>
              <dt>Payment</dt>
              <dd className="code">{detail.case.payment_id}</dd>
            </div>
            <div>
              <dt>Amount</dt>
              <dd className="money">
                {formatMoney(detail.case.amount_minor, detail.case.currency)}
              </dd>
            </div>
            <div>
              <dt>Raw reason code</dt>
              <dd className="code">
                {detail.case.raw_reason_code ?? "Not supplied"}
              </dd>
            </div>
            <div>
              <dt>Local profile</dt>
              <dd className="code">{detail.case.reason_profile}</dd>
            </div>
            <div>
              <dt>Workflow</dt>
              <dd>{detail.workflow_status}</dd>
            </div>
          </dl>
          <h3>Structured refunds</h3>
          {detail.refunds.length ? (
            <ul className="record-list">
              {detail.refunds.map((refund) => (
                <li key={refund.id}>
                  <strong>
                    {formatMoney(refund.amount_minor, refund.currency)}
                  </strong>
                  <span>{refund.local_status}</span>
                  <span className="code">{refund.reference ?? refund.id}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="empty-note">No refund records in the local ledger.</p>
          )}
        </aside>

        <article className="evidence-panel" aria-labelledby="evidence-title">
          <div className="section-heading">
            <div>
              <p className="section-kicker">Canonical local evidence</p>
              <h3 id="evidence-title">Evidence</h3>
            </div>
            <span className="synthetic-label">SYNTHETIC DEMO DATA</span>
          </div>
          {detail.evidence_documents.map((document) => (
            <section className="document" key={document.id}>
              <header>
                <strong>{document.source_type.replaceAll("_", " ")}</strong>
                <span>{document.source_system ?? "Local fixture"}</span>
              </header>
              <p className="document-text">
                {sourceText(document.id, document.canonical_text)}
              </p>
              <details>
                <summary>Technical source details</summary>
                <dl>
                  <div>
                    <dt>Document ID</dt>
                    <dd className="code">{document.id}</dd>
                  </div>
                  <div>
                    <dt>Ingested</dt>
                    <dd>{displayTimestamp(document.ingested_at)}</dd>
                  </div>
                  <div>
                    <dt>SHA-256</dt>
                    <dd className="digest">{document.content_sha256}</dd>
                  </div>
                </dl>
              </details>
            </section>
          ))}
          {!detail.evidence_documents.length && (
            <p className="empty-note">
              No customer communication is available.
            </p>
          )}
          {!!detail.grounded_claims.length && (
            <section className="claims" aria-labelledby="claims-title">
              <h3 id="claims-title">Grounded claims</h3>
              {detail.grounded_claims.map((claim) => (
                <blockquote key={claim.id}>
                  <p>“{claim.source_quote}”</p>
                  <footer>
                    {claim.claim_type.replaceAll("_", " ")} ·{" "}
                    {claim.grounding_status}
                  </footer>
                  <button
                    className="source-link"
                    aria-label={`Show exact source for ${claim.claim_type.replaceAll("_", " ")}`}
                    onClick={() => setSelectedClaimId(claim.id)}
                  >
                    Show exact source
                  </button>
                </blockquote>
              ))}
            </section>
          )}
          <p className="sr-only" role="status">
            {selectedClaim
              ? `Focused exact source quote for ${selectedClaim.claim_type.replaceAll("_", " ")}.`
              : ""}
          </p>
        </article>

        <aside className="findings-panel" aria-labelledby="findings-title">
          <p className="section-kicker">Deterministic gate</p>
          <h3 id="findings-title">Findings</h3>
          {status === "REVIEW" && (
            <section
              className="review-panel"
              aria-labelledby="review-reason-title"
            >
              <h4 id="review-reason-title">Why review is required</h4>
              {reviewReasons.length ? (
                <ul>
                  {reviewReasons.map((reason) => {
                    const copyForReason = reviewReasonCopy[reason];
                    return (
                      <li key={reason}>
                        <strong>{copyForReason?.title ?? reason}</strong>
                        <span>
                          {copyForReason?.action ??
                            "Inspect the recorded reason, repair local evidence, then reprocess."}
                        </span>
                        <code>{reason}</code>
                      </li>
                    );
                  })}
                </ul>
              ) : (
                <p>The recorded decision requires analyst review.</p>
              )}
              <button
                className="primary-action"
                disabled={reprocessing}
                onClick={() => void requestReprocess()}
              >
                {reprocessing ? "Queueing…" : "Reprocess after repair"}
              </button>
              {reprocessMessage && <p role="status">{reprocessMessage}</p>}
            </section>
          )}
          {detail.findings.map((finding) => (
            <article
              className={`finding finding-${finding.decision_effect.toLowerCase()}`}
              key={finding.id}
            >
              <div className="finding-header">
                <StatusBadge status={finding.decision_effect} />
                <code>{finding.rule_code}</code>
              </div>
              <p>{finding.explanation}</p>
              <dl>
                <div>
                  <dt>Decision effect</dt>
                  <dd>{finding.decision_effect}</dd>
                </div>
                <div>
                  <dt>Claim sources</dt>
                  <dd className="code">
                    {finding.claim_refs.join(", ") || "None"}
                  </dd>
                </div>
                <div>
                  <dt>Structured sources</dt>
                  <dd className="code">
                    {finding.structured_refs.join(", ") || "None"}
                  </dd>
                </div>
              </dl>
            </article>
          ))}
          {!detail.findings.length && (
            <p className="empty-note">
              No supported integrity finding is recorded.
            </p>
          )}
          <div className="local-only-note">
            <strong>Local decision support only</strong>
            <span>
              No accept, contest, refund, or payment write is available.
            </span>
          </div>
          <LocalWorkflowActions
            detail={detail}
            onShowClaim={setSelectedClaimId}
          />
        </aside>
      </div>
    </section>
  );
}

function objectValue(value: unknown): Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : {};
}

function ratioLabel(value: unknown): string {
  const ratio = objectValue(value);
  const measured =
    typeof ratio.value === "number"
      ? `${(ratio.value * 100).toFixed(1)}%`
      : "N/A";
  return typeof ratio.numerator === "number" &&
    typeof ratio.denominator === "number"
    ? `${measured} (${ratio.numerator}/${ratio.denominator})`
    : measured;
}

function scoreLabel(value: unknown): string {
  return typeof value === "number" ? value.toFixed(3) : "N/A";
}

function EvaluationView() {
  const [evaluation, setEvaluation] = useState<EvaluationResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    void fetchLatestEvaluation()
      .then((response) => {
        if (active) setEvaluation(response);
      })
      .catch((failure: unknown) => {
        if (active)
          setError(
            failure instanceof Error
              ? failure.message
              : "Evaluation unavailable",
          );
      });
    return () => {
      active = false;
    };
  }, []);

  if (error)
    return (
      <p role="alert" className="error-banner">
        {error}
      </p>
    );
  if (!evaluation)
    return (
      <p role="status" className="loading">
        Loading saved evaluation artifact…
      </p>
    );
  if (evaluation.status === "NOT_YET_MEASURED") {
    return (
      <section
        className="evaluation empty-evaluation"
        aria-labelledby="evaluation-title"
      >
        <p className="section-kicker">Artifact-backed evaluation</p>
        <h2 id="evaluation-title">NOT YET MEASURED</h2>
        <p>
          No saved, digest-verified result artifact is available. No performance
          values are shown.
        </p>
      </section>
    );
  }

  const material = objectValue(evaluation.metrics.material_conflict);
  const operational = objectValue(evaluation.metrics.operational);
  const claims = objectValue(evaluation.metrics.claims);
  const confusion = objectValue(evaluation.metrics.confusion_matrix);
  const slices = objectValue(evaluation.metrics.slices);
  const baseline =
    evaluation.metrics.baseline_delta ?? evaluation.metrics.baseline_comparison;
  const costs = evaluation.metrics.cost_sensitivity;
  return (
    <section className="evaluation" aria-labelledby="evaluation-title">
      <header className="evaluation-header">
        <div>
          <p className="section-kicker">Saved result artifact</p>
          <p>
            Historical baseline evidence. These metrics do not evaluate the
            repaired current runtime.
          </p>
          <h2 id="evaluation-title">Evaluation · {evaluation.run_id}</h2>
        </div>
        <span className="synthetic-label">SYNTHETIC BENCHMARK</span>
      </header>
      <p className="synthetic-warning">{evaluation.synthetic_warning}</p>
      <dl className="provenance-grid">
        <div>
          <dt>Dataset</dt>
          <dd>
            {evaluation.dataset.dataset_id} ·{" "}
            {evaluation.dataset.split.toUpperCase()}
          </dd>
        </div>
        <div>
          <dt>Extractor</dt>
          <dd>{evaluation.system.extractor_id}</dd>
        </div>
        <div>
          <dt>Recorded</dt>
          <dd>{displayTimestamp(evaluation.created_at)}</dd>
        </div>
        <div>
          <dt>Artifact SHA-256</dt>
          <dd className="digest">{evaluation.artifact_sha256}</dd>
        </div>
        <div>
          <dt>Config SHA-256</dt>
          <dd className="digest">{evaluation.system.config_sha256}</dd>
        </div>
        <div>
          <dt>Code revision</dt>
          <dd className="code">{evaluation.system.code_commit}</dd>
        </div>
      </dl>

      <div className="metric-grid">
        <article>
          <h3>Material precision</h3>
          <strong>{ratioLabel(material.precision)}</strong>
        </article>
        <article>
          <h3>Material recall</h3>
          <strong>{ratioLabel(material.recall)}</strong>
        </article>
        <article>
          <h3>Material F1</h3>
          <strong>{scoreLabel(material.f1)}</strong>
        </article>
        <article>
          <h3>REVIEW rate</h3>
          <strong>{ratioLabel(operational.review_rate)}</strong>
        </article>
        <article>
          <h3>Decision coverage</h3>
          <strong>{ratioLabel(operational.auto_decision_coverage)}</strong>
        </article>
        <article>
          <h3>Claim micro-F1</h3>
          <strong>{scoreLabel(objectValue(claims.micro).f1)}</strong>
        </article>
        <article>
          <h3>Exact grounding</h3>
          <strong>{ratioLabel(claims.exact_grounding_rate)}</strong>
        </article>
        <article>
          <h3>False PASS / BLOCK</h3>
          <strong>{String(operational.false_pass_block_cases ?? "N/A")}</strong>
        </article>
        <article>
          <h3>False BLOCK / non-BLOCK</h3>
          <strong>
            {String(operational.false_block_nonblock_cases ?? "N/A")}
          </strong>
        </article>
      </div>

      <div className="evaluation-tables">
        <section>
          <h3>Confusion matrix</h3>
          <pre>{JSON.stringify(confusion, null, 2)}</pre>
        </section>
        <section>
          <h3>Slice counts</h3>
          <pre>{JSON.stringify(slices, null, 2)}</pre>
        </section>
        <section>
          <h3>Baseline delta</h3>
          <pre>
            {baseline
              ? JSON.stringify(baseline, null, 2)
              : "Not present in saved artifact."}
          </pre>
        </section>
        <section>
          <h3>Illustrative cost sensitivity</h3>
          <pre>
            {costs
              ? JSON.stringify(costs, null, 2)
              : "Not present in saved artifact."}
          </pre>
        </section>
      </div>
    </section>
  );
}

function AnalystExperience({
  initialView = "cases",
  onNavigate,
}: {
  initialView?: "cases" | "evaluation";
  onNavigate: (destination: ProductRoute) => void;
}) {
  const [items, setItems] = useState<QueueItem[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [detail, setDetail] = useState<CaseDetail | null>(null);
  const [gateFilter, setGateFilter] = useState("");
  const [processingFilter, setProcessingFilter] = useState("");
  const [loadingQueue, setLoadingQueue] = useState(true);
  const [loadingCase, setLoadingCase] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [view, setView] = useState<"cases" | "evaluation">(initialView);
  const selectedIdRef = useRef<string | null>(null);

  function selectCase(caseId: string) {
    if (caseId === selectedIdRef.current) return;
    selectedIdRef.current = caseId;
    setDetail(null);
    setLoadingCase(true);
    setSelectedId(caseId);
  }

  useEffect(() => {
    let active = true;
    void fetchQueue(gateFilter, processingFilter)
      .then((response) => {
        if (!active) return;
        setError(null);
        setItems(response.items);
        const current = selectedIdRef.current;
        const next = response.items.some((item) => item.case_id === current)
          ? current
          : (response.items[0]?.case_id ?? null);
        if (next !== current) {
          selectedIdRef.current = next;
          setDetail(null);
          setLoadingCase(next !== null);
          setSelectedId(next);
        }
      })
      .catch((reason: unknown) => {
        if (active)
          setError(
            reason instanceof Error ? reason.message : "Queue unavailable",
          );
      })
      .finally(() => {
        if (active) setLoadingQueue(false);
      });
    return () => {
      active = false;
    };
  }, [gateFilter, processingFilter]);

  useEffect(() => {
    let active = true;
    if (!selectedId) {
      return () => {
        active = false;
      };
    }
    void fetchCase(selectedId)
      .then((response) => {
        if (active) {
          setError(null);
          setDetail(response);
        }
      })
      .catch((reason: unknown) => {
        if (active)
          setError(
            reason instanceof Error ? reason.message : "Case unavailable",
          );
      })
      .finally(() => {
        if (active) setLoadingCase(false);
      });
    return () => {
      active = false;
    };
  }, [selectedId]);

  return (
    <>
      <a className="skip-link" href="#analyst-main">
        Skip to main content
      </a>
      <UnifiedNavigation
        currentRoute="workspace"
        currentView={view}
        onNavigate={(route, nextView) => {
          if (
            route === "workspace" &&
            (nextView === "cases" || nextView === "evaluation")
          ) {
            setView(nextView);
            return;
          }
          if (
            route === "evaluation" ||
            (route === "proof" && nextView === "evaluation")
          ) {
            setView("evaluation");
            return;
          }
          onNavigate(route as ProductRoute);
        }}
      />
      <main id="analyst-main">
        <header className="app-header">
          <div>
            <p className="eyebrow">Razorpay AI Buildathon 2026 · Track 02</p>
            <h1>Dispute Integrity Gate</h1>
            <p>
              Read-only evidence integrity verification for refund-not-processed
              disputes.
            </p>
          </div>
          <div className="mode-badge">
            <span aria-hidden="true">●</span>OFFLINE REPLAY · PRECOMPUTED REGEX
          </div>
        </header>
        <nav className="workspace-view-nav" aria-label="Primary">
          <button
            type="button"
            className={view === "cases" ? "active" : ""}
            aria-current={view === "cases" ? "page" : undefined}
            onClick={() => setView("cases")}
          >
            Cases
          </button>
          <button
            type="button"
            className={view === "evaluation" ? "active" : ""}
            aria-current={view === "evaluation" ? "page" : undefined}
            onClick={() => setView("evaluation")}
          >
            Evaluation
          </button>
        </nav>
        {view === "cases" ? (
          <>
            <section className="queue" aria-labelledby="queue-title">
              <div className="queue-toolbar">
                <div>
                  <p className="section-kicker">Analyst triage</p>
                  <h2 id="queue-title">Case queue</h2>
                </div>
                <div className="filters" aria-label="Queue filters">
                  <label>
                    Gate state
                    <select
                      name="gate_filter"
                      autoComplete="off"
                      value={gateFilter}
                      onChange={(event) => {
                        setLoadingQueue(true);
                        setGateFilter(event.target.value);
                      }}
                    >
                      <option value="">All gate states</option>
                      <option value="REVIEW">Review</option>
                      <option value="BLOCK">Block</option>
                      <option value="PASS">Pass</option>
                    </select>
                  </label>
                  <label>
                    Processing
                    <select
                      name="processing_filter"
                      autoComplete="off"
                      value={processingFilter}
                      onChange={(event) => {
                        setLoadingQueue(true);
                        setProcessingFilter(event.target.value);
                      }}
                    >
                      <option value="">All processing states</option>
                      <option value="READY">Ready</option>
                      <option value="PROCESSING">Processing</option>
                      <option value="FAILED">Failed</option>
                    </select>
                  </label>
                </div>
              </div>
              {loadingQueue ? (
                <p role="status" className="loading">
                  Loading local case queue…
                </p>
              ) : items.length ? (
                <QueueTable
                  items={items}
                  selectedId={selectedId}
                  onSelect={selectCase}
                />
              ) : (
                <p className="empty-note">
                  No cases match the current local filters.
                </p>
              )}
            </section>
            {error && (
              <p role="alert" className="error-banner">
                {error}
              </p>
            )}
            {loadingCase && (
              <p role="status" className="loading">
                Loading case evidence…
              </p>
            )}
            {!loadingCase && detail && <CaseWorkspace detail={detail} />}
          </>
        ) : (
          <EvaluationView />
        )}
        <footer className="app-footer">
          Synthetic demo data · Local state only · No Razorpay writes
        </footer>
      </main>
    </>
  );
}

type ProductRoute =
  | "proof"
  | "landing"
  | "walkthrough"
  | "complete"
  | "workspace"
  | "evaluation"
  | "research"
  | "decision-engine"
  | "ai";

function routeFromPath(pathname: string): ProductRoute {
  if (pathname === "/start") return "landing";
  if (pathname === "/walkthrough") return "walkthrough";
  if (pathname === "/complete") return "complete";
  if (pathname === "/research") return "research";
  if (pathname === "/decision-engine" || pathname === "/ai")
    return "decision-engine";
  if (pathname === "/evaluation") return "evaluation";
  if (pathname === "/workspace") return "workspace";
  return "proof";
}

const routePaths: Record<ProductRoute, string> = {
  proof: "/proof",
  landing: "/start",
  walkthrough: "/walkthrough",
  complete: "/complete",
  workspace: "/workspace",
  evaluation: "/evaluation",
  research: "/research",
  "decision-engine": "/decision-engine",
  ai: "/decision-engine",
};

const guidedSteps = [
  { short: "Signed notice", title: "A dispute notice arrives" },
  {
    short: "Exact claim",
    title: "What did the communication actually claim?",
  },
  { short: "Compare records", title: "The records disagree" },
  { short: "Human control", title: "Human judgment stays in control" },
] as const;

function ProductHeader({
  onNavigate,
}: {
  onNavigate?: (route: ProductRoute) => void;
} = {}) {
  return (
    <UnifiedNavigation
      currentRoute="landing"
      onNavigate={(route) => onNavigate?.(route as ProductRoute)}
    />
  );
}

function ProductFooter() {
  return (
    <footer className="product-page product-footer">
      <span className="product-mono">
        Synthetic demo data · Local state only
      </span>
      <span>PASS is not a win prediction · BLOCK is not a legal verdict</span>
    </footer>
  );
}

function Landing({
  onStart,
  onWorkspace,
}: {
  onStart: () => void;
  onWorkspace: () => void;
}) {
  const preview = [
    ["A dispute arrives", "Authenticate the signed notice.", WebhooksLogo],
    ["Read the exact claim", "Ground the customer communication.", Quotes],
    [
      "Compare trusted state",
      "Find the material contradiction.",
      ArrowsLeftRight,
    ],
    ["Keep judgment human", "Inspect before any local override.", UserCheck],
  ] as const;
  return (
    <section className="product-landing" aria-labelledby="landing-title">
      <div>
        <p className="product-eyebrow">
          Razorpay AI Buildathon 2026 · Track 02
        </p>
        <h1 id="landing-title">
          Catch the contradiction before it becomes an expensive submission.
        </h1>
        <p className="product-lede">
          In 90 seconds, follow one refund-not-processed dispute from signed
          notice to a human-controlled local hold. No setup. No risk jargon. No
          network write.
        </p>
        <div className="product-actions">
          <button className="product-primary" type="button" onClick={onStart}>
            Start the guided walkthrough <ArrowRight size={18} />
          </button>
          <button className="product-quiet" type="button" onClick={onWorkspace}>
            Open analyst workspace
          </button>
        </div>
        <div className="product-truth-row" aria-label="Product boundaries">
          <span>
            <strong>Scope:</strong> refund-not-processed only
          </span>
          <span>
            <strong>Data:</strong> synthetic demo
          </span>
          <span>
            <strong>Authority:</strong> human decision
          </span>
        </div>
      </div>
      <aside
        className="product-journey-preview"
        aria-label="What the walkthrough covers"
      >
        <div className="product-preview-head">
          <p className="product-eyebrow">What you will prove</p>
          <h2>One case. Four guided steps.</h2>
          <p>
            Each screen explains what matters and gives you one clear next
            action.
          </p>
        </div>
        {preview.map(([title, subtitle, Icon], index) => (
          <div className="product-preview-step" key={title}>
            <span className="product-step-number product-mono">
              {String(index + 1).padStart(2, "0")}
            </span>
            <div>
              <strong>{title}</strong>
              <small>{subtitle}</small>
            </div>
            <Icon size={19} aria-hidden="true" />
          </div>
        ))}
      </aside>
    </section>
  );
}

function GuidedEvidence({
  detail,
  step,
}: {
  detail: CaseDetail | null;
  step: number;
}) {
  if (!detail) {
    return (
      <p role="status" className="product-loading">
        Loading the signed local demo case…
      </p>
    );
  }
  const claim =
    detail.grounded_claims.find(
      (item) => item.claim_type === "refund_claimed_processed",
    ) ?? detail.grounded_claims[0];
  const processedTotal = detail.refunds
    .filter((refund) => refund.local_status === "processed")
    .reduce((total, refund) => total + refund.amount_minor, 0);
  const finding =
    detail.findings.find((item) => item.decision_effect === "BLOCK") ??
    detail.findings[0];

  if (step === 0) {
    return (
      <article className="product-evidence-card">
        <div className="product-card-head">
          <strong>Authenticated dispute notice</strong>
          <span className="product-status product-pass">
            <Check size={13} /> SIGNATURE VALID
          </span>
        </div>
        <dl className="product-notice-grid">
          <div className="product-notice-cell">
            <dt>Documented event</dt>
            <dd className="product-mono">payment.dispute.created</dd>
          </div>
          <div className="product-notice-cell">
            <dt>Event identity</dt>
            <dd className="product-mono">x-razorpay-event-id</dd>
          </div>
          <div className="product-notice-cell">
            <dt>Case</dt>
            <dd className="product-mono">{detail.case.case_id}</dd>
          </div>
          <div className="product-notice-cell">
            <dt>Processing</dt>
            <dd>{detail.case.processing_status}</dd>
          </div>
        </dl>
        <div className="product-safe-boundary">
          <strong>What the system will not do:</strong> initiate a dispute,
          contact a customer, accept a chargeback, contest it, issue a refund,
          or change a payment.
        </div>
      </article>
    );
  }
  if (step === 1) {
    return (
      <article className="product-evidence-card">
        <div className="product-card-head">
          <strong>Customer communication</strong>
          <span className="product-status product-pass">
            <Quotes size={13} /> EXACTLY GROUNDED
          </span>
        </div>
        <div className="product-document">
          <div className="product-document-meta">
            <span className="product-mono">
              {claim?.document_id ?? "No document"}
            </span>
            <span>Synthetic fixture</span>
          </div>
          <blockquote>
            “
            <mark>
              {claim?.source_quote ?? "No decision-relevant claim was found."}
            </mark>
            ”
          </blockquote>
          <div className="product-grounding">
            <CheckCircle size={17} /> Exact quote found once in the cited
            document
          </div>
        </div>
      </article>
    );
  }
  if (step === 2) {
    return (
      <article className="product-evidence-card">
        <div className="product-card-head">
          <strong>Deterministic evidence comparison</strong>
          <span className="product-status product-block">
            <WarningOctagon size={13} /> LOCAL HOLD
          </span>
        </div>
        <div className="product-comparison">
          <section className="product-compare-side">
            <h3>Customer says</h3>
            <p className="product-compare-quote">
              “{claim?.source_quote ?? "No grounded claim"}”
            </p>
            <p className="product-source-ref product-mono">
              {claim?.document_id}
            </p>
          </section>
          <section className="product-compare-side">
            <h3>Ledger shows</h3>
            <div className="product-ledger">
              <div>
                <span>Processed total</span>
                <strong className="product-red">
                  {formatMoney(processedTotal, detail.case.currency)}
                </strong>
              </div>
              <div>
                <span>Records</span>
                <strong>{detail.refunds.length}</strong>
              </div>
              <div>
                <span>Snapshot</span>
                <strong className="product-mono">
                  {detail.payment_snapshot?.snapshot_complete
                    ? "COMPLETE"
                    : "INCOMPLETE"}
                </strong>
              </div>
            </div>
            <p className="product-source-ref product-mono">
              refund_ledger_snapshot
            </p>
          </section>
        </div>
        <div className="product-conflict">
          <strong>
            {finding?.explanation ?? "A material conflict requires review."}
          </strong>
          <p>
            Deterministic finding:{" "}
            {finding?.rule_code ?? detail.case.primary_reason_code}
          </p>
        </div>
      </article>
    );
  }
  return (
    <article className="product-evidence-card">
      <div className="product-card-head">
        <strong>Local workflow boundary</strong>
        <span className="product-status product-review">
          <UserCheck size={13} /> HUMAN REVIEW
        </span>
      </div>
      <div className="product-human-panel">
        <h3>Both sides of the conflict are visible before override.</h3>
        <div className="product-check-row">
          <CheckCircle size={20} />
          <div>
            <strong>Customer source inspected</strong>
            <p>Exact claim and document identity are available.</p>
          </div>
        </div>
        <div className="product-check-row">
          <CheckCircle size={20} />
          <div>
            <strong>Trusted ledger inspected</strong>
            <p>The local structured snapshot is visible beside the claim.</p>
          </div>
        </div>
        <div className="product-check-row">
          <ShieldCheck size={20} />
          <div>
            <strong>No external write available</strong>
            <p>
              Any override changes only local analyst workflow state and
              requires a structured reason.
            </p>
          </div>
        </div>
      </div>
    </article>
  );
}

function Walkthrough({
  detail,
  error,
  onExit,
  onComplete,
}: {
  detail: CaseDetail | null;
  error: string | null;
  onExit: () => void;
  onComplete: () => void;
}) {
  const [step, setStep] = useState(0);
  const [inspected, setInspected] = useState(false);
  const titleRef = useRef<HTMLHeadingElement | null>(null);
  useEffect(() => titleRef.current?.focus(), [step]);
  const copy = [
    {
      body: "The workflow begins only after an existing dispute reaches the merchant. The raw request is authenticated before any case is created.",
      why: "Defense-only starts at ingestion. An unsigned or altered request is rejected instead of becoming a risk decision.",
      next: "Verify that the incoming event is authentic.",
      action: "Verify the evidence",
    },
    {
      body: "The extractor may only return typed claims backed by an exact quotation. Local code verifies that the quote really exists in the source document.",
      why: "A fluent summary is not evidence. The human reviewer needs the exact words and source before a claim can affect policy.",
      next: "Read the highlighted words, then compare them with trusted refund state.",
      action: "Compare with trusted state",
    },
    {
      body: "Now the grounded claim is compared with trusted structured state. Money, dates, identifiers, and the final gate are deterministic.",
      why: "A material mismatch requires a local hold before a human proceeds.",
      next: "Inspect both cited sources, then advance to human review.",
      action: inspected
        ? "Continue to human review"
        : "Inspect both cited sources",
    },
    {
      body: "The gate has no submission authority. A consequential local override remains inspection-gated and requires a structured reason.",
      why: "The system supports a decision; it does not predict a chargeback win or make a legal judgment.",
      next: "Complete the walkthrough and choose where to continue.",
      action: "Complete walkthrough",
    },
  ][step];
  function advance() {
    if (step === 2 && !inspected) {
      setInspected(true);
      return;
    }
    if (step === 3) {
      onComplete();
      return;
    }
    setStep((current) => current + 1);
  }
  return (
    <section className="product-walkthrough" aria-labelledby="walk-title">
      <div className="product-walk-head">
        <div>
          <p className="product-eyebrow">Guided case · Step {step + 1} of 4</p>
          <h1 id="walk-title" ref={titleRef} tabIndex={-1}>
            {guidedSteps[step].title}
          </h1>
        </div>
        <button className="product-exit" onClick={onExit}>
          Exit walkthrough
        </button>
      </div>
      <div className="product-progress" aria-label="Walkthrough progress">
        {guidedSteps.map((item, index) => (
          <div
            key={item.short}
            className={`product-progress-item ${index === step ? "current" : ""} ${index < step ? "done" : ""}`}
            aria-current={index === step ? "step" : undefined}
          >
            <span className="product-progress-dot">
              {index < step ? <Check size={13} /> : index + 1}
            </span>
            <span className="product-progress-copy">
              <strong>{item.short}</strong>
              <small>
                {index < step
                  ? "Complete"
                  : index === step
                    ? "Current step"
                    : "Upcoming"}
              </small>
            </span>
          </div>
        ))}
      </div>
      {error ? (
        <p role="alert" className="error-banner">
          {error}
        </p>
      ) : (
        <div className="product-stage">
          <aside className="product-guide">
            <p className="product-eyebrow">What am I looking at?</p>
            <h2>{guidedSteps[step].title}</h2>
            <p>{copy.body}</p>
            <div className="product-guide-note">
              <strong>Why it matters</strong>
              <p>{copy.why}</p>
            </div>
            <div className="product-guide-note">
              <strong>What to do next</strong>
              <p>{copy.next}</p>
            </div>
          </aside>
          <div className="product-evidence-stage">
            <GuidedEvidence detail={detail} step={step} />
          </div>
        </div>
      )}
      <div className="product-actionbar">
        <button
          className="product-secondary"
          disabled={step === 0}
          onClick={() => setStep((current) => Math.max(0, current - 1))}
        >
          <ArrowLeft size={17} /> Back
        </button>
        <span className="product-step-hint">
          One action at a time. You can exit without changing case state.
        </span>
        <button
          className="product-primary"
          disabled={!detail || Boolean(error)}
          onClick={advance}
        >
          {copy.action} <ArrowRight size={17} />
        </button>
      </div>
    </section>
  );
}

function WalkthroughComplete({
  onWorkspace,
  onAi,
}: {
  onWorkspace: () => void;
  onAi: () => void;
}) {
  return (
    <section className="product-complete" aria-labelledby="complete-title">
      <div className="product-complete-card">
        <span className="product-complete-icon">
          <ShieldCheck size={29} />
        </span>
        <p className="product-eyebrow">Walkthrough complete</p>
        <h1 id="complete-title">
          You stopped an unsupported claim from moving forward blindly.
        </h1>
        <p>
          The system authenticated an existing dispute, grounded the exact
          customer claim, compared it with trusted state, and created only a
          local human-review hold.
        </p>
        <div className="product-actions product-centered">
          <button className="product-primary" onClick={onWorkspace}>
            Open analyst workspace
          </button>
          <button className="product-secondary" onClick={onAi}>
            See the Decision Engine
          </button>
        </div>
      </div>
    </section>
  );
}

export const AiLab = DecisionEnginePage;

export function App({
  initialRoute = routeFromPath(window.location.pathname),
}: {
  initialRoute?: ProductRoute;
}) {
  const [route, setRoute] = useState<ProductRoute>(initialRoute);
  const [guidedDetail, setGuidedDetail] = useState<CaseDetail | null>(null);
  const [guidedError, setGuidedError] = useState<string | null>(null);

  function navigate(next: ProductRoute) {
    if (next === route) return;
    window.history.pushState({}, "", routePaths[next]);
    setRoute(next);
  }

  useEffect(() => {
    const restoreRoute = () =>
      setRoute(routeFromPath(window.location.pathname));
    window.addEventListener("popstate", restoreRoute);
    return () => window.removeEventListener("popstate", restoreRoute);
  }, []);

  useEffect(() => {
    if (route !== "walkthrough" || guidedDetail) return;
    let active = true;
    async function loadWalkthrough() {
      try {
        setGuidedError(null);
        const queue = await fetchQueue("BLOCK", "");
        const caseId = queue.items[0]?.case_id;
        if (!caseId)
          throw new Error("The seeded local demo has no BLOCK case.");
        const nextDetail = await fetchCase(caseId);
        if (active) setGuidedDetail(nextDetail);
      } catch (reason: unknown) {
        if (active) {
          setGuidedError(
            reason instanceof Error
              ? reason.message
              : "Guided case unavailable",
          );
        }
      }
    }
    void loadWalkthrough();
    return () => {
      active = false;
    };
  }, [route, guidedDetail]);

  function startWalkthrough() {
    navigate("walkthrough");
  }
  let content: React.ReactNode;
  if (route === "workspace" || route === "evaluation") {
    content = (
      <AnalystExperience
        initialView={route === "evaluation" ? "evaluation" : "cases"}
        onNavigate={navigate}
      />
    );
  } else if (route === "proof") {
    content = <ProofConsole onNavigate={(r) => navigate(r as ProductRoute)} />;
  } else if (route === "research") {
    content = <CarveResearchLab onBack={() => navigate("proof")} />;
  } else if (route === "ai" || route === "decision-engine") {
    content = (
      <DecisionEnginePage
        caseId={guidedDetail?.case.case_id ?? null}
        onBack={() => navigate("proof")}
        onWorkspace={() => navigate("workspace")}
      />
    );
  } else {
    content = (
      <div className="product-app">
        <a className="skip-link" href="#product-main">
          Skip to main content
        </a>
        <ProductHeader onNavigate={navigate} />
        <main id="product-main" className="product-page product-main">
          {route === "landing" && (
            <Landing
              onStart={startWalkthrough}
              onWorkspace={() => navigate("workspace")}
            />
          )}
          {route === "walkthrough" && (
            <Walkthrough
              detail={guidedDetail}
              error={guidedError}
              onExit={() => navigate("landing")}
              onComplete={() => navigate("complete")}
            />
          )}
          {route === "complete" && (
            <WalkthroughComplete
              onWorkspace={() => navigate("workspace")}
              onAi={() => navigate("ai")}
            />
          )}
        </main>
        <ProductFooter />
      </div>
    );
  }

  return (
    <TutorialProvider
      route={route}
      onNavigate={(next) => navigate(next as ProductRoute)}
    >
      <TutorialSpotlight />
      <TutorialTooltip />
      {content}
    </TutorialProvider>
  );
}
