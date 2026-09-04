# ADR-002 — No Razorpay Write Actions in the MVP

**Status:** Accepted

## Context
Razorpay exposes dispute accept/contest actions, but the Buildathon Track 02 solution is strongest as an independent defensive verifier. Earlier reports contradicted themselves by claiming both human-gated behavior and automatic contest/accept execution.

## Decision
The MVP does **not** call Razorpay dispute write endpoints. It may replay/ingest documented webhook fixtures and expose local analyst decisions such as `MARK_READY`, `REVIEW`, `HOLD`, or `OVERRIDE_LOCAL_HOLD`.

## Consequences
- defense-only boundary is easier to demonstrate;
- no accidental financial/network action in demo;
- PASS is not submission approval or win prediction;
- production integration can be designed later behind explicit authorization and policy gates.
