# 19 — Demo, Pitch & Submission Strategy

## One-sentence hook
> **Evidence assembly is not evidence integrity. Dispute Integrity Gate verifies refund-dispute packets before a human contests them—grounding what customer communication says and reconciling it against the merchant's actual refund state.**

## 5-minute pitch structure

### 0:00–0:35 — Problem
Show one case:
- support communication says full refund was processed;
- structured refund ledger has no matching final refund.

Say:
> “This packet can look complete while its own evidence disagrees.”

Do not claim a prevalence percentage.

### 0:35–1:05 — Why this fits Razorpay
- Track 02 explicitly allows a verifier;
- held-out precision/recall + false-positive cost required;
- Razorpay already has dispute evidence and `action_required` when evidence is insufficient/unreadable/mismatched.

### 1:05–2:40 — Live golden demo
Deeply show BLOCK:
1. signed `payment.dispute.created` replay;
2. case appears;
3. model extracts exact quote “we processed…”
4. clicking finding highlights exact source;
5. structured refund ledger shown side by side;
6. deterministic rule creates local hold;
7. override requires evidence inspection + structured reason.

Quickly show:
- REVIEW via model unavailable/ungrounded;
- PASS consistent refund.

### 2:40–3:35 — AI judgment
Diagram:
`unstructured communication → grounded typed extraction (AI) → deterministic refund verifier → gate`.

Say:
> “AI interprets language. It never decides money, dates, IDs or network actions.”

Mention NLI/agents deliberately omitted unless evaluation proves need.

### 3:35–4:25 — Evaluation
Open real `/evaluation` page:
- synthetic dataset label;
- holdout N;
- precision/recall/F1;
- exact counts;
- baseline;
- error slices;
- parameterized false-positive cost.

Never read metrics from a script written before the final run.

### 4:25–5:00 — Failure + honesty
Show:
- provider outage → REVIEW;
- durable job/reprocess;
- no auto-contest;
- synthetic benchmark limitation.

Close:
> “The product does not try to win disputes with more generated text. It gives the merchant a verifiable reason to stop, repair, or review before submitting.”

## 2-minute judge demo
- 0:00–0:20: queue + one-line problem.
- 0:20–1:15: BLOCK case source grounding + ledger conflict.
- 1:15–1:35: local override safety.
- 1:35–1:50: REVIEW on semantic outage.
- 1:50–2:00: real held-out metric page.

## README content requirements
Root implementation README should include:
1. exact problem/scope;
2. working-vs-mocked table;
3. 60-second quickstart;
4. architecture;
5. reason profile;
6. benchmark card;
7. current computed results;
8. failure behavior;
9. security boundaries;
10. limitations;
11. source links;
12. demo video.

## Working vs mocked disclosure

### Working
Expected:
- HMAC validation;
- idempotent event intake;
- SQLite/job worker;
- deterministic verifier;
- semantic extraction adapter;
- grounding;
- UI;
- evaluation harness.

### Synthetic/mocked
- merchant refund records;
- customer communications;
- dispute fixture events;
- offline replay model responses.

### Not implemented
- actual contest/accept submission;
- issuer outcome;
- real merchant data;
- production auth/tenant controls.

## Hostile questions

### “Why isn't this just a chargeback letter writer?”
Because it generates no argument. Its output is an integrity finding with verifiable source evidence.

### “Why not one giant LLM prompt?”
Because it would combine interpretation and decision. Our decomposition allows grounded semantic extraction and deterministic financial resolution, plus a comparable regex baseline.

### “Do you know competitors don't already do this?”
No. Public docs reviewed emphasize collection/generation/submission; we do not claim private capabilities are absent. Our contribution is a standalone, inspectable implementation of the verification control point.

### “Why RZP04 / refund not processed?”
Razorpay publicly documents RZP04 evidence around refund proof, bank/refund amount, communication and policy, and Visa 13.6 is the analogous credit-not-processed condition. This creates a tight structured+unstructured test surface.

### “Why is a BLOCK correct?”
BLOCK is not a legal decision. It is a local hold when a material conflict is established under our documented reason profile.

### “Why synthetic data?”
Real merchant dispute data is sensitive/unavailable. Synthetic fixtures provide deterministic ground truth for the Buildathon's required held-out evaluation; we explicitly do not claim production prevalence or win-rate lift.

### “What happens when the model is wrong?”
If its quote cannot be grounded, REVIEW. If a grounded claim drives a finding, the operator can inspect the exact text. Final cross-source rule is code, not the model.

### “How is prompt injection prevented?”
Not by magic delimiters. The model has no tools, secrets or action authority; its structured output is untrusted and grounding/policy are deterministic.

### “Why SQLite?”
Zero-config local reproducibility. It is a hackathon storage choice, with durable jobs and WAL, not a claim about enterprise scale.

### “What would you build next?”
First validate on de-identified real dispute bundles with domain experts; then broaden reason profiles based on evidence, improve document ingestion, and evaluate any dedicated semantic classifier only where needed.
