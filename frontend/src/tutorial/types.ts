export type RequiredActionType =
  "click" | "upload" | "submit" | "tab" | "observe" | "repair";

export type TourMachineStatus =
  | "IDLE"
  | "STARTING"
  | "ACTIVE"
  | "WAITING_FOR_TARGET"
  | "TRANSITIONING"
  | "PAUSED"
  | "COMPLETED"
  | "CANCELLED"
  | "ERROR";

export type TourMachineEvent =
  | "START"
  | "BEGIN_STEP"
  | "TARGET_READY"
  | "TARGET_MISSING"
  | "NEXT"
  | "BACK"
  | "PAUSE"
  | "RESUME"
  | "COMPLETE"
  | "CANCEL"
  | "FAIL"
  | "RESET";

export type TourPanelSize = "compact" | "standard" | "expanded";
export type TourPlacement =
  | "auto"
  | "top-left"
  | "top-right"
  | "bottom-left"
  | "bottom-right"
  | "side-center";
export type ResolvedTourPlacement = Exclude<TourPlacement, "auto">;
export type TourTargetStatus =
  "idle" | "resolving" | "primary" | "fallback" | "missing";

export interface TutorialAppContext {
  route: string;
  journeyStep: number;
  inputError?: string | null;
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
  kind: "welcome" | "workflow";
  title: string;
  route: string;
  targetSelector: string | null;
  fallbackSelector?: string;
  summary: string;
  actionDirective: string;
  whyItMatters: string;
  requiredAction: RequiredActionType;
  hints: readonly string[];
  isSatisfied: (context: TutorialAppContext) => boolean;
}

export type TutorialAnalyticsEvent =
  | { type: "tour_started" }
  | { type: "step_entered"; stepId: string; workflowNumber: number | null }
  | { type: "step_completed"; stepId: string; durationMs: number }
  | { type: "target_missing"; stepId: string }
  | { type: "hint_escalated"; stepId: string; hintLevel: number }
  | { type: "tour_cancelled"; stepId: string }
  | { type: "tour_completed"; totalDurationMs: number };
