#!/usr/bin/env python3
"""Apply OOLITA's locale-specific Stripe commerce configuration.

Spanish book checkout uses EUR and English book checkout uses GBP. The book
purchase controls may be visible before launch, but they must remain inert until
a complete Stripe offer exists and BookVault fulfilment is explicitly marked
ready. Invalid or partial commerce state stops deployment rather than guessing.
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
        "staged_button": True,
        "pages": [
            {
                "path": "ediciones/libro/index.html",
                "offer": "es_eur",
                "locale": "es",
                "currency": "eur",
                "old_label": "Avísame cuando pueda comprarlo",
                "buy_label": "Comprar el libro",
                "staged_label": "Comprar el libro · próximamente",
                "staged_title": "Compra todavía no disponible",
                "prelaunch_hrefs": ("/?follow=book#seguir-oolita",),
            },
            {
                "path": "en/editions/book/index.html",
                "offer": "en_gbp",
                "locale": "en",
                "currency": "gbp",
                "old_label": "Tell me when I can buy it",
                "buy_label": "Buy the book",
                "staged_label": "Buy the book · coming soon",
                "staged_title": "Checkout is not active yet",
                "prelaunch_hrefs": ("/en/?follow=book#follow-oolita",),
            },
        ],
    },
    "textile_01": {
        "checkout_key": "textile-01",
        "staged_button": False,
        "pages": [
            {
                "path": "ediciones/camiseta/index.html",
                "offer": "es_eur",
                "locale": "es",
                "currency": "eur",
                "old_label": "Avísame cuando pueda comprarla",
                "buy_label": "Comprar la edición",
                "staged_label": "Comprar la edición · próximamente",
                "staged_title": "Compra todavía no disponible",
                "prelaunch_hrefs": ("/?follow=textile#seguir-oolita",),
            },
            {
                "path": "en/editions/t-shirt/index.html",
                "offer": "en_gbp",
                "locale": "en",
                "currency": "gbp",
                "old_label": "Tell me when I can buy it",
                "buy_label": "Buy the edition",
                "staged_label": "Buy the edition · coming soon",
                "staged_title": "Checkout is not active yet",
                "prelaunch_hrefs": ("/en/?follow=textile#follow-oolita",),
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


def valid_prelaunch_href(href: str, allowed_first_party: tuple[str, ...]) -> bool:
    return href.startswith("mailto:") or href in allowed_first_party


def set_attr(anchor: str, name: str, value: str) -> str:
    quoted = f'{name}="{value}"'
    pattern = re.compile(rf'\s{name}="[^"]*"', re.I)
    if pattern.search(anchor):
        return pattern.sub(f' {quoted}', anchor, count=1)
    return anchor.replace('<a ', f'<a {quoted} ', 1)


def remove_attr(anchor: str, name: str) -> str:
    return re.sub(rf'\s{name}="[^"]*"', '', anchor, count=1, flags=re.I)


def normalize_label(anchor: str, page: dict, target: str) -> str:
    labels = (page["old_label"], page["buy_label"], page["staged_label"])
    for label in labels:
        if label in anchor:
            return anchor.replace(label, target, 1)
    raise SystemExit(f"Could not find a known commerce label in {page['path']}")


def patch_page(path: str, checkout_key: str, offer_key: str, currency: str,
               payment_link: str | None, staged_button: bool, page: dict) -> None:
    p = ROOT / path
    if not p.is_file():
        raise SystemExit(f"Missing commerce page: {path}")
    text = p.read_text(encoding="utf-8")

    anchor_re = re.compile(
        rf'<a\b[^>]*data-checkout="{re.escape(checkout_key)}"[^>]*>[\s\S]*?</a>',
        re.I,
    )
    match = anchor_re.search(text)
    if not match:
        raise SystemExit(f"Prepared checkout hook missing in {path}: {checkout_key}")

    anchor = match.group(0)
    anchor = set_attr(anchor, "data-commerce-offer", offer_key)
    anchor = set_attr(anchor, "data-commerce-currency", currency.upper())

    if payment_link:
        if not valid_payment_link(payment_link):
            raise SystemExit(f"Invalid Stripe payment link for {checkout_key}/{offer_key}: {payment_link}")
        if re.search(r'\shref="[^"]*"', anchor, re.I):
            anchor = re.sub(r'\shref="[^"]*"', f' href="{payment_link}"', anchor, count=1, flags=re.I)
        else:
            anchor = anchor.replace('<a ', f'<a href="{payment_link}" ', 1)
        for attr in ("aria-disabled", "tabindex", "title", "role"):
            anchor = remove_attr(anchor, attr)
        anchor = set_attr(anchor, "data-commerce-state", "live")
        anchor = normalize_label(anchor, page, page["buy_label"])
        if 'rel="nofollow"' in anchor:
            anchor = anchor.replace('rel="nofollow"', 'rel="nofollow noopener"', 1)
        print(f"commerce live: {path} -> Stripe {currency.upper()}")

    elif staged_button:
        href_match = re.search(r'\shref="([^"]+)"', anchor, re.I)
        if href_match:
            href = href_match.group(1)
            if not valid_prelaunch_href(href, page["prelaunch_hrefs"]):
                raise SystemExit(f"Unexpected staged checkout href in {path}: {href}")
            anchor = remove_attr(anchor, "href")
        elif 'data-commerce-state="staged"' not in anchor:
            raise SystemExit(f"Staged checkout in {path} has neither approved prelaunch href nor staged state")
        anchor = set_attr(anchor, "data-commerce-state", "staged")
        anchor = set_attr(anchor, "role", "button")
        anchor = set_attr(anchor, "aria-disabled", "true")
        anchor = set_attr(anchor, "tabindex", "-1")
        anchor = set_attr(anchor, "title", page["staged_title"])
        anchor = normalize_label(anchor, page, page["staged_label"])
        if re.search(r'https://(?:buy|checkout)\.stripe\.com', anchor, re.I):
            raise SystemExit(f"Stripe URL present in staged checkout control: {path}")
        print(f"commerce staged: {path} shows inert {currency.upper()} purchase control")

    else:
        href_match = re.search(r'\shref="([^"]+)"', anchor, re.I)
        if not href_match or not valid_prelaunch_href(href_match.group(1), page["prelaunch_hrefs"]):
            raise SystemExit(f"Expected approved pre-launch interest link in {path}")
        anchor = set_attr(anchor, "data-commerce-state", "prelaunch")
        anchor = normalize_label(anchor, page, page["old_label"])
        print(f"commerce prelaunch: {path} remains email-interest ({currency.upper()})")

    text = text[:match.start()] + anchor + text[match.end():]
    p.write_text(text, encoding="utf-8")


products = catalog.get("products")
if not isinstance(products, dict):
    raise SystemExit("commerce/catalog.json products must be an object")

for product_key, spec in PRODUCTS.items():
    product = products.get(product_key)
    if not isinstance(product, dict):
        raise SystemExit(f"Missing commerce product: {product_key}")

    fulfilment = product.get("fulfilment") if product_key == "book" else None
    if product_key == "book":
        if not isinstance(fulfilment, dict) or fulfilment.get("provider") != "bookvault":
            raise SystemExit("OOLITA book must declare BookVault fulfilment")
        isbn = str(fulfilment.get("isbn", ""))
        if not re.fullmatch(r"\d{13}", isbn):
            raise SystemExit("OOLITA BookVault fulfilment must contain a 13-digit ISBN")

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
            if product_key == "book" and fulfilment.get("status") != "ready":
                raise SystemExit("Book checkout cannot go live until BookVault fulfilment status is 'ready'")
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
            payment_link,
            spec["staged_button"],
            page,
        )

print("OOLITA EUR/GBP commerce configuration validated successfully.")

# Deployment trigger: staged checkout / reader-path compatibility, 2026-08-27.
