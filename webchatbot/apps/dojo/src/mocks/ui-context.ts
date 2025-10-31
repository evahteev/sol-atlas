import type { TaskListPayload, UiContextPayload } from "@/types/ui-context";

export const MOCK_UI_CONTEXT: UiContextPayload = {
  type: "uiContext",
  contextId: "mock-context",
  timestamp: Date.now(),
  activeMode: "start",
  modes: [
    { id: "start", label: "🏠 Start", emoji: "🏠", showInMenu: true },
    { id: "tasks", label: "📋 Tasks", emoji: "📋", showInMenu: true, requiresAuth: true, badgeCount: 2 },
    { id: "groups", label: "👥 Groups", emoji: "👥", showInMenu: true, requiresAuth: true },
    { id: "profile", label: "👤 Profile", emoji: "👤", showInMenu: true, requiresAuth: true },
    { id: "catalog", label: "📚 Catalog", emoji: "📚", showInMenu: true },
  ],
  quickPrompts: [
    { id: "prompt_group_update", text: "Summarize the latest group updates" },
    { id: "prompt_helpdesk", text: "Help desk: troubleshooting tips" },
    { id: "prompt_weekly_digest", text: "Prepare weekly digest" },
  ],
  scopeControls: [
    { id: "edit_groups", label: "Edit", emoji: "⚙️", selected: false },
    { id: "all_sources", label: "All", emoji: "🌐", selected: true },
    { id: "my_groups", label: "Mine", emoji: "🎯", selected: false },
  ],
  userInfo: { userId: "mock-user", displayName: "Luka User", language: "en" },
};

export const MOCK_TASK_LIST: TaskListPayload = {
  type: "taskList",
  timestamp: Date.now(),
  source: "chatbot_start",
  tasks: [
    {
      id: "task-1",
      name: "Verify knowledge base",
      status: "pending",
      createdAt: Date.now() - 1000 * 60 * 60,
      metadata: { emoji: "📋", groupId: "group-1" },
    },
    {
      id: "task-2",
      name: "Review escalation request",
      status: "pending",
      createdAt: Date.now() - 1000 * 60 * 20,
      metadata: { emoji: "⚠️", priority: 2 },
    },
  ],
  selectedTaskId: "task-1",
  pagination: { limit: 10, offset: 0, total: 2 },
};
