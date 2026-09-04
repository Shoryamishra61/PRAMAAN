# 00 — Source of Truth

**Status:** Canonical. Any conflicting project document must be changed to match this file unless a newer primary source requires an explicit revision.

## Product identity

**Name:** Dispute Integrity Gate  
**Competition:** Razorpay AI Buildathon 2026  
**Track:** 02 — AI Risk Manager  
**Loss class:** Refund / Credit Not Processed disputes  
**MVP profile:** `refund_not_processed_v1`

## Product thesis

Merchants can assemble dispute evidence that is individually plausible yet mutually inconsistent. Razorpay already supports dispute evidence fields, contest/accept workflows, and an `action_required` event when submitted evidence is insufficient, unreadable, or mismatched. The product adds a **merchant-side pre-submission verification checkpoint** before a human decides whether a packet is ready to contest.

The verifier:
1. preserves Razorpay dispute/payment state;
2. checks trusted structured values deterministically;
3. uses AI only to convert messy customer communication into typed, grounded claims;
4. verifies those grounded claims against structured refund/payment state with code;
5. routes cases to PASS, REVIEW, or BLOCK;
6. exposes exact evidence behind every material finding.

## Why this is Track 02 compliant

Official Track 02 asks for a **working detector, verifier, or auto-responder for one class of loss**, measured with **precision and recall on a held-out set**, with **honest false-positive cost**, and requires defense-only behavior. [SRC-RZP-01]

This product is a verifier, is narrow to one dispute loss family, has a benchmarkable output, and intentionally contains no offensive capability.

## Supported semantic claim types

The default AI extractor may emit only the allowlisted claim types required by the reason profile:

- `refund_requested`
- `refund_promised`
- `refund_approved`
- `refund_claimed_processed`
- `refund_denied`
- `refund_amount`
- `refund_timing_commitment`
- `return_claimed`
- `return_not_received_claim`
- `policy_condition_reference`

The schema may evolve only through an ADR + benchmark version bump.

## Trusted vs untrusted evidence

### Trusted structured inputs
For the synthetic MVP, these are fixture-controlled merchant/system records:
- Razorpay-like dispute/payment event fields;
- payment capture amount/currency;
- structured refund ledger records;
- evidence inventory metadata.

These are “trusted” only within the demo threat model; production integrations require provenance/authentication.

### Untrusted semantic inputs
- customer support text;
- email/chat text;
- merchant policy prose;
- free-form notes.

Model outputs derived from these are always untrusted until schema and grounding checks pass.

## Gate status semantics

### PASS
All **supported** deterministic checks succeeded, required-to-evaluate structured state exists, semantic claims used by the reason profile are grounded, and no material conflict supported by current rules was found.

PASS **does not mean**:
- the issuer will accept the representment;
- the dispute is legally valid;
- the evidence is complete for every network;
- the merchant should automatically contest.

UI wording: **“Gate clear — no supported integrity issue detected.”**

### REVIEW
Manual review is required because at least one of:
- evidence recommended by the profile is absent;
- source text cannot be parsed/grounded safely;
- model provider is unavailable;
- structured source is incomplete/stale;
- the case is outside supported scope;
- two untrusted sources disagree without a trusted resolver;
- a business/policy interpretation cannot be made deterministically.

REVIEW is the universal fail-safe for uncertainty.

### BLOCK
A **local safety hold** is applied only when a material inconsistency is deterministically established using:
- trusted structured state; and
- either another trusted field or an AI-extracted claim whose exact source quotation was grounded and validated.

Examples:
- communication says a refund was processed for ₹X, but complete refund ledger has no corresponding refund;
- communication says full refund ₹X was approved/processed, trusted ledger shows only ₹Y and the relevant refund is final;
- refund record references a different payment/currency than the dispute case.

BLOCK does **not** mean “unwinnable,” “fraud,” “illegal,” or “must accept dispute.”

## Action boundary

MVP has **zero automatic or direct Razorpay write actions**.

The UI may expose:
- `Mark ready for contest` — local workflow state only;
- `Request evidence repair`;
- `Override local hold` — local workflow state only;
- `Return to review`.

