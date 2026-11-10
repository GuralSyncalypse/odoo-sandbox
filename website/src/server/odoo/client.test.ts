import assert from "node:assert/strict";
import test from "node:test";
import { normalizeOdooError } from "./client";

test("normalizes Odoo error payloads and marks gateway errors retryable", () => {
  const error = normalizeOdooError(503, { error: "Service unavailable" });
  assert.equal(error.message, "Service unavailable");
  assert.equal(error.retryable, true);
});

test("does not mark validation failures retryable", () => {
  const error = normalizeOdooError(400, { error: "Invalid request" });
  assert.equal(error.retryable, false);
});
