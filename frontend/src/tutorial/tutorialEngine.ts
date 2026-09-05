import type {
  GuidedTourStep,
  TutorialAppContext,
  ResolvedTourPlacement,
  TourMachineEvent,
  TourMachineStatus,
  TutorialAnalyticsEvent,
} from "./types";

export const TUTORIAL_STORAGE_KEY = "pramaan.tour.state.v3";
export const TUTORIAL_SESSION_KEY = "pramaan.tour.preferences.v1";
export const TUTORIAL_ANALYTICS_KEY = "pramaan.tour.telemetry.v3";
export const TARGET_RESOLUTION_TIMEOUT_MS = 1_800;

export const TOUR_TARGETS = {
  hero: '[data-tour="verifier-hero"]',
  scenarios: '[data-tour="sample-pills"]',
  evidenceDropzone: '[data-tour="evidence-dropzone"]',
  runVerification: '[data-tour="check-case-btn"]',
  extractedClaim: '[data-tour="extracted-claim-box"]',
  financialState: '[data-tour="truth-layer"]',
  inspectFinancialState: '[data-tour="step2-next-btn"]',
  inspectDecision: '[data-tour="step3-next-btn"]',
  verdict: '[data-tour="verdict-banner"]',
  evaluation: '[data-tour="metrics-summary"]',
  decisionEngine: '[data-tour="decision-engine"]',
  debuggerNavigation: '[data-tour="nav-debugger"]',
} as const;

