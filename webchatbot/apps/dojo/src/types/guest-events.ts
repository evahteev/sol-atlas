/**
 * Guest Mode Event Types
 * 
 * Defines TypeScript interfaces for guest user management,
 * restrictions, and authentication upgrade flow.
 */

import type { AppBaseEvent } from "./app-events";

// Guest session management
export interface GuestSession {
  sessionId: string;
  createdAt: string;
  expiresAt: string;
  startTime?: number;
  messageCount: number;
  messageLimit: number;
  usage?: {
    messages: number;
    commands: number;
  };
  rateLimit: {
    requestsPerMinute: number;
    currentRequests: number;
    resetAt: string;
  };
  permissions: string[];
}

// Guest session events
export interface GuestSessionCreatedEvent extends AppBaseEvent {
  type: "guestSessionCreated";
  session: GuestSession;
  timestamp: number;
}

export interface GuestSessionUpdatedEvent extends AppBaseEvent {
  type: "guestSessionUpdated";
  sessionId: string;
  updates: Partial<GuestSession>;
  timestamp: number;
}

export interface GuestSessionExpiredEvent extends AppBaseEvent {
  type: "guestSessionExpired";
  sessionId: string;
  reason: "timeout" | "limit_exceeded" | "manual";
  timestamp: number;
}

// Guest limitation events
export interface GuestLimitationEvent extends AppBaseEvent {
  type: "guestLimitation";
  limitationType: "message_count" | "rate_limit" | "feature_access" | "time_limit";
  current: number;
  limit: number;
  feature?: string;
  upgradePrompt: boolean;
  timestamp: number;
}

export interface GuestFeatureBlockedEvent extends AppBaseEvent {
  type: "guestFeatureBlocked";
  feature: string;
  featureName: string;
  description: string;
  requiresAuth: boolean;
  upgradeUrl?: string;
  timestamp: number;
}

// Guest upgrade flow events
export interface GuestUpgradePromptEvent extends AppBaseEvent {
  type: "guestUpgradePrompt";
  trigger: "message_limit" | "feature_access" | "time_limit" | "manual";
  title: string;
  message: string;
  benefits: string[];
  upgradeUrl: string;
  timestamp: number;
}

export interface GuestUpgradeInitiatedEvent extends AppBaseEvent {
  type: "guestUpgradeInitiated";
  sessionId: string;
  upgradeMethod: "telegram_miniapp" | "oauth" | "email";
  timestamp: number;
}

export interface GuestUpgradeCompletedEvent extends AppBaseEvent {
  type: "guestUpgradeCompleted";
  sessionId: string;
  userId: string;
  upgradeMethod: string;
  preservedData: {
    messageHistory: boolean;
    preferences: boolean;
    context: boolean;
  };
  timestamp: number;
}

export interface GuestUpgradeFailedEvent extends AppBaseEvent {
  type: "guestUpgradeFailed";
  sessionId: string;
  error: string;
  upgradeMethod: string;
  retryable: boolean;
  timestamp: number;
}

// Guest analytics events
export interface GuestAnalyticsEvent extends AppBaseEvent {
  type: "guestAnalytics";
  event: "page_view" | "feature_attempt" | "command_used" | "upgrade_clicked";
  sessionId: string;
  metadata?: Record<string, any>;
  timestamp: number;
}

// Guest permissions and capabilities
export interface GuestCapabilities {
  canSendMessages: boolean;
  canUseCommands: string[]; // List of allowed commands
  canAccessFeatures: string[]; // List of allowed features
  canViewContent: string[]; // List of viewable content types
  messageLimit: number;
  sessionDurationMinutes: number;
  rateLimits: {
    messagesPerMinute: number;
    commandsPerMinute: number;
    searchesPerMinute: number;
  };
}

export interface GuestCapabilitiesEvent extends AppBaseEvent {
  type: "guestCapabilities";
  capabilities: GuestCapabilities;
  timestamp: number;
}

// Guest onboarding events
export interface GuestOnboardingEvent extends AppBaseEvent {
  type: "guestOnboarding";
  step: "welcome" | "features_demo" | "limitations_explained" | "upgrade_benefits";
  content: {
    title: string;
    description: string;
    actions?: Array<{
      label: string;
      action: string;
      primary?: boolean;
    }>;
  };
  timestamp: number;
}

// Union type for all guest events
export type GuestEvent = 
  | GuestSessionCreatedEvent
  | GuestSessionUpdatedEvent
  | GuestSessionExpiredEvent
  | GuestLimitationEvent
  | GuestFeatureBlockedEvent
  | GuestUpgradePromptEvent
  | GuestUpgradeInitiatedEvent
  | GuestUpgradeCompletedEvent
  | GuestUpgradeFailedEvent
  | GuestAnalyticsEvent
  | GuestCapabilitiesEvent
  | GuestOnboardingEvent;