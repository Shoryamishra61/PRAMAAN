# 25 — Research Corrections & Reconciliation Log

This file records material corrections made while consolidating the supplied reports.

## C-001 Razorpay dispute webhook
**Old:** `dispute.opened`  
**Correct:** `payment.dispute.created` for creation; Razorpay documents additional `payment.dispute.*` lifecycle events.  
Source: SRC-RZP-02.

## C-002 Visa reason-code conflation
**Old:** Visa 13.6 = Credit Not Processed (Canceled Merchandise/Services).  
**Correct:** Visa 13.6 = Credit Not Processed; Visa 13.7 = Cancelled Merchandise/Services.  
Source: SRC-RZP-06, SRC-VISA-01.

## C-003 Evidence “mandatory” language
**Old:** email + policy universally mandatory for Visa 13.6.  
**Correct:** Razorpay page lists suggested evidence including refund proof/timestamp/return/policy/reversal records. Missing suggested evidence defaults REVIEW.  
Source: SRC-RZP-06.

## C-004 Auto-contest contradiction
**Old:** PASS auto-submits/auto-contests while same docs claim no auto action.  
**Correct:** MVP has no Razorpay write action. PASS only unlocks a local “ready” workflow state.

## C-005 Accept/contest method
**Old:** `POST /v1/disputes/{id}/contest`.  
**Correct:** Razorpay documents `PATCH /v1/disputes/:id/contest`; accept is POST.  
Source: SRC-RZP-04/05.

## C-006 HMAC/replay
**Old:** HMAC prevents replay.  
**Correct:** HMAC authenticates payload; dedupe uses `x-razorpay-event-id`.  
Source: SRC-RZP-03.

## C-007 Webhook latency
**Old:** must ACK in <15ms.  
**Correct:** Razorpay requires 2xx within 5 seconds. Measure actual p95; do not invent 15ms.  
Source: SRC-RZP-03.

## C-008 Event ID questioned, then verified
Earlier review suspected `X-Razorpay-Event-Id` might be invented. Current Razorpay docs explicitly document `x-razorpay-event-id` as unique per event.  
Source: SRC-RZP-03.

## C-009 FastAPI BackgroundTasks durability
**Old:** acknowledged work safely handled by in-memory background tasks.  
**Correct:** use durable DB job record before ACK; worker resumes pending/stale jobs.

## C-010 SQLite claims
**Old:** “thread-safe high-throughput production backend.”  
**Correct:** local hackathon storage with WAL/short transactions; no enterprise throughput claim.

## C-011 LLM confidence
**Old:** model returns confidence κ; threshold 0.80/0.85.  
**Correct:** no model self-confidence drives policy. Verification incompleteness routes REVIEW.

## C-012 Temperature/calibration
**Old:** temperature=0 = temperature scaling/calibration.  
**Correct:** unrelated. Guo et al. temperature scaling is a post-hoc classifier calibration method.  
Source: SRC-ML-01.

## C-013 Platt/Brier claims
**Old:** show Platt-scaled margin/Brier score without a validated probability model.  
**Correct:** removed unless future classifier actually produces calibrated probabilities.

## C-014 Two probabilistic stages
**Old:** LLM extraction + LLM NLI mandatory.  
**Correct:** one AI extraction stage + deterministic cross-source verifier. NLI optional ablation.

## C-015 Character offsets
**Old:** LLM must generate exact offsets.  
**Correct:** model returns exact quote; deterministic backend locates offsets.

## C-016 Shipping-after-cancellation
**Old:** hard Visa 13.6 contradiction/legal unwinnability.  
**Correct:** removed from core 13.6 profile; that framing conflated 13.7 and contextual business rules.

## C-017 Legal language
**Old:** “legally invalid,” “unwinnable,” “immediate fraud/bad-faith proof.”  
**Correct:** local integrity finding only; issuer/network outcome outside scope.

## C-018 Evidence hashes
**Old:** SHA-256 proves provenance/authenticity.  
**Correct:** proves byte identity/change relative to stored digest.

## C-019 Immutable SQLite
**Old:** immutable audit ledger.  
**Correct:** optional tamper-evident hash chain with threat-model caveat.

## C-020 PII regex
**Old:** regex fully redacts names/PII and guarantees compliance.  
**Correct:** synthetic data in MVP; deterministic patterns are partial minimization only; no compliance claim.

## C-021 Prompt injection
**Old:** XML delimiters make injection inert.  
**Correct:** no foolproof prompt defense; contain impact via no tools/secrets/actions, schema/grounding, deterministic policy.  
Source: SRC-OWASP-01.

## C-022 Prompt-injection result
**Old:** suspicious instruction text automatically BLOCK.  
**Correct:** if it causes unreliable extraction → REVIEW; content itself is not evidence conflict.

## C-023 50-character cognitive forcing
**Old:** override requires 50 characters + gibberish regex.  
**Correct:** inspect both sources + structured reason + optional note.

## C-024 Auto-submit PASS queue
**Old:** silent auto-contest of clean cases.  
**Correct:** no network write. Local readiness only.

## C-025 Fabricated metrics
Removed all unverified:
- 0.89 F1;
- 0.81 baseline;
- 0.74 raw prompt;
- Brier 0.04;
- ₹70,100 savings;
- 100% injection interception;
- exact latency figures;
- Cohen κ 0.88;
- 30% human-factor improvement.

They may reappear only after actual measurement.

## C-026 Benchmark statistical claim
**Old:** 120 total/30 holdout “statistically strong” via binomial accuracy formula.  
**Correct:** no population-generalization claim. Recommend 60-case family-separated holdout and report counts/uncertainty.

## C-027 Chronological synthetic “OOD”
**Old:** later synthetic dates = OOD.  
**Correct:** use unseen scenario-family split.

## C-028 Generator truth is error-free
**Old:** programmatic labels guarantee error-free truth.  
**Correct:** generator can be wrong; manually inspect scenario families before freeze.

## C-029 Competitor absence
**Old:** competitors definitively lack contradiction checking.  
**Correct:** public docs reviewed do not expose standalone gate as primary workflow; private/internal capability unknown.

## C-030 Product scope
**Old:** broad cancellation/shipping/refund contradiction engine.  
**Correct:** refund/credit-not-processed integrity verifier focused on processed/promised refund evidence and ledger state.

## C-031 PDF/OCR
**Old:** ingest PDFs/scans in core path.  
**Correct:** v1 text/JSON evidence; PDF/OCR deferred.

## C-032 Auth/RBAC
**Old:** simultaneously “no auth” and “audited JWT/RBAC.”  
**Correct:** local demo identity; production auth explicitly out of scope.

## C-033 Fake “what broke”
**Old:** prewritten bugs presented as genuine build failures.  
**Correct:** only actual bugs or clearly labeled fault injections can appear in final narrative.

## C-034 Cost model
**Old:** universal transaction+network fee equations with invented values.  
**Correct:** parameterized sensitivity analysis unless real merchant cost inputs are supplied.

## C-035 Deadline
**Old:** Sep 5 treated as official-page verified.  
**Correct:** operational Sep 5 from contemporaneous secondary sources; official landing text verified did not expose it.

## C-036 Cross-track contamination
One final uploaded paste was titled **Hybrid Recovery Orchestrator (Track 03)** and contained UPI retry/NPCI recovery logic. It is not part of the selected Track 02 Dispute Integrity Gate product and is intentionally excluded from implementation requirements. Reusing its retry caps, Z9/ZA codes, SHAP recovery UI, or revenue-recovery state machine would create track drift.
