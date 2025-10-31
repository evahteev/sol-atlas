"use client";

import React, { createContext, useContext, useState, useCallback, useEffect } from "react";
import { useCopilotChat } from "@copilotkit/react-core";
import { createCompatibleMessage } from "@/utils/copilotkit-compat";
import type {
  GuestSession,
  GuestLimitationEvent,
  GuestUpgradePromptEvent,
  GuestSessionCreatedEvent,
  GuestCapabilities
} from "@/types/guest-events";

// Define missing types locally
type GuestLimitation = {
  feature: string;
  type: string;
  allowedValues?: string[];
  limit?: number;
  description: string;
};

type GuestUpgradeEvent = {
  type: string;
  reason: string;
  feature?: string;
  guestSessionId?: string;
  timestamp: number;
};

type GuestSessionEvent = {
  type: string;
  session: GuestSession;
  timestamp: number;
};

type AuthenticationEvent = {
  type: string;
  userId: string;
  userInfo?: any;
  previousGuestSession?: string;
  timestamp: number;
};

interface GuestContextValue {
  // Guest state
  isGuest: boolean;
  guestSession?: GuestSession;
  limitations: GuestLimitation[];
  
  // Session management
  initializeGuestSession: () => Promise<void>;
  upgradeToAuthenticated: (authData: any) => Promise<void>;
  endGuestSession: () => void;
  
  // Limitation checking
  isFeatureAllowed: (feature: string) => boolean;
  getRemainingUsage: (feature: string) => number;
  checkCommandAccess: (command: string) => boolean;
  
  // Upgrade prompts
  showUpgradePrompt: (reason: string, feature?: string) => void;
  dismissUpgradePrompt: () => void;
  
  // UI state
  showingUpgradePrompt: boolean;
  upgradePromptReason?: string;
  upgradePromptFeature?: string;
  
  // Usage tracking
  incrementUsage: (feature: string) => void;
  getUsageStats: () => Record<string, number>;
  resetUsageStats: () => void;
}

const GuestContext = createContext<GuestContextValue | undefined>(undefined);

interface GuestContextProviderProps {
  children: React.ReactNode;
  onAuthenticationRequired?: (feature: string) => void;
  onGuestSessionStart?: (session: GuestSession) => void;
  onGuestSessionEnd?: (session: GuestSession) => void;
  onUpgradeRequest?: (event: GuestUpgradeEvent) => void;
}

// Default guest limitations
const DEFAULT_LIMITATIONS: GuestLimitation[] = [
  {
    feature: "commands",
    type: "whitelist",
    allowedValues: ["start", "groups", "catalog", "help"],
    limit: undefined,
    description: "Only basic commands available in guest mode"
  },
  {
    feature: "messages",
    type: "limit",
    allowedValues: undefined,
    limit: 50,
    description: "Limited to 50 messages per session"
  },
  {
    feature: "groupJoin",
    type: "limit",
    allowedValues: undefined,
    limit: 3,
    description: "Can join up to 3 groups as guest"
  },
  {
    feature: "catalogSearch",
    type: "limit",
    allowedValues: undefined,
    limit: 10,
    description: "Limited catalog searches per session"
  },
  {
    feature: "tasks",
    type: "blocked",
    allowedValues: undefined,
    limit: undefined,
    description: "Task management requires authentication"
  },
  {
    feature: "profile",
    type: "blocked",
    allowedValues: undefined,
    limit: undefined,
    description: "Profile access requires authentication"
  }
];

