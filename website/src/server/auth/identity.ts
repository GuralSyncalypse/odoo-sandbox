import "server-only";

const EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const PHONE = /^\+?[1-9]\d{7,14}$/;

export type IdentityKind = "email" | "phone";

export type NormalizedIdentity = {
  subject: string;
  kind: IdentityKind;
};

export function normalizeIdentity(raw: string): NormalizedIdentity {
  const value = raw.trim();
  if (EMAIL.test(value)) {
    return { subject: value.toLowerCase(), kind: "email" };
  }

  const compactPhone = value.replace(/[\s().-]/g, "");
  if (PHONE.test(compactPhone)) {
    return { subject: compactPhone.startsWith("+") ? compactPhone : `+${compactPhone}`, kind: "phone" };
  }

  throw new Error("Enter a valid email address or international phone number.");
}
