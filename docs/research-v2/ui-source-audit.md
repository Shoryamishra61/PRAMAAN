# UI source audit

**FACT — scope.** This is a source-level review against the Web Interface Guidelines fetched from the upstream Vercel repository on 2026-09-01. It is not a screenshot or pixel audit: the configured in-app browser reported that no browser surface was available. No frontend changes are authorized until the Superdesign branch is approved.

## `frontend/src/App.tsx`

- `frontend/src/App.tsx:1002` — analyst experience starts at `<main>` without a skip link.
- `frontend/src/App.tsx:1017` — product destinations are navigation but use `<button>` and local state; use route links so open-in-new-tab and browser history work.
- `frontend/src/App.tsx:2139` — route state is initialized from the URL but later transitions do not update the URL, so walkthrough, lab, and workspace state are not deep-linkable.
- `frontend/src/App.tsx:384` — override reason control lacks `name` and an explicit non-auth `autoComplete` policy.
- `frontend/src/App.tsx:402` — override note lacks `name` and an explicit non-auth `autoComplete` policy.
- `frontend/src/App.tsx:1677` — modal scroll container lacks `overscroll-behavior: contain` in its corresponding CSS rule.
- `frontend/src/App.tsx:1509` — decorative progress icon is not hidden from assistive technology.
- `frontend/src/App.tsx:1554` — decorative arrow inside a labeled button is not `aria-hidden`.
- `frontend/src/App.tsx:1564` — decorative arrow inside a labeled button is not `aria-hidden`.

## `frontend/src/ProofConsole.tsx`

**FACT — pass.** The proof console has a skip link, semantic navigation controls, hierarchical headings, status/error semantics, and decorative icons marked `aria-hidden`.

## `frontend/src/styles.css`

- `frontend/src/styles.css:1677` — add `overscroll-behavior: contain` to `.override-dialog`.

## Disposition

**DESIGN DECISION — defer.** Apply these mechanical fixes together with the approved evidence-debugger implementation, then run keyboard, reduced-motion, 320 px, 768 px, and desktop visual QA in the user-selected browser. None of these findings changes the frozen evaluation results or the deterministic decision contract.
