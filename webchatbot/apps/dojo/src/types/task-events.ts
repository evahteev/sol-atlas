/**
 * Task Event Types for Camunda Integration
 * 
 * Defines TypeScript interfaces for Camunda task rendering, completion,
 * and workflow management in the chat interface.
 */

import type { AppBaseEvent } from "./app-events";

// Task metadata and structure
export interface CamundaTask {
  id: string;
  name: string;
  description?: string;
  assignee?: string;
  created: string;
  due?: string;
  priority: "low" | "medium" | "high" | "critical";
  processInstanceId: string;
  processDefinitionKey: string;
  formKey?: string;
  variables?: Record<string, any>;
}

// Task form field definitions
export interface TaskFormField {
  id: string;
  name: string;
  type: "string" | "boolean" | "long" | "double" | "date" | "enum";
  label: string;
  defaultValue?: any;
  required: boolean;
  readonly: boolean;
  constraints?: {
    required?: boolean;
    min?: number;
    max?: number;
    pattern?: string;
  };
  enumValues?: Array<{
    id: string;
    name: string;
  }>;
}

// Task rendering events
export interface TaskRenderEvent extends AppBaseEvent {
  type: "taskRender";
  task: CamundaTask;
  formFields: TaskFormField[];
  messageId: string;
  timestamp: number;
}

export interface TaskListEvent extends AppBaseEvent {
  type: "taskList";
  tasks: CamundaTask[];
  totalCount: number;
  filters?: {
    assignee?: string;
    processDefinitionKey?: string;
    priority?: string[];
  };
  timestamp: number;
}

// Task interaction events
export interface TaskClaimEvent extends AppBaseEvent {
  type: "taskClaim";
  taskId: string;
  userId: string;
  timestamp: number;
}

export interface TaskCompleteEvent extends AppBaseEvent {
  type: "taskComplete";
  taskId: string;
  formData: Record<string, any>;
  userId: string;
  timestamp: number;
}

export interface TaskAssignEvent extends AppBaseEvent {
  type: "taskAssign";
  taskId: string;
  assigneeId: string;
  assignedBy: string;
  timestamp: number;
}

// Task status updates
export interface TaskStatusUpdateEvent extends AppBaseEvent {
  type: "taskStatusUpdate";
  taskId: string;
  status: "created" | "assigned" | "completed" | "cancelled";
  assignee?: string;
  completedBy?: string;
  completedAt?: string;
  timestamp: number;
}

// Task error events
export interface TaskErrorEvent extends AppBaseEvent {
  type: "taskError";
  taskId: string;
  error: string;
  code: string;
  timestamp: number;
}

// Task notification events
export interface TaskNotificationEvent extends AppBaseEvent {
  type: "taskNotification";
  taskId: string;
  notificationType: "assigned" | "due_soon" | "overdue" | "completed";
  message: string;
  recipients: string[];
  timestamp: number;
}

// Task workflow context
export interface TaskWorkflowContext {
  processInstanceId: string;
  processDefinitionKey: string;
  businessKey?: string;
  variables: Record<string, any>;
  activeTaskIds: string[];
}

export interface TaskWorkflowEvent extends AppBaseEvent {
  type: "taskWorkflow";
  context: TaskWorkflowContext;
  timestamp: number;
}

// Union type for all task events
export type TaskEvent = 
  | TaskRenderEvent
  | TaskListEvent
  | TaskClaimEvent
  | TaskCompleteEvent
  | TaskAssignEvent
  | TaskStatusUpdateEvent
  | TaskErrorEvent
  | TaskNotificationEvent
  | TaskWorkflowEvent;