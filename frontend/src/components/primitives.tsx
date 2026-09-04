import React, { useEffect, useRef, type ReactNode } from "react";
import {
  CheckCircle,
  WarningOctagon,
  Warning,
  CircleNotch,
  ArrowsLeftRight,
  GitDiff,
  DownloadSimple,
} from "@phosphor-icons/react";
import type { GateStatus } from "../api";

export interface StatusBadgeProps {
  status: GateStatus | "CLEAR" | "PENDING" | string | null | undefined;
  size?: "sm" | "md";
}

export function StatusBadge({ status, size = "md" }: StatusBadgeProps) {
  if (!status || status === "PENDING") {
    return (
      <span
        className={`ds-badge ds-badge-pending ds-badge-${size}`}
        role="status"
      >
        ○ PENDING
      </span>
    );
  }
  const normalized = status.toUpperCase();
  if (
    normalized === "PASS" ||
    normalized === "CLEAR" ||
    normalized === "GATE CLEAR"
  ) {
    return (
      <span className={`ds-badge ds-badge-pass ds-badge-${size}`} role="status">
        <CheckCircle size={14} aria-hidden="true" weight="bold" /> PASS
      </span>
    );
  }
  if (normalized === "REVIEW" || normalized === "REVIEW REQUIRED") {
    return (
      <span
        className={`ds-badge ds-badge-review ds-badge-${size}`}
        role="status"
      >
        <Warning size={14} aria-hidden="true" weight="bold" /> REVIEW
      </span>
    );
  }
  if (normalized === "BLOCK" || normalized === "LOCAL HOLD") {
    return (
      <span
        className={`ds-badge ds-badge-block ds-badge-${size}`}
        role="status"
      >
        <WarningOctagon size={14} aria-hidden="true" weight="bold" /> BLOCK
      </span>
    );
  }
  return (
    <span className={`ds-badge ds-badge-info ds-badge-${size}`} role="status">
      {status}
    </span>
  );
}

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "danger" | "quiet";
  busy?: boolean;
  icon?: ReactNode;
  children: ReactNode;
}

export function Button({
  variant = "secondary",
  busy = false,
  disabled = false,
  icon,
  children,
  className = "",
  ...rest
}: ButtonProps) {
  return (
    <button
      className={`ds-btn ds-btn-${variant} ${className}`}
      disabled={disabled || busy}
      aria-busy={busy}
      {...rest}
    >
      {busy ? (
        <CircleNotch className="ds-spinner" size={16} aria-hidden="true" />
      ) : (
        icon
      )}
      <span>{children}</span>
    </button>
  );
}

export interface CardProps {
  title?: ReactNode;
  subtitle?: ReactNode;
  badge?: ReactNode;
  actions?: ReactNode;
  children: ReactNode;
  className?: string;
}

export function Card({
  title,
  subtitle,
  badge,
  actions,
  children,
  className = "",
}: CardProps) {
  return (
    <div className={`ds-card ${className}`}>
      {(title || subtitle || badge || actions) && (
        <div className="ds-card-header">
          <div>
            {title && <h3>{title}</h3>}
            {subtitle && <p>{subtitle}</p>}
          </div>
          {(badge || actions) && (
            <div
              style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}
            >
              {badge}
              {actions}
            </div>
          )}
        </div>
      )}
      <div className="ds-card-body">{children}</div>
    </div>
  );
}

export interface MetricStatProps {
  label: string;
  value: ReactNode;
  subtitle?: ReactNode;
  accent?: "pass" | "review" | "block" | "info";
}

export function MetricStat({
  label,
  value,
  subtitle,
  accent,
}: MetricStatProps) {
  return (
    <div className="ds-metric-stat">
      <span>{label}</span>
      <strong
        style={accent ? { color: `var(--ds-${accent}-solid)` } : undefined}
      >
        {value}
      </strong>
      {subtitle && <small>{subtitle}</small>}
    </div>
  );
}

export interface ProofCertificateProps {
  certificateId: string;
  invariantId: string;
  proofSha256: string;
  solver?: string;
  facts: Array<{
    kind: string;
    field: string;
    value: string | number | boolean;
    evidenceId?: string | null;
  }>;
}

export function ProofCertificateView({
  certificateId,
  invariantId,
  proofSha256,
  solver = "Z3 SMT Solver (UNSAT Minimizer)",
  facts,
}: ProofCertificateProps) {
  return (
    <article className="ds-proof-cert minimum-certificate">
      <div className="ds-proof-cert-header">
        <div>
          <span className="ds-badge ds-badge-block">
            Minimum contradiction certificate
          </span>
          <strong
            style={{
              marginLeft: "0.5rem",
              fontSize: "0.75rem",
              fontFamily: "var(--font-mono)",
            }}
          >
            {invariantId}
          </strong>
        </div>
        <span
          style={{
            fontSize: "0.6875rem",
            color: "var(--ds-ink-muted)",
            fontFamily: "var(--font-mono)",
          }}
        >
          {solver}
        </span>
      </div>
      <ul className="ds-proof-facts">
        {facts.map((fact, idx) => (
          <li key={`${fact.field}-${idx}`}>
            <div>
              <span
                className="ds-badge ds-badge-info"
                style={{ marginRight: "0.5rem" }}
              >
                {fact.kind}
              </span>
              <strong>{fact.field}</strong>: <code>{String(fact.value)}</code>
            </div>
            {fact.evidenceId && (
              <small
                style={{
                  color: "var(--ds-ink-muted)",
                  fontFamily: "var(--font-mono)",
                }}
              >
                src: {fact.evidenceId}
              </small>
            )}
          </li>
        ))}
      </ul>
      <div
        style={{
          padding: "0.5rem 1rem",
          background: "var(--ds-surface-subtle)",
          borderTop: "1px solid var(--ds-border-subtle)",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          fontSize: "0.6875rem",
          fontFamily: "var(--font-mono)",
          color: "var(--ds-ink-muted)",
        }}
      >
        <span>CERT ID: {certificateId}</span>
        <span>SHA-256: {proofSha256.slice(0, 16)}…</span>
      </div>
    </article>
  );
}

