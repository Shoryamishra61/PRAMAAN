# 18 — Observability & Failure Recovery

## Objective
Make failures diagnosable and safe without pretending the demo has enterprise observability.

## Correlation model
Every ingest creates:
- `correlation_id`
- `razorpay_event_id`
- `case_id`
- `job_id`

All logs carry whichever IDs are available.

## Structured log events
Examples:
- `webhook.signature_valid`
- `webhook.duplicate`
- `case.created`
- `job.claimed`
- `extract.start`
- `extract.success`
- `extract.failure`
- `grounding.failure`
- `finding.created`
- `decision.created`
- `review.source_inspected`
- `review.override`
- `evaluation.run_complete`

## Log payload policy
Allowed:
- IDs;
- hashes;
- status;
- model/config identifiers;
- measured durations;
- exception class;
- safe error code.

Forbidden:
- raw evidence text;
- secrets;
- full prompts;
- API keys;
- complete raw webhook bodies.

## Job retry classification

### Transient
- provider 429;
- provider 5xx;
- temporary network failure.

Policy:
- bounded retry with backoff;
- after max attempts → REVIEW.

### Permanent
- output schema incompatible;
- unsupported source type;
- quote cannot be grounded;
- incomplete resolver state.

Policy:
- no repeated model retry;
- REVIEW.

### System error
- DB corruption;
- migration mismatch;
- impossible internal invariant.

Policy:
- job FAILED;
- case must not display PASS;
- operator sees system unavailable/retry message.

## Restart recovery
On worker startup:
1. locate `PENDING` jobs;
2. locate `PROCESSING` jobs whose lease expired;
3. requeue safely;
4. avoid duplicating prior committed decisions using idempotent evaluation version keys.

## Health
`/api/v1/health`:
- DB reachable;
- worker heartbeat freshness;
- inference mode configured;
- last successful job time.

No fake “network healthy” state.

## Demo failure injection
At least one visible failure in demo/repo:
- toggle provider unavailable;
- process case;
- show REVIEW;
- show structured log/reason;
- restore provider/offline replay;
- reprocess.

This directly demonstrates safe failure recovery without inventing a bug.

## Metrics
Optional local counters:
- jobs processed;
- jobs failed;
- review reasons;
- extraction cache hit;
- provider calls;
- webhook duplicates.

Do not build Prometheus/Grafana unless already trivial and judge-visible.

## Failure narrative source
Submission story should prefer:
1. a genuine bug discovered during build, with regression test;
2. otherwise a clearly labeled intentional fault injection and resulting engineering improvement.

Never manufacture “15% signatures failed” or similar history.
