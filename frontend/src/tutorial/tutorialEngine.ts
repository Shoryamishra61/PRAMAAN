import {
  type GuidedTourStep,
  type TutorialAppContext,
  type TutorialAnalyticsEvent,
} from "./types";

export const TUTORIAL_STORAGE_KEY = "pramaan_interactive_tutorial_v2";
export const TUTORIAL_COMPLETED_KEY = "pramaan_tutorial_completed_v2";

export const TUTORIAL_STEPS: GuidedTourStep[] = [
  {
    id: "step-welcome",
    stepIndex: 1,
    title: "PRAMAAN AI Risk Manager: Dispute Integrity Gate",
    targetSelector: '[data-tour="verifier-hero"]',
    roleExplanation:
      "When dispute chargebacks arrive, merchants lose money by contesting unwinnable claims or missing valid evidence. PRAMAAN verifies evidence deterministically before mounting any contest.",
    actionDirective:
      "Click 'Start Guided Walkthrough' to begin the interactive verification workflow.",
    whyItMatters:
      "Blind dispute contests incur card network penalties and merchant fees. Pre-contest verification prevents guaranteed financial losses.",
    requiredAction: "click",
    preferredPlacement: "bottom",
    hints: [
      "Click the 'Start Guided Walkthrough' button in this guidance card to begin.",
      "The tutorial will guide you step-by-step through ingesting, analyzing, and repairing evidence.",
    ],
    isSatisfied: () => false, // Advanced by clicking Start button
  },
  {
    id: "step-select-sample",
    stepIndex: 2,
    title: "Step 1: Evidence Ingestion & Test Scenario",
    targetSelector: '[data-tour="sample-pill-wrong-amount"]',
    fallbackSelector: '[data-tour="evidence-dropzone"]',
    roleExplanation:
      "In a real workflow, you drag-and-drop multiple customer emails, order invoices, and bank statements into the dropzone. For this walkthrough, we will test a case where the customer communication contradicts the refund ledger.",
    actionDirective:
      "Click the highlighted 'Wrong refund amount' scenario button to load the test case.",
    whyItMatters:
      "Multi-document disputes contain inconsistent claims. Robust systems isolate file parsing errors and normalize amounts for verification.",
    requiredAction: "click",
    preferredPlacement: "bottom",
    hints: [
      "Click the highlighted 'Wrong refund amount' button below.",
      "You can also drag and drop any JSON evidence file into the Evidence Dropzone.",
    ],
    isSatisfied: (ctx: TutorialAppContext) =>
      ctx.selectedScenario === "wrong_amount" || ctx.hasFiles,
    shouldSkip: (ctx: TutorialAppContext) =>
      ctx.hasResult && ctx.journeyStep > 1,
  },
  {
    id: "step-run-verification",
    stepIndex: 3,
    title: "Step 2: Execute SMT Financial Logic Solver",
    targetSelector: '[data-tour="check-case-btn"]',
    roleExplanation:
      "Instead of letting a generative LLM guess whether a refund occurred, PRAMAAN compiles financial rules into formal Z3 SMT arithmetic constraints. It executes offline in sub-30ms with zero network writes.",
    actionDirective:
      "Click 'Check this case' to run the formal verification engine on this evidence.",
    whyItMatters:
      "Financial risk systems require mathematical certitude. Automated AI must never guess on payment balances.",
    requiredAction: "submit",
    preferredPlacement: "top",
    hints: [
      "Click the blue 'Check this case' button highlighted below.",
      "The engine will run locally and extract grounded facts without modifying any external records.",
    ],
    isSatisfied: (ctx: TutorialAppContext) => ctx.hasResult || ctx.isEvaluating,
    shouldSkip: (ctx: TutorialAppContext) =>
      ctx.hasResult && ctx.journeyStep > 1,
  },
  {
    id: "step-inspect-claim",
    stepIndex: 4,
    title: "Step 3: Grounded Semantic Claim Span",
    targetSelector: '[data-tour="extracted-claim-box"]',
    fallbackSelector: '[data-tour="step-nav-2"]',
    roleExplanation:
      "Notice the extracted quote: 'Your INR 4,999 refund was processed...'. Every extracted semantic fact is strictly anchored to an exact verbatim quotation in the customer's text to prevent LLM hallucinations.",
    actionDirective:
      "Click the 'Check payment truth' button or navigation tab to examine the authoritative ledger.",
    whyItMatters:
      "Generative models frequently invent amounts and dates. Anchoring every claim to a verbatim text quote ensures full legal and card-network auditability.",
    requiredAction: "tab",
    preferredPlacement: "top",
    hints: [
      "Click the 'Check payment truth' button at the bottom of the card or the tab at the top.",
      "This advances the investigation to compare the claim against the payment ledger.",
    ],
    isSatisfied: (ctx: TutorialAppContext) => ctx.journeyStep >= 3,
  },
  {
    id: "step-smt-truth-layer",
    stepIndex: 5,
    title: "Step 4: Formal SMT Arithmetic Contradiction",
    targetSelector: '[data-tour="truth-layer"]',
    fallbackSelector: '[data-tour="step-nav-3"]',
    roleExplanation:
      "Here is the contradiction: the customer communication claimed ₹4,999, but the authoritative bank ledger records ₹499. The arithmetic inequality is formally unsatisfiable.",
    actionDirective:
      "Click 'See the decision' to view the resulting gate verdict.",
    whyItMatters:
      "Discrepancies between customer communications and bank ledgers are a primary source of merchant chargeback loss.",
    requiredAction: "tab",
    preferredPlacement: "top",
    hints: [
      "Click 'See the decision' button or tab to view the final verdict.",
      "Notice the formal constraint details verifying the ₹4,500 mismatch.",
    ],
    isSatisfied: (ctx: TutorialAppContext) => ctx.journeyStep >= 4,
  },
  {
    id: "step-verdict-analysis",
    stepIndex: 6,
    title:
      "Step 5: Calibrated Verdict: BLOCK (INSUFFICIENT OR CONTRADICTORY EVIDENCE)",
    targetSelector: '[data-tour="verdict-banner"]',
    roleExplanation:
      "The gate returned a BLOCK verdict (INSUFFICIENT OR CONTRADICTORY EVIDENCE). Contesting this dispute with contradictory evidence guarantees a loss and network fines. The gate stops merchant losses locally.",
    actionDirective:
      "Click 'Repair evidence & re-check' to see how the system behaves when the ledger is reconciled.",
    whyItMatters:
      "A defensive gate's most important job is knowing when NOT to contest. Blocking invalid disputes protects merchant chargeback ratios.",
    requiredAction: "repair",
    preferredPlacement: "bottom",
    hints: [
      "Click the highlighted 'Repair evidence & re-check' button.",
      "This updates the refund ledger to ₹4,999 and automatically re-verifies the case.",
    ],
    isSatisfied: (ctx: TutorialAppContext) =>
      ctx.hasRepaired || (ctx.hasResult && ctx.resultVerdict === "PASS"),
  },
  {
    id: "step-repair-pass",
    stepIndex: 7,
    title: "Step 6: Mathematical Proof Satisfied: PASS (CONTEST READY)",
    targetSelector: '[data-tour="verdict-banner"]',
    roleExplanation:
      "The ledger has been reconciled! The customer claim of ₹4,999 now matches the ledger record of ₹4,999. The Z3 solver proved satisfiability, and the gate issues a confident PASS (CONTEST READY) verdict.",
    actionDirective:
      "Click 'Generated evaluation' in the top navigation bar to inspect held-out benchmark metrics.",
    whyItMatters:
      "Merchants should only contest disputes when evidence is mathematically verified and defensible.",
    requiredAction: "tab",
    preferredPlacement: "bottom",
    hints: [
      "Click the 'Generated evaluation' tab in the top navigation bar.",
      "This will take you to the measured benchmark evaluation page.",
    ],
    isSatisfied: (ctx: TutorialAppContext) =>
      ctx.evaluationView === "evaluation" || ctx.route === "evaluation",
  },
  {
    id: "step-heldout-evaluation",
    stepIndex: 8,
    title: "Step 7: Frozen Benchmark Evaluation",
    targetSelector: '[data-tour="nav-decision-engine"]',
    fallbackSelector: '[data-tour="metrics-summary"]',
    roleExplanation:
      "All metrics here are computed on 1,000 synthetic held-out cases with zero decorative counters. We track precision, recall, and false-pass cost explicitly.",
    actionDirective:
      "Click 'Decision Engine' in the top navigation bar to inspect model competition & calibration.",
    whyItMatters:
      "Evaluation artifacts must be reproducible and frozen. Model promotion requires measured safety gains.",
    requiredAction: "tab",
    preferredPlacement: "bottom",
    hints: [
      "Click 'Decision Engine' in the top navigation bar.",
      "You will see the model tournament and risk calibration curves.",
    ],
    isSatisfied: (ctx: TutorialAppContext) =>
      ctx.route === "decision-engine" || ctx.route === "ai",
  },
  {
    id: "step-decision-engine",
    stepIndex: 9,
    title: "Step 8: Full Risk Lifecycle Mastered",
    targetSelector: '[data-tour="nav-debugger"]',
    roleExplanation:
      "You have completed the full PRAMAAN guided tour! You know how to ingest multi-file evidence, run deterministic SMT verification, evaluate held-out benchmarks, and inspect model governance.",
    actionDirective:
      "Click 'Evidence Debugger' to return to interactive testing, or click 'Finish Tutorial' below.",
    whyItMatters:
      "PRAMAAN gives fintech risk teams an unassailable audit trail with zero external writes.",
    requiredAction: "observe",
    preferredPlacement: "bottom",
    hints: [
      "Click 'Evidence Debugger' in the top navigation bar to return to the workbench.",
      "You can re-launch this interactive tour anytime using the top navigation button.",
    ],
    isSatisfied: () => false,
  },
];

export function emitTutorialAnalytics(event: TutorialAnalyticsEvent) {
  try {
    const history = JSON.parse(
      localStorage.getItem("pramaan_tutorial_analytics") || "[]",
    ) as unknown[];
    history.push({ ...event, timestamp: new Date().toISOString() });
    localStorage.setItem(
      "pramaan_tutorial_analytics",
      JSON.stringify(history.slice(-100)),
    );
  } catch {
    // Ignore storage quota or disabled localStorage in sandboxes
  }
}
