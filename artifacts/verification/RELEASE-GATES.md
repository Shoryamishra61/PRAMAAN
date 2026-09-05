# Current hardening receipt — 2026-09-05

Status: final automated gate passed on 2026-09-05; rendered UI release gate remains pending.
This receipt supersedes the 2026-08-23 claims for the current working tree. Historical task
receipts are not evidence that the current product was visually verified.

## Changes established in source and focused tests

- One bounded JSON/TXT/CSV ingestion path, full JSON request validation, strict UTF-8 decoding,
  robust CSV quoting, per-file failures and retry, duplicate-name retention, and source offsets.
  Communication never silently becomes authoritative financial state. Oversize input is rejected,
  not truncated. Parsing and evaluation lock case editing to prevent stale results.
- Exact decimal source segmentation, explicit malformed-value normalization failure, and matching
  full refund claims against multiple final ledger records without ignoring specific references.
- Actual backend certificates only; no browser-fabricated proof identifiers or fake phase delays.
  Quant-risk projection endpoint returns 410. Historical metric generators and completion-only
  training wrapper removed; mixed historical results explicitly labeled unverified.
- One restrained light interface system across every active route: flat document sections,
  consistent navigation and buttons, semantic status text, and contextual guidance from real
  errors/results/stages. Hard-coded merchant-economics tiles, decorative model charts, nested
  cards, colored status containers, and the duplicate tutorial launcher were removed.
- The contextual guide now gates progress on the highlighted product action, follows verification
  and journey-stage changes automatically, moves through held-out evidence and model selection,
  and finishes in the analyst queue. Its highlight and panel geometry use short, reduced-motion-
  aware transitions. The evidence form keeps its completeness checkbox beside its label.
- Real PyTorch optimizer/checkpoint smoke and DEV-only local classifier retraining. Learned
  candidate remains unpromoted because it does not beat its simpler comparator.

## Evaluation boundaries

[DEV before/after and reproduction commands](dev-hardening-20260905/README.md): 120 synthetic
cases, false BLOCKs 10 to 0, recall 40/40, REVIEW 40/120. These repairs were developed from DEV
failures; they are not an independent test result. Refund-amount extraction precision remains
56/72. Final illustrative cost scenarios total 40, 120, and 80 units from REVIEW costs; these
are not observed rupee savings or a deployment prevalence estimate.

Saved August HOLDOUT baseline: precision 10/10, recall 10/20, false PASS 10, false BLOCK 0,
REVIEW 20/60. SHA-256 remains
`15349fd24f2fbceb1c6a38edafee92d5953f22af2e9611efcda17ba20f1992b8`.
Current runtime **does not** match `artifacts/release/freeze-v1.json`; verification correctly
raises "Runtime code/config bytes differ from release freeze." No HOLDOUT rerun or silent
promotion was performed. Frontend evaluation copy identifies the historical baseline.

The final Git commit is the source provenance for this receipt. It is not a replacement for the
pre-HOLDOUT freeze.

## Automated verification

`scripts/check.ps1` passed at source revision `bd0b5a0`: 313 backend tests and 38 frontend tests,
Python formatting/linting, mypy across 157 source files, specification/package validation,
write-safety and stale-claim scans, API demo smoke, Prettier, ESLint, TypeScript, and the Vite
production build. The complete output is saved in `dev-hardening-20260905/check-final.log`.
The subsequent frontend-only tour and layout repair reran Prettier, ESLint, TypeScript, the Vite
production build, and all 38 frontend tests; backend source did not change.

## Manual / remaining release gates

- No browser was available: CUA inventory returned no browsers or apps. Desktop/mobile visual
  inspection, full tour traversal, drag/resize behavior, focus visibility, contrast, zoom/reflow,
  and screen-reader behavior remain unverified. Component tests do not establish WCAG compliance.
- No fresh live Razorpay read integration, external merchant-loss validation, new independent
  held-out evaluation, deployed demonstration, or narrated video was established in this pass.
- Synthetic research can justify mechanisms and reveal failures; it cannot establish actual
  merchant savings, production prevalence, or readiness for consequential financial operation.
- FastAPI TestClient emits an upstream Starlette/httpx deprecation warning. It is not suppressed.
