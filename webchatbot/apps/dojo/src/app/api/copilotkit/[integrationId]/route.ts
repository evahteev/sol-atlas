import {
  CopilotRuntime,
  ExperimentalEmptyAdapter,
  copilotRuntimeNextJSAppRouterEndpoint,
} from "@copilotkit/runtime";
import { agentsIntegrations } from "@/agents";

import { NextRequest } from "next/server";

export async function POST(
  request: NextRequest,
  context: { params: Promise<{ integrationId: string }> }
) {
  const { integrationId } = await context.params;
  
  console.log('🔌 API Route: Processing request for integration:', integrationId);

  const integration = agentsIntegrations.find((i) => i.id === integrationId);
  if (!integration) {
    console.error('❌ API Route: Integration not found:', integrationId);
    return new Response("Integration not found", { status: 404 });
  }
  console.log('✅ API Route: Found integration:', integration.id);
  const agents = await integration.agents({ request });
  const runtime = new CopilotRuntime({
    // @ts-ignore for now
    agents,
  });
  const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
    runtime,
    serviceAdapter: new ExperimentalEmptyAdapter(),
    endpoint: `/api/copilotkit/${integrationId}`,
  });

  return handleRequest(request);
}
