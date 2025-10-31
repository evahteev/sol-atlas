"use client";

import React from "react";
import { useUiContext } from "@/contexts/ui-context";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export function QuickPromptStrip({ className }: { className?: string }) {
  const { uiContext, sendQuickPrompt } = useUiContext();

  if (!uiContext || !uiContext.quickPrompts || uiContext.quickPrompts.length === 0) {
    return null;
  }

  return (
    <div className={cn("flex flex-wrap gap-2", className)}>
      {uiContext.quickPrompts.map((prompt) => (
        <Button
          key={prompt.id}
          variant="secondary"
          size="sm"
          className="max-w-full truncate border-border text-xs text-muted-foreground hover:text-foreground"
          onClick={() => sendQuickPrompt(prompt.id, prompt.text)}
        >
          {prompt.text}
        </Button>
      ))}
    </div>
  );
}
