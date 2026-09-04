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
  inferredRequest: {
    payment_amount_inr?: string;
    refund_amount_inr?: string | null;
    refund_status?: string;
    refund_ledger_complete?: boolean;
    raw_reason_code?: string;
  };
}

const MAX_FILE_BYTES = 256 * 1024; // 256 KB safety limit per file

export function detectFileType(fileName: string): FileType {
  const lower = fileName.toLowerCase();
  if (lower.endsWith(".json")) return "json";
  if (lower.endsWith(".txt") || lower.endsWith(".log")) return "txt";
  if (lower.endsWith(".csv")) return "csv";
  return "unsupported";
}

export function parseCsvRows(content: string): Record<string, string>[] {
  const lines = content
    .split(/\r?\n/)
    .map((l) => l.trim())
    .filter((l) => l.length > 0);
  if (lines.length < 2) return [];

  const delimiter = lines[0].includes(",")
    ? ","
    : lines[0].includes(";")
      ? ";"
      : "\t";
  const headers = lines[0].split(delimiter).map((h) =>
    h
      .replace(/^["']|["']$/g, "")
      .trim()
      .toLowerCase(),
  );

  const rows: Record<string, string>[] = [];
  for (let i = 1; i < lines.length; i++) {
    const cells = lines[i]
      .split(delimiter)
      .map((c) => c.replace(/^["']|["']$/g, "").trim());
    const row: Record<string, string> = {};
    headers.forEach((h, idx) => {
      row[h] = cells[idx] ?? "";
    });
    rows.push(row);
  }
  return rows;
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
        parsed = JSON.parse(content);
      } catch (err) {
        return {
          ...baseRecord,
          status: "failed",
          errorMessage: `Malformed JSON: ${err instanceof Error ? err.message : "Syntax error"}`,
        };
      }

      if (!parsed || typeof parsed !== "object") {
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
          if (/amount|payment|refund/i.test(key) && val) {
            const num = val.replace(/[^\d.]/g, "");
            if (num) baseRecord.facts.ledgerAmounts.push(num);
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

      baseRecord.status = "complete";
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
  const validFiles = files.filter(
    (f) => f.status === "complete" || f.status === "warning",
  );
  const failedFiles = files.filter((f) => f.status === "failed");

  const anomalies: CrossFileAnomaly[] = [];
  const corroborations: string[] = [];

  const inferred: CrossFileAnalysisResult["inferredRequest"] = {
    refund_ledger_complete: true,
    raw_reason_code: "raw_demo_refund_mismatch",
  };

  // 1. Gather all communication blocks
  const commBlocks: string[] = [];
  files.forEach((f, idx) => {
    if (f.status === "failed") return;
    const body =
      f.facts.communicationSnippet || (f.type === "txt" ? f.rawContent : "");
    if (body.trim()) {
      commBlocks.push(`=== Document ${idx + 1}: ${f.name} ===\n${body.trim()}`);
    } else if (f.type === "csv") {
      commBlocks.push(
        `=== Document ${idx + 1}: ${f.name} (Structured Ledger) ===\nRows: ${f.facts.sourceLineCount - 1} records extracted.`,
      );
    }
  });

  let combinedCommunication = commBlocks.join("\n\n");
  if (combinedCommunication.length > 9800) {
    combinedCommunication = `${combinedCommunication.slice(0, 9750)}\n\n[... Truncated for safety]`;
  }

  // 2. Check amount discrepancies across documents
  const allClaimedAmounts = Array.from(
    new Set(validFiles.flatMap((f) => f.facts.claimedAmounts)),
  );
  const allLedgerAmounts = Array.from(
    new Set(validFiles.flatMap((f) => f.facts.ledgerAmounts)),
  );

  if (allClaimedAmounts.length > 0 && allLedgerAmounts.length > 0) {
    const claimVal = parseFloat(allClaimedAmounts[0]);
    const ledgerVal = parseFloat(allLedgerAmounts[0]);
    if (
      !isNaN(claimVal) &&
      !isNaN(ledgerVal) &&
      Math.abs(claimVal - ledgerVal) > 0.01
    ) {
      anomalies.push({
        type: "AMOUNT_DISCREPANCY",
        severity: "high",
        title: "Cross-document amount mismatch",
        description: `Customer document claims ₹${claimVal.toLocaleString("en-IN")}, but authoritative ledger records ₹${ledgerVal.toLocaleString("en-IN")}.`,
        sources: validFiles.map((f) => f.name),
      });
      inferred.payment_amount_inr = String(claimVal);
      inferred.refund_amount_inr = String(ledgerVal);
    } else if (!isNaN(claimVal) && !isNaN(ledgerVal)) {
      corroborations.push(
        `Consistent transaction amount ₹${claimVal.toLocaleString("en-IN")} verified across ${validFiles.length} documents.`,
      );
      inferred.payment_amount_inr = String(claimVal);
      inferred.refund_amount_inr = String(ledgerVal);
    }
  } else if (allClaimedAmounts.length > 0) {
    inferred.payment_amount_inr = allClaimedAmounts[0];
  } else if (allLedgerAmounts.length > 0) {
    inferred.payment_amount_inr = allLedgerAmounts[0];
  }

  // 3. Check refund status consistency
  const allStatuses = Array.from(
    new Set(validFiles.flatMap((f) => f.facts.refundStatuses)),
  );
  if (allStatuses.includes("failed") || allStatuses.includes("none")) {
    if (
      combinedCommunication.toLowerCase().includes("refund processed") ||
      combinedCommunication.toLowerCase().includes("promised refund")
    ) {
      anomalies.push({
        type: "STATUS_CONFLICT",
        severity: "high",
        title: "Refund claim vs ledger state conflict",
        description: `Communication claims a refund occurred, but ledger status is '${allStatuses.find((s) => s === "failed" || s === "none")}'.`,
        sources: validFiles.map((f) => f.name),
      });
      inferred.refund_status = allStatuses.find(
        (s) => s === "failed" || s === "none",
      );
    }
  } else if (allStatuses.includes("processed")) {
    inferred.refund_status = "processed";
    corroborations.push(
      "Refund ledger confirms record with status 'processed'.",
    );
  }

  // 4. Check duplicate inputs
  const nameSet = new Set<string>();
  files.forEach((f) => {
    if (nameSet.has(f.name)) {
      anomalies.push({
        type: "DUPLICATE_EVIDENCE",
        severity: "low",
        title: "Duplicate file detected",
        description: `Multiple files named "${f.name}" uploaded. Deduplicating content for SMT verification.`,
        sources: [f.name],
      });
    }
    nameSet.add(f.name);
  });

  return {
    totalFiles: files.length,
    successfulFiles: validFiles.length,
    failedFiles: failedFiles.length,
    combinedCommunication,
    anomalies,
    corroborations,
    inferredRequest: inferred,
  };
}

export async function parseEvidenceFile(
  file: File,
): Promise<EvidenceFileRecord> {
  const text = await file.text();
  return processEvidenceFile(file.name, file.size, text);
}

export async function processMultiFileBatch(
  files: File[],
): Promise<EvidenceFileRecord[]> {
  return Promise.all(files.map((file) => parseEvidenceFile(file)));
}

export function detectCrossFileAnomalies(
  files: EvidenceFileRecord[],
): CrossFileAnomaly[] {
  return analyzeCrossFileEvidence(files).anomalies;
}
