# Demo and video script

These are timed allocations, not a claim that a video has been recorded or submitted. Every performance number below comes from the saved synthetic HOLDOUT artifact with SHA-256 `15349fd24f2fbceb1c6a38edafee92d5953f22af2e9611efcda17ba20f1992b8`. Run `scripts/rehearse-demo.ps1` before presenting to verify the technical path without loading or recomputing the HOLDOUT.

## Two-minute golden demo

| Time | Screen/action | Words to convey |
| --- | --- | --- |
| 00:00-00:15 | Open LIVE RUN and point to the editable communication and trusted-ledger inputs. | “This is one narrow, defense-only refund-evidence verifier. The input is synthetic, runtime is offline, and the MVP makes no Razorpay writes.” |
| 00:15-00:45 | Submit the BLOCK example. | “The backend extracts the processed-refund claim, resolves its exact quote and INR amount, then deterministic code finds no ledger match and returns this rule-coded local hold. BLOCK is not a legal verdict.” |
| 00:45-01:05 | Load PASS, submit, and point to the matching processed refund. | “The same claim becomes PASS only after the trusted ledger contains the exact processed amount. PASS is not a win prediction.” |
| 01:05-01:25 | Load REVIEW, submit, and point to the incomplete snapshot. | “Uncertainty abstains. An incomplete ledger cannot produce PASS or BLOCK.” |
| 01:25-01:40 | Point to the extractor ID, exact span, and deterministic-policy boundary. | “Language extraction is bounded and inspectable; money, grounding, identifiers, and gate authority remain code-owned.” |
| 01:40-02:00 | Open HELD-OUT EVAL and point to false PASS plus the known miss. | “The frozen synthetic artifact reports 10 of 20 material conflicts found and 10 false PASS. The limitation is visible, not tuned away.” |

Total allocated time: **02:00**.

## Five-minute video/pitch

| Time | Screen/action | Words to convey |
| --- | --- | --- |
| 00:00-00:30 | Title, narrow problem statement, and boundary. | “Dispute Integrity Gate checks whether merchant evidence contradicts trusted local refund state before an analyst proceeds. It evaluates only `refund_not_processed_v1`; it does not accept, contest, refund, or write to Razorpay.” |
| 00:30-01:15 | Edit LIVE RUN input and submit the BLOCK example. | “The custom input reaches a real local API. The selected extractor emits only typed claims; backend grounding binds this one to span 0:36 and normalizes ₹2,500 to paise.” |
| 01:15-02:30 | Demonstrate PASS and REVIEW by changing only ledger truth/completeness, then open the saved BLOCK analyst case. | “Deterministic code owns money, evidence completeness, conflicts, and policy. Matching truth produces PASS; incomplete truth abstains to REVIEW. The saved signed-webhook case supports source inspection and local-only override without a Razorpay write.” |
| 02:30-03:10 | REVIEW workspace and injected outage command/output. | “Unsupported input, bad schema, missing grounding, or extractor outage routes to REVIEW. The deliberate outage rehearsal produces `F_MODEL_UNAVAILABLE`; restoring the versioned offline replay output recovers the consistent fixture to PASS without logging raw evidence.” |
| 03:10-03:40 | PASS workspace and audit timeline. | “PASS says only that the available evidence produced no material conflict. It is not a win probability. The analyst can inspect the local audit timeline, while the raw Razorpay reason code remains preserved.” |
| 03:40-04:30 | Evaluation dashboard. | “The frozen synthetic HOLDOUT has 60 balanced cases. Material-conflict precision is 10/10, recall is 10/20, REVIEW is 20/60, automatic coverage is 40/60, false BLOCK is 0, and false PASS is 10. The `partial_full_amount` slice is 0/10 correct. The regex system is identical to baseline B0, so every displayed delta is zero; no model-backed B1 is claimed.” |
| 04:30-05:00 | README boundaries and close. | “The dashboard reads the digest-verified saved artifact; it does not calculate or hard-code metrics in the UI. The repository separates working, synthetic, mocked, and future capabilities. The current evidence supports a reproducible research prototype and exposes where it fails.” |

Total allocated time: **05:00**.

## Technical rehearsal

```powershell
powershell -ExecutionPolicy Bypass -File scripts/rehearse-demo.ps1
```

The command intentionally injects extractor unavailability, verifies REVIEW and offline recovery, starts the seeded demo, reads health, queue, evaluation, and frontend responses over loopback with proxies disabled, verifies the final artifact digest and measured counts, then stops only the recorded demo processes. It does not evaluate or tune on the frozen HOLDOUT.

## Presenter guardrails

- Say “synthetic class-balanced diagnostic benchmark,” never imply production prevalence.
- Say “local integrity hold,” never legal verdict, fraud verdict, or chargeback-win prediction.
- State the 10 false PASS cases and the failed `partial_full_amount` slice whenever reporting precision.
- Do not describe the regex baseline as a live model, and do not claim B1 improvement.
- Do not claim ROI, savings, user study results, production latency, PCI compliance, immutability, or Razorpay endorsement.
