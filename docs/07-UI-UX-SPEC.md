# 07 — UI/UX & Human-Factors Specification

## UX objective
Help an analyst **verify**, not admire, the system's recommendation.

Research supports that AI-assisted users can over-rely on wrong suggestions; cognitive forcing can reduce overreliance but also adds usability cost. Therefore friction is applied only to consequential BLOCK overrides, not globally. [SRC-HCI-01, SRC-HCI-02]

## Information hierarchy
1. **What is the gate status?**
2. **What exact finding caused it?**
3. **What source evidence supports the finding?**
4. **What can the operator do next?**
5. Technical/model metadata only on demand.

No “AI thinks…” copy. No unvalidated probability badges.

## Screen 1 — Queue

Columns:
- case/dispute ID;
- amount/currency;
- respond-by;
- raw reason code;
- local profile;
- processing state;
- gate status;
- primary reason.

Default sort:
1. REVIEW/BLOCK before PASS;
2. respond-by ascending;
3. amount only as secondary context.

Do not claim this is an empirically optimal triage formula.

Filters:
- gate state;
- processing state;
- reason profile.

Keyboard:
- standard table/row focus first;
- optional `j/k` shortcuts only when focus is not inside an editable control and shortcuts are discoverable.

## Screen 2 — Case workspace

Responsive desktop layout:
- left: queue/context (collapsible);
- center: evidence viewer;
- right: gate findings/actions.

At narrower laptop widths, collapse queue before squeezing evidence.

Header:
- `GATE CLEAR`, `REVIEW REQUIRED`, or `LOCAL HOLD`;
- plain-language reason;
- label: `Decision support only — not a win prediction`.

## Evidence viewer
MVP renders canonical text/JSON, not arbitrary PDF.

Each document shows:
- source type;
- source system label;
- captured/ingested time if present;
- SHA-256 integrity digest in technical details;
- canonical source text.

Selecting a grounded claim:
- moves focus to exact quote;
- highlights it;
- announces concise context to assistive technology without noisy global `aria-live` behavior.

## Finding card

For material conflict:

**Claimed in communication**
> exact grounded quote

**Structured refund state**
> refund ledger summary

Then:
- finding code;
- why these conflict under local rule;
- decision effect;
- source links.

Never say “legally invalid,” “fraudulent,” or “unwinnable.”

## PASS UI
Copy:
> **Gate clear.** No supported integrity issue was detected in the evidence available to this verifier.

Actions:
- `Mark ready for contest` (LOCAL ONLY)
- inspect evidence.

## REVIEW UI
Copy must name the unresolved reason:
- missing recommended evidence;
- model unavailable;
- quote not grounded;
- incomplete ledger;
- unsupported evidence type.

Primary action:
- `Review / repair evidence`.

No “low confidence 74%” unless a future validated probabilistic score exists.

## BLOCK UI
Copy:
> **Local hold.** A material evidence inconsistency was verified. Review the cited sources before marking this case ready.

Primary:
- `Resolve evidence`.

Secondary:
- `Override local hold`.

No direct “Accept dispute/Forfeit” network action.

## Structured override flow

Opening override modal:
1. focus goes to modal heading/first control;
2. list finding(s) being overridden;
3. operator must open/acknowledge both cited evidence sources;
4. choose reason:
   - `SOURCE_DATA_ERROR`
   - `EVIDENCE_REPAIRED_OUTSIDE_APP`
   - `KNOWN_BUSINESS_EXCEPTION`
   - `DISAGREE_WITH_RULE`
   - `OTHER`
5. optional note; require a short note only for OTHER;
6. confirm `This changes only the local readiness state`;
7. append audit event.

This is evidence-directed cognitive forcing, not character-count friction.

## Evaluation page
Show:
- dataset ID/version;
- synthetic warning;
- holdout size;
- baseline and proposed metrics;
- confusion matrix;
- slice table;
- result artifact timestamp/config hash.

Every value comes from backend artifact.

## Judge proof console

### Interactive first screen

The default view is a working financial evidence debugger, not a status dashboard or saved-case
presentation. It opens on a wrong-refund-amount contradiction and exposes six deliberate break
modes: wrong amount, missing/incomplete ledger, contradictory communication, prompt injection,
malformed evidence, and extractor outage. The editor accepts disputed INR amount, customer
communication, refund state/amount, and ledger completeness. Each scenario runs directly through
the real sandbox endpoint and every field remains editable.

The result reads as a single causal trace: input evidence → grounded claim extraction → authoritative
ledger reconciliation → visible contradiction → PASS/REVIEW/BLOCK. Semantic extraction is labeled
as replaceable and non-authoritative; ledger reconciliation and gate policy are labeled
deterministic. Every finding provides keyboard-operable links back to its exact communication and/or
ledger proof. The evidence-repair action attaches a matching processed refund record, reruns the same
policy, and displays a before/repair/after decision diff. No confidence score, decorative model
feature, or autonomous financial action is present.

The saved signed-webhook golden path remains available through the analyst workspace and adjacent
proof chapters; the sandbox must not claim that free-text submission performed webhook HMAC or
durable ingestion.

The default demo entry is a single evidence-debugging and evaluation surface, not a
marketing landing page, guided tutorial, analyst queue, or generic metric
dashboard. The first chapter makes the canonical BLOCK case inspectable as one
continuous sequence:

1. persisted signed dispute notice and raw event facts;
2. authenticated/durable ingestion boundary;
3. bounded semantic extraction and exact quote grounding;
4. deterministic comparison with trusted refund state;
5. local BLOCK hold and human analyst handoff;
6. saved-artifact HOLDOUT metrics and parameterized illustrative cost.

The only adjacent view is `GENERATED EVALUATION`: precision, recall, F1, false-pass cost signals,
review rate, selected rules-only baseline, known failure slice, and artifact provenance. It renders
only values loaded from the latest saved evaluation artifact and shows `NOT YET MEASURED` when no
artifact exists.

The proof console may replay/read the persisted seeded case, but must not imply
that a fresh webhook was transmitted when it only reloaded saved local state.
All benchmark values come from the digest-verified evaluation response. Cost
controls may combine saved case counts with explicitly user-selected,
illustrative unit costs; they must not be labeled INR, savings, ROI, or merchant
outcomes.

## Offline AI/ML evidence lab

The proof console/workspace may expose an experimental panel that shows:
- which exact sentence the local model nominated;
- the present n-gram contributions behind that nomination;
- DEV-only candidate-versus-regex metrics;
- explicit `PROMOTED` or `NOT PROMOTED` status;
- retrieved local guidance with source path, section, and exact excerpt.

It must say that the lab is non-authoritative, makes no external model call, and cannot change the gate. Do not show model probability, opaque “AI confidence”, fake RAG animation, or a chatbot.

## Audit page
Shows:
- decisions;
- inspections;
- overrides;
- processing failures;
- audit-chain health if implemented.

No edit/delete UI.

## Accessibility
Target WCAG 2.2 AA practices:
- semantic HTML;
- visible focus;
- adequate contrast tested in implementation;
- color + icon + text for states;
- keyboard-operable dialogs/links;
- no hover-only information;
- reduced-motion support;
- dialogs trap focus correctly; general workspace does not.

## Motion
No decorative animation.
Functional source jump may use smooth scroll only when reduced motion is not requested; exact duration is not a product requirement.

## Human-factors evaluation
Optional formative test after MVP:
- compare warning-only vs source-inspection override flow;
- use intentionally wrong system findings;
- measure final decision correctness and time;
- report participants and protocol honestly;
- do not claim statistical/generalizable overreliance reduction from a tiny sample.
