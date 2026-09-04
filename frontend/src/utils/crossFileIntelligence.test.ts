import { describe, expect, it } from "vitest";
import {
  analyzeCrossFileEvidence,
  parseEvidenceFile,
  processMultiFileBatch,
  type EvidenceFileRecord,
} from "./crossFileIntelligence";

describe("crossFileIntelligence", () => {
  it("successfully parses valid JSON evidence", async () => {
    const jsonContent = JSON.stringify({
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
    expect(parsed.status).toBe("complete");
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

  it("detects cross-file amount contradictions between communication and ledger", () => {
    const files: EvidenceFileRecord[] = [
      {
        id: "f1",
        name: "chat.txt",
        size: 100,
        type: "txt",
        status: "complete",
        rawContent: "Refund claimed for ₹4,999.00",
        facts: {
          claimedAmounts: ["4999"],
          ledgerAmounts: [],
          transactionIds: [],
          refundStatuses: [],
          datesFound: [],
          sourceLineCount: 1,
          communicationSnippet: "Refund claimed for ₹4,999.00",
        },
        warnings: [],
        processedAt: new Date().toISOString(),
      },
      {
        id: "f2",
        name: "ledger.csv",
        size: 100,
        type: "csv",
        status: "complete",
        rawContent: "amount,status\n499.00,processed",
        facts: {
          claimedAmounts: [],
          ledgerAmounts: ["499"],
          transactionIds: [],
          refundStatuses: ["processed"],
          datesFound: [],
          sourceLineCount: 2,
        },
        warnings: [],
        processedAt: new Date().toISOString(),
      },
    ];

    const result = analyzeCrossFileEvidence(files);
    const amountAnomaly = result.anomalies.find(
      (a) => a.type === "AMOUNT_DISCREPANCY",
    );
    expect(amountAnomaly).toBeDefined();
    expect(amountAnomaly?.severity).toBe("high");
    expect(amountAnomaly?.description).toContain("claims ₹4,999");
    expect(amountAnomaly?.description).toContain("records ₹499");
  });

  it("detects cross-file status contradictions when communication claims processed but ledger shows failed", () => {
    const files: EvidenceFileRecord[] = [
      {
        id: "f1",
        name: "customer_claim.txt",
        size: 100,
        type: "txt",
        status: "complete",
        rawContent: "They promised refund processed yesterday.",
        facts: {
          claimedAmounts: ["1000"],
          ledgerAmounts: [],
          transactionIds: [],
          refundStatuses: [],
          datesFound: [],
          sourceLineCount: 1,
          communicationSnippet: "They promised refund processed yesterday.",
        },
        warnings: [],
        processedAt: new Date().toISOString(),
      },
      {
        id: "f2",
        name: "bank_ledger.csv",
        size: 100,
        type: "csv",
        status: "complete",
        rawContent: "amount,status\n1000,failed",
        facts: {
          claimedAmounts: [],
          ledgerAmounts: ["1000"],
          transactionIds: [],
          refundStatuses: ["failed"],
          datesFound: [],
          sourceLineCount: 2,
        },
        warnings: [],
        processedAt: new Date().toISOString(),
      },
    ];

    const result = analyzeCrossFileEvidence(files);
    const statusAnomaly = result.anomalies.find(
      (a) => a.type === "STATUS_CONFLICT",
    );
    expect(statusAnomaly).toBeDefined();
    expect(statusAnomaly?.severity).toBe("high");
    expect(statusAnomaly?.description).toContain("failed");
  });
});
