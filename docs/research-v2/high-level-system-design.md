# High-level system design

## Architecture boundary

- **DESIGN DECISION:** The system is a read-only decision-support verifier. It has no payment, refund, accept, contest or evidence-submission authority.
- **DESIGN DECISION:** Learned components transform untrusted evidence into grounded candidate claims/relations; deterministic code owns financial reconciliation and final policy.

```text
Merchant/Razorpay-compatible evidence
  -> canonical case adapter
  -> evidence normalizer + immutable-by-convention blob refs
  -> case representation
       |- deterministic financial facts
       |- grounded semantic claims
       |- temporal relations
       `- typed evidence graph
  -> candidate model(s)
  -> grounding + OOD + disagreement + risk controller
  -> deterministic reconciliation/policy
  -> PASS | REVIEW | BLOCK
  -> human inspection/repair
  -> idempotent recomputation + decision diff
```

## Planes

| Plane | Components | Contracts and failure behavior |
|---|---|---|
| **DESIGN DECISION:** Data | signed event ingest, canonical adapter, evidence store, case snapshots, feature materialization | raw bytes read once; idempotency key; integer minor units; UTC; unsupported or incomplete inputs never silently PASS |
| **DESIGN DECISION:** Model/research | dataset registry, feature definitions, training runners, model registry, offline evaluation | TRAIN/DEV/CALIBRATION/HOLDOUT separation; pinned model revisions; artifacts contain predictions and hashes |
| **DESIGN DECISION:** Decision/risk | grounding validator, OOD/disagreement selector, deterministic reconciler, policy engine | model output is untrusted; uncertainty -> REVIEW; only grounded material conflict against complete authoritative state -> BLOCK |
| **DESIGN DECISION:** Control | config/version registry, feature flags, shadow/canary, promotion, rollback, replay scheduler | dual-control promotion; previous model/policy retained; rollbacks do not rewrite historical decisions |
| **DESIGN DECISION:** Audit/observability | structured logs, traces, metrics, append-only application audit, hash-chain verifier | no raw evidence/secrets in logs; hashes show recorded-content continuity, not authenticity |
| **DESIGN DECISION:** Human review | queue, evidence debugger, graph, finding inspector, repair import, override workflow | exact source jumps, structured reason, before/after snapshot and local-only action |

## Data contracts

- **DESIGN DECISION:** `CaseSnapshot`: case ID, `as_of`, reason profile, payment/refund facts, ledger completeness, document refs and schema version.
- **DESIGN DECISION:** `GroundedClaim`: allowlisted type, normalized attributes, exact quote, offsets, document ID, extractor/model version and grounding state.
- **DESIGN DECISION:** `Relation`: typed source/target IDs, deterministic-or-learned provenance, score if applicable, calibration version and status.
- **DESIGN DECISION:** `Finding`: reason code, severity, deterministic rule version, all causal source IDs and remediation requirements.
- **DESIGN DECISION:** `Decision`: case snapshot hash, finding IDs, policy version, state, abstention reasons and timestamp.

## Reliability and lifecycle

- **DESIGN DECISION:** Durable job row is committed before webhook acknowledgement; retries are bounded and transient-only.
- **DESIGN DECISION:** Every processing attempt is idempotent on event ID + case snapshot hash + pipeline version.
- **DESIGN DECISION:** Replay writes a new versioned decision; it never mutates the historical output.
- **DESIGN DECISION:** Model outage, malformed output, ambiguous grounding or dependency failure produces REVIEW/processing error, not BLOCK.
- **DESIGN DECISION:** Shadow candidates receive copied, de-identified snapshots and no decision authority.

## Latency budget

- **ASSUMPTION:** Local interactive target: p95 under 1.5 s for a small text case after warm load; this is a design budget, not a measured SLO.
- **DESIGN DECISION:** Budget allocation: normalize 50 ms, deterministic facts 50 ms, semantic stage 900 ms, controller/policy 50 ms, persistence/trace 150 ms, UI/network margin 300 ms.
- **DESIGN DECISION:** Cold model load is measured separately and prewarming is optional; an unavailable model routes safely.

## Security

- **DESIGN DECISION:** Evidence is data, never executable instruction; models have no tools, secrets, database credentials or network actions.
- **DESIGN DECISION:** Strict MIME/size/schema allowlists, generated storage names, encryption in transit/at rest, least-privilege service identities and tenant scoping are production requirements.
- **DESIGN DECISION:** Exact evidence may contain PII; access, retention and redaction require policy and threat-model review before production.

