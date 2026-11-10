# Telesales Portal API System

`telesales_data_allocation` is an API-only Odoo backend. Website users do not log
in to Odoo and every endpoint uses a Website-issued JWT.

## Authentication

- The Website signs JWTs using **RS256**; Odoo stores only the PEM public key in
  `telesales_data_allocation.jwt_public_key`.
- Tokens must contain `sub`, `jti`, `exp`, `nbf`, `iss`, and `aud`.
- Odoo checks `iss` and `aud` against `jwt_issuer` and `jwt_audience`, rejects
  revoked JTIs, and maps `sub` to `telesales.api.account.external_user_id`.
- An Admin endpoint requires both an active account with `is_admin=true` and
  the JWT claim `admin: true`.
- The Website identifies a user by a basic-valid phone number or email address
  and normalises it before using it as JWT `sub`. This scope does not verify
  ownership through OTP; therefore it must never grant an Admin claim based on
  the identifier alone.

### Website configuration

The Next.js Website source is at `website/`. Its server-only configuration is
read from `website/.env` (start with `website/.env.example`):

- `TELESALES_ODOO_BASE_URL`, `TELESALES_JWT_ISSUER`, and
  `TELESALES_JWT_AUDIENCE` must match the reachable Odoo server and its JWT
  system parameters.
- `TELESALES_JWT_PRIVATE_KEY_PEM` remains only on the Website server. Copy the
  matching PEM public key into Odoo parameter
  `telesales_data_allocation.jwt_public_key`.
- `TELESALES_ADMIN_SUBJECTS` is a controlled, comma-separated mapping that may
  add an Admin JWT claim. Odoo still verifies `is_admin` itself.

Browser code calls the Website gateway under `/api/odoo/*`; the gateway issues
the Bearer token server-side and adds an `Idempotency-Key` for mutations.

## Wallet and allocation rules

- Wallet balances are derived from immutable `telesales.wallet.ledger` entries.
- A redemption in `pending` state reserves its point price. It becomes a debit
  only after Admin approval.
- Approved redemptions select available data FIFO by `pool_date`; database row
  locks prevent two approvals from assigning the same item.
- `Idempotency-Key` is mandatory for every mutation initiated by a Website user.

## VietQR top-up flow

1. The Website creates a pending top-up request with an `order_id`, expected VND
   amount, and number of points.
2. VietQR POSTs a callback to `/api/v1/payments/vietqr/callback`.
3. An Admin reviews the bank statement manually and approves the matching
   top-up. Only then does Odoo post a positive top-up ledger entry.

The VietQR callback endpoint remains available as optional supporting evidence:
when a valid callback matches the order and amount, approval is recorded as
`callback`; otherwise it is recorded as `manual`.

VietQR settings are stored in `ir.config_parameter` and must include the secret
key, Merchant ID, API credentials, and the selected UAT/production endpoint.

## API surface

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/v1/wallet` | Read the caller's balances. |
| `GET` | `/api/v1/data-types` | List active data types and point prices. |
| `POST` | `/api/v1/topup-requests` | Create a pending top-up request. |
| `POST` | `/api/v1/redemption-requests` | Reserve points for a pending redemption. |
| `GET` | `/api/v1/redemption-requests/:id` | Read the caller's request. |
| `GET` | `/api/v1/allocations` | Read only the caller's assigned data. |
| `POST` | `/api/v1/refund-requests` | Request an Admin-approved refund. |
| `GET` | `/api/v1/{topup,redemption,refund}-requests` | Read only the caller's own request history. |
| `POST` | `/api/v1/payments/vietqr/callback` | Receive an unauthenticated, signed VietQR callback. |
| `POST` | `/api/v1/admin/...` | External Admin-only account, pool, approval, and pricing actions. |

## Admin portal API

All endpoints below require both the Website Admin claim and an active Odoo
`telesales.api.account` with `is_admin=true`.

| Method | Path | Purpose |
| --- | --- | --- |
| `GET`, `POST` | `/api/v1/admin/accounts` | List or create external accounts. |
| `PATCH` | `/api/v1/admin/accounts/:id` | Activate/deactivate an account or change its Admin flag. |
| `GET`, `POST` | `/api/v1/admin/data-types` | List or create redeemable data types. |
| `PUT` | `/api/v1/admin/data-types/:code/price` | Set point price. |
| `GET`, `POST` | `/api/v1/admin/data-pools` | List or create dated data pools. |
| `GET` | `/api/v1/admin/{topup,redemption,refund}-requests?state=pending` | Read reconciliation/audit queues. |
| `POST` | `/api/v1/admin/{topup,redemption,refund}-requests/:id/approve` | Approve a pending request. |
| `POST` | `/api/v1/admin/{topup,redemption,refund}-requests/:id/reject` | Reject a pending request. |

Request-list responses contain the requester, state, amounts/points, and
approval audit fields. Top-ups additionally include optional verified callback
evidence and `approval_method`; it is `manual` without matching evidence or
`callback` when evidence is verified. Neither path auto-credits a wallet.
