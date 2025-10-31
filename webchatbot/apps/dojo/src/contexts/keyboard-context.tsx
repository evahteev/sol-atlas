"use client";

import React, { createContext, useContext, useState, useCallback, useEffect } from "react";
import { useCopilotChat } from "@copilotkit/react-core";
import { createCompatibleMessage } from "@/utils/copilotkit-compat";
import type {
  ReplyKeyboard,
  InlineKeyboard,
  ReplyKeyboardButton,
  InlineKeyboardButton,
  KeyboardState,
  KeyboardButtonClickEvent
} from "@/types/keyboard-events";

interface KeyboardContextValue extends KeyboardState {
  // State setters
  setReplyKeyboard: (keyboard: ReplyKeyboard | undefined) => void;
  setInlineKeyboard: (messageId: string, keyboard: InlineKeyboard) => void;
  removeInlineKeyboard: (messageId: string) => void;
  clearAllKeyboards: () => void;
  
  // Button interaction handlers
  handleReplyButtonClick: (button: ReplyKeyboardButton) => void;
  handleInlineButtonClick: (button: InlineKeyboardButton, messageId?: string) => void;
  
  // Utility functions
  getInlineKeyboard: (messageId: string) => InlineKeyboard | undefined;
  hasAnyKeyboards: () => boolean;
}

const KeyboardContext = createContext<KeyboardContextValue | undefined>(undefined);

interface KeyboardContextProviderProps {
  children: React.ReactNode;
  onCommandExecute?: (command: string, data?: any) => void;
  onMessageSend?: (message: string) => void;
}

