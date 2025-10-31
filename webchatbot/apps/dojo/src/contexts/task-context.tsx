"use client";

import React, { createContext, useContext, useState, useCallback, useEffect } from "react";
import { useCopilotChat } from "@copilotkit/react-core";
import { createCompatibleMessage } from "@/utils/copilotkit-compat";
import type {
  CamundaTask,
  TaskStatusUpdateEvent,
  TaskCompleteEvent,
  TaskFormField,
  TaskListEvent
} from "@/types/task-events";

// Define missing types locally
type TaskActionEvent = {
  type: string;
  taskId: string;
  action: string;
  variables?: any;
  userId?: string;
  assignee?: string;
  timestamp: number;
};

type TaskFormEvent = {
  type: string;
  taskId: string;
  formData: Record<string, any>;
  userId?: string;
  timestamp: number;
};

type TaskStatusEvent = {
  type: string;
  taskId: string;
  status: string;
  assignee?: string;
  timestamp: number;
};

interface TaskContextValue {
  // State
  tasks: CamundaTask[];
  selectedTaskId?: string;
  expandedTasks: Set<string>;
  isLoading: boolean;
  isSubmitting: boolean;
  error?: string;
  
  // Task management
  setTasks: (tasks: CamundaTask[]) => void;
  addTask: (task: CamundaTask) => void;
  updateTask: (taskId: string, updates: Partial<CamundaTask>) => void;
  removeTask: (taskId: string) => void;
  clearTasks: () => void;
  
  // Task actions
  completeTask: (taskId: string, variables?: Record<string, any>) => Promise<void>;
  claimTask: (taskId: string) => Promise<void>;
  unclaimTask: (taskId: string) => Promise<void>;
  delegateTask: (taskId: string, assignee: string) => Promise<void>;
  
  // Task filtering and sorting
  getTasksByStatus: (status: string) => CamundaTask[];
  getTasksByPriority: (priority: CamundaTask['priority']) => CamundaTask[];
  getTasksByProcess: (processKey: string) => CamundaTask[];
  searchTasks: (query: string) => CamundaTask[];
  
  // Task forms
  getTaskForm: (taskId: string) => Promise<any>;
  submitTaskForm: (taskId: string, formData: Record<string, any>) => Promise<void>;
  
  // UI state
  setSelectedTaskId: (taskId: string | undefined) => void;
  toggleTaskExpanded: (taskId: string) => void;
}

const TaskContext = createContext<TaskContextValue | undefined>(undefined);

interface TaskContextProviderProps {
  children: React.ReactNode;
  userId?: string;
  isGuest?: boolean;
  onTaskAction?: (action: TaskActionEvent) => void;
  onTaskUpdate?: (task: CamundaTask) => void;
}

