# Web interface audit — CARVE research instrument

Scope: `TryVerifier.tsx`, `ProofConsole.tsx`, `CarveResearchLab.tsx`, and the associated proof/research styles.

## Guided-flow revision

- Replaced simultaneous input/trace/certificate columns with one active step at a time: evidence, grounded claim, payment truth, decision.
- Removed automatic execution on page load and sample selection; the user explicitly chooses `Check this case`.
- Replaced visible machine codes and underscore-heavy labels with plain-language findings. Raw codes remain in a technical drawer.
- Added measured browser-to-local-API elapsed time and an explanation of why lightweight local extraction and deterministic constraints complete in milliseconds. No artificial delay is used.
- Exposed each mechanism with input, operation, output, and authority. Semantic extraction is visibly non-authoritative.
- Kept research details and generated evaluation outside the primary beginner journey.
- Replaced research slogans with frozen artifact rows: split sizes, candidate metrics, failure counts, rejection reasons, and allowed authority.
- Added explicit evidence-integrity, corrupted-text, and model-outage injections; each terminates at REVIEW before financial truth can be asserted.

## Passed in source and automated checks

- Native labelled controls are used for evidence entry, file import, sample loading, repair, acquisition, model selection, and view changes.
- Toggle-like model controls expose `aria-pressed`; decorative chart and icon content is hidden from assistive technology.
- Decision updates use live-region semantics and pending work exposes busy state.
- Exact-evidence findings are keyboard-operable and focus the originating source span.
- File import is local-only, named, and accepts bounded JSON/TXT evidence.
- URL state reflects the selected research/evaluation view.
- Focus-visible styling, reduced-motion handling, and responsive breakpoints are present.
- Production build, zero-warning lint, 12 frontend interaction tests, and 12 targeted backend tests pass.

## Blocked visual checks

- Browser discovery returned no connected runtime, so screenshots, rendered overflow checks, visual contrast inspection, and mobile tab-order verification remain unclaimed.
- See `design-qa.md` for the exact rerun protocol and required desktop/mobile states.

## Release position

The instrument is code- and interaction-verified. Browser-rendered design QA remains a named pre-release gate, not a silently assumed pass.
