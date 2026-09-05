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
  const path = hasTarget
    ? `M0 0H${viewport.width}V${viewport.height}H0Z M${x} ${y}H${x + width}V${y + height}H${x}Z`
    : `M0 0H${viewport.width}V${viewport.height}H0Z`;

  return (
    <div className="tour-spotlight" aria-hidden="true">
      <svg
        width="100%"
        height="100%"
        viewBox={`0 0 ${viewport.width} ${viewport.height}`}
        preserveAspectRatio="none"
      >
        <path d={path} fillRule="evenodd" className="tour-spotlight-shade" />
        {hasTarget && (
          <rect
            x={x}
            y={y}
            width={width}
            height={height}
            rx={6}
            className="tour-spotlight-ring"
          />
        )}
      </svg>
    </div>
  );
}
