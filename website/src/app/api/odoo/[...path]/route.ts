import { NextResponse } from "next/server";
import { getSession } from "@/server/auth/session";
import { callOdoo, normalizeOdooError, OdooApiError } from "@/server/odoo/client";

type Params = { params: Promise<{ path: string[] }> };

async function proxy(request: Request, { params }: Params) {
  const session = await getSession();
  if (!session) return NextResponse.json({ error: "Sign-in is required." }, { status: 401 });

  const path = (await params).path.join("/");
  if (path.startsWith("admin/") && !session.isAdmin) {
    return NextResponse.json({ error: "Admin access is required." }, { status: 403 });
  }
  if (path === "payments/vietqr/callback") {
    return NextResponse.json({ error: "Payment callbacks cannot be proxied." }, { status: 403 });
  }

  try {
    const body = ["GET", "HEAD"].includes(request.method) ? undefined : await request.text();
    const response = await callOdoo(session, {
      path,
      method: request.method,
      body: body || undefined,
      idempotencyKey: request.headers.get("Idempotency-Key") ?? undefined,
    });
    const text = await response.text();
    const payload = text ? JSON.parse(text) as unknown : null;
    if (!response.ok) {
      const error = normalizeOdooError(response.status, payload);
      return NextResponse.json({ error: error.message, retryable: error.retryable }, { status: error.status });
    }
    return NextResponse.json(payload, { status: response.status });
  } catch (error) {
    if (error instanceof OdooApiError) {
      return NextResponse.json({ error: error.message, retryable: error.retryable }, { status: error.status });
    }
    return NextResponse.json({ error: "Unexpected Website gateway error." }, { status: 500 });
  }
}

export const GET = proxy;
export const POST = proxy;
export const PUT = proxy;
export const PATCH = proxy;
export const DELETE = proxy;
