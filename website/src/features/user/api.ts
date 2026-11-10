import { callWebsiteApi } from "@/lib/api";

export type Wallet = { posted_balance: number; reserved_balance: number; available_balance: number };
export type DataType = { code: string; name: string; price_points: number };
export type Redemption = { id: number; data_type: string; quantity: number; reserved_points: number; state: string };
export type Allocation = { id: number; payload: unknown; state: string };
export type Topup = { id: number; order_id: string; points: number; expected_amount: number; state: string; approval_method: string | false };
export type Refund = { id: number; redemption_request_id: number; points: number; reason: string; state: string };
const list = <T,>(path: string) => callWebsiteApi<{ data: T[] }>(path).then((value) => value.data);
export const userApi = {
  wallet: () => callWebsiteApi<Wallet>("wallet"), dataTypes: () => list<DataType>("data-types"),
  topups: () => list<Topup>("topup-requests"), redemptions: () => list<Redemption>("redemption-requests"), refunds: () => list<Refund>("refund-requests"), allocations: () => list<Allocation>("allocations"),
  topup: (points: number, expected_amount: number) => callWebsiteApi("topup-requests", { method: "POST", body: JSON.stringify({ order_id: `TOPUP-${crypto.randomUUID()}`, points, expected_amount }) }),
  redeem: (data_type_code: string, quantity: number) => callWebsiteApi("redemption-requests", { method: "POST", body: JSON.stringify({ data_type_code, quantity }) }),
  refund: (redemption_request_id: number, points: number, reason: string) => callWebsiteApi("refund-requests", { method: "POST", body: JSON.stringify({ redemption_request_id, points, reason }) }),
};
