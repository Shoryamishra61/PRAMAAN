# Evidence Debugger Research Source

Audience: Razorpay Buildathon judges and product reviewers  
Date: 2026-09-01  
Scope: `refund_not_processed_v1`, defense-only merchant evidence integrity

## Direct answer

The strongest defensible product is not another dispute dashboard or autonomous responder. It is an
interactive evidence debugger: extract a narrow refund claim from merchant communication, ground it
to the exact quote, reconcile it against the authoritative refund ledger with deterministic code,
surface the contradiction, and let a human repair the evidence while the decision diff updates.

This directly satisfies the track's requirement for a working detector/verifier with held-out
precision and recall while preserving a strict defense-only boundary. It also matches Razorpay's
merchant evidence context for RZP04 / refund-not-processed disputes, where proof generation, amount
matching, and customer communication are relevant evidence.

## Evidence shaping the build

| Source | What it supports | Product consequence |
|---|---|---|
| https://razorpay.com/buildathon/ | Track 02 requires a working detector/verifier/auto-responder, held-out precision/recall, honest false-positive cost, and defense-only scope. | Keep one measurable verifier; show false passes and false blocks; prohibit offensive capability. |
| https://razorpay.com/docs/payments/disputes/submit-evidence/ | RZP04 is refund not processed; merchant-facing evidence includes refund proof, amount-matching bank evidence, and customer communication. | Center the judge loop on communication claims versus refund-ledger truth. |
| https://razorpay.com/docs/webhooks/disputes/ | Dispute lifecycle events include created and action-required states. | Preserve real ingestion architecture, but do not make it the judge's first screen. |
| https://razorpay.com/docs/webhooks/best-practices/ | Webhooks can be duplicated/out of order and require timely durable handling. | Retain HMAC/idempotent ingestion outside the ephemeral debugger. |
| https://docs.stripe.com/disputes/smart-disputes/auto-respond | Public competitor positioning emphasizes evidence auto-response/submission. | Differentiate on pre-submission integrity debugging without claiming competitors lack private checks. |
| https://docs.chargeflow.io/docs/merchants/automation | Public competitor positioning emphasizes evidence enrichment and automation. | Make the human-visible causal proof and repair diff the product moment. |
| https://justt.ai/platform/ | Public positioning emphasizes automated evidence and representment. | Keep financial authority human and deterministic rather than adding autonomous actions. |
| https://genai.owasp.org/llmrisk/llm01-prompt-injection/ | Prompt injection has no foolproof prevention; least privilege, separation, validation, and adversarial testing matter. | Treat communication as untrusted data, give extraction no gate authority, and expose a break case. |

## Implemented interaction contract

1. Wrong processed amount → verified material conflict → BLOCK.
2. Incomplete ledger → absence cannot be proved → REVIEW.
3. Contradictory communication → unsupported semantics → REVIEW.
4. Prompt instruction in evidence → ignored as instruction; grounded claim still reconciled → BLOCK.
5. More than two money decimals → HTTP 422 input rejection; no decision.
6. Controlled extractor outage → `F_MODEL_UNAVAILABLE` → REVIEW.
7. Attach matching processed refund record → rerun unchanged deterministic policy → PASS with visible before/repair/after diff.

## Evaluation and model decision

The selected system remains the bounded B0 regex extractor. The saved local TF-IDF/logistic
candidate was not promoted under the predeclared DEV comparison. No fine-tuning job is justified:
there is no new representative dataset or demonstrated baseline gap that warrants training expense,
and the current frozen result already identifies `partial_full_amount` as the known recall failure.
The evaluation screen therefore loads only saved generated artifacts and keeps that failure slice
visible.

## Limitations

- Synthetic holdout performance does not establish production prevalence or merchant savings.
- The debugger accepts bounded canonical text and structured ledger state; it is not a document parser.
- PASS means no supported integrity issue was found under complete bounded evidence, not dispute victory.
- BLOCK is a local decision-support hold, not a legal verdict or Razorpay-side action.
- Public competitor documentation cannot prove absence of private/internal integrity checks.