export const TUTORIAL_STEPS: readonly GuidedTourStep[] = [
  {
    id: "welcome",
    kind: "welcome",
    title: "Trace one dispute from evidence to a bounded decision",
    route: "proof",
    targetSelector: null,
    summary:
      "PRAMAAN is the defensive product. CARVE-FECL is its research engine for testing evidence, models, calibration, and formal financial invariants without granting a model payment authority.",
    actionDirective:
      "Start the walkthrough, or skip it and use every screen directly.",
    whyItMatters:
      "A reviewer should be able to trace source evidence, deterministic findings, uncertainty, and the local decision without trusting a score or hidden automation.",
    requiredAction: "click",
    hints: ["Select Start to begin with the editable case intake."],
    isSatisfied: () => false,
  },
  {
    id: "case-intake",
    kind: "workflow",
    title: "Case intake and scenario scope",
    route: "proof",
    targetSelector: TOUR_TARGETS.scenarios,
    fallbackSelector: TOUR_TARGETS.hero,
    summary:
      "Choose a bounded synthetic scenario or keep the default wrong-amount case. Sample labels describe expected test behavior, not production prevalence.",
    actionDirective:
      "Choose a scenario to load its communication and structured refund state. Next is always available.",
    whyItMatters:
      "Explicit scope prevents unsupported evidence or reason codes from being treated as verified.",
    requiredAction: "click",
    hints: ["The scenario controls are below the evidence dropzone."],
    isSatisfied: (context) => context.selectedScenario !== null,
  },
  {
    id: "evidence-requirements",
    kind: "workflow",
    title: "Evidence requirements",
    route: "proof",
    targetSelector: TOUR_TARGETS.evidenceDropzone,
    fallbackSelector: TOUR_TARGETS.scenarios,
    summary:
      "Communication can support a grounded claim; only the structured payment and refund ledger can establish financial state. Missing or malformed authoritative evidence must abstain to REVIEW.",
    actionDirective:
      "Optionally import bounded JSON, TXT, or CSV evidence, then continue.",
    whyItMatters:
      "Separating narrative evidence from authoritative state prevents fluent text from becoming financial truth.",
    requiredAction: "upload",
    hints: [
      "You can continue with the loaded synthetic sample; upload is optional.",
    ],
    isSatisfied: (context) => context.hasFiles,
  },
  {
    id: "evidence-ingestion",
    kind: "workflow",
    title: "Evidence ingestion and normalization",
    route: "proof",
    targetSelector: TOUR_TARGETS.runVerification,
    fallbackSelector: TOUR_TARGETS.evidenceDropzone,
    summary:
      "The sandbox validates bounded input and exact two-decimal INR strings before running the real local extraction, grounding, reconciliation, and decision-policy path.",
    actionDirective:
      "Run Check this case, or continue to inspect the contract first.",
    whyItMatters:
      "Invalid money precision or unsupported input is rejected instead of being rounded or silently dropped.",
    requiredAction: "submit",
    hints: ["Check this case is the primary action below the evidence fields."],
    isSatisfied: (context) => context.isEvaluating || context.hasResult,
  },
  {
    id: "semantic-grounding",
    kind: "workflow",
    title: "Semantic extraction and exact grounding",
    route: "proof",
    targetSelector: TOUR_TARGETS.extractedClaim,
    fallbackSelector: TOUR_TARGETS.runVerification,
    summary:
      "The replaceable semantic layer may nominate a typed claim only when its exact source quotation can be located unambiguously. It never decides PASS, REVIEW, or BLOCK.",
    actionDirective:
      "Run the case if needed, then inspect the exact quote and its source boundary.",
    whyItMatters:
      "Exact spans make hallucinated or ambiguous claims unable to influence the deterministic policy.",
    requiredAction: "observe",
    hints: [
      "After a run, the grounded quote appears in the second journey stage.",
    ],
    isSatisfied: (context) => context.hasResult && context.journeyStep >= 2,
  },
  {
    id: "financial-state",
    kind: "workflow",
    title: "Authoritative financial state",
    route: "proof",
    targetSelector: TOUR_TARGETS.inspectFinancialState,
    fallbackSelector: TOUR_TARGETS.financialState,
    summary:
      "The normalized claim is compared with complete structured refund state using integer minor units and explicit ledger completeness.",
    actionDirective:
      "Open Check payment truth when available, or use Next to continue.",
    whyItMatters:
      "Narrative text cannot override the ledger, and an incomplete ledger cannot prove absence.",
    requiredAction: "tab",
    hints: [
      "Check payment truth advances the case journey without changing external state.",
    ],
    isSatisfied: (context) => context.journeyStep >= 3,
  },
  {
    id: "formal-verification",
    kind: "workflow",
    title: "Formal verification and abstention",
    route: "proof",
    targetSelector: TOUR_TARGETS.inspectDecision,
    fallbackSelector: TOUR_TARGETS.financialState,
    summary:
      "PRAMAAN evaluates deterministic compiled constraints. CARVE-FECL separately cross-checks supported invariant families with a bounded Z3 solver; timeout or unknown is never treated as SAT.",
    actionDirective:
      "Inspect the compiled constraints, then open See the decision or continue.",
    whyItMatters:
      "A technical failure must remain visible and route to human review rather than silently becoming contest-ready.",
    requiredAction: "tab",
    hints: [
      "Constraint details identify their evidence layer and resolved state.",
    ],
    isSatisfied: (context) => context.journeyStep >= 4,
  },
  {
    id: "risk-evaluation",
    kind: "workflow",
    title: "Artifact-backed risk and uncertainty",
    route: "evaluation",
    targetSelector: TOUR_TARGETS.evaluation,
    fallbackSelector: TOUR_TARGETS.debuggerNavigation,
    summary:
      "The evaluation screen reads digest-verified saved artifacts. Counts, slices, calibration, and false-pass cost assumptions remain labeled synthetic and are never hard-coded into the tour.",
    actionDirective:
      "Inspect the dataset identity and exact numerators before trusting any metric.",
    whyItMatters:
      "Model selection is defensible only when splits, artifacts, uncertainty, and negative results remain reproducible.",
    requiredAction: "observe",
    hints: [
      "The route changes automatically; loading and missing-artifact states remain usable.",
    ],
    isSatisfied: (context) => context.route === "evaluation",
  },
  {
    id: "decision-provenance",
    kind: "workflow",
    title: "Final decision, provenance, and human authority",
    route: "decision-engine",
    targetSelector: TOUR_TARGETS.decisionEngine,
    fallbackSelector: TOUR_TARGETS.debuggerNavigation,
    summary:
      "The Decision Engine exposes retained and rejected research candidates while deterministic evidence rules and human review keep authority. No Razorpay write path exists.",
    actionDirective:
      "Finish the tour. You can return to the Evidence Debugger from global navigation.",
    whyItMatters:
      "A defensible fintech system shows why a decision happened, what failed, which artifact was used, and who still owns the next action.",
    requiredAction: "observe",
    hints: [
      "Finish records completion locally; it does not submit or mutate a dispute.",
    ],
    isSatisfied: (context) => context.route === "decision-engine",
  },
] as const;

