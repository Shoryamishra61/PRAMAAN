import { describe, it, expect, beforeEach } from "vitest";
import {
  TUTORIAL_STEPS,
  TUTORIAL_STORAGE_KEY,
  TUTORIAL_COMPLETED_KEY,
  emitTutorialAnalytics,
} from "./tutorialEngine";
import { type TutorialAppContext } from "./types";

describe("tutorialEngine", () => {
  const baseContext: TutorialAppContext = {
    route: "proof",
    journeyStep: 1,
    hasFiles: false,
    fileCount: 0,
    hasResult: false,
    isEvaluating: false,
    resultVerdict: null,
    hasRepaired: false,
    selectedScenario: null,
    evaluationView: "debugger",
    activeTab: "debugger",
  };

  beforeEach(() => {
    localStorage.clear();
  });

  it("contains 9 structured, action-gated tutorial steps", () => {
    expect(TUTORIAL_STORAGE_KEY).toBeTruthy();
    expect(TUTORIAL_COMPLETED_KEY).toBeTruthy();
    expect(TUTORIAL_STEPS.length).toBe(9);
    for (const step of TUTORIAL_STEPS) {
      expect(step.id).toBeTruthy();
      expect(step.title).toBeTruthy();
      expect(step.targetSelector).toBeTruthy();
      expect(step.roleExplanation).toBeTruthy();
      expect(step.actionDirective).toBeTruthy();
      expect(step.whyItMatters).toBeTruthy();
      expect(step.hints.length).toBeGreaterThan(0);
      expect([
        "click",
        "upload",
        "submit",
        "tab",
        "observe",
        "repair",
      ]).toContain(step.requiredAction);
    }
  });

  it("satisfies step-select-sample when a scenario or file is loaded", () => {
    const step = TUTORIAL_STEPS.find((s) => s.id === "step-select-sample")!;
    expect(step.isSatisfied(baseContext)).toBe(false);

    expect(
      step.isSatisfied({
        ...baseContext,
        selectedScenario: "wrong_amount",
      }),
    ).toBe(true);

    expect(
      step.isSatisfied({
        ...baseContext,
        hasFiles: true,
        fileCount: 2,
      }),
    ).toBe(true);
  });

  it("satisfies step-run-verification when evaluation runs or produces a result", () => {
    const step = TUTORIAL_STEPS.find((s) => s.id === "step-run-verification")!;
    expect(step.isSatisfied(baseContext)).toBe(false);

    expect(
      step.isSatisfied({
        ...baseContext,
        isEvaluating: true,
      }),
    ).toBe(true);

    expect(
      step.isSatisfied({
        ...baseContext,
        hasResult: true,
      }),
    ).toBe(true);
  });

  it("satisfies step-inspect-claim when journeyStep advances to 3", () => {
    const step = TUTORIAL_STEPS.find((s) => s.id === "step-inspect-claim")!;
    expect(step.isSatisfied(baseContext)).toBe(false);
    expect(step.isSatisfied({ ...baseContext, journeyStep: 2 })).toBe(false);
    expect(step.isSatisfied({ ...baseContext, journeyStep: 3 })).toBe(true);
    expect(step.isSatisfied({ ...baseContext, journeyStep: 4 })).toBe(true);
  });

  it("satisfies step-smt-truth-layer when journeyStep advances to 4", () => {
    const step = TUTORIAL_STEPS.find((s) => s.id === "step-smt-truth-layer")!;
    expect(step.isSatisfied(baseContext)).toBe(false);
    expect(step.isSatisfied({ ...baseContext, journeyStep: 3 })).toBe(false);
    expect(step.isSatisfied({ ...baseContext, journeyStep: 4 })).toBe(true);
  });

  it("satisfies step-verdict-analysis when ledger is repaired or verdict is PASS", () => {
    const step = TUTORIAL_STEPS.find((s) => s.id === "step-verdict-analysis")!;
    expect(step.isSatisfied(baseContext)).toBe(false);
    expect(
      step.isSatisfied({
        ...baseContext,
        hasRepaired: true,
      }),
    ).toBe(true);
    expect(
      step.isSatisfied({
        ...baseContext,
        hasResult: true,
        resultVerdict: "PASS",
      }),
    ).toBe(true);
  });

  it("satisfies step-repair-pass when evaluation view is opened", () => {
    const step = TUTORIAL_STEPS.find((s) => s.id === "step-repair-pass")!;
    expect(step.isSatisfied(baseContext)).toBe(false);
    expect(
      step.isSatisfied({
        ...baseContext,
        evaluationView: "evaluation",
      }),
    ).toBe(true);
    expect(
      step.isSatisfied({
        ...baseContext,
        route: "evaluation",
      }),
    ).toBe(true);
  });

  it("records analytics safely in localStorage", () => {
    emitTutorialAnalytics({ type: "tour_started" });
    emitTutorialAnalytics({
      type: "step_entered",
      stepId: "step-welcome",
      stepIndex: 1,
    });

    const stored = JSON.parse(
      localStorage.getItem("pramaan_tutorial_analytics") || "[]",
    );
    expect(stored.length).toBe(2);
    expect(stored[0].type).toBe("tour_started");
    expect(stored[1].type).toBe("step_entered");
    expect(stored[1].stepId).toBe("step-welcome");
  });
});
