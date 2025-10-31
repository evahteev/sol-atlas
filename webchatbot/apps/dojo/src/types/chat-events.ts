/**
 * Chat Event Types - Main Index
 * 
 * Combines all event types for the full-screen chat implementation.
 * This file serves as the main entry point for all custom event types.
 */

// Re-export all event types
export * from "./keyboard-events";
export * from "./command-events";
export * from "./task-events";
export * from "./guest-events";

// Import union types
import type { KeyboardEvent } from "./keyboard-events";
import type { CommandEvent } from "./command-events";
import type { TaskEvent } from "./task-events";
import type { GuestEvent } from "./guest-events";
import type { BaseEvent } from "@ag-ui/core";

// Main union type for all custom chat events
export type ChatEvent = 
  | KeyboardEvent
  | CommandEvent
  | TaskEvent
  | GuestEvent;

// Extended event type that includes both AG-UI core events and our custom events
export type ExtendedChatEvent = BaseEvent | ChatEvent;

// Event type guards for type safety
export function isKeyboardEvent(event: ExtendedChatEvent): event is KeyboardEvent {
  return event.type.includes("Keyboard") || 
         event.type === "replyKeyboard" || 
         event.type === "inlineKeyboard" ||
         event.type === "removeKeyboard";
}

export function isCommandEvent(event: ExtendedChatEvent): event is CommandEvent {
  return event.type.includes("command") || 
         event.type === "commandExecution" ||
         event.type === "commandResult" ||
         event.type === "commandError" ||
         event.type === "guestRestriction" ||
         event.type === "commandHelp" ||
         event.type === "availableCommands";
}

export function isTaskEvent(event: ExtendedChatEvent): event is TaskEvent {
  return event.type.includes("task") ||
         event.type === "taskRender" ||
         event.type === "taskList" ||
         event.type === "taskClaim" ||
         event.type === "taskComplete" ||
         event.type === "taskAssign" ||
         event.type === "taskStatusUpdate" ||
         event.type === "taskError" ||
         event.type === "taskNotification" ||
         event.type === "taskWorkflow";
}

export function isGuestEvent(event: ExtendedChatEvent): event is GuestEvent {
  return event.type.includes("guest") ||
         event.type === "guestSessionCreated" ||
         event.type === "guestSessionUpdated" ||
         event.type === "guestSessionExpired" ||
         event.type === "guestLimitation" ||
         event.type === "guestFeatureBlocked" ||
         event.type === "guestUpgradePrompt" ||
         event.type === "guestUpgradeInitiated" ||
         event.type === "guestUpgradeCompleted" ||
         event.type === "guestUpgradeFailed" ||
         event.type === "guestAnalytics" ||
         event.type === "guestCapabilities" ||
         event.type === "guestOnboarding";
}

// Event handler types
export type ChatEventHandler<T extends ExtendedChatEvent = ExtendedChatEvent> = (event: T) => void | Promise<void>;

export type KeyboardEventHandler = ChatEventHandler<KeyboardEvent>;
export type CommandEventHandler = ChatEventHandler<CommandEvent>;
export type TaskEventHandler = ChatEventHandler<TaskEvent>;
export type GuestEventHandler = ChatEventHandler<GuestEvent>;

// Event subscription types
export interface ChatEventSubscription {
  id: string;
  eventTypes: string[];
  handler: ChatEventHandler;
  priority?: number;
}

// Common event metadata
export interface EventMetadata {
  source: "backend" | "frontend" | "user";
  userId?: string;
  sessionId?: string;
  threadId?: string;
  correlationId?: string;
  version?: string;
}

// Event with metadata wrapper
export interface EventWithMetadata<T extends ExtendedChatEvent = ExtendedChatEvent> {
  event: T;
  metadata: EventMetadata;
  receivedAt: number;
}