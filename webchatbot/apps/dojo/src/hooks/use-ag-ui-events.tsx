import { useEffect, useRef } from 'react';

interface AgUiEventListener {
  onFormRequest?: (data: any) => void;
  onKeyboardReply?: (data: any) => void;
  onKeyboardInline?: (data: any) => void;
  onCommandResult?: (data: any) => void;
  onTaskList?: (data: any) => void;
  onUiContext?: (data: any) => void;
}

// Hook to listen to AG-UI events from CopilotKit runtime
export function useAgUiEvents(handlers: AgUiEventListener) {
  const handlersRef = useRef(handlers);
  handlersRef.current = handlers;
  
  useEffect(() => {
    console.log('🎯 useAgUiEvents: Setting up AG-UI event listeners', {
      handlers: Object.keys(handlers),
      timestamp: new Date().toISOString()
    });
    
    // Listen for CopilotKit runtime events
    const handleRuntimeMessage = (event: MessageEvent) => {
      // Filter for messages from CopilotKit runtime
      if (!event.data || typeof event.data !== 'object') return;
      
      // Log all messages for debugging
      console.log('🔍 useAgUiEvents: Received message event', {
        data: event.data,
        origin: event.origin,
        hasHandlers: !!handlersRef.current
      });
      
      // Check if this is a CopilotKit event
      if (event.data.type === 'copilotkit-custom-event') {
        const { name, value } = event.data;
        console.log('📨 useAgUiEvents: Processing CopilotKit custom event', { name, value });
        
        switch (name) {
          case 'form:request':
            handlersRef.current.onFormRequest?.(value);
            break;
          case 'keyboard:reply':
            handlersRef.current.onKeyboardReply?.(value);
            break;
          case 'keyboard:inline':
            handlersRef.current.onKeyboardInline?.(value);
            break;
          case 'command:result':
            handlersRef.current.onCommandResult?.(value);
            break;
          case 'task:list':
            handlersRef.current.onTaskList?.(value);
            break;
          case 'ui:context':
            handlersRef.current.onUiContext?.(value);
            break;
        }
      }
    };
    
    // Listen for postMessage events (in case CopilotKit uses them)
    window.addEventListener('message', handleRuntimeMessage);
    
    // Also listen for direct AG-UI protocol events via globalThis
    const checkGlobalEvents = () => {
      if (typeof globalThis !== 'undefined' && (globalThis as any).__aguiEvents) {
        const events = (globalThis as any).__aguiEvents;
        (globalThis as any).__aguiEvents = [];
        
        events.forEach((event: any) => {
          console.log('📦 useAgUiEvents: Processing global AG-UI event', event);
          
          if (event.type === 'CUSTOM') {
            switch (event.name) {
              case 'form:request':
                handlersRef.current.onFormRequest?.(event.value);
                break;
              case 'keyboard:reply':
                handlersRef.current.onKeyboardReply?.(event.value);
                break;
              case 'keyboard:inline':
                handlersRef.current.onKeyboardInline?.(event.value);
                break;
              case 'command:result':
                handlersRef.current.onCommandResult?.(event.value);
                break;
              case 'task:list':
                handlersRef.current.onTaskList?.(event.value);
                break;
              case 'ui:context':
                handlersRef.current.onUiContext?.(event.value);
                break;
            }
          }
        });
      }
    };
    
    // Check for events periodically
    const interval = setInterval(checkGlobalEvents, 100);
    
    // Initial check
    checkGlobalEvents();
    
    return () => {
      window.removeEventListener('message', handleRuntimeMessage);
      clearInterval(interval);
      console.log('🗑️ useAgUiEvents: Cleaned up event listeners');
    };
  }, []); // Empty deps since we use ref for handlers
}