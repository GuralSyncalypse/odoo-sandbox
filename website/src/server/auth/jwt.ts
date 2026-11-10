import "server-only";

import { importPKCS8, jwtVerify, SignJWT } from "jose";
import { getConfig } from "@/server/config";

export type WebsiteSession = {
  subject: string;
  isAdmin: boolean;
};

const SESSION_ISSUER = "telesales-website-session";
const SESSION_AUDIENCE = "telesales-website";

async function privateKey() {
  return importPKCS8(getConfig().jwtPrivateKeyPem, "RS256");
}

function nowSeconds() {
  return Math.floor(Date.now() / 1000);
}

export async function issueOdooToken(session: WebsiteSession): Promise<string> {
  const config = getConfig();
  const now = nowSeconds();
  const token = new SignJWT(session.isAdmin ? { admin: true } : {})
    .setProtectedHeader({ alg: "RS256", typ: "JWT" })
    .setSubject(session.subject)
    .setJti(crypto.randomUUID())
    .setIssuer(config.jwtIssuer)
    .setAudience(config.jwtAudience)
    .setIssuedAt(now)
    .setNotBefore(now)
    .setExpirationTime(now + config.jwtTtlSeconds);
  return token.sign(await privateKey());
}

export async function issueSessionToken(session: WebsiteSession): Promise<string> {
  const now = nowSeconds();
  return new SignJWT({ admin: session.isAdmin, purpose: "website-session" })
    .setProtectedHeader({ alg: "RS256", typ: "JWT" })
    .setSubject(session.subject)
    .setJti(crypto.randomUUID())
    .setIssuer(SESSION_ISSUER)
    .setAudience(SESSION_AUDIENCE)
    .setIssuedAt(now)
    .setNotBefore(now)
    .setExpirationTime(now + 60 * 60 * 8)
    .sign(await privateKey());
}

export async function verifySessionToken(token: string): Promise<WebsiteSession> {
  const { payload } = await jwtVerify(token, await privateKey(), {
    issuer: SESSION_ISSUER,
    audience: SESSION_AUDIENCE,
  });
  if (payload.purpose !== "website-session" || typeof payload.sub !== "string") {
    throw new Error("Invalid Website session.");
  }
  return { subject: payload.sub, isAdmin: payload.admin === true };
}