export interface IntelligentReviewProps {
  missingEvidenceId: string;
  reason: string;
  action: string;
  costInr: number;
  decisionImpact: string;
  onAcquire?: () => void;
  busy?: boolean;
}

export function IntelligentReviewCard({
  missingEvidenceId,
  reason,
  action,
  costInr,
  decisionImpact,
  onAcquire,
  busy = false,
}: IntelligentReviewProps) {
  return (
    <div
      className="ds-review-callout"
      role="region"
      aria-label="Intelligent Review Abstention"
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: "0.5rem",
        }}
      >
        <h4>Abstention: Incomplete Financial Grounding</h4>
        <span className="ds-badge ds-badge-review">Cost: ₹{costInr}</span>
      </div>
      <p>
        <strong>Unresolved Evidence:</strong> <code>{missingEvidenceId}</code>:{" "}
        {reason}
      </p>
      <p
        style={{
          margin: "0.25rem 0 0.75rem",
          color: "var(--ds-ink-secondary)",
        }}
      >
        <strong>Impact:</strong> {decisionImpact}
      </p>
      {onAcquire && (
        <Button
          variant="secondary"
          busy={busy}
          onClick={onAcquire}
          icon={<DownloadSimple size={15} />}
        >
          {action}
        </Button>
      )}
    </div>
  );
}

export interface CounterfactualRepairProps {
  pairId?: string;
  field: string;
  fromValue: string | number;
  toValue: string | number;
  originalCommunication: string;
  repairedCommunication?: string;
  decisionChange: string;
  onApplyRepair?: () => void;
}

export function CounterfactualRepairCard({
  field,
  fromValue,
  toValue,
  originalCommunication,
  repairedCommunication,
  decisionChange,
  onApplyRepair,
}: CounterfactualRepairProps) {
  return (
    <div
      style={{
        padding: "1rem",
        borderRadius: "var(--radius-lg)",
        border: "1px solid var(--ds-border)",
        background: "var(--ds-surface)",
        display: "flex",
        flexDirection: "column",
        gap: "0.75rem",
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
        }}
      >
        <span className="ds-badge ds-badge-info">
          <ArrowsLeftRight size={14} style={{ marginRight: "0.25rem" }} />
          Minimal Causal Counterfactual
        </span>
        <span
          style={{
            fontSize: "0.75rem",
            color: "var(--ds-pass-solid)",
            fontWeight: 700,
          }}
        >
          {decisionChange}
        </span>
      </div>
      <div style={{ fontSize: "0.8125rem", color: "var(--ds-ink-secondary)" }}>
        Changing causal field <code>{field}</code> from{" "}
        <span
          style={{
            textDecoration: "line-through",
            color: "var(--ds-block-solid)",
          }}
        >
          {String(fromValue)}
        </span>{" "}
        to{" "}
        <strong style={{ color: "var(--ds-pass-solid)" }}>
          {String(toValue)}
        </strong>{" "}
        removes the contradiction.
      </div>
      <blockquote
        style={{
          margin: 0,
          padding: "0.5rem 0.75rem",
          background: "var(--ds-surface-muted)",
          borderLeft: "3px solid var(--ds-info-solid)",
          fontStyle: "italic",
          fontSize: "0.8125rem",
          borderRadius: "0 var(--radius-sm) var(--radius-sm) 0",
        }}
      >
        “{repairedCommunication ?? originalCommunication}”
      </blockquote>
      {onApplyRepair && (
        <Button
          variant="secondary"
          onClick={onApplyRepair}
          icon={<GitDiff size={15} />}
        >
          Apply Counterfactual Repair
        </Button>
      )}
    </div>
  );
}

export interface ModalDialogProps {
  open: boolean;
  onClose: () => void;
  title: ReactNode;
  children: ReactNode;
  actions?: ReactNode;
}

export function ModalDialog({
  open,
  onClose,
  title,
  children,
  actions,
}: ModalDialogProps) {
  const dialogRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!open) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div
      className="ds-modal-overlay"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
      role="dialog"
      aria-modal="true"
      aria-labelledby="ds-modal-title"
    >
      <div className="ds-modal-card" ref={dialogRef}>
        <div className="ds-card-header">
          <h3 id="ds-modal-title">{title}</h3>
          <button
            type="button"
            className="ds-btn ds-btn-quiet"
            onClick={onClose}
            aria-label="Close dialog"
            style={{ minHeight: "auto", padding: "0.25rem 0.5rem" }}
          >
            ✕
          </button>
        </div>
        <div className="ds-card-body">{children}</div>
        {actions && (
          <div
            style={{
              padding: "0.75rem 1.25rem",
              background: "var(--ds-surface-subtle)",
              borderTop: "1px solid var(--ds-border-subtle)",
              display: "flex",
              justifyContent: "flex-end",
              gap: "0.5rem",
            }}
          >
            {actions}
          </div>
        )}
      </div>
    </div>
  );
}
