# Local runbook

The demo runtime is fully local and uses a versioned, precomputed regex fixture cache. It makes no model-provider or Razorpay write calls. The three bundled cases and any evaluation dataset are synthetic.

## Fresh Windows checkout

Prerequisites: Python 3.10+ and Node.js/npm.

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup.ps1
powershell -ExecutionPolicy Bypass -File scripts/check.ps1
powershell -ExecutionPolicy Bypass -File scripts/demo.ps1
```

Open `http://127.0.0.1:5173`. The queue contains demonstrable PASS, REVIEW, and BLOCK cases produced from signed Razorpay-compatible webhook fixtures through the offline extraction, grounding, deterministic verification, and policy path.

Stop the two recorded local processes with:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/stop-demo.ps1
```

## Reproducibility boundaries

- `scripts/setup.ps1` may need package-registry access for the initial dependency install. The running demo requires no external service.
- `scripts/demo.ps1` resets only the exact ignored path `var/demo.sqlite3`; its seed function refuses to overwrite other database paths.
- The webhook secret is a synthetic demo-only value, not a Razorpay credential.
- UI state changes are local. No accept, contest, refund, or payment write path exists.
- `scripts/check.ps1` runs formatting checks, lint, strict Python/TypeScript checks, security/static guards, backend tests, the frontend production build, and frontend tests.
- Development commands never load the frozen HOLDOUT. The final holdout runner requires a separate explicit confirmation.
