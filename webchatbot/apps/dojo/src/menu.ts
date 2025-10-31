import { MenuIntegrationConfig } from "./types/integration";

export const menuIntegrations: MenuIntegrationConfig[] = [
  {
    id: "bot-api",
    name: "Bot API (Luka Bot)",
    features: [
      "agentic_chat",
      "agentic_generative_ui",
      "human_in_the_loop",
      "shared_state",
      "tool_based_generative_ui",
      "backend_tool_rendering",
      "bot_api_chat",
    ],
  },
];

