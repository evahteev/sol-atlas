import "server-only";

import { BotApiSession } from "@/types/auth";

export const BOT_API_AUTH_COOKIE = "botApiAuth";
const BASE64_ENCODING: BufferEncoding = "base64url";

export function serializeBotApiSession(session: BotApiSession): string {
  return Buffer.from(JSON.stringify(session), "utf8").toString(BASE64_ENCODING);
}

export function deserializeBotApiSession(value?: string | null): BotApiSession | null {
  if (!value) {
    return null;
  }

  try {
    const decoded = Buffer.from(value, BASE64_ENCODING).toString("utf8");
    return JSON.parse(decoded) as BotApiSession;
  } catch (error) {
    console.error("Failed to deserialize bot API session cookie", error);
    return null;
  }
}
