/**
 * Agent Integration Configurations
 *
 * Defines how different bot agents are integrated with CopilotKit.
 * Each integration maps to a specific bot API endpoint and authentication scheme.
 *
 * Architecture:
 * - Server-only module (contains sensitive configuration)
 * - BotApiAgent handles SSE streaming with authentication
 * - Supports both authenticated users (next-auth) and guest authentication
 * - URL configuration from environment variables
 */
import { NextRequest } from 'next/server'

import { env } from 'next-runtime-env'
import 'server-only'

import auth from '@/auth'

import { BotApiAgent } from './bot-api-agent'

export interface AgentIntegrationConfig {
  id: string
  name?: string
  description?: string
  agents: (params?: { request?: NextRequest }) => Promise<{
    agentic_chat: BotApiAgent
    backend_tool_rendering: BotApiAgent
    human_in_the_loop: BotApiAgent
    shared_state: BotApiAgent
  }>
}

export const agentsIntegrations: AgentIntegrationConfig[] = [
  // ========================================
  // 🤖 LUKA BOT - Community Knowledge Assistant
  // ========================================
  {
    id: 'luka',
    name: 'Luka Bot',
    description: 'Community Knowledge Assistant',
    agents: async () => {
      const botApiUrl = env('NEXT_PUBLIC_BOT_API_URL') || 'https://bot-dexguru.dexguru.biz'

      // Try to get authenticated user session from next-auth
      const session = await auth()
      const jwtToken = session?.access_token as string | undefined
      const userId = session?.user?.webapp_user_id || session?.user?.camunda_user_id

      // Create BotApiAgent with authentication
      // If user is authenticated, use their JWT token
      // Otherwise, BotApiAgent will automatically call /api/auth/guest
      const createAgent = () =>
        new BotApiAgent({
          baseUrl: botApiUrl,
          jwtToken, // Pass existing token if available
          userId: userId ? String(userId) : undefined,
          // If jwtToken is undefined, BotApiAgent will auto-authenticate as guest
        })

      // All agent types use the same Luka bot
      return {
        agentic_chat: createAgent(),
        backend_tool_rendering: createAgent(),
        human_in_the_loop: createAgent(),
        shared_state: createAgent(),
      }
    },
  },
]
