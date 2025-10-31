"use client";

import React from "react";
import { useUiContext } from "@/contexts/ui-context";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { UiScopeControl } from "@/types/ui-context";

interface ScopeControlsProps {
  className?: string;
}

export function ScopeControls({ className }: ScopeControlsProps) {
  const { uiContext, sendCommand } = useUiContext();

  if (!uiContext || !uiContext.scopeControls || uiContext.scopeControls.length === 0) {
    return null;
  }

  const handleToggle = (control: UiScopeControl) => {
    sendCommand({ commandId: "scope_toggle", payload: { scopeId: control.id } });
  };

  return (
    <div className={cn("flex flex-wrap items-center gap-2", className)}>
      {uiContext.scopeControls.map((control) => (
        <Button
          key={control.id}
          size="sm"
          variant={control.selected ? "default" : "outline"}
          className={cn(
            "border-border text-xs",
            control.selected ? "shadow-sm" : "text-muted-foreground hover:text-foreground",
          )}
          onClick={() => handleToggle(control)}
        >
          {control.emoji ? `${control.emoji} ${control.label}` : control.label}
        </Button>
      ))}
    </div>
  );
}
