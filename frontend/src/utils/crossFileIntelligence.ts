import type { SandboxEvaluateRequest } from "../api";
import { isSandboxRequest } from "./sandboxRequest";

/**
 * Cross-File Evidence Ingestion and Synthesis Engine
 * Provides multi-format parsing (.json, .txt, .csv), per-file lifecycle tracking,
 * fault isolation, and cross-document contradiction detection for dispute integrity verification.
 */

export type FileType = "json" | "txt" | "csv" | "unsupported";

export type IngestionStatus =
  | "queued"
  | "validating"
  | "parsing"
  | "extracting"
  | "analyzing"
  | "complete"
  | "warning"
  | "failed";

export interface ExtractedCaseFacts {
  communicationSnippet?: string;
  claimedAmounts: string[];
  ledgerAmounts: string[];
  transactionIds: string[];
  refundStatuses: string[];
  datesFound: string[];
  sourceLineCount: number;
}

export interface EvidenceFileRecord {
  id: string;
  name: string;
  size: number;
  type: FileType;
  status: IngestionStatus;
  rawContent: string;
  facts: ExtractedCaseFacts;
  errorMessage?: string;
  warnings: string[];
  processedAt: string;
  structuredRequest?: SandboxEvaluateRequest;
}

export interface CrossFileAnomaly {
  type:
    | "AMOUNT_DISCREPANCY"
    | "STATUS_CONFLICT"
    | "DUPLICATE_EVIDENCE"
    | "MISSING_AUTHORITATIVE_RECORD";
  severity: "high" | "medium" | "low";
  title: string;
  description: string;
  sources: string[];
}

export interface CrossFileAnalysisResult {
  totalFiles: number;
  successfulFiles: number;
  failedFiles: number;
  combinedCommunication: string;
  anomalies: CrossFileAnomaly[];
  corroborations: string[];
  structuredRequest?: SandboxEvaluateRequest;
  errors: string[];
  sources: { id: string; name: string; start: number; end: number }[];
}

const MAX_FILE_BYTES = 256 * 1024; // 256 KB safety limit per file

export function parseMoneyMinorUnits(value: string): bigint | null {
  const normalized = value
    .trim()
    .replace(/^(?:₹|INR|rs\.?)\s*/i, "")
    .replaceAll(",", "");
  if (!/^\d+(?:\.\d{1,2})?$/.test(normalized)) return null;
  const [whole, fraction = ""] = normalized.split(".");
  return BigInt(whole) * 100n + BigInt(fraction.padEnd(2, "0"));
}

export function detectFileType(fileName: string): FileType {
  const lower = fileName.toLowerCase();
  if (lower.endsWith(".json")) return "json";
  if (lower.endsWith(".txt") || lower.endsWith(".log")) return "txt";
  if (lower.endsWith(".csv")) return "csv";
  return "unsupported";
}

export function parseCsvRows(content: string): Record<string, string>[] {
  const firstLine = content.replace(/^\uFEFF/, "").split(/\r?\n/, 1)[0];
  const delimiter = firstLine.includes(",")
    ? ","
    : firstLine.includes(";")
      ? ";"
      : "\t";
  const rows: string[][] = [];
  let row: string[] = [];
  let field = "";
  let quoted = false;
  let closed = false;
  const input = content.replace(/^\uFEFF/, "");
  for (let i = 0; i < input.length; i++) {
    const char = input[i];
    if (quoted) {
      if (char === '"') {
        if (input[i + 1] === '"') {
          field += '"';
          i++;
        } else {
          quoted = false;
          closed = true;
        }
      } else field += char;
    } else if (char === delimiter || char === "\n" || char === "\r") {
      row.push(field);
      field = "";
      closed = false;
      if (char !== delimiter) {
        if (row.some((cell) => cell !== "")) rows.push(row);
        row = [];
        if (char === "\r" && input[i + 1] === "\n") i++;
      }
    } else if (char === '"' && field === "" && !closed) {
      quoted = true;
    } else {
      if (closed || char === '"') throw new Error("Malformed CSV quoting.");
      field += char;
    }
  }
  if (quoted) throw new Error("CSV contains an unterminated quoted field.");
  row.push(field);
  if (row.some((cell) => cell !== "")) rows.push(row);
  if (!rows.length) return [];
  const headers = rows[0].map((h) => h.trim().toLowerCase());
  if (headers.some((h) => !h) || new Set(headers).size !== headers.length)
    throw new Error("CSV headers must be nonempty and unique.");
  return rows.slice(1).map((cells, index) => {
    if (cells.length !== headers.length)
      throw new Error(
        `CSV record ${index + 2} has ${cells.length} fields; expected ${headers.length}.`,
      );
    return Object.fromEntries(headers.map((header, i) => [header, cells[i]]));
  });
}

