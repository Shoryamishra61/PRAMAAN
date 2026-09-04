# 16 — Security, Privacy & Threat Model

## Security posture
The hackathon system processes synthetic evidence, but its design should demonstrate correct trust boundaries without claiming enterprise compliance.

## Assets
- webhook secret;
- model API credential;
- synthetic dispute/payment/refund state;
- evidence text;
- grounded claims/findings;
- evaluation artifacts;
- audit/review records.

## Trust boundaries
1. Razorpay-compatible webhook → API.
2. API/storage → external model provider.
3. backend → browser.
4. benchmark ground truth → evaluation code (must not leak to runtime).

## Threats & mitigations

### S — Webhook spoofing
Mitigation:
- HMAC-SHA256 over raw body using `X-Razorpay-Signature`. [SRC-RZP-02]
- constant-time comparison.
- reject before business processing.

### T — Duplicate/replay delivery
Razorpay uses at-least-once semantics and documents `x-razorpay-event-id` as unique per event. [SRC-RZP-03]
Mitigation:
- DB unique key;
- idempotent response.

Do not claim HMAC alone prevents replay.

### T — Evidence tampering after ingestion
Mitigation:
- SHA-256 content digest at ingestion;
- re-hash before processing if file-backed.

Claim only: detects byte changes relative to stored digest. It does not establish source authenticity.

### I — Sensitive data to model
MVP uses synthetic data.
If pattern minimization is implemented:
- PAN/email/phone pattern masking is defense in depth;
- do not claim complete anonymization;
- do not mask values needed for case resolution without stable placeholders.

Never claim names are reliably redacted via regex.

### I — Logs
Never log:
- secrets;
- provider keys;
- raw evidence;
- full prompts;
- raw webhook bodies with customer fields.

Use IDs/hashes/structured failure codes.

### D — Provider outage/cost
- timeout;
- bounded retry;
- extraction cache;
- REVIEW fallback;
- offline replay for demo.

### E — Prompt injection
OWASP states prompt injection has no foolproof prompt-only prevention. [SRC-OWASP-01]

Defense:
- model has no tools;
- no secrets;
- no DB/action authority;
- server-defined task/schema;
- segregated untrusted content;
- schema validation;
- exact quote grounding;
- deterministic final policy;
- adversarial tests.

A prompt-injection-looking string is not itself a BLOCK reason. If extraction remains valid, continue; if semantics become unreliable, REVIEW.

### E — IDOR/operator access
MVP is a local single-user demo.
Do not pretend JWT/RBAC production auth exists.
Use a fixed demo operator identity and document production gap.

## Evidence input
MVP avoids arbitrary file upload attack surface by supporting seeded/canonical text/JSON evidence.

If repair import is added:
- allowlist text/plain/application/json;
- size limit;
- application-generated filename;
- storage outside webroot;
- content validation.
OWASP recommends defense in depth for uploads. [SRC-OWASP-02]

Do not add PDF parsing/gVisor merely for “security maturity.”

## SQL
All SQL parameterized.
No model output concatenated into SQL.

## Secrets
- `.env.example` placeholders only;
- real `.env` gitignored;
- fail fast if live provider mode selected without key;
- no “rzp_live_*” example secrets.

## Audit integrity
Optional hash chain:
`hash_i = SHA256(hash_{i-1} || canonical_event_i)`

Threat-model truth:
- detects modification/deletion if attacker does not recompute chain/head;
- a fully privileged attacker able to rewrite all records can recompute a local chain;
- therefore call it tamper-evident, not immutable.

## Compliance language
Do not claim:
- PCI DSS compliance;
- GDPR compliance;
- DPDP compliance;
- certification;
- legal validity.

Allowed:
> “The design applies data minimization, least privilege, auditable actions, and secure webhook validation patterns.”

## Security test minimum
- missing signature;
- wrong signature;
- valid signature;
- duplicate event;
- payload mutation after signature;
- prompt-injection text;
- schema-extraneous output;
- grounding mismatch;
- secret/log redaction;
- SQL injection string in free text;
- offline/provider outage.
