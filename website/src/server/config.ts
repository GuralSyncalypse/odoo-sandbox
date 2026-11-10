import "server-only";

export type TelesalesConfig = {
  websiteUrl: string;
  odooBaseUrl: string;
  jwtIssuer: string;
  jwtAudience: string;
  jwtTtlSeconds: number;
  jwtPrivateKeyPem: string;
  adminSubjects: Set<string>;
  vietQrImageUrl: string;
  bankInstructions: string;
};

function required(name: string, value = process.env[name]): string {
  if (!value?.trim()) {
    throw new Error(`Missing required server configuration: ${name}`);
  }
  return value.trim();
}

function positiveInteger(name: string, value: string | undefined): number {
  const parsed = Number(value);
  if (!Number.isSafeInteger(parsed) || parsed <= 0) {
    throw new Error(`${name} must be a positive integer.`);
  }
  return parsed;
}

export function getConfig(environment = process.env): TelesalesConfig {
  const read = (name: string) => required(name, environment[name]);
  return {
    websiteUrl: read("TELESALES_WEBSITE_URL").replace(/\/$/, ""),
    odooBaseUrl: read("TELESALES_ODOO_BASE_URL").replace(/\/$/, ""),
    jwtIssuer: read("TELESALES_JWT_ISSUER"),
    jwtAudience: read("TELESALES_JWT_AUDIENCE"),
    jwtTtlSeconds: positiveInteger("TELESALES_JWT_TTL_SECONDS", environment.TELESALES_JWT_TTL_SECONDS),
    jwtPrivateKeyPem: read("TELESALES_JWT_PRIVATE_KEY_PEM").replace(/\\n/g, "\n"),
    adminSubjects: new Set(
      (environment.TELESALES_ADMIN_SUBJECTS ?? "")
        .split(",")
        .map((value) => value.trim().toLowerCase())
        .filter(Boolean),
    ),
    vietQrImageUrl: environment.TELESALES_VIETQR_IMAGE_URL?.trim() ?? "",
    bankInstructions: environment.TELESALES_BANK_INSTRUCTIONS?.trim() ?? "",
  };
}
