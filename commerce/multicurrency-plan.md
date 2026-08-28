# OOLITA book checkout and fulfilment plan

## Authoritative launch dates

- Paid pre-orders open: **2027-01-03 00:00 UTC**.
- Publication / normal sales begin: **2027-01-31 00:00 UTC**.
- Runtime enforcement lives in `functions/_lib/commerce-config.js`. The public site must not bypass that server-side gate.

## Product model

OOLITA is one physical bilingual book, ISBN `9781066939800`. Spanish and English website routes are presentation languages, not separate editions or inventory items.

Checkout is created server-side with Stripe Checkout Sessions. Delivery country determines fulfilment and currency; site language determines Checkout language and return page.

| Delivery country | Currency | Fulfilment | State |
| --- | --- | --- | --- |
| GB | GBP | BookVault UK | backend adapter implemented; credentials/price/shipping rate still required |
| ES | EUR | Spanish POD | provider and adapter pending |

No other delivery countries are accepted until an explicit fulfilment route is added.

## Required Cloudflare secrets / variables

Common:

- `STRIPE_SECRET_KEY`
- `STRIPE_WEBHOOK_SECRET`
- `STRIPE_BOOK_PRICE_GBP_ID`
- `STRIPE_BOOK_SHIPPING_GB_GBP_ID`
- `STRIPE_BOOK_PRICE_EUR_ID`
- `STRIPE_BOOK_SHIPPING_ES_EUR_ID`

UK BookVault:

- `BOOKVAULT_ENABLED=true`
- `BOOKVAULT_API_KEY`
- optional `BOOKVAULT_OOLITA_ISBN`, `BOOKVAULT_PRODUCTION_LEVEL`, `BOOKVAULT_REQUESTED_SERVICE`, `BOOKVAULT_ORDER_STATUS`

Spain:

- `SPANISH_POD_ENABLED=true` only after the provider adapter is implemented and tested.

Secrets must never be committed to GitHub.

## Runtime safety

`POST /api/create-checkout` refuses to create a Stripe session before 3 January 2027, for unsupported countries, or when the selected route lacks its Stripe price, shipping rate, provider adapter, or credentials.

`POST /api/stripe-webhook` verifies the Stripe signature, requires a paid OOLITA session, checks that the paid shipping country matches the country/provider encoded at Checkout creation, and uses D1 idempotency before fulfilment. BookVault can only receive GB addresses. The Spain adapter currently fails closed.

`GET /api/commerce-status` exposes only non-secret launch and availability state for the future public button/controller.
