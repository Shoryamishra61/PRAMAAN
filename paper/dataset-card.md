# DIG-FECL-SYN-v2 dataset card

## Summary

Synthetic diagnostic benchmark for evidence/state consistency in the narrow refund-not-processed
domain. It contains 640 training, 256 development,
384 frozen test, and 40 OOD cases. Every
in-distribution case belongs to a minimal pair that shares authoritative state while one material
claim changes.

## Intended use

- research on semantic-state extraction, relational representations, selective prediction and
  deterministic reconciliation;
- regression testing of a defense-only evidence debugger.

## Prohibited claims

The dataset does not estimate production prevalence, dispute win rate, fraud, legal correctness,
merchant savings or real customer behavior. It must not train autonomous payment/dispute actions.

## Splits and leakage controls

- Train families: formal, support, portal, terse, Hinglish-train.
- DEV families: narrative, passive.
- Frozen test families: indirect, temporal, Hinglish-holdout.
- Test SHA-256: `6c87aa0aac576383d3c760bcb6da087d01d3adff83fefc1a69b05e0b0b43b82f`.
- Dataset manifest SHA-256: `ae90df0d718ca887e7a12a0972791c5e04b27535a1666f18a75b830c4a7f1189`.

## Known limitations

Template-generated language, balanced labels, fixed graph topology, single-event temporal state,
canonical text/JSON only, and no merchant/issuer outcome labels. Results are synthetic benchmark
results only.
