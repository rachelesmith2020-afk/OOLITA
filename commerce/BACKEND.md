# OOLITA commerce backend

This is the operational source of truth for the physical OOLITA book checkout.

## Fixed publishing schedule

- **2027-01-03:** paid pre-order phase begins.
- **2027-01-31:** publication date; checkout phase becomes normal sale.

The dates are enforced server-side by `functions/_lib/commerce-config.js`. Changing labels or links in static HTML cannot open checkout early.

## UK pricing decision

- **Canonical UK RRP:** £20.00.
- **BookVault UK production cost:** £5.27 per copy for ISBN `9781066939800`.
- **Shipping:** charged separately at checkout; it is not included in the £20.00 RRP.
- Printed books are zero-rated for UK VAT under the normal UK treatment of qualifying books.
- The direct website sale uses Stripe; the BookVault portal remains the fulfilment provider for GB orders.

The structured version of this decision is stored in `commerce/catalog.json` under `products.book.pricing_decisions.GB`.

## Architecture

1. The book page asks for delivery country and sends `{country, locale}` to `POST /api/create-checkout`.
2. The Pages Function resolves the delivery route and checks launch phase plus provider/Stripe readiness.
3. It creates a Stripe-hosted Checkout Session restricted to that delivery country.
4. Stripe collects payment and the shipping address.
5. Stripe sends the paid Checkout Session to `POST /api/stripe-webhook`.
6. The webhook verifies the Stripe signature, validates the route against the paid shipping address, claims the order idempotently in D1, and calls the correct POD adapter.

## Fulfilment routing

- `GB` → `bookvault`.
- `ES` → `spanish_pod` (intentionally disabled until a provider is chosen and its API adapter is implemented).

Website language never selects the POD provider.

## Safe staging rule

A route is not purchasable unless all of the following are true:

- the date is 2027-01-03 or later;
- the route exists and its adapter is implemented;
- the Stripe secret key is configured;
- a Stripe book Price ID is configured for the route currency;
- a Stripe Shipping Rate ID is configured for the route;
- the POD provider is enabled and its credentials are configured.

The Spain route therefore cannot accept money accidentally while its provider is unresolved.

## Endpoints

- `GET /api/commerce-status` — non-secret phase/readiness status.
- `POST /api/create-checkout` — create one Stripe Checkout Session for one book.
- `POST /api/stripe-webhook` — paid-order fulfilment.

## D1

The webhook creates `commerce_orders` if needed. `stripe_session_id` is the primary key, preventing duplicate POD orders when Stripe retries a webhook. BookVault also uses a deterministic `DocRef` so a lost API response can be recovered without printing a second copy.

## Remaining launch inputs

These are commercial/provider decisions rather than missing backend structure:

1. Final retail price in EUR for the Spain route.
2. Customer shipping charge / Stripe Shipping Rate for GB and ES.
3. Spanish POD provider, product identifier and API contract.
4. Cloudflare secret values and Stripe webhook signing secret.
5. Stripe Product/Price objects for the decided UK £20.00 price and the later EUR price.

Do not enable a route until a complete end-to-end test order has passed.
