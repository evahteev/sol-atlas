/**
 * Utility functions for CopilotKit compatibility
 */

export interface CopilotKitCompatibleMessage {
  id?: string;
  role?: string;
  content?: string;
  createdAt?: string;
  isAgentStateMessage?: () => boolean;
  isResultMessage?: () => boolean;
  isTextMessage?: () => boolean;
  isActionExecutionMessage?: () => boolean;
  isToolCallMessage?: () => boolean;
  isToolResultMessage?: () => boolean;
  isChatMessage?: () => boolean;
}

/**
 * Adds CopilotKit compatibility methods to any message object
 * This ensures that all messages have the required methods that CopilotKit expects
 */
export function addCopilotKitMethods<T extends { id?: string; role?: string; content?: string; createdAt?: string }>(
  message: T
): T & CopilotKitCompatibleMessage {
  if (!message) {
    throw new Error('addCopilotKitMethods: message cannot be null or undefined');
  }
  
  const compatibleMessage = message as T & CopilotKitCompatibleMessage;
  
  // Add required createdAt field if missing
  if (!compatibleMessage.createdAt) {
    compatibleMessage.createdAt = new Date().toISOString();
  }
  
  // Only add methods if they don't already exist
  if (!compatibleMessage.isAgentStateMessage) {
    compatibleMessage.isAgentStateMessage = () => false;
  }
  if (!compatibleMessage.isResultMessage) {
    compatibleMessage.isResultMessage = () => false;
  }
  if (!compatibleMessage.isTextMessage) {
    compatibleMessage.isTextMessage = () => true;
  }
  if (!compatibleMessage.isActionExecutionMessage) {
    compatibleMessage.isActionExecutionMessage = () => false;
  }
  if (!compatibleMessage.isToolCallMessage) {
    compatibleMessage.isToolCallMessage = () => false;
  }
  if (!compatibleMessage.isToolResultMessage) {
    compatibleMessage.isToolResultMessage = () => false;
  }
  if (!compatibleMessage.isChatMessage) {
    compatibleMessage.isChatMessage = () => compatibleMessage.role === 'user' || compatibleMessage.role === 'assistant';
  }
  
  return compatibleMessage;
}

/**
 * Creates a CopilotKit-compatible message with all required methods and properties
 */
export function createCompatibleMessage(
  message: { id?: string; role?: string; content?: string; createdAt?: string }
): any {
  const compatibleMessage = addCopilotKitMethods(message);
  
  // Add CopilotKit required properties
  return {
    ...compatibleMessage,
    type: 'text' as const,
    status: 'success' as const,
    isImageMessage: () => false,
  };
}