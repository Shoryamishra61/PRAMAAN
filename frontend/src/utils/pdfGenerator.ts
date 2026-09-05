import type { SandboxEvaluateResponse } from "../api";

export type SandboxClaim = SandboxEvaluateResponse["claims"][number];

/**
 * Pure TypeScript PDF-1.4 Document Generator
 * Emits compliant, binary PDF documents for Dispute Audit Certificates and Case Evidence Packs.
 * Zero external native C++ or heavyweight library dependencies; runs ephemerally in any browser.
 */

function getBusinessSafeDecision(status: "PASS" | "REVIEW" | "BLOCK"): string {
  switch (status) {
    case "PASS":
      return "Safe to defend without financial loss";
    case "REVIEW":
      return "Hold for manual evidence review";
    case "BLOCK":
      return "Do not submit dispute - refund already processed or contradicted";
    default:
      return "Hold for manual review";
  }
}

function escapePdfText(text: string): string {
  return text
    .replace(/\\/g, "\\\\")
    .replace(/\(/g, "\\(")
    .replace(/\)/g, "\\)")
    .replace(/[^\x20-\x7E]/g, "?");
}

export interface PdfCertificateOptions {
  includeProofDetails?: boolean;
  operatorNotes?: string;
}

export function generateAuditPdf(
  result: SandboxEvaluateResponse,
  primaryClaim?: SandboxClaim | null,
  options: PdfCertificateOptions = {},
): Uint8Array {
  const safeDecision = getBusinessSafeDecision(result.status);
  const now = new Date().toISOString();
  const runShort = result.run_id.slice(-8);

  // Content stream instructions (in points: 72 points = 1 inch, A4 = 595.28 x 841.89)
  const lines: string[] = [];

  // Helper functions for drawing
  const setStrokeColor = (r: number, g: number, b: number) =>
    lines.push(`${(r / 255).toFixed(3)} ${(g / 255).toFixed(3)} ${(b / 255).toFixed(3)} RG`);
  const setFillColor = (r: number, g: number, b: number) =>
    lines.push(`${(r / 255).toFixed(3)} ${(g / 255).toFixed(3)} ${(b / 255).toFixed(3)} rg`);
  const drawRect = (x: number, y: number, w: number, h: number, fill = false, stroke = true) => {
    lines.push(`${x.toFixed(2)} ${y.toFixed(2)} ${w.toFixed(2)} ${h.toFixed(2)} re`);
    if (fill && stroke) lines.push("B");
    else if (fill) lines.push("f");
    else if (stroke) lines.push("S");
  };
  const drawLine = (x1: number, y1: number, x2: number, y2: number) => {
    lines.push(`${x1.toFixed(2)} ${y1.toFixed(2)} m ${x2.toFixed(2)} ${y2.toFixed(2)} l S`);
  };
  const text = (font: string, size: number, x: number, y: number, content: string) => {
    lines.push("BT");
    lines.push(`/${font} ${size} Tf`);
    lines.push(`${x.toFixed(2)} ${y.toFixed(2)} Td`);
    lines.push(`(${escapePdfText(content)}) Tj`);
    lines.push("ET");
  };

  // Background Canvas Border
  setStrokeColor(226, 232, 240); // #e2e8f0
  lines.push("1 w");
  drawRect(36, 36, 523.28, 769.89, false, true);

  // Top Brand Header Banner
  setFillColor(15, 23, 42); // #0f172a (Slate 900)
  drawRect(36, 735, 523.28, 70.89, true, false);

  setFillColor(255, 255, 255);
  text("F2", 18, 54, 775, "PRAMAAN  |  DISPUTE INTEGRITY GATE");
  setFillColor(148, 163, 184);
  text("F1", 9, 54, 755, "OFFLINE VERIFICATION RECEIPT  *  TRACK 02 AI RISK MANAGER");
  text("F1", 9, 410, 755, `RUN: ${result.run_id}`);

  // Verdict Callout Box
  let badgeR = 59, badgeG = 130, badgeB = 246; // PASS (Blue)
  if (result.status === "BLOCK") {
    badgeR = 239; badgeG = 68; badgeB = 68; // Red
  } else if (result.status === "REVIEW") {
    badgeR = 245; badgeG = 158; badgeB = 11; // Amber
  }

  // Verdict Banner Background
  setFillColor(badgeR, badgeG, badgeB);
  drawRect(54, 665, 487.28, 52, true, false);

  setFillColor(255, 255, 255);
  text("F2", 15, 68, 695, `GATE DECISION: ${result.status}`);
  text("F1", 10, 68, 678, `Business Action: ${safeDecision}`);
  text("F1", 9, 390, 678, `Profile: ${result.profile_id}`);

  // Summary Metadata Table
  let curY = 640;
  setFillColor(248, 250, 252);
  drawRect(54, curY - 50, 487.28, 50, true, false);
  setStrokeColor(203, 213, 225);
  drawLine(54, curY - 50, 541.28, curY - 50);

  setFillColor(71, 85, 105);
  text("F2", 9, 68, curY - 18, "EVALUATION TIMESTAMP");
  text("F1", 9, 68, curY - 36, now);

  text("F2", 9, 230, curY - 18, "CRYPTOGRAPHIC DIGEST (SHA-256)");
  text("F3", 8, 230, curY - 36, `${result.request_sha256.slice(0, 32)}...`);

  text("F2", 9, 430, curY - 18, "AUTHORITY MODEL");
  text("F1", 9, 430, curY - 36, result.boundary.gate_authority);

  curY -= 75;

  // SECTION 1: Evidence Grounding
  setFillColor(15, 23, 42);
  text("F2", 12, 54, curY, "1. SEMANTIC CLAIM GROUNDING");
  setStrokeColor(15, 23, 42);
  drawLine(54, curY - 4, 541.28, curY - 4);

  curY -= 20;
  setFillColor(248, 250, 252);
  drawRect(54, curY - 60, 487.28, 60, true, true);

  setFillColor(71, 85, 105);
  const batchCount = result.claims?.length || (primaryClaim ? 1 : 0);
  const headerText =
    batchCount > 1
      ? `EXTRACTED SOURCE QUOTE (Primary of ${batchCount} Grounded Claims):`
      : "EXTRACTED SOURCE QUOTE:";
  text("F2", 9, 66, curY - 16, headerText);
  setFillColor(15, 23, 42);
  const quote = primaryClaim?.source_quote || "No claim grounded (Extractor abstained).";
  const truncatedQuote = quote.length > 80 ? `${quote.slice(0, 77)}...` : quote;
  text("F3", 9, 66, curY - 32, `"${truncatedQuote}"`);

  setFillColor(71, 85, 105);
  const claimAmtStr = primaryClaim?.amount_minor
    ? `INR ${(primaryClaim.amount_minor / 100).toFixed(2)}`
    : "None";
  const batchSummary = batchCount > 1 ? `  |  Batch Grounded: ${batchCount} Claims` : "";
  text("F1", 9, 66, curY - 48, `Claim Amount: ${claimAmtStr}${batchSummary}  |  Grounding: ${primaryClaim?.grounding_status || "ABSTAINED"}`);

  curY -= 85;

  // SECTION 2: Authoritative Ledger State
  setFillColor(15, 23, 42);
  text("F2", 12, 54, curY, "2. AUTHORITATIVE PAYMENT LEDGER");
  setStrokeColor(15, 23, 42);
  drawLine(54, curY - 4, 541.28, curY - 4);

  curY -= 20;
  setFillColor(248, 250, 252);
  drawRect(54, curY - 65, 487.28, 65, true, true);

  setFillColor(71, 85, 105);
  text("F2", 9, 66, curY - 18, "PAYMENT RECORD ID");
  text("F3", 9, 66, curY - 34, result.ledger.payment_id);

  text("F2", 9, 210, curY - 18, "LEDGER STATUS");
  setFillColor(15, 23, 42);
  text("F2", 9, 210, curY - 34, result.ledger.refund_status.toUpperCase());

  setFillColor(71, 85, 105);
  text("F2", 9, 340, curY - 18, "RECORDED REFUND");
  setFillColor(15, 23, 42);
  const ledgerAmt = result.ledger.refund_amount_minor
    ? `INR ${(result.ledger.refund_amount_minor / 100).toFixed(2)}`
    : "None";
  text("F2", 9, 340, curY - 34, ledgerAmt);

  setFillColor(71, 85, 105);
  text("F2", 9, 450, curY - 18, "COMPLETENESS");
  text("F1", 9, 450, curY - 34, result.ledger.refund_ledger_complete ? "Complete" : "INCOMPLETE");

  setFillColor(100, 116, 139);
  text("F1", 8, 66, curY - 52, "* Ledger truth takes strict precedence over unstructured communication.");

  curY -= 90;

  // SECTION 3: Deterministic Proof & Invariants
  setFillColor(15, 23, 42);
  text("F2", 12, 54, curY, "3. DETERMINISTIC PROOF & CONTRADICTION CERTIFICATE");
  setStrokeColor(15, 23, 42);
  drawLine(54, curY - 4, 541.28, curY - 4);

  curY -= 20;
  setFillColor(248, 250, 252);
  drawRect(54, curY - 70, 487.28, 70, true, true);

  setFillColor(71, 85, 105);
  text("F2", 9, 66, curY - 18, "SOLVER STATUS:");
  setFillColor(15, 23, 42);
  text("F2", 9, 160, curY - 18, result.proof.status);

  setFillColor(71, 85, 105);
  text("F2", 9, 240, curY - 18, "INVARIANT ENGINE:");
  setFillColor(15, 23, 42);
  text("F1", 9, 350, curY - 18, result.proof.certificate?.solver || "DETERMINISTIC_COMPILER");

  setFillColor(71, 85, 105);
  text("F2", 9, 66, curY - 36, "PROOF SHA-256:");
  setFillColor(15, 23, 42);
  text("F3", 8, 160, curY - 36, result.proof.certificate?.proof_sha256 || "N/A (Satisfiable or Incomplete)");

  setFillColor(71, 85, 105);
  const firstFinding = result.findings[0]?.code || "NONE";
  text("F1", 8, 66, curY - 54, `Primary Finding: ${firstFinding}  *  Model override permitted: false`);

  curY -= 95;

  // SECTION 4: Architecture Boundary & Audit Non-Repudiation
  setFillColor(15, 23, 42);
  text("F2", 12, 54, curY, "4. SAFETY GUARANTEES & DEFENSE BOUNDARY");
  setStrokeColor(15, 23, 42);
  drawLine(54, curY - 4, 541.28, curY - 4);

  curY -= 18;
  setFillColor(71, 85, 105);
  text("F1", 8, 54, curY, "* Local Offline Execution: No external model or third-party payment APIs accessed.");
  text("F1", 8, 54, curY - 13, "* Defense-Only Guarantee: Strictly verification support; zero external payment write authority.");
  text("F1", 8, 54, curY - 26, "* Non-repudiation: All evidence tokens and verdicts are cryptographically bound to the SHA-256 digest.");
  if (options.operatorNotes) {
    text("F2", 8, 54, curY - 39, `* Operator Note: ${options.operatorNotes.slice(0, 80)}`);
  }

  // Bottom Footer
  setFillColor(241, 245, 249);
  drawRect(36, 36, 523.28, 30, true, false);
  setFillColor(100, 116, 139);
  text("F1", 8, 54, 48, `PRAMAAN AI Risk Manager (Track 02)  *  Certificate ID: PRM-${runShort}  *  Defense-Only Safety Engine`);
  text("F1", 8, 430, 48, `Page 1 of 1  *  Valid PDF`);

  const streamContent = lines.join("\n");
  const streamLength = streamContent.length;

  // Assemble PDF Objects
  const objects: string[] = [];

  // 1: Catalog
  objects.push("1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj");

  // 2: Pages
  objects.push("2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj");

  // 3: Page
  objects.push(
    "3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595.28 841.89] /Contents 4 0 R /Resources << /Font << /F1 5 0 R /F2 6 0 R /F3 7 0 R >> >> >>\nendobj",
  );

  // 4: Contents
  objects.push(`4 0 obj\n<< /Length ${streamLength} >>\nstream\n${streamContent}\nendstream\nendobj`);

  // 5: F1 (Helvetica)
  objects.push("5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj");

  // 6: F2 (Helvetica-Bold)
  objects.push("6 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>\nendobj");

  // 7: F3 (Courier)
  objects.push("7 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>\nendobj");

  // 8: Info
  objects.push(
    `8 0 obj\n<< /Title (PRAMAAN Dispute Integrity Audit Certificate) /Author (PRAMAAN AI Risk Manager) /Creator (PRAMAAN CARVE-FECL) /CreationDate (D:${now.replace(/[-:T]/g, "").slice(0, 14)}Z) >>\nendobj`,
  );

  // Compute byte offsets for xref
  let pdfOutput = "%PDF-1.4\n%\xE2\xE3\xCF\xD3\n";
  const offsets: number[] = [0];

  for (let i = 0; i < objects.length; i++) {
    offsets.push(pdfOutput.length);
    pdfOutput += objects[i] + "\n";
  }

  const xrefOffset = pdfOutput.length;
  pdfOutput += `xref\n0 ${objects.length + 1}\n0000000000 65535 f \n`;

  for (let i = 1; i <= objects.length; i++) {
    const offsetStr = offsets[i].toString().padStart(10, "0");
    pdfOutput += `${offsetStr} 00000 n \n`;
  }

  pdfOutput += `trailer\n<< /Size ${objects.length + 1} /Root 1 0 R /Info 8 0 R >>\nstartxref\n${xrefOffset}\n%%EOF\n`;

  // Encode string as binary bytes
  const bytes = new Uint8Array(pdfOutput.length);
  for (let i = 0; i < pdfOutput.length; i++) {
    bytes[i] = pdfOutput.charCodeAt(i) & 0xff;
  }

  return bytes;
}

export function downloadAuditPdf(
  result: SandboxEvaluateResponse,
  primaryClaim?: SandboxClaim | null,
  filename?: string,
): void {
  const bytes = generateAuditPdf(result, primaryClaim);
  const blob = new Blob([bytes.buffer as ArrayBuffer], { type: "application/pdf" });
  const url = URL.createObjectURL(blob);
  const resolvedName = filename || `pramaan-certificate-${result.run_id.slice(-8)}.pdf`;

  const link = document.createElement("a");
  link.href = url;
  link.download = resolvedName;
  link.style.display = "none";
  document.body.appendChild(link);
  link.click();
  setTimeout(() => {
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  }, 200);
}
