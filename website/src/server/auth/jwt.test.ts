import assert from "node:assert/strict";
import test from "node:test";
import { exportPKCS8, exportSPKI, generateKeyPair, importSPKI, jwtVerify } from "jose";

test("issues an RS256 Odoo JWT with required claims and an Admin claim", async () => {
  const keys = await generateKeyPair("RS256", { extractable: true });
  process.env.TELESALES_WEBSITE_URL = "http://localhost:3000";
  process.env.TELESALES_ODOO_BASE_URL = "http://localhost:8069";
  process.env.TELESALES_JWT_ISSUER = "website";
  process.env.TELESALES_JWT_AUDIENCE = "odoo";
  process.env.TELESALES_JWT_TTL_SECONDS = "900";
  process.env.TELESALES_JWT_PRIVATE_KEY_PEM = await exportPKCS8(keys.privateKey);

  const { issueOdooToken } = await import("./jwt");
  const token = await issueOdooToken({ subject: "admin@example.com", isAdmin: true });
  const publicKey = await importSPKI(await exportSPKI(keys.publicKey), "RS256");
  const { payload, protectedHeader } = await jwtVerify(token, publicKey, { issuer: "website", audience: "odoo" });

  assert.equal(protectedHeader.alg, "RS256");
  assert.equal(payload.sub, "admin@example.com");
  assert.equal(payload.admin, true);
  assert.equal(typeof payload.jti, "string");
  assert.equal(typeof payload.exp, "number");
  assert.equal(typeof payload.nbf, "number");
});
