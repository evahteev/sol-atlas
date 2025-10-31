"use client";
import React, { useEffect, useMemo, useState } from "react";
import "@copilotkit/react-ui/styles.css";
import "./style.css";
import {
  CopilotKit,
  useFrontendTool,
  useCopilotChat,
} from "@copilotkit/react-core";
import { CopilotChat } from "@copilotkit/react-ui";

interface BotApiChatProps {
  params: Promise<{ integrationId: string }>;
}

const BotApiChat: React.FC<BotApiChatProps> = ({ params }) => {
  const { integrationId } = React.use(params);

  return (
    <CopilotKit
      runtimeUrl={`/api/copilotkit/${integrationId}`}
      showDevConsole={false}
      // agent lock to the relevant agent
      agent="bot_api_chat"
    >
      <Chat />
    </CopilotKit>
  );
};

const Chat = () => {
  const [background, setBackground] = useState<string>();
  const chat = useCopilotChat();
  const { isLoading } = chat;
  
  const messages = useMemo(
    () =>
      (chat as { messages?: Array<{ id?: string; role?: string; content?: string }> }).messages ?? [],
    [chat]
  );

  const messageSummaries = useMemo(
    () =>
      messages.map((msg) => ({
        id: msg.id,
        role: msg.role,
        contentPreview: msg.content?.slice(0, 80) ?? "",
        contentLength: msg.content?.length ?? 0,
      })),
    [messages],
  );

  useEffect(() => {
    console.log("BotApiChat: CopilotChat messages updated", messageSummaries);
  }, [messageSummaries]);

  useEffect(() => {
    console.log("BotApiChat: Chat loading state changed", { isLoading });
  }, [isLoading]);

  useFrontendTool({
    name: "change_background",
    description:
      "Change the background color of the chat. Can be anything that the CSS background attribute accepts. Regular colors, linear of radial gradients etc.",
    parameters: [
      {
        name: "background",
        type: "string",
        description: "The background. Prefer gradients. Only use when asked.",
      },
    ],
    handler: ({ background }) => {
      setBackground(background);
      return {
        status: "success",
        message: `Background changed to ${background}`,
      };
    },
  });

  console.log("BotApiChat: Rendering Chat component", {
    isLoading,
    background,
    messageCount: messages.length,
    messageSummaries,
  });

  return (
    <div
      className="flex justify-center items-center h-full w-full"
      data-testid="background-container"
      style={{ background }}
    >
      <div className="h-full w-full md:w-8/10 md:h-8/10 rounded-lg">
        <CopilotChat
          className="h-full rounded-2xl max-w-6xl mx-auto"
          labels={{ initial: "Hi! I'm Luka Bot. How can I help you today?" }}
          suggestions={[
            {
              title: "Check bot health",
              message: "Check the health status of the Luka bot",
            },
            {
              title: "Get bot info",
              message: "Get detailed information about the Luka bot",
            },
            {
              title: "Change background",
              message: "Change the background to something new.",
            },
          ]}
        />
      </div>
    </div>
  );
};

export default BotApiChat;
