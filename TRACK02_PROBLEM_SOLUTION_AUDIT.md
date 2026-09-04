# TRACK 02 AUDIT: RAZORPAY AI BUILDATHON ALIGNMENT

**Auditor Role**: Principal AI/ML Research Scientist & Payment Risk Specialist  
**Standard**: Razorpay Track 02 Official Guidelines (AI Risk Manager)  
**Date**: September 2026  
**Repository**: `dispute-integrity-gate-spec`  

---

## 1. Problem Statement & Loss Class Definition

### Official Razorpay Track 02 Mandate
> **Stop the merchant losing money to fraud, returns and chargebacks.**  
> Build a working detector, verifier or auto-responder for **one class of loss**, with measured **precision and recall on a held-out test set**.

### CARVE-FECL Specific Loss Class
> **Merchant financial loss caused by submitting inconsistent, incomplete, contradictory, or ungrounded chargeback evidence during dispute contestation (representment), particularly in `CREDIT_NOT_PROCESSED` (CNP) disputes.**

### The Economic Failure Mechanism
When a merchant contests a cardholder dispute, submitting flawed evidence results in a double penalty:
1. **Direct Loss of Dispute Amount**: The acquiring bank / card network rules in favor of the cardholder, debiting the merchant.
2. **Network Dispute Administration Fee**: Razorpay and card networks (Visa/Mastercard) assess non-refundable dispute administration fees (typically ₹200–₹500 / $15–$25 per lost contest).
3. **Analyst Friction Overhead**: Spending 15–30 minutes of human review time compiling a representment package for a transaction where the merchant ledger already proves the customer was right, wasting operational salary.

CARVE-FECL serves as an **inbound evidence firewall / pre-submission verifier** that inspects evidence packages *before* contestation, guaranteeing that ungrounded claims never proceed to draft preparation.

---

## 2. The Buildathon Standard Evaluation

| Track 02 Requirement | Repository Implementation | Verification & File Proof | Status |
| :--- | :--- | :--- | :---: |
| **One Specific Loss Class** | Pre-submission verification of chargeback evidence consistency for refund / credit-not-processed disputes. | Defined in `backend/app/domain.py` and `contracts/gate-decision.schema.json`. | **COMPLIANT** |
| **Held-Out Test Set** | Frozen held-out partitions: `DIG-FECL-BENCH-v4.5` (480 cases) and `FECL-SCM-V2` (5,000 cases, Seed 9999). | Cryptographically sealed in `data/financial-evidence-integrity/v4.5/manifest.json`. | **COMPLIANT** |
| **Measured Precision & Recall** | Evaluated on frozen holdout: **82.54% Precision** [95% Wilson CI: 79.9%, 84.9%] and **78.44% Recall** [75.7%, 80.9%]. | Recorded in `FINAL_EMPIRICAL_MANIFEST.json` and `FINAL_RESULTS.md`. | **COMPLIANT** |
| **Explicit False-Positive Cost** | Modeled under asymmetric loss matrix: $\text{Cost} = 10.0 \times \text{False PASS} + 1.0 \times \text{False BLOCK} + 0.25 \times \text{REVIEW}$. | Evaluated in `evaluation/cost_analysis.py` and `LOSS_SENSITIVITY.md`. | **COMPLIANT** |
| **Strictly Defense-Only** | Pre-submission verification only. Zero payment gateway mutations, zero bank ledger debits, zero autonomous dispute filing. | Static AST verification in `scripts/check_no_razorpay_writes.py` and `backend/tests/test_no_razorpay_writes.py`. | **COMPLIANT** |
| **Explainable & Bounded** | Every hold produces an unsat core `ContradictionCertificate` citing exact character spans in customer text against ledger entries. | Implemented in `backend/app/carve.py:compile_financial_proof`. | **COMPLIANT** |
| **Audit Trail & Provenance** | Every request, state change, and operator inspection is logged in SQLite `review_events` and immutable `ingest_events`. | Schema in `backend/app/database.py` and tested in `backend/tests/test_database.py`. | **COMPLIANT** |
| **Fail-Closed on Failure** | Any unhandled exception, model timeout, or solver timeout transitions immediately to `REVIEW` (human queue). | Enforced in `backend/app/semantic_pipeline.py` and `backend/app/carve.py:apply_hard_precedence`. | **COMPLIANT** |

---

## 3. Defense-Only Boundary Verification

The master directive mandates that any offense-capable system (e.g., auto-charging cards, manipulating merchant balances, automated dispute generation without evidence) is disqualified.

We conducted an automated AST analysis across all 138 Python files and frontend TypeScript source files:

```python
# From scripts/check_no_razorpay_writes.py
FORBIDDEN_CALLS = [
    "razorpay.Client",
    "client.payment.capture",
    "client.refund.create",
    "client.dispute.contest",
    "requests.post('https://api.razorpay.com",
    "fetch('https://api.razorpay.com"
]
```

### Static AST Check Result
```
PRD requirements traced: 28
External source IDs referenced: 19 / defined: 57
JSON contracts: valid
No Razorpay write client, host, endpoint pattern, or non-local frontend fetch found.
```

The system is strictly an **internal decision-support verifier** for merchant operations teams. It outputs `GateDecision`:
- `PASS -> CONTEST_READY` (Safe to generate representment package)
- `REVIEW -> REVIEW_REQUIRED` (Human analyst inspection needed)
- `BLOCK -> INSUFFICIENT_OR_CONTRADICTORY_EVIDENCE` (Hold representment; evidence contradicts ledger)

---

## 4. Operational & Economic Modeling for Razorpay Merchants

In `evaluation/merchant_economics.py`, the system is modeled on an annual merchant dispute volume of 10,000 cases (mean dispute ticket: ₹5,000):

*Economic Model Scope Note*: This projection models expected financial impact under baseline operational assumptions (₹150 analyst review cost, ₹50 evidence acquisition fee) prior to live merchant shadow deployment.

1. **Baseline Rules Annual Loss**: ₹21,500,000.00
2. **CARVE-FECL Decision Loss**: ₹17,500,000.00
3. **Gross Merchant Edge**: **₹4,000,000.00**
4. **Operational Frictions Deducted**:
   - Analyst Review Overhead (3,300 reviews @ ₹150): ₹495,000.00
   - Evidence Acquisition Cost (1,320 queries @ ₹50): ₹66,000.00
   - Cloud Compute Overhead (10,000 cases @ ₹0.50): ₹5,000.00
5. **Net Merchant Edge**: **₹3,434,000.00 (15.97% net annual margin savings)**
6. **Return on Operational Investment (ROOI)**: **6.07x**

### Track 02 Solution Summary
CARVE-FECL addresses the concrete operational failure mode targeted by Razorpay Track 02: merchant financial loss from ungrounded dispute submissions. It enforces deterministic SMT invariants, accounts explicitly for analyst review friction, and operates strictly within a defense-only boundary.

