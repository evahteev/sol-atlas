"use server";

import { NextRequest, NextResponse } from "next/server";

import { BOT_API_AUTH_COOKIE, deserializeBotApiSession } from "@/server/bot-api-session";

export async function GET(request: NextRequest) {
  const cookieValue = request.cookies.get(BOT_API_AUTH_COOKIE)?.value;
  const session = deserializeBotApiSession(cookieValue);

  if (!session?.token) {
    return NextResponse.json({ authenticated: false }, { status: 200 });
  }

  return NextResponse.json(
    {
      authenticated: true,
      user: session.user,
      expiresAt: session.expiresAt,
      issuedAt: session.issuedAt,
    },
    { status: 200 },
  );
}

export async function DELETE() {
  const response = NextResponse.json({ authenticated: false }, { status: 200 });

  response.cookies.set({
    name: BOT_API_AUTH_COOKIE,
    value: "",
    httpOnly: true,
    sameSite: "lax",
    secure: process.env.NODE_ENV === "production",
    path: "/",
    maxAge: 0,
  });

  return response;
}
