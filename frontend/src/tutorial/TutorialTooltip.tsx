import {
  ArrowCounterClockwise,
  ArrowLeft,
  ArrowRight,
  ArrowsIn,
  ArrowsOutCardinal,
  CheckCircle,
  Lightbulb,
  Info,
  WarningCircle,
  X,
} from "@phosphor-icons/react";
import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type PointerEvent as ReactPointerEvent,
} from "react";
import {
  chooseTourPlacement,
  tourPanelCoordinates,
  contextualTourGuidance,
} from "./tutorialEngine";
import type {
  ResolvedTourPlacement,
  TourPanelSize,
  TourPlacement,
} from "./types";
import { useTutorial } from "./useTutorial";

const PANEL_WIDTHS: Record<TourPanelSize, number> = {
  compact: 300,
  standard: 380,
  expanded: 500,
};
const VIEWPORT_MARGIN = 16;

function isEditableTarget(target: EventTarget | null): boolean {
  return (
    target instanceof HTMLElement &&
    Boolean(target.closest("input, textarea, select, [contenteditable='true']"))
  );
}

export function TutorialTooltip() {
  const {
    isActive,
    appContext,
    status,
    currentStep,
    currentStepIndex,
    workflowStepNumber,
    totalSteps,
    targetRect,
    targetStatus,
    isDocked,
    currentHintLevel,
    actionSatisfied,
    userOffset,
    panelSize,
    placement,
    setUserOffset,
    setPanelSize,
    setPlacement,
    toggleDock,
    stopTour,
    nextStep,
    prevStep,
  } = useTutorial();
  const [viewport, setViewport] = useState({
    width: window.innerWidth,
    height: window.innerHeight,
  });
  const [panelHeight, setPanelHeight] = useState(460);
  const [isDragging, setIsDragging] = useState(false);
  const dragStartRef = useRef<{
    pointerId: number;
    x: number;
    y: number;
    offsetX: number;
    offsetY: number;
  } | null>(null);
  const tooltipRef = useRef<HTMLElement>(null);
  const headingRef = useRef<HTMLHeadingElement>(null);
  const panelWidth = Math.min(
    PANEL_WIDTHS[panelSize],
    Math.max(280, viewport.width - VIEWPORT_MARGIN * 2),
  );
  const resolvedPlacement: ResolvedTourPlacement =
    placement === "auto"
      ? chooseTourPlacement(
          targetRect,
          viewport.width,
          viewport.height,
          panelWidth,
          panelHeight,
        )
      : placement;
  const basePosition = tourPanelCoordinates(
    resolvedPlacement,
    targetRect,
    viewport.width,
    viewport.height,
    panelWidth,
    panelHeight,
    VIEWPORT_MARGIN,
  );
  const maxLeft = Math.max(
    VIEWPORT_MARGIN,
    viewport.width - panelWidth - VIEWPORT_MARGIN,
  );
  const maxTop = Math.max(
    VIEWPORT_MARGIN,
    viewport.height -
      Math.min(panelHeight, viewport.height - 32) -
      VIEWPORT_MARGIN,
  );
  const left = Math.max(
    VIEWPORT_MARGIN,
    Math.min(maxLeft, basePosition.left + userOffset.x),
  );
  const top = Math.max(
    VIEWPORT_MARGIN,
    Math.min(maxTop, basePosition.top + userOffset.y),
  );

  useEffect(() => {
    const updateViewport = () =>
      setViewport({ width: window.innerWidth, height: window.innerHeight });
    window.addEventListener("resize", updateViewport, { passive: true });
    return () => window.removeEventListener("resize", updateViewport);
  }, []);

  useEffect(() => {
    const element = tooltipRef.current;
    if (!element) return;
    const updateHeight = () => setPanelHeight(element.offsetHeight || 460);
    updateHeight();
    if (typeof ResizeObserver === "undefined") return;
    const observer = new ResizeObserver(updateHeight);
    observer.observe(element);
    return () => observer.disconnect();
  }, [currentStepIndex, isDocked, panelSize]);

  useEffect(() => {
    if (!isActive || isDocked) return;
    headingRef.current?.focus();
  }, [isActive, isDocked]);

  useEffect(() => {
    if (!isActive) return;
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        event.preventDefault();
        stopTour();
      } else if (!isEditableTarget(event.target) && event.key === "ArrowLeft") {
        event.preventDefault();
        prevStep();
      } else if (
        !isEditableTarget(event.target) &&
        event.key === "ArrowRight"
      ) {
        event.preventDefault();
        nextStep();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isActive, nextStep, prevStep, stopTour]);

  const handlePointerDown = useCallback(
    (event: ReactPointerEvent<HTMLElement>) => {
      if ((event.target as HTMLElement).closest("button, select, label"))
        return;
      event.currentTarget.setPointerCapture(event.pointerId);
      dragStartRef.current = {
        pointerId: event.pointerId,
        x: event.clientX,
        y: event.clientY,
        offsetX: userOffset.x,
        offsetY: userOffset.y,
      };
      setIsDragging(true);
    },
    [userOffset],
  );

  const handlePointerMove = useCallback(
    (event: ReactPointerEvent<HTMLElement>) => {
      const drag = dragStartRef.current;
      if (!drag || drag.pointerId !== event.pointerId) return;
      const desiredLeft =
        basePosition.left + drag.offsetX + event.clientX - drag.x;
      const desiredTop =
        basePosition.top + drag.offsetY + event.clientY - drag.y;
      const boundedLeft = Math.max(
        VIEWPORT_MARGIN,
        Math.min(maxLeft, desiredLeft),
      );
      const boundedTop = Math.max(
        VIEWPORT_MARGIN,
        Math.min(maxTop, desiredTop),
      );
      setUserOffset({
        x: boundedLeft - basePosition.left,
        y: boundedTop - basePosition.top,
      });
    },
    [basePosition.left, basePosition.top, maxLeft, maxTop, setUserOffset],
  );

  const handlePointerUp = useCallback(
    (event: ReactPointerEvent<HTMLElement>) => {
      if (dragStartRef.current?.pointerId !== event.pointerId) return;
      dragStartRef.current = null;
      setIsDragging(false);
    },
    [],
  );

  if (!isActive || !currentStep) return null;

  const isWelcome = currentStep.kind === "welcome";
  const isFinal = currentStepIndex === totalSteps;
  const progressPercent =
    workflowStepNumber === null ? 0 : (workflowStepNumber / totalSteps) * 100;
  const progressLabel =
    workflowStepNumber === null
      ? "Welcome"
      : `Step ${workflowStepNumber} of ${totalSteps}`;

  if (isDocked) {
    return (
      <aside className="tour-docked-pill" aria-label="Product tour minimized">
        <button
          type="button"
          className="tour-docked-resume-btn"
          onClick={toggleDock}
          title="Expand product tour"
        >
          <Info size={16} aria-hidden="true" />
          <span>{progressLabel}</span>
          <ArrowsOutCardinal size={15} aria-hidden="true" />
        </button>
        <button
          type="button"
          className="tour-icon-btn"
          onClick={stopTour}
          aria-label="Close product tour"
        >
          <X size={16} aria-hidden="true" />
        </button>
      </aside>
    );
  }

  return (
    <aside
      ref={tooltipRef}
      className={`tour-tooltip-card ${isDragging ? "tour-dragging" : ""}`}
      role="dialog"
      aria-labelledby="tour-step-title"
      aria-describedby="tour-step-summary"
      data-placement={resolvedPlacement}
      style={
        viewport.width < 560
          ? {
              left: 8,
              bottom: 8,
              width: viewport.width - 16,
              maxHeight: "min(78vh, 620px)",
            }
          : {
              left,
              top,
              width: panelWidth,
              maxHeight: `calc(100vh - ${VIEWPORT_MARGIN * 2}px)`,
            }
      }
    >
      <header
        className="tour-tooltip-header"
        onPointerDown={handlePointerDown}
        onPointerMove={handlePointerMove}
        onPointerUp={handlePointerUp}
        onPointerCancel={handlePointerUp}
      >
        <div className="tour-tooltip-badge">
          <Info size={15} aria-hidden="true" />
          <span>{progressLabel}</span>
        </div>
        <div className="tour-tooltip-controls">
          <label>
            <span className="visually-hidden">Tour card size</span>
            <select
              value={panelSize}
              onChange={(event) =>
                setPanelSize(event.target.value as TourPanelSize)
              }
              aria-label="Tour card size"
            >
              <option value="compact">Compact</option>
              <option value="standard">Standard</option>
              <option value="expanded">Expanded</option>
            </select>
          </label>
          <label>
            <span className="visually-hidden">Tour card position</span>
            <select
              value={placement}
              onChange={(event) =>
                setPlacement(event.target.value as TourPlacement)
              }
              aria-label="Tour card position"
            >
              <option value="auto">Auto</option>
              <option value="top-left">Top left</option>
              <option value="top-right">Top right</option>
              <option value="bottom-left">Bottom left</option>
              <option value="bottom-right">Bottom right</option>
              <option value="side-center">Side center</option>
            </select>
          </label>
          {(userOffset.x !== 0 || userOffset.y !== 0) && (
            <button
              type="button"
              className="tour-icon-btn"
              onClick={() => setUserOffset({ x: 0, y: 0 })}
              title="Reset tour card position"
              aria-label="Reset tour card position"
            >
              <ArrowCounterClockwise size={16} aria-hidden="true" />
            </button>
          )}
          <button
            type="button"
            className="tour-icon-btn"
            onClick={toggleDock}
            title="Minimize product tour"
            aria-label="Minimize product tour"
          >
            <ArrowsIn size={16} aria-hidden="true" />
          </button>
          <button
            type="button"
            className="tour-icon-btn"
            onClick={stopTour}
            title="Close product tour"
            aria-label="Close product tour"
          >
            <X size={16} aria-hidden="true" />
          </button>
        </div>
      </header>

      <div
        className="tour-progress"
        role="progressbar"
        aria-label="Product tour progress"
        aria-valuemin={0}
        aria-valuemax={totalSteps}
        aria-valuenow={workflowStepNumber ?? 0}
        aria-valuetext={progressLabel}
      >
        <span style={{ width: `${progressPercent}%` }} />
      </div>
      <p className="visually-hidden" aria-live="polite">
        {progressLabel}: {currentStep.title}
      </p>

      <div className="tour-tooltip-body">
        {contextualTourGuidance(appContext) && (
          <p className="tour-context-note" role="status">
            {contextualTourGuidance(appContext)}
          </p>
        )}
        <h2 id="tour-step-title" ref={headingRef} tabIndex={-1}>
          {currentStep.title}
        </h2>
        <p id="tour-step-summary">{currentStep.summary}</p>

        <div className="tour-action-callout">
          <strong>{actionSatisfied ? "Action observed" : "Try this"}</strong>
          <span>{currentStep.actionDirective}</span>
        </div>

        {targetStatus === "missing" && (
          <div className="tour-target-note" role="status">
            <WarningCircle size={16} aria-hidden="true" />
            <span>
              This target is not available in the current screen state.
              Continue, go back, or use the screen directly.
            </span>
          </div>
        )}
        {targetStatus === "fallback" && (
          <p className="tour-target-note" role="status">
            Showing the nearest stable context while the primary control is
            unavailable.
          </p>
        )}
        {status === "WAITING_FOR_TARGET" && (
          <p className="tour-target-note" role="status">
            Locating the relevant control…
          </p>
        )}

        <details className="tour-why">
          <summary>
            <Lightbulb size={15} aria-hidden="true" />
            Why this matters
          </summary>
          <p>{currentStep.whyItMatters}</p>
        </details>

        {currentHintLevel > 0 &&
          currentStep.hints[
            Math.min(currentHintLevel - 1, currentStep.hints.length - 1)
          ] && (
            <div className="tour-hint" role="status">
              <WarningCircle size={16} aria-hidden="true" />
              <span>
                {
                  currentStep.hints[
                    Math.min(currentHintLevel - 1, currentStep.hints.length - 1)
                  ]
                }
              </span>
            </div>
          )}
      </div>

      <footer className="tour-tooltip-footer">
        <button type="button" className="tour-quiet-btn" onClick={stopTour}>
          Skip
        </button>
        <div>
          <button
            type="button"
            className="tour-secondary-btn"
            onClick={prevStep}
            disabled={currentStepIndex === 0}
          >
            <ArrowLeft size={15} aria-hidden="true" />
            Back
          </button>
          <button type="button" className="tour-primary-btn" onClick={nextStep}>
            {isWelcome ? "Start" : isFinal ? "Finish" : "Next"}
            {isFinal ? (
              <CheckCircle size={16} aria-hidden="true" />
            ) : (
              <ArrowRight size={15} aria-hidden="true" />
            )}
          </button>
        </div>
      </footer>
    </aside>
  );
}
