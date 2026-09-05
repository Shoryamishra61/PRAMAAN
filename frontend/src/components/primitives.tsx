import React, { type ReactNode } from "react";
import {
  CheckCircle,
  WarningOctagon,
  Warning,
  CircleNotch,
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

export interface IntelligentReviewProps {
  missingEvidenceId: string;
  reason: string;
  action: string;
  decisionImpact: string;
  onAcquire?: () => void;
  busy?: boolean;
}

export function IntelligentReviewCard({
  missingEvidenceId,
  reason,
  action,
  decisionImpact,
  onAcquire,
  busy = false,
}: IntelligentReviewProps) {
  return (
    <div
      className="ds-review-callout"
      role="region"
      aria-label="Evidence needed for review"
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: "0.5rem",
        }}
      >
        <h4>Additional evidence needed</h4>
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
