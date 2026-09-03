# OOLITA UK textile backend

## Purpose

Stage the UK textile checkout around The Inner Sanctum Group without requiring a supplier API. Stripe remains the payment and address collection layer; fulfilment is intentionally manual until the workflow has been proven in practice.

## Garment

OOLITA has one first textile garment:

- `oversized` — Stanley/Stella Blaster 2.0 STTU959, white, supplier path `/products/sx795`, 200 gsm organic cotton, oversized unisex fit. The current production benchmark is £23.00 from current public garment + print pricing. The existing sample checkout was prepared at £22.00 before shipping, so this figure must be rechecked before final retail pricing.
- It carries the OOLITA front artwork and the deliberately low back artwork. The supplier order remains the source of truth for physical placement.

No alternative garment or second cut is part of the first textile edition.

## Backend flow

1. `POST /api/textile-checkout` receives `style`, `size`, and `locale`; the only accepted style is `oversized`.
2. Before release, `dry_run: true` validates the complete OOLITA garment/size/provider mapping without creating a Stripe session.
3. Live checkout is blocked until 11 April 2027 and until the UK textile runtime variables are explicitly configured.
4. Stripe Checkout collects a GB shipping address and phone number and stores the OOLITA garment, size, SKU and Inner Sanctum product reference in Checkout metadata.
5. After successful card payment Stripe redirects through `GET /api/textile-confirm`.
6. The confirm endpoint retrieves the Checkout Session directly from Stripe, verifies it is paid and internally consistent, then records the order in D1 table `textile_orders` with state `manual_pending`.
7. No call is made to Inner Sanctum. OOLITA staff place the corresponding supplier order manually using the recorded garment, size and customer delivery address.

## Required Cloudflare runtime variables for live UK sales

- `TEXTILE_UK_ENABLED=true`
- `TEXTILE_OVERSIZED_PRICE_GBP_MINOR` — customer price in pence.
- `TEXTILE_UK_SHIPPING_GBP_MINOR` — fixed customer UK delivery charge in pence.
- Existing `STRIPE_SECRET_KEY`.
- Existing `OOLITA_SUBSCRIBERS` D1 binding.

The provisional commercial working figure in code is £34. It is returned only by dry-run diagnostics and is not accepted as a live price unless the corresponding Cloudflare runtime value is deliberately configured.

## Known limitation of the no-supplier-API launch path

The first version records the manual order on Stripe's success redirect rather than adding textile handling to the existing book webhook. Stripe itself still retains every successful payment and delivery address, so a missed browser redirect is recoverable from Stripe, but this is not the final belt-and-braces architecture. Before public launch either:

- add textile handling to the existing signed Stripe webhook, or
- provide an authenticated reconciliation job that imports any paid textile Checkout Sessions not yet present in `textile_orders`.

This staged version exists to prove that the customer checkout and manual Inner Sanctum workflow are workable before investing in supplier-specific automation.
