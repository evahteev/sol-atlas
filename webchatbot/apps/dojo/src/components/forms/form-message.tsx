import React from 'react';
import { InlineChatForm } from './inline-chat-form';
import { InlineFormMessage } from '@/types/inline-forms';
import { useFormContext } from '@/contexts/form-context';

interface FormMessageProps {
  formMessage: InlineFormMessage;
  className?: string;
}

export const FormMessage: React.FC<FormMessageProps> = ({
  formMessage,
  className = ''
}) => {
  const { submitForm, updateInlineFormStatus } = useFormContext();

  const handleFormSubmit = async (formId: string, data: Record<string, any>) => {
    // Update form status to submitting
    updateInlineFormStatus(formId, 'submitting');
    
    try {
      // Submit the form through the context
      await submitForm(formId, data);
      
      // Update form status to submitted
      updateInlineFormStatus(formId, 'submitted');
    } catch (error) {
      console.error('Error submitting inline form:', error);
      updateInlineFormStatus(formId, 'error');
    }
  };

  const isDisabled = formMessage.status === 'submitted' || formMessage.status === 'expired';

  return (
    <div className={`form-message my-2 ${className}`}>
      <InlineChatForm
        form={formMessage.formData}
        onSubmit={handleFormSubmit}
        disabled={isDisabled}
        className={`
          ${formMessage.status === 'submitted' ? 'opacity-60' : ''}
          ${formMessage.status === 'expired' ? 'opacity-40' : ''}
        `}
      />
      
      {/* Status indicator */}
      {formMessage.status === 'submitted' && (
        <div className="text-xs text-green-600 mt-1 pl-2">
          ✓ Submitted
        </div>
      )}
      
      {formMessage.status === 'expired' && (
        <div className="text-xs text-gray-500 mt-1 pl-2">
          ⏰ Expired
        </div>
      )}
    </div>
  );
};