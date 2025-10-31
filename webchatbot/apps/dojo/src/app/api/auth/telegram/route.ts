"use server";

import { NextRequest, NextResponse } from "next/server";

import getEnvVars from "@/env";
import { BOT_API_AUTH_COOKIE, serializeBotApiSession } from "@/server/bot-api-session";
import { BotApiSession, TelegramUser } from "@/types/auth";

type TelegramAuthResponse = {
  jwt_token?: string;
  token?: string;
  refresh_token?: string;
  expires_in?: number;
  expires_at?: string;
  user?: TelegramUser;
};

const DEFAULT_SESSION_TTL_SECONDS = 60 * 60; // 1 hour

export async function POST(request: NextRequest) {
  let initData: string | undefined;

  try {
    const body = await request.json();
    initData = body?.initData;
  } catch {
    // Ignore json parse errors here; handled below with validation
  }

  if (!initData || typeof initData !== "string" || initData.trim().length === 0) {
    return NextResponse.json({ error: "Missing Telegram init data" }, { status: 400 });
  }

  const envVars = getEnvVars();

  let authResponse: Response;
  try {
    authResponse = await fetch(`${envVars.botApiUrl}/api/auth/telegram-miniapp`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ initData }),
    });
  } catch (error) {
    console.error("Failed to reach bot API Telegram auth endpoint", error);
    return NextResponse.json({ error: "Unable to reach bot authentication service" }, { status: 502 });
  }

  if (!authResponse.ok) {
    let errorDetails: unknown;
    try {
      errorDetails = await authResponse.json();
    } catch {
      errorDetails = await authResponse.text();
    }
    console.error("Bot API Telegram auth failed", authResponse.status, errorDetails);
    return NextResponse.json(
      { error: "Telegram authentication failed", details: errorDetails },
      { status: authResponse.status === 401 ? 401 : 502 },
    );
  }

  let authPayload: TelegramAuthResponse;
  try {
    authPayload = (await authResponse.json()) as TelegramAuthResponse;
  } catch (error) {
    console.error("Unable to parse bot API auth response", error);
    return NextResponse.json({ error: "Invalid authentication response" }, { status: 502 });
  }

  const token = authPayload.jwt_token || authPayload.token;
  if (!token) {
    console.error("Authentication response missing token", authPayload);
    return NextResponse.json({ error: "Authentication response missing token" }, { status: 502 });
  }

  const issuedAt = Date.now();
  const expiresAt =
    authPayload.expires_at != null
      ? new Date(authPayload.expires_at).getTime()
      : issuedAt + 1000 * (authPayload.expires_in ?? DEFAULT_SESSION_TTL_SECONDS);

  const session: BotApiSession = {
    token,
    refreshToken: authPayload.refresh_token,
    expiresAt,
    issuedAt,
    user: authPayload.user,
  };

  const response = NextResponse.json(
    {
      authenticated: true,
      user: authPayload.user,
      issuedAt,
      expiresAt,
    },
    { status: 200 },
  );

  const maxAgeSeconds = Math.max(
    60,
    Math.floor((expiresAt - issuedAt) / 1000 || DEFAULT_SESSION_TTL_SECONDS),
  );

  response.cookies.set({
    name: BOT_API_AUTH_COOKIE,
    value: serializeBotApiSession(session),
    httpOnly: true,
    sameSite: "lax",
    secure: process.env.NODE_ENV === "production",
    path: "/",
    maxAge: maxAgeSeconds,
  });

  return response;
}
