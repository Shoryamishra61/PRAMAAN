import { useState, useRef, useEffect, useCallback } from "react";
import {
  Sparkle,
  X,
  Lightbulb,
  ArrowRight,
  ArrowsOutCardinal,
  ArrowsIn,
  ArrowCounterClockwise,
  CheckCircle,
  WarningCircle,
  CursorClick,
  CornersOut,
} from "@phosphor-icons/react";
import { useTutorial } from "./useTutorial";

const DEFAULT_CARD_WIDTH = 420;

export function TutorialTooltip() {
  const {
    isActive,
    currentStep,
    currentStepIndex,
    totalSteps,
    targetRect,
    isDocked,
    currentHintLevel,
    userOffset,
    setUserOffset,
    toggleDock,
    stopTour,
    nextStep,
  } = useTutorial();

  const [cardWidth, setCardWidth] = useState<number>(DEFAULT_CARD_WIDTH);
  const [isDragging, setIsDragging] = useState(false);
  const dragStartRef = useRef<{
    mouseX: number;
    mouseY: number;
    startOffsetX: number;
    startOffsetY: number;
  } | null>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);

  function cycleCardSize() {
    setCardWidth((prev) => (prev === 420 ? 540 : prev === 540 ? 340 : 420));
  }

  // Drag event listeners
  const handleMouseDown = useCallback(
    (e: React.MouseEvent) => {
      if ((e.target as HTMLElement).closest("button")) return;
      setIsDragging(true);
      dragStartRef.current = {
        mouseX: e.clientX,
        mouseY: e.clientY,
        startOffsetX: userOffset.x,
        startOffsetY: userOffset.y,
      };
      e.preventDefault();
    },
    [userOffset],
  );

  useEffect(() => {
    if (!isDragging) return;

    function handleMouseMove(e: MouseEvent) {
      if (!dragStartRef.current) return;
      const deltaX = e.clientX - dragStartRef.current.mouseX;
      const deltaY = e.clientY - dragStartRef.current.mouseY;
      setUserOffset({
        x: dragStartRef.current.startOffsetX + deltaX,
        y: dragStartRef.current.startOffsetY + deltaY,
      });
    }

    function handleMouseUp() {
      setIsDragging(false);
      dragStartRef.current = null;
    }

    window.addEventListener("mousemove", handleMouseMove);
    window.addEventListener("mouseup", handleMouseUp);
    return () => {
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("mouseup", handleMouseUp);
    };
  }, [isDragging, setUserOffset]);

  if (!isActive || !currentStep) return null;

  // Calculate position relative to target element
  const vpWidth = window.innerWidth || document.documentElement.clientWidth;
  const vpHeight = window.innerHeight || document.documentElement.clientHeight;

  const isIntro =
    currentStep.id === "step-welcome" ||
    currentStep.preferredPlacement === "center";
  const isFinal = currentStep.id === "step-decision-engine";
  const progressPercent = ((currentStepIndex + 1) / totalSteps) * 100;

  let top = 0;
  let left = 0;
  let hasAnchor = false;

  if (targetRect && !isDocked && !isIntro) {
    hasAnchor = true;
    const placement = currentStep.preferredPlacement || "bottom";
    const estimatedHeight = 360;
    let computedTop: number;
    let computedLeft = targetRect.left + (targetRect.width - cardWidth) / 2;

    if (placement === "bottom") {
      if (targetRect.bottom + estimatedHeight + 20 < vpHeight) {
        computedTop = targetRect.bottom + 14;
      } else if (targetRect.top - estimatedHeight - 20 > 0) {
        computedTop = targetRect.top - estimatedHeight - 14;
      } else if (targetRect.right + cardWidth + 20 < vpWidth) {
        computedLeft = targetRect.right + 16;
        computedTop = Math.max(16, targetRect.top);
      } else if (targetRect.left - cardWidth - 20 > 0) {
        computedLeft = targetRect.left - cardWidth - 16;
        computedTop = Math.max(16, targetRect.top);
      } else {
        computedTop = Math.max(16, targetRect.top - estimatedHeight - 14);
      }
    } else if (placement === "top") {
      if (targetRect.top - estimatedHeight - 20 > 0) {
        computedTop = targetRect.top - estimatedHeight - 14;
      } else if (targetRect.bottom + estimatedHeight + 20 < vpHeight) {
        computedTop = targetRect.bottom + 14;
      } else if (targetRect.right + cardWidth + 20 < vpWidth) {
        computedLeft = targetRect.right + 16;
        computedTop = Math.max(16, targetRect.top);
      } else if (targetRect.left - cardWidth - 20 > 0) {
        computedLeft = targetRect.left - cardWidth - 16;
        computedTop = Math.max(16, targetRect.top);
      } else {
        computedTop = targetRect.bottom + 14;
      }
    } else {
      computedTop = Math.max(20, targetRect.top);
      computedLeft = targetRect.left + (targetRect.width - cardWidth) / 2;
    }

    const cardRenderHeight = 480;

    // Clamp inside viewport
    left = Math.max(16, Math.min(vpWidth - cardWidth - 16, computedLeft));
    top = Math.max(16, Math.min(vpHeight - cardRenderHeight - 20, computedTop));

    // Anti-collision guard: Ensure tooltip NEVER overlaps targetRect
    const overlapsX =
      left < targetRect.right && left + cardWidth > targetRect.left;
    const overlapsY =
      top < targetRect.bottom && top + cardRenderHeight > targetRect.top;
    if (overlapsX && overlapsY) {
      if (targetRect.top >= cardRenderHeight + 20) {
        top = Math.max(16, targetRect.top - cardRenderHeight - 12);
      } else if (vpHeight - targetRect.bottom >= cardRenderHeight + 20) {
        top = Math.min(
          vpHeight - cardRenderHeight - 20,
          targetRect.bottom + 12,
        );
      }
    }

    // Apply manual user drag offset
    top += userOffset.y;
    left += userOffset.x;
  }

  if (isDocked) {
    return (
      <aside
        className="tour-docked-pill"
        role="complementary"
        aria-label="Tutorial minimized"
        style={{ zIndex: 100001 }}
      >
        <button
          type="button"
          className="tour-docked-resume-btn"
          onClick={toggleDock}
          title="Expand guidance tooltip"
        >
          <Sparkle size={16} />
          <span>
            Step {currentStep.stepIndex} of {totalSteps}: {currentStep.title}
          </span>
          <ArrowsOutCardinal size={15} />
        </button>
        <button
          type="button"
          className="tour-docked-close-btn"
          onClick={stopTour}
          aria-label="Close tutorial"
        >
          <X size={14} />
        </button>
      </aside>
    );
  }

  // When unanchored or intro, anchor cleanly to bottom-right with 24px margin
  // Dragging linearly adjusts distance from bottom and right
  const unanchoredBottom = Math.max(
    20,
    Math.min(vpHeight - 100, 24 - userOffset.y),
  );
  const unanchoredRight = Math.max(
    20,
    Math.min(vpWidth - cardWidth - 20, 24 - userOffset.x),
  );

  return (
    <aside
      ref={tooltipRef}
      className={`tour-tooltip-card ${isDragging ? "tour-dragging" : ""}`}
      role="dialog"
      aria-modal="true"
      aria-labelledby="tour-step-title"
      style={
        hasAnchor
          ? {
              position: "fixed",
              top: `${top}px`,
              left: `${left}px`,
              width: `${cardWidth}px`,
              maxHeight: "calc(100vh - 48px)",
              zIndex: 100000,
            }
          : {
              position: "fixed",
              bottom: `${unanchoredBottom}px`,
              right: `${unanchoredRight}px`,
              width: `${cardWidth}px`,
              maxHeight: "calc(100vh - 48px)",
              zIndex: 100000,
            }
      }
    >
      {/* Draggable header bar */}
      <header
        className="tour-tooltip-header"
        onMouseDown={handleMouseDown}
        style={{ cursor: isDragging ? "grabbing" : "grab" }}
      >
        <div className="tour-tooltip-badge">
          <Sparkle size={15} aria-hidden="true" />
          <span>
            Step {currentStep.stepIndex} of {totalSteps}
          </span>
        </div>

        <div className="tour-tooltip-controls">
          <button
            type="button"
            className="tour-icon-btn"
            onClick={cycleCardSize}
            title={`Toggle card size (Current: ${cardWidth}px)`}
            aria-label="Toggle card size"
          >
            <CornersOut size={14} />
          </button>
          {(userOffset.x !== 0 || userOffset.y !== 0) && (
            <button
              type="button"
              className="tour-icon-btn"
              onClick={() => setUserOffset({ x: 0, y: 0 })}
              title="Reset position to corner"
              aria-label="Reset position"
            >
              <ArrowCounterClockwise size={14} />
            </button>
          )}
          <button
            type="button"
            className="tour-icon-btn"
            onClick={toggleDock}
            title="Minimize / Dock to corner"
            aria-label="Dock tutorial"
          >
            <ArrowsIn size={14} />
          </button>
          <button
            type="button"
            className="tour-icon-btn tour-icon-close"
            onClick={stopTour}
            title="Exit tutorial (Esc)"
            aria-label="Exit tutorial"
          >
            <X size={14} />
          </button>
        </div>
      </header>

      {/* Progress bar */}
      <div className="tour-progress-bar" aria-hidden="true">
        <div
          className="tour-progress-fill"
          style={{ width: `${progressPercent}%` }}
        />
      </div>

      {/* Body content */}
      <div className="tour-tooltip-body">
        <h3 id="tour-step-title" className="tour-step-title">
          {currentStep.title}
        </h3>

        <p className="tour-role-text">{currentStep.roleExplanation}</p>

        {/* Action Directive Banner */}
        <div className="tour-action-callout">
          <div className="tour-action-icon">
            <CursorClick size={18} />
          </div>
          <div className="tour-action-content">
            <span className="tour-action-label">REQUIRED ACTION</span>
            <strong className="tour-action-directive">
              {currentStep.actionDirective}
            </strong>
          </div>
        </div>

        {/* Why this matters for merchants */}
        <div className="tour-why-matters">
          <div className="tour-why-header">
            <Lightbulb size={14} aria-hidden="true" />
            <span>Why this matters for merchants</span>
          </div>
          <p>{currentStep.whyItMatters}</p>
        </div>

        {/* Contextual hint escalation */}
        {currentHintLevel > 0 && currentStep.hints[currentHintLevel - 1] && (
          <div className="tour-hint-banner" role="status">
            <WarningCircle size={15} aria-hidden="true" />
            <div className="tour-hint-content">
              <strong>Need a hand?</strong>
              <span>{currentStep.hints[currentHintLevel - 1]}</span>
            </div>
          </div>
        )}
      </div>

      {/* Footer actions */}
      <footer className="tour-tooltip-footer">
        <button type="button" className="tour-quiet-btn" onClick={stopTour}>
          Skip tour
        </button>

        <div className="tour-footer-actions">
          {isIntro ? (
            <button
              type="button"
              className="tour-primary-btn"
              onClick={nextStep}
            >
              <span>Start Guided Walkthrough</span>
              <ArrowRight size={15} />
            </button>
          ) : isFinal ? (
            <button
              type="button"
              className="tour-primary-btn"
              onClick={nextStep}
            >
              <span>Finish Tutorial</span>
              <CheckCircle size={15} />
            </button>
          ) : (
            <div className="tour-listening-pill">
              <span className="tour-listening-pulse" />
              <span>Waiting for your action…</span>
            </div>
          )}
        </div>
      </footer>
    </aside>
  );
}
