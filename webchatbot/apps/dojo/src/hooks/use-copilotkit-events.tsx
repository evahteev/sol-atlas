import { useEffect, useCallback, useRef } from 'react';
import { useCopilotChat } from '@copilotkit/react-core';

interface CopilotKitEventHandler {
  onFormRequest?: (data: any) => void;
  onKeyboardReply?: (data: any) => void;
  onKeyboardInline?: (data: any) => void;
  onCommandResult?: (data: any) => void;
  onTaskList?: (data: any) => void;
  onUiContext?: (data: any) => void;
}

export function useCopilotKitEvents(handlers: CopilotKitEventHandler) {
  const chat = useCopilotChat();
  const messages = (chat as any)?.messages || [];
  
  // Log initial state
  console.log('🎬 useCopilotKitEvents: Hook initialized', {
    hasChat: !!chat,
    messageCount: messages.length,
    handlers: Object.keys(handlers),
    timestamp: new Date().toISOString()
  });
  
  // Track processed events to avoid duplicate processing
  const processedEventsRef = useRef(new Set<string>());
  const processedEvents = processedEventsRef.current;
  
  useEffect(() => {
    console.log('🔍 useCopilotKitEvents: Checking messages and state', {
      messageCount: messages.length,
      chatState: chat,
      lastMessage: messages.length > 0 ? messages[messages.length - 1] : null,
      timestamp: new Date().toISOString()
    });
    
    // Log all messages for debugging
    if (messages.length > 0) {
      console.log('📋 useCopilotKitEvents: All messages:', messages.map((m: any) => ({
        id: m.id,
        role: m.role,
        hasMetadata: !!m.metadata,
        metadata: m.metadata,
        contentPreview: m.content?.substring(0, 50),
        fullContent: m.content
      })));
    }
    
    // Process new messages
    messages.forEach((message: any) => {
      // Skip if already processed
      const messageId = message?.id || `msg_${Date.now()}`;
      if (processedEvents.has(messageId)) {
        return;
      }
      
      // Check if this is a form event message (from server-side BotApiAgent)
      if (message.metadata?.isFormEvent && message.metadata?.formEvent) {
        console.log('📨 useCopilotKitEvents: Found form event message', {
          messageId: message.id,
          formEvent: message.metadata.formEvent
        });
        
        // Dispatch the form event as a DOM event for the FormContext to catch
        if (typeof window !== 'undefined') {
          const formEvent = new CustomEvent('copilotkit-form-request', {
            detail: message.metadata.formEvent,
            bubbles: true,
            cancelable: true
          });
          window.dispatchEvent(formEvent);
          console.log('🎯 useCopilotKitEvents: Dispatched form event to window', message.metadata.formEvent);
        }
        
        // Also call the handler if provided
        if (handlers.onFormRequest) {
          handlers.onFormRequest(message.metadata.formEvent);
        }
        
        processedEvents.add(messageId);
      }
      
      // Check if message has custom events
      if (message.metadata?.customEvents) {
        console.log('📨 useCopilotKitEvents: Found custom events in message', {
          messageId: message.id,
          events: message.metadata.customEvents
        });
        
        message.metadata.customEvents.forEach((event: any) => {
          console.log('🎯 useCopilotKitEvents: Processing custom event', {
            eventName: event.name,
            eventData: event.value
          });
          
          switch (event.name) {
            case 'form:request':
              // Dispatch as DOM event
              if (typeof window !== 'undefined') {
                const formEvent = new CustomEvent('copilotkit-form-request', {
                  detail: event.value,
                  bubbles: true,
                  cancelable: true
                });
                window.dispatchEvent(formEvent);
                console.log('🎯 useCopilotKitEvents: Dispatched form:request to window', event.value);
              }
              if (handlers.onFormRequest) {
                handlers.onFormRequest(event.value);
              }
              break;
            case 'keyboard:reply':
              if (handlers.onKeyboardReply) {
                handlers.onKeyboardReply(event.value);
              }
              break;
            case 'keyboard:inline':
              if (handlers.onKeyboardInline) {
                handlers.onKeyboardInline(event.value);
              }
              break;
            case 'command:result':
              if (handlers.onCommandResult) {
                handlers.onCommandResult(event.value);
              }
              break;
            case 'task:list':
              if (handlers.onTaskList) {
                handlers.onTaskList(event.value);
              }
              break;
            case 'ui:context':
              if (handlers.onUiContext) {
                handlers.onUiContext(event.value);
              }
              break;
          }
        });
        
        processedEvents.add(messageId);
      }
      
      // Also check for AG-UI events in the message itself
      if (message.aguiEvents) {
        console.log('📨 useCopilotKitEvents: Found AG-UI events in message', {
          messageId,
          events: message.aguiEvents
        });
        
        message.aguiEvents.forEach((event: any) => {
          if (event.type === 'CUSTOM' && event.name === 'form:request') {
            console.log('🎯 useCopilotKitEvents: Processing AG-UI form:request event', event.value);
            // Dispatch as DOM event
            if (typeof window !== 'undefined') {
              const formEvent = new CustomEvent('copilotkit-form-request', {
                detail: event.value,
                bubbles: true,
                cancelable: true
              });
              window.dispatchEvent(formEvent);
            }
            if (handlers.onFormRequest) {
              handlers.onFormRequest(event.value);
            }
          }
        });
        
        processedEvents.add(messageId);
      }
    });
  }, [messages, handlers]);
  
  return { messages };
}