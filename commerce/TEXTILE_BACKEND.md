# OOLITA UK textile backend

## Purpose

Stage the UK textile checkout around The Inner Sanctum Group without requiring a supplier API. Stripe remains the payment and address collection layer; fulfilment is intentionally manual until the workflow has been proven in practice.

## Garment

OOLITA has one first textile garment:

- `oversized` — Stanley/Stella Blaster 2.0 STTU959, white, supplier path `/products/sx795`, 200 gsm organic cotton, oversized unisex fit. The current production benchmark is £23.00 from current public garment + print pricing. The existing sample checkout was prepared at £22.00 before shipping, so this figure must be rechecked before final retail pricing.
- It carries the OOLITA front artwork and the deliberately low back artwork. The supplier order remains the source of truth for physical placement.

No alternative garment or second cut is part of the first textile edition.

## Storefront model

There are exactly two website storefront entry points for this one garment:

- `es` — `https://oolita.es/ediciones/camiseta/`
- `en` — `https://oolita.es/en/editions/t-shirt/`

They are language storefronts, not separate Stripe products or garment variants. The runtime rejects any locale other than `es` or `en` and any style other than `oversized`.

Both storefronts reuse the same persistent Stripe Blaster 2.0 Price ID. The checkout function must never send inline Stripe `price_data` or `product_data`, because that creates unnecessary Stripe catalogue objects and was the source of the earlier four-entry setup. CI fails if inline textile product/price creation or separate locale prices are reintroduced.

## Backend flow

1. `POST /api/textile-checkout` receives `style`, `size`, and `locale`; the only accepted style is `oversized` and the only accepted storefronts are `es` and `en`.
2. Before release, `dry_run: true` validates the complete OOLITA garment/size/provider/storefront mapping without creating a Stripe session.
3. Live checkout is blocked until 11 April 2027 and until the UK textile runtime variables are explicitly configured.
4. Before creating a Checkout Session, the backend retrieves the one configured persistent Stripe Blaster Price and verifies that it is active, one-time, GBP, and exactly matches the configured OOLITA retail amount.
5. Stripe Checkout reuses that one persistent Price for both languages, collects a GB shipping address and phone number, and stores the OOLITA storefront, garment, size, SKU and Inner Sanctum product reference in Checkout metadata.
6. Checkout cancellation returns to the exact Spanish or English T-shirt page. Successful payment redirects through `GET /api/textile-confirm`.
7. The confirm endpoint retrieves the Checkout Session directly from Stripe and trusts the verified Stripe metadata, not the query-string locale, to choose the return storefront. It verifies the session is an OOLITA textile payment and records the order in D1 table `textile_orders` with state `manual_pending`.
8. No call is made to Inner Sanctum. OOLITA staff place the corresponding supplier order manually using the recorded garment, size and customer delivery address.

## Required Cloudflare runtime variables for live UK sales

- `TEXTILE_UK_ENABLED=true`
- `TEXTILE_OVERSIZED_PRICE_GBP_MINOR` — customer price in pence.
- `TEXTILE_BLASTER_PRICE_GBP_ID` — the single persistent Stripe one-time GBP Price reused by both Spanish and English T-shirt storefronts.
- `TEXTILE_UK_SHIPPING_GBP_MINOR` — fixed customer UK delivery charge in pence.
- Existing `STRIPE_SECRET_KEY`.
- Existing `OOLITA_SUBSCRIBERS` D1 binding.

The single Stripe Price ID must point to the intended Blaster 2.0 product and have the same GBP amount as `TEXTILE_OVERSIZED_PRICE_GBP_MINOR`. The checkout verifies amount, currency and activity before taking payment.

The provisional commercial working figure in code is £34. It is returned only by dry-run diagnostics and is not accepted as a live price unless the corresponding Cloudflare runtime value is deliberately configured.

## Deployment guard

After every successful production deployment, CI rechecks the live site fail-closed: sitemap/SEO and internal targets, a genuine HTTP 404 with no redirect, the single Blaster public state in Spanish and English, and the absence of internal legacy `?follow=3d` links.

The same guard checks the textile commerce source of truth and fails unless:

- storefront keys are exactly `es` and `en`;
- the only textile variant is `oversized`;
- both storefronts share the one `TEXTILE_BLASTER_PRICE_GBP_ID` runtime price;
- those storefronts point to the exact Spanish and English T-shirt pages;
- checkout uses a persistent Stripe `price` reference;
- no separate locale-specific Stripe price configuration remains; and
- no inline `price_data` or `product_data` remains in the textile checkout function.

## Known limitation of the no-supplier-API launch path

The first version records the manual order on Stripe's success redirect rather than adding textile handling to the existing book webhook. Stripe itself still retains every successful payment and delivery address, so a missed browser redirect is recoverable from Stripe, but this is not the final belt-and-braces architecture. Before public launch either:

- add textile handling to the existing signed Stripe webhook, or
- provide an authenticated reconciliation job that imports any paid textile Checkout Sessions not yet present in `textile_orders`.

This staged version exists to prove that the customer checkout and manual Inner Sanctum workflow are workable before investing in supplier-specific automation.
