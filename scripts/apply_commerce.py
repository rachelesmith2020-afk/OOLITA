#!/usr/bin/env python3
"""Apply OOLITA's locale-specific Stripe commerce configuration.

Spanish product pages use EUR offers; English product pages use GBP offers.
The public site stays in pre-launch email-interest mode until a real Stripe
Payment Link exists for that exact locale/currency offer. Invalid or partial
commerce state stops deployment rather than guessing.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
CATALOG = Path(sys.argv[2] if len(sys.argv) > 2 else "commerce/catalog.json")

if not CATALOG.is_file():
    raise SystemExit(f"Missing commerce catalog: {CATALOG}")

catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
if catalog.get("provider") != "stripe":
    raise SystemExit("Commerce catalog provider must be 'stripe'")

PRODUCTS = {
    "book": {
        "checkout_key": "book",
        "pages": [
            {
                "path": "ediciones/libro/index.html",
                "offer": "es_eur",
                "locale": "es",
                "currency": "eur",
                "old_label": "Avísame cuando pueda comprarlo",
                "buy_label": "Comprar el libro",
            },
            {
                "path": "en/editions/book/index.html",
                "offer": "en_gbp",
                "locale": "en",
                "currency": "gbp",
                "old_label": "Tell me when I can buy it",
                "buy_label": "Buy the book",
            },
        ],
    },
    "textile_01": {
        "checkout_key": "textile-01",
        "pages": [
            {
                "path": "ediciones/camiseta/index.html",
                "offer": "es_eur",
                "locale": "es",
                "currency": "eur",
                "old_label": "Avísame cuando pueda comprarla",
                "buy_label": "Comprar la edición",
            },
            {
                "path": "en/editions/t-shirt/index.html",
                "offer": "en_gbp",
                "locale": "en",
                "currency": "gbp",
                "old_label": "Tell me when I can buy it",
                "buy_label": "Buy the edition",
            },
        ],
    },
}


def valid_payment_link(url: str) -> bool:
    try:
        parts = urlsplit(url)
    except Exception:
        return False
    return parts.scheme == "https" and parts.hostname in {"buy.stripe.com", "checkout.stripe.com"}


def patch_page(
    path: str,
    checkout_key: str,
    offer_key: str,
    currency: str,
    old_label: str,
    buy_label: str,
    payment_link: str | None,
):
    p = ROOT / path
    if not p.is_file():
        raise SystemExit(f"Missing commerce page: {path}")
    text = p.read_text(encoding="utf-8")

    anchor_re = re.compile(
        rf'(<a\b[^>]*data-checkout="{re.escape(checkout_key)}"[^>]*)(href="[^"]+")([^>]*>[\s\S]*?</a>)',
        re.I,
    )
    match = anchor_re.search(text)
    if not match:
        raise SystemExit(f"Prepared checkout hook missing in {path}: {checkout_key}")

    anchor = match.group(0)
    if f'data-commerce-offer="{offer_key}"' not in anchor:
        anchor = anchor.replace(
            '<a ',
            f'<a data-commerce-offer="{offer_key}" data-commerce-currency="{currency.upper()}" ',
            1,
        )

    if payment_link:
        if not valid_payment_link(payment_link):
            raise SystemExit(f"Invalid Stripe payment link for {checkout_key}/{offer_key}: {payment_link}")
        new_anchor = re.sub(r'href="[^"]+"', f'href="{payment_link}"', anchor, count=1)
        new_anchor = re.sub(r'\srel="nofollow"', ' rel="nofollow noopener"', new_anchor, count=1)
        new_anchor = new_anchor.replace(old_label, buy_label)
        if 'data-commerce-state=' not in new_anchor:
            new_anchor = new_anchor.replace('<a ', '<a data-commerce-state="live" ', 1)
        text = text[:match.start()] + new_anchor + text[match.end():]
        print(f"commerce live: {path} -> Stripe {currency.upper()}")
    else:
        href = re.search(r'href="([^"]+)"', anchor)
        if not href or not href.group(1).startswith("mailto:"):
            raise SystemExit(f"Expected pre-launch mailto checkout in {path}")
        if buy_label in anchor:
            raise SystemExit(f"Buy label present without payment link in {path}")
        if 'data-commerce-state=' not in anchor:
            anchor = anchor.replace('<a ', '<a data-commerce-state="prelaunch" ', 1)
        text = text[:match.start()] + anchor + text[match.end():]
        print(f"commerce prelaunch: {path} remains email-interest ({currency.upper()})")

    p.write_text(text, encoding="utf-8")


products = catalog.get("products")
if not isinstance(products, dict):
    raise SystemExit("commerce/catalog.json products must be an object")

for product_key, spec in PRODUCTS.items():
    product = products.get(product_key)
    if not isinstance(product, dict):
        raise SystemExit(f"Missing commerce product: {product_key}")

    stripe_product_id = product.get("stripe_product_id")
    offers = product.get("offers")
    if not isinstance(offers, dict):
        raise SystemExit(f"{product_key} offers must be an object")

    for page in spec["pages"]:
        offer_key = page["offer"]
        offer = offers.get(offer_key)
        if not isinstance(offer, dict):
            raise SystemExit(f"Missing commerce offer: {product_key}/{offer_key}")

        if offer.get("locale") != page["locale"]:
            raise SystemExit(f"Wrong locale for {product_key}/{offer_key}")
        if offer.get("currency") != page["currency"]:
            raise SystemExit(f"Wrong currency for {product_key}/{offer_key}")

        amount_minor = offer.get("amount_minor")
        stripe_price_id = offer.get("stripe_price_id")
        payment_link = offer.get("payment_link")

        if payment_link:
            if not isinstance(amount_minor, int) or amount_minor <= 0:
                raise SystemExit(f"{product_key}/{offer_key} has payment link but invalid amount_minor")
            if not stripe_product_id or not stripe_price_id:
                raise SystemExit(
                    f"{product_key}/{offer_key} has a payment link but incomplete Stripe IDs; refusing deployment"
                )
        else:
            if amount_minor is not None or stripe_price_id is not None:
                raise SystemExit(
                    f"{product_key}/{offer_key} has partial price metadata but no payment link; refusing deployment"
                )

        patch_page(
            page["path"],
            spec["checkout_key"],
            offer_key,
            page["currency"],
            page["old_label"],
            page["buy_label"],
            payment_link,
        )

print("OOLITA EUR/GBP commerce configuration validated successfully.")
