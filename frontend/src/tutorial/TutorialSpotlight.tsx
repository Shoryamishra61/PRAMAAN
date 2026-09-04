import { useEffect } from "react";
import { useTutorial } from "./useTutorial";

const PADDING = 8;
const RADIUS = 8;

export function TutorialSpotlight() {
  const { isActive, targetRect, stopTour } = useTutorial();

  useEffect(() => {
    if (!isActive) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        stopTour();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isActive, stopTour]);

  if (!isActive) return null;

  const width = window.innerWidth || document.documentElement.clientWidth;
  const height = window.innerHeight || document.documentElement.clientHeight;

  const hasCutout =
    targetRect !== null && targetRect.width > 0 && targetRect.height > 0;

  const cutoutX = hasCutout ? Math.max(0, targetRect.left - PADDING) : 0;
  const cutoutY = hasCutout ? Math.max(0, targetRect.top - PADDING) : 0;
  const cutoutW = hasCutout
    ? Math.min(width - cutoutX, targetRect.width + PADDING * 2)
    : 0;
  const cutoutH = hasCutout
    ? Math.min(height - cutoutY, targetRect.height + PADDING * 2)
    : 0;

  return (
    <div
      className="tour-spotlight-container"
      aria-hidden="true"
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 99990,
        pointerEvents: "none",
        overflow: "hidden",
      }}
    >
      <svg
        width="100%"
        height="100%"
        viewBox={`0 0 ${width} ${height}`}
        style={{
          position: "absolute",
          inset: 0,
          width: "100vw",
          height: "100vh",
        }}
      >
        {/* Dimmed backdrop layer with geometric hole so cutout area has ZERO SVG fill and ZERO pointer event interception */}
        {hasCutout ? (
          <path
            d={`M 0 0 L ${width} 0 L ${width} ${height} L 0 ${height} Z M ${cutoutX} ${cutoutY} L ${cutoutX + cutoutW} ${cutoutY} L ${cutoutX + cutoutW} ${cutoutY + cutoutH} L ${cutoutX} ${cutoutY + cutoutH} Z`}
            fillRule="evenodd"
            fill="rgba(15, 23, 42, 0.72)"
            style={{
              pointerEvents: "auto",
              transition: "all 0.25s cubic-bezier(0.16, 1, 0.3, 1)",
            }}
          />
        ) : (
          <rect
            x="0"
            y="0"
            width="100%"
            height="100%"
            fill="rgba(15, 23, 42, 0.72)"
            style={{
              pointerEvents: "auto",
              transition: "all 0.25s cubic-bezier(0.16, 1, 0.3, 1)",
            }}
          />
        )}

        {/* Interactive pulsing focus ring around the cutout */}
        {hasCutout && (
          <rect
            x={cutoutX}
            y={cutoutY}
            width={cutoutW}
            height={cutoutH}
            rx={RADIUS}
            ry={RADIUS}
            fill="none"
            className="tour-spotlight-ring"
            style={{
              pointerEvents: "none",
              stroke: "#38bdf8",
              strokeWidth: 2.5,
            }}
          />
        )}
      </svg>
    </div>
  );
}
