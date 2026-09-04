import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { render, screen, fireEvent, cleanup } from "@testing-library/react";
import {
  TutorialProvider,
  TutorialSpotlight,
  TutorialTooltip,
  useTutorial,
} from "./index";

function TestController() {
  const { isActive, startTour, stopTour, nextStep, isDocked, toggleDock } =
    useTutorial();
  return (
    <div>
      <div data-testid="active-status">{isActive ? "active" : "inactive"}</div>
      <div data-testid="dock-status">{isDocked ? "docked" : "floating"}</div>
      <button data-testid="btn-start" onClick={() => startTour()}>
        Start
      </button>
      <button data-testid="btn-stop" onClick={stopTour}>
        Stop
      </button>
      <button data-testid="btn-next" onClick={nextStep}>
        Next
      </button>
      <button data-testid="btn-dock" onClick={toggleDock}>
        Toggle Dock
      </button>
      <div
        data-tour="verifier-hero"
        data-testid="hero-element"
        style={{ width: "200px", height: "100px" }}
      >
        Hero Target Element
      </div>
    </div>
  );
}

describe("TutorialComponents", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it("renders closed by default", () => {
    render(
      <TutorialProvider>
        <TestController />
        <TutorialSpotlight />
        <TutorialTooltip />
      </TutorialProvider>,
    );

    expect(screen.getByTestId("active-status").textContent).toBe("inactive");
    expect(screen.queryByRole("dialog")).toBeNull();
  });

  it("opens spotlight and anchored tooltip when startTour is called", () => {
    render(
      <TutorialProvider>
        <TestController />
        <TutorialSpotlight />
        <TutorialTooltip />
      </TutorialProvider>,
    );

    fireEvent.click(screen.getByTestId("btn-start"));

    expect(screen.getByTestId("active-status").textContent).toBe("active");
    const dialog = screen.getByRole("dialog");
    expect(dialog).toBeTruthy();
    expect(
      screen.getByText(/AI Risk Manager: Dispute Integrity Gate/i),
    ).toBeTruthy();
    expect(screen.getByText(/REQUIRED ACTION/i)).toBeTruthy();
  });

  it("closes tutorial when Escape key is pressed", () => {
    render(
      <TutorialProvider>
        <TestController />
        <TutorialSpotlight />
        <TutorialTooltip />
      </TutorialProvider>,
    );

    fireEvent.click(screen.getByTestId("btn-start"));
    expect(screen.getByTestId("active-status").textContent).toBe("active");

    fireEvent.keyDown(window, { key: "Escape" });
    expect(screen.getByTestId("active-status").textContent).toBe("inactive");
    expect(screen.queryByRole("dialog")).toBeNull();
  });

  it("supports docking/minimization to a floating pill", () => {
    render(
      <TutorialProvider>
        <TestController />
        <TutorialSpotlight />
        <TutorialTooltip />
      </TutorialProvider>,
    );

    fireEvent.click(screen.getByTestId("btn-start"));
    expect(screen.getByTestId("active-status").textContent).toBe("active");

    // Click dock button on tooltip card
    const dockBtn = screen.getByLabelText(/Dock tutorial/i);
    fireEvent.click(dockBtn);

    expect(screen.getByTestId("dock-status").textContent).toBe("docked");
    expect(screen.getByRole("complementary")).toBeTruthy();
    expect(screen.getByText(/Step 1 of 9:/i)).toBeTruthy();

    // Re-expand from pill
    const resumeBtn = screen.getByTitle(/Expand guidance tooltip/i);
    fireEvent.click(resumeBtn);
    expect(screen.getByTestId("dock-status").textContent).toBe("floating");
    expect(screen.getByRole("dialog")).toBeTruthy();
  });

  it("advances steps cleanly through nextStep", () => {
    render(
      <TutorialProvider>
        <TestController />
        <TutorialSpotlight />
        <TutorialTooltip />
      </TutorialProvider>,
    );

    fireEvent.click(screen.getByTestId("btn-start"));
    expect(screen.getByText(/Step 1 of 9/i)).toBeTruthy();

    fireEvent.click(screen.getByTestId("btn-next"));
    expect(screen.getByText(/Step 2 of 9/i)).toBeTruthy();
    expect(screen.getByText(/Step 1: Evidence Ingestion/i)).toBeTruthy();
  });
});
