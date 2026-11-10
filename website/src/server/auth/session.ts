import "server-only";

import { cookies } from "next/headers";
import { getConfig } from "@/server/config";
import { issueSessionToken, type WebsiteSession, verifySessionToken } from "@/server/auth/jwt";

export const SESSION_COOKIE = "telesales_session";

export async function getSession(): Promise<WebsiteSession | null> {
  const token = (await cookies()).get(SESSION_COOKIE)?.value;
  if (!token) return null;
  try {
    return await verifySessionToken(token);
  } catch {
    return null;
  }
}

export async function setSession(session: WebsiteSession) {
  const config = getConfig();
  (await cookies()).set(SESSION_COOKIE, await issueSessionToken(session), {
    httpOnly: true,
    secure: config.websiteUrl.startsWith("https://"),
    sameSite: "lax",
    path: "/",
    maxAge: 60 * 60 * 8,
  });
}

export async function clearSession() {
  (await cookies()).set(SESSION_COOKIE, "", { httpOnly: true, path: "/", maxAge: 0 });
}
