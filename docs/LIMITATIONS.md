# Research Limitations & Operational Boundaries: CARVE-FECL

**Standard:** Section 101 & Section 103 of Principal Research Directive  
**Date:** 2026-09-03  
**Status:** Canonical / Unvarnished Research Accounting  

---

## 1. Synthetic-to-Real Distribution Gap

- **Simulation Nature:** Due to legal and regulatory constraints protecting cardholder payment data (Gramm-Leach-Bliley Act, PCI-DSS, RBI Digital Payment Directions), the FECL-Bench evaluation dataset (`DIG-RNP-SYN-V1`) was synthesized using a structural causal lifecycle model.
- **Consequence:** While the causal lifecycle accurately reproduces state transitions (Auth $\to$ Capture $\to$ Fulfillment $\to$ Refund $\to$ Dispute), it does not fully replicate the full variety of scanned merchant PDF receipts, handwritten notes, or non-standard ledger database exports encountered across diverse SMB merchants.

---

## 2. Extraction Scope & Phrasing Boundaries

- **Supported Evidence Relations:** The current production extractor is formally verified for refund-not-processed dispute categories (`RZP04_refund_not_processed`, Visa 13.6/13.7 family).
- **Known Failure Slice (Partial vs Full Refund):** On the held-out test split, colloquial statements that fail to distinguish whether a partial or full refund was promised achieved 0/10 automated contradiction recall. The gate correctly abstained to `REVIEW` (0 false `BLOCK` errors), but could not resolve the claim autonomously.
- **Multilingual Support:** Hinglish and Indian-English regional idioms are covered via regex anchor variants, but low-resource non-Latin scripts (e.g., Devanagari, Tamil, Bengali) require external OCR normalization before entering the evidence graph.

---

## 3. Strict Defense-Only Operational Boundary

- **No Gateway Mutation:** CARVE-FECL contains **zero network mutation endpoints**. It cannot submit disputes to Razorpay or card networks, issue ledger refunds, or alter merchant database states.
- **Decision Support Exclusively:** The output actions (`PASS`, `REVIEW`, `BLOCK`) represent pre-submission recommendations backed by signed proof certificates. A human analyst or configured merchant policy engine retains final operational authority over actual payment disputes.

---

## 4. Formal Invariant Assumptions

- **Ledger Completeness:** The formal Z3 solver can prove an invariant contradiction (`UNSAT`) only when the provided authoritative ledger snapshot is certified complete (`refund_ledger_complete = true`). When the ledger is incomplete, absence of a refund record cannot mathematically prove non-refund, forcing an abstention to `REVIEW`.
- **Monetary Normalization:** All amounts must be normalized into minor integer units (paise/cents) before solver evaluation. Rounding errors or floating-point decimals in raw evidence are rejected at the input schema boundary.
