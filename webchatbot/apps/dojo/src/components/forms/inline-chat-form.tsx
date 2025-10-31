import React, { useState } from 'react';
import { FormRequest, FormField } from '@/components/form-renderer';
import { ChatFormButton } from './chat-form-button';

interface InlineChatFormProps {
  form: FormRequest;
  onSubmit: (formId: string, data: Record<string, any>) => void;
  className?: string;
  disabled?: boolean;
}

export const InlineChatForm: React.FC<InlineChatFormProps> = ({
  form,
  onSubmit,
  className = '',
  disabled = false
}) => {
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleButtonClick = async (field: FormField) => {
    if (disabled || isSubmitting) return;

    setIsSubmitting(true);
    try {
      // For button fields, submit immediately with button data
      await onSubmit(form.form_id, {
        action: field.name,
        ...field.metadata,
        // Include any data from the field itself
        ...(field.metadata?.data || {})
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  // Get only button fields for inline rendering
  const buttonFields = form.fields.filter(f => f.type === 'button');
  
  // Determine layout based on number of buttons
  const getButtonLayout = () => {
    const count = buttonFields.length;
    if (count <= 3) {
      return 'flex flex-wrap gap-2';
    } else if (count <= 6) {
      return 'grid grid-cols-2 gap-2';
    } else {
      return 'flex flex-col gap-2';
    }
  };

  return (
    <div className={`
      inline-chat-form
      bg-muted/50 border border-border rounded-lg p-4 max-w-lg
      ${className}
    `}>
      {/* Form header */}
      <div className="mb-3">
        <h3 className="font-medium text-sm text-foreground mb-1">
          {form.title}
        </h3>
        {form.description && (
          <p className="text-xs text-muted-foreground leading-relaxed">
            {form.description}
          </p>
        )}
      </div>

      {/* Button layout */}
      {buttonFields.length > 0 && (
        <div className={getButtonLayout()}>
          {buttonFields.map((field) => (
            <ChatFormButton
              key={field.name}
              field={field}
              onSubmit={handleButtonClick}
              disabled={disabled || isSubmitting}
            />
          ))}
        </div>
      )}

      {/* Loading state indicator */}
      {isSubmitting && (
        <div className="mt-2 text-xs text-muted-foreground">
          Processing...
        </div>
      )}
    </div>
  );
};