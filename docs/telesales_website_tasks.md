# Telesales Website Tasks

This document records the delivery order for the Website that fronts the
API-only `telesales_data_allocation` Odoo module. Users and external Admins
do not log in to Odoo directly.

## Identity and authentication baseline

- A person identifies themself with either a phone number or an email address.
- The Website performs basic format validation and normalises the identifier
  before using it as the JWT `sub` and before resolving its external Odoo
  account.
- No OTP or other ownership verification is in this scope. Therefore this is
  an asserted identity, not proof that the person owns the phone number or
  email address.
- The Website signs Odoo access tokens on the server using RS256. The private
  key must never be sent to a browser; Odoo receives only the matching public
  key and validates `iss`, `aud`, `sub`, `jti`, `nbf`, and `exp`.
- A basic identifier must never grant the `admin: true` claim. External Admin
  status needs a separately provisioned and controlled account mapping.

## Delivery tasks

| Order | Task | Outcome | Dependency |
| --- | --- | --- | --- |
| 1 | [OS-99S7D5](../.knowns/tasks/OS-99S7D5.md) | Set up the shared Website foundation, server-side RS256 JWT issuer, configuration, session boundary, and Odoo API client. | None |
| 2 | [OS-HC8S4N](../.knowns/tasks/OS-HC8S4N.md) | Build the external Admin portal to manage accounts, data types/prices, dated pools, and manual approvals. | OS-99S7D5 |
| 3 | [OS-8FDBW1](../.knowns/tasks/OS-8FDBW1.md) | Build the end-user portal for wallet status, top-up, redemption, allocation, and refund requests. | OS-99S7D5 |

The Admin and end-user portal tasks can proceed in parallel once the shared
foundation is complete.

The User portal at `/portal` displays only the signed-in account's wallet,
request history and assigned data, and creates pending top-up/redemption/refund
requests through the server-side gateway.

The Admin portal is implemented at `/admin`. It uses the server-side Odoo
gateway and offers account/catalog/pool administration plus request queues for
manual approval or rejection. The end-user portal remains a separate task.

## Payment rule

Top-ups create a unique order and remain pending. An external Admin manually
reviews the bank statement and approves or rejects the request. A VietQR
callback can be retained as supporting evidence, but it cannot automatically
credit a wallet. This follows
`@decision/20261110-1058-require-manual-approval-before-crediting-telesales-wallets`.
