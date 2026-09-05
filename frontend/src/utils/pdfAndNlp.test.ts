import { describe, expect, it } from "vitest";
import { generateAuditPdf } from "./pdfGenerator";
import {
  analyzeMultilingualDisputeText,
  detectTextLanguage,
  extractAmountsFromText,
  extractPlaces,
  extractFinancialEntities,
  extractTransactionReferences,
  classifyDisputeIntent,
} from "./nlpEngine";
import type { SandboxEvaluateResponse } from "../api";

describe("pdfGenerator", () => {
  it("generates a valid, standards-compliant PDF 1.4 binary document", () => {
    const mockResult: SandboxEvaluateResponse = {
      run_id: "sandbox_test12345678",
      request_sha256: "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
      raw_reason_code: "sample_normal",
      profile_id: "refund_not_processed_v1",
      status: "PASS",
      semantic_status: "SUCCESS",
      claims: [],
      findings: [],
      ledger: {
        payment_id: "pay_1234567890ab",
        payment_amount_minor: 250000,
        currency: "INR",
        refund_ledger_complete: true,
        refund_status: "processed",
        refund_amount_minor: 250000,
      },
      proof: {
        status: "SAT",
        constraints: [],
        certificate: {
          solver: "DETERMINISTIC_COMPILER",
          invariant_id: "INV_REFUND_MATCH",
          proof_sha256: "a".repeat(64),
          evidence_refs: ["claim:1"],
          minimal_relative_to_compiled_constraints: true,
        },
        model_override_allowed: false,
      },
      comparison: {
        semantic_output: "GROUNDED_RELATION",
        deterministic_output: "PASS",
        relationship: "DIVISION_OF_AUTHORITY",
        uncertainty_basis: "VERIFICATION_COMPLETENESS",
        probability_exposed: false,
      },
      boundary: {
        runtime: "LOCAL_OFFLINE",
        ephemeral: true,
        synthetic_input: true,
        external_api_calls: false,
        razorpay_write_performed: false,
        persisted: false,
        holdout_accessed: false,
        extractor_id: "regex-baseline-v1",
        gate_authority: "DETERMINISTIC_POLICY",
      },
      disclaimer: "Decision support only — not a dispute outcome prediction or legal verdict.",
    };

    const bytes = generateAuditPdf(mockResult);
    expect(bytes).toBeInstanceOf(Uint8Array);
    expect(bytes.length).toBeGreaterThan(500);

    const pdfString = String.fromCharCode(...bytes.subarray(0, 10));
    expect(pdfString).toContain("%PDF-1.4");

    const tailString = String.fromCharCode(...bytes.subarray(bytes.length - 20));
    expect(tailString).toContain("%%EOF");
  });
});

describe("nlpEngine", () => {
  it("detects Hinglish and Hindi accurately", () => {
    const hinglish = "Aapka INR 3,200 refund kal process ho gaya tha, reference RF-HI-01.";
    expect(detectTextLanguage(hinglish).language).toBe("Hinglish (Romanized Hindi)");

    const hindiDevanagari = "कृपया मेरा 500 रुपये का रिफंड वापस करो";
    expect(detectTextLanguage(hindiDevanagari).language).toBe("Hindi (Devanagari)");

    const english = "Your refund of INR 4,999 has been processed successfully.";
    expect(detectTextLanguage(english).language).toBe("English");
  });

  it("extracts amounts from words, numbers, and currency formats", () => {
    const text = "I was debited INR 3,200 and also 500 rupaye for order in Bengaluru.";
    const amounts = extractAmountsFromText(text);
    expect(amounts.map((a) => a.normalizedInr)).toContain("3200.00");
    expect(amounts.map((a) => a.normalizedInr)).toContain("500.00");

    const wordText = "Customer paid do hazaar rupees.";
    const wordAmounts = extractAmountsFromText(wordText);
    expect(wordAmounts.map((a) => a.normalizedInr)).toContain("2000.00");
  });

  it("identifies Indian places and commercial hubs", () => {
    const text = "Dispute registered by merchant in Bengaluru and delivery hub in Mumbai.";
    const places = extractPlaces(text);
    expect(places).toContain("Bengaluru");
    expect(places).toContain("Mumbai");
  });

  it("identifies financial rails, banks, and transaction references", () => {
    const text = "Payment made via Razorpay using HDFC Bank, UPI ref 492019284719, pay_89a0bcdef123.";
    const entities = extractFinancialEntities(text);
    expect(entities).toContain("Razorpay");
    expect(entities).toContain("HDFC Bank");
    expect(entities).toContain("UPI");

    const refs = extractTransactionReferences(text);
    expect(refs).toContain("UTR: 492019284719");
    expect(refs).toContain("pay_89a0bcdef123");
  });

  it("classifies dispute intent across distinct categories", () => {
    expect(classifyDisputeIntent("Mera refund nahi mila abhi tak.").intent).toBe(
      "REFUND_NOT_RECEIVED",
    );
    expect(classifyDisputeIntent("Amount kat gaye do baar.").intent).toBe("DOUBLE_DEBIT");
    expect(
      classifyDisputeIntent("Your INR 2,500 refund was processed on 28 August.").intent,
    ).toBe("REFUND_CLAIMED_PROCESSED");
  });

  it("produces a comprehensive entity intelligence packet", () => {
    const text =
      "Aapka INR 3,200 refund kal process ho gaya tha in Bengaluru via Razorpay, reference RF-HI-01.";
    const nlp = analyzeMultilingualDisputeText(text);
    expect(nlp.language).toBe("Hinglish (Romanized Hindi)");
    expect(nlp.claimedAmounts[0].normalizedInr).toBe("3200.00");
    expect(nlp.places).toContain("Bengaluru");
    expect(nlp.banksAndRails).toContain("Razorpay");
    expect(nlp.transactionReferences).toContain("RF-HI-01");
  });
});
