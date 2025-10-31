"use client";

import React from "react";
import { Button } from "@/components/ui/button";
import { useUiContext } from "@/contexts/ui-context";
import { useCommand } from "@/contexts/command-context";
import type { UiMode } from "@/types/ui-context";
import { cn } from "@/lib/utils";

interface ModeButtonProps {
  mode: UiMode;
  isActive: boolean;
  onSelect: (mode: UiMode) => void;
}

function ModeButton({ mode, isActive, onSelect }: ModeButtonProps) {
  return (
    <Button
      variant={isActive ? "default" : "outline"}
      size="sm"
      className={cn(
        "whitespace-nowrap",
        isActive ? "shadow-sm" : "border-border text-muted-foreground hover:text-foreground",
      )}
      onClick={() => onSelect(mode)}
    >
      {mode.label ?? mode.id}
      {typeof mode.badgeCount === "number" && mode.badgeCount > 0 && (
        <span className="ml-2 inline-flex min-w-[1.25rem] items-center justify-center rounded-full bg-primary-foreground px-1 text-[10px] font-semibold text-primary">
          {mode.badgeCount}
        </span>
      )}
    </Button>
  );
}

export function ModeBar({ className }: { className?: string }) {
  const { uiContext, sendCommand } = useUiContext();
  const { executeCommand } = useCommand();

  if (!uiContext) {
    return null;
  }

  const handleSelect = async (mode: UiMode) => {
    // Update the UI state
    sendCommand({ commandId: mode.id });
    
    // Also execute the actual command to send to the bot
    try {
      await executeCommand(`/${mode.id}`);
      
      // Special handling for the start command to fetch onboarding form
      if (mode.id === 'start') {
        try {
          // Detect browser language and create Accept-Language header
          const browserLang = navigator.language || 'en-US';
          const acceptLanguage = browserLang.startsWith('ru') ? 'ru-RU,ru;q=0.9,en;q=0.8' : 'en-US,en;q=0.9';
          
          console.log('ModeBar: Detected browser language:', browserLang, '-> Accept-Language:', acceptLanguage);
          
          const response = await fetch('http://localhost:8000/api/agent/luka/onboarding-form?is_guest=true', {
            headers: {
              'Accept-Language': acceptLanguage
            }
          });
          if (response.ok) {
            const formData = await response.json();
            console.log('ModeBar: Received onboarding form', formData);
            
            // Dispatch form-request event for FormContext
            if (formData.type === 'formRequest') {
              window.dispatchEvent(new CustomEvent('form-request', {
                detail: formData
              }));
            }
          } else {
            console.error('ModeBar: Failed to fetch onboarding form', response.status);
          }
        } catch (fetchError) {
          console.error('ModeBar: Error fetching onboarding form', fetchError);
        }
      }
    } catch (error) {
      console.error('ModeBar: Failed to execute command', { mode: mode.id, error });
    }
  };

  return (
    <div className={cn("flex flex-wrap gap-2", className)}>
      {uiContext.modes
        .filter((mode) => mode.showInMenu ?? true)
        .map((mode) => (
          <ModeButton
            key={mode.id}
            mode={mode}
            isActive={mode.id === uiContext.activeMode}
            onSelect={handleSelect}
          />
        ))}
    </div>
  );
}
