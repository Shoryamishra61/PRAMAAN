# Track 02 judge-visibility audit

## Evidence captured

- `01-current-entry.png`: rejected landing/tutorial entry.
- `03-current-decision.png`: deterministic contradiction hidden in step 3.
- `05-current-ai-lab.png`: ML evidence isolated from the case decision.
- `06-current-evaluation.png`: artifact-backed values presented as a raw metric/JSON page.
- `08-approved-proof-console.png`: selected replacement visual target.
- `13-implementation-910x642.png`: browser-rendered localhost implementation.
- `15-implementation-mobile.png`: responsive implementation evidence.

## Findings and resolution

- **P1 — Judge must infer the system across unrelated screens.** The old entry
  required a four-step tutorial before exposing the analyst product, then put AI
  and held-out evaluation on separate pages. Replaced with one default proof
  console containing the case trace, semantic boundary, deterministic finding,
  benchmark weakness, cost inputs, and analyst handoff.
- **P1 — AI contribution is invisible during the decision.** The DEV-only model
  appeared only after the tutorial and emphasized rejection without showing why
  that is good governance. The proof console now shows selected B0, the grouped
  TF-IDF/logistic challenger, `NOT_PROMOTED`, comparator F1, and signed n-grams
  beside the live case while preserving zero gate authority.
- **P1 — Evaluation is not five-minute-demo legible.** The old page led with
  provenance blocks and dumped confusion/slice JSON. Replaced with artifact-
  backed precision, recall, F1, false-PASS, REVIEW, known miss, cost sensitivity,
  and a readable three-class confusion matrix.
- **P2 — Architecture and failure recovery are absent from the product story.**
  Added code-aligned architecture and recorded fault-injection chapters with
  explicit REVIEW fail-safe behavior.
- **P2 — Rejected interaction model remains reachable.** Analyst navigation now
  returns to `Proof console`, not `Product tour`; the old guided route is no
  longer the default product path.

## Accessibility scope

Semantic headings, navigation, buttons, labeled number inputs, text-plus-color
states, focus outlines, reduced-motion behavior, and keyboard-operable chapter
switching were inspected. This is implementation evidence, not a WCAG or
screen-reader certification.
