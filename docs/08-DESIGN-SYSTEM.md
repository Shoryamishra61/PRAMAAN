# 08 — Design System

## Intent
A compact, serious financial-operations interface. Avoid “AI dashboard” visual tropes: gradients, glowing orbs, trust scores, animated agents, giant metric cards.

## Foundations

### Typography
Use system fonts by default to reduce setup risk.
- UI: `Inter, ui-sans-serif, system-ui, sans-serif` if Inter is already bundled; otherwise system stack.
- monospace: `ui-monospace, SFMono-Regular, Menlo, Consolas, monospace`.

Recommended scale:
- page title: 20/28
- section title: 16/24
- body: 14/20
- dense metadata: 12/18
Do not shrink primary evidence text below comfortable reading size merely for density.

### Spacing
4px base rhythm:
`4, 8, 12, 16, 24, 32`.

### Surfaces
Use clear borders and restrained elevation. Evidence/document boundaries should be visually obvious.

## Semantic states
State must be represented by:
- text;
- icon;
- color.

Tokens must be checked with automated/manual contrast testing during implementation; this spec does not claim hardcoded contrast ratios.

Suggested semantic names:
- `status-pass`
- `status-review`
- `status-block`
- `status-processing`
- `status-error`

## Component inventory
- AppShell
- QueueTable
- QueueRow
- StatusBadge
- DeadlineBadge
- CaseHeader
- EvidenceList
- EvidenceViewer
- SourceQuoteHighlight
- FindingCard
- StructuredStateCard
- ReviewReasonPanel
- LocalHoldPanel
- OverrideDialog
- AuditTimeline
- EvaluationSummary
- ConfusionMatrix
- SliceMetricsTable
- OfflineReplayBadge

## Prohibited components
- AI confidence gauge without validated probability;
- win probability;
- “trust score”;
- chat panel;
- autonomous agent activity theatre;
- fake network health if not backed by runtime status;
- auto-submit button.

## Content style
Prefer:
- “No matching processed refund was found in the complete fixture ledger.”
Avoid:
- “AI is 94% sure merchant never refunded.”
- “This dispute is fraudulent.”
- “This representment is legally invalid.”

## Responsive rule
Desktop-first, but usable at ~1280px width.
At narrower widths:
1. collapse queue;
2. preserve evidence + finding comparison;
3. never shrink source text into unreadable columns.

## Implementation accessibility checklist
- all icon buttons have accessible names;
- focus order follows visual/task order;
- dialogs return focus to invoking control;
- table rows can be selected without mouse;
- source quotes reachable via links/buttons;
- error text associated with controls;
- state not conveyed by color alone.
