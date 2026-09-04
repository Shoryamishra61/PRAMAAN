import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { InteractiveTour } from "./InteractiveTour";

describe("InteractiveTour", () => {
  afterEach(() => {
    cleanup();
  });

  it("renders the tour when open and shows step 1 orientation", () => {
    const handleClose = vi.fn();
    render(
      <InteractiveTour
        isOpen={true}
        onClose={handleClose}
        hasFiles={false}
        hasResult={false}
        hasCheckedCase={false}
        currentJourneyStep={1}
      />,
    );

    expect(screen.getByRole("dialog")).toBeVisible();
    expect(
      screen.getByText(/Interactive Product Tutorial · Step 1 of 10/),
    ).toBeVisible();
    expect(
      screen.getByRole("heading", { name: "AI Risk Manager Overview" }),
    ).toBeVisible();
    expect(
      screen.getByText(
        /Stop merchants losing money to invalid chargeback contests/,
      ),
    ).toBeVisible();
  });

  it("navigates forward to step 2 when Next is clicked", () => {
    const handleClose = vi.fn();
    render(
      <InteractiveTour
        isOpen={true}
        onClose={handleClose}
        hasFiles={true}
        hasResult={false}
        hasCheckedCase={false}
        currentJourneyStep={1}
      />,
    );

    const nextBtn = screen.getByRole("button", { name: /Next/i });
    fireEvent.click(nextBtn);

    expect(
      screen.getByText(/Interactive Product Tutorial · Step 2 of 10/),
    ).toBeVisible();
    expect(
      screen.getByRole("heading", { name: "Multi-File Evidence Ingestion" }),
    ).toBeVisible();
  });

  it("navigates backwards when Back is clicked", () => {
    const handleClose = vi.fn();
    render(
      <InteractiveTour
        isOpen={true}
        onClose={handleClose}
        hasFiles={true}
        hasResult={false}
        hasCheckedCase={false}
        currentJourneyStep={1}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: /Next/i }));
    expect(
      screen.getByText(/Interactive Product Tutorial · Step 2 of 10/),
    ).toBeVisible();

    fireEvent.click(screen.getByRole("button", { name: /Back/i }));
    expect(
      screen.getByText(/Interactive Product Tutorial · Step 1 of 10/),
    ).toBeVisible();
  });

  it("calls onClose when Skip tour button or close icon is clicked", () => {
    const handleClose = vi.fn();
    render(
      <InteractiveTour
        isOpen={true}
        onClose={handleClose}
        hasFiles={false}
        hasResult={false}
        hasCheckedCase={false}
        currentJourneyStep={1}
      />,
    );

    const skipBtn = screen.getByRole("button", { name: /Skip tour/i });
    fireEvent.click(skipBtn);
    expect(handleClose).toHaveBeenCalledTimes(1);

    const closeIcon = screen.getByRole("button", { name: "Exit tutorial" });
    fireEvent.click(closeIcon);
    expect(handleClose).toHaveBeenCalledTimes(2);
  });

  it("closes when Escape key is pressed", () => {
    const handleClose = vi.fn();
    render(
      <InteractiveTour
        isOpen={true}
        onClose={handleClose}
        hasFiles={false}
        hasResult={false}
        hasCheckedCase={false}
        currentJourneyStep={1}
      />,
    );

    fireEvent.keyDown(window, { key: "Escape" });
    expect(handleClose).toHaveBeenCalledTimes(1);
  });

  it("does not render when isOpen is false", () => {
    const handleClose = vi.fn();
    const { container } = render(
      <InteractiveTour
        isOpen={false}
        onClose={handleClose}
        hasFiles={false}
        hasResult={false}
        hasCheckedCase={false}
        currentJourneyStep={1}
      />,
    );

    expect(container.firstChild).toBeNull();
  });
});
