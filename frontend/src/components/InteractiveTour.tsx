import { useState, useEffect, useRef } from "react";
import {
  Sparkle,
  ArrowRight,
  ArrowLeft,
  X,
  CheckCircle,
  WarningCircle,
  Lightbulb,
} from "@phosphor-icons/react";

export interface TourStep {
  id: string;
  stepNumber: number;
  title: string;
  subtitle: string;
  instructions: string;
  whyItMatters: string;
  targetSelector?: string;
  requiredAction?: {
    description: string;
    isSatisfied: () => boolean;
  };
}

interface InteractiveTourProps {
  isOpen: boolean;
  onClose: () => void;
  onNavigateTab?: (tab: string) => void;
  hasFiles: boolean;
  hasResult: boolean;
  hasCheckedCase: boolean;
  currentJourneyStep: number;
}

export function InteractiveTour({
  isOpen,
  onClose,
  onNavigateTab,
  hasFiles,
  hasResult,
  hasCheckedCase,
  currentJourneyStep,
}: InteractiveTourProps) {
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [actionNotice, setActionNotice] = useState<string | null>(null);
  const modalRef = useRef<HTMLDivElement>(null);

  const steps: TourStep[] = [
    {
      id: "workspace-intro",
      stepNumber: 1,
      title: "AI Risk Manager Overview",
      subtitle: "Stop merchants losing money to invalid chargeback contests",
      instructions:
        "Welcome to PRAMAAN. When dispute notices arrive, contesting them blindly incurs network fines and merchant losses. This system verifies evidence deterministically before any contest is mounted.",
      whyItMatters:
        "Every dispute contest costs merchant time and payment network fees. Contesting an invalid case guarantees a loss.",
    },
    {
      id: "import-evidence",
      stepNumber: 2,
      title: "Multi-File Evidence Ingestion",
      subtitle: "Bring customer messages, chat logs, and refund ledgers",
      instructions:
        "Notice the Evidence Dropzone below. Ingesting multiple evidence sources is a primary workflow. Try loading a sample case or dragging evidence files.",
      whyItMatters:
        "Disputes rarely have just one document. You need customer communications, order receipts, and bank ledger records together.",
      targetSelector: ".evidence-dropzone-wrapper",
      requiredAction: {
        description: "Select a sample case or upload an evidence file",
        isSatisfied: () => hasFiles,
      },
    },
    {
      id: "inspect-ingestion",
      stepNumber: 3,
      title: "Inspect File-Level Processing",
      subtitle: "Parsing, fault isolation, and format normalization",
      instructions:
        "Look at the evidence tray. Each file is parsed and validated independently. If one file is malformed, the rest of your batch continues processing safely.",
      whyItMatters:
        "Real-world merchant files are messy. Robust systems isolate errors at the individual file level instead of failing the entire batch.",
      targetSelector: ".evidence-tray",
    },
    {
      id: "fact-grounding",
      stepNumber: 4,
      title: "Exact Claim Grounding",
      subtitle: "Deterministic extraction beats LLM hallucination",
      instructions:
        "Review the customer communication and payment amount fields. Grounded claims require exact quotations in the source document. No facts are invented.",
      whyItMatters:
        "Statistical language models hallucinate amounts and dates. In financial risk, every claim must anchor to an auditable quotation.",
      targetSelector: ".guided-fields",
    },
    {
      id: "execute-verification",
      stepNumber: 5,
      title: "Run SMT Financial Logic Solver",
      subtitle: "Execute live Z3 arithmetic constraint checking",
      instructions:
        "Click the 'Check this case' button to run the offline verification engine. It evaluates claims against the authoritative ledger under sub-30ms execution.",
      whyItMatters:
        "The verifier compiles financial rules into SAT/UNSAT constraint certificates. Mathematical proof replaces guesswork.",
      targetSelector: 'button[type="submit"]',
      requiredAction: {
        description: "Click 'Check this case' to run the verification engine",
        isSatisfied: () => hasResult || hasCheckedCase,
      },
    },
    {
      id: "interpret-verdict",
      stepNumber: 6,
      title: "Interpret the Gate Verdict",
      subtitle: "PASS, REVIEW, or BLOCK with zero state authority",
      instructions:
        "Inspect the decision output. BLOCK stops unwinnable contests locally; REVIEW flags missing or incomplete ledgers; PASS verifies that evidence is consistent.",
      whyItMatters:
        "Honest risk management means knowing when to abstain. When ledger records are missing, the system abstains to REVIEW rather than making a blind guess.",
      targetSelector: ".guided-stage",
    },
    {
      id: "investigate-findings",
      stepNumber: 7,
      title: "Investigate Contradiction & Provenance",
      subtitle: "Click through to verify exact source quotes",
      instructions:
        "Step through the result tabs: 'Understand the claim', 'Check payment truth', and 'See the decision'. Notice the exact quoted customer words and ledger facts.",
      whyItMatters:
        "Human analysts must be able to audit why a case was flagged. Transparent provenance ensures defensibility with payment card networks.",
      targetSelector: ".guided-stepper",
      requiredAction: {
        description: "Advance to Step 2, 3, or 4 of the case inspection",
        isSatisfied: () => currentJourneyStep > 1,
      },
    },
    {
      id: "defense-only-workflow",
      stepNumber: 8,
      title: "Strictly Defense-Only Guardrails",
      subtitle: "Zero Razorpay writes · Zero automated fund transfers",
      instructions:
        "The system has no external write authority. It never initiates a dispute, charges a customer, or debits a merchant account. It produces local decision support only.",
      whyItMatters:
        "Fintech security invariant: automated AI systems must never possess write access to live payment rails without human oversight.",
      targetSelector: ".guided-boundary",
    },
    {
      id: "heldout-evaluation",
      stepNumber: 9,
      title: "Held-Out Metrics & False-Positive Cost",
      subtitle: "Inspect honest evaluation on frozen test sets",
      instructions:
        "Navigate to 'Generated Evaluation' in the top bar to inspect precision, recall, and false-positive cost analysis across 1,000 synthetic held-out cases.",
      whyItMatters:
        "High accuracy is meaningless if false positives trigger excessive dispute fees. Our benchmark explicitly measures financial impact per error.",
    },
    {
      id: "complete-loop",
      stepNumber: 10,
      title: "Full Risk Lifecycle Mastered",
      subtitle: "Evidence Ingestion → SMT Solver → Defense-Only Decision",
      instructions:
        "You have completed the full product tour! You know how to ingest multi-file evidence, isolate file failures, run deterministic SMT checks, and interpret calibrated verdicts.",
      whyItMatters:
        "PRAMAAN gives payment-risk engineers and merchants an unassailable audit trail for every dispute decision.",
    },
  ];

  const currentStep = steps[currentStepIndex];

  useEffect(() => {
    if (isOpen) {
      modalRef.current?.focus();
      const handleKeyDown = (e: KeyboardEvent) => {
        if (e.key === "Escape") onClose();
      };
      window.addEventListener("keydown", handleKeyDown);
      return () => window.removeEventListener("keydown", handleKeyDown);
    }
  }, [isOpen, currentStepIndex, onClose]);

  if (!isOpen) return null;

  function canAdvance(): boolean {
    if (!currentStep.requiredAction) return true;
    return currentStep.requiredAction.isSatisfied();
  }

  function handleNext() {
    if (!canAdvance()) {
      setActionNotice(
        `Action required: ${currentStep.requiredAction?.description}`,
      );
      return;
    }
    setActionNotice(null);
    if (currentStepIndex < steps.length - 1) {
      setCurrentStepIndex((prev) => prev + 1);
      if (currentStepIndex === 7 && onNavigateTab) {
        // suggest navigating to evaluation on step 9
      }
    } else {
      onClose();
    }
  }

  function handleBack() {
    setActionNotice(null);
    if (currentStepIndex > 0) {
      setCurrentStepIndex((prev) => prev - 1);
    }
  }

  return (
    <div
      className="interactive-tour-overlay"
      role="dialog"
      aria-modal="true"
      aria-labelledby="tour-step-title"
      ref={modalRef}
      tabIndex={-1}
      onKeyDown={(e) => {
        if (e.key === "Escape") onClose();
      }}
    >
      <div className="interactive-tour-card">
        <header className="tour-header">
          <div className="tour-badge">
            <Sparkle size={14} />
            <span>
              Interactive Product Tutorial · Step {currentStep.stepNumber} of{" "}
              {steps.length}
            </span>
          </div>
          <button
            type="button"
            className="tour-close-btn"
            onClick={onClose}
            aria-label="Exit tutorial"
          >
            <X size={16} />
          </button>
        </header>

        <div className="tour-progress-bar" aria-hidden="true">
          <div
            className="tour-progress-fill"
            style={{
              width: `${((currentStepIndex + 1) / steps.length) * 100}%`,
            }}
          />
        </div>

        <div className="tour-body">
          <h3 id="tour-step-title">{currentStep.title}</h3>
          <p className="tour-subtitle">{currentStep.subtitle}</p>

          <div className="tour-instruction-box">
            <p>{currentStep.instructions}</p>
          </div>

          <div className="tour-why-matters">
            <div className="why-title">
              <Lightbulb size={16} />
              <strong>Why this matters for merchants:</strong>
            </div>
            <p>{currentStep.whyItMatters}</p>
          </div>

          {currentStep.requiredAction && (
            <div
              className={`tour-action-required ${currentStep.requiredAction.isSatisfied() ? "action-satisfied" : "action-pending"}`}
            >
              <div className="action-status-icon">
                {currentStep.requiredAction.isSatisfied() ? (
                  <CheckCircle size={16} />
                ) : (
                  <WarningCircle size={16} />
                )}
              </div>
              <div className="action-details">
                <strong>
                  {currentStep.requiredAction.isSatisfied()
                    ? "Action completed!"
                    : "Action to proceed:"}
                </strong>
                <span>{currentStep.requiredAction.description}</span>
              </div>
            </div>
          )}

          {actionNotice && (
            <div className="tour-notice-banner" role="alert">
              {actionNotice}
            </div>
          )}
        </div>

        <footer className="tour-footer">
          <button
            type="button"
            className="tour-btn tour-btn-secondary"
            onClick={handleBack}
            disabled={currentStepIndex === 0}
          >
            <ArrowLeft size={16} /> Back
          </button>

          <div className="tour-footer-right">
            <button
              type="button"
              className="tour-btn tour-btn-quiet"
              onClick={onClose}
            >
              Skip tour
            </button>

            <button
              type="button"
              className="tour-btn tour-btn-primary"
              onClick={handleNext}
            >
              {currentStepIndex === steps.length - 1 ? (
                <>
                  Complete <CheckCircle size={16} />
                </>
              ) : (
                <>
                  {canAdvance() ? "Next" : "Proceed"} <ArrowRight size={16} />
                </>
              )}
            </button>
          </div>
        </footer>
      </div>
    </div>
  );
}
