# 17 — Reliability & Testing Strategy

## Safety invariant
**Degraded uncertainty must never silently become PASS.**

## Test layers

### 1. Unit
- money parser/minor units;
- timestamp normalization;
- quote grounding;
- reason-profile rules;
- decision precedence;
- canonical audit serialization.

### 2. Property-based
Examples:
- refund totals never become negative through arithmetic;
- direct comparison never occurs across mismatched currencies;
- BLOCK cannot be emitted from ungrounded semantic claim;
- model failure never yields PASS;
- duplicate event ID cannot create two logical jobs.

### 3. Schema/contract
- Razorpay-compatible event parse;
- unknown extra fields tolerated;
- required local fields validated;
- semantic extractor output strict schema.

### 4. Webhook integration
- valid raw body/signature;
- signature mismatch after byte mutation;
- missing event ID;
- duplicate delivery;
- 2xx after durable persistence;
- measured response under 5 seconds.

Important: whitespace is not “malicious.” The correct test is that the signature is calculated over the **exact transmitted bytes**.

### 5. Worker recovery
- kill worker after job persisted;
- restart;
- stale job reclaimed exactly once logically;
- no duplicate decision side effects.

### 6. Semantic boundary
- model schema failure → REVIEW;
- quote not found → REVIEW;
- quote repeated ambiguously → REVIEW;
- negation hard negative;
- prompt injection text;
- provider timeout;
- offline replay parity.

### 7. Golden end-to-end
- PASS case;
- REVIEW case;
- BLOCK case;
- BLOCK structured override;
- reprocess after repaired evidence.

### 8. Benchmark regression
DEV only during iteration:
- ensure prediction artifact schema stable;
- watch per-slice regressions;
- no accidental holdout load.

### 9. Holdout integrity
Test:
- manifest hash;
- case hashes;
- no dev command includes holdout path;
- final runner requires explicit `--split holdout --confirm-frozen`.

### 10. Frontend
- queue selection;
- claim-to-source focus;
- REVIEW reason display;
- BLOCK local hold;
- override source-inspection precondition;
- modal focus;
- keyboard behavior;
- no network-write copy.

### 11. Accessibility
Automated:
- axe or equivalent;
- semantic landmarks;
- labels.

Manual:
- keyboard-only golden path;
- visible focus;
- screen reader spot check;
- zoom/responsive check;
- state without color.

Automated tests alone do not prove WCAG compliance.

### 12. Security
See `16-SECURITY-THREAT-MODEL.md`.

## Failure injection matrix

| Fault | Expected behavior |
|---|---|
| Model timeout | REVIEW + provider failure reason |
| Malformed model output | REVIEW |
| Ungrounded quote | REVIEW |
| Ledger missing | REVIEW |
| Unsupported language | REVIEW |
| Duplicate webhook | one logical case/job, 2xx |
| Invalid HMAC | reject ingest |
| Worker crash | job resumes |
| Audit row modified | chain verifier fails, if feature enabled |
| Evaluation artifact missing | UI says NOT YET MEASURED |

## Performance
Measure, don't invent.

Required measured values before submission:
- webhook p50/p95 response locally;
- deterministic verifier p50/p95;
- semantic extraction latency/provider;
- end-to-end case processing for demo fixture.

Only requirement imposed by Razorpay webhook is successful 2xx within 5 seconds after consume. [SRC-RZP-03]

## Genuine “what broke” journal
Create `FAILURE-NARRATIVE.md` during implementation.

Entry format:
- symptom;
- reproduction;
- root cause;
- fix;
- regression test;
- residual risk;
- commit/test reference.

Do **not** pre-fill fictional bugs. Intentional fault-injection findings may be described as fault-injection results, not accidental bugs.

## Definition of test-complete
Every MUST requirement:
- has at least one acceptance test;
- critical failure path tested;
- traceability row present;
- all relevant tests pass from fresh clone.
