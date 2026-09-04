# 32 — Research integrity reconciliation

Status: generated evidence audited on 2026-09-01  
Machine-readable source: `artifacts/research/fecl-integrity-audit.json`

## Verdict

FECL-v1, FECL-v2 and FECL-v3 are separate protocols. Their metrics cannot be combined into one
leaderboard. FECL-v3 is a useful negative result: ESRAN failed its frozen promotion gates and the
runtime stayed `regex-baseline-v1`. No repository artifact supports a REISeR result.

## Reconciled dataset cardinality

| Version | TRAIN | DEV | CAL | TEST | OOD | Total | Integrity |
|---|---:|---:|---:|---:|---:|---:|---|
| FECL-v2 | 640 | 256 | — | 384 | 40 | 1,320 | manifest/file hashes match |
| FECL-v3 | 800 | 240 | — | 320 | 64 | 1,424 | manifest/file hashes match |

The prose total `1,420` for v3 is wrong. The current v3 generator creates exactly the requested
case count; the externally reported five-family multiplier bug is not present in the audited file.

## Reconciled frozen results

| Protocol | Projection | Model | F1 | False PASS | False BLOCK | Cases |
|---|---|---|---:|---:|---:|---:|
| FECL-v2 TEST | DEV-calibrated | neuro-symbolic | 0.712871 | 48 | 68 | 384 |
| FECL-v2 TEST | DEV-calibrated | relational XGBoost | 0.728971 | 35 | 82 | 384 |
| FECL-v3 TEST | DEV threshold | relational XGBoost | 0.923588 | 21 | 2 | 320 |
| FECL-v3 TEST | DEV threshold, five-seed ensemble | ESRAN | 0.734908 | 20 | 81 | 320 |

These rows measure different generators, family shifts, feature contracts, thresholds and model
implementations. The v2 XGBoost `35` and v3 XGBoost `21` are both valid only in their own protocols.
Numbers `12`, `34`, and `REISeR 9` supplied in later narrative summaries are unsupported by the
repository and are excluded.

## FECL-v3 negative result

- XGBoost F1: `0.923588`; ESRAN F1: `0.734908`.
- Pair-group bootstrap ESRAN-minus-XGBoost delta: `-0.188688`, 95% interval
  `[-0.233336, -0.144487]` over 2,000 pair resamples.
- ESRAN grounding-node F1: `0.62069`.
- Greedy exact-subgraph recovery: `0.0`; mean deletion drop: `-0.004467`.
- ESRAN repair-flip rate: below the preregistered `0.80` gate.
- Learned OOD rejection: `0.3125`; combined rejection was `1.0` only because every OOD example
  triggered the schema controller.

The result rejects relation-aware message passing for this synthetic case-local topology. It does
not establish that all graph learning is ineffective in payment fraud networks.

## Metadata defects

The v3 freeze artifact records `test_open_count: 0`, while a frozen TEST artifact exists. The runner
correctly refuses a second TEST file, but the mutable-looking count was never updated. It is stale
metadata and must not be cited as execution proof. FECL-v4 uses an append-only test receipt whose
existence and digest are validated separately from the immutable pre-test freeze.

## Explanation terminology correction

FECL-v3's greedy node masking is a diagnostic attribution experiment. It is not a proof of
minimality and must not be called a minimum contradictory subgraph. CARVE reserves **Minimum
Contradiction Certificate (MCC)** for a minimized solver-provable set of grounded semantic and
authoritative facts. Statistical-only outcomes receive a model counterfactual, never an MCC.

## Conformal terminology correction

FECL-v2 calibration worsened under family shift. FECL-v3's split-conformal sets are diagnostics;
the protocol itself acknowledges that unseen TEST families violate exchangeability. CARVE will
report any Conformal Risk Control statement with its bounded loss, calibration population,
finite-sample rule and invalidation conditions. It will not claim arbitrary conditional guarantees.

## Binding v4 constraints

1. Separate TRAIN, DEV, CALIBRATION, TEST and OOD.
2. Keep causal pairs within a split and bootstrap at pair level.
3. Freeze protocol, generator, data hashes, feature schema, model artifacts and operating thresholds
   before TEST.
4. Record the one TEST execution in an append-only receipt.
5. Never merge old-version metrics into v4 tables.
6. Formal proof cannot be overridden by a learned score.
7. Any missing, OOD, corrupt, or unverifiable state routes to REVIEW.

