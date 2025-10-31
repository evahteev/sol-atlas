import { BotApiChatPanel } from "@/components/bot-api-chat-panel";

export default function Home() {
  return (
    <div className="flex h-full w-full bg-background text-foreground">
      <section className="w-full h-full bg-card">
        <BotApiChatPanel />
      </section>
    </div>
  );
}
