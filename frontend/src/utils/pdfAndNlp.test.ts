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

    // Regional scripts
    expect(detectTextLanguage("আমার টাকা এখনও পাইনি").language).toBe("Bengali");
    expect(detectTextLanguage("பணம் இன்னும் வரவில்லை").language).toBe("Tamil");
    expect(detectTextLanguage("నా డబ్బులు ఇంకా రాలేదు").language).toBe("Telugu");
    expect(detectTextLanguage("ನನ್ನ ಹಣ ಇನ್ನೂ ಬಂದಿಲ್ಲ").language).toBe("Kannada");

    // Regional Romanized
    expect(detectTextLanguage("Taka ferot paini").language).toBe("Bengali");
    expect(detectTextLanguage("Panam kidaikkavillai").language).toBe("Tamil");
    expect(detectTextLanguage("Dabbulu raledu ayindi").language).toBe("Telugu");
    expect(detectTextLanguage("Paise parat aale nahit").language).toBe("Marathi");
  });

  it("extracts amounts from words, numbers, and currency formats", () => {
    const text = "I was debited INR 3,200 and also 500 rupaye for order in Bengaluru.";
    const amounts = extractAmountsFromText(text);
    expect(amounts.map((a) => a.normalizedInr)).toContain("3200.00");
    expect(amounts.map((a) => a.normalizedInr)).toContain("500.00");

    const wordText = "Customer paid do hazaar rupees.";
    const wordAmounts = extractAmountsFromText(wordText);
    expect(wordAmounts.map((a) => a.normalizedInr)).toContain("2000.00");

    const multiText = "Paid paanch sau and 10k rs.";
    const multiAmounts = extractAmountsFromText(multiText);
    expect(multiAmounts.map((a) => a.normalizedInr)).toContain("500.00");
    expect(multiAmounts.map((a) => a.normalizedInr)).toContain("10000.00");
  });

  it("identifies Indian places and commercial hubs", () => {
    const text = "Dispute registered by merchant in Bengaluru and delivery hub in Mumbai.";
    const places = extractPlaces(text);
    expect(places).toContain("Bengaluru");
    expect(places).toContain("Mumbai");

    const text2 = "Shipment from Hyderabad to Chennai and warehouse in Pune.";
    const places2 = extractPlaces(text2);
    expect(places2).toContain("Hyderabad");
    expect(places2).toContain("Chennai");
    expect(places2).toContain("Pune");
  });

  it("identifies financial rails, banks, and transaction references", () => {
    const text =
      "Payment made via Razorpay using HDFC Bank, UPI ref 492019284719, pay_89a0bcdef123 to merchant@okhdfcbank.";
    const entities = extractFinancialEntities(text);
    expect(entities).toContain("Razorpay");
    expect(entities).toContain("HDFC Bank");
    expect(entities).toContain("UPI");

    const refs = extractTransactionReferences(text);
    expect(refs).toContain("UTR: 492019284719");
    expect(refs).toContain("pay_89a0bcdef123");
    expect(refs).toContain("merchant@okhdfcbank");
  });

  it("classifies dispute intent across distinct categories", () => {
    expect(classifyDisputeIntent("Mera refund nahi mila abhi tak.").intent).toBe(
      "REFUND_NOT_RECEIVED",
    );
    expect(classifyDisputeIntent("Amount kat gaye do baar.").intent).toBe("DOUBLE_DEBIT");
    expect(
      classifyDisputeIntent("Your INR 2,500 refund was processed on 28 August.").intent,
    ).toBe("REFUND_CLAIMED_PROCESSED");
    expect(
      classifyDisputeIntent("Returned the product and parcel delivered but no refund.").intent,
    ).toBe("RETURN_DELIVERED_NO_REFUND");
    expect(
      classifyDisputeIntent("Fraudulent charge, unapproved transaction, not authorized.").intent,
    ).toBe("UNAUTHORIZED_TRANSACTION");
  });

  it("handles empty strings and adversarial inputs safely", () => {
    const empty = analyzeMultilingualDisputeText("");
    expect(empty.language).toBe("English");
    expect(empty.claimedAmounts).toEqual([]);

    const huge = analyzeMultilingualDisputeText("refund ".repeat(500));
    expect(huge.intent).toBe("GENERAL_INQUIRY");

    const mixed = analyzeMultilingualDisputeText("💸 ₹500 का रिफंड wapas karo in Mumbai user@oksbi 🎉");
    expect(["Hindi (Devanagari)", "Hinglish (Romanized Hindi)"]).toContain(mixed.language);
    expect(mixed.places).toContain("Mumbai");
    expect(mixed.transactionReferences).toContain("user@oksbi");
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

  it("extracts all batch statements from multi-statement communications", () => {
    const multiCommunication = [
      "Your INR 2500 refund was processed on 28 August",
      "Aapka INR 3200 refund kal process ho gaya tha",
      "कृपया मेरा 500 रुपये का रिफंड वापस करो",
      "Debit of 4999 rupaye duplicate charged",
    ].join("\n\n");

    const nlp = analyzeMultilingualDisputeText(multiCommunication);
    expect(nlp.claimedAmounts.length).toBeGreaterThanOrEqual(4);
    expect(nlp.batchStatements.length).toBe(4);

    const amounts = nlp.claimedAmounts.map((a) => a.normalizedInr);
    expect(amounts).toContain("2500.00");
    expect(amounts).toContain("3200.00");
    expect(amounts).toContain("500.00");
    expect(amounts).toContain("4999.00");

    expect(nlp.batchStatements[0].quote).toContain("2500");
    expect(nlp.batchStatements[1].quote).toContain("3200");
    expect(nlp.batchStatements[2].quote).toContain("500");
    expect(nlp.batchStatements[3].quote).toContain("4999");
    expect(nlp.batchStatements[3].intent).toBe("DOUBLE_DEBIT");
  });
});
