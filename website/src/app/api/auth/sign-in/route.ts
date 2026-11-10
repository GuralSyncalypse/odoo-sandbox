import { NextResponse } from "next/server";
import { normalizeIdentity } from "@/server/auth/identity";
import { setSession } from "@/server/auth/session";
import { getConfig } from "@/server/config";

export async function POST(request: Request) {
  try {
    const body = await request.json() as { identifier?: unknown };
    if (typeof body.identifier !== "string") {
      return NextResponse.json({ error: "identifier is required." }, { status: 400 });
    }
    const identity = normalizeIdentity(body.identifier);
    const isAdmin = getConfig().adminSubjects.has(identity.subject.toLowerCase());
    await setSession({ subject: identity.subject, isAdmin });
    return NextResponse.json({ subject: identity.subject, isAdmin });
  } catch (error) {
    return NextResponse.json({ error: error instanceof Error ? error.message : "Unable to sign in." }, { status: 400 });
  }
}
