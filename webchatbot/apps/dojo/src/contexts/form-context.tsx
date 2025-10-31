import React, { createContext, useContext, useState, useCallback, useEffect, ReactNode } from 'react';
import { useCopilotChat } from '@copilotkit/react-core';
import { FormRequest } from '@/components/form-renderer';
import { createCompatibleMessage } from '@/utils/copilotkit-compat';
import { FormRenderMode, InlineFormMessage, InlineFormState } from '@/types/inline-forms';
import { useCopilotKitEvents } from '@/hooks/use-copilotkit-events';
import { useAgUiEvents } from '@/hooks/use-ag-ui-events';
import { getFormEventBus } from '@/utils/form-event-bus';

interface FormContextValue {
  // Existing modal form functionality
  currentForm: FormRequest | null;
  showForm: (form: FormRequest) => void;
  hideForm: () => void;
  submitForm: (formId: string, data: Record<string, any>) => void;
  isFormVisible: boolean;
  
  // New inline form functionality
  renderMode: FormRenderMode;
  setRenderMode: (mode: FormRenderMode) => void;
  inlineForms: InlineFormMessage[];
  addInlineForm: (form: FormRequest) => void;
  updateInlineFormStatus: (formId: string, status: InlineFormState['status']) => void;
  removeInlineForm: (formId: string) => void;
}

const FormContext = createContext<FormContextValue | undefined>(undefined);

export const useFormContext = () => {
  const context = useContext(FormContext);
  if (!context) {
    throw new Error('useFormContext must be used within a FormContextProvider');
  }
  return context;
};

interface FormContextProviderProps {
  children: ReactNode;
}

