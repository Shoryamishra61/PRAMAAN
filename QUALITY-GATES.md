# Quality Gates

A release candidate is valid only if every mandatory gate below is green.

Acceptance record: `artifacts/verification/RELEASE-GATES.md` and `artifacts/verification/MUST-COVERAGE.md`.

## QG-01 Source correctness
- [x] No code/doc references `dispute.opened` as a Razorpay event.
- [x] Ingestion supports documented `payment.dispute.created`.
- [x] HMAC validation uses raw request bytes.
- [x] Deduplication uses documented `x-razorpay-event-id`.
- [x] Successful webhook consumption returns 2xx within Razorpay's 5-second window.
- [x] No document describes Visa 13.6 as Cancelled Merchandise/Services.

## QG-02 Product boundary
- [x] No automatic Razorpay contest/accept/refund/payment write.
- [x] No letter generation or win-probability score.
- [x] PASS/REVIEW/BLOCK semantics exactly match source-of-truth.
- [x] Model outage cannot result in PASS.

## QG-03 Grounding
- [x] Every AI-derived claim used in a decision has document ID + exact source quote.
- [x] Backend deterministically resolves and validates the quote span.
- [x] Ambiguous/not-found quote routes case to REVIEW.
- [x] Structured ledger values never originate from model inference.

## QG-04 Evaluation integrity
- [x] Dataset version and manifest committed.
- [x] Holdout family split is frozen and checksum-verified.
- [x] Development scripts cannot load holdout by default.
- [x] Baselines and proposed system use the same case-level evaluation protocol.
- [x] Metrics UI reads saved result artifacts.
- [x] No hard-coded performance or financial savings numbers.
- [x] README labels benchmark as synthetic.

## QG-05 Security
- [x] Webhook missing/invalid signature rejected.
- [x] Secrets excluded from the package/logs; no Git-history claim is made because this workspace has no Git metadata.
- [x] SQL is parameterized.
- [x] Semantic extractor has no tools/secrets.
- [x] External/untrusted text is clearly segregated and output schema validated.
- [x] Uploads are disabled; the extractor contract allowlists only v1 text/JSON types.
- [x] Audit hash chain is not implemented; the conditional verification gate is not applicable.

## QG-06 Reliability
- [x] Durable job state survives process restart.
- [x] Duplicate webhook replay produces one logical job.
- [x] Model timeout/schema failure/grounding failure routes to REVIEW.
- [x] No generic error is misclassified as BLOCK.
- [x] Deterministic financial invariants have property tests.

## QG-07 UX/accessibility
- [x] All gate states use text/icon, not color alone.
- [x] Conflict evidence is keyboard reachable.
- [x] Override modal has initial focus, focus trap, Escape close, and trigger-focus restoration.
- [x] BLOCK override requires inspection acknowledgement + structured reason.
- [x] No artificial 50-character/gibberish rule.
- [x] No pseudo-precise AI confidence badge unless a validated classifier later exists.

## QG-08 Demo/repo
- [x] Isolated clean-source setup works; Git-clone provenance is unavailable in this non-Git workspace.
- [x] One command starts seeded local demo.
- [x] One command runs tests.
- [x] 2-minute golden demo works offline/reliably.
- [x] 5-minute pitch uses only measured claims.
- [x] Genuine failure narrative comes from encountered test/runtime defects and explicit fault injection, not fiction.