export function TaskContextProvider({ 
  children, 
  userId,
  isGuest = false,
  onTaskAction,
  onTaskUpdate
}: TaskContextProviderProps) {
  // State management
  const [tasks, setTasksState] = useState<CamundaTask[]>([]);
  const [selectedTaskId, setSelectedTaskId] = useState<string | undefined>();
  const [expandedTasks, setExpandedTasks] = useState<Set<string>>(new Set());
  const [isLoading, setIsLoading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | undefined>();

  // Get CopilotKit chat functions
  const { appendMessage } = useCopilotChat();

  // Task management
  const setTasks = useCallback((newTasks: CamundaTask[]) => {
    setTasksState(newTasks);
    setError(undefined);
    console.log('TaskContext: Tasks updated', { count: newTasks.length });
  }, []);

  const addTask = useCallback((task: CamundaTask) => {
    setTasksState(prev => {
      const exists = prev.find(t => t.id === task.id);
      if (exists) {
        return prev.map(t => t.id === task.id ? task : t);
      }
      return [...prev, task];
    });
    console.log('TaskContext: Task added/updated', task.id);
  }, []);

  const updateTask = useCallback((taskId: string, updates: Partial<CamundaTask>) => {
    setTasksState(prev => 
      prev.map(task => 
        task.id === taskId 
          ? { ...task, ...updates } 
          : task
      )
    );
    
    const updatedTask = tasks.find(t => t.id === taskId);
    if (updatedTask && onTaskUpdate) {
      onTaskUpdate({ ...updatedTask, ...updates });
    }
    
    console.log('TaskContext: Task updated', taskId, updates);
  }, [tasks, onTaskUpdate]);

  const removeTask = useCallback((taskId: string) => {
    setTasksState(prev => prev.filter(task => task.id !== taskId));
    
    // Clear selection if removed task was selected
    if (selectedTaskId === taskId) {
      setSelectedTaskId(undefined);
    }
    
    // Remove from expanded tasks
    setExpandedTasks(prev => {
      const newSet = new Set(prev);
      newSet.delete(taskId);
      return newSet;
    });
    
    console.log('TaskContext: Task removed', taskId);
  }, [selectedTaskId]);

  const clearTasks = useCallback(() => {
    setTasksState([]);
    setSelectedTaskId(undefined);
    setExpandedTasks(new Set());
    setError(undefined);
    console.log('TaskContext: All tasks cleared');
  }, []);

  // Task actions
  const completeTask = useCallback(async (taskId: string, variables?: Record<string, any>): Promise<void> => {
    if (isGuest) {
      setError('Task completion requires authentication');
      return;
    }

    setIsSubmitting(true);
    setError(undefined);

    try {
      const actionEvent: TaskActionEvent = {
        type: "taskAction",
        action: "complete",
        taskId,
        variables,
        userId,
        timestamp: Date.now()
      };

      console.log('TaskContext: Completing task', actionEvent);

      // Emit task action event for backend processing
      window.dispatchEvent(new CustomEvent('task-action', {
        detail: actionEvent
      }));

      onTaskAction?.(actionEvent);

      // Show completion message
      appendMessage(createCompatibleMessage({
        id: `task_complete_${Date.now()}`,
        role: 'assistant',
        content: `Task completed successfully.`
      }));

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to complete task';
      setError(errorMessage);
      console.error('TaskContext: Task completion error', error);
      
      appendMessage(createCompatibleMessage({
        id: `task_error_${Date.now()}`,
        role: 'assistant',
        content: `Error completing task: ${errorMessage}`
      }));
    } finally {
      setIsSubmitting(false);
    }
  }, [isGuest, userId, onTaskAction, appendMessage]);

  const claimTask = useCallback(async (taskId: string): Promise<void> => {
    if (isGuest) {
      setError('Task claiming requires authentication');
      return;
    }

    setIsSubmitting(true);
    
    try {
      const actionEvent: TaskActionEvent = {
        type: "taskAction",
        action: "claim",
        taskId,
        userId,
        timestamp: Date.now()
      };

      console.log('TaskContext: Claiming task', actionEvent);
      
      window.dispatchEvent(new CustomEvent('task-action', {
        detail: actionEvent
      }));

      onTaskAction?.(actionEvent);

      // Update task locally
      updateTask(taskId, { assignee: userId });

    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to claim task');
      console.error('TaskContext: Task claim error', error);
    } finally {
      setIsSubmitting(false);
    }
  }, [isGuest, userId, onTaskAction, updateTask]);

  const unclaimTask = useCallback(async (taskId: string): Promise<void> => {
    if (isGuest) {
      setError('Task unclaiming requires authentication');
      return;
    }

    setIsSubmitting(true);
    
    try {
      const actionEvent: TaskActionEvent = {
        type: "taskAction",
        action: "unclaim", 
        taskId,
        userId,
        timestamp: Date.now()
      };

      console.log('TaskContext: Unclaiming task', actionEvent);
      
      window.dispatchEvent(new CustomEvent('task-action', {
        detail: actionEvent
      }));

      onTaskAction?.(actionEvent);

      // Update task locally
      updateTask(taskId, { assignee: undefined });

    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to unclaim task');
      console.error('TaskContext: Task unclaim error', error);
    } finally {
      setIsSubmitting(false);
    }
  }, [isGuest, userId, onTaskAction, updateTask]);

  const delegateTask = useCallback(async (taskId: string, assignee: string): Promise<void> => {
    if (isGuest) {
      setError('Task delegation requires authentication');
      return;
    }

    setIsSubmitting(true);
    
    try {
      const actionEvent: TaskActionEvent = {
        type: "taskAction",
        action: "delegate",
        taskId,
        assignee,
        userId,
        timestamp: Date.now()
      };

      console.log('TaskContext: Delegating task', actionEvent);
      
      window.dispatchEvent(new CustomEvent('task-action', {
        detail: actionEvent
      }));

      onTaskAction?.(actionEvent);

      // Update task locally
      updateTask(taskId, { assignee });

    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to delegate task');
      console.error('TaskContext: Task delegation error', error);
    } finally {
      setIsSubmitting(false);
    }
  }, [isGuest, userId, onTaskAction, updateTask]);

  // Task filtering and searching
  const getTasksByStatus = useCallback((status: string): CamundaTask[] => {
    return tasks.filter(task => {
      // Map status to task properties
      switch (status.toLowerCase()) {
        case 'pending':
          return !task.assignee;
        case 'assigned':
          return !!task.assignee;
        case 'overdue':
          return task.due && new Date(task.due) < new Date();
        default:
          return true;
      }
    });
  }, [tasks]);

  const getTasksByPriority = useCallback((priority: CamundaTask['priority']): CamundaTask[] => {
    return tasks.filter(task => task.priority === priority);
  }, [tasks]);

  const getTasksByProcess = useCallback((processKey: string): CamundaTask[] => {
    return tasks.filter(task => task.processDefinitionKey === processKey);
  }, [tasks]);

  const searchTasks = useCallback((query: string): CamundaTask[] => {
    const lowercaseQuery = query.toLowerCase();
    return tasks.filter(task => 
      task.name.toLowerCase().includes(lowercaseQuery) ||
      task.description?.toLowerCase().includes(lowercaseQuery) ||
      task.processDefinitionKey.toLowerCase().includes(lowercaseQuery)
    );
  }, [tasks]);

  // Task forms
  const getTaskForm = useCallback(async (taskId: string): Promise<any> => {
    if (isGuest) {
      throw new Error('Task form access requires authentication');
    }

    setIsLoading(true);
    setError(undefined);
    
    try {
      const task = tasks.find(t => t.id === taskId);
      if (!task?.formKey) {
        return null;
      }

      // Emit form request event
      const formEvent = {
        type: "taskFormRequest",
        taskId,
        formKey: task.formKey,
        userId,
        timestamp: Date.now()
      };

      window.dispatchEvent(new CustomEvent('task-form-request', {
        detail: formEvent
      }));

      console.log('TaskContext: Task form requested', formEvent);
      
      // Return placeholder form for now - in real implementation, this would fetch from backend
      return {
        formKey: task.formKey,
        fields: [],
        data: task.variables || {}
      };

    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to get task form');
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, [tasks, isGuest, userId]);

  const submitTaskForm = useCallback(async (taskId: string, formData: Record<string, any>): Promise<void> => {
    if (isGuest) {
      setError('Task form submission requires authentication');
      return;
    }

    setIsSubmitting(true);
    setError(undefined);
    
    try {
      const formEvent: TaskFormEvent = {
        type: "taskFormSubmit",
        taskId,
        formData,
        userId,
        timestamp: Date.now()
      };

      console.log('TaskContext: Task form submitted', formEvent);
      
      window.dispatchEvent(new CustomEvent('task-form-submit', {
        detail: formEvent
      }));

      // Update task variables locally
      updateTask(taskId, { 
        variables: { 
          ...tasks.find(t => t.id === taskId)?.variables,
          ...formData 
        }
      });

      appendMessage(createCompatibleMessage({
        id: `task_form_submit_${Date.now()}`,
        role: 'assistant',
        content: `Task form submitted successfully.`
      }));

    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to submit task form');
      console.error('TaskContext: Task form submission error', error);
    } finally {
      setIsSubmitting(false);
    }
  }, [isGuest, userId, tasks, updateTask, appendMessage]);

  // UI state management
  const toggleTaskExpanded = useCallback((taskId: string) => {
    setExpandedTasks(prev => {
      const newSet = new Set(prev);
      if (newSet.has(taskId)) {
        newSet.delete(taskId);
      } else {
        newSet.add(taskId);
      }
      return newSet;
    });
  }, []);

  // Listen for task events from external sources
  useEffect(() => {
    const handleTaskListEvent = (event: CustomEvent<TaskListEvent>) => {
      setTasks(event.detail.tasks);
      setError(undefined);
    };

    const handleTaskStatusEvent = (event: CustomEvent<TaskStatusEvent>) => {
      const { taskId, status, assignee } = event.detail;
      updateTask(taskId, { assignee: status === 'assigned' ? assignee : undefined });
    };

    const handleTaskError = (event: CustomEvent<{ taskId: string; error: string }>) => {
      setError(event.detail.error);
      setIsSubmitting(false);
      setIsLoading(false);
    };

    window.addEventListener('task-list', handleTaskListEvent as EventListener);
    window.addEventListener('task-status', handleTaskStatusEvent as EventListener);
    window.addEventListener('task-error', handleTaskError as EventListener);

    return () => {
      window.removeEventListener('task-list', handleTaskListEvent as EventListener);
      window.removeEventListener('task-status', handleTaskStatusEvent as EventListener);
      window.removeEventListener('task-error', handleTaskError as EventListener);
    };
  }, [setTasks, updateTask]);

  const value: TaskContextValue = {
    // State
    tasks,
    selectedTaskId,
    expandedTasks,
    isLoading,
    isSubmitting,
    error,
    
    // Task management
    setTasks,
    addTask,
    updateTask,
    removeTask,
    clearTasks,
    
    // Task actions
    completeTask,
    claimTask,
    unclaimTask,
    delegateTask,
    
    // Filtering and searching
    getTasksByStatus,
    getTasksByPriority,
    getTasksByProcess,
    searchTasks,
    
    // Forms
    getTaskForm,
    submitTaskForm,
    
    // UI state
    setSelectedTaskId,
    toggleTaskExpanded,
  };

  return (
    <TaskContext.Provider value={value}>
      {children}
    </TaskContext.Provider>
  );
}

export function useTask(): TaskContextValue {
  const context = useContext(TaskContext);
  if (!context) {
    throw new Error("useTask must be used within TaskContextProvider");
  }
  return context;
}

// Hook for task event handling
export function useTaskEvents() {
  const { setTasks, addTask, updateTask } = useTask();

  useEffect(() => {
    const handleTaskEvents = (event: CustomEvent) => {
      const { type, data } = event.detail;
      
      switch (type) {
        case 'taskList':
          setTasks(data.tasks);
          break;
        case 'taskAdded':
          addTask(data.task);
          break;
        case 'taskUpdated':
          updateTask(data.taskId, data.updates);
          break;
      }
    };

    window.addEventListener('task-event', handleTaskEvents as EventListener);
    return () => {
      window.removeEventListener('task-event', handleTaskEvents as EventListener);
    };
  }, [setTasks, addTask, updateTask]);
}