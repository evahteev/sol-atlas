import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

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

interface FormRendererProps {
  form: FormRequest;
  onSubmit: (formId: string, data: Record<string, any>) => void;
  onCancel?: () => void;
}

export const FormRenderer: React.FC<FormRendererProps> = ({
  form,
  onSubmit,
  onCancel
}) => {
  const [formData, setFormData] = useState<Record<string, any>>({});
  const [errors, setErrors] = useState<Record<string, string>>({});

  const handleInputChange = (name: string, value: any) => {
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    // Clear error when user types
    if (errors[name]) {
      setErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[name];
        return newErrors;
      });
    }
  };

  const handleButtonClick = (field: FormField) => {
    // Dispatch form submission event
    window.dispatchEvent(new CustomEvent('copilotkit-form-submit', {
      detail: { formId: form.form_id, field: field.name },
      bubbles: true
    }));
    
    // For button fields, submit immediately with button data
    onSubmit(form.form_id, {
      action: field.name,
      ...field.metadata,
      ...formData
    });
  };

  const handleFormSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validate required fields
    const newErrors: Record<string, string> = {};
    let hasErrors = false;
    
    form.fields.forEach(field => {
      if (field.type === 'text' && field.required && !formData[field.name]) {
        newErrors[field.name] = `${field.label} is required`;
        hasErrors = true;
      }
    });

    if (hasErrors) {
      setErrors(newErrors);
      return;
    }

    // Dispatch form submission event
    window.dispatchEvent(new CustomEvent('copilotkit-form-submit', {
      detail: { formId: form.form_id },
      bubbles: true
    }));

    onSubmit(form.form_id, formData);
  };

  const renderField = (field: FormField) => {
    switch (field.type) {
      case 'text':
        return (
          <div key={field.name} className="space-y-2">
            <Label htmlFor={field.name}>
              {field.label}
              {field.required && <span className="text-red-500 ml-1">*</span>}
            </Label>
            <Input
              id={field.name}
              name={field.name}
              placeholder={field.placeholder}
              value={formData[field.name] || ''}
              onChange={(e) => handleInputChange(field.name, e.target.value)}
              className={errors[field.name] ? 'border-red-500' : ''}
            />
            {errors[field.name] && (
              <p className="text-sm text-red-500">{errors[field.name]}</p>
            )}
          </div>
        );

      case 'button':
        return (
          <Button
            key={field.name}
            variant={field.variant as any || 'secondary'}
            onClick={() => handleButtonClick(field)}
            className="w-full sm:w-auto"
          >
            {field.label}
          </Button>
        );

      // Add more field types as needed
      default:
        return (
          <div key={field.name} className="text-muted-foreground text-sm">
            Unsupported field type: {field.type}
          </div>
        );
    }
  };

  // Separate button fields from input fields
  const inputFields = form.fields.filter(f => f.type !== 'button');
  const buttonFields = form.fields.filter(f => f.type === 'button');

  return (
    <Card className="w-full max-w-2xl mx-auto">
      <CardHeader>
        <CardTitle>{form.title}</CardTitle>
        {form.description && (
          <CardDescription>{form.description}</CardDescription>
        )}
      </CardHeader>
      <CardContent>
        <form onSubmit={handleFormSubmit} className="space-y-4">
          {/* Render input fields */}
          {inputFields.map(field => renderField(field))}

          {/* Render button fields */}
          {buttonFields.length > 0 && (
            <div className="flex flex-wrap gap-2 pt-4">
              {buttonFields.map(field => renderField(field))}
            </div>
          )}

          {/* Form actions */}
          {inputFields.length > 0 && (
            <div className="flex justify-end space-x-2 pt-4">
              {onCancel && (
                <Button type="button" variant="outline" onClick={onCancel}>
                  Cancel
                </Button>
              )}
              <Button type="submit">
                Submit
              </Button>
            </div>
          )}
        </form>
      </CardContent>
    </Card>
  );
};