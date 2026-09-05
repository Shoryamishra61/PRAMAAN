import { describe, expect, it } from "vitest";
import {
  analyzeCrossFileEvidence,
  parseEvidenceFile,
  processMultiFileBatch,
  parseMoneyMinorUnits,
} from "./crossFileIntelligence";

describe("crossFileIntelligence", () => {
  it("successfully parses valid JSON evidence", async () => {
    const jsonContent = JSON.stringify({
      raw_reason_code: "RZP04",
      customer_communication: "Your INR 2,500 refund was processed.",
      payment_amount_inr: "2500.00",
      refund_amount_inr: "2500.00",
      refund_status: "processed",
      refund_ledger_complete: true,
    });
    const file = new File([jsonContent], "case_evidence.json", {
      type: "application/json",
    });

    const parsed = await parseEvidenceFile(file);
    expect(parsed.status).toBe("complete");
    expect(parsed.type).toBe("json");
    expect(parsed.facts.claimedAmounts).toContain("2500");
    expect(parsed.facts.refundStatuses).toContain("processed");
    expect(parsed.facts.communicationSnippet).toBe(
      "Your INR 2,500 refund was processed.",
    );
  });

  it("successfully parses CSV ledger evidence", async () => {
    const csvContent = `transaction_id,amount,currency,status,created_at
txn_101,499.00,INR,failed,2026-08-25T10:00:00Z`;
    const file = new File([csvContent], "ledger_export.csv", {
      type: "text/csv",
    });

    const parsed = await parseEvidenceFile(file);
    expect(parsed.status).toBe("warning");
    expect(parsed.type).toBe("csv");
    expect(parsed.facts.ledgerAmounts).toContain("499.00");
    expect(parsed.facts.refundStatuses).toContain("failed");
  });

  it("successfully parses TXT customer communication", async () => {
    const textContent =
      "Hello support, I was told on WhatsApp that my refund of INR 3,000 was processed yesterday.";
    const file = new File([textContent], "whatsapp_chat.txt", {
      type: "text/plain",
    });

    const parsed = await parseEvidenceFile(file);
    expect(parsed.status).toBe("complete");
    expect(parsed.type).toBe("txt");
    expect(parsed.facts.claimedAmounts).toContain("3000");
    expect(parsed.facts.communicationSnippet).toContain(
      "refund of INR 3,000 was processed",
    );
  });

  it("rejects unsupported file formats gracefully without throwing", async () => {
    const file = new File(["dummy pdf content"], "statement.pdf", {
      type: "application/pdf",
    });

    const parsed = await parseEvidenceFile(file);
    expect(parsed.status).toBe("failed");
    expect(parsed.errorMessage).toContain("Unsupported file format");
  });

  it("rejects oversized files exceeding 256 KB limit", async () => {
    const hugeContent = "A".repeat(300 * 1024);
    const file = new File([hugeContent], "huge_log.txt", {
      type: "text/plain",
    });

    const parsed = await parseEvidenceFile(file);
    expect(parsed.status).toBe("failed");
    expect(parsed.errorMessage).toContain("256 KB safety limit");
  });

  it("isolates errors so 1 malformed file does not destroy a batch", async () => {
    const validFile = new File(
      [JSON.stringify({ customer_communication: "Valid message" })],
      "valid.json",
      { type: "application/json" },
    );
    const corruptFile = new File(["{not valid json"], "corrupt.json", {
      type: "application/json",
    });

    const results = await processMultiFileBatch([validFile, corruptFile]);
    expect(results).toHaveLength(2);
    expect(results[0].status).toBe("complete");
    expect(results[1].status).toBe("failed");
    expect(results[1].errorMessage).toContain("Malformed JSON");
  });

  it("never promotes communication amounts or CSV fields to financial authority", async () => {
    const files = await processMultiFileBatch([
      new File(["Refund processed for INR 90071992547409.93"], "claim.txt"),
      new File(["amount,status\n499,processed"], "ledger.csv"),
    ]);
    const analysis = analyzeCrossFileEvidence(files);
    expect(analysis.structuredRequest).toBeUndefined();
    expect(analysis.anomalies).toEqual([]);
    expect(analysis.corroborations).toEqual([]);
    expect(parseMoneyMinorUnits("90,071,992,547,409.93")).toBe(
      9007199254740993n,
    );
    expect(parseMoneyMinorUnits("1.001")).toBeNull();
  });

  it("retains same-name evidence and exact source offsets without truncation", async () => {
    const body = "  source text\n".repeat(900);
    const files = await processMultiFileBatch([
      new File([body], "claim.txt"),
      new File(["second source"], "claim.txt"),
    ]);
    const analysis = analyzeCrossFileEvidence(files);
    expect(analysis.totalFiles).toBe(2);
    expect(analysis.errors[0]).toContain("no text was truncated");
    for (const [index, source] of analysis.sources.entries()) {
      expect(
        analysis.combinedCommunication.slice(source.start, source.end),
      ).toBe(files[index].rawContent);
    }
    expect(analysis.anomalies[0].type).toBe("DUPLICATE_EVIDENCE");
  });

  it("isolates disk read failures and does not read oversized files", async () => {
    const broken = new File(["x"], "broken.txt");
    Object.defineProperty(broken, "arrayBuffer", {
      value: () => Promise.reject(new Error("Access denied")),
    });
    const oversized = new File(["x"], "huge.txt");
    Object.defineProperty(oversized, "size", { value: 300_000 });
    Object.defineProperty(oversized, "arrayBuffer", {
      value: () => {
        throw new Error("Must not read");
      },
    });
    const results = await processMultiFileBatch([
      broken,
      oversized,
      new File(["valid"], "ok.txt"),
    ]);
    expect(results.map((r) => r.status)).toEqual([
      "failed",
      "failed",
      "complete",
    ]);
    expect(results[0].errorMessage).toContain("Access denied");
    expect(results[1].errorMessage).toContain("256 KB");
  });

  it("parses quoted CSV fields and rejects silent column loss", async () => {
    const valid = await parseEvidenceFile(
      new File(
        ['amount,note\r\n"1,000.00","line one\nline ""two"""'],
        "ledger.csv",
      ),
    );
    expect(valid.status).toBe("warning");
    expect(valid.facts.ledgerAmounts).toEqual(["1,000.00"]);
    for (const content of [
      "amount,status\n1,processed,extra",
      "amount,amount\n1,2",
      'amount,note\n1,"unclosed',
    ]) {
      expect(
        (await parseEvidenceFile(new File([content], "bad.csv"))).status,
      ).toBe("failed");
    }
  });

  it("rejects ambiguous financial JSON rather than dropping invalid fields", async () => {
    for (const value of [
      [],
      { customer_communication: "refund", refund_amount_inr: 100 },
      { request: [] },
    ]) {
      expect(
        (await parseEvidenceFile(new File([JSON.stringify(value)], "bad.json")))
          .status,
      ).toBe("failed");
    }
  });
});
