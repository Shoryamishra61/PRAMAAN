import {
  useState,
  useEffect,
  useCallback,
  useRef,
  type ReactNode,
} from "react";
import { type TutorialAppContext, type RequiredActionType } from "./types";
import {
  TUTORIAL_STEPS,
  TUTORIAL_STORAGE_KEY,
  TUTORIAL_COMPLETED_KEY,
  emitTutorialAnalytics,
} from "./tutorialEngine";
import { TutorialContext, defaultAppContext } from "./useTutorial";

export function TutorialProvider({ children }: { children: ReactNode }) {
  const [isActive, setIsActive] = useState<boolean>(() => {
    try {
      const saved = localStorage.getItem(TUTORIAL_STORAGE_KEY);
      return saved === "true";
    } catch {
      return false;
    }
  });

  const [currentStepIndex, setCurrentStepIndex] = useState<number>(0);
  const [appContext, setAppContext] =
    useState<TutorialAppContext>(defaultAppContext);
  const [targetRect, setTargetRect] = useState<DOMRect | null>(null);
  const [targetElement, setTargetElement] = useState<HTMLElement | null>(null);
  const [isTargetVisible, setIsTargetVisible] = useState<boolean>(false);
  const [stuckSeconds, setStuckSeconds] = useState<number>(0);
  const [currentHintLevel, setCurrentHintLevel] = useState<number>(0);
  const [userOffset, setUserOffset] = useState<{ x: number; y: number }>({
    x: 0,
    y: 0,
  });
  const [isDocked, setIsDocked] = useState<boolean>(false);

  const currentStep = TUTORIAL_STEPS[currentStepIndex] || null;
  const advanceTimerRef = useRef<number | null>(null);
  const stepStartTimeRef = useRef<number>(0);

  const updateAppContext = useCallback(
    (partial: Partial<TutorialAppContext>) => {
      setAppContext((prev) => {
        let changed = false;
        for (const key of Object.keys(
          partial,
        ) as (keyof TutorialAppContext)[]) {
          if (prev[key] !== partial[key]) {
            changed = true;
            break;
          }
        }
        return changed ? { ...prev, ...partial } : prev;
      });
    },
    [],
  );

  const startTour = useCallback((stepId?: string) => {
    let index = 0;
    if (stepId) {
      const found = TUTORIAL_STEPS.findIndex((s) => s.id === stepId);
      if (found !== -1) index = found;
    }
    setCurrentStepIndex(index);
    setIsActive(true);
    setStuckSeconds(0);
    setCurrentHintLevel(0);
    setUserOffset({ x: 0, y: 0 });
    setIsDocked(false);
    stepStartTimeRef.current = Date.now();
    try {
      localStorage.setItem(TUTORIAL_STORAGE_KEY, "true");
    } catch {
      // ignore
    }
    emitTutorialAnalytics({ type: "tour_started" });
    if (TUTORIAL_STEPS[index]) {
      emitTutorialAnalytics({
        type: "step_entered",
        stepId: TUTORIAL_STEPS[index].id,
        stepIndex: index + 1,
      });
    }
  }, []);

  const stopTour = useCallback(() => {
    if (currentStep) {
      emitTutorialAnalytics({
        type: "tour_skipped",
        stepId: currentStep.id,
      });
    }
    setIsActive(false);
    setTargetRect(null);
    setTargetElement(null);
    try {
      localStorage.setItem(TUTORIAL_STORAGE_KEY, "false");
    } catch {
      // ignore
    }
  }, [currentStep]);

  const resetTour = useCallback(() => {
    try {
      localStorage.removeItem(TUTORIAL_STORAGE_KEY);
      localStorage.removeItem(TUTORIAL_COMPLETED_KEY);
    } catch {
      // ignore
    }
    startTour(TUTORIAL_STEPS[0].id);
  }, [startTour]);

  const goToStep = useCallback(
    (stepId: string) => {
      const idx = TUTORIAL_STEPS.findIndex((s) => s.id === stepId);
      if (idx !== -1) {
        if (currentStep) {
          const duration =
            stepStartTimeRef.current > 0
              ? Date.now() - stepStartTimeRef.current
              : 0;
          emitTutorialAnalytics({
            type: "step_completed",
            stepId: currentStep.id,
            durationMs: duration,
          });
        }
        setCurrentStepIndex(idx);
        setStuckSeconds(0);
        setCurrentHintLevel(0);
        stepStartTimeRef.current = Date.now();
        emitTutorialAnalytics({
          type: "step_entered",
          stepId: TUTORIAL_STEPS[idx].id,
          stepIndex: idx + 1,
        });
      }
    },
    [currentStep],
  );

  const nextStep = useCallback(() => {
    if (currentStepIndex < TUTORIAL_STEPS.length - 1) {
      if (currentStep) {
        const duration =
          stepStartTimeRef.current > 0
            ? Date.now() - stepStartTimeRef.current
            : 0;
        emitTutorialAnalytics({
          type: "step_completed",
          stepId: currentStep.id,
          durationMs: duration,
        });
      }
      const nextIdx = currentStepIndex + 1;
      setCurrentStepIndex(nextIdx);
      setStuckSeconds(0);
      setCurrentHintLevel(0);
      stepStartTimeRef.current = Date.now();
      emitTutorialAnalytics({
        type: "step_entered",
        stepId: TUTORIAL_STEPS[nextIdx].id,
        stepIndex: nextIdx + 1,
      });
    } else {
      // completed
      try {
        localStorage.setItem(TUTORIAL_COMPLETED_KEY, "true");
        localStorage.setItem(TUTORIAL_STORAGE_KEY, "false");
      } catch {
        // ignore
      }
      const totalDur =
        stepStartTimeRef.current > 0
          ? Date.now() - stepStartTimeRef.current
          : 0;
      emitTutorialAnalytics({
        type: "tour_completed",
        totalDurationMs: totalDur,
      });
      setIsActive(false);
    }
  }, [currentStepIndex, currentStep]);

  const prevStep = useCallback(() => {
    if (currentStepIndex > 0) {
      const prevIdx = currentStepIndex - 1;
      setCurrentStepIndex(prevIdx);
      setStuckSeconds(0);
      setCurrentHintLevel(0);
      stepStartTimeRef.current = Date.now();
    }
  }, [currentStepIndex]);

  const toggleDock = useCallback(() => {
    setIsDocked((prev) => !prev);
  }, []);

  const notifyAction = useCallback(
    (actionType: RequiredActionType) => {
      if (!isActive || !currentStep) return;
      if (currentStep.requiredAction === actionType) {
        // Short debounce before advancing so user sees the immediate effect
        if (advanceTimerRef.current)
          window.clearTimeout(advanceTimerRef.current);
        advanceTimerRef.current = window.setTimeout(() => {
          nextStep();
        }, 350);
      }
    },
    [isActive, currentStep, nextStep],
  );

  // Inactivity / hint escalation timer
  useEffect(() => {
    if (!isActive || !currentStep) return;
    const interval = window.setInterval(() => {
      setStuckSeconds((prev) => {
        const next = prev + 1;
        if (next === 12 && currentStep.hints.length > 0) {
          setCurrentHintLevel(1);
          emitTutorialAnalytics({
            type: "hint_escalated",
            stepId: currentStep.id,
            hintLevel: 1,
          });
        } else if (next === 24 && currentStep.hints.length > 1) {
          setCurrentHintLevel(2);
          emitTutorialAnalytics({
            type: "hint_escalated",
            stepId: currentStep.id,
            hintLevel: 2,
          });
        }
        return next;
      });
    }, 1000);

    return () => window.clearInterval(interval);
  }, [isActive, currentStep]);

  // Reactive state predicate evaluation
  useEffect(() => {
    if (!isActive || !currentStep) return;

    // First check if step should be skipped based on current app state
    if (currentStep.shouldSkip && currentStep.shouldSkip(appContext)) {
      const timer = window.setTimeout(() => {
        nextStep();
      }, 0);
      return () => window.clearTimeout(timer);
    }

    // Then check if the action or state change has already been satisfied
    if (currentStep.isSatisfied(appContext)) {
      if (advanceTimerRef.current) window.clearTimeout(advanceTimerRef.current);
      advanceTimerRef.current = window.setTimeout(() => {
        nextStep();
      }, 400);
      return () => {
        if (advanceTimerRef.current)
          window.clearTimeout(advanceTimerRef.current);
      };
    }
  }, [isActive, currentStep, appContext, nextStep]);

  // Target element locator, resize observer, and bounding rect tracker
  useEffect(() => {
    if (!isActive || !currentStep) {
      return;
    }

    let isSubscribed = true;

    const isTestEnv =
      typeof window !== "undefined" &&
      window.navigator?.userAgent?.includes("jsdom");

    const isIntro =
      currentStep.id === "step-welcome" ||
      currentStep.preferredPlacement === "center";

    function updateRect() {
      if (!isSubscribed) return;
      if (isIntro) {
        setTargetElement(null);
        setTargetRect(null);
        setIsTargetVisible(true);
        return;
      }
      const el =
        document.querySelector<HTMLElement>(currentStep.targetSelector) ||
        (currentStep.fallbackSelector
          ? document.querySelector<HTMLElement>(currentStep.fallbackSelector)
          : null);

      if (el) {
        const rect = el.getBoundingClientRect();
        const isVisible =
          rect.width > 0 &&
          rect.height > 0 &&
          rect.bottom >= 0 &&
          rect.right >= 0 &&
          rect.top <=
            (window.innerHeight || document.documentElement.clientHeight) &&
          rect.left <=
            (window.innerWidth || document.documentElement.clientWidth);

        setTargetElement(el);
        setTargetRect((prev) => {
          if (
            prev &&
            Math.abs(prev.top - rect.top) < 1 &&
            Math.abs(prev.left - rect.left) < 1 &&
            Math.abs(prev.width - rect.width) < 1 &&
            Math.abs(prev.height - rect.height) < 1
          ) {
            return prev;
          }
          return rect;
        });
        setIsTargetVisible(isVisible);
      } else {
        setTargetElement(null);
        setTargetRect(null);
        setIsTargetVisible(false);
      }
    }

    // Initial query and scroll (only when not intro modal)
    const el = isIntro
      ? null
      : document.querySelector<HTMLElement>(currentStep.targetSelector) ||
        (currentStep.fallbackSelector
          ? document.querySelector<HTMLElement>(currentStep.fallbackSelector)
          : null);

    if (el) {
      el.classList.add("tour-target-elevated");
    }

    if (el && !isTestEnv && typeof el.scrollIntoView === "function") {
      try {
        el.scrollIntoView({
          behavior: "smooth",
          block: "center",
          inline: "center",
        });
      } catch {
        // Fallback
      }
    }

    updateRect();

    // Re-check after 150ms in case smooth scroll or animation is ongoing
    const timeout = window.setTimeout(updateRect, 150);

    // Listeners for window resize and scroll
    window.addEventListener("resize", updateRect, { passive: true });
    window.addEventListener("scroll", updateRect, {
      passive: true,
      capture: true,
    });

    let resizeObserver: ResizeObserver | null = null;
    if (el && typeof ResizeObserver !== "undefined") {
      resizeObserver = new ResizeObserver(updateRect);
      resizeObserver.observe(el);
    }

    return () => {
      isSubscribed = false;
      if (el) {
        el.classList.remove("tour-target-elevated");
      }
      window.clearTimeout(timeout);
      window.removeEventListener("resize", updateRect);
      window.removeEventListener("scroll", updateRect, true);
      if (resizeObserver) {
        resizeObserver.disconnect();
      }
    };
  }, [isActive, currentStep, currentStepIndex]);

  return (
    <TutorialContext.Provider
      value={{
        isActive,
        currentStep,
        currentStepIndex,
        totalSteps: TUTORIAL_STEPS.length,
        appContext,
        targetRect,
        targetElement,
        isTargetVisible,
        stuckSeconds,
        currentHintLevel,
        userOffset,
        isDocked,
        startTour,
        stopTour,
        resetTour,
        nextStep,
        prevStep,
        goToStep,
        setUserOffset,
        toggleDock,
        updateAppContext,
        notifyAction,
      }}
    >
      {children}
    </TutorialContext.Provider>
  );
}
