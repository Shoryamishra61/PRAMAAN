# ADR-001 — One Bounded AI Stage by Default

**Status:** Accepted for MVP

## Context
Legacy reports required an LLM claim extractor followed by a second LLM/NLI contradiction stage. That adds variance, latency, cost, and an additional calibration problem without first proving that a second probabilistic stage adds measurable lift.

## Decision
The MVP uses **one bounded probabilistic task**: extract typed refund/credit claims from unstructured customer communication and return exact source quotations. Deterministic code validates the quotation, resolves offsets, and compares those claims with trusted structured refund/payment state.

A dedicated NLI/cross-encoder or second LLM stage is an **experiment**, not a dependency. It may be retained only if a predeclared dev-set ablation demonstrates material improvement on hard semantic cases without unacceptable false holds or complexity.

## Consequences
- simpler failure surface and judge story;
- no self-reported LLM confidence used as policy input;
- semantic ambiguity defaults to REVIEW;
- future model-stage additions require an ADR and evaluation evidence.
