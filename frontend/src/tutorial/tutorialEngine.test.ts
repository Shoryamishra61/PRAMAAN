import { contextualTourGuidance } from "./tutorialEngine";
import { defaultAppContext } from "./useTutorial";
import { beforeEach, describe, expect, it } from "vitest";
import {
  chooseTourPlacement,
  emitTutorialAnalytics,
  TUTORIAL_ANALYTICS_KEY,
  TUTORIAL_STEPS,
  tourPanelCoordinates,
  transitionTourStatus,
  workflowNumberForIndex,
  WORKFLOW_STEP_COUNT,
} from "./tutorialEngine";

describe("tutorialEngine", () => {
  beforeEach(() => localStorage.clear());

  it("owns one welcome plus seven numbered workflow steps", () => {
    expect(TUTORIAL_STEPS).toHaveLength(8);
    expect(TUTORIAL_STEPS[0].kind).toBe("welcome");
    expect(WORKFLOW_STEP_COUNT).toBe(7);
    expect(
      TUTORIAL_STEPS.slice(1).map((_, index) =>
        workflowNumberForIndex(index + 1),
      ),
    ).toEqual([1, 2, 3, 4, 5, 6, 7]);
    expect(new Set(TUTORIAL_STEPS.map((step) => step.id)).size).toBe(8);
  });

  it("keeps copy truthful and derives all targets from one registry", () => {
    const copy = TUTORIAL_STEPS.map(
      (step) => `${step.title} ${step.summary} ${step.whyItMatters}`,
    ).join(" ");
    expect(copy).not.toMatch(
      /guarantees? a loss|unassailable|confusion score|sub-30ms/i,
    );
    for (const step of TUTORIAL_STEPS) {
      expect(step.route).toBeTruthy();
      expect(step.hints.length).toBeGreaterThan(0);
    }
  });

  it("enforces explicit terminal lifecycle transitions", () => {
    expect(transitionTourStatus("IDLE", "START")).toBe("STARTING");
    expect(transitionTourStatus("STARTING", "BEGIN_STEP")).toBe(
      "WAITING_FOR_TARGET",
    );
    expect(transitionTourStatus("WAITING_FOR_TARGET", "TARGET_MISSING")).toBe(
      "ACTIVE",
    );
    expect(transitionTourStatus("ACTIVE", "NEXT")).toBe("TRANSITIONING");
    expect(transitionTourStatus("TRANSITIONING", "BEGIN_STEP")).toBe(
      "WAITING_FOR_TARGET",
    );
    expect(transitionTourStatus("ACTIVE", "COMPLETE")).toBe("COMPLETED");
    expect(transitionTourStatus("COMPLETED", "NEXT")).toBe("COMPLETED");
    expect(transitionTourStatus("ACTIVE", "CANCEL")).toBe("CANCELLED");
  });

  it("places the panel within bounds and away from a bottom-right target", () => {
    const target = {
      left: 1180,
      right: 1380,
      top: 720,
      bottom: 800,
      width: 200,
      height: 80,
    } as DOMRect;
    const placement = chooseTourPlacement(target, 1440, 900, 380, 460);
    expect(placement).not.toBe("bottom-right");
    const point = tourPanelCoordinates(placement, target, 1440, 900, 380, 460);
    expect(point.left).toBeGreaterThanOrEqual(16);
    expect(point.top).toBeGreaterThanOrEqual(16);
    expect(point.left + 380).toBeLessThanOrEqual(1424);
    expect(point.top + 460).toBeLessThanOrEqual(884);
  });

  it("stores only bounded local lifecycle telemetry", () => {
    emitTutorialAnalytics({ type: "tour_started" });
    emitTutorialAnalytics({
      type: "step_entered",
      stepId: "welcome",
      workflowNumber: null,
    });
    const stored = JSON.parse(
      localStorage.getItem(TUTORIAL_ANALYTICS_KEY) ?? "[]",
    );
    expect(stored).toHaveLength(2);
    expect(stored[1]).toMatchObject({
      stepId: "welcome",
      workflowNumber: null,
    });
  });
});

describe("observed case guidance", () => {
  it("prioritizes input repair, waiting and actual outcomes over generic steps", () => {
    const context = {
      ...defaultAppContext,
      route: "proof",
      hasFiles: true,
      fileCount: 2,
    };
    expect(contextualTourGuidance(context)).toContain("2 local files");
    expect(
      contextualTourGuidance({ ...context, inputError: "Invalid CSV" }),
    ).toContain("Invalid CSV");
    expect(
      contextualTourGuidance({ ...context, isEvaluating: true }),
    ).toContain("running");
    expect(
      contextualTourGuidance({
        ...context,
        hasResult: true,
        resultVerdict: "BLOCK",
      }),
    ).toContain("local hold");
    expect(
      contextualTourGuidance({
        ...context,
        hasResult: true,
        resultVerdict: "PASS",
      }),
    ).toContain("does not predict");
  });
});
