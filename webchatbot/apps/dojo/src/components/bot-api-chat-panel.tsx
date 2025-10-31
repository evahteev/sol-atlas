"use client";

import React, { useEffect, useMemo, useState, useCallback, useRef } from "react";
import "@copilotkit/react-ui/styles.css";
import {
  CopilotKit,
  useFrontendTool,
  useCopilotChat,
} from "@copilotkit/react-core";
import { CopilotChat } from "@copilotkit/react-ui";
import { useLocale } from "@/contexts/locale-context";

// Import all our new context providers
import { KeyboardContextProvider, useKeyboard, useKeyboardEvents } from "@/contexts/keyboard-context";
import { CommandContextProvider, useCommand, useCommandInput } from "@/contexts/command-context";
import { TaskContextProvider, useTask, useTaskEvents } from "@/contexts/task-context";
import { GuestContextProvider, useGuest, useGuestLimitations } from "@/contexts/guest-context";
import { FormContextProvider, useFormContext } from "@/contexts/form-context";
import { UiContextProvider, useUiContext } from "@/contexts/ui-context";

// Import keyboard components
import { ReplyKeyboard } from "@/components/keyboards/reply-keyboard";
import { InlineKeyboard } from "@/components/keyboards/inline-keyboard";
import { FormRenderer } from "@/components/form-renderer";
import { FormMessage } from "@/components/forms/form-message";
import { addCopilotKitMethods } from "@/utils/copilotkit-compat";
import { AgUiEventProcessor } from "@/components/ag-ui-event-processor";

const BOT_API_INTEGRATION_ID = "bot-api";
const BOT_API_AGENT_ID = "bot_api_chat";

