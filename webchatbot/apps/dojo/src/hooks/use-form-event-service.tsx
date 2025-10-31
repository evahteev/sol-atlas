import { useEffect, useRef } from 'react';
import { FormRequest } from '@/components/form-renderer';
import { getFormEventService } from '@/services/form-event-service';
import getEnvVars from '@/env';

interface UseFormEventServiceOptions {
  onFormRequest: (form: FormRequest) => void;
  enabled?: boolean;
}

export function useFormEventService({ onFormRequest, enabled = true }: UseFormEventServiceOptions) {
  const serviceRef = useRef(getFormEventService());
  const envVars = getEnvVars();
  
  useEffect(() => {
    if (!enabled) return;
    
    const service = serviceRef.current;
    
    // Connect to the backend if not already connected
    service.connect(envVars.botApiUrl);
    
    // Subscribe to form events
    const unsubscribe = service.subscribe((form) => {
      console.log('🎣 useFormEventService: Received form event', form);
      onFormRequest(form);
    });
    
    // Cleanup on unmount
    return () => {
      unsubscribe();
    };
  }, [enabled, onFormRequest, envVars.botApiUrl]);
  
  // Return service instance for manual operations if needed
  return serviceRef.current;
}