export const FormContextProvider: React.FC<FormContextProviderProps> = ({ children }) => {
  const [currentForm, setCurrentForm] = useState<FormRequest | null>(null);
  const [isFormVisible, setIsFormVisible] = useState(false);
  const [renderMode, setRenderMode] = useState<FormRenderMode>(FormRenderMode.MODAL);
  const [inlineForms, setInlineForms] = useState<InlineFormMessage[]>([]);

  // Get appendMessage from useCopilotChat
  const copilotChat = useCopilotChat();
  const appendMessage = copilotChat?.appendMessage;

  // Inline form management functions - define these first
  const addInlineForm = useCallback((form: FormRequest) => {
    console.log('FormContext: Adding inline form', form);
    const inlineForm: InlineFormMessage = {
      id: `inline_${form.form_id}_${Date.now()}`,
      type: 'form',
      formData: form,
      renderMode: FormRenderMode.INLINE,
      status: 'active',
      timestamp: Date.now()
    };
    setInlineForms(prev => [...prev, inlineForm]);
  }, []);

  const updateInlineFormStatus = useCallback((formId: string, status: InlineFormState['status']) => {
    console.log('FormContext: Updating inline form status', { formId, status });
    setInlineForms(prev => prev.map(form => 
      form.formData.form_id === formId 
        ? { ...form, status: status as any }
        : form
    ));
  }, []);

  const removeInlineForm = useCallback((formId: string) => {
    console.log('FormContext: Removing inline form', formId);
    setInlineForms(prev => prev.filter(form => form.formData.form_id !== formId));
  }, []);

  const showForm = useCallback((form: FormRequest) => {
    console.log('FormContext: Showing form', form);
    setCurrentForm(form);
    setIsFormVisible(true);
  }, []);

  const hideForm = useCallback(() => {
    console.log('FormContext: Hiding form');
    setCurrentForm(null);
    setIsFormVisible(false);
  }, []);

  // Fallback method for form submission when CopilotKit is not available
  const submitFormFallback = useCallback(async (formId: string, data: Record<string, any>, message: string) => {
    console.log('FormContext: Using fallback submission method', { formId, data, message });

    try {
      // For start_exploring action, make a direct API call to the agent
      if (data.action === 'start_exploring' || data.action === 'sign_in') {
        const currentLang = currentForm?.metadata?.language || inlineForms.find(f => f.formData.form_id === formId)?.formData.metadata?.language || 'en';

        const response = await fetch('http://localhost:8000/api/agent/luka', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            messages: [
              {
                role: 'user',
                content: message,
                id: `fallback_${Date.now()}`,
              }
            ],
            user_id: 'guest',
            thread_id: 'fallback-thread',
            agent: 'luka',
          }),
        });

        if (response.ok) {
          console.log('FormContext: Fallback submission successful');
          // Force a page refresh to show the new conversation
          window.location.reload();
        } else {
          console.error('FormContext: Fallback API call failed:', response.status);
        }
      } else {
        console.warn('FormContext: Fallback supports start_exploring and sign_in actions');
      }
    } catch (error) {
      console.error('FormContext: Fallback submission error:', error);
    }
  }, [inlineForms, currentForm]);

  const submitForm = useCallback(async (formId: string, data: Record<string, any>) => {
    console.log('FormContext: Submitting form', { formId, data });
    
    // Handle special language selection actions that should re-render forms
    const isLanguageAction = data.action === 'select_language' || 
                            data.action === 'set_language' || 
                            data.action === 'back_to_onboarding' ||
                            (data.language && typeof data.language === 'string') || // Handle buttons with data.language
                            (data.action && data.action.startsWith('set_language')); // Handle buttons like set_language_ru
    
    console.log('FormContext: Is language action?', isLanguageAction, 'data:', data);
    
    // For non-language actions, remove the inline form immediately
    if (!isLanguageAction) {
      const currentInlineForm = inlineForms.find(f => f.formData.form_id === formId);
      if (currentInlineForm) {
        removeInlineForm(formId);
      }
    }
    
    if (isLanguageAction) {
      try {
        // For language actions, fetch the new form directly
        let endpoint = 'http://localhost:8000/api/agent/luka/onboarding-form?is_guest=true';
        let requestData: any = {};
        
        if (data.action === 'select_language') {
          // Get current language from form metadata
          const currentLang = currentForm?.metadata?.language || 'en';
          endpoint = `http://localhost:8000/api/agent/luka/onboarding-form?command=select_language&language=${currentLang}`;
        } else if ((data.action === 'set_language' || !data.action) && data.language) {
          // Set specific language (either explicit action or button with data.language)
          endpoint = `http://localhost:8000/api/agent/luka/onboarding-form?command=set_language&language=${data.language}`;
        } else if (data.action && data.action.startsWith('set_language_')) {
          // Handle buttons like set_language_ru, set_language_en
          const language = data.action.split('_')[2]; // Extract 'ru' from 'set_language_ru'
          endpoint = `http://localhost:8000/api/agent/luka/onboarding-form?command=set_language&language=${language}`;
        } else if (data.action === 'back_to_onboarding') {
          // Back to onboarding with current language
          const currentLang = currentForm?.metadata?.current_language || 'en';
          endpoint = `http://localhost:8000/api/agent/luka/onboarding-form?command=back_to_onboarding&language=${currentLang}`;
        }
        
        const response = await fetch(endpoint);
        if (response.ok) {
          const formData = await response.json();
          console.log('FormContext: Received new form after language action', formData);
          
          // Show the new form inline (replace current inline form)
          if (formData.type === 'formRequest') {
            const newForm: FormRequest = {
              form_id: formData.form_id,
              title: formData.title,
              description: formData.description,
              fields: formData.fields || [],
              metadata: formData.metadata,
            };
            
            // Remove the current inline form first
            removeInlineForm(formId);
            
            // Always show language selection forms as modal
            showForm(newForm);
            return; // Don't proceed with normal form submission
          }
        }
      } catch (error) {
        console.error('FormContext: Error handling language action', error);
      }
    }
    
    // For all other actions, hide the form and proceed normally
    hideForm();
    
    // Prepare submission message
    let message = '';
    if (data.action === 'start_exploring') {
      // Special handling for start_exploring - send a language-appropriate prompt
      const currentLang = currentForm?.metadata?.language || inlineForms.find(f => f.formData.form_id === formId)?.formData.metadata?.language || 'en';
      if (currentLang === 'ru') {
        message = "Привет! Я готов исследовать возможности Luka Bot. Расскажи мне, как ты можешь помочь с управлением Telegram сообществами?";
      } else {
        message = "Hello! I'm ready to start exploring Luka Bot. Can you tell me how you can help with managing Telegram communities?";
      }
    } else if (data.action) {
      // Button action
      message = `/${data.action}`;
      if (data.kb_id) {
        message += ` ${data.kb_id}`;
      }
      if (data.language) {
        message += ` ${data.language}`;
      }
    } else if (data.search_query) {
      // Search query
      message = `/search ${data.search_query}`;
    } else {
      // Generic form data
      message = `/submit ${formId} ${JSON.stringify(data)}`;
    }
    
    // Send the message through CopilotKit
    try {
      if (appendMessage && typeof appendMessage === 'function') {
        const userMessage = createCompatibleMessage({
          id: `form_${Date.now()}`,
          role: 'user' as const,
          content: message,
          createdAt: new Date().toISOString(),
        });
        
        appendMessage(userMessage);
        console.log('FormContext: Successfully sent message to CopilotKit:', message);
      } else {
        console.warn('FormContext: appendMessage not available, using fallback');
        // Fallback: trigger the form submission via direct API call
        await submitFormFallback(formId, data, message);
      }
    } catch (error) {
      console.error('FormContext: Error sending message to CopilotKit', error);
      // Try fallback method
      try {
        await submitFormFallback(formId, data, message);
      } catch (fallbackError) {
        console.error('FormContext: Fallback submission also failed', fallbackError);
      }
    }
  }, [appendMessage, hideForm, showForm, currentForm, inlineForms, removeInlineForm, addInlineForm, submitFormFallback]);

  // Use CopilotKit events to listen for form events from the message stream
  useCopilotKitEvents({
    onFormRequest: (formData) => {
      console.log('📥 FormContext: Received form request from CopilotKit events', {
        form_id: formData.form_id,
        title: formData.title,
        renderMode: formData.renderMode,
        timestamp: new Date().toISOString()
      });

      // Create FormRequest from event data
      const form: FormRequest = {
        form_id: formData.form_id,
        title: formData.title,
        description: formData.description,
        fields: formData.fields || [],
        metadata: formData.metadata,
      };

      // Check if form has renderMode specified
      const formRenderMode = formData.renderMode as FormRenderMode || FormRenderMode.MODAL;

      if (formRenderMode === FormRenderMode.INLINE) {
        console.log('📝 FormContext: Adding inline form from CopilotKit event');
        addInlineForm(form);
      } else {
        console.log('🔲 FormContext: Showing modal form from CopilotKit event');
        showForm(form);
      }
    }
  });

  // Also use AG-UI events directly
  useAgUiEvents({
    onFormRequest: (formData) => {
      console.log('📥 FormContext: Received form request from AG-UI events', {
        form_id: formData.form_id,
        title: formData.title,
        renderMode: formData.renderMode,
        timestamp: new Date().toISOString()
      });

      // Create FormRequest from event data
      const form: FormRequest = {
        form_id: formData.form_id,
        title: formData.title,
        description: formData.description,
        fields: formData.fields || [],
        metadata: formData.metadata,
      };

      // Check if form has renderMode specified
      const formRenderMode = formData.renderMode as FormRenderMode || FormRenderMode.MODAL;

      if (formRenderMode === FormRenderMode.INLINE) {
        console.log('📝 FormContext: Adding inline form from AG-UI event');
        addInlineForm(form);
      } else {
        console.log('🔲 FormContext: Showing modal form from AG-UI event');
        showForm(form);
      }
    }
  });

  // Subscribe to form event bus and check for pending form events
  useEffect(() => {
    const formEventBus = getFormEventBus();

    const handleFormEvent = (formData: any) => {
      console.log('📥 FormContext: Received form request from FormEventBus', {
        form_id: formData.form_id,
        title: formData.title,
        renderMode: formData.renderMode,
        timestamp: new Date().toISOString()
      });

      // Check if form has renderMode specified
      const formRenderMode = formData.renderMode as FormRenderMode || FormRenderMode.MODAL;

      if (formRenderMode === FormRenderMode.INLINE) {
        console.log('📝 FormContext: Adding inline form from FormEventBus');
        addInlineForm(formData);
      } else {
        console.log('🔲 FormContext: Showing modal form from FormEventBus');
        showForm(formData);
      }
    };

    const unsubscribe = formEventBus.subscribe(handleFormEvent);

    // Check for pending form events from server-side
    const checkPendingFormEvents = () => {
      if (typeof globalThis !== 'undefined' && globalThis.__pendingFormEvents) {
        const pendingEvents = globalThis.__pendingFormEvents;
        if (pendingEvents.length > 0) {
          console.log('📥 FormContext: Processing pending form events from globalThis', pendingEvents.length);
          pendingEvents.forEach(handleFormEvent);
          globalThis.__pendingFormEvents = []; // Clear processed events
        }
      }
    };

    // Check immediately and set up periodic checking
    checkPendingFormEvents();
    const interval = setInterval(checkPendingFormEvents, 500);

    return () => {
      unsubscribe();
      clearInterval(interval);
    };
  }, [addInlineForm, showForm]);

  // Listen for form:request events from CopilotKit via custom event listener
  // Since CopilotKit's event stream isn't easily accessible, we'll use a custom approach
  useEffect(() => {
    // Ensure this only runs on client-side
    if (typeof window === 'undefined') {
      console.log('🔴 FormContext: Window is undefined, skipping event listener setup');
      return;
    }
    console.log('🟢 FormContext: Setting up event listeners for form:request events');
    
    const handleCustomFormRequest = (event: CustomEvent) => {
      const formData = event.detail;
      console.log('🎯 FormContext: Received custom form:request event', {
        formData,
        renderMode: formData.renderMode,
        form_id: formData.form_id,
        title: formData.title,
        eventType: event.type,
        timestamp: new Date().toISOString()
      });
      
      // Create FormRequest from event data
      const form: FormRequest = {
        form_id: formData.form_id,
        title: formData.title,
        description: formData.description,
        fields: formData.fields || [],
        metadata: formData.metadata,
      };
      
      // Check if form has renderMode specified
      const formRenderMode = formData.renderMode as FormRenderMode || FormRenderMode.MODAL;
      
      if (formRenderMode === FormRenderMode.INLINE) {
        addInlineForm(form);
      } else {
        showForm(form);
      }
    };

    // Check for any pending events stored during SSR
    if (typeof globalThis !== 'undefined' && globalThis.__pendingFormEvents) {
      console.log('FormContext: Processing pending form events from SSR', globalThis.__pendingFormEvents);
      const pendingEvents = globalThis.__pendingFormEvents;
      globalThis.__pendingFormEvents = []; // Clear the pending events
      
      pendingEvents.forEach((eventDetail: any) => {
        const syntheticEvent = new CustomEvent('copilotkit-form-request', {
          detail: eventDetail
        });
        handleCustomFormRequest(syntheticEvent);
      });
    }

    // Listen for custom form:request events
    console.log('🎧 FormContext: Adding copilotkit-form-request event listener');
    window.addEventListener('copilotkit-form-request', handleCustomFormRequest as EventListener);

    // Add debug listener to verify events are fired
    const debugListener = (e: Event) => {
      console.log('🔍 FormContext: DEBUG - Event fired on window', {
        type: e.type,
        detail: (e as CustomEvent).detail,
        timestamp: new Date().toISOString()
      });
    };
    window.addEventListener('copilotkit-form-request', debugListener);

    return () => {
      console.log('🗑️ FormContext: Removing copilotkit-form-request event listener');
      window.removeEventListener('copilotkit-form-request', handleCustomFormRequest as EventListener);
      window.removeEventListener('copilotkit-form-request', debugListener);
    };
  }, [addInlineForm, showForm]);

  // Keep DOM event listener for backward compatibility (e.g., auto-trigger)
  useEffect(() => {
    const handleFormRequest = (event: Event) => {
      const customEvent = event as CustomEvent;
      const formData = customEvent.detail;
      
      console.log('FormContext: Received DOM form request', formData);
      
      // Create FormRequest from event data
      const form: FormRequest = {
        form_id: formData.form_id,
        title: formData.title,
        description: formData.description,
        fields: formData.fields || [],
        metadata: formData.metadata,
      };
      
      // Check if form has renderMode specified
      const formRenderMode = formData.renderMode as FormRenderMode || FormRenderMode.MODAL;
      
      if (formRenderMode === FormRenderMode.INLINE) {
        addInlineForm(form);
      } else {
        showForm(form);
      }
    };

    window.addEventListener('form-request', handleFormRequest);

    return () => {
      window.removeEventListener('form-request', handleFormRequest);
    };
  }, [addInlineForm, showForm]);

  const value: FormContextValue = {
    // Existing
    currentForm,
    showForm,
    hideForm,
    submitForm,
    isFormVisible,
    // New
    renderMode,
    setRenderMode,
    inlineForms,
    addInlineForm,
    updateInlineFormStatus,
    removeInlineForm,
  };

  return (
    <FormContext.Provider value={value}>
      {children}
    </FormContext.Provider>
  );
};