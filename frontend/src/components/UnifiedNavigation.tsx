import { Info } from "@phosphor-icons/react";
import { useTutorialActions } from "../tutorial";

export type NavRoute =
  | "proof"
  | "workspace"
  | "evaluation"
  | "research"
  | "decision-engine"
  | "ai"
  | "walkthrough";

interface UnifiedNavigationProps {
  currentRoute: NavRoute | string;
  currentView?: "debugger" | "evaluation" | "cases";
  onNavigate?: (
    route: NavRoute,
    view?: "debugger" | "evaluation" | "cases",
  ) => void;
}

export function UnifiedNavigation({
  currentRoute,
  currentView = "debugger",
  onNavigate,
}: UnifiedNavigationProps) {
  const tutorial = useTutorialActions();
  const tutorialStartTour = tutorial.startTour;

  function handleNav(
    route: NavRoute,
    view?: "debugger" | "evaluation" | "cases",
  ) {
    tutorial.notifyAction("tab", route);
    if (route === "proof" && view === "debugger") {
      tutorial.notifyAction("tab", "debugger");
    }
    if (onNavigate) {
      onNavigate(route, view);
    } else {
      if (route === "proof" && view === "evaluation") {
        window.location.href = "/evaluation";
      } else if (route === "proof") {
        window.location.href = "/proof";
      } else if (route === "workspace") {
        window.location.href = "/workspace";
      } else if (route === "evaluation") {
        window.location.href = "/evaluation";
      } else if (route === "research") {
        window.location.href = "/research";
      } else if (route === "decision-engine" || route === "ai") {
        window.location.href = "/decision-engine";
      } else if (route === "walkthrough") {
        window.location.href = "/walkthrough";
      }
    }
  }

  const isDebuggerActive =
    (currentRoute === "proof" && currentView !== "evaluation") ||
    currentRoute === "debugger";
  const isCasesActive =
    (currentRoute === "workspace" && currentView !== "evaluation") ||
    currentView === "cases";
  const isEvalActive =
    currentRoute === "evaluation" ||
    (currentRoute === "proof" && currentView === "evaluation") ||
    (currentRoute === "workspace" && currentView === "evaluation");
  const isResearchActive = currentRoute === "research";
  const isDecisionActive =
    currentRoute === "decision-engine" || currentRoute === "ai";

  return (
    <header className="unified-nav" aria-label="Global application navigation">
      <div className="unified-nav-inner">
        <button
          type="button"
          className="unified-brand"
          onClick={() => handleNav("proof", "debugger")}
          aria-label="PRAMAAN Dispute Integrity Gate"
        >
          <span className="brand-title-wrap">
            <span className="brand-main-line">
              <strong>PRAMAAN</strong>
            </span>
            <small>Refund evidence verification</small>
          </span>
        </button>

        <nav className="unified-nav-tabs" aria-label="Primary navigation">
          <button
            type="button"
            data-tour="nav-debugger"
            aria-current={isDebuggerActive ? "page" : undefined}
            className={isDebuggerActive ? "active" : ""}
            onClick={() => handleNav("proof", "debugger")}
          >
            Evidence Debugger
          </button>
          <button
            type="button"
            data-tour="nav-queue"
            aria-current={isCasesActive ? "page" : undefined}
            className={isCasesActive ? "active" : ""}
            onClick={() => handleNav("workspace", "cases")}
          >
            Analyst Queue
          </button>
          <button
            type="button"
            data-tour="nav-evaluation"
            aria-current={isEvalActive ? "page" : undefined}
            className={isEvalActive ? "active" : ""}
            onClick={() => handleNav("evaluation", "evaluation")}
          >
            Evaluation
          </button>
          <button
            type="button"
            data-tour="nav-research"
            aria-current={isResearchActive ? "page" : undefined}
            className={isResearchActive ? "active" : ""}
            onClick={() => handleNav("research")}
          >
            Research
          </button>
          <button
            type="button"
            data-tour="nav-decision-engine"
            aria-current={isDecisionActive ? "page" : undefined}
            className={isDecisionActive ? "active" : ""}
            onClick={() => handleNav("decision-engine")}
          >
            Decision Engine
          </button>
        </nav>

        <div className="unified-nav-actions">
          <button
            type="button"
            className="tour-nav-launch-btn"
            data-tour="launch-tour-btn"
            onClick={() => {
              if (currentRoute !== "proof") {
                handleNav("proof", "debugger");
              }
              if (tutorialStartTour) {
                tutorialStartTour();
              }
            }}
            title="Open contextual guide"
            aria-label="Open contextual guide"
          >
            <Info size={14} aria-hidden="true" />
            <span>Guide</span>
          </button>

          <div className="unified-nav-badge">
            <span>Local demo · Synthetic evidence</span>
          </div>
        </div>
      </div>
    </header>
  );
}
