import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import type {
  RequiredActionType,
  TourMachineEvent,
  TourMachineStatus,
  TourPanelSize,
  TourPlacement,
  TourTargetStatus,
  TutorialAppContext,
} from "./types";
import {
  emitTutorialAnalytics,
  TARGET_RESOLUTION_TIMEOUT_MS,
  TUTORIAL_SESSION_KEY,
  TUTORIAL_STEPS,
  TUTORIAL_STORAGE_KEY,
  transitionTourStatus,
  workflowNumberForIndex,
  WORKFLOW_STEP_COUNT,
} from "./tutorialEngine";
import {
  defaultAppContext,
  TutorialActionsContext,
  TutorialContext,
  type TutorialActionsValue,
} from "./useTutorial";

interface TutorialProviderProps {
  children: ReactNode;
  route?: string;
  onNavigate?: (route: string) => void;
}

interface SessionPreferences {
  version: 1;
  panelSize: TourPanelSize;
  placement: TourPlacement;
  userOffset: { x: number; y: number };
}

const RUNNING_STATES = new Set<TourMachineStatus>([
  "STARTING",
  "ACTIVE",
  "WAITING_FOR_TARGET",
  "TRANSITIONING",
  "PAUSED",
]);

function readSessionPreferences(): SessionPreferences {
  const fallback: SessionPreferences = {
    version: 1,
    panelSize: "standard",
    placement: "auto",
    userOffset: { x: 0, y: 0 },
  };
  try {
    const parsed = JSON.parse(
      sessionStorage.getItem(TUTORIAL_SESSION_KEY) ?? "null",
    );
    if (
      parsed?.version === 1 &&
      ["compact", "standard", "expanded"].includes(parsed.panelSize) &&
      [
        "auto",
        "top-left",
        "top-right",
        "bottom-left",
        "bottom-right",
        "side-center",
      ].includes(parsed.placement) &&
      Number.isFinite(parsed.userOffset?.x) &&
      Number.isFinite(parsed.userOffset?.y)
    ) {
      return parsed as SessionPreferences;
    }
  } catch {
    // Disabled or malformed session storage falls back to safe defaults.
  }
  return fallback;
}