No production/test API call to Razorpay `accept` or `contest` is part of the MVP. Their documented existence may be shown in architecture context only. [SRC-RZP-04, SRC-RZP-05]

## Evidence guidance

Razorpay publicly lists **suggested documents** for Visa 13.6 and RZP04. Suggested evidence must not be mislabeled as universally mandatory. Missing suggested evidence routes to REVIEW unless a documented profile rule is explicitly verified. [SRC-RZP-06]

For the MVP, the recommended evidence set is:
- refund processing/confirmation evidence;
- refund amount/timestamp/transaction state;
- customer communication around the refund;
- refund policy/context when relevant.

## AI architecture

Default architecture uses **one probabilistic task**: structured claim extraction from unstructured text.

Required:
- strict structured output;
- exact source quote;
- document ID;
- typed values;
- no tool calls;
- no secrets;
- no database access;
- no final decision field accepted from model.

Local code resolves quote → exact character span and rejects/REVIEWs ungrounded output.

A separate NLI model/LLM stage is **not required**. It may be evaluated later as an ablation and retained only if it materially improves a predeclared evaluation target.

## Uncertainty

Do not use:
- LLM self-reported confidence;
- temperature=0 as “calibration”;
- fixed 0.80/0.85 thresholds without validated probabilistic scores.

Default abstention is rule-based on **verification completeness**, not pseudo-probability:
- schema valid?
- quote exactly groundable?
- all trusted resolver state present?
- supported claim type?
- supported language/type?
- semantic provider healthy?

## Benchmark truth

MVP benchmark is synthetic and must be labeled as such.

Recommended v1:
- 180 total synthetic cases;
- 120 development cases from development scenario families;
- 60 frozen holdout cases from **unseen scenario families**, not merely later dates;
- balanced classes are permitted for diagnostic evaluation but must not be represented as production prevalence.

No result exists until executable evaluation produces it.

Primary Track 02 metrics:
- material-conflict precision;
- material-conflict recall;
- F1;
- false-PASS count/rate;
- false-BLOCK count/rate;
- REVIEW rate / automated coverage.

Claim extraction metrics:
- claim-type precision/recall/F1;
- exact grounding rate.

No Brier score unless a validated probabilistic classifier is actually added.

## Frontend truth

Core screens:
1. analyst queue;
2. case workspace;
3. evidence/source viewer;
4. finding/contradiction panel;
5. local override/review dialog;
6. evaluation dashboard.

A BLOCK override must not be a “type 50 characters” ritual. The operator must:
1. open/acknowledge both relevant evidence sources;
2. select a structured override reason;
3. optionally add concise free text;
4. create an audit event.

## Backend truth

Default:
- FastAPI;
- SQLite WAL;
- durable `jobs` table;
- worker loop that resumes persisted pending jobs;
- raw-body Razorpay webhook HMAC;
- `x-razorpay-event-id` for deduplication;
- 2xx response after durable consume, within Razorpay's 5-second window. [SRC-RZP-02, SRC-RZP-03]

Do not rely solely on FastAPI `BackgroundTasks` for acknowledged work that must survive restart.

## Security truth

- Evidence text is untrusted.
- LLM output is untrusted.
- Prompt delimiters are only one mitigation; least privilege and deterministic authorization are the primary control. [SRC-OWASP-01]
- Hashing proves file identity relative to stored digest, not source authenticity.
- Hash-chained audit logs are tamper-evident under a limited threat model, not immutable.
- Demo data is synthetic; do not claim PCI/GDPR/DPDP compliance.

## Success definition

The submission is successful if judges can verify:
1. a real Razorpay-aligned dispute workflow;
2. a narrow, non-generic verifier;
3. meaningful AI used only where language requires it;
4. deterministic financial safety and evidence traceability;
5. held-out precision/recall with transparent synthetic limitations;
6. visible safe failure behavior;
7. a reproducible repo;
8. a memorable, evidence-backed two-minute product demonstration.

## Non-goals

- chargeback win prediction;
- generic fraud detection;
- evidence generation;
- persuasive letter generation;
- autonomous dispute submission;
- OCR/scanned-document parsing;
- broad card-network coverage;
- customer-facing chatbot;
- RAG/vector search;
- agentic browsing;
- production compliance certification.
