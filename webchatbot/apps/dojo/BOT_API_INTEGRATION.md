# Bot API Integration

This document describes how to integrate Dojo with the Luka Bot API that is AG-UI compatible.

## Overview

The integration connects Dojo to the Luka Bot API at `https://bot-dexguru.dexguru.biz` and provides a chat interface for interacting with the bot using the AG-UI protocol.

**Status: ✅ FULLY FUNCTIONAL** - The integration is complete and working with guest authentication.

## Features

- **AG-UI Compatible**: Uses the standard AG-UI protocol for agent communication
- **Authentication Support**: Supports guest sessions, Telegram Mini App authentication, and the Telegram web login widget
- **Password Protection**: Supports password-protected bot access
- **Multiple Endpoints**: Connects to various bot API endpoints including health checks and agent info
- **Real-time Chat**: Provides a real-time chat interface for user interaction

## Setup

### 1. Environment Variables

Add the following environment variables to your `.env.local` file:

```bash
BOT_API_URL=https://bot-dexguru.dexguru.biz
BOT_API_PASSWORD=your_bot_password_here
NEXT_PUBLIC_TELEGRAM_BOT_USERNAME=your_bot_username_without_at_symbol
```

### 2. Available Features

The bot API integration provides the following features:

- `agentic_chat` - Basic chat functionality
- `agentic_generative_ui` - Generative UI capabilities
- `human_in_the_loop` - Human-in-the-loop interactions
- `shared_state` - Shared state management
- `tool_based_generative_ui` - Tool-based UI generation
- `backend_tool_rendering` - Backend tool rendering
- `predictive_state_updates` - Predictive state updates
- `bot_api_chat` - Dedicated bot API chat interface

## API Endpoints

The bot API provides several endpoints:

- `/api/agent/luka` - Main agent endpoint for chat interactions
- `/api/auth/guest` - Create guest sessions
- `/api/auth/telegram-miniapp` - Telegram Mini App authentication
- `/api/auth/refresh` - Token refresh
- `/api/agent/luka/health` - Bot health check
- `/api/agent/luka/info` - Bot information
- `/api/catalog` - Knowledge base catalog
- `/api/profile` - User profile management
- `/api/auth/telegram` *(Next.js)* - Exchanges Telegram auth data for Luka JWT tokens and stores them in secure cookies
- `/api/auth/session` *(Next.js)* - Reads or clears the stored Luka bot session

## Usage

1. Set the `BOT_API_PASSWORD` environment variable with your bot password
2. Start the Dojo development server: `pnpm run dev` (or `NEXT_DEV_HTTPS=1 pnpm run dev` for HTTPS)
3. Select the "Bot API" integration from the menu
4. (Optional) Authenticate with Telegram via the sidebar login button or by opening the demo inside the Telegram Mini App (auto sign-in)
5. Choose any of the available features (e.g., "Bot API Chat")
6. Start chatting with the Luka Bot

**Note**: The BotApiAgent automatically handles authentication by:
- Creating a guest session on first use
- Using the guest token with your password for agent requests
- Automatically re-authenticating if the token expires

## Authentication

The bot uses a two-step authentication process:

1. **Guest Session Creation**: First, create a guest session via `/api/auth/guest` to get a bearer token
2. **Password Authentication**: Use the bearer token with a password to access the agent endpoints

### Authentication Methods:

- **Guest Session + Password**: Create guest session, then use password with the token
- **Telegram Mini App**: Full authentication via Telegram initData (returns JWT token)
- **Telegram Web Login**: Sidebar login widget exchanges Telegram auth data via `/api/auth/telegram`
- **Token Refresh**: Refresh expired tokens via `/api/auth/refresh`

### Guest Session Permissions:
- `read:public_kb` - Read public knowledge bases
- `chat:ephemeral` - Send ephemeral chat messages
- `search:public_kb` - Search public knowledge bases

## Bot Capabilities

Based on the API health check, the Luka Bot supports:

- **Agentic Chat**: Real-time chat with LLM streaming
- **Human in the Loop**: Interactive task approval and completion
- **Backend Tool Rendering**: Visualization of tool execution
- **Catalog Search**: Search across knowledge bases
- **Task Management**: Camunda BPMN task management
- **Command Execution**: Slash commands for quick actions

## Integrations

The bot integrates with:

- **Camunda**: BPMN workflow engine
- **Elasticsearch**: Knowledge base search
- **Flow API**: User authentication
- **S3**: File storage

## Customization

You can customize the bot behavior by:

- Modifying the agent instructions in the CopilotSidebar
- Adding custom actions using `useCopilotAction`
- Configuring different bot endpoints for different features
- Implementing custom authentication flows

## Troubleshooting

### Common Issues

1. **403 Forbidden Error**: Make sure you've set the `BOT_API_PASSWORD` environment variable
2. **Connection Failed**: Verify the `BOT_API_URL` is correct and accessible
3. **Authentication Issues**: Check that your password is correct and the bot is running

### Testing the Connection

You can test the bot API connection using the provided test script:

```bash
node test-bot-api.js
```

This will test:
- Health endpoint
- Info endpoint
- Guest session creation
- Agent endpoint (with password)

## Files Modified

- `src/agents/bot-api-agent.ts` - Bot API agent implementation
- `src/agents.ts` - Agent integration configuration
- `src/env.ts` - Environment variable configuration
- `src/types/integration.ts` - Feature type definitions
- `src/config.ts` - Feature configuration
- `src/app/[integrationId]/feature/bot_api_chat/` - Bot API chat feature page
