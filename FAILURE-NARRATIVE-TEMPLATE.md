# Failure Narrative — Fill Only From Real Build Evidence

> Do not invent a bug for the Buildathon form. Use an issue that actually occurred, or clearly label a deliberate fault-injection exercise.

## Symptom
What observable behavior failed?

## Reproduction
Exact fixture/command/request needed to reproduce it.

## Impact
What requirement or user/system safety property was violated?

## Root cause
What actually caused the failure? Avoid “AI was wrong” as a root cause; identify the mechanism.

## Fix
What changed and why is the change minimal/safe?

## Regression evidence
Test name(s), artifact(s), and before/after behavior.

## Residual risk
What remains unresolved or outside MVP scope?

## Classification
- [ ] Real implementation defect encountered during build
- [ ] Deliberate fault injection / chaos test

## Related requirement IDs
`REQ-...`
