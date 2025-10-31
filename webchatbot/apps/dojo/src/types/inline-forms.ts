export enum FormRenderMode {
  MODAL = 'modal',
  INLINE = 'inline'
}

export interface InlineFormState {
  formId: string;
  status: 'active' | 'submitting' | 'submitted' | 'expired' | 'error';
  submittedData?: Record<string, any>;
  error?: string;
  timestamp: number;
}

// Define FormRequest and FormField locally to avoid import issues
export interface FormField {
  type: 'text' | 'button' | 'checkbox' | 'radio' | 'combobox' | 'slider';
  name: string;
  label: string;
  placeholder?: string;
  required?: boolean;
  variant?: 'primary' | 'secondary' | 'outline';
  metadata?: Record<string, any>;
}

export interface FormRequest {
  form_id: string;
  title: string;
  description?: string;
  fields: FormField[];
  metadata?: Record<string, any>;
}

export interface InlineFormMessage {
  id: string;
  type: 'form';
  formData: FormRequest;
  renderMode: FormRenderMode;
  status: 'active' | 'submitted' | 'expired';
  timestamp: number;
}

export interface ChatFormMessage extends BaseMessage {
  type: 'form';
  formData: FormRequest;
  renderMode: FormRenderMode;
  status: 'active' | 'submitted' | 'expired';
}

// Base message interface (should match your existing chat message structure)
interface BaseMessage {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  createdAt: string;
}