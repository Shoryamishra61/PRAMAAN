import { createContext, useContext } from "react";
import type {
  GuidedTourStep,
  RequiredActionType,
  TourMachineStatus,
  TourPanelSize,
  TourPlacement,
  TourTargetStatus,
  TutorialAppContext,
} from "./types";

export interface TutorialActionsValue {
  startTour: (stepId?: string) => void;
  stopTour: () => void;
  resetTour: () => void;
  nextStep: () => void;
  prevStep: () => void;
  goToStep: (stepId: string) => void;
  setUserOffset: (offset: { x: number; y: number }) => void;
  setPanelSize: (size: TourPanelSize) => void;
  setPlacement: (placement: TourPlacement) => void;
  toggleDock: () => void;
  updateAppContext: (partial: Partial<TutorialAppContext>) => void;
  notifyAction: (actionType: RequiredActionType, payload?: unknown) => void;
}

export interface TutorialContextValue extends TutorialActionsValue {
  isActive: boolean;
  status: TourMachineStatus;
  currentStep: GuidedTourStep | null;
  currentStepIndex: number;
  workflowStepNumber: number | null;
  totalSteps: number;
  appContext: TutorialAppContext;
  targetRect: DOMRect | null;
  targetStatus: TourTargetStatus;
  stuckSeconds: number;
  currentHintLevel: number;
  actionSatisfied: boolean;
  userOffset: { x: number; y: number };
  panelSize: TourPanelSize;
  placement: TourPlacement;
  isDocked: boolean;
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
  selectedScenario: null,
  evaluationView: "debugger",
  activeTab: "debugger",
};

const defaultActionsValue: TutorialActionsValue = {
  startTour: () => {},
  stopTour: () => {},
  resetTour: () => {},
  nextStep: () => {},
  prevStep: () => {},
  goToStep: () => {},
  setUserOffset: () => {},
  setPanelSize: () => {},
  setPlacement: () => {},
  toggleDock: () => {},
  updateAppContext: () => {},
  notifyAction: () => {},
};

const defaultContextValue: TutorialContextValue = {
  isActive: false,
  status: "IDLE",
  currentStep: null,
  currentStepIndex: 0,
  workflowStepNumber: null,
  totalSteps: 8,
  appContext: defaultAppContext,
  targetRect: null,
  targetStatus: "idle",
  stuckSeconds: 0,
  currentHintLevel: 0,
  actionSatisfied: false,
  userOffset: { x: 0, y: 0 },
  panelSize: "standard",
  placement: "auto",
  isDocked: false,
  ...defaultActionsValue,
};

export const TutorialContext = createContext<TutorialContextValue | null>(null);
export const TutorialActionsContext =
  createContext<TutorialActionsValue | null>(null);

export function useTutorial(): TutorialContextValue {
  return useContext(TutorialContext) ?? defaultContextValue;
}

export function useTutorialActions(): TutorialActionsValue {
  return useContext(TutorialActionsContext) ?? defaultActionsValue;
}
