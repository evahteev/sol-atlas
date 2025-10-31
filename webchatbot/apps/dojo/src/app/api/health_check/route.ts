import { NextResponse } from "next/server";

export function GET() {
  return NextResponse.json({ status: "ok" }, { status: 200 });
}

export function HEAD() {
  return new Response(null, { status: 200 });
}