// Define ChatWithKeyboards component first
const ChatWithKeyboards: React.FC = () => {
  const [background, setBackground] = useState<string>();
  const [hasTriggeredStart, setHasTriggeredStart] = useState(false);
  const chat = useCopilotChat();
  const { isLoading } = chat;
  
  // Get all context hooks
  const { replyKeyboard, handleReplyButtonClick, hasAnyKeyboards } = useKeyboard();
  const { isGuest, checkCommandAccess } = useGuest();
  const { executeCommand, handleInput: handleCommandInput } = useCommandInput();
  const { tasks, isLoading: tasksLoading } = useTask();
  const { currentForm, isFormVisible, submitForm, hideForm, inlineForms } = useFormContext();
  const { uiContext, sendQuickPrompt } = useUiContext();
  
  // Initialize keyboard and other event listeners
  useKeyboardEvents();
  useTaskEvents();

  // Automatically trigger /start on component mount for guests (only once)
  useEffect(() => {
    if (isGuest && !hasTriggeredStart) {
      setHasTriggeredStart(true);
      
      // Immediate trigger - no delay needed
      console.log('BotApiChat: Auto-triggering /start command for guest user');
      executeCommand('/start');
    }
  }, [isGuest, hasTriggeredStart, executeCommand]);
  
  const messages = useMemo(
    () => {
      const rawMessages = (chat as {
        messages?: Array<{ id?: string; role?: string; content?: string }>;
      }).messages ?? [];
      
      // Apply CopilotKit compatibility methods to each message
      return rawMessages.map(msg => addCopilotKitMethods(msg));
    },
    [chat]
  );

  const messageSummaries = useMemo(
    () =>
      messages.map((msg) => ({
        id: msg.id,
        role: msg.role,
        contentPreview: msg.content?.slice(0, 80) ?? "",
        contentLength: msg.content?.length ?? 0,
      })),
    [messages],
  );

  useEffect(() => {
    console.debug("BotApiChat: messages updated", messageSummaries);
    
    // Check for form events in messages and dispatch them
    messages.forEach((message: any) => {
      if (message.metadata?.isFormEvent && message.metadata?.formEvent) {
        console.log('🔥 BotApiChat: Found form event in message, dispatching!', {
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
          
          console.log('🔥 BotApiChat: Form event dispatched successfully');
        }
      }
    });
    
    // Alternative approach: Look for form notification patterns in message content
    // This handles cases where CopilotKit messages aren't properly loaded but UI messages exist
    messages.forEach((message: any) => {
      const content = message.content || '';
      if (content.includes('[📋') && content.includes('Welcome to Luka')) {
        console.log('🔥 BotApiChat: Found welcome form pattern, triggering form!', {
          messageId: message.id,
          content: content
        });
        
        // Fetch and trigger the welcome form directly
        if (typeof window !== 'undefined') {
          fetchWelcomeForm();
        }
      }
    });
  }, [messageSummaries, messages]);
  
  // Function to trigger welcome form (using hardcoded data to avoid CORS)
  const fetchWelcomeForm = async () => {
    try {
      console.log('🔥 BotApiChat: Creating welcome form event...');
      
      // Create welcome form data (based on the backend response structure)
      const welcomeFormData = {
        form_id: `guest_welcome_${Date.now()}`,
        title: '👋 Welcome to Luka!',
        description: `I'm your AI-powered group management assistant for Telegram communities.

🎯 What I can do for your groups:
• 🤖 AI Assistant - Answer questions and help members with smart, context-aware responses
• 📚 Knowledge Base - Index and search through all group messages and conversations
• 🛡️ Smart Moderation - Automatic content filtering, stopwords, and AI-powered quality scoring
• 📊 Analytics - Track activity, member engagement, and generate detailed group statistics

🚀 Get Started:
1️⃣ Use /groups to manage your Telegram groups
2️⃣ Add me to your group as an admin
3️⃣ Configure AI assistance, moderation, and KB indexing

💡 Guest Mode: Limited access to public content`,
        fields: [
          {
            type: 'button',
            name: 'start_exploring',
            label: '🚀 Start Exploring',
            variant: 'primary'
          },
          {
            type: 'button',
            name: 'sign_in',
            label: '🔑 Sign In for Full Access',
            variant: 'secondary'
          },
          {
            type: 'button',
            name: 'select_language',
            label: '🌍',
            variant: 'outline',
            action: 'select_language'
          }
        ],
        metadata: {
          command: 'start',
          user_type: 'guest',
          language: 'en'
        },
        renderMode: 'modal'
      };

      const formEvent = new CustomEvent('copilotkit-form-request', {
        detail: welcomeFormData,
        bubbles: true,
        cancelable: true
      });
      window.dispatchEvent(formEvent);
      
      console.log('🔥 BotApiChat: Welcome form event dispatched successfully');
    } catch (error) {
      console.error('❌ BotApiChat: Error creating welcome form', error);
    }
  };

  useEffect(() => {
    console.debug("BotApiChat: loading state changed", { isLoading });
  }, [isLoading]);

  useEffect(() => {
    console.debug("BotApiChat: guest status", { isGuest, hasKeyboards: hasAnyKeyboards() });
  }, [isGuest, hasAnyKeyboards]);

  // Debug form visibility
  useEffect(() => {
    console.log('🔷 BotApiChatPanel: Form visibility check', {
      isFormVisible,
      currentForm: currentForm ? { form_id: currentForm.form_id, title: currentForm.title } : null,
      shouldRenderModal: isFormVisible && currentForm
    });
    
    if (isFormVisible && currentForm) {
      console.log('🔷 BotApiChatPanel: Rendering form modal', {
        form_id: currentForm.form_id,
        title: currentForm.title
      });
    }
  }, [isFormVisible, currentForm]);

  // Track processed notifications outside useEffect to persist across renders
  const processedNotificationsRef = useRef(new Set<string>());
  const [isFormSubmissionInProgress, setIsFormSubmissionInProgress] = useState(false);

  // Listen for form submission events to temporarily disable detection
  useEffect(() => {
    const handleFormSubmit = () => {
      console.log('🛑 BotApiChat: Form submission detected, pausing DOM detection');
      setIsFormSubmissionInProgress(true);
      // Re-enable after 3 seconds
      setTimeout(() => {
        console.log('✅ BotApiChat: Re-enabling DOM detection after form submission');
        setIsFormSubmissionInProgress(false);
      }, 3000);
    };

    window.addEventListener('copilotkit-form-submit', handleFormSubmit);
    return () => window.removeEventListener('copilotkit-form-submit', handleFormSubmit);
  }, []);

  // DOM-based form detection - check for form notification in the actual DOM
  useEffect(() => {
    const checkForFormNotification = () => {
      // Skip detection if form submission is in progress
      if (isFormSubmissionInProgress) {
        return false;
      }
      // Look for the form notification in the DOM
      const formNotificationElements = document.querySelectorAll('p, div, span');
      
      for (const element of formNotificationElements) {
        const text = element.textContent || '';
        if (text.includes('[📋') && text.includes('Welcome to Luka')) {
          // Create a unique identifier for this notification to avoid duplicates
          const notificationId = `${text.substring(0, 50)}_${element.tagName}`;
          
          if (!processedNotificationsRef.current.has(notificationId)) {
            console.log('🔥 BotApiChat: Found NEW welcome form notification in DOM!', {
              text: text,
              element: element.tagName,
              notificationId: notificationId
            });
            
            processedNotificationsRef.current.add(notificationId);
            
            // Fetch and trigger the welcome form directly
            fetchWelcomeForm();
            return true; // Found new notification
          }
        }
      }
      return false;
    };

    // Set up continuous monitoring that checks every 2 seconds
    const interval = setInterval(() => {
      checkForFormNotification();
    }, 2000);

    // Also check immediately
    checkForFormNotification();

    return () => clearInterval(interval);
  }, [messageSummaries, isFormSubmissionInProgress]); // Re-run when messages change

  useFrontendTool({
    name: "change_background",
    description:
      "Change the background color of the chat. Can be anything that the CSS background attribute accepts. Regular colors, linear or radial gradients etc.",
    parameters: [
      {
        name: "background",
        type: "string",
        description: "The background. Prefer gradients. Only use when asked.",
      },
    ],
    handler: ({ background }) => {
      setBackground(background);
      return {
        status: "success",
        message: `Background changed to ${background}`,
      };
    },
  });

  return (
    <div
      className="flex h-full w-full flex-col gap-3 p-3 md:p-4"
      data-testid="bot-api-chat-panel"
      style={{ background }}
    >
      {/* Header with inline forms and status indicators */}
      <div className="flex flex-col gap-2">        
        {/* Persistent inline forms widget area - always present to catch events */}
        <div className={`
          transition-all duration-300 ease-in-out
          ${inlineForms.length > 0 
            ? 'bg-background/95 p-3 space-y-2 rounded-lg border animate-in slide-in-from-top-2' 
            : 'h-0 overflow-hidden'
          }
        `}>
          {inlineForms.map((formMessage) => (
            <FormMessage
              key={formMessage.id}
              formMessage={formMessage}
            />
          ))}
        </div>
        
        {/* Optional status indicators */}
        <div className="flex gap-2">
          {/* Show guest status indicator */}
          {isGuest && (
            <div className="text-xs text-muted-foreground px-3 py-1.5 bg-orange-50 border border-orange-200 rounded-md flex items-center gap-2">
              <span>🔓</span>
              <span>Guest Mode</span>
            </div>
          )}
          
          {/* Show task count if available */}
          {tasks.length > 0 && (
            <div className="text-xs text-muted-foreground px-3 py-1.5 bg-blue-50 border border-blue-200 rounded-md flex items-center gap-2">
              <span>📋</span>
              <span>{tasks.length} task{tasks.length !== 1 ? 's' : ''}</span>
            </div>
          )}
          
          {/* Debug: Show form widget status */}
          {process.env.NODE_ENV === 'development' && (
            <div className="flex gap-2">
              <div className="text-xs text-muted-foreground px-3 py-1.5 bg-green-50 border border-green-200 rounded-md flex items-center gap-2">
                <span>📝</span>
                <span>Form Widget: {inlineForms.length > 0 ? `${inlineForms.length} active` : 'listening'}</span>
              </div>
              <button
                onClick={() => {
                  console.log('Testing form widget by dispatching test event');
                  window.dispatchEvent(new CustomEvent('copilotkit-form-request', {
                    detail: {
                      form_id: 'test_form_' + Date.now(),
                      title: '🧪 Test Form',
                      description: 'This is a test form to verify the widget is working',
                      fields: [
                        {
                          type: 'button',
                          name: 'test_action',
                          label: '✅ Test Action',
                          variant: 'primary'
                        }
                      ],
                      renderMode: 'inline',
                      metadata: { test: true }
                    }
                  }));
                }}
                className="text-xs px-2 py-1 bg-purple-100 hover:bg-purple-200 border border-purple-300 rounded text-purple-700"
              >
                🧪 Test Widget
              </button>
            </div>
          )}
        </div>
      </div>
      
      <div className="flex-1 overflow-hidden rounded-lg border bg-card shadow-sm flex flex-col relative">
        {/* Main chat area */}
        <div className="flex-1 min-h-0">
          <CopilotChat
              className="h-full w-full rounded-t-2xl"
              labels={{ 
                initial: "" // No initial message, let /start handle everything
              }}
              suggestions={
                // Use quickPrompts from uiContext if available, otherwise fallback to defaults
                uiContext?.quickPrompts && uiContext.quickPrompts.length > 0
                  ? uiContext.quickPrompts.map(prompt => ({
                      title: prompt.text.length > 40 
                        ? prompt.text.substring(0, 37) + "..." 
                        : prompt.text,
                      message: prompt.text,
                    }))
                  : isGuest 
                    ? [
                        {
                          title: "👥 Browse Groups", 
                          message: "/groups",
                        },
                        {
                          title: "📚 Search Catalog",
                          message: "/catalog",
                        },
                        {
                          title: "❓ Get Help",
                          message: "/help",
                        },
                        {
                          title: "🔑 Sign In",
                          message: "How can I sign in to access all features?",
                        },
                      ]
                    : [
                        {
                          title: "📋 My Tasks",
                          message: "/tasks",
                        },
                        {
                          title: "👤 Profile",
                          message: "/profile",
                        },
                        {
                          title: "👥 Groups",
                          message: "/groups",
                        },
                        {
                          title: "📚 Catalog",
                          message: "/catalog",
                        },
                        {
                          title: "💡 Help",
                          message: "/help",
                        },
                        {
                          title: "🎨 Customize",
                          message: "Change the background to something new",
                        },
                      ]
              }
            />
        </div>
        
        {/* Form overlay when visible */}
        {isFormVisible && currentForm && (
          <div className="absolute inset-0 bg-background/95 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <FormRenderer
              form={currentForm}
              onSubmit={submitForm}
              onCancel={hideForm}
            />
          </div>
        )}
        
        {/* Reply keyboard at the bottom */}
        {replyKeyboard && (
          <div className="border-t">
            <ReplyKeyboard
              keyboard={replyKeyboard}
              onButtonClick={handleReplyButtonClick}
              disabled={isLoading}
            />
          </div>
        )}
        
        {/* Test button to manually trigger form event */}
        <div className="absolute bottom-4 left-4">
          <button 
            onClick={() => {
              console.log('🧪 TEST: Manually dispatching form event');
              const testEvent = new CustomEvent('copilotkit-form-request', {
                detail: {
                  form_id: 'test_form',
                  title: 'Test Form',
                  description: 'This is a test form',
                  fields: [
                    {
                      name: 'test_field',
                      type: 'text',
                      label: 'Test Field',
                      required: true
                    }
                  ],
                  renderMode: 'modal',
                  timestamp: Date.now()
                },
                bubbles: true,
                cancelable: true
              });
              const dispatched = window.dispatchEvent(testEvent);
              console.log('🧪 TEST: Event dispatched', { dispatched });
            }}
            className="px-3 py-1 bg-blue-500 text-white rounded text-xs hover:bg-blue-600"
          >
            Test Form Event
          </button>
        </div>
      </div>
    </div>
  );
};

export function BotApiChatPanel() {
  const { locale } = useLocale();
  const runtimeUrl = useMemo(
    () => `/api/copilotkit/${BOT_API_INTEGRATION_ID}?locale=${encodeURIComponent(locale)}`,
    [locale],
  );

  // Handler for command execution from keyboards
  const handleCommandExecute = useCallback((command: string, data?: any) => {
    console.log('BotApiChatPanel: Command execute requested', { command, data });
    // This will be handled by the CommandContext
  }, []);

  // Handler for message sending from keyboards
  const handleMessageSend = useCallback((message: string) => {
    console.log('BotApiChatPanel: Message send requested', { message });
    // This will be handled by the CopilotKit integration
  }, []);


  return (
    <CopilotKit
      key={locale}
      runtimeUrl={runtimeUrl}
      showDevConsole={false}
      agent={BOT_API_AGENT_ID}
    >
      {/* Wrap with all context providers in the correct order */}
      <UiContextProvider>
        <GuestContextProvider
          onAuthenticationRequired={(feature) => {
            console.log('BotApiChatPanel: Authentication required for feature:', feature);
          }}
        >
          <CommandContextProvider
            onCommandResult={(result) => {
              console.log('BotApiChatPanel: Command result received:', result);
            }}
          >
            <TaskContextProvider
              onTaskAction={(action) => {
                console.log('BotApiChatPanel: Task action:', action);
              }}
            >
              <FormContextProvider>
                <KeyboardContextProvider
                  onCommandExecute={handleCommandExecute}
                  onMessageSend={handleMessageSend}
                >
                  <AgUiEventProcessor />
                  <ChatWithKeyboards />
                </KeyboardContextProvider>
              </FormContextProvider>
            </TaskContextProvider>
          </CommandContextProvider>
        </GuestContextProvider>
      </UiContextProvider>
    </CopilotKit>
  );
}