import { useEffect } from 'react';
import { useFormContext } from '@/contexts/form-context';
import { FormRequest } from '@/components/form-renderer';
import { FormRenderMode } from '@/types/inline-forms';

// This component acts as a bridge between server-side AG-UI events and client-side handling
export function AgUiEventProcessor() {
  const { showForm, addInlineForm } = useFormContext();
  
  useEffect(() => {
    console.log('🌉 AgUiEventProcessor: Mounted and listening for events');
    
    // Check for server-side rendered events stored in globalThis
    if (typeof globalThis !== 'undefined' && globalThis.__pendingFormEvents) {
      console.log('🌉 AgUiEventProcessor: Found pending form events', {
        count: globalThis.__pendingFormEvents.length,
        events: globalThis.__pendingFormEvents
      });
      
      // Process all pending events
      const pendingEvents = [...globalThis.__pendingFormEvents];
      globalThis.__pendingFormEvents = []; // Clear after processing
      
      pendingEvents.forEach((formData: any) => {
        console.log('🌉 AgUiEventProcessor: Processing pending form event', formData);
        
        const form: FormRequest = {
          form_id: formData.form_id,
          title: formData.title,
          description: formData.description,
          fields: formData.fields || [],
          metadata: formData.metadata,
        };
        
        const formRenderMode = formData.renderMode as FormRenderMode || FormRenderMode.MODAL;
        
        if (formRenderMode === FormRenderMode.INLINE) {
          console.log('📝 AgUiEventProcessor: Adding inline form');
          addInlineForm(form);
        } else {
          console.log('🔲 AgUiEventProcessor: Showing modal form');
          showForm(form);
        }
      });
    }
    
    // Also listen for any runtime events that might be dispatched
    const handleFormEvent = (event: CustomEvent) => {
      console.log('🌉 AgUiEventProcessor: Received runtime form event', event.detail);
      
      const formData = event.detail;
      const form: FormRequest = {
        form_id: formData.form_id,
        title: formData.title,
        description: formData.description,
        fields: formData.fields || [],
        metadata: formData.metadata,
      };
      
      const formRenderMode = formData.renderMode as FormRenderMode || FormRenderMode.MODAL;
      
      if (formRenderMode === FormRenderMode.INLINE) {
        console.log('📝 AgUiEventProcessor: Adding inline form from runtime event');
        addInlineForm(form);
      } else {
        console.log('🔲 AgUiEventProcessor: Showing modal form from runtime event');
        showForm(form);
      }
    };
    
    // Listen for runtime events
    window.addEventListener('agui:form:request', handleFormEvent as EventListener);
    
    // Check periodically for new pending events (in case they're added after initial mount)
    const checkInterval = setInterval(() => {
      if (globalThis.__pendingFormEvents && globalThis.__pendingFormEvents.length > 0) {
        console.log('🌉 AgUiEventProcessor: Found new pending events in interval check');
        const newEvents = [...globalThis.__pendingFormEvents];
        globalThis.__pendingFormEvents = [];
        
        newEvents.forEach((formData: any) => {
          const event = new CustomEvent('agui:form:request', { detail: formData });
          window.dispatchEvent(event);
        });
      }
    }, 500); // Check every 500ms
    
    return () => {
      window.removeEventListener('agui:form:request', handleFormEvent as EventListener);
      clearInterval(checkInterval);
    };
  }, [showForm, addInlineForm]);
  
  return null; // This is a logic-only component
}