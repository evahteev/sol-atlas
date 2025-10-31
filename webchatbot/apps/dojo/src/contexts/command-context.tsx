"use client";

import React, { createContext, useContext, useState, useCallback, useEffect } from "react";
import { useCopilotChat } from "@copilotkit/react-core";
import { createCompatibleMessage } from "@/utils/copilotkit-compat";
import type {
  ParsedCommand,
  CommandDefinition,
  CommandExecutionEvent,
  CommandResultEvent
} from "@/types/command-events";

interface CommandContextValue {
  // Command state
  availableCommands: CommandDefinition[];
  commandHistory: ParsedCommand[];
  isExecuting: boolean;
  lastResult?: CommandResultEvent;
  
  // Command execution
  executeCommand: (commandText: string) => Promise<void>;
  parseCommand: (input: string) => ParsedCommand | null;
  
  // Command management
  addCommand: (command: CommandDefinition) => void;
  removeCommand: (commandName: string) => void;
  isCommandAvailable: (commandName: string) => boolean;
  getCommandSuggestions: (partial: string) => CommandDefinition[];
  
  // History management
  clearHistory: () => void;
  getRecentCommands: (limit?: number) => ParsedCommand[];
}

const CommandContext = createContext<CommandContextValue | undefined>(undefined);

interface CommandContextProviderProps {
  children: React.ReactNode;
  isGuest?: boolean;
  userId?: string;
  onCommandResult?: (result: CommandResultEvent) => void;
}

// Default available commands
const DEFAULT_COMMANDS: CommandDefinition[] = [
  {
    name: "start",
    description: "Show main menu with quick actions",
    requiresAuth: false,
    guestAllowed: true,
    aliases: ["menu", "home"],
    usage: "/start",
    examples: ["/start"]
  },
  {
    name: "groups",
    description: "Browse and manage groups",
    requiresAuth: false,
    guestAllowed: true, // Limited access for guests
    usage: "/groups [action]",
    examples: ["/groups", "/groups list", "/groups join"]
  },
  {
    name: "catalog",
    description: "Browse knowledge base catalog",
    requiresAuth: false,
    guestAllowed: true,
    usage: "/catalog [search]",
    examples: ["/catalog", "/catalog defi", "/catalog search trading"]
  },
  {
    name: "tasks",
    description: "View and manage Camunda tasks",
    requiresAuth: true,
    guestAllowed: false,
    usage: "/tasks [filter]",
    examples: ["/tasks", "/tasks pending", "/tasks completed"]
  },
  {
    name: "profile",
    description: "View and edit user profile",
    requiresAuth: true,
    guestAllowed: false,
    usage: "/profile [action]",
    examples: ["/profile", "/profile edit", "/profile settings"]
  },
  {
    name: "help",
    description: "Show available commands and help",
    requiresAuth: false,
    guestAllowed: true,
    aliases: ["?", "commands"],
    usage: "/help [command]",
    examples: ["/help", "/help tasks", "/?"]
  }
];

