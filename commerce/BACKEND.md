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

## Live Stripe objects

The production Stripe account contains the canonical OOLITA book objects:

- Product: `prod_V9i8v2t5IfLjdS`
- GBP Price: `price_1U9Oi8Hcycje25JhAOkHZr9L`
- Amount: **£17.00** one-time
- Webhook endpoint: `we_1U9OkHHcycje25JhshLBbJdF`
- Webhook URL: `https://oolita.es/api/stripe-webhook`
- Enabled webhook events: `checkout.session.completed`, `checkout.session.async_payment_succeeded`

The webhook signing secret is a Cloudflare secret and must never be committed to Git.

## Architecture

1. The book page asks for delivery country. For GB it also requires the delivery postcode.
2. `POST /api/create-checkout` resolves the delivery route and checks the launch phase plus provider/Stripe readiness.
3. For GB, the Pages Function calls BookVault `POST /Dispatch` with the OOLITA ISBN, postcode, GBP currency and `CheapestTracked` service level.
4. The backend selects the cheapest usable tracked BookVault service, records its `ServID`, and uses its `DelTotal` as an inline Stripe Checkout shipping charge.
5. Stripe Checkout is restricted to the selected delivery country and collects the full shipping address and payment.
6. Stripe sends the paid Checkout Session to `POST /api/stripe-webhook`.
7. The webhook verifies the Stripe signature, confirms the paid postcode and shipping amount match the original BookVault quote, claims the order idempotently in D1, and calls the correct POD adapter.
8. For GB, the BookVault order requests the exact quoted service ID using `RequestedService: Specified`.

## Public checkout control

The book pages ship with an inert, hidden purchase control. The browser asks `GET /api/commerce-status` for the authoritative server phase and configured delivery routes before making that control usable.

- Before **2027-01-03**, the purchase control remains hidden and the existing email-notification CTA remains public.
- From **2027-01-03**, when at least one delivery route is fully configured, the label becomes **Reservar el libro / Pre-order the book**.
- From **2027-01-31**, it becomes **Comprar el libro / Buy the book**.
- The customer chooses **delivery country** before Stripe Checkout is created. Website language never determines fulfilment.
- GB checkout asks for a postcode before Stripe opens because BookVault shipping is destination-dependent.
- A supported but unconfigured country is shown as unavailable rather than routed to the wrong POD.
- Failure to read commerce status fails closed: no purchase control is enabled.

The runtime wiring is installed by `scripts/reposition_book_checkout_v1.py`; the server remains authoritative.

## Fulfilment routing

- `GB` → `bookvault`.
- `ES` → `spanish_pod` (intentionally disabled until a provider is chosen and its API adapter is implemented).

Website language never selects the POD provider.

## Shipping rule

GB shipping is **not a flat Stripe Shipping Rate**. It is quoted from BookVault at checkout time using the customer's UK postcode.

The BookVault request uses:

- `OrderLines`: OOLITA ISBN, quantity 1
- `CountryCode`: `GB`
- `ServiceLevel`: `CheapestTracked`
- `PartnerID`: `0`
- `Currency`: `GBP`
- `AreaCode`: customer postcode
- `ShipmentDate`: release date during pre-order; current date during normal sale

The selected tracked service's `DelTotal` is converted to pence and passed to Stripe as inline `shipping_rate_data`. Stripe metadata carries the quoted postcode, BookVault service ID and quoted shipping amount. The paid webhook refuses fulfilment if the address postcode or paid shipping amount differs from that quote.

## Safe staging rule

A route is not purchasable unless all of the following are true:

- the date is 2027-01-03 or later;
- the route exists and its adapter is implemented;
- the Stripe secret key is configured;
- a Stripe book Price ID is configured for the route currency;
- the route uses an approved provider-quote shipping implementation;
- the POD provider is enabled and its credentials are configured.

The Spain route therefore cannot accept money accidentally while its provider is unresolved.

## Endpoints

- `GET /api/commerce-status` — non-secret phase/readiness status, including supported/configured/checkout delivery countries.
- `POST /api/create-checkout` — quote provider shipping and create one Stripe Checkout Session for one book.
- `POST /api/stripe-webhook` — verify paid order and fulfil it once.

## D1

The webhook creates `commerce_orders` if needed. `stripe_session_id` is the primary key, preventing duplicate POD orders when Stripe retries a webhook. BookVault also uses a deterministic `DocRef` so a lost API response can be recovered without printing a second copy.

## Remaining launch inputs

The UK core architecture and live Stripe catalog objects are now prepared. Remaining inputs are secure configuration, provider completion and testing:

1. Cloudflare production secrets/variables for the Stripe secret key, Stripe webhook secret and GBP Price ID.
2. BookVault API key plus `BOOKVAULT_ENABLED=true` in Cloudflare.
3. A live BookVault dispatch-quote test against OOLITA and a controlled end-to-end Stripe test before enabling GB.
4. Spanish POD provider, product identifier, API contract, EUR retail price and shipping implementation.
5. Complete end-to-end test orders, including postcode mismatch, duplicate webhooks and fulfilment failures.

Do not enable a route until a complete end-to-end test order has passed.
