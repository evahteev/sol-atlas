import { AbstractAgent, RunAgentInput } from "@ag-ui/client";
import type { Observer } from "rxjs";
import { Observable } from "rxjs";
import {
  AssistantMessage,
  EventType,
  type BaseEvent,
  type CustomEvent,
  type RunErrorEvent,
  type RunFinishedEvent,
  type RunStartedEvent,
  type TextMessageContentEvent,
  type TextMessageEndEvent,
  type TextMessageStartEvent,
  type MessagesSnapshotEvent,
} from "@ag-ui/core";
import { addCopilotKitMethods } from "@/utils/copilotkit-compat";

// Type declaration for globalThis property
declare global {
  var __pendingFormEvents: any[] | undefined;
}

export interface BotApiAgentConfig {
  baseUrl: string;
  jwtToken?: string;
  userId?: string;
  threadId?: string;
  // Password is handled conversationally, not in config
}

export interface BotApiMessage {
  role: string;
  content: string;
  id?: string;
}

export interface BotApiRunAgentInput {
  messages?: BotApiMessage[];
  user_id?: string;
  thread_id?: string;
  agent?: string;
  // Password is handled conversationally, not in the request
}

export class BotApiAgent extends AbstractAgent {
  private baseUrl: string;
  private jwtToken?: string;
  private userId?: string;
  public threadId: string;

  constructor(config: BotApiAgentConfig) {
    super();
    console.log('🚀 BotApiAgent: Constructor called', {
      baseUrl: config.baseUrl,
      hasJwtToken: !!config.jwtToken,
      userId: config.userId,
      threadId: config.threadId,
      timestamp: new Date().toISOString()
    });
    this.baseUrl = config.baseUrl.replace(/\/$/, ''); // Remove trailing slash
    this.jwtToken = config.jwtToken;
    this.userId = config.userId || 'guest';
    this.threadId = config.threadId || 'default';
  }

  // Utility method to add CopilotKit compatibility methods to any message object
  // Note: This now uses the centralized utility function
  private addCopilotKitMethods(message: any): any {
    return addCopilotKitMethods(message);
  }

  run(input: RunAgentInput): Observable<BaseEvent> {
    console.log('🎯 BotApiAgent: run() called', {
      messages: input.messages?.length || 0,
      threadId: input.threadId,
      timestamp: new Date().toISOString()
    });
    
    return new Observable((observer) => {
      const abortController = new AbortController();

      const execute = async () => {
        try {
          await this.runAgentStream(input, observer, abortController);
          observer.complete();
        } catch (error) {
          console.error('BotApiAgent: Error in runAgentStream:', error);
          observer.error(error);
        }
      };

      void execute();

      return () => {
        console.log('🛑 BotApiAgent: Aborting stream');
        abortController.abort();
      };
    });
  }

