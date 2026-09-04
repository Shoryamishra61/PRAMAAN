import { Fingerprint, ShieldCheck, Sparkle } from "@phosphor-icons/react";
import { useTutorial } from "../tutorial";

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
  const tutorial = useTutorial();
  const tutorialStartTour = tutorial.startTour;

  function handleNav(
    route: NavRoute,
    view?: "debugger" | "evaluation" | "cases",
  ) {
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
        >
          <span className="brand-mark" aria-hidden="true">
            <Fingerprint size={20} />
          </span>
          <span className="brand-title-wrap">
            <strong>PRAMAAN</strong>
            <small>CARVE-FECL Dispute Integrity Gate | Razorpay Track 02</small>
          </span>
        </button>

        <nav className="unified-nav-tabs" aria-label="Primary navigation">
          <button
            type="button"
            data-tour="nav-debugger"
            className={isDebuggerActive ? "active" : ""}
            onClick={() => handleNav("proof", "debugger")}
          >
            Evidence Debugger
          </button>
          <button
            type="button"
            data-tour="nav-queue"
            className={isCasesActive ? "active" : ""}
            onClick={() => handleNav("workspace", "cases")}
          >
            Analyst Queue
          </button>
          <button
            type="button"
            data-tour="nav-evaluation"
            className={isEvalActive ? "active" : ""}
            onClick={() => handleNav("evaluation", "evaluation")}
          >
            Generated evaluation
          </button>
          <button
            type="button"
            data-tour="nav-research"
            className={isResearchActive ? "active" : ""}
            onClick={() => handleNav("research")}
          >
            CARVE Research
          </button>
          <button
            type="button"
            data-tour="nav-decision-engine"
            className={isDecisionActive ? "active" : ""}
            onClick={() => handleNav("decision-engine")}
          >
            Decision Engine
          </button>
        </nav>

        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
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
            title="Launch interactive element-level tutorial"
            aria-label="Launch interactive product tutorial"
          >
            <Sparkle size={14} aria-hidden="true" />
            <span>Interactive Guide</span>
          </button>

          <div className="unified-nav-badge">
            <ShieldCheck size={16} aria-hidden="true" />
            <span>OFFLINE REPLAY | ZERO WRITES | Z3 SMT</span>
          </div>
        </div>
      </div>
    </header>
  );
}
