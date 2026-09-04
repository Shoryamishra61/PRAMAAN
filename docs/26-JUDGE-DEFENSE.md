# 26 — Judge Defense / Panel Q&A

Use these as factual answer structures, not memorized marketing claims. Replace placeholders with measured values only after the build generates them.

## Why isn't this just another chargeback responder?
The MVP does not draft or submit a response. It verifies one narrow evidence-integrity problem before a merchant decides what to do. Public product documentation for major dispute-automation vendors emphasizes evidence collection/enrichment, argument construction, and submission; we did not find public documentation positioning a standalone merchant-side grounded inconsistency gate as the primary workflow. We do not claim competitors have no internal checks.

## Why Track 02?
Razorpay explicitly asks Track 02 teams for a working detector/verifier/auto-responder for one loss class with held-out precision/recall and honest false-positive cost. This design is a verifier and is deliberately defense-only. See SRC-RZP-01.

## Why refund/credit-not-processed?
Razorpay's current evidence guide explicitly describes RZP04 Refund not Processed and Visa 13.6 Credit Not Processed, including refund proof, matching amount/state, customer communication, policy context, and reversal/credit records. That creates a narrow multi-source verification surface. See SRC-RZP-06 and SRC-VISA-01.

## Why AI at all?
Customer communication is natural language; typed extraction can normalize statements such as “we approved a full refund” or “your credit will arrive in 5 days.” The model cannot decide the gate. Structured payment/refund truth, amounts, identity links, and final policy stay deterministic. If the AI stage does not outperform a strong non-AI baseline on the dev benchmark, remove it.

## Why no NLI model?
A second probabilistic stage is not free. The MVP first tests whether grounded extraction plus deterministic resolution solves the selected family. NLI/cross-encoder becomes an ablation candidate for genuinely ambiguous text-pair cases.

## What does PASS mean?
Only: no integrity issue supported by this verifier was detected in the available evidence. It is not a prediction that the dispute will be won and not authorization to submit.

## What does BLOCK mean?
A local safety hold caused by a material inconsistency that the engine can establish from grounded text plus trusted structured state. It is not a legal judgment or statement of fraud/bad faith.

## What happens when the model is down or uncertain?
REVIEW. Degraded semantics never silently PASS.

## Isn't synthetic data a toy?
It is a controlled benchmark, not production validation. The value is reproducibility, explicit ground truth, hard negatives, family-separated holdout, and baseline comparison. The README must state that real merchant prevalence and production win-rate impact are unknown.

## How do you avoid benchmark circularity?
The holdout uses unseen scenario/template families; generator labels and detector rules are separately reviewed; runtime code cannot read ground-truth labels; frozen files are hash-manifested; any change creates a new benchmark version.

## Where are the metrics?
Only in generated evaluation artifacts. If the run has not happened, the UI says NOT YET MEASURED. No 0.89 F1 or rupee-savings number is prewritten.

## How do you handle false-positive cost?
Use parameterized sensitivity analysis: `false_pass*C_false_pass + false_block*C_false_block + review*C_review`. Unless merchant-specific inputs exist, costs are illustrative parameters, not claimed savings.

## Why no PDF/OCR?
It is not needed to test the core hypothesis and would add parser/security/evaluation complexity. v1 uses canonical text/JSON evidence; document ingestion can be evaluated as a later subsystem.

## What is the real Razorpay webhook event?
Use documented `payment.dispute.created` and other `payment.dispute.*` events. `dispute.opened` was a legacy-report error.

## Do you call Razorpay contest/accept APIs?
No in the MVP. Razorpay documents contest as PATCH and accept as POST, but this verifier deliberately has no write authority.

## How is prompt injection handled?
Not by pretending delimiters are foolproof. Evidence is untrusted data; the model has no tools, secrets, DB access, or state authority; outputs are schema-validated and grounded; deterministic policy contains impact; adversarial fixtures test degradation to REVIEW.

## Is the audit log immutable?
No. If hash chaining is implemented, call it tamper-evident under a limited threat model. A privileged attacker able to rewrite all state may recompute a local chain unless an external checkpoint exists.

## Why SQLite?
For zero-service local reproducibility. WAL, short transactions, durable job state, and restart tests are sufficient for the Buildathon. It is not presented as the final enterprise datastore.

## What broke?
Answer only from `FAILURE-NARRATIVE.md` generated during implementation. Never use a prewritten hypothetical defect as a genuine incident.
