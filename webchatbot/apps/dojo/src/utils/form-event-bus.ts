import { FormRequest } from '@/components/form-renderer';

interface FormEventData extends FormRequest {
  renderMode?: string;
  complexity?: string;
  timestamp?: number;
}

class FormEventBus {
  private listeners: Set<(event: FormEventData) => void> = new Set();
  
  constructor() {
    console.log('🚌 FormEventBus: Initialized');
    
    // Make it available globally for server-side code
    if (typeof globalThis !== 'undefined') {
      (globalThis as any).__formEventBus = this;
    }
  }
  
  emit(event: FormEventData) {
    console.log('📤 FormEventBus: Emitting event', {
      form_id: event.form_id,
      title: event.title,
      renderMode: event.renderMode,
      listenerCount: this.listeners.size
    });
    
    // Store in globalThis for SSR scenarios
    if (typeof globalThis !== 'undefined') {
      if (!(globalThis as any).__pendingFormEvents) {
        (globalThis as any).__pendingFormEvents = [];
      }
      (globalThis as any).__pendingFormEvents.push(event);
    }
    
    // Notify all listeners
    this.listeners.forEach(listener => {
      try {
        listener(event);
      } catch (error) {
        console.error('❌ FormEventBus: Error in listener', error);
      }
    });
  }
  
  subscribe(listener: (event: FormEventData) => void): () => void {
    this.listeners.add(listener);
    console.log('👂 FormEventBus: Listener subscribed, total:', this.listeners.size);
    
    return () => {
      this.listeners.delete(listener);
      console.log('👋 FormEventBus: Listener unsubscribed, remaining:', this.listeners.size);
    };
  }
  
  // Process any pending events from SSR
  processPendingEvents() {
    if (typeof globalThis !== 'undefined' && (globalThis as any).__pendingFormEvents) {
      const pendingEvents = (globalThis as any).__pendingFormEvents;
      (globalThis as any).__pendingFormEvents = [];
      
      console.log('🔄 FormEventBus: Processing', pendingEvents.length, 'pending events');
      pendingEvents.forEach((event: FormEventData) => {
        this.listeners.forEach(listener => {
          try {
            listener(event);
          } catch (error) {
            console.error('❌ FormEventBus: Error processing pending event', error);
          }
        });
      });
    }
  }
}

// Singleton instance
let formEventBus: FormEventBus | null = null;

export function getFormEventBus(): FormEventBus {
  if (!formEventBus) {
    formEventBus = new FormEventBus();
  }
  return formEventBus;
}