export function CommandContextProvider({ 
  children, 
  isGuest = false,
  userId,
  onCommandResult 
}: CommandContextProviderProps) {
  // State management
  const [availableCommands, setAvailableCommands] = useState<CommandDefinition[]>(DEFAULT_COMMANDS);
  const [commandHistory, setCommandHistory] = useState<ParsedCommand[]>([]);
  const [isExecuting, setIsExecuting] = useState(false);
  const [lastResult, setLastResult] = useState<CommandResultEvent | undefined>();

  // Get CopilotKit chat functions
  const { appendMessage } = useCopilotChat();

  // Command parsing
  const parseCommand = useCallback((input: string): ParsedCommand | null => {
    const trimmed = input.trim();
    if (!trimmed.startsWith('/')) {
      return null;
    }

    const withoutSlash = trimmed.slice(1);
    const parts = withoutSlash.split(/\s+/);
    const command = parts[0].toLowerCase();
    const args = parts.slice(1);

    // Check if command exists (including aliases)
    const commandDef = availableCommands.find(cmd => 
      cmd.name === command || (cmd.aliases && cmd.aliases.includes(command))
    );

    const isValid = !!commandDef && (!commandDef.requiresAuth || !isGuest);

    const parsedCommand: ParsedCommand = {
      command: commandDef?.name || command,
      args,
      raw: trimmed,
      isValid
    };

    console.log('CommandContext: Parsed command', parsedCommand);
    return parsedCommand;
  }, [availableCommands, isGuest]);

  // Command execution
  const executeCommand = useCallback(async (commandText: string): Promise<void> => {
    const parsedCommand = parseCommand(commandText);
    
    if (!parsedCommand) {
      console.log('CommandContext: Invalid command format', commandText);
      return;
    }

    if (!parsedCommand.isValid) {
      console.log('CommandContext: Command not available or requires auth', parsedCommand);
      
      // Show error message for invalid commands
      const commandDef = availableCommands.find(cmd => cmd.name === parsedCommand.command);
      if (commandDef?.requiresAuth && isGuest) {
        // Emit guest restriction event
        const restrictionEvent = {
          type: "guestRestriction",
          command: parsedCommand.command,
          message: `Command '/${parsedCommand.command}' requires authentication. Please sign in to use this feature.`,
          upgradePrompt: true,
          timestamp: Date.now()
        };
        
        window.dispatchEvent(new CustomEvent('command-restriction', {
          detail: restrictionEvent
        }));
      }
      return;
    }

    setIsExecuting(true);
    
    try {
      // Add to history
      setCommandHistory(prev => [...prev.slice(-9), parsedCommand]); // Keep last 10 commands

      // Create execution event
      const executionEvent: CommandExecutionEvent = {
        type: "commandExecution",
        command: parsedCommand,
        userId,
        isGuest,
        timestamp: Date.now()
      };

      console.log('CommandContext: Executing command', executionEvent);

      // Add user message to chat
      if (appendMessage && typeof appendMessage === 'function') {
        const userMessage = createCompatibleMessage({
          id: `cmd_${Date.now()}`,
          role: 'user' as const,
          content: commandText,
          createdAt: new Date().toISOString(),
        });
        appendMessage(userMessage);
      }

      // Emit command execution event for other components to handle
      window.dispatchEvent(new CustomEvent('command-execute', {
        detail: executionEvent
      }));

      // Handle built-in commands
      if (parsedCommand.command === 'help') {
        await handleHelpCommand(parsedCommand.args[0]);
      }

    } catch (error) {
      console.error('CommandContext: Command execution error', error);
      
      const errorResult: CommandResultEvent = {
        type: "commandResult",
        command: parsedCommand.command,
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
        timestamp: Date.now()
      };
      
      setLastResult(errorResult);
      onCommandResult?.(errorResult);
    } finally {
      setIsExecuting(false);
    }
  }, [parseCommand, availableCommands, isGuest, userId, appendMessage, onCommandResult]);

  // Handle help command
  const handleHelpCommand = useCallback(async (specificCommand?: string) => {
    const availableForUser = availableCommands.filter(cmd => 
      !cmd.requiresAuth || !isGuest
    );

    if (specificCommand) {
      const cmd = availableForUser.find(c => c.name === specificCommand);
      if (cmd) {
        const helpText = `**/${cmd.name}** - ${cmd.description}\n\n` +
          `**Usage:** ${cmd.usage}\n\n` +
          `**Examples:**\n${cmd.examples?.map(ex => `• ${ex}`).join('\n') || 'No examples available'}` +
          (cmd.aliases ? `\n\n**Aliases:** ${cmd.aliases.map(a => `/${a}`).join(', ')}` : '');
        
        if (appendMessage && typeof appendMessage === 'function') {
          const helpMessage = createCompatibleMessage({
            id: `help_${Date.now()}`,
            role: 'assistant' as const,
            content: helpText,
            createdAt: new Date().toISOString(),
          });
          appendMessage(helpMessage);
        }
      } else {
        if (appendMessage && typeof appendMessage === 'function') {
          const errorMessage = createCompatibleMessage({
            id: `help_error_${Date.now()}`,
            role: 'assistant' as const,
            content: `Command '/${specificCommand}' not found or not available.`,
            createdAt: new Date().toISOString(),
          });
          appendMessage(errorMessage);
        }
      }
    } else {
      const helpText = "**Available Commands:**\n\n" +
        availableForUser.map(cmd => 
          `**/${cmd.name}** - ${cmd.description}`
        ).join('\n') +
        (isGuest ? '\n\n*Some commands require authentication. Sign in for full access.*' : '') +
        '\n\nUse `/help <command>` for detailed information about a specific command.';
      
      if (appendMessage && typeof appendMessage === 'function') {
        const helpMessage = createCompatibleMessage({
          id: `help_all_${Date.now()}`,
          role: 'assistant' as const,
          content: helpText,
          createdAt: new Date().toISOString(),
        });
        appendMessage(helpMessage);
      }
    }
  }, [availableCommands, isGuest, appendMessage]);

  // Command management
  const addCommand = useCallback((command: CommandDefinition) => {
    setAvailableCommands(prev => {
      const exists = prev.find(cmd => cmd.name === command.name);
      if (exists) {
        return prev.map(cmd => cmd.name === command.name ? command : cmd);
      }
      return [...prev, command];
    });
  }, []);

  const removeCommand = useCallback((commandName: string) => {
    setAvailableCommands(prev => prev.filter(cmd => cmd.name !== commandName));
  }, []);

  const isCommandAvailable = useCallback((commandName: string): boolean => {
    const cmd = availableCommands.find(c => c.name === commandName);
    return !!cmd && (!cmd.requiresAuth || !isGuest);
  }, [availableCommands, isGuest]);

  const getCommandSuggestions = useCallback((partial: string): CommandDefinition[] => {
    const clean = partial.toLowerCase().replace(/^\//, '');
    
    return availableCommands
      .filter(cmd => {
        const matchesName = cmd.name.startsWith(clean);
        const matchesAlias = cmd.aliases?.some(alias => alias.startsWith(clean));
        const isAvailable = !cmd.requiresAuth || !isGuest;
        
        return (matchesName || matchesAlias) && isAvailable;
      })
      .sort((a, b) => {
        // Prioritize exact name matches over alias matches
        const aNameMatch = a.name.startsWith(clean);
        const bNameMatch = b.name.startsWith(clean);
        
        if (aNameMatch && !bNameMatch) return -1;
        if (!aNameMatch && bNameMatch) return 1;
        
        return a.name.localeCompare(b.name);
      })
      .slice(0, 5); // Limit to 5 suggestions
  }, [availableCommands, isGuest]);

  // History management
  const clearHistory = useCallback(() => {
    setCommandHistory([]);
  }, []);

  const getRecentCommands = useCallback((limit: number = 5): ParsedCommand[] => {
    return commandHistory.slice(-limit).reverse();
  }, [commandHistory]);

  // Update available commands when guest status changes
  useEffect(() => {
    console.log('CommandContext: Guest status or user changed', { isGuest, userId });
  }, [isGuest, userId]);

  // Listen for command result events from other components
  useEffect(() => {
    const handleCommandResult = (event: CustomEvent<CommandResultEvent>) => {
      setLastResult(event.detail);
      onCommandResult?.(event.detail);
      setIsExecuting(false);
    };

    window.addEventListener('command-result', handleCommandResult as EventListener);
    return () => {
      window.removeEventListener('command-result', handleCommandResult as EventListener);
    };
  }, [onCommandResult]);

  const value: CommandContextValue = {
    // State
    availableCommands,
    commandHistory,
    isExecuting,
    lastResult,
    
    // Execution
    executeCommand,
    parseCommand,
    
    // Management
    addCommand,
    removeCommand,
    isCommandAvailable,
    getCommandSuggestions,
    
    // History
    clearHistory,
    getRecentCommands,
  };

  return (
    <CommandContext.Provider value={value}>
      {children}
    </CommandContext.Provider>
  );
}

export function useCommand(): CommandContextValue {
  const context = useContext(CommandContext);
  if (!context) {
    throw new Error("useCommand must be used within CommandContextProvider");
  }
  return context;
}

// Hook for command input handling
export function useCommandInput() {
  const { executeCommand, parseCommand, getCommandSuggestions } = useCommand();
  
  const handleInput = useCallback(async (input: string) => {
    const trimmed = input.trim();
    
    if (trimmed.startsWith('/')) {
      await executeCommand(trimmed);
      return true; // Indicates command was handled
    }
    
    return false; // Not a command, let normal message handling proceed
  }, [executeCommand]);
  
  const getSuggestions = useCallback((input: string) => {
    if (input.startsWith('/') && input.length > 1) {
      return getCommandSuggestions(input);
    }
    return [];
  }, [getCommandSuggestions]);
  
  return {
    executeCommand,
    handleInput,
    getSuggestions,
    parseCommand
  };
}