export function TutorialProvider({
  children,
  route = "proof",
  onNavigate,
}: TutorialProviderProps) {
  const initialPreferences = useMemo(() => readSessionPreferences(), []);
  const [status, setStatus] = useState<TourMachineStatus>("IDLE");
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [appContext, setAppContext] = useState<TutorialAppContext>({
    ...defaultAppContext,
    route,
  });
  const [targetRect, setTargetRect] = useState<DOMRect | null>(null);
  const [targetStatus, setTargetStatus] = useState<TourTargetStatus>("idle");
  const [stuckSeconds, setStuckSeconds] = useState(0);
  const [currentHintLevel, setCurrentHintLevel] = useState(0);
  const [actionObserved, setActionObserved] = useState(false);
  const [userOffset, setUserOffset] = useState(initialPreferences.userOffset);
  const [panelSize, setPanelSize] = useState<TourPanelSize>(
    initialPreferences.panelSize,
  );
  const [placement, setPlacement] = useState<TourPlacement>(
    initialPreferences.placement,
  );
  const [isDocked, setIsDocked] = useState(false);
  const currentStep = TUTORIAL_STEPS[currentStepIndex] ?? null;
  const isActive = RUNNING_STATES.has(status);
  const resolvedAppContext = useMemo(
    () => (appContext.route === route ? appContext : { ...appContext, route }),
    [appContext, route],
  );
  const actionSatisfied =
    actionObserved || Boolean(currentStep?.isSatisfied(resolvedAppContext));
  const stepStartedAtRef = useRef(0);
  const tourStartedAtRef = useRef(0);
  const launchFocusRef = useRef<HTMLElement | null>(null);
  const observedJourneyRef = useRef(1);

  const send = useCallback((event: TourMachineEvent) => {
    setStatus((current) => transitionTourStatus(current, event));
  }, []);

  const restoreLaunchFocus = useCallback(() => {
    window.setTimeout(() => launchFocusRef.current?.focus(), 0);
  }, []);

  const updateAppContext = useCallback(
    (partial: Partial<TutorialAppContext>) => {
      const stageChanged =
        partial.journeyStep !== undefined &&
        partial.journeyStep !== observedJourneyRef.current;
      if (partial.journeyStep !== undefined)
        observedJourneyRef.current = partial.journeyStep;
      if (stageChanged && isActive && !isDocked && partial.hasResult) {
        const stepId =
          partial.journeyStep === 2
            ? "semantic-grounding"
            : partial.journeyStep === 3
              ? "financial-state"
              : partial.journeyStep === 4
                ? "formal-verification"
                : null;
        if (stepId) {
          setCurrentStepIndex(
            TUTORIAL_STEPS.findIndex((step) => step.id === stepId),
          );
          setTargetRect(null);
          setTargetStatus("resolving");
          setCurrentHintLevel(0);
          setActionObserved(false);
          send("BEGIN_STEP");
        }
      }
      setAppContext((previous) => {
        const changed = (
          Object.keys(partial) as (keyof TutorialAppContext)[]
        ).some((key) => previous[key] !== partial[key]);
        return changed ? { ...previous, ...partial } : previous;
      });
    },
    [isActive, isDocked, send],
  );

  useEffect(() => {
    try {
      const preferences: SessionPreferences = {
        version: 1,
        panelSize,
        placement,
        userOffset,
      };
      sessionStorage.setItem(TUTORIAL_SESSION_KEY, JSON.stringify(preferences));
    } catch {
      // Preferences are optional and scoped to the current browser session.
    }
  }, [panelSize, placement, userOffset]);

  const startTour = useCallback(
    (stepId?: string) => {
      const requested = stepId
        ? TUTORIAL_STEPS.findIndex((step) => step.id === stepId)
        : 0;
      const index = requested >= 0 ? requested : 0;
      launchFocusRef.current =
        document.activeElement instanceof HTMLElement
          ? document.activeElement
          : null;
      onNavigate?.(TUTORIAL_STEPS[index].route);
      setCurrentStepIndex(index);
      setTargetRect(null);
      setTargetStatus("resolving");
      setActionObserved(false);
      setStuckSeconds(0);
      setCurrentHintLevel(0);
      setIsDocked(false);
      tourStartedAtRef.current = Date.now();
      stepStartedAtRef.current = Date.now();
      send("START");
      emitTutorialAnalytics({ type: "tour_started" });
      emitTutorialAnalytics({
        type: "step_entered",
        stepId: TUTORIAL_STEPS[index].id,
        workflowNumber: workflowNumberForIndex(index),
      });
    },
    [onNavigate, send],
  );

  const stopTour = useCallback(() => {
    if (currentStep) {
      emitTutorialAnalytics({ type: "tour_cancelled", stepId: currentStep.id });
    }
    send("CANCEL");
    setTargetRect(null);
    setTargetStatus("idle");
    try {
      localStorage.setItem(
        TUTORIAL_STORAGE_KEY,
        JSON.stringify({ version: 3, outcome: "cancelled" }),
      );
    } catch {
      // Completion persistence is optional.
    }
    restoreLaunchFocus();
  }, [currentStep, restoreLaunchFocus, send]);

  const completeTour = useCallback(() => {
    if (currentStep) {
      emitTutorialAnalytics({
        type: "step_completed",
        stepId: currentStep.id,
        durationMs: Math.max(0, Date.now() - stepStartedAtRef.current),
      });
    }
    send("COMPLETE");
    setTargetRect(null);
    setTargetStatus("idle");
    try {
      localStorage.setItem(
        TUTORIAL_STORAGE_KEY,
        JSON.stringify({
          version: 3,
          outcome: "completed",
          completedAt: new Date().toISOString(),
        }),
      );
    } catch {
      // Completion persistence is optional.
    }
    emitTutorialAnalytics({
      type: "tour_completed",
      totalDurationMs: Math.max(0, Date.now() - tourStartedAtRef.current),
    });
    restoreLaunchFocus();
  }, [currentStep, restoreLaunchFocus, send]);

  const enterStep = useCallback(
    (index: number, event: "NEXT" | "BACK") => {
      if (currentStep) {
        emitTutorialAnalytics({
          type: "step_completed",
          stepId: currentStep.id,
          durationMs: Math.max(0, Date.now() - stepStartedAtRef.current),
        });
      }
      send(event);
      onNavigate?.(TUTORIAL_STEPS[index].route);
      setCurrentStepIndex(index);
      setTargetRect(null);
      setTargetStatus("resolving");
      setActionObserved(false);
      setStuckSeconds(0);
      setCurrentHintLevel(0);
      stepStartedAtRef.current = Date.now();
      emitTutorialAnalytics({
        type: "step_entered",
        stepId: TUTORIAL_STEPS[index].id,
        workflowNumber: workflowNumberForIndex(index),
      });
    },
    [currentStep, onNavigate, send],
  );

  const nextStep = useCallback(() => {
    if (currentStepIndex >= TUTORIAL_STEPS.length - 1) {
      completeTour();
      return;
    }
    enterStep(currentStepIndex + 1, "NEXT");
  }, [completeTour, currentStepIndex, enterStep]);

  const prevStep = useCallback(() => {
    if (currentStepIndex > 0) enterStep(currentStepIndex - 1, "BACK");
  }, [currentStepIndex, enterStep]);

  const goToStep = useCallback(
    (stepId: string) => {
      const index = TUTORIAL_STEPS.findIndex((step) => step.id === stepId);
      if (index >= 0 && index !== currentStepIndex) {
        enterStep(index, index < currentStepIndex ? "BACK" : "NEXT");
      }
    },
    [currentStepIndex, enterStep],
  );

  const resetTour = useCallback(() => {
    try {
      localStorage.removeItem(TUTORIAL_STORAGE_KEY);
      sessionStorage.removeItem(TUTORIAL_SESSION_KEY);
    } catch {
      // Storage is optional.
    }
    send("RESET");
    setUserOffset({ x: 0, y: 0 });
    setPanelSize("standard");
    setPlacement("auto");
    startTour();
  }, [send, startTour]);

  const toggleDock = useCallback(() => {
    setIsDocked((docked) => {
      send(docked ? "RESUME" : "PAUSE");
      return !docked;
    });
  }, [send]);

  const notifyAction = useCallback(
    (actionType: RequiredActionType) => {
      if (isActive && currentStep?.requiredAction === actionType) {
        setActionObserved(true);
      }
    },
    [currentStep, isActive],
  );

  useEffect(() => {
    if (!isActive || isDocked || !currentStep) return;
    let seconds = 0;
    const interval = window.setInterval(() => {
      seconds += 1;
      if (seconds === 15 || seconds === 30) {
        const level = seconds === 15 ? 1 : 2;
        setStuckSeconds(seconds);
        setCurrentHintLevel(level);
        emitTutorialAnalytics({
          type: "hint_escalated",
          stepId: currentStep.id,
          hintLevel: level,
        });
      }
    }, 1_000);
    return () => window.clearInterval(interval);
  }, [currentStep, currentStepIndex, isActive, isDocked]);

  useEffect(() => {
    if (!isActive || isDocked || !currentStep) return;

    let active = true;
    let resolvedElement: HTMLElement | null = null;
    let resizeObserver: ResizeObserver | null = null;
    let observer: MutationObserver | null = null;
    let resolutionTimeout: number | null = null;
    let animationFrame: number | null = null;
    let listenersConnected = false;

    const updateGeometry = () => {
      if (!active || !resolvedElement) return;
      const nextRect = resolvedElement.getBoundingClientRect();
      setTargetRect((previous) => {
        if (
          previous &&
          Math.abs(previous.top - nextRect.top) < 1 &&
          Math.abs(previous.left - nextRect.left) < 1 &&
          Math.abs(previous.width - nextRect.width) < 1 &&
          Math.abs(previous.height - nextRect.height) < 1
        ) {
          return previous;
        }
        return nextRect;
      });
    };

    const scheduleGeometry = () => {
      if (animationFrame !== null) cancelAnimationFrame(animationFrame);
      animationFrame = requestAnimationFrame(updateGeometry);
    };

    const connectElement = (
      element: HTMLElement,
      source: "primary" | "fallback",
    ) => {
      resolvedElement = element;
      setTargetStatus(source);
      updateGeometry();
      send("TARGET_READY");
      if (
        typeof ResizeObserver !== "undefined" &&
        !window.navigator.userAgent.includes("jsdom")
      ) {
        resizeObserver = new ResizeObserver(scheduleGeometry);
        resizeObserver.observe(element);
      }
      const rect = element.getBoundingClientRect();
      if (
        (rect.bottom < 72 || rect.top > window.innerHeight - 40) &&
        typeof element.scrollIntoView === "function" &&
        !window.navigator.userAgent.includes("jsdom")
      ) {
        element.scrollIntoView({ block: "nearest", inline: "nearest" });
      }
    };

    const resolve = (): boolean => {
      if (resolvedElement) return true;
      const primary = document.querySelector<HTMLElement>(
        currentStep.targetSelector ?? "",
      );
      if (primary) {
        connectElement(primary, "primary");
        return true;
      }
      const fallback = currentStep.fallbackSelector
        ? document.querySelector<HTMLElement>(currentStep.fallbackSelector)
        : null;
      if (fallback) {
        connectElement(fallback, "fallback");
        return true;
      }
      return false;
    };

    const initialize = () => {
      if (!active) return;
      setTargetRect(null);
      setTargetStatus("resolving");
      send("BEGIN_STEP");

      if (currentStep.route !== route) return;
      if (!currentStep.targetSelector) {
        setTargetStatus("primary");
        send("TARGET_READY");
        return;
      }

      observer =
        typeof MutationObserver === "undefined"
          ? null
          : new MutationObserver(() => {
              if (resolve()) observer?.disconnect();
            });
      if (!resolve()) {
        observer?.observe(document.body, { childList: true, subtree: true });
      }
      resolutionTimeout = window.setTimeout(() => {
        if (!active || resolvedElement) return;
        observer?.disconnect();
        setTargetStatus("missing");
        send("TARGET_MISSING");
        emitTutorialAnalytics({
          type: "target_missing",
          stepId: currentStep.id,
        });
      }, TARGET_RESOLUTION_TIMEOUT_MS);

      window.addEventListener("resize", scheduleGeometry, { passive: true });
      window.addEventListener("scroll", scheduleGeometry, {
        passive: true,
        capture: true,
      });
      listenersConnected = true;
    };

    animationFrame = requestAnimationFrame(initialize);
    return () => {
      active = false;
      observer?.disconnect();
      resizeObserver?.disconnect();
      if (resolutionTimeout !== null) window.clearTimeout(resolutionTimeout);
      if (animationFrame !== null) cancelAnimationFrame(animationFrame);
      if (listenersConnected) {
        window.removeEventListener("resize", scheduleGeometry);
        window.removeEventListener("scroll", scheduleGeometry, true);
      }
    };
  }, [currentStep, currentStepIndex, isActive, isDocked, route, send]);

  const actionsValue = useMemo<TutorialActionsValue>(
    () => ({
      startTour,
      stopTour,
      resetTour,
      nextStep,
      prevStep,
      goToStep,
      setUserOffset,
      setPanelSize,
      setPlacement,
      toggleDock,
      updateAppContext,
      notifyAction,
    }),
    [
      goToStep,
      nextStep,
      notifyAction,
      prevStep,
      resetTour,
      startTour,
      stopTour,
      toggleDock,
      updateAppContext,
    ],
  );

  const contextValue = useMemo(
    () => ({
      ...actionsValue,
      isActive,
      status,
      currentStep,
      currentStepIndex,
      workflowStepNumber: workflowNumberForIndex(currentStepIndex),
      totalSteps: WORKFLOW_STEP_COUNT,
      appContext: resolvedAppContext,
      targetRect,
      targetStatus,
      stuckSeconds,
      currentHintLevel,
      actionSatisfied,
      userOffset,
      panelSize,
      placement,
      isDocked,
    }),
    [
      actionSatisfied,
      actionsValue,
      currentStep,
      currentStepIndex,
      currentHintLevel,
      isActive,
      isDocked,
      panelSize,
      placement,
      resolvedAppContext,
      status,
      stuckSeconds,
      targetRect,
      targetStatus,
      userOffset,
    ],
  );

  return (
    <TutorialActionsContext.Provider value={actionsValue}>
      <TutorialContext.Provider value={contextValue}>
        {children}
      </TutorialContext.Provider>
    </TutorialActionsContext.Provider>
  );
}
