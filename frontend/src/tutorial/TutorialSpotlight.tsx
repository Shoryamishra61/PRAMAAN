import { useEffect, useState } from "react";
import { useTutorial } from "./useTutorial";

function targetPadding(rect: DOMRect): number {
  return Math.max(
    8,
    Math.min(16, Math.round(Math.min(rect.width, rect.height) * 0.12)),
  );
}

export function TutorialSpotlight() {
  const { isActive, currentStep, targetRect, targetStatus, isDocked } =
    useTutorial();
  const [viewport, setViewport] = useState({
    width: window.innerWidth,
    height: window.innerHeight,
  });

  useEffect(() => {
    const update = () =>
      setViewport({ width: window.innerWidth, height: window.innerHeight });
    window.addEventListener("resize", update, { passive: true });
    return () => window.removeEventListener("resize", update);
  }, []);

  if (!isActive || isDocked || !currentStep) return null;

  const hasTarget =
    targetStatus !== "missing" &&
    targetRect !== null &&
    targetRect.width > 0 &&
    targetRect.height > 0;
  const padding = hasTarget ? targetPadding(targetRect) : 0;
  const x = hasTarget ? Math.max(0, targetRect.left - padding) : 0;
  const y = hasTarget ? Math.max(0, targetRect.top - padding) : 0;
  const width = hasTarget
    ? Math.min(viewport.width - x, targetRect.width + padding * 2)
    : 0;
  const height = hasTarget
    ? Math.min(viewport.height - y, targetRect.height + padding * 2)
    : 0;
  return (
    <div
      className={`tour-spotlight ${hasTarget ? "" : "tour-spotlight-idle"}`}
      aria-hidden="true"
    >
      {hasTarget && (
        <div
          className="tour-spotlight-focus"
          style={{ left: x, top: y, width, height }}
        />
      )}
    </div>
  );
}
