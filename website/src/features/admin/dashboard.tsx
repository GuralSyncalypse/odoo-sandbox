"use client";

import { useCallback, useEffect, useState } from "react";
import { adminApi, type Account, type DataPool, type DataType, type RefundRequest, type RedemptionRequest, type TopupRequest } from "./api";
import { WebsiteApiError } from "@/lib/api";

type Tab = "accounts" | "catalog" | "pools" | "requests";
type RequestKind = "topup" | "redemption" | "refund";

function Message({ error }: { error: unknown }) {
  if (!error) return null;
  const apiError = error instanceof WebsiteApiError ? error : null;
  return <p className="error" role="alert">{error instanceof Error ? error.message : "Request failed."}{apiError?.retryable ? " You can retry." : ""}</p>;
}

export function AdminDashboard() {
  const [tab, setTab] = useState<Tab>("accounts");
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [types, setTypes] = useState<DataType[]>([]);
  const [pools, setPools] = useState<DataPool[]>([]);
  const [requests, setRequests] = useState<{ topup: TopupRequest[]; redemption: RedemptionRequest[]; refund: RefundRequest[] }>({ topup: [], redemption: [], refund: [] });
  const [loading, setLoading] = useState(true); const [error, setError] = useState<unknown>(null);

  const refresh = useCallback(async () => {
    setLoading(true); setError(null);
    try {
      const [nextAccounts, nextTypes, nextPools, topup, redemption, refund] = await Promise.all([
        adminApi.accounts(), adminApi.dataTypes(), adminApi.dataPools(), adminApi.topups(), adminApi.redemptions(), adminApi.refunds(),
      ]);
      setAccounts(nextAccounts); setTypes(nextTypes); setPools(nextPools); setRequests({ topup, redemption, refund });
    } catch (caught) { setError(caught); } finally { setLoading(false); }
  }, []);
  useEffect(() => { void refresh(); }, [refresh]);

  async function run(action: () => Promise<unknown>) { try { setError(null); await action(); await refresh(); } catch (caught) { setError(caught); } }
  return <section className="stack">
    <nav className="tabs">{(["accounts", "catalog", "pools", "requests"] as Tab[]).map((item) => <button key={item} className={tab === item ? "selected" : ""} onClick={() => setTab(item)}>{item}</button>)}<button onClick={() => void refresh()}>Refresh</button></nav>
    {loading ? <p>Loading Admin data…</p> : <><Message error={error} />
      {tab === "accounts" && <Accounts accounts={accounts} run={run} />}
      {tab === "catalog" && <Catalog types={types} run={run} />}
      {tab === "pools" && <Pools pools={pools} types={types} run={run} />}
      {tab === "requests" && <Requests requests={requests} run={run} />}
    </>}
  </section>;
}

function Accounts({ accounts, run }: { accounts: Account[]; run: (action: () => Promise<unknown>) => Promise<void> }) {
  const [identifier, setIdentifier] = useState(""); const [isAdmin, setIsAdmin] = useState(false);
  return <div className="stack"><form className="card inline" onSubmit={(event) => { event.preventDefault(); void run(() => adminApi.createAccount({ external_user_id: identifier, is_admin: isAdmin })); setIdentifier(""); }}><input placeholder="Phone or email" value={identifier} onChange={(event) => setIdentifier(event.target.value)} required /><label><input type="checkbox" checked={isAdmin} onChange={(event) => setIsAdmin(event.target.checked)} /> Admin</label><button>Create account</button></form><Table headers={["Identity", "Role", "Status", "Wallet", "Actions"]}>{accounts.map((account) => <tr key={account.id}><td>{account.external_user_id}</td><td>{account.is_admin ? "Admin" : "User"}</td><td>{account.active ? "Active" : "Inactive"}</td><td>{account.wallet.available_balance}</td><td><button onClick={() => void run(() => adminApi.updateAccount(account.id, { active: !account.active }))}>{account.active ? "Disable" : "Enable"}</button> <button onClick={() => void run(() => adminApi.updateAccount(account.id, { is_admin: !account.is_admin }))}>{account.is_admin ? "Remove Admin" : "Make Admin"}</button></td></tr>)}</Table></div>;
}

