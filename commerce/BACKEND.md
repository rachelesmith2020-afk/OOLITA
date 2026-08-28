# OOLITA commerce backend

This is the operational source of truth for the physical OOLITA book checkout.

## Fixed publishing schedule

- **2027-01-03:** paid pre-order phase begins.
- **2027-01-31:** publication date; checkout phase becomes normal sale.

The dates are enforced server-side by `functions/_lib/commerce-config.js`. Changing labels or links in static HTML cannot open checkout early.

## UK pricing decision

- **Canonical UK RRP:** £17.00.
- **BookVault UK production cost:** £5.27 per copy for ISBN `9781066939800`.
- **Shipping:** charged separately at checkout; it is not included in the £17.00 RRP.
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

## Public checkout control

The book pages ship with an inert, hidden purchase control. The browser asks `GET /api/commerce-status` for the authoritative server phase and configured delivery routes before making that control usable.

- Before **2027-01-03**, the purchase control remains hidden and the existing email-notification CTA remains public.
- From **2027-01-03**, when at least one delivery route is fully configured, the label becomes **Reservar el libro / Pre-order the book**.
- From **2027-01-31**, it becomes **Comprar el libro / Buy the book**.
- The customer chooses **delivery country** before Stripe Checkout is created. Website language never determines fulfilment.
- A supported but unconfigured country is shown as unavailable rather than routed to the wrong POD.
- Failure to read commerce status fails closed: no purchase control is enabled.

The runtime wiring is installed by `scripts/reposition_book_checkout_v1.py`; the server remains authoritative.

## Fulfilment routing

- `GB` → `bookvault`.
- `ES` → `spanish_pod` (intentionally disabled until a provider is chosen and its API adapter is implemented).

Website language never selects the POD provider.

## Shipping rule

The intended production behaviour is **destination-based provider shipping**, not an invented flat postage figure. BookVault shipping varies by destination/postcode and service, so the GB route must not be enabled until the exact BookVault shipping quote/API contract has been confirmed and integrated or an explicitly approved equivalent charging method has been chosen.

The current `STRIPE_BOOK_SHIPPING_GB_GBP_ID` / `STRIPE_BOOK_SHIPPING_ES_EUR_ID` checks are therefore staging safeguards, not a decision to charge a universal flat rate. Do not use a guessed Stripe Shipping Rate to make a route ready.

## Safe staging rule

A route is not purchasable unless all of the following are true:

- the date is 2027-01-03 or later;
- the route exists and its adapter is implemented;
- the Stripe secret key is configured;
- a Stripe book Price ID is configured for the route currency;
- an approved shipping implementation is configured for the route;
- the POD provider is enabled and its credentials are configured.

The Spain route therefore cannot accept money accidentally while its provider is unresolved.

## Endpoints

- `GET /api/commerce-status` — non-secret phase/readiness status, including supported/configured/checkout delivery countries.
- `POST /api/create-checkout` — create one Stripe Checkout Session for one book.
- `POST /api/stripe-webhook` — paid-order fulfilment.

## D1

The webhook creates `commerce_orders` if needed. `stripe_session_id` is the primary key, preventing duplicate POD orders when Stripe retries a webhook. BookVault also uses a deterministic `DocRef` so a lost API response can be recovered without printing a second copy.

## Remaining launch inputs

These are commercial/provider or secure-configuration inputs rather than missing core backend structure:

1. Stripe Product and GBP Price object for the decided UK **£17.00** price.
2. Exact BookVault destination-based shipping implementation for GB.
3. BookVault API credentials and Cloudflare production secrets.
4. Stripe live webhook registration and signing secret.
5. Spanish POD provider, product identifier, API contract, EUR retail price and shipping implementation.
6. Complete end-to-end test orders, including duplicate webhooks and fulfilment failures.

Do not enable a route until a complete end-to-end test order has passed.
