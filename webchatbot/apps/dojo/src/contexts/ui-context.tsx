"use client";

import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import type {
  TaskListPayload,
  UiCommandPayload,
  UiContextPayload,
  UiContextState,
} from "@/types/ui-context";
import { MOCK_TASK_LIST, MOCK_UI_CONTEXT } from "@/mocks/ui-context";

interface UiContextValue extends UiContextState {
  sendCommand: (command: UiCommandPayload) => void;
  sendQuickPrompt: (promptId: string, text: string) => void;
}

const UiContext = createContext<UiContextValue | undefined>(undefined);

export function UiContextProvider({ children }: { children: React.ReactNode }) {
  const [uiContext, setUiContext] = useState<UiContextPayload | undefined>();
  const [taskList, setTaskList] = useState<TaskListPayload | undefined>();
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Listen for ui-context events from bot-api-agent
    const handleUiContext = (event: Event) => {
      const customEvent = event as CustomEvent;
      const contextData = customEvent.detail;
      
      console.log('UiContext: Received ui-context event', contextData);
      
      // Update UI context with real data
      setUiContext(contextData);
      setLoading(false);
    };

    // Listen for task-list events
    const handleTaskList = (event: Event) => {
      const customEvent = event as CustomEvent;
      const taskData = customEvent.detail;
      
      console.log('UiContext: Received task-list event', taskData);
      setTaskList(taskData);
    };

    window.addEventListener('ui-context', handleUiContext);
    window.addEventListener('task-list', handleTaskList);

    // Initialize with mock data if no real data comes in
    const timeout = window.setTimeout(() => {
      if (!uiContext) {
        setUiContext(MOCK_UI_CONTEXT);
        setTaskList(MOCK_TASK_LIST);
        setLoading(false);
      }
    }, 2000);

    return () => {
      window.removeEventListener('ui-context', handleUiContext);
      window.removeEventListener('task-list', handleTaskList);
      window.clearTimeout(timeout);
    };
  }, [uiContext]);

  const sendCommand = useCallback(
    (command: UiCommandPayload) => {
      console.debug("UI command dispatched", command);

      // Optimistic UI updates until real backend wiring is complete
      setUiContext((prev) => {
        if (!prev) return prev;

        if (prev.modes.some((mode) => mode.id === command.commandId)) {
          return { ...prev, activeMode: command.commandId as typeof prev.activeMode };
        }

        if (command.commandId === "scope_toggle" && command.payload?.scopeId) {
          const scopeId = String(command.payload.scopeId);
          return {
            ...prev,
            scopeControls: prev.scopeControls?.map((control) =>
              control.id === scopeId
                ? { ...control, selected: !control.selected }
                : control,
            ),
          };
        }

        return prev;
      });
    },
    [],
  );

  const sendQuickPrompt = useCallback(
    (promptId: string, text: string) => {
      sendCommand({
        commandId: "quick_prompt",
        payload: { promptId, text },
      });
    },
    [sendCommand],
  );

  const value = useMemo<UiContextValue>(
    () => ({
      loading,
      uiContext,
      taskList,
      sendCommand,
      sendQuickPrompt,
    }),
    [loading, sendCommand, sendQuickPrompt, taskList, uiContext],
  );

  return <UiContext.Provider value={value}>{children}</UiContext.Provider>;
}

export function useUiContext(): UiContextValue {
  const context = useContext(UiContext);
  if (!context) {
    throw new Error("useUiContext must be used within UiContextProvider");
  }
  return context;
}
