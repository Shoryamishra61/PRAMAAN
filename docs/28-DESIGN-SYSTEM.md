# 28 — Interface design system

## Direction

CARVE uses a restrained financial-ledger visual language: warm paper, high-contrast ink, one dark
green action color, amber for REVIEW, and red only for proven BLOCK conditions. Decorative model
scores and unrelated dashboard ornament are prohibited.

## Shared tokens

The canonical implementation lives in `frontend/src/styles.css`.

- Body type: Aptos with Segoe UI and system fallbacks.
- Display type: Georgia with Times fallback.
- Technical type: Cascadia Mono with IBM Plex Mono and Consolas fallbacks.
- Paper: `#f4f1e9`; surface: `#fffefa`; ink: `#17211d`; muted ink: `#5d6962`.
- Action: `#174d35`; REVIEW: `#755600`; BLOCK: `#983334`.
- Control radius: 4 px; panel radius: 6 px; focus ring: 3 px blue with 2 px offset.
- Minimum interactive height: 44 px. Numeric comparisons use tabular figures.

`proof-console.css` and `carve-research.css` alias these tokens inside their own roots. They may
change composition and density, but must not redefine the product palette or typography globally.

## Component rules

- Actions use buttons; navigation uses links or route-aware navigation controls.
- Every input has a visible label, stable `name`, suitable input mode, and bounded value.
- Primary actions use solid green. Secondary actions use a bordered surface. Quiet actions are
  text-only and never carry the only path out of an error.
- PASS, REVIEW, and BLOCK always use text plus shape/icon; color is supporting information.
- Errors explain the next action. Loading states use live-region semantics and an ellipsis.
- Tables place units in headers or labels, align numeric columns right, and permit horizontal
  scrolling inside a labelled region on narrow screens.
- Technical identifiers, hashes, and raw constraints stay available through progressive disclosure.

## Responsive behavior

- 320–559 px: one-column content, full-width controls, scrollable tables, no fixed side panels.
- 560–899 px: compact two-column groups where labels remain readable.
- 900 px and above: multi-column evidence comparison and research tables.
- Reduced-motion preferences disable non-essential motion. Keyboard focus must never be hidden by
  sticky navigation.
