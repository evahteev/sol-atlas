"use client";

import React from "react";
import { CommandDialog, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from "@/components/ui/command";
import { useUiContext } from "@/contexts/ui-context";

interface CommandPaletteProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function CommandPalette({ open, onOpenChange }: CommandPaletteProps) {
  const { uiContext, sendCommand } = useUiContext();

  const modes = uiContext?.modes ?? [];

  const handleSelect = (commandId: string) => {
    sendCommand({ commandId });
    onOpenChange(false);
  };

  return (
    <CommandDialog open={open} onOpenChange={onOpenChange}>
      <CommandInput placeholder="Type a command or search…" />
      <CommandList>
        <CommandEmpty>No commands found.</CommandEmpty>
        <CommandGroup heading="Navigation">
          {modes.map((mode) => (
            <CommandItem key={mode.id} value={mode.label} onSelect={() => handleSelect(mode.id)}>
              <span className="mr-2" aria-hidden>
                {mode.emoji ?? "•"}
              </span>
              {mode.label}
            </CommandItem>
          ))}
        </CommandGroup>
      </CommandList>
    </CommandDialog>
  );
}