export function KeyboardContextProvider({ 
  children, 
  onCommandExecute,
  onMessageSend 
}: KeyboardContextProviderProps) {
  // State management
  const [replyKeyboard, setReplyKeyboardState] = useState<ReplyKeyboard | undefined>();
  const [inlineKeyboards, setInlineKeyboards] = useState<Map<string, InlineKeyboard>>(new Map());
  const [placeholder, setPlaceholder] = useState<string | undefined>();
  const [isVisible, setIsVisible] = useState<boolean>(true);

  // Get CopilotKit chat functions for sending messages
  const { appendMessage } = useCopilotChat();

  // Reply keyboard management
  const setReplyKeyboard = useCallback((keyboard: ReplyKeyboard | undefined) => {
    setReplyKeyboardState(keyboard);
    setPlaceholder(keyboard?.placeholder);
    setIsVisible(!!keyboard);
    
    console.log('KeyboardContext: Reply keyboard updated', {
      hasKeyboard: !!keyboard,
      buttonsCount: keyboard?.keyboard?.length || 0,
      placeholder: keyboard?.placeholder
    });
  }, []);

  // Inline keyboard management
  const setInlineKeyboard = useCallback((messageId: string, keyboard: InlineKeyboard) => {
    setInlineKeyboards(prev => {
      const newMap = new Map(prev);
      newMap.set(messageId, keyboard);
      console.log('KeyboardContext: Inline keyboard set for message', messageId, keyboard);
      return newMap;
    });
  }, []);

  const removeInlineKeyboard = useCallback((messageId: string) => {
    setInlineKeyboards(prev => {
      const newMap = new Map(prev);
      const removed = newMap.delete(messageId);
      if (removed) {
        console.log('KeyboardContext: Inline keyboard removed for message', messageId);
      }
      return newMap;
    });
  }, []);

  const clearAllKeyboards = useCallback(() => {
    setReplyKeyboardState(undefined);
    setInlineKeyboards(new Map());
    setPlaceholder(undefined);
    setIsVisible(false);
    console.log('KeyboardContext: All keyboards cleared');
  }, []);

  // Button click handlers
  const handleReplyButtonClick = useCallback((button: ReplyKeyboardButton) => {
    console.log('KeyboardContext: Reply button clicked', button);

    const clickEvent: KeyboardButtonClickEvent = {
      buttonType: "reply",
      button,
      timestamp: Date.now()
    };

    if (button.command) {
      // Handle command buttons (e.g., /start, /groups)
      onCommandExecute?.(button.command);
    } else if (button.callback_data) {
      // Handle callback data
      onCommandExecute?.('callback', { data: button.callback_data, type: 'reply' });
    } else if (button.url) {
      // Handle URL buttons
      window.open(button.url, '_blank', 'noopener,noreferrer');
    } else if (button.request_contact) {
      // Handle contact request (show appropriate UI)
      onCommandExecute?.('request_contact');
    } else if (button.request_location) {
      // Handle location request (show appropriate UI)
      onCommandExecute?.('request_location');
    } else {
      // Send button text as message
      onMessageSend?.(button.text);
      // Use CopilotKit to append the message
      appendMessage(createCompatibleMessage({
        id: `user_${Date.now()}`,
        role: 'user',
        content: button.text
      }));
    }

    // Hide keyboard if one_time_keyboard is true
    if (replyKeyboard?.one_time_keyboard) {
      setReplyKeyboard(undefined);
    }

    // Emit analytics event
    window.dispatchEvent(new CustomEvent('keyboard-button-click', {
      detail: clickEvent
    }));
  }, [replyKeyboard, onCommandExecute, onMessageSend, appendMessage, setReplyKeyboard]);

  const handleInlineButtonClick = useCallback((button: InlineKeyboardButton, messageId?: string) => {
    console.log('KeyboardContext: Inline button clicked', button, 'for message', messageId);

    const clickEvent: KeyboardButtonClickEvent = {
      buttonType: "inline",
      button,
      messageId,
      timestamp: Date.now()
    };

    if (button.callback_data) {
      // Handle callback data with message context
      onCommandExecute?.('inline_callback', { 
        data: button.callback_data,
        messageId,
        type: 'inline'
      });
    } else if (button.url) {
      // Handle URL buttons (open in new tab)
      window.open(button.url, '_blank', 'noopener,noreferrer');
    } else if (button.switch_inline_query !== undefined) {
      // Handle inline query switch
      onMessageSend?.(button.switch_inline_query);
      appendMessage(createCompatibleMessage({
        id: `user_${Date.now()}`,
        role: 'user',
        content: button.switch_inline_query
      }));
    } else if (button.switch_inline_query_current_chat !== undefined) {
      // Handle inline query in current chat
      onMessageSend?.(button.switch_inline_query_current_chat);
      appendMessage(createCompatibleMessage({
        id: `user_${Date.now()}`,
        role: 'user',
        content: button.switch_inline_query_current_chat
      }));
    } else if (button.pay) {
      // Handle payment button (special handling)
      onCommandExecute?.('payment', { 
        messageId,
        buttonText: button.text
      });
    }

    // Emit analytics event
    window.dispatchEvent(new CustomEvent('keyboard-button-click', {
      detail: clickEvent
    }));
  }, [onCommandExecute, onMessageSend, appendMessage]);

  // Utility functions
  const getInlineKeyboard = useCallback((messageId: string): InlineKeyboard | undefined => {
    return inlineKeyboards.get(messageId);
  }, [inlineKeyboards]);

  const hasAnyKeyboards = useCallback((): boolean => {
    return !!replyKeyboard || inlineKeyboards.size > 0;
  }, [replyKeyboard, inlineKeyboards]);

  // Cleanup effect for removing old inline keyboards
  useEffect(() => {
    // Clean up inline keyboards for messages that might no longer exist
    // This is a simple cleanup - in production, you might want more sophisticated cleanup
    const cleanup = () => {
      if (inlineKeyboards.size > 50) { // Arbitrary limit
        const entries = Array.from(inlineKeyboards.entries());
        const toKeep = entries.slice(-25); // Keep last 25
        setInlineKeyboards(new Map(toKeep));
        console.log('KeyboardContext: Cleaned up old inline keyboards');
      }
    };

    const timer = setTimeout(cleanup, 30000); // Cleanup every 30 seconds
    return () => clearTimeout(timer);
  }, [inlineKeyboards]);

  // Context value
  const value: KeyboardContextValue = {
    // State
    replyKeyboard,
    inlineKeyboards,
    placeholder,
    isVisible,
    
    // State setters
    setReplyKeyboard,
    setInlineKeyboard,
    removeInlineKeyboard,
    clearAllKeyboards,
    
    // Button handlers
    handleReplyButtonClick,
    handleInlineButtonClick,
    
    // Utilities
    getInlineKeyboard,
    hasAnyKeyboards,
  };

  return (
    <KeyboardContext.Provider value={value}>
      {children}
    </KeyboardContext.Provider>
  );
}

export function useKeyboard(): KeyboardContextValue {
  const context = useContext(KeyboardContext);
  if (!context) {
    throw new Error("useKeyboard must be used within KeyboardContextProvider");
  }
  return context;
}

// Custom hook for keyboard event listening
export function useKeyboardEvents() {
  const { setReplyKeyboard, setInlineKeyboard, removeInlineKeyboard } = useKeyboard();

  useEffect(() => {
    const handleKeyboardEvent = (event: CustomEvent) => {
      const { type, data } = event.detail;
      
      switch (type) {
        case 'replyKeyboard':
          setReplyKeyboard(data.keyboard);
          break;
        case 'inlineKeyboard':
          setInlineKeyboard(data.messageId, data.keyboard);
          break;
        case 'removeKeyboard':
          if (data.keyboardType === 'reply') {
            setReplyKeyboard(undefined);
          } else if (data.keyboardType === 'inline' && data.messageId) {
            removeInlineKeyboard(data.messageId);
          }
          break;
      }
    };

    window.addEventListener('keyboard-event', handleKeyboardEvent as EventListener);
    return () => {
      window.removeEventListener('keyboard-event', handleKeyboardEvent as EventListener);
    };
  }, [setReplyKeyboard, setInlineKeyboard, removeInlineKeyboard]);
}