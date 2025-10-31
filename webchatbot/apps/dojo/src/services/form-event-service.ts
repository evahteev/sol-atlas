import { FormRequest } from '@/components/form-renderer';

interface FormEventListener {
  (event: FormRequest): void;
}

class FormEventService {
  private listeners: Set<FormEventListener> = new Set();
  private eventSource: EventSource | null = null;
  private isConnected: boolean = false;
  
  constructor() {
    console.log('🎯 FormEventService: Initialized');
  }
  
  // Connect to the backend SSE stream
  connect(baseUrl: string, token?: string) {
    if (this.isConnected) {
      console.log('🔌 FormEventService: Already connected');
      return;
    }
    
    try {
      const url = `${baseUrl}/api/events/forms`;
      const headers: Record<string, string> = {};
      
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
      
      console.log('🚀 FormEventService: Connecting to', url);
      
      // Create EventSource for SSE connection
      this.eventSource = new EventSource(url);
      
      this.eventSource.onopen = () => {
        console.log('✅ FormEventService: Connected to form event stream');
        this.isConnected = true;
      };
      
      this.eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('📨 FormEventService: Received event', data);
          
          if (data.type === 'form:request') {
            this.notifyListeners(data.form);
          }
        } catch (error) {
          console.error('❌ FormEventService: Error parsing event', error);
        }
      };
      
      this.eventSource.onerror = (error) => {
        console.error('❌ FormEventService: Connection error', error);
        this.isConnected = false;
        
        // Reconnect after 5 seconds
        setTimeout(() => {
          console.log('🔄 FormEventService: Attempting reconnection...');
          this.disconnect();
          this.connect(baseUrl, token);
        }, 5000);
      };
      
    } catch (error) {
      console.error('❌ FormEventService: Failed to connect', error);
    }
  }
  
  // Disconnect from the event stream
  disconnect() {
    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
      this.isConnected = false;
      console.log('🔌 FormEventService: Disconnected');
    }
  }
  
  // Subscribe to form events
  subscribe(listener: FormEventListener): () => void {
    this.listeners.add(listener);
    console.log('👂 FormEventService: Listener subscribed, total:', this.listeners.size);
    
    // Return unsubscribe function
    return () => {
      this.listeners.delete(listener);
      console.log('👋 FormEventService: Listener unsubscribed, remaining:', this.listeners.size);
    };
  }
  
  // Notify all listeners
  private notifyListeners(form: FormRequest) {
    console.log('📢 FormEventService: Notifying', this.listeners.size, 'listeners');
    this.listeners.forEach(listener => {
      try {
        listener(form);
      } catch (error) {
        console.error('❌ FormEventService: Error in listener', error);
      }
    });
  }
  
  // Manual form event dispatch (for testing or fallback)
  dispatchFormEvent(form: FormRequest) {
    console.log('📤 FormEventService: Manually dispatching form event', form);
    this.notifyListeners(form);
  }
}

// Singleton instance
let formEventService: FormEventService | null = null;

export function getFormEventService(): FormEventService {
  if (!formEventService) {
    formEventService = new FormEventService();
  }
  return formEventService;
}