/**
 * Custom base event interface for application-specific events
 * 
 * This is separate from the core AG-UI BaseEvent to avoid type conflicts
 * with custom event type strings that don't exist in the core EventType enum.
 */

export interface AppBaseEvent {
  type: string;
  timestamp?: number;
  rawEvent?: any;
}
