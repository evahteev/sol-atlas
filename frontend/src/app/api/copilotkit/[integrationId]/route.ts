/**
 * CopilotKit Runtime Endpoint for Bot API Integration
 *
 * This endpoint handles SSE streaming communication with the bot API.
 * It's called by the CopilotKit client-side hooks and proxies requests
 * to the bot API with proper authentication.
 *
 * Architecture decisions:
 * - Uses Next.js App Router route handlers for streaming support
 * - BotAPIServiceAdapter handles authentication with bot API
 * - integrationId maps to specific bot agents (e.g., 'luka')
 */
import { NextRequest } from 'next/server'

import {
  CopilotRuntime,
  ExperimentalEmptyAdapter,
  copilotRuntimeNextJSAppRouterEndpoint,
} from '@copilotkit/runtime'

import { agentsIntegrations } from '@/lib/agents-runtime'

export async function POST(request: NextRequest) {
  const { pathname } = new URL(request.url)
  const integrationId = pathname.split('/').pop()

  // Find the matching integration configuration
  const integration = agentsIntegrations.find((i) => i.id === integrationId)
  if (!integration) {
    return new Response('Integration not found', { status: 404 })
  }

  // Load agents for this integration
  // Auth is handled via auth() call inside agents-runtime
  const agents = await integration.agents()

  // Create CopilotKit runtime with bot API service adapter
  const runtime = new CopilotRuntime({
    agents,
  })

  // Configure endpoint handler
  const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
    runtime,
    serviceAdapter: new ExperimentalEmptyAdapter(),
    endpoint: `/api/copilotkit/${integrationId}`,
  })

  return handleRequest(request)
}

/**
 * OPTIONS handler for CORS preflight requests
 */
export async function OPTIONS() {
  return new Response(null, {
    status: 200,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    },
  })
}
