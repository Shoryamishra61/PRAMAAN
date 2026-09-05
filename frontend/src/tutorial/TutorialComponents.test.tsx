import {
  act,
  cleanup,
  fireEvent,
  render,
  screen,
} from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  TARGET_RESOLUTION_TIMEOUT_MS,
  TUTORIAL_STORAGE_KEY,
  TutorialProvider,
  TutorialSpotlight,
  TutorialTooltip,
  useTutorial,
} from "./index";

function TestController() {
  const {
    isActive,
    status,
    startTour,
    nextStep,
    toggleDock,
    isDocked,
    updateAppContext,
  } = useTutorial();
  return (
    <div>
      <output data-testid="active">{isActive ? "active" : "inactive"}</output>
      <output data-testid="status">{status}</output>
      <output data-testid="docked">{isDocked ? "docked" : "floating"}</output>
      <button onClick={() => startTour()}>Open tour</button>
      <button onClick={() => startTour("decision-provenance")}>
        Open final
      </button>
      <button onClick={nextStep}>Controller next</button>
      <button onClick={toggleDock}>Controller dock</button>
      <button
        onClick={() =>
          updateAppContext({
            journeyStep: 2,
            hasResult: true,
            resultVerdict: "BLOCK",
          })
        }
      >
        Observe evaluated case
      </button>
      <div data-tour="verifier-hero">Hero context</div>
    </div>
  );
}

function renderTour(route = "proof") {
  return render(
    <TutorialProvider route={route}>
      <TestController />
      <TutorialSpotlight />
      <TutorialTooltip />
    </TutorialProvider>,
  );
}

describe("TutorialComponents", () => {
  beforeEach(() => {
    localStorage.clear();
    sessionStorage.clear();
  });

  afterEach(() => {
    cleanup();
    vi.useRealTimers();
  });

  it("opens an unnumbered welcome with every escape path visible", () => {
    renderTour();
    fireEvent.click(screen.getByText("Open tour"));
    expect(screen.getByTestId("active").textContent).toBe("active");
    expect(screen.getByText("Welcome")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Back" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Start" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Skip" })).toBeTruthy();
    expect(
      screen.getByRole("button", { name: "Close product tour" }),
    ).toBeTruthy();
  });

  it("supports manual next, back, keyboard navigation, and Escape", () => {
    renderTour();
    fireEvent.click(screen.getByText("Open tour"));
    fireEvent.click(screen.getByRole("button", { name: "Start" }));
    expect(screen.getByText("Step 1 of 8")).toBeTruthy();
    fireEvent.keyDown(window, { key: "ArrowRight" });
    expect(screen.getByText("Step 2 of 8")).toBeTruthy();
    fireEvent.keyDown(window, { key: "ArrowLeft" });
    expect(screen.getByText("Step 1 of 8")).toBeTruthy();
    fireEvent.keyDown(window, { key: "Escape" });
    expect(screen.getByTestId("status").textContent).toBe("CANCELLED");
    expect(screen.queryByRole("dialog")).toBeNull();
  });

  it("follows an actual case result without requiring manual Next clicks", () => {
    renderTour();
    fireEvent.click(screen.getByText("Open tour"));
    fireEvent.click(screen.getByText("Observe evaluated case"));
    expect(
      screen.getByRole("heading", {
        name: "Semantic extraction and exact grounding",
      }),
    ).toBeVisible();
    expect(screen.getByText(/This case has a local hold/)).toBeVisible();
  });

  it("minimizes without losing progress and restores the card", () => {
    renderTour();
    fireEvent.click(screen.getByText("Open tour"));
    fireEvent.click(
      screen.getByRole("button", { name: "Minimize product tour" }),
    );
    expect(screen.getByTestId("docked").textContent).toBe("docked");
    fireEvent.click(screen.getByTitle("Expand product tour"));
    expect(screen.getByTestId("docked").textContent).toBe("floating");
    expect(screen.getByRole("dialog")).toBeTruthy();
  });

  it("bounds missing-target resolution and preserves manual progress", () => {
    vi.useFakeTimers();
    renderTour("decision-engine");
    fireEvent.click(screen.getByText("Open final"));
    act(() => {
      vi.advanceTimersByTime(20);
    });
    act(() => {
      vi.advanceTimersByTime(TARGET_RESOLUTION_TIMEOUT_MS + 1);
    });
    expect(screen.getByText(/target is not available/i)).toBeTruthy();
    expect(screen.getByRole("button", { name: "Finish" })).toBeTruthy();
  });

  it("persists size and placement only for the current session", () => {
    renderTour();
    fireEvent.click(screen.getByText("Open tour"));
    fireEvent.change(screen.getByLabelText("Tour card size"), {
      target: { value: "compact" },
    });
    fireEvent.change(screen.getByLabelText("Tour card position"), {
      target: { value: "top-left" },
    });
    expect(sessionStorage.getItem("pramaan.tour.preferences.v1")).toContain(
      '"panelSize":"compact"',
    );
    expect(localStorage.getItem(TUTORIAL_STORAGE_KEY)).toBeNull();
  });

  it("reaches COMPLETED and never leaves a stuck final card", () => {
    renderTour("decision-engine");
    fireEvent.click(screen.getByText("Open final"));
    fireEvent.click(screen.getByRole("button", { name: "Finish" }));
    expect(screen.getByTestId("status").textContent).toBe("COMPLETED");
    expect(screen.queryByRole("dialog")).toBeNull();
    expect(localStorage.getItem(TUTORIAL_STORAGE_KEY)).toContain(
      '"outcome":"completed"',
    );
  });
});
