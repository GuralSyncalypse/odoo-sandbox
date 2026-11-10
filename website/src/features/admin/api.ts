import { callWebsiteApi } from "@/lib/api";

export type Account = { id: number; external_user_id: string; active: boolean; is_admin: boolean; wallet: { posted_balance: number; reserved_balance: number; available_balance: number } };
export type DataType = { id: number; name: string; code: string; active: boolean; price_points: number };
export type DataPool = { id: number; name: string; pool_date: string; data_type: string; active: boolean; item_count: number };
export type TopupRequest = { id: number; account: string; order_id: string; points: number; expected_amount: number; state: string; approval_method: "manual" | "callback" | false; approved_by: string | false; approved_at: string | false; callback: { transaction_id: string; amount: number; received_at: string; state: string } | false };
export type RedemptionRequest = { id: number; account: string; data_type: string; quantity: number; point_price: number; reserved_points: number; state: string; approved_by: string | false; approved_at: string | false };
export type RefundRequest = { id: number; account: string; redemption_request_id: number; points: number; reason: string; state: string; approved_by: string | false; approved_at: string | false };

const list = <T,>(path: string) => callWebsiteApi<{ data: T[] }>(path).then((result) => result.data);

export const adminApi = {
  accounts: () => list<Account>("admin/accounts"),
  createAccount: (body: { external_user_id: string; is_admin: boolean }) => callWebsiteApi<Account>("admin/accounts", { method: "POST", body: JSON.stringify(body) }),
  updateAccount: (id: number, body: Partial<Pick<Account, "active" | "is_admin">>) => callWebsiteApi<Account>(`admin/accounts/${id}`, { method: "PATCH", body: JSON.stringify(body) }),
  dataTypes: () => list<DataType>("admin/data-types"),
  createDataType: (body: { name: string; code: string; price_points: number }) => callWebsiteApi("admin/data-types", { method: "POST", body: JSON.stringify(body) }),
  setPrice: (code: string, price_points: number) => callWebsiteApi(`admin/data-types/${code}/price`, { method: "PUT", body: JSON.stringify({ price_points }) }),
  dataPools: () => list<DataPool>("admin/data-pools"),
  createPool: (body: { name: string; pool_date: string; data_type_code: string; items: unknown[] }) => callWebsiteApi("admin/data-pools", { method: "POST", body: JSON.stringify(body) }),
  topups: (state = "") => list<TopupRequest>(`admin/topup-requests${state ? `?state=${state}` : ""}`),
  redemptions: (state = "") => list<RedemptionRequest>(`admin/redemption-requests${state ? `?state=${state}` : ""}`),
  refunds: (state = "") => list<RefundRequest>(`admin/refund-requests${state ? `?state=${state}` : ""}`),
  approve: (kind: "topup" | "redemption" | "refund", id: number) => callWebsiteApi(`admin/${kind}-requests/${id}/approve`, { method: "POST" }),
  reject: (kind: "topup" | "redemption" | "refund", id: number) => callWebsiteApi(`admin/${kind}-requests/${id}/reject`, { method: "POST" }),
};