export const WORKFLOW_STEP_COUNT = TUTORIAL_STEPS.filter(
  (step) => step.kind === "workflow",
).length;

const TRANSITIONS: Record<
  TourMachineStatus,
  Partial<Record<TourMachineEvent, TourMachineStatus>>
> = {
  IDLE: { START: "STARTING", RESET: "IDLE" },
  STARTING: {
    START: "STARTING",
    BEGIN_STEP: "WAITING_FOR_TARGET",
    TARGET_READY: "ACTIVE",
    TARGET_MISSING: "ACTIVE",
    COMPLETE: "COMPLETED",
    CANCEL: "CANCELLED",
    FAIL: "ERROR",
  },
  ACTIVE: {
    START: "STARTING",
    NEXT: "TRANSITIONING",
    BACK: "TRANSITIONING",
    BEGIN_STEP: "WAITING_FOR_TARGET",
    PAUSE: "PAUSED",
    COMPLETE: "COMPLETED",
    CANCEL: "CANCELLED",
    FAIL: "ERROR",
  },
  WAITING_FOR_TARGET: {
    START: "STARTING",
    TARGET_READY: "ACTIVE",
    TARGET_MISSING: "ACTIVE",
    NEXT: "TRANSITIONING",
    BACK: "TRANSITIONING",
    PAUSE: "PAUSED",
    COMPLETE: "COMPLETED",
    CANCEL: "CANCELLED",
    FAIL: "ERROR",
  },
  TRANSITIONING: {
    START: "STARTING",
    BEGIN_STEP: "WAITING_FOR_TARGET",
    TARGET_READY: "ACTIVE",
    TARGET_MISSING: "ACTIVE",
    COMPLETE: "COMPLETED",
    CANCEL: "CANCELLED",
    FAIL: "ERROR",
  },
  PAUSED: {
    START: "STARTING",
    RESUME: "WAITING_FOR_TARGET",
    COMPLETE: "COMPLETED",
    CANCEL: "CANCELLED",
  },
  COMPLETED: { START: "STARTING", RESET: "IDLE" },
  CANCELLED: { START: "STARTING", RESET: "IDLE" },
  ERROR: { START: "STARTING", RESET: "IDLE", CANCEL: "CANCELLED" },
};

export function transitionTourStatus(
  status: TourMachineStatus,
  event: TourMachineEvent,
): TourMachineStatus {
  return TRANSITIONS[status][event] ?? status;
}

export function workflowNumberForIndex(index: number): number | null {
  if (TUTORIAL_STEPS[index]?.kind !== "workflow") return null;
  return TUTORIAL_STEPS.slice(0, index + 1).filter(
    (step) => step.kind === "workflow",
  ).length;
}

type Rect = Pick<
  DOMRect,
  "left" | "right" | "top" | "bottom" | "width" | "height"
>;

function overlapArea(a: Rect, b: Rect): number {
  return (
    Math.max(0, Math.min(a.right, b.right) - Math.max(a.left, b.left)) *
    Math.max(0, Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top))
  );
}

