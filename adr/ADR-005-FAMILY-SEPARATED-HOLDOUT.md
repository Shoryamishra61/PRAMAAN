# ADR-005 — Scenario-Family-Separated Frozen Holdout

**Status:** Accepted

## Context
Changing synthetic dates does not create meaningful OOD evaluation. If the generator and detector share the same templates/rules, performance can be circular and misleading.

## Decision
Benchmark v1 targets 180 synthetic cases: 120 development and 60 frozen holdout. Holdout cases use **unseen scenario/template families**, paraphrase families, irrelevant evidence patterns, and failure modes not exposed during prompt/rule tuning. The split is frozen by manifest and file hashes.

The exact count may be reduced if implementation time requires it, but any reduction must be disclosed and must not be defended with unsupported population-level statistical claims.

## Consequences
- stronger generalization test than date-based split;
- metrics remain synthetic benchmark metrics;
- holdout is not opened during normal development loops.
