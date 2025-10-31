/**
 * Keyboard Event Types for AG-UI Protocol
 * 
 * Defines TypeScript interfaces for reply keyboards, inline keyboards,
 * and related SSE events that match the Telegram Bot API structure.
 */

import type { AppBaseEvent } from "./app-events";

// Base keyboard button interfaces
export interface ReplyKeyboardButton {
  text: string;
  command?: string;
  callback_data?: string;
  url?: string;
  request_contact?: boolean;
  request_location?: boolean;
}

export interface InlineKeyboardButton {
  text: string;
  callback_data?: string;
  url?: string;
  switch_inline_query?: string;
  switch_inline_query_current_chat?: string;
  pay?: boolean;
}

// Keyboard structure interfaces
export interface ReplyKeyboard {
  keyboard: ReplyKeyboardButton[][];
  resize_keyboard?: boolean;
  one_time_keyboard?: boolean;
  selective?: boolean;
  placeholder?: string;
}

export interface InlineKeyboard {
  inline_keyboard: InlineKeyboardButton[][];
}

// SSE Event interfaces
export interface ReplyKeyboardEvent extends AppBaseEvent {
  type: "replyKeyboard";
  keyboard: ReplyKeyboard;
  timestamp: number;
}

export interface InlineKeyboardEvent extends AppBaseEvent {
  type: "inlineKeyboard";
  messageId: string;
  keyboard: InlineKeyboard;
  timestamp: number;
}

export interface RemoveKeyboardEvent extends AppBaseEvent {
  type: "removeKeyboard";
  keyboardType: "reply" | "inline";
  messageId?: string; // For removing specific inline keyboard
  timestamp: number;
}

// Button interaction events
export interface KeyboardButtonClickEvent {
  buttonType: "reply" | "inline";
  button: ReplyKeyboardButton | InlineKeyboardButton;
  messageId?: string; // For inline buttons
  timestamp: number;
}

// Keyboard state management
export interface KeyboardState {
  replyKeyboard?: ReplyKeyboard;
  inlineKeyboards: Map<string, InlineKeyboard>; // messageId -> keyboard
  placeholder?: string;
  isVisible: boolean;
}

// Union type for all keyboard events
export type KeyboardEvent = 
  | ReplyKeyboardEvent 
  | InlineKeyboardEvent 
  | RemoveKeyboardEvent;