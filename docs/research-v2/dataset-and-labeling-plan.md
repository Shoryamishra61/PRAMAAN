# Dataset and labeling plan

## Data unit and provenance

- **DESIGN DECISION:** The atomic deployment/evaluation unit is a complete dispute case, not a sentence.
- **DESIGN DECISION:** Each case contains de-identified payment/order/refund state, ledger completeness, timestamped communications, policy version, dispute reason, evidence inventory and final domain-reviewed labels.
- **DESIGN DECISION:** Raw sources receive stable IDs, observed/event timestamps, source-system class, content digest and consent/license metadata.

## Label schema

- **DESIGN DECISION:** span labels: `refund_requested`, `refund_promised`, `refund_approved`, `refund_claimed_processed`, `refund_denied`, plus material attributes for amount, currency, reference and event time.
- **DESIGN DECISION:** relation labels: `supports`, `contradicts`, `neutral`, `same_payment_as`, `same_amount_as`, `precedes`, `settles`, `governed_by`.
- **DESIGN DECISION:** authority labels: `merchant_communication`, `merchant_policy`, `payment_record`, `refund_ledger`, `dispute_metadata`.
- **DESIGN DECISION:** case labels are decomposed findings and evidence-completeness states; PASS/REVIEW/BLOCK is computed by policy, never annotated by the extraction model.

## Collection

- **DESIGN DECISION:** Minimum target before span-model training: 2,000 cases, at least 500 positive processed-refund spans, at least 200 reviewed contradiction pairs, and representation across merchants/templates/time.
- **ASSUMPTION:** These are engineering sufficiency gates, not statistical power guarantees; a pilot will estimate prevalence and revise them before holdout freeze.
- **DESIGN DECISION:** Sources must be consented, de-identified, access-controlled and excluded from prompts/logs beyond approved research storage.
- **DESIGN DECISION:** Synthetic cases are retained only for adversarial coverage and never mixed into a production-performance headline.

## Annotation protocol

1. **DESIGN DECISION:** Two independent annotators mark exact spans and attributes from canonical text.
2. **DESIGN DECISION:** Domain adjudicator resolves material disagreements without seeing model output.
3. **DESIGN DECISION:** Record ambiguity reason rather than forcing a label.
4. **DESIGN DECISION:** Measure span overlap/exact match, label agreement and adjudication rate.
5. **DESIGN DECISION:** Build hard negatives from approval-vs-completion, obligation-vs-event, partial-vs-full, duplicate quotes, future tense, negation, quoted customer text and prompt injection.

## Split policy

- **DESIGN DECISION:** TRAIN: model fitting and hard-negative mining.
- **DESIGN DECISION:** DEV: architecture/threshold/feature selection.
- **DESIGN DECISION:** CALIBRATION: one-time risk/calibration fitting after model freeze.
- **DESIGN DECISION:** FROZEN HOLDOUT: final evaluation only, manifest hashed before access.
- **DESIGN DECISION:** STRESS/OOD: explicit shifts, not merged with i.i.d. metrics.
- **DESIGN DECISION:** Group by merchant, communication template, linked entity component and chronology; use later time windows for validation/holdout where feasible.

## Leakage controls

- **DESIGN DECISION:** Near-duplicate hashing and embedding similarity audit across splits.
- **DESIGN DECISION:** Fit vocabulary, scalers, embeddings adapters and calibration only on permitted partitions.
- **DESIGN DECISION:** No issuer outcome, post-decision repair or later refund event may enter a point-in-time feature.
- **DESIGN DECISION:** Version labels and corrections; any holdout label change creates benchmark v3 and invalidates earlier comparisons.

