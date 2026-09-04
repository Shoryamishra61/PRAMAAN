# HUMAN VALIDATION & EXTERNAL VALIDITY GOVERNANCE REPORT

**Standard**: Frontier Research Scientific Rigor (Sections 6 & 7)  
**Repository**: `RAZOR/dispute-integrity-gate-spec`  
**Classification**: Audit of Real-Data Claims, Auxiliary Benchmarks, and Blind Human Challenge Protocol  

---

## 1. External Validity Hierarchy

A central requirement of our research integrity mandate is that **synthetic scale cannot substitute for real merchant chargeback ground truth**. We define and enforce the following 7-tier external validity hierarchy across the repository:

```
[Tier 1: Synthetic In-Distribution (FECL-SCM-V2 G0-G2)] 
     ↓
[Tier 2: Synthetic Template Holdout (G3 Syntactic Shift)]
     ↓
[Tier 3: Synthetic Mechanism Holdout (Unseen Financial Rules)]
     ↓
[Tier 4: Independent Generator Holdout (G4 Formal Lexicon)]
     ↓
[Tier 5: Real Public Financial Language (CFPB / SEC Filings - Auxiliary Only)]
     ↓
[Tier 6: Human-Authored Blind Cases (Double-Annotated Challenge Set)]
     ↓
[Tier 7: Real Merchant Production Shadow Traffic (Live Gateway Logs)]
```

### Critical Negative Clarifications
1. **CFPB Complaints Are NOT Chargeback Ground Truth**:
   The Consumer Financial Protection Bureau (CFPB) dataset contains real consumer complaints against financial institutions, but it does NOT contain merchant dispute arbitration outcomes or payment gateway ledger reconciliation. In CARVE-FECL, CFPB is classified strictly as **Tier 5 auxiliary financial text**, not chargeback decisioning ground truth.
2. **CORD, SROIE, & DocVQA Are Document Benchmarks, NOT Risk Benchmarks**:
   High OCR extraction F1 on receipt datasets (CORD/SROIE) proves document intelligence capability, but does NOT validate whether a dispute is fraudulent or consistent.

---

## 2. Status of Real-World Merchant Data (Tier 7)

- **Current Status**: **NOT ACCESSIBLE / SIMULATION ONLY**
- **Justification**: Payment gateway dispute arbitration records contain sensitive Payment Card Industry Data Security Standard (PCI-DSS) protected card numbers, customer PII, and proprietary banking merchant identifiers. No live merchant shadow traffic has been ingested into this open-source repository.
- **Enforcement**: Any claim that CARVE-FECL has been *"tested on live merchant production traffic"* is strictly **BANNED** from all pitch presentations and documentation.

---

## 3. Human Blind Challenge Protocol (Tier 6)

To establish genuine external validity beyond synthetic simulation, we formulated the **FECL-Human-100 Blind Challenge Protocol**.

### 3.1 Design Principles
1. **Zero LLM Generation**: LLMs must NEVER be used to write "human" cases. Every case must be authored by a human with e-commerce or dispute experience.
2. **Double-Blind Annotation**: Neither the case author nor the model knows the benchmark identifier. Two independent annotators review every evidence packet.
3. **Target Sample Size**: Exactly **100 high-quality, verified cases** (50 genuine disputes, 50 fraudulent/contradictory claims) rather than hundreds of low-quality automated templates.

### 3.2 Human Case Schema & Composition
The 100 cases span realistic Indian and global merchant payment scenarios:

| Category | Count | Scenario Description | Key Ambiguity |
| :--- | :---: | :--- | :--- |
| **Credit Not Processed** | 25 | Customer claims refund promised on WhatsApp; merchant shows refund ARN generated. | Timing delay vs actual non-issuance. |
| **Goods Not Received** | 25 | Delivery partner marked "Delivered at Security Gate"; customer claims no OTP provided. | Third-party carrier handoff ambiguity. |
| **Duplicate Billing** | 15 | Double debits during UPI server timeout; bank automatically reversed second charge within 2 hours. | Temporal reconciliation latency. |
| **Authorization Error** | 15 | International card used via 3DS OTP bypass vs friction-less mandate. | Card network liability shift. |
| **Services Not as Described** | 20 | Software SaaS annual renewal dispute; customer logged in 3 times post-renewal. | Partial utility vs total breach. |

### 3.3 Inter-Annotator Agreement & Adjudication
- **Agreement Metric**: Cohen's Kappa $\kappa \ge 0.85$ required across the double-annotators.
- **Tie-Breaker**: In cases of annotator disagreement, a Senior Payment Risk Analyst acts as referee.
- **Ground Truth Storage**: Stored with SHA-256 integrity hash at `data/benchmark/human_100_manifest.json`.

---

## 4. Current Execution Status: Protocol Defined / Annotation Pending

> [!IMPORTANT]
> **Human-100 Study Status: PROTOCOL DESIGNED / ANNOTATION EXECUTION PENDING**  
> While the FECL-Human-100 protocol, double-blind schema, and adjudication guidelines are formally established, live multi-annotator collection and execution on real human cases remain **PENDING**. This constitutes the primary external-validity boundary of this submission.
>
> In accordance with our research integrity mandate, we do NOT report synthetic approximations as "human results", nor do we use LLMs to simulate human annotators. Full human execution is scheduled for pre-production merchant pilot onboarding.

### 4.1 Evaluation Protocol for Execution Phase
When evaluated on the 100 human cases upon annotation completion:
1. **Model Evaluation**: CARVE-FECL runs in offline inference mode (`DIG_INFERENCE_MODE=offline`).
2. **Disagreement Triage**: Human cases with high colloquial noise (e.g. Hinglish: *"bhai refund abhi tak nahi aaya bank me"*) are analyzed to verify whether the frozen MiniLM encoder maintains semantic retrieval or triggers OOD abstention.
3. **Safety Floor**: Formal SMT constraints continue to hold unconditionally: regardless of human text phrasing, if the merchant bank ledger proves refund settlement, the claim is mathematically blocked from false dispute payouts.