export function GuestContextProvider({ 
  children,
  onAuthenticationRequired,
  onGuestSessionStart,
  onGuestSessionEnd,
  onUpgradeRequest
}: GuestContextProviderProps) {
  // State management
  const [isGuest, setIsGuest] = useState(true);
  const [guestSession, setGuestSession] = useState<GuestSession | undefined>();
  const [limitations] = useState<GuestLimitation[]>(DEFAULT_LIMITATIONS);
  const [showingUpgradePrompt, setShowingUpgradePrompt] = useState(false);
  const [upgradePromptReason, setUpgradePromptReason] = useState<string | undefined>();
  const [upgradePromptFeature, setUpgradePromptFeature] = useState<string | undefined>();
  const [usageStats, setUsageStats] = useState<Record<string, number>>({});

  // Get CopilotKit chat functions
  const { appendMessage } = useCopilotChat();

  // Session management
  const initializeGuestSession = useCallback(async (): Promise<void> => {
    const sessionId = `guest_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    
    const newSession: GuestSession = {
      sessionId,
      createdAt: new Date().toISOString(),
      expiresAt: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(), // 24 hours
      startTime: Date.now(),
      messageCount: 0,
      messageLimit: 10,
      usage: {
        messages: 0,
        commands: 0
      },
      rateLimit: {
        requestsPerMinute: 10,
        currentRequests: 0,
        resetAt: new Date(Date.now() + 60 * 1000).toISOString()
      },
      permissions: ['basic_chat']
    };

    setGuestSession(newSession);
    setIsGuest(true);
    setUsageStats({});

    console.log('GuestContext: Guest session initialized', newSession);

    // Emit session start event
    const sessionEvent: GuestSessionEvent = {
      type: "guestSessionStart",
      session: newSession,
      timestamp: Date.now()
    };

    window.dispatchEvent(new CustomEvent('guest-session', {
      detail: sessionEvent
    }));

    onGuestSessionStart?.(newSession);

    // Don't show welcome message - let auto-trigger /start handle it

  }, [limitations, onGuestSessionStart, appendMessage]);

  const upgradeToAuthenticated = useCallback(async (authData: any): Promise<void> => {
    console.log('GuestContext: Upgrading to authenticated mode', authData);

    // End current guest session
    if (guestSession) {
      const endedSession = {
        ...guestSession,
        endTime: Date.now(),
        isActive: false,
        upgradeTime: Date.now()
      };

      setGuestSession(endedSession);
      
      const sessionEndEvent: GuestSessionEvent = {
        type: "guestSessionEnd",
        session: endedSession,
        timestamp: Date.now()
      };

      window.dispatchEvent(new CustomEvent('guest-session', {
        detail: sessionEndEvent
      }));

      onGuestSessionEnd?.(endedSession);
    }

    // Switch to authenticated mode
    setIsGuest(false);
    setGuestSession(undefined);
    setShowingUpgradePrompt(false);
    setUpgradePromptReason(undefined);
    setUpgradePromptFeature(undefined);

    // Emit authentication event
    const authEvent: AuthenticationEvent = {
      type: "authenticationComplete",
      userId: authData.userId || authData.id,
      userInfo: authData,
      previousGuestSession: guestSession?.sessionId,
      timestamp: Date.now()
    };

    window.dispatchEvent(new CustomEvent('authentication', {
      detail: authEvent
    }));

    appendMessage(createCompatibleMessage({
      id: `auth_complete_${Date.now()}`,
      role: 'assistant',
      content: "Authentication complete! You now have access to all features."
    }));

  }, [guestSession, onGuestSessionEnd, appendMessage]);

  const endGuestSession = useCallback(() => {
    if (guestSession) {
      const endedSession = {
        ...guestSession,
        endTime: Date.now(),
        isActive: false
      };

      console.log('GuestContext: Guest session ended', endedSession);

      const sessionEndEvent: GuestSessionEvent = {
        type: "guestSessionEnd",
        session: endedSession,
        timestamp: Date.now()
      };

      window.dispatchEvent(new CustomEvent('guest-session', {
        detail: sessionEndEvent
      }));

      onGuestSessionEnd?.(endedSession);
    }

    setGuestSession(undefined);
    setIsGuest(false);
    setUsageStats({});
  }, [guestSession, onGuestSessionEnd]);

  // Limitation checking
  const isFeatureAllowed = useCallback((feature: string): boolean => {
    if (!isGuest) return true;

    const limitation = limitations.find(l => l.feature === feature);
    if (!limitation) return true;

    switch (limitation.type) {
      case "blocked":
        return false;
      case "whitelist":
        return true; // Specific values checked in checkCommandAccess
      case "limit":
        const usage = usageStats[feature] || 0;
        return usage < (limitation.limit || 0);
      default:
        return true;
    }
  }, [isGuest, limitations, usageStats]);

  const getRemainingUsage = useCallback((feature: string): number => {
    if (!isGuest) return Infinity;

    const limitation = limitations.find(l => l.feature === feature);
    if (!limitation || limitation.type !== "limit") return Infinity;

    const usage = usageStats[feature] || 0;
    const limit = limitation.limit || 0;
    return Math.max(0, limit - usage);
  }, [isGuest, limitations, usageStats]);

  const checkCommandAccess = useCallback((command: string): boolean => {
    if (!isGuest) return true;

    const commandLimitation = limitations.find(l => l.feature === "commands");
    if (!commandLimitation) return true;

    if (commandLimitation.type === "whitelist") {
      return commandLimitation.allowedValues?.includes(command) || false;
    }

    return true;
  }, [isGuest, limitations]);

  // Upgrade prompts
  const showUpgradePrompt = useCallback((reason: string, feature?: string) => {
    setShowingUpgradePrompt(true);
    setUpgradePromptReason(reason);
    setUpgradePromptFeature(feature);

    const upgradeEvent: GuestUpgradeEvent = {
      type: "guestUpgradePrompt",
      reason,
      feature,
      guestSessionId: guestSession?.sessionId,
      timestamp: Date.now()
    };

    console.log('GuestContext: Showing upgrade prompt', upgradeEvent);

    window.dispatchEvent(new CustomEvent('guest-upgrade', {
      detail: upgradeEvent
    }));

    onUpgradeRequest?.(upgradeEvent);
    onAuthenticationRequired?.(feature || reason);

    // Show upgrade message in chat
    appendMessage(createCompatibleMessage({
      id: `upgrade_prompt_${Date.now()}`,
      role: 'assistant',
      content: `🔐 ${reason}${feature ? ` (Feature: ${feature})` : ''}\n\nSign in to unlock all features and continue using the chat without limitations.`
    }));

  }, [guestSession, onUpgradeRequest, onAuthenticationRequired, appendMessage]);

  const dismissUpgradePrompt = useCallback(() => {
    setShowingUpgradePrompt(false);
    setUpgradePromptReason(undefined);
    setUpgradePromptFeature(undefined);
  }, []);

  // Usage tracking
  const incrementUsage = useCallback((feature: string) => {
    if (!isGuest) return;

    setUsageStats(prev => ({
      ...prev,
      [feature]: (prev[feature] || 0) + 1
    }));

    // Update guest session usage
    if (guestSession && guestSession.usage) {
      const updatedSession = {
        ...guestSession,
        usage: {
          ...guestSession.usage,
          [feature]: (guestSession.usage[feature as keyof typeof guestSession.usage] || 0) + 1
        }
      };
      setGuestSession(updatedSession);
    }

    console.log('GuestContext: Usage incremented', feature, usageStats[feature] + 1);

    // Check if limit is reached
    const limitation = limitations.find(l => l.feature === feature);
    if (limitation?.type === "limit") {
      const newUsage = (usageStats[feature] || 0) + 1;
      const limit = limitation.limit || 0;
      
      if (newUsage >= limit) {
        showUpgradePrompt(
          `You've reached the limit for ${feature} (${limit} uses). Sign in to continue.`,
          feature
        );
      } else if (newUsage >= limit * 0.8) {
        // Warn at 80% usage
        appendMessage(createCompatibleMessage({
          id: `usage_warning_${Date.now()}`,
          role: 'assistant',
          content: `⚠️ You're approaching the limit for ${feature}: ${newUsage}/${limit} uses. Consider signing in for unlimited access.`
        }));
      }
    }
  }, [isGuest, guestSession, usageStats, limitations, showUpgradePrompt, appendMessage]);

  const getUsageStats = useCallback((): Record<string, number> => {
    return { ...usageStats };
  }, [usageStats]);

  const resetUsageStats = useCallback(() => {
    setUsageStats({});
    if (guestSession) {
      setGuestSession({
        ...guestSession,
        usage: {
          messages: 0,
          commands: 0
        }
      });
    }
  }, [guestSession]);

  // Auto-initialize guest session on mount
  useEffect(() => {
    if (isGuest && !guestSession) {
      // Add a small delay to avoid double initialization in React Strict Mode
      const timer = setTimeout(() => {
        initializeGuestSession();
      }, 100);
      
      return () => clearTimeout(timer);
    }
  }, [isGuest, guestSession, initializeGuestSession]);

  // Listen for authentication events
  useEffect(() => {
    const handleAuthEvent = (event: CustomEvent<AuthenticationEvent>) => {
      if (event.detail.type === "authenticationComplete") {
        upgradeToAuthenticated(event.detail.userInfo);
      }
    };

    const handleCommandRestriction = (event: CustomEvent) => {
      const { command, message } = event.detail;
      showUpgradePrompt(message, "commands");
    };

    window.addEventListener('authentication', handleAuthEvent as EventListener);
    window.addEventListener('command-restriction', handleCommandRestriction as EventListener);

    return () => {
      window.removeEventListener('authentication', handleAuthEvent as EventListener);
      window.removeEventListener('command-restriction', handleCommandRestriction as EventListener);
    };
  }, [upgradeToAuthenticated, showUpgradePrompt]);

  const value: GuestContextValue = {
    // State
    isGuest,
    guestSession,
    limitations,
    
    // Session management
    initializeGuestSession,
    upgradeToAuthenticated,
    endGuestSession,
    
    // Limitation checking
    isFeatureAllowed,
    getRemainingUsage,
    checkCommandAccess,
    
    // Upgrade prompts
    showUpgradePrompt,
    dismissUpgradePrompt,
    
    // UI state
    showingUpgradePrompt,
    upgradePromptReason,
    upgradePromptFeature,
    
    // Usage tracking
    incrementUsage,
    getUsageStats,
    resetUsageStats,
  };

  return (
    <GuestContext.Provider value={value}>
      {children}
    </GuestContext.Provider>
  );
}

export function useGuest(): GuestContextValue {
  const context = useContext(GuestContext);
  if (!context) {
    throw new Error("useGuest must be used within GuestContextProvider");
  }
  return context;
}

// Hook for guest limitation checking
export function useGuestLimitations() {
  const { isGuest, isFeatureAllowed, checkCommandAccess, incrementUsage, showUpgradePrompt } = useGuest();

  const checkAndEnforce = useCallback((feature: string, action?: () => void): boolean => {
    if (!isGuest) {
      action?.();
      return true;
    }

    if (!isFeatureAllowed(feature)) {
      showUpgradePrompt(`This feature requires authentication.`, feature);
      return false;
    }

    incrementUsage(feature);
    action?.();
    return true;
  }, [isGuest, isFeatureAllowed, incrementUsage, showUpgradePrompt]);

  const checkCommand = useCallback((command: string): boolean => {
    if (!isGuest) return true;
    
    if (!checkCommandAccess(command)) {
      showUpgradePrompt(`Command '/${command}' requires authentication.`, "commands");
      return false;
    }

    incrementUsage("commands");
    return true;
  }, [isGuest, checkCommandAccess, incrementUsage, showUpgradePrompt]);

  return {
    checkAndEnforce,
    checkCommand,
    isGuest
  };
}