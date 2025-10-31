"use client";

import React from "react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { Phone, MapPin, ExternalLink } from "lucide-react";
import type { ReplyKeyboard, ReplyKeyboardButton } from "@/types/keyboard-events";

interface ReplyKeyboardProps {
  keyboard: ReplyKeyboard;
  onButtonClick: (button: ReplyKeyboardButton) => void;
  className?: string;
  disabled?: boolean;
}

function KeyboardButton({ 
  button, 
  onButtonClick, 
  isResized 
}: { 
  button: ReplyKeyboardButton; 
  onButtonClick: (button: ReplyKeyboardButton) => void;
  isResized: boolean;
}) {
  const getButtonIcon = () => {
    if (button.request_contact) {
      return <Phone className="h-4 w-4" />;
    }
    if (button.request_location) {
      return <MapPin className="h-4 w-4" />;
    }
    if (button.url) {
      return <ExternalLink className="h-4 w-4" />;
    }
    return null;
  };

  const getButtonVariant = () => {
    if (button.request_contact || button.request_location) {
      return "secondary";
    }
    if (button.command) {
      return "default";
    }
    return "outline";
  };

  const getButtonText = () => {
    let text = button.text;
    
    // Truncate long text if needed
    if (text.length > 25) {
      text = text.substring(0, 22) + "...";
    }
    
    return text;
  };

  const icon = getButtonIcon();

  return (
    <Button
      variant={getButtonVariant()}
      size={isResized ? "sm" : "default"}
      className={cn(
        "flex-1 min-h-[40px] transition-all duration-200",
        "hover:scale-[1.02] active:scale-[0.98]",
        "font-medium text-sm",
        isResized && "text-xs py-1.5",
        button.request_contact && "bg-green-50 hover:bg-green-100 border-green-200",
        button.request_location && "bg-blue-50 hover:bg-blue-100 border-blue-200",
        icon && "gap-2"
      )}
      onClick={() => onButtonClick(button)}
    >
      {icon}
      {getButtonText()}
    </Button>
  );
}

export function ReplyKeyboard({ 
  keyboard, 
  onButtonClick, 
  className,
  disabled = false 
}: ReplyKeyboardProps) {
  if (!keyboard.keyboard || keyboard.keyboard.length === 0) {
    return null;
  }

  const isResized = keyboard.resize_keyboard ?? true;
  const maxButtonsPerRow = Math.max(...keyboard.keyboard.map(row => row.length));
  const shouldCompact = maxButtonsPerRow > 3 || keyboard.keyboard.length > 4;

  return (
    <div 
      className={cn(
        "reply-keyboard bg-background border-t border-border/50",
        "p-3 space-y-2 transition-all duration-300 ease-in-out",
        "shadow-sm backdrop-blur-sm",
        disabled && "opacity-50 pointer-events-none",
        className
      )}
      role="group"
      aria-label="Reply keyboard"
    >
      {keyboard.keyboard.map((row, rowIndex) => (
        <div 
          key={rowIndex} 
          className={cn(
            "flex gap-2",
            shouldCompact && "gap-1"
          )}
          role="group"
          aria-label={`Keyboard row ${rowIndex + 1}`}
        >
          {row.map((button, buttonIndex) => (
            <KeyboardButton
              key={`${rowIndex}-${buttonIndex}`}
              button={button}
              onButtonClick={onButtonClick}
              isResized={isResized && shouldCompact}
            />
          ))}
        </div>
      ))}
      
      {/* Keyboard indicator */}
      <div className="flex justify-center pt-1">
        <div className="h-1 w-8 bg-border/30 rounded-full" />
      </div>
    </div>
  );
}

// Export types for external use