function Catalog({ types, run }: { types: DataType[]; run: (action: () => Promise<unknown>) => Promise<void> }) {
  const [name, setName] = useState(""); const [code, setCode] = useState(""); const [price, setPrice] = useState("1");
  return <div className="stack"><form className="card inline" onSubmit={(event) => { event.preventDefault(); void run(() => adminApi.createDataType({ name, code, price_points: Number(price) })); }}><input placeholder="Name" value={name} onChange={(event) => setName(event.target.value)} required /><input placeholder="Code" value={code} onChange={(event) => setCode(event.target.value)} required /><input type="number" min="1" value={price} onChange={(event) => setPrice(event.target.value)} required /><button>Create data type</button></form><Table headers={["Name", "Code", "Price", "Update"]}>{types.map((type) => <DataTypeRow key={type.id} dataType={type} run={run} />)}</Table></div>;
}

function DataTypeRow({ dataType, run }: { dataType: DataType; run: (action: () => Promise<unknown>) => Promise<void> }) { const [price, setPrice] = useState(String(dataType.price_points)); return <tr><td>{dataType.name}</td><td>{dataType.code}</td><td>{dataType.price_points}</td><td><input type="number" min="1" value={price} onChange={(event) => setPrice(event.target.value)} /><button onClick={() => void run(() => adminApi.setPrice(dataType.code, Number(price)))}>Save</button></td></tr>; }

function Pools({ pools, types, run }: { pools: DataPool[]; types: DataType[]; run: (action: () => Promise<unknown>) => Promise<void> }) {
  const [name, setName] = useState(""); const [poolDate, setPoolDate] = useState(""); const [code, setCode] = useState(""); const [items, setItems] = useState("[]");
  return <div className="stack"><form className="card stack" onSubmit={(event) => { event.preventDefault(); try { const parsed = JSON.parse(items); if (!Array.isArray(parsed)) throw new Error(); void run(() => adminApi.createPool({ name, pool_date: poolDate, data_type_code: code, items: parsed })); } catch { alert("Items must be a JSON array."); } }}><input placeholder="Pool name" value={name} onChange={(event) => setName(event.target.value)} required /><input type="date" value={poolDate} onChange={(event) => setPoolDate(event.target.value)} required /><select value={code} onChange={(event) => setCode(event.target.value)} required><option value="">Select data type</option>{types.map((type) => <option key={type.id} value={type.code}>{type.name}</option>)}</select><textarea value={items} onChange={(event) => setItems(event.target.value)} aria-label="Data item JSON array" /><button>Create daily pool</button></form><Table headers={["Name", "Date", "Type", "Items", "Status"]}>{pools.map((pool) => <tr key={pool.id}><td>{pool.name}</td><td>{pool.pool_date}</td><td>{pool.data_type}</td><td>{pool.item_count}</td><td>{pool.active ? "Active" : "Inactive"}</td></tr>)}</Table></div>;
}

function Requests({ requests, run }: { requests: { topup: TopupRequest[]; redemption: RedemptionRequest[]; refund: RefundRequest[] }; run: (action: () => Promise<unknown>) => Promise<void> }) {
  return <div className="stack"><RequestTable kind="topup" rows={requests.topup} run={run} /><RequestTable kind="redemption" rows={requests.redemption} run={run} /><RequestTable kind="refund" rows={requests.refund} run={run} /></div>;
}

function RequestTable({ kind, rows, run }: { kind: RequestKind; rows: Array<TopupRequest | RedemptionRequest | RefundRequest>; run: (action: () => Promise<unknown>) => Promise<void> }) {
  return <section className="card"><h2>{kind} requests</h2><Table headers={["Account", "Details", "State", "Audit", "Action"]}>{rows.map((row) => <tr key={row.id}><td>{row.account}</td><td>{kind === "topup" ? `${(row as TopupRequest).order_id}: ${(row as TopupRequest).points} pts / ${(row as TopupRequest).expected_amount} VND` : kind === "redemption" ? `${(row as RedemptionRequest).data_type} × ${(row as RedemptionRequest).quantity}` : `${(row as RefundRequest).points} pts: ${(row as RefundRequest).reason}`}</td><td>{row.state}</td><td>{kind === "topup" && (row as TopupRequest).approval_method ? `${(row as TopupRequest).approval_method} · ` : ""}{row.approved_by || "—"} {row.approved_at || ""}</td><td>{row.state === "pending" && <><button onClick={() => { if (confirm(`Approve ${kind} request #${row.id}?`)) void run(() => adminApi.approve(kind, row.id)); }}>Approve</button> <button onClick={() => { if (confirm(`Reject ${kind} request #${row.id}?`)) void run(() => adminApi.reject(kind, row.id)); }}>Reject</button></>}</td></tr>)}</Table></section>;
}

function Table({ headers, children }: { headers: string[]; children: React.ReactNode }) { return <div className="table-wrap"><table><thead><tr>{headers.map((header) => <th key={header}>{header}</th>)}</tr></thead><tbody>{children}</tbody></table></div>; }
