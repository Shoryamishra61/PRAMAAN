import { createContext, useContext } from "react";
import {
  type GuidedTourStep,
  type TutorialAppContext,
  type RequiredActionType,
} from "./types";

export interface TutorialContextValue {
  isActive: boolean;
  currentStep: GuidedTourStep | null;
  currentStepIndex: number;
  totalSteps: number;
  appContext: TutorialAppContext;
  targetRect: DOMRect | null;
  targetElement: HTMLElement | null;
  isTargetVisible: boolean;
  stuckSeconds: number;
  currentHintLevel: number;
  userOffset: { x: number; y: number };
  isDocked: boolean;
  startTour: (stepId?: string) => void;
  stopTour: () => void;
  resetTour: () => void;
  nextStep: () => void;
  prevStep: () => void;
  goToStep: (stepId: string) => void;
  setUserOffset: (offset: { x: number; y: number }) => void;
  toggleDock: () => void;
  updateAppContext: (partial: Partial<TutorialAppContext>) => void;
  notifyAction: (actionType: RequiredActionType, payload?: unknown) => void;
}

export const defaultAppContext: TutorialAppContext = {
  route: "proof",
  journeyStep: 1,
  hasFiles: false,
  fileCount: 0,
  hasResult: false,
  isEvaluating: false,
  resultVerdict: null,
  hasRepaired: false,
  selectedScenario: "wrong_amount",
  evaluationView: "debugger",
  activeTab: "debugger",
};

const defaultContextValue: TutorialContextValue = {
  isActive: false,
  currentStep: null,
  currentStepIndex: 0,
  totalSteps: 9,
  appContext: defaultAppContext,
  targetRect: null,
  targetElement: null,
  isTargetVisible: false,
  stuckSeconds: 0,
  currentHintLevel: 0,
  userOffset: { x: 0, y: 0 },
  isDocked: false,
  startTour: () => {},
  stopTour: () => {},
  resetTour: () => {},
  nextStep: () => {},
  prevStep: () => {},
  goToStep: () => {},
  setUserOffset: () => {},
  toggleDock: () => {},
  updateAppContext: () => {},
  notifyAction: () => {},
};

export const TutorialContext = createContext<TutorialContextValue | null>(null);

export function useTutorial(): TutorialContextValue {
  const ctx = useContext(TutorialContext);
  return ctx ?? defaultContextValue;
}