export function tourPanelCoordinates(
  placement: ResolvedTourPlacement,
  target: Rect | null,
  viewportWidth: number,
  viewportHeight: number,
  panelWidth: number,
  panelHeight: number,
  margin = 16,
): { left: number; top: number } {
  const right = Math.max(margin, viewportWidth - panelWidth - margin);
  const bottom = Math.max(margin, viewportHeight - panelHeight - margin);
  if (placement === "top-left") return { left: margin, top: margin };
  if (placement === "top-right") return { left: right, top: margin };
  if (placement === "bottom-left") return { left: margin, top: bottom };
  if (placement === "bottom-right") return { left: right, top: bottom };
  const targetOnLeft = target
    ? target.left + target.width / 2 < viewportWidth / 2
    : true;
  return {
    left: targetOnLeft ? right : margin,
    top: Math.max(
      margin,
      Math.min(
        bottom,
        (target?.top ?? viewportHeight / 2) +
          (target?.height ?? 0) / 2 -
          panelHeight / 2,
      ),
    ),
  };
}

export function chooseTourPlacement(
  target: Rect | null,
  viewportWidth: number,
  viewportHeight: number,
  panelWidth: number,
  panelHeight: number,
): ResolvedTourPlacement {
  if (!target) return "bottom-right";
  const choices: readonly ResolvedTourPlacement[] = [
    "top-left",
    "top-right",
    "bottom-left",
    "bottom-right",
    "side-center",
  ];
  const targetCenterX = target.left + target.width / 2;
  const targetCenterY = target.top + target.height / 2;
  return choices.reduce(
    (best, placement) => {
      const point = tourPanelCoordinates(
        placement,
        target,
        viewportWidth,
        viewportHeight,
        panelWidth,
        panelHeight,
      );
      const candidate = {
        left: point.left,
        top: point.top,
        right: point.left + panelWidth,
        bottom: point.top + panelHeight,
        width: panelWidth,
        height: panelHeight,
      };
      const distance = Math.hypot(
        point.left + panelWidth / 2 - targetCenterX,
        point.top + panelHeight / 2 - targetCenterY,
      );
      const score = overlapArea(candidate, target) * 1_000 - distance;
      return score < best.score ? { placement, score } : best;
    },
    { placement: choices[0], score: Number.POSITIVE_INFINITY },
  ).placement;
}

export function emitTutorialAnalytics(event: TutorialAnalyticsEvent): void {
  try {
    const parsed = JSON.parse(
      localStorage.getItem(TUTORIAL_ANALYTICS_KEY) ?? "[]",
    );
    const history = Array.isArray(parsed) ? parsed : [];
    history.push({ ...event, timestamp: new Date().toISOString() });
    localStorage.setItem(
      TUTORIAL_ANALYTICS_KEY,
      JSON.stringify(history.slice(-100)),
    );
  } catch {
    // Telemetry is local, bounded, optional, and contains no evidence or identifiers.
  }
}

/** Explain observed local state; this guide has no model or decision authority. */
export function contextualTourGuidance(
  context: TutorialAppContext,
): string | null {
  if (context.route !== "proof") return null;
  if (context.inputError)
    return `The case needs input repair: ${context.inputError}`;
  if (context.isEvaluating)
    return "The local verifier is running. Your evidence is retained; the decision will appear when the request completes.";
  if (context.hasResult) {
    if (context.resultVerdict === "BLOCK")
      return "This case has a local hold. Inspect the cited quote and refund record, then repair the conflicting evidence. BLOCK is not a fraud accusation.";
    if (context.resultVerdict === "REVIEW")
      return "This case needs review. Inspect the stated missing evidence or extraction failure; add the required source and check again.";
    if (context.resultVerdict === "PASS")
      return "No supported integrity issue was detected. Inspect the evidence before a human decides the next step; PASS does not predict a dispute win.";
  }
  if (context.hasFiles)
    return `${context.fileCount} local file${context.fileCount === 1 ? " is" : "s are"} staged. Open each source, confirm the financial fields, then check the case. Text and CSV never establish ledger completeness.`;
  return null;
}