  private async runAgentStream(
    input: RunAgentInput,
    observer: Observer<BaseEvent>,
    abortController: AbortController,
  ): Promise<void> {
    try {
      console.log('BotApiAgent: Starting _runAgent with input:', input);
      // Ensure we have a valid token
      await this.ensureAuthenticated();
      console.log('BotApiAgent: Authentication successful');

      // Convert AG-UI RunAgentInput to Bot API format
      const botApiInput: BotApiRunAgentInput = {
        messages: this.convertMessages(input.messages),
        user_id: this.userId,
        thread_id: this.threadId,
        agent: 'luka',
        // Don't include password in the request - let the bot ask for it conversationally
      };

      this.threadId = input.threadId;

      // Prepare headers
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream',
      };

      if (this.jwtToken) {
        headers['Authorization'] = `Bearer ${this.jwtToken}`;
      }

      // Make request to bot API with SSE streaming
      console.log('BotApiAgent: Making request to:', `${this.baseUrl}/api/agent/luka`);
      console.log('BotApiAgent: Request body:', botApiInput);
      const response = await fetch(`${this.baseUrl}/api/agent/luka`, {
        method: 'POST',
        headers,
        body: JSON.stringify(botApiInput),
        signal: abortController.signal,
      });
      console.log('BotApiAgent: Response status:', response.status);

      if (!response.ok) {
        // If we get a 401/403, try to re-authenticate
        if (response.status === 401 || response.status === 403) {
          console.log('Authentication failed, attempting to re-authenticate...');
          await this.authenticateGuest();
          
          // Retry the request with new token
          headers['Authorization'] = `Bearer ${this.jwtToken}`;
          const retryResponse = await fetch(`${this.baseUrl}/api/agent/luka`, {
            method: 'POST',
            headers,
            body: JSON.stringify(botApiInput),
            signal: abortController.signal,
          });
          
          if (!retryResponse.ok) {
            throw new Error(`Bot API request failed after re-authentication: ${retryResponse.status} ${retryResponse.statusText}`);
          }
          
          await this.processSSEResponse(retryResponse, observer);
          return;
        }
        
        throw new Error(`Bot API request failed: ${response.status} ${response.statusText}`);
      }

      // Process SSE response
      await this.processSSEResponse(response, observer);
    } catch (error) {
      console.error('Bot API Agent error:', error);
      throw error;
    }
  }

  private async processSSEResponse(response: Response, observer: Observer<BaseEvent>): Promise<void> {
    console.log('🌊 BotApiAgent: Processing SSE response', {
      status: response.status,
      headers: Object.fromEntries(response.headers.entries()),
      timestamp: new Date().toISOString()
    });
    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error('No response body reader available');
    }

    const decoder = new TextDecoder();
    let buffer = '';
    const aggregatedMessages: AssistantMessage[] = [];
    const messageIndex = new Map<string, AssistantMessage>();
    let latestRunMetadata: { runId?: string; threadId?: string; timestamp?: number } = {};

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.trim() === '') continue; // Skip empty lines
          console.log('🌊 BotApiAgent: SSE line:', line);
          
          if (line.startsWith('data: ')) {
            try {
              const dataStr = line.slice(6);
              console.log('🌊 BotApiAgent: Parsing SSE data:', dataStr);
              const eventData = JSON.parse(dataStr);
              console.log('🌊 BotApiAgent: Parsed SSE event:', {
                type: eventData.type,
                ...eventData,
                timestamp: new Date().toISOString()
              });
              this.emitEventsFromSSE(
                eventData,
                observer,
                aggregatedMessages,
                messageIndex,
                latestRunMetadata,
              );
            } catch (e) {
              console.warn('🌊 BotApiAgent: Failed to parse SSE event:', {
                line,
                error: e,
                timestamp: new Date().toISOString()
              });
            }
          }
        }
      }
    } catch (error) {
      if ((error as DOMException)?.name === 'AbortError') {
        console.log('BotApiAgent: SSE stream aborted by client');
        return;
      }
      throw error;
    } finally {
      reader.releaseLock();
    }

    console.log('BotApiAgent: Completed SSE response stream');
  }

  private emitEventsFromSSE(
    eventData: any,
    observer: Observer<BaseEvent>,
    aggregatedMessages: AssistantMessage[],
    messageIndex: Map<string, AssistantMessage>,
    runMetadata: { runId?: string; threadId?: string; timestamp?: number },
  ) {
    switch (eventData.type) {
      case 'RUN_STARTED': {
        runMetadata.runId = eventData.runId;
        runMetadata.threadId = eventData.threadId ?? this.threadId;
        runMetadata.timestamp = eventData.timestamp;
        const runStartedEvent: RunStartedEvent = {
          type: EventType.RUN_STARTED,
          runId: runMetadata.runId!,
          threadId: runMetadata.threadId ?? this.threadId,
          timestamp: eventData.timestamp,
        };
        observer.next(runStartedEvent);
        break;
      }
      case 'TEXT_MESSAGE_START': {
        const messageId =
          eventData.messageId ??
          `msg_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
        const role = eventData.role ?? 'assistant';

        if (!messageIndex.has(messageId)) {
          const newMessage: AssistantMessage = this.addCopilotKitMethods({
            id: messageId,
            role,
            content: "",
          }) as AssistantMessage;
          aggregatedMessages.push(newMessage);
          messageIndex.set(messageId, newMessage);
        }

        const textStartEvent: TextMessageStartEvent = {
          type: EventType.TEXT_MESSAGE_START,
          messageId,
          role,
          timestamp: eventData.timestamp,
        };
        observer.next(textStartEvent);
        break;
      }
      case 'TEXT_MESSAGE_CONTENT':
      case 'TEXT_MESSAGE': {
        const messageId =
          eventData.messageId ??
          `msg_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
        const role = eventData.role ?? 'assistant';

        let targetMessage = messageIndex.get(messageId);
        if (!targetMessage) {
          targetMessage = this.addCopilotKitMethods({
            id: messageId,
            role,
            content: "",
          }) as AssistantMessage;
          aggregatedMessages.push(targetMessage);
          messageIndex.set(messageId, targetMessage);
          const syntheticStart: TextMessageStartEvent = {
            type: EventType.TEXT_MESSAGE_START,
            messageId,
            role,
            timestamp: eventData.timestamp,
          };
          observer.next(syntheticStart);
        }

        const previousContent = targetMessage.content ?? "";
        const eventContent =
          typeof eventData.content === "string" ? eventData.content : undefined;
        const eventDelta = typeof eventData.delta === "string" ? eventData.delta : undefined;

        let delta = eventDelta;

        if (!delta && eventContent !== undefined) {
          delta =
            previousContent.length === 0
              ? eventContent
              : eventContent.slice(previousContent.length);
        }

        if (!delta && eventContent !== undefined) {
          delta = eventContent;
        }

        if (delta && delta.length > 0) {
          const resolvedContent = previousContent + delta;
          targetMessage.content = resolvedContent;
          console.log('BotApiAgent: Emitting TEXT_MESSAGE_CONTENT', {
            messageId,
            delta,
            previousContentLength: previousContent.length,
            resolvedContentLength: resolvedContent.length,
          });
          const textContentEvent: TextMessageContentEvent = {
            type: EventType.TEXT_MESSAGE_CONTENT,
            messageId,
            delta,
            timestamp: eventData.timestamp,
          };
          observer.next(textContentEvent);
        } else {
          console.log('BotApiAgent: No delta computed for TEXT_MESSAGE_CONTENT', {
            messageId,
            eventContent,
            eventDelta,
            previousContentLength: previousContent.length,
          });
        }
        break;
      }
      case 'TEXT_MESSAGE_END': {
        const messageId =
          eventData.messageId ??
          `msg_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
        const textEndEvent: TextMessageEndEvent = {
          type: EventType.TEXT_MESSAGE_END,
          messageId,
          timestamp: eventData.timestamp,
        };
        console.log('BotApiAgent: Emitting TEXT_MESSAGE_END', {
          messageId,
          finalContentLength: messageIndex.get(messageId)?.content?.length ?? 0,
        });
        observer.next(textEndEvent);
        break;
      }
      case 'RUN_FINISHED': {
        // Ensure all messages have CopilotKit compatibility methods
        const messagesWithMethods = aggregatedMessages.map(msg => this.addCopilotKitMethods(msg));
        
        const result = {
          messages: messagesWithMethods,
          state: {},
          tools: [],
          metadata: {
            runId: eventData.runId ?? runMetadata.runId,
            threadId: eventData.threadId ?? runMetadata.threadId ?? this.threadId,
            timestamp: eventData.timestamp ?? runMetadata.timestamp,
          },
        };
        console.log('BotApiAgent: Converted RUN_FINISHED result:', result);

        const runFinishedEvent: RunFinishedEvent = {
          type: EventType.RUN_FINISHED,
          runId: eventData.runId ?? runMetadata.runId ?? '',
          threadId: eventData.threadId ?? runMetadata.threadId ?? this.threadId,
          timestamp: eventData.timestamp ?? runMetadata.timestamp,
          result,
        };
        observer.next(runFinishedEvent);
        break;
      }
      case 'RUN_ERROR': {
        const runErrorEvent: RunErrorEvent = {
          type: EventType.RUN_ERROR,
          message: eventData.message ?? 'Bot API run error',
          code: eventData.code,
          timestamp: eventData.timestamp,
        };
        observer.next(runErrorEvent);
        break;
      }
      // Handle keyboard events
      case 'REPLY_KEYBOARD': {
        console.log('BotApiAgent: Processing REPLY_KEYBOARD event', eventData);
        const keyboardEvent: CustomEvent = {
          type: EventType.CUSTOM,
          name: 'keyboard:reply',
          value: {
            keyboard: eventData.keyboard,
            messageId: eventData.messageId,
            timestamp: eventData.timestamp
          },
          timestamp: eventData.timestamp,
        };
        observer.next(keyboardEvent);
        
        // Emit DOM event for React context
        if (typeof window !== 'undefined') {
          window.dispatchEvent(new CustomEvent('keyboard-event', {
            detail: {
              type: 'replyKeyboard',
              data: {
                keyboard: eventData.keyboard
              }
            }
          }));
        }
        break;
      }
      case 'INLINE_KEYBOARD': {
        console.log('BotApiAgent: Processing INLINE_KEYBOARD event', eventData);
        const keyboardEvent: CustomEvent = {
          type: EventType.CUSTOM,
          name: 'keyboard:inline',
          value: {
            keyboard: eventData.keyboard,
            messageId: eventData.messageId,
            timestamp: eventData.timestamp
          },
          timestamp: eventData.timestamp,
        };
        observer.next(keyboardEvent);
        
        // Emit DOM event for React context
        if (typeof window !== 'undefined') {
          window.dispatchEvent(new CustomEvent('keyboard-event', {
            detail: {
              type: 'inlineKeyboard',
              data: {
                keyboard: eventData.keyboard,
                messageId: eventData.messageId
              }
            }
          }));
        }
        break;
      }
      case 'REMOVE_KEYBOARD': {
        console.log('BotApiAgent: Processing REMOVE_KEYBOARD event', eventData);
        const keyboardEvent: CustomEvent = {
          type: EventType.CUSTOM,
          name: 'keyboard:remove',
          value: {
            keyboardType: eventData.keyboardType,
            messageId: eventData.messageId,
            timestamp: eventData.timestamp
          },
          timestamp: eventData.timestamp,
        };
        observer.next(keyboardEvent);
        
        // Emit DOM event for React context
        if (typeof window !== 'undefined') {
          window.dispatchEvent(new CustomEvent('keyboard-event', {
            detail: {
              type: 'removeKeyboard',
              data: {
                keyboardType: eventData.keyboardType,
                messageId: eventData.messageId
              }
            }
          }));
        }
        break;
      }
      // Handle command events
      case 'COMMAND_RESULT': {
        console.log('BotApiAgent: Processing COMMAND_RESULT event', eventData);
        const commandEvent: CustomEvent = {
          type: EventType.CUSTOM,
          name: 'command:result',
          value: {
            command: eventData.command,
            success: eventData.success,
            result: eventData.result,
            error: eventData.error,
            timestamp: eventData.timestamp
          },
          timestamp: eventData.timestamp,
        };
        observer.next(commandEvent);
        
        // Emit DOM event for React context
        if (typeof window !== 'undefined') {
          window.dispatchEvent(new CustomEvent('command-result', {
            detail: {
              type: 'commandResult',
              command: eventData.command,
              success: eventData.success,
              result: eventData.result,
              error: eventData.error,
              timestamp: eventData.timestamp
            }
          }));
        }
        break;
      }
      // Handle task events
      case 'TASK_LIST': {
        console.log('BotApiAgent: Processing TASK_LIST event', eventData);
        const taskEvent: CustomEvent = {
          type: EventType.CUSTOM,
          name: 'task:list',
          value: {
            tasks: eventData.tasks,
            timestamp: eventData.timestamp
          },
          timestamp: eventData.timestamp,
        };
        observer.next(taskEvent);
        
        // Emit DOM event for React context
        if (typeof window !== 'undefined') {
          window.dispatchEvent(new CustomEvent('task-list', {
            detail: {
              type: 'taskList',
              tasks: eventData.tasks
            }
          }));
        }
        break;
      }
      case 'TASK_STATUS': {
        console.log('BotApiAgent: Processing TASK_STATUS event', eventData);
        const taskEvent: CustomEvent = {
          type: EventType.CUSTOM,
          name: 'task:status',
          value: {
            taskId: eventData.taskId,
            status: eventData.status,
            assignee: eventData.assignee,
            timestamp: eventData.timestamp
          },
          timestamp: eventData.timestamp,
        };
        observer.next(taskEvent);
        
        // Emit DOM event for React context
        if (typeof window !== 'undefined') {
          window.dispatchEvent(new CustomEvent('task-status', {
            detail: {
              taskId: eventData.taskId,
              status: eventData.status,
              assignee: eventData.assignee,
              timestamp: eventData.timestamp
            }
          }));
        }
        break;
      }
      // Handle guest events
      case 'GUEST_LIMITATION': {
        console.log('BotApiAgent: Processing GUEST_LIMITATION event', eventData);
        const guestEvent: CustomEvent = {
          type: EventType.CUSTOM,
          name: 'guest:limitation',
          value: {
            feature: eventData.feature,
            reason: eventData.reason,
            limit: eventData.limit,
            usage: eventData.usage,
            timestamp: eventData.timestamp
          },
          timestamp: eventData.timestamp,
        };
        observer.next(guestEvent);
        
        // Emit DOM event for React context
        if (typeof window !== 'undefined') {
          window.dispatchEvent(new CustomEvent('guest-limitation', {
            detail: {
              feature: eventData.feature,
              reason: eventData.reason,
              limit: eventData.limit,
              usage: eventData.usage,
              timestamp: eventData.timestamp
            }
          }));
        }
        break;
      }
      case 'formRequest': {
        console.log('🔵 BotApiAgent: Processing formRequest event', {
          ...eventData,
          window_available: typeof window !== 'undefined',
          globalThis_available: typeof globalThis !== 'undefined'
        });
        
        // Create the form event detail
        const eventDetail = {
          form_id: eventData.form_id,
          title: eventData.title,
          description: eventData.description,
          fields: eventData.fields,
          metadata: eventData.metadata,
          renderMode: eventData.renderMode,
          complexity: eventData.complexity,
          timestamp: eventData.timestamp
        };
        
        // Store form event in globalThis for client-side pickup
        if (typeof globalThis !== 'undefined') {
          if (!globalThis.__pendingFormEvents) {
            globalThis.__pendingFormEvents = [];
          }
          globalThis.__pendingFormEvents.push(eventDetail);
          console.log('🚀 BotApiAgent: Stored form event in globalThis', {
            form_id: eventDetail.form_id,
            title: eventDetail.title,
            renderMode: eventDetail.renderMode,
            totalPending: globalThis.__pendingFormEvents.length
          });
        }
        
        // Since BotApiAgent runs server-side, we need to pass the form event through the message stream
        // Create a special message that contains the form event in metadata
        const formMessage: AssistantMessage = this.addCopilotKitMethods({
          id: `form_msg_${eventData.form_id}_${Date.now()}`,
          role: 'assistant' as const,
          content: `[📋 ${eventData.title}]`, // Form notification with emoji
          metadata: {
            isFormEvent: true,
            formEvent: eventDetail,
            customEvents: [{
              name: 'form:request',
              value: eventDetail
            }]
          }
        }) as AssistantMessage;
        
        // Add to aggregated messages so it gets picked up by the client
        aggregatedMessages.push(formMessage);
        messageIndex.set(formMessage.id, formMessage);
        
        // Emit MESSAGES_SNAPSHOT to ensure the client gets the updated messages
        const messagesSnapshot: MessagesSnapshotEvent = {
          type: EventType.MESSAGES_SNAPSHOT,
          messages: aggregatedMessages,
          timestamp: Date.now(),
        };
        observer.next(messagesSnapshot);
        
        // Also emit as AG-UI custom event
        const formEvent: CustomEvent = {
          type: EventType.CUSTOM,
          name: 'form:request',
          value: eventDetail,
          timestamp: eventData.timestamp,
        };
        observer.next(formEvent);
        
        console.log('🟢 BotApiAgent: Emitted form:request through message stream', {
          messageId: formMessage.id,
          form_id: eventDetail.form_id,
          title: eventDetail.title,
          renderMode: eventDetail.renderMode
        });
        
        console.log('BotApiAgent: Emitted form:request AG-UI event', {
          renderMode: eventData.renderMode,
          form_id: eventData.form_id,
          title: eventData.title
        });
        break;
      }
      case 'uiContext': {
        console.log('BotApiAgent: Processing uiContext event', eventData);
        const uiContextEvent: CustomEvent = {
          type: EventType.CUSTOM,
          name: 'ui:context',
          value: eventData,
          timestamp: eventData.timestamp,
        };
        observer.next(uiContextEvent);
        
        // Emit DOM event for React context
        if (typeof window !== 'undefined') {
          window.dispatchEvent(new CustomEvent('ui-context', {
            detail: eventData
          }));
        }
        break;
      }
      default: {
        console.log('BotApiAgent: Processing unknown event type', eventData.type, eventData);
        const customEvent: CustomEvent = {
          type: EventType.CUSTOM,
          name: `botapi:${eventData.type ?? 'unknown'}`,
          value: eventData,
          timestamp: eventData.timestamp,
        };
        observer.next(customEvent);
      }
    }
  }

  private convertMessages(messages?: any[]): BotApiMessage[] {
    if (!messages) return [];
    
    return messages.map((msg: any) => {
      const converted = {
        role: msg.role || 'user',
        content: msg.content || '',
        id: msg.id,
      };
      
      // Ensure CopilotKit compatibility methods are available
      return this.addCopilotKitMethods(converted);
    });
  }

  // Helper method to authenticate with Telegram Mini App
  async authenticateTelegram(initData: string): Promise<{ jwtToken: string; user: any }> {
    const response = await fetch(`${this.baseUrl}/api/auth/telegram-miniapp`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ initData }),
    });

    if (!response.ok) {
      throw new Error(`Telegram authentication failed: ${response.status} ${response.statusText}`);
    }

    const authData = await response.json();
    this.jwtToken = authData.jwt_token;
    return authData;
  }

  // Helper method to ensure we have a valid authentication token
  private async ensureAuthenticated(): Promise<void> {
    if (!this.jwtToken) {
      await this.authenticateGuest();
    }
  }

  // Helper method to create guest session
  async createGuestSession(): Promise<{ jwtToken: string }> {
    return this.authenticateGuest();
  }

  // Helper method to authenticate as guest
  private async authenticateGuest(): Promise<{ jwtToken: string }> {
    const response = await fetch(`${this.baseUrl}/api/auth/guest`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Guest session creation failed: ${response.status} ${response.statusText}`);
    }

    const guestData = await response.json();
    // The API returns 'token' not 'jwt_token' based on our test
    this.jwtToken = guestData.token || guestData.jwt_token;
    return { jwtToken: this.jwtToken! };
  }

  // Helper method to refresh token
  async refreshToken(token: string): Promise<{ jwtToken: string; user: any }> {
    const response = await fetch(`${this.baseUrl}/api/auth/refresh?token=${encodeURIComponent(token)}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Token refresh failed: ${response.status} ${response.statusText}`);
    }

    const refreshData = await response.json();
    this.jwtToken = refreshData.jwt_token;
    return refreshData;
  }

  // Helper method to get agent health
  async getHealth(): Promise<any> {
    const response = await fetch(`${this.baseUrl}/api/agent/luka/health`);
    
    if (!response.ok) {
      throw new Error(`Health check failed: ${response.status} ${response.statusText}`);
    }

    return response.json();
  }

  // Helper method to get agent info
  async getInfo(): Promise<any> {
    const response = await fetch(`${this.baseUrl}/api/agent/luka/info`);
    
    if (!response.ok) {
      throw new Error(`Info request failed: ${response.status} ${response.statusText}`);
    }

    return response.json();
  }
}
