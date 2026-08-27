# OOLITA commerce activation

The public book pages are deliberately staged: Spanish uses EUR and English uses GBP, but neither route is allowed to charge a customer until the complete Stripe and BookVault configuration is present.

## Current staged architecture

`oolita.es` / `oolita.es/en` → Stripe hosted checkout → `/api/stripe-webhook` → BookVault v3 `/Order` → one-copy POD fulfilment.

The physical book is one underlying product in both locales:

- product key: `oolita-book`
- ISBN: `9781066939800`
- BookVault title ID: `3788652`
- Spanish offer: EUR
- English offer: GBP

## Cloudflare secrets / variables required before activation

Never commit these values to GitHub.

- `STRIPE_WEBHOOK_SECRET` — Stripe endpoint signing secret (`whsec_...`).
- `BOOKVAULT_API_KEY` — BookVault API credential generated from BookVault Apps.
- `BOOKVAULT_ENABLED` — must be exactly `true` before the webhook will transmit an order.

Optional overrides:

- `BOOKVAULT_OOLITA_ISBN` — defaults to `9781066939800`.
- `BOOKVAULT_PRODUCTION_LEVEL` — defaults to `Standard`.
- `BOOKVAULT_REQUESTED_SERVICE` — defaults to `CheapestTracked`.
- `BOOKVAULT_ORDER_STATUS` — defaults to `Active` once BookVault is enabled.

The existing D1 binding `OOLITA_SUBSCRIBERS` is reused only as infrastructure; commerce data is kept in its own `commerce_fulfilment` table. The webhook creates that table lazily and uses the Stripe Checkout Session ID as the primary idempotency key.

## Activation gate

Do not populate a `payment_link` in `commerce/catalog.json` until all of the following are true:

1. physical proof approved;
2. retail price decided for EUR and GBP;
3. Stripe product and locale prices created;
4. Stripe Payment Links collect shipping address and phone and carry Checkout Session metadata `oolita_product_key=oolita-book`;
5. shipping countries/rates decided;
6. Stripe webhook endpoint points to `https://oolita.es/api/stripe-webhook` and its signing secret is stored in Cloudflare;
7. BookVault API key is stored in Cloudflare;
8. BookVault account has a saved payment method or sufficient funds;
9. `BOOKVAULT_ENABLED=true` is set;
10. `products.book.fulfilment.status` in `commerce/catalog.json` is changed from `staged` to `ready`.

`apply_commerce.py` fails deployment if a Stripe Payment Link is supplied before BookVault fulfilment is marked ready. This is intentional.

## Stripe event handling

The webhook accepts paid `checkout.session.completed` and `checkout.session.async_payment_succeeded` events only. It verifies the `Stripe-Signature` against the raw request body before parsing the event. Sessions that are unpaid or do not carry `metadata.oolita_product_key=oolita-book` are ignored.

## BookVault order mapping

Paid book sessions are mapped to BookVault v3 `POST /Order` with:

- unique `DocRef` derived from the Stripe Checkout Session;
- Stripe shipping name/address/email/phone;
- `ProductionLevel=Standard` by default;
- `DispatchRequest.RequestedService=CheapestTracked` by default;
- one `OrderLine` for ISBN `9781066939800`, quantity 1.

BookVault API failures return a non-2xx response to Stripe so Stripe can retry. Successful sessions are recorded as fulfilled in D1 to prevent duplicate printing on webhook retries.