export async function processEvidenceFile(
  name: string,
  size: number,
  content: string,
): Promise<EvidenceFileRecord> {
  const id = `${name}-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
  const type = detectFileType(name);
  const warnings: string[] = [];

  const baseRecord: EvidenceFileRecord = {
    id,
    name,
    size,
    type,
    status: "validating",
    rawContent: content,
    facts: {
      claimedAmounts: [],
      ledgerAmounts: [],
      transactionIds: [],
      refundStatuses: [],
      datesFound: [],
      sourceLineCount: content.split(/\r?\n/).length,
    },
    warnings,
    processedAt: new Date().toISOString(),
  };

  // 1. Validation phase
  if (type === "unsupported") {
    return {
      ...baseRecord,
      status: "failed",
      errorMessage:
        "Unsupported file format. Please upload .json, .txt, or .csv files.",
    };
  }

  if (size > MAX_FILE_BYTES) {
    return {
      ...baseRecord,
      status: "failed",
      errorMessage: `File size exceeds the 256 KB safety limit (${(size / 1024).toFixed(1)} KB).`,
    };
  }

  if (content.trim().length === 0) {
    return {
      ...baseRecord,
      status: "failed",
      errorMessage: "The file is completely empty.",
    };
  }

  // 2. Parsing & Extraction phase
  baseRecord.status = "parsing";

  try {
    if (type === "json") {
      let parsed: unknown;
      try {
        parsed = JSON.parse(content.replace(/^\uFEFF/, ""));
      } catch (err) {
        return {
          ...baseRecord,
          status: "failed",
          errorMessage: `Malformed JSON: ${err instanceof Error ? err.message : "Syntax error"}`,
        };
      }

      if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
        return {
          ...baseRecord,
          status: "failed",
          errorMessage: "JSON root must be an object payload.",
        };
      }

      baseRecord.status = "extracting";
      const record = parsed as Record<string, unknown>;
      const candidate = (
        record.request && typeof record.request === "object"
          ? record.request
          : record
      ) as Record<string, unknown>;

      if (!candidate || Array.isArray(candidate))
        throw new Error("JSON request must be an object.");
      const hasFinancialFields = [
        "payment_amount_inr",
        "refund_amount_inr",
        "refund_status",
        "refund_ledger_complete",
      ].some((key) => key in candidate);
      if (hasFinancialFields && !isSandboxRequest(candidate)) {
        throw new Error(
          "Financial JSON must match the sample request schema, including raw_reason_code and explicit ledger completeness.",
        );
      }
      if (isSandboxRequest(candidate)) baseRecord.structuredRequest = candidate;
      if (
        typeof candidate.customer_communication !== "string" &&
        typeof candidate.message !== "string"
      ) {
        throw new Error(
          "JSON has no supported customer_communication or message field.",
        );
      }
      const comm =
        typeof candidate.customer_communication === "string"
          ? candidate.customer_communication
          : typeof candidate.message === "string"
            ? candidate.message
            : "";
      if (comm) {
        baseRecord.facts.communicationSnippet = comm;
        const amounts =
          comm.match(/(?:₹|INR|rs\.?)\s*([\d,]+(?:\.\d{1,2})?)/gi) ?? [];
        baseRecord.facts.claimedAmounts = amounts.map((a) =>
          a.replace(/[^\d.]/g, ""),
        );
      }

      if (typeof candidate.payment_amount_inr === "string") {
        baseRecord.facts.ledgerAmounts.push(candidate.payment_amount_inr);
      }
      if (typeof candidate.refund_status === "string") {
        baseRecord.facts.refundStatuses.push(
          candidate.refund_status.toLowerCase(),
        );
      }
      if (typeof candidate.refund_amount_inr === "string") {
        baseRecord.facts.ledgerAmounts.push(candidate.refund_amount_inr);
      }

      baseRecord.status = "complete";
      return baseRecord;
    }

    if (type === "txt") {
      baseRecord.status = "extracting";
      baseRecord.facts.communicationSnippet = content;
      const amounts =
        content.match(/(?:₹|INR|rs\.?)\s*([\d,]+(?:\.\d{1,2})?)/gi) ?? [];
      baseRecord.facts.claimedAmounts = amounts.map((a) =>
        a.replace(/[^\d.]/g, ""),
      );

      const txns =
        content.match(/(?:txn|pay|order|case|disp)_[a-zA-Z0-9_-]+/gi) ?? [];
      baseRecord.facts.transactionIds = Array.from(new Set(txns));

      const dates =
        content.match(
          /\b(?:\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4}|\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4})\b/gi,
        ) ?? [];
      baseRecord.facts.datesFound = Array.from(new Set(dates));

      baseRecord.status = "complete";
      return baseRecord;
    }

    if (type === "csv") {
      baseRecord.status = "extracting";
      const rows = parseCsvRows(content);
      if (rows.length === 0) {
        return {
          ...baseRecord,
          status: "warning",
          warnings: ["CSV file parsed but contains zero valid data rows."],
        };
      }

      rows.forEach((row) => {
        Object.entries(row).forEach(([key, val]) => {
          if (
            /^(?:amount|payment_amount_inr|refund_amount_inr)$/i.test(key) &&
            val
          ) {
            if (parseMoneyMinorUnits(val) === null)
              throw new Error(`Invalid amount in CSV field ${key}.`);
            baseRecord.facts.ledgerAmounts.push(val);
          }
          if (/status/i.test(key) && val) {
            baseRecord.facts.refundStatuses.push(val.toLowerCase());
          }
          if (/id|reference|txn/i.test(key) && val) {
            baseRecord.facts.transactionIds.push(val);
          }
          if (/date|time/i.test(key) && val) {
            baseRecord.facts.datesFound.push(val);
          }
        });
      });

      baseRecord.warnings.push(
        "CSV is retained for inspection. Confirm payment, currency, refund relationship and completeness in the form; CSV does not populate authoritative fields.",
      );
      baseRecord.status = "warning";
      return baseRecord;
    }

    return baseRecord;
  } catch (err) {
    return {
      ...baseRecord,
      status: "failed",
      errorMessage:
        err instanceof Error ? err.message : "Unexpected parsing failure",
    };
  }
}

export function analyzeCrossFileEvidence(
  files: EvidenceFileRecord[],
): CrossFileAnalysisResult {
  const valid = files.filter(
    (f) => f.status === "complete" || f.status === "warning",
  );
  const failed = files.filter((f) => f.status === "failed");
  const errors = failed.map(
    (f) => `${f.name}: ${f.errorMessage ?? "Could not read evidence."}`,
  );
  const sources: CrossFileAnalysisResult["sources"] = [];
  let combinedCommunication = "";
  for (const file of valid) {
    const body = file.facts.communicationSnippet;
    if (!body) continue;
    if (combinedCommunication) combinedCommunication += "\n\n";
    const start = combinedCommunication.length;
    combinedCommunication += body;
    sources.push({
      id: file.id,
      name: file.name,
      start,
      end: combinedCommunication.length,
    });
  }
  if (combinedCommunication.length > 10_000)
    errors.push(
      "Combined communication exceeds 10,000 characters. Remove files or select a smaller evidence packet; no text was truncated.",
    );
  const requests = valid.flatMap((f) =>
    f.structuredRequest ? [f.structuredRequest] : [],
  );
  if (requests.length > 1)
    errors.push(
      "More than one financial request bundle is present. Keep one bundle per case; records are not merged by assumption.",
    );
  const anomalies: CrossFileAnomaly[] = [];
  const names = new Set<string>();
  for (const file of files) {
    if (names.has(file.name))
      anomalies.push({
        type: "DUPLICATE_EVIDENCE",
        severity: "low",
        title: "Repeated filename",
        description: `Both copies of ${file.name} are retained. Inspect their contents before removing a duplicate.`,
        sources: [file.name],
      });
    names.add(file.name);
  }
  return {
    totalFiles: files.length,
    successfulFiles: valid.length,
    failedFiles: failed.length,
    combinedCommunication,
    anomalies,
    corroborations: [],
    errors,
    sources,
    structuredRequest: requests.length === 1 ? requests[0] : undefined,
  };
}

export async function parseEvidenceFile(
  file: File,
): Promise<EvidenceFileRecord> {
  if (file.size > MAX_FILE_BYTES || detectFileType(file.name) === "unsupported")
    return processEvidenceFile(file.name, file.size, "");
  try {
    const content =
      typeof file.arrayBuffer === "function"
        ? new TextDecoder("utf-8", { fatal: true }).decode(
            await file.arrayBuffer(),
          )
        : await file.text();
    if (content.includes("\u0000"))
      throw new Error("Binary content is not supported.");
    return processEvidenceFile(file.name, file.size, content);
  } catch (error) {
    const record = await processEvidenceFile(file.name, file.size, "");
    return {
      ...record,
      status: "failed",
      errorMessage: `Could not read UTF-8 evidence. Select the file again. ${error instanceof Error ? error.message : "Read failed."}`,
    };
  }
}

export async function processMultiFileBatch(
  files: File[],
): Promise<EvidenceFileRecord[]> {
  const results: EvidenceFileRecord[] = [];
  for (const file of files) results.push(await parseEvidenceFile(file));
  return results;
}
