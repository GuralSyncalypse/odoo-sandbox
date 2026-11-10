"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export function SignInForm() {
  const router = useRouter();
  const [identifier, setIdentifier] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true); setError("");
    const response = await fetch("/api/auth/sign-in", {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ identifier }),
    });
    const payload = await response.json() as { error?: string; isAdmin?: boolean };
    setBusy(false);
    if (!response.ok) return setError(payload.error ?? "Unable to sign in.");
    router.push(payload.isAdmin ? "/admin" : "/portal"); router.refresh();
  }

  return <form onSubmit={submit} className="card stack">
    <label>Phone or email<input value={identifier} onChange={(event) => setIdentifier(event.target.value)} required /></label>
    {error && <p role="alert" className="error">{error}</p>}
    <button disabled={busy}>{busy ? "Signing in…" : "Sign in"}</button>
  </form>;
}
