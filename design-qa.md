# Design QA — guided CARVE evidence walkthrough

**Source visual truth**

- Superdesign draft `f9423d06-27b3-405f-8368-c21e9c1024a3`, version 3 titled `Dispute Integrity Gate — Guided Forensic Walkthrough`.
- Preview URL: `https://p.superdesign.dev/draft/f9423d06-27b3-405f-8368-c21e9c1024a3`.

**Rendered implementation**

- Intended local route: `http://127.0.0.1:5173/proof`.
- Screenshot path: unavailable in this run.
- Intended viewport: 1440 × 1100 CSS px at DPR 1, plus a 390 × 844 responsive pass.

**State and comparison evidence**

- Intended states: unloaded evidence entry; explicit run into grounded-claim step; authoritative-truth step; plain-language BLOCK/PASS/REVIEW decision; missing-evidence REVIEW before acquisition and BLOCK after authoritative evidence acquisition.
- Full-view comparison: blocked because the browser runtime reported no available in-app or extension browser.
- Focused-region comparison: blocked for the same reason.
- Source pixels and implementation pixels: unavailable; no density-normalized screenshot pair could be captured.

**Verified without visual claims**

- TypeScript/Vite production build passes.
- ESLint passes with zero warnings.
- Twelve frontend interaction tests pass, including explicit run control, guided navigation, downloadable sample loading, proof inspection, repair, and generated evaluation.
- Twelve targeted sandbox and CARVE research API tests pass, including unsupported Hinglish/OOD, evidence-integrity, corrupted-text, and model-outage fail-closed behavior.
- Keyboard semantics use native buttons, links, labels, file input, visible focus styles, `aria-live`, `aria-busy`, and programmatic exact-source focus.
- Responsive layouts are defined for 980 px, 760 px, and 640 px breakpoints, but were not screenshot-verified in this run.

**Findings**

- [P1] Browser-rendered evidence is unavailable.
  Location: `/proof`, desktop and mobile.
  Evidence: browser discovery returned an empty browser list.
  Impact: typography, spacing rhythm, overflow, color contrast appearance, and implementation-to-Superdesign fidelity cannot be honestly passed from code or tests alone.
  Fix: reconnect the in-app browser or browser extension; capture the three primary states at 1440 × 1100 and 390 × 844; inspect console, overflow, focus, download, import, acquisition, and decision-diff states; then compare with the Superdesign source in one combined view.

**Required fidelity surfaces**

- Fonts/typography: implementation tokens inspected; visual fidelity blocked.
- Spacing/layout rhythm: responsive CSS inspected; visual fidelity blocked.
- Colors/tokens: implementation uses the established paper/ink/green/amber/red system; rendered contrast and balance blocked.
- Image/assets: no raster imagery is required; interface icons use the existing Phosphor library.
- Copy/content: API/artifact boundaries and synthetic/sample disclosures are verified by tests.

**Comparison history**

- The prior dense research instrument was refined in place through Superdesign into a single-task, four-step walkthrough with measured timing, plain-language findings, and expandable mechanics.
- The research view now derives split sizes and candidate outcomes from frozen artifacts and shows why failed models have no decision authority.
- No implementation screenshot was available after the refinement, so no P0/P1/P2 visual iteration can be claimed.

**Implementation checklist**

- Re-run browser capture when a browser surface is connected.
- Verify no horizontal overflow at 390 px and 1440 px.
- Verify every sample download and JSON/TXT import visually.
- Verify exact-source focus, missing-evidence acquisition, certificate digest, and before/after diff.
- Check console errors and keyboard tab order.

final result: blocked
