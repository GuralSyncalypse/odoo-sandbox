import assert from "node:assert/strict";
import test from "node:test";
import { normalizeIdentity } from "./identity";

test("normalizes an email identity", () => {
  assert.deepEqual(normalizeIdentity("  SALES@Example.COM "), { subject: "sales@example.com", kind: "email" });
});

test("normalizes formatted international phone numbers", () => {
  assert.deepEqual(normalizeIdentity("+84 (90) 123-4567"), { subject: "+84901234567", kind: "phone" });
});

test("rejects malformed identities", () => {
  assert.throws(() => normalizeIdentity("not an identity"));
});
