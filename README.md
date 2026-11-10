# odoo-sandbox

## Run the Odoo backend

Create `.env` from the existing database example, then start Odoo and Postgres:

```powershell
docker compose up -d --wait db web
```

## Run the Telesales Website

The Website lives in `website/` and is a separate Next.js server. It signs
RS256 JWTs for the API-only Odoo module; it must keep its private key outside
the browser and outside Git.

```powershell
Copy-Item website/.env.example website/.env
Set-Location website
npm install
npm run dev
```

Before signing in, configure `website/.env` with a real RSA private key. Put
the matching public key in Odoo system parameter
`telesales_data_allocation.jwt_public_key`, and set the issuer/audience values
to match `TELESALES_JWT_ISSUER` and `TELESALES_JWT_AUDIENCE`.

To start the production container together with Odoo, set the same
`TELESALES_*` variables in the repository `.env`, then run:

```powershell
docker compose up -d --build website
```

Open `http://localhost:3000`. Phone/email sign-in is basic asserted identity
only; it has no OTP verification. `TELESALES_ADMIN_SUBJECTS` must contain only
separately provisioned Admin identities, and Odoo independently validates its
`is_admin` account flag.

