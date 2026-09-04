# 27 — Final Research Audit

## Final verdict
**GO — Track 02 / Dispute Integrity Gate**, with the corrected MVP defined in `00-SOURCE-OF-TRUTH.md`.

This is not a claim that the product will win. It is the highest-confidence specification produced from the supplied reports after removing unsupported facts, cross-track contamination, fabricated metrics, and unnecessary architecture.

## Verified external facts that shape the build

### Razorpay Buildathon
Verified from current Razorpay page:
- Track 02 is AI Risk Manager;
- detector/verifier/auto-responder for one loss class;
- measured precision and recall on a held-out set;
- honest false-positive cost;
- defense-only;
- repo + 5-minute video + architecture are part of the work-sample signal.

### Razorpay dispute integration
Verified from current Razorpay docs:
- use `payment.dispute.created` rather than legacy `dispute.opened`;
- webhooks are at-least-once and can arrive out of order;
- `x-razorpay-event-id` can deduplicate deliveries;
- signature validation uses raw request body with HMAC-SHA256;
- successful consumption must return 2xx within the documented webhook window;
- Razorpay exposes dispute fetch/accept/contest APIs; contest is PATCH, accept is POST;
- `payment.dispute.action_required` exists for evidence issues such as insufficient/unreadable/mismatched evidence.

### Reason-code scope
Verified:
- Visa 13.6 = **Credit Not Processed**;
- Visa 13.7 = **Cancelled Merchandise/Services**;
- Razorpay also documents **RZP04 — Refund not Processed**;
- Razorpay's merchant guide lists suggested evidence around refund generation/state, amount, customer communication, policy/context, and reversal/credit records.

Therefore the MVP is a refund/credit evidence-integrity verifier, not a generic cancellation/shipping contradiction engine.

## Strong inferences, not facts
- A standalone, independently positioned pre-submission integrity gate appears differentiated from the public positioning of major dispute-automation products reviewed. We do **not** claim competitors lack internal consistency checks.
- Grounded semantic extraction is likely useful because customer communication is unstructured. This remains an empirical hypothesis until the benchmark beats a strong regex/deterministic baseline.
- Evidence-directed friction at BLOCK override may reduce blind overreliance, but our exact UI requires formative testing; literature does not validate our specific interaction automatically.

## Unverified and deliberately excluded
- real-world prevalence of contradictory packets;
- chargeback win-rate uplift;
- production ROI or rupee savings;
- any pre-existing F1/Brier/calibration number;
- a universal false-block tolerance;
- a universal network fee cost;
- “production-grade,” PCI/GDPR/DPDP compliance, or enterprise throughput;
- fabricated user-study or inter-rater agreement results.

## Architecture outcome
The final MVP is deliberately:
- one bounded AI extraction stage;
- deterministic grounding/resolution/policy;
- no direct Razorpay writes;
- durable SQLite job state;
- canonical text/JSON evidence;
- optional NLI only if ablation proves value;
- synthetic family-separated benchmark with frozen holdout;
- generated evaluation artifacts as the only source of metrics.

## Win condition
The submission has strong hiring signal only if the implementation proves:
1. the repo runs cleanly;
2. the main BLOCK case is visually obvious and technically grounded;
3. failure states visibly become REVIEW rather than fake certainty;
4. held-out results are genuinely computed and limitations disclosed;
5. the README/video make the AI/non-AI boundary obvious;
6. the “what broke” story is real;
7. every claim survives a senior-engineer panel challenge.

If the semantic AI stage does not create measurable lift over the strong baseline, remove it rather than protecting sunk cost.
