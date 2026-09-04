# FECL-Bench v4.4 certificate-taxonomy erratum

Status: final benchmark candidate before model fitting and TEST access.

v4.3 passed all non-TEST label-blind decision checks, but a pre-fit certificate audit found that
single-record partial refunds were annotated `CUMULATIVE_AMOUNT`. The compiler has no label-blind
reason to distinguish that invariant from ordinary single-record `AMOUNT_EQUALITY`; only multiple
refund records require `CUMULATIVE_AMOUNT`.

v4.4 preserves all v4.3 causal, grounding, identity, split, and acquisition corrections and changes
only that certificate vocabulary. All single-refund amount checks use `AMOUNT_EQUALITY`; multiple
refund records use `CUMULATIVE_AMOUNT`. No model was fitted and TEST was not evaluated before this
correction.
