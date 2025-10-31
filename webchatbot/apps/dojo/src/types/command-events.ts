/**
 * Command Event Types for AG-UI Protocol
 * 
 * Defines TypeScript interfaces for command parsing, execution,
 * and response handling in the dojo chat interface.
 */

import type { AppBaseEvent } from "./app-events";

// Command parsing and structure
export interface ParsedCommand {
  command: string;
  args: string[];
  raw: string;
  isValid: boolean;
}

export interface CommandDefinition {
  name: string;
  description: string;
  requiresAuth: boolean;
  guestAllowed: boolean;
  aliases?: string[];
  usage?: string;
  examples?: string[];
}

// Command execution events
export interface CommandExecutionEvent extends AppBaseEvent {
  type: "commandExecution";
  command: ParsedCommand;
  userId?: string;
  isGuest: boolean;
  timestamp: number;
}

export interface CommandResultEvent extends AppBaseEvent {
  type: "commandResult";
  command: string;
  success: boolean;
  message?: string;
  data?: any;
  error?: string;
  timestamp: number;
}

export interface CommandErrorEvent extends AppBaseEvent {
  type: "commandError";
  command: string;
  error: string;
  code: string;
  timestamp: number;
}

// Guest access events
export interface GuestRestrictionEvent extends AppBaseEvent {
  type: "guestRestriction";
  command: string;
  message: string;
  upgradePrompt: boolean;
  timestamp: number;
}

// Command suggestions and help
export interface CommandSuggestion {
  command: string;
  description: string;
  priority: number;
  category: "navigation" | "tasks" | "social" | "settings";
}

export interface CommandHelpEvent extends AppBaseEvent {
  type: "commandHelp";
  suggestions: CommandSuggestion[];
  helpText?: string;
  timestamp: number;
}

// Available commands list
export interface AvailableCommandsEvent extends AppBaseEvent {
  type: "availableCommands";
  commands: CommandDefinition[];
  isGuest: boolean;
  timestamp: number;
}

// Union type for all command events
export type CommandEvent = 
  | CommandExecutionEvent
  | CommandResultEvent
  | CommandErrorEvent
  | GuestRestrictionEvent
  | CommandHelpEvent
  | AvailableCommandsEvent;