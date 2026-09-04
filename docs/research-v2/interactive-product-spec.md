# Interactive AI Risk Research Workbench

## Core judge loop

```text
INPUT EVIDENCE
 -> GROUNDED CLAIM
 -> AUTHORITATIVE REFUND RECONCILIATION
 -> VISIBLE CONTRADICTION
 -> PASS / REVIEW / BLOCK
 -> EVIDENCE REPAIR
 -> LIVE DECISION DIFF
```

- **DESIGN DECISION:** The first screen is an evidence debugger, not a portfolio dashboard.
- **DESIGN DECISION:** AI-derived claims use a distinct `LEARNED CLAIM` label and source-span treatment; deterministic facts/checks use `AUTHORITATIVE FACT` and `RULE CHECK` labels.
- **DESIGN DECISION:** No confidence percentage is displayed. The UI shows model identity, score type, calibration status, OOD/disagreement state and whether the output is eligible or abstained.

## Workbench anatomy

1. **DESIGN DECISION:** Case strip: reason, amount, as-of time, synthetic/offline disclosure and boundary status.
2. **DESIGN DECISION:** Evidence editor: communication and ledger records with deliberate break controls.
3. **DESIGN DECISION:** Causal trace: exact claim span -> normalized attributes -> matching ledger query -> finding -> decision.
4. **DESIGN DECISION:** Evidence graph: typed nodes/edges with source provenance; visual explanation only unless a learned graph artifact exists.
5. **DESIGN DECISION:** Decision rail: state, typed reasons, recovery steps and external-action prohibition.
6. **DESIGN DECISION:** Repair diff: before/after evidence, findings and state; unrelated findings remain unchanged.

## Deliberate break matrix

| Judge action | Required safe response |
|---|---|
| **DESIGN DECISION:** wrong refund amount | deterministic amount contradiction -> BLOCK when authoritative ledger is complete; exact claim and ledger row clickable |
| **DESIGN DECISION:** missing ledger entry / incomplete export | REVIEW for insufficient authoritative evidence, not BLOCK |
| **DESIGN DECISION:** contradictory email | REVIEW when semantic conflict is unresolved; BLOCK only when a grounded processed claim materially contradicts complete ledger state |
| **DESIGN DECISION:** prompt injection text | treated as evidence text; no tool/action; unsupported/ambiguous semantics -> REVIEW |
| **DESIGN DECISION:** malformed money/evidence | schema rejection before a financial decision; prior state is not silently reused |
| **DESIGN DECISION:** model outage | typed `F_MODEL_UNAVAILABLE` -> REVIEW with deterministic features still visible |
| **DESIGN DECISION:** attach matching repair ledger row | idempotent recomputation; contradiction removed; decision diff identifies exact changed edge/finding |

## `/ai` research lab

- **DESIGN DECISION:** model switch replays saved per-case predictions from generated artifacts; it does not invent client-side scores.
- **DESIGN DECISION:** leaderboard includes baseline, status (`ACTIVE`, `RESEARCH_ONLY`, `REJECTED`, `NOT_RUN`), dataset/split and promotion reason.
- **DESIGN DECISION:** panels: PR curve, confusion matrix, calibration, risk-coverage, cost Pareto, OOD/adversarial slices, latency/memory/size, ablation, case failures and disagreement.
- **DESIGN DECISION:** SHAP is shown only for fitted tabular/tree candidates and labeled `MODEL ATTRIBUTION — NOT CAUSAL`; grounded spans are the primary semantic explanation.
- **DESIGN DECISION:** frozen holdout is read-only and clearly separated from DEV; no threshold controls operate on it.

## Accessibility and behavior

- **DESIGN DECISION:** all interactions are keyboard reachable; focus moves to the exact cited evidence; state is never communicated by color alone.
- **DESIGN DECISION:** tables have captions/headers, plots have text summaries, status announcements use appropriate live regions, and reduced-motion preferences are respected.
- **DESIGN DECISION:** mobile collapses into Evidence -> Finding -> Decision -> Repair order without hiding causal sources.

## Acceptance tests

- **DESIGN DECISION:** A first-time judge can break, diagnose and repair a case without narration.
- **DESIGN DECISION:** Every material finding has working source jumps and deterministic/learned provenance.
- **DESIGN DECISION:** Every visible metric resolves to an artifact digest and per-example predictions.
- **DESIGN DECISION:** No control implies a Razorpay/network write or autonomous financial action.

