import React from 'react';
import { Button } from '@/components/ui/button';
import { FormField } from '@/components/form-renderer';

interface ChatFormButtonProps {
  field: FormField;
  onSubmit: (field: FormField) => void;
  disabled?: boolean;
  className?: string;
}

export const ChatFormButton: React.FC<ChatFormButtonProps> = ({
  field,
  onSubmit,
  disabled = false,
  className = ''
}) => {
  const handleClick = () => {
    if (!disabled) {
      onSubmit(field);
    }
  };

  // Map form field variants to button variants
  const getButtonVariant = (variant?: string) => {
    switch (variant) {
      case 'primary':
        return 'default';
      case 'secondary':
        return 'secondary';
      case 'outline':
        return 'outline';
      default:
        return 'secondary';
    }
  };

  return (
    <Button
      variant={getButtonVariant(field.variant)}
      onClick={handleClick}
      disabled={disabled}
      className={`
        inline-flex items-center justify-center 
        text-sm font-medium transition-colors
        min-h-[36px] px-3 py-1.5
        hover:scale-105 active:scale-95
        ${className}
      `}
      size="sm"
    >
      {field.label}
    </Button>
  );
};