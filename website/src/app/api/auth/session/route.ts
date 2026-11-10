import { NextResponse } from "next/server";
import { clearSession, getSession } from "@/server/auth/session";

export async function GET() {
  const session = await getSession();
  return NextResponse.json({ authenticated: Boolean(session), session });
}

export async function DELETE() {
  await clearSession();
  return new NextResponse(null, { status: 204 });
}
