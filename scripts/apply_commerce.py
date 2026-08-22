#!/usr/bin/env python3
"""Apply OOLITA commerce configuration to a built site.

The public site stays in pre-launch email-interest mode until a real Stripe
Payment Link exists in commerce/catalog.json. When a payment link is added,
this script swaps only the matching prepared checkout hooks. Invalid or partial
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
        "pages": [
            ("ediciones/libro/index.html", "Avísame cuando pueda comprarlo", "Comprar el libro"),
            ("en/editions/book/index.html", "Tell me when I can buy it", "Buy the book"),
        ],
        "checkout_key": "book",
    },
    "textile_01": {
        "pages": [
            ("ediciones/camiseta/index.html", "Avísame cuando pueda comprarla", "Comprar la edición"),
            ("en/editions/t-shirt/index.html", "Tell me when I can buy it", "Buy the edition"),
        ],
        "checkout_key": "textile-01",
    },
}


def valid_payment_link(url: str) -> bool:
    try:
        parts = urlsplit(url)
    except Exception:
        return False
    return parts.scheme == "https" and parts.hostname in {"buy.stripe.com", "checkout.stripe.com"}


def patch_page(path: str, checkout_key: str, old_label: str, buy_label: str, payment_link: str | None):
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
    if payment_link:
        if not valid_payment_link(payment_link):
            raise SystemExit(f"Invalid Stripe payment link for {checkout_key}: {payment_link}")
        new_anchor = re.sub(r'href="[^"]+"', f'href="{payment_link}"', anchor, count=1)
        new_anchor = re.sub(r'\srel="nofollow"', ' rel="nofollow noopener"', new_anchor, count=1)
        new_anchor = new_anchor.replace(old_label, buy_label)
        if 'data-commerce-state=' not in new_anchor:
            new_anchor = new_anchor.replace('<a ', '<a data-commerce-state="live" ', 1)
        text = text[:match.start()] + new_anchor + text[match.end():]
        print(f"commerce live: {path} -> Stripe")
    else:
        # Pre-launch mode must remain an email-interest action, never a fake buy button.
        href = re.search(r'href="([^"]+)"', anchor)
        if not href or not href.group(1).startswith("mailto:"):
            raise SystemExit(f"Expected pre-launch mailto checkout in {path}")
        if buy_label in anchor:
            raise SystemExit(f"Buy label present without payment link in {path}")
        print(f"commerce prelaunch: {path} remains email-interest")

    p.write_text(text, encoding="utf-8")


products = catalog.get("products")
if not isinstance(products, dict):
    raise SystemExit("commerce/catalog.json products must be an object")

for key, spec in PRODUCTS.items():
    product = products.get(key)
    if not isinstance(product, dict):
        raise SystemExit(f"Missing commerce product: {key}")

    payment_link = product.get("payment_link")
    price = product.get("price")
    currency = product.get("currency")
    stripe_product_id = product.get("stripe_product_id")
    stripe_price_id = product.get("stripe_price_id")

    if payment_link:
        if price is None or not currency or not stripe_product_id or not stripe_price_id:
            raise SystemExit(
                f"{key} has a payment link but incomplete product/price metadata; refusing deployment"
            )
    elif any(v is not None for v in (price, currency, stripe_product_id, stripe_price_id)):
        raise SystemExit(
            f"{key} has partial Stripe metadata but no payment link; refusing deployment"
        )

    for path, old_label, buy_label in spec["pages"]:
        patch_page(path, spec["checkout_key"], old_label, buy_label, payment_link)

print("OOLITA commerce configuration validated successfully.")
