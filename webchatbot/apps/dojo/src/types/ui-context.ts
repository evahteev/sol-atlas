export type UiModeId =
  | "start"
  | "tasks"
  | "groups"
  | "profile"
  | "catalog"
  | "chat";

export interface UiMode {
  id: UiModeId;
  label: string;
  emoji?: string;
  description?: string;
  requiresAuth?: boolean;
  showInMenu?: boolean;
  badgeCount?: number;
}

export interface UiQuickPrompt {
  id: string;
  text: string;
}

export type ScopeControlId = "edit_groups" | "all_sources" | "my_groups" | string;

export interface UiScopeControl {
  id: ScopeControlId;
  label: string;
  emoji?: string;
  selected?: boolean;
}

export interface UiUserInfo {
  userId: string;
  displayName?: string;
  language?: string;
}

export interface UiContextEvent {
  type: "uiContext";
  contextId: string;
  timestamp: number;
  activeMode: UiModeId;
  modes: UiMode[];
  quickPrompts?: UiQuickPrompt[];
  scopeControls?: UiScopeControl[];
  userInfo?: UiUserInfo;
  metadata?: Record<string, unknown>;
}

export type TaskStatus = "pending" | "completed" | "failed";

export interface TaskSummary {
  id: string;
  name: string;
  status: TaskStatus;
  createdAt?: number;
  dueAt?: number;
  processDefinition?: string;
  priority?: number;
  metadata?: Record<string, unknown>;
}

export interface EmptyTaskState {
  title: string;
  message: string;
  actions?: {
    id: string;
    label: string;
  }[];
}

export interface TaskListEvent {
  type: "taskList";
  timestamp: number;
  source?: string;
  tasks: TaskSummary[];
  selectedTaskId?: string;
  emptyState?: EmptyTaskState;
  pagination?: {
    limit: number;
    offset: number;
    total: number;
  };
  traceId?: string;
}

export type UiContextPayload = UiContextEvent;
export type TaskListPayload = TaskListEvent;

export interface UiContextState {
  loading: boolean;
  uiContext?: UiContextPayload;
  taskList?: TaskListPayload;
}

export interface UiCommandPayload {
  commandId: string;
  payload?: Record<string, unknown>;
}
