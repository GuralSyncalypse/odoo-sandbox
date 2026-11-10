import "server-only";

import { getConfig } from "@/server/config";
import { issueOdooToken, type WebsiteSession } from "@/server/auth/jwt";

const RETRYABLE_STATUS = new Set([502, 503, 504]);
const SAFE_METHODS = new Set(["GET", "HEAD"]);

export class OdooApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
    public readonly retryable: boolean,
  ) {
    super(message);
  }
}

export function normalizeOdooError(status: number, payload: unknown): OdooApiError {
  const message = typeof payload === "object" && payload && "error" in payload && typeof payload.error === "string"
    ? payload.error
    : "Odoo API request failed.";
  return new OdooApiError(message, status, RETRYABLE_STATUS.has(status));
}

export type OdooRequest = {
  path: string;
  method: string;
  body?: string;
  idempotencyKey?: string;
};

export async function callOdoo(session: WebsiteSession, options: OdooRequest): Promise<Response> {
  const config = getConfig();
  const method = options.method.toUpperCase();
  const headers = new Headers({
    Authorization: `Bearer ${await issueOdooToken(session)}`,
    Accept: "application/json",
  });
  if (options.body) headers.set("Content-Type", "application/json");
  if (!SAFE_METHODS.has(method)) headers.set("Idempotency-Key", options.idempotencyKey ?? crypto.randomUUID());

  const url = new URL(`/api/v1/${options.path.replace(/^\/+/, "")}`, `${config.odooBaseUrl}/`);
  const attempts = SAFE_METHODS.has(method) ? 2 : 1;
  let latest: Response | undefined;
  for (let attempt = 0; attempt < attempts; attempt += 1) {
    try {
      latest = await fetch(url, { method, headers, body: options.body, cache: "no-store" });
      if (!RETRYABLE_STATUS.has(latest.status) || attempt === attempts - 1) return latest;
    } catch (error) {
      if (attempt === attempts - 1) {
        throw new OdooApiError(error instanceof Error ? error.message : "Network error", 503, true);
      }
    }
  }
  return latest!;
}
