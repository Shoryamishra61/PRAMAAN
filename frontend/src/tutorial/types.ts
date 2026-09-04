export type RequiredActionType =
  "click" | "upload" | "submit" | "tab" | "observe" | "repair";

export type PopoverPlacement = "top" | "bottom" | "left" | "right" | "auto";

export interface TutorialAppContext {
  route: string;
  journeyStep: number;
  hasFiles: boolean;
  fileCount: number;
  hasResult: boolean;
  isEvaluating: boolean;
  resultVerdict: "BLOCK" | "REVIEW" | "PASS" | null;
  hasRepaired: boolean;
  selectedScenario: string | null;
  evaluationView: "debugger" | "evaluation";
  activeTab: string;
}

export interface GuidedTourStep {
  id: string;
  stepIndex: number;
  title: string;
  targetSelector: string;
  fallbackSelector?: string;
  roleExplanation: string;
  actionDirective: string;
  whyItMatters: string;
  requiredAction: RequiredActionType;
  preferredPlacement?: PopoverPlacement;
  hints: string[];
  isSatisfied: (ctx: TutorialAppContext) => boolean;
  shouldSkip?: (ctx: TutorialAppContext) => boolean;
  getBranchNext?: (ctx: TutorialAppContext) => string | null;
}

export type TutorialAnalyticsEvent =
  | { type: "tour_started" }
  | { type: "step_entered"; stepId: string; stepIndex: number }
  | { type: "step_completed"; stepId: string; durationMs: number }
  | { type: "hint_escalated"; stepId: string; hintLevel: number }
  | { type: "tour_skipped"; stepId: string }
  | { type: "tour_completed"; totalDurationMs: number };
