"use client";

import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { ExternalLink, CreditCard, Search, Loader2 } from "lucide-react";
import type { InlineKeyboard, InlineKeyboardButton } from "@/types/keyboard-events";

interface InlineKeyboardProps {
  keyboard: InlineKeyboard;
  onButtonClick: (button: InlineKeyboardButton) => void;
  className?: string;
  messageId?: string;
  disabled?: boolean;
}

function InlineButton({ 
  button, 
  onButtonClick, 
  isLoading = false 
}: { 
  button: InlineKeyboardButton; 
  onButtonClick: (button: InlineKeyboardButton) => void;
  isLoading?: boolean;
}) {
  const getButtonIcon = () => {
    if (isLoading) {
      return <Loader2 className="h-3 w-3 animate-spin" />;
    }
    if (button.url) {
      return <ExternalLink className="h-3 w-3" />;
    }
    if (button.pay) {
      return <CreditCard className="h-3 w-3" />;
    }
    if (button.switch_inline_query !== undefined || button.switch_inline_query_current_chat !== undefined) {
      return <Search className="h-3 w-3" />;
    }
    return null;
  };

  const getButtonVariant = () => {
    if (button.pay) {
      return "destructive";
    }
    if (button.url) {
      return "outline";
    }
    if (button.callback_data) {
      return "secondary";
    }
    return "default";
  };

  const getButtonText = () => {
    let text = button.text;
    
    // Truncate very long text for inline buttons
    if (text.length > 20) {
      text = text.substring(0, 17) + "...";
    }
    
    return text;
  };

  const icon = getButtonIcon();

  return (
    <Button
      variant={getButtonVariant()}
      size="sm"
      disabled={isLoading}
      className={cn(
        "flex-1 h-8 text-xs font-medium px-2",
        "transition-all duration-200",
        "hover:scale-[1.02] active:scale-[0.98]",
        "min-w-0", // Allow button to shrink
        button.pay && "bg-red-50 hover:bg-red-100 border-red-200 text-red-700",
        button.url && "bg-blue-50 hover:bg-blue-100 border-blue-200",
        icon && "gap-1.5"
      )}
      onClick={() => onButtonClick(button)}
    >
      {icon}
      <span className="truncate">{getButtonText()}</span>
    </Button>
  );
}

export function InlineKeyboard({ 
  keyboard, 
  onButtonClick, 
  className, 
  messageId,
  disabled = false 
}: InlineKeyboardProps) {
  const [loadingButtons, setLoadingButtons] = useState<Set<string>>(new Set());

  if (!keyboard.inline_keyboard || keyboard.inline_keyboard.length === 0) {
    return null;
  }

  const handleButtonClick = async (button: InlineKeyboardButton) => {
    if (disabled) return;

    // Add loading state for callback buttons
    if (button.callback_data) {
      const buttonKey = `${messageId}-${button.text}-${button.callback_data}`;
      setLoadingButtons(prev => new Set(prev).add(buttonKey));
      
      // Remove loading state after 3 seconds (fallback)
      setTimeout(() => {
        setLoadingButtons(prev => {
          const newSet = new Set(prev);
          newSet.delete(buttonKey);
          return newSet;
        });
      }, 3000);
    }

    onButtonClick(button);
  };

  const isButtonLoading = (button: InlineKeyboardButton): boolean => {
    if (!button.callback_data) return false;
    const buttonKey = `${messageId}-${button.text}-${button.callback_data}`;
    return loadingButtons.has(buttonKey);
  };

  const maxButtonsPerRow = Math.max(...keyboard.inline_keyboard.map(row => row.length));
  const shouldCompact = maxButtonsPerRow > 4;

  return (
    <div 
      className={cn(
        "inline-keyboard mt-3 space-y-1.5",
        "transition-all duration-200",
        disabled && "opacity-50 pointer-events-none",
        className
      )}
      data-message-id={messageId}
      role="group"
      aria-label="Inline keyboard"
    >
      {keyboard.inline_keyboard.map((row, rowIndex) => (
        <div 
          key={rowIndex} 
          className={cn(
            "flex gap-1.5",
            shouldCompact && "gap-1"
          )}
          role="group"
          aria-label={`Inline keyboard row ${rowIndex + 1}`}
        >
          {row.map((button, buttonIndex) => (
            <InlineButton
              key={`${rowIndex}-${buttonIndex}`}
              button={button}
              onButtonClick={handleButtonClick}
              isLoading={isButtonLoading(button)}
            />
          ))}
        </div>
      ))}
    </div>
  );
}

