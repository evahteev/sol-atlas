import "server-only";

import { AgentIntegrationConfig } from "./types/integration";
import getEnvVars from "./env";
import { BotApiAgent } from "./agents/bot-api-agent";
import { BOT_API_AUTH_COOKIE, deserializeBotApiSession } from "@/server/bot-api-session";

const envVars = getEnvVars();

export const agentsIntegrations: AgentIntegrationConfig[] = [
  {
    id: "bot-api",
    agents: async ({ request }) => {
      console.log('🏗️ bot-api integration: Creating agents');
      const authCookie = request.cookies.get(BOT_API_AUTH_COOKIE)?.value;
      const session = deserializeBotApiSession(authCookie);

      const jwtToken = session?.token;
      const userId = session?.user?.id ? String(session.user.id) : undefined;
      
      console.log('🏗️ bot-api integration: Agent config', {
        baseUrl: envVars.botApiUrl,
        hasJwtToken: !!jwtToken,
        userId
      });

      const createAgent = () =>
        new BotApiAgent({
          baseUrl: envVars.botApiUrl,
          jwtToken,
          userId,
        });

      return {
        agentic_chat: createAgent(),
        agentic_generative_ui: createAgent(),
        human_in_the_loop: createAgent(),
        shared_state: createAgent(),
        tool_based_generative_ui: createAgent(),
        backend_tool_rendering: createAgent(),
        predictive_state_updates: createAgent(),
        bot_api_chat: createAgent(),
      };
    },
  },
];
