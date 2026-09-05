import type { SandboxEvaluateRequest } from "../api";

const refundStatuses = new Set([
  "none",
  "created",
  "pending",
  "processed",
  "failed",
  "cancelled",
]);
const simulations = new Set([
  undefined,
  "none",
  "model_outage",
  "hash_mismatch",
  "ocr_corruption",
]);

export function isSandboxRequest(
  value: unknown,
): value is SandboxEvaluateRequest {
  if (!value || typeof value !== "object") return false;
  const item = value as Record<string, unknown>;
  return (
    typeof item.raw_reason_code === "string" &&
    item.raw_reason_code.length > 0 &&
    item.raw_reason_code.length <= 128 &&
    typeof item.payment_amount_inr === "string" &&
    item.payment_amount_inr.length > 0 &&
    item.payment_amount_inr.length <= 32 &&
    typeof item.customer_communication === "string" &&
    item.customer_communication.length > 0 &&
    item.customer_communication.length <= 10_000 &&
    typeof item.refund_ledger_complete === "boolean" &&
    typeof item.refund_status === "string" &&
    refundStatuses.has(item.refund_status) &&
    (item.refund_amount_inr === null ||
      (typeof item.refund_amount_inr === "string" &&
        item.refund_amount_inr.length <= 32)) &&
    simulations.has(item.simulation as string | undefined)
  );
}
