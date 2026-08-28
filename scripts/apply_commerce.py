#!/usr/bin/env python3
"""Apply OOLITA's locale-specific Stripe commerce configuration.

Spanish book checkout uses EUR and English book checkout uses GBP. The book
purchase controls may be visible before launch, but they must remain inert until
a complete Stripe offer exists and BookVault fulfilment is explicitly marked
ready. The confirmed ISBN remains visible and machine-readable in both book
pages. Invalid or partial commerce state stops deployment rather than guessing.
"""
from __future__ import annotations

from html import unescape
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

dynamic_checkout = catalog.get("checkout_mode") == "dynamic_checkout_sessions_by_delivery_country"

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
    """Allow the legacy mailto or an explicitly approved first-party interest path."""
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
    labels = (page["old_label"], page["staged_label"], page["buy_label"])
    for label in labels:
        if label in anchor:
            return anchor.replace(label, target, 1)
    raise SystemExit(f"Could not find a known commerce label in {page['path']}")


def rendered(fragment: str) -> str:
    return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", " ", fragment))).strip()


def matching_div_block(text: str, label: str, value: str) -> tuple[int, int]:
    """Return the smallest div block containing one complete specification row."""
    token_re = re.compile(r"</?div\b[^>]*>", flags=re.I)
    stack: list[int] = []
    candidates: list[tuple[int, int]] = []
    for match in token_re.finditer(text):
        token = match.group(0)
        if token.lower().startswith("</div"):
            if not stack:
                continue
            start = stack.pop()
            block = text[start:match.end()]
            visible = rendered(block)
            if label in visible and value in visible:
                candidates.append((start, match.end()))
        else:
            stack.append(match.start())

    if not candidates:
        raise SystemExit(f"Could not locate book specification row: {label} / {value}")
    return min(candidates, key=lambda pair: pair[1] - pair[0])


def patch_book_isbn(path: str, locale: str, isbn13: str) -> None:
    """Publish the ISBN in the book specification and machine-readable Book data."""
    p = ROOT / path
    if not p.is_file():
        raise SystemExit(f"Missing ISBN target page: {path}")
    text = p.read_text(encoding="utf-8")
    isbn_display = "978-1-0669398-0-0"

    if isbn13 != "9781066939800":
        raise SystemExit(f"Unexpected canonical OOLITA ISBN-13: {isbn13!r}")

    if not re.search(r"\bISBN\s+978-1-0669398-0-0\b", rendered(text)):
        if locale == "es":
            anchor_label = "Impresión"
            anchor_value = "Bajo demanda, uno a uno"
        elif locale == "en":
            anchor_label = "Printing"
            anchor_value = "On demand, one at a time"
        else:
            raise SystemExit(f"Unsupported ISBN page locale: {locale}")

        start, end = matching_div_block(text, anchor_label, anchor_value)
        row = text[start:end]
        if anchor_label not in row or anchor_value not in row:
            raise SystemExit(f"Book specification markup is not safely cloneable in {path}")
        isbn_row = row.replace(anchor_label, "ISBN", 1).replace(anchor_value, isbn_display, 1)
        text = text[:end] + "\n" + isbn_row + text[end:]

    schema_marker = 'data-oolita-isbn-schema="v1"'
    if schema_marker not in text:
        canonical = (
            "https://oolita.es/ediciones/libro/"
            if locale == "es"
            else "https://oolita.es/en/editions/book/"
        )
        schema = {
            "@context": "https://schema.org",
            "@type": "Book",
            "@id": canonical + "#book",
            "url": canonical,
            "name": "OOLITA",
            "isbn": isbn13,
            "author": {"@type": "Person", "name": "Raquel Costantini"},
            "publisher": {"@type": "Organization", "name": "Vestini Tribe"},
            "bookFormat": "https://schema.org/Hardcover",
            "numberOfPages": 48,
            "inLanguage": ["es", "en"],
            "datePublished": "2027-01-31",
        }
        script = (
            f'<script type="application/ld+json" {schema_marker}>'
            + json.dumps(schema, ensure_ascii=False, separators=(",", ":"))
            + "</script>"
        )
        if "</head>" not in text:
            raise SystemExit(f"Missing </head> while adding ISBN schema in {path}")
        text = text.replace("</head>", script + "\n</head>", 1)

    p.write_text(text, encoding="utf-8")

    final = p.read_text(encoding="utf-8")
    visible = rendered(final)
    if f"ISBN {isbn_display}" not in visible:
        raise SystemExit(f"Visible ISBN missing after commerce pass: {path}")
    if f'"isbn":"{isbn13}"' not in final:
        raise SystemExit(f"Book ISBN schema missing after commerce pass: {path}")
    if final.count(schema_marker) != 1:
        raise SystemExit(f"ISBN schema duplicated in {path}")
    print(f"book ISBN published: {path} -> {isbn_display}")


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

    if product_key == "book":
        isbn13 = product.get("isbn13")
        if not isinstance(isbn13, str) or not re.fullmatch(r"\d{13}", isbn13):
            raise SystemExit("book isbn13 must be a 13-digit string")
        fulfilment = product.get("fulfilment")
        if not isinstance(fulfilment, dict) or fulfilment.get("provider") != "bookvault":
            raise SystemExit("OOLITA book must declare BookVault fulfilment")
        if str(fulfilment.get("isbn", "")) != isbn13:
            raise SystemExit("BookVault fulfilment ISBN must match the canonical book ISBN")
    else:
        isbn13 = None
        fulfilment = None

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
        elif amount_minor is not None or stripe_price_id is not None:
            if not dynamic_checkout:
                raise SystemExit(
                    f"{product_key}/{offer_key} has price metadata without a Payment Link outside dynamic checkout mode"
                )
            if not isinstance(amount_minor, int) or amount_minor <= 0 or not stripe_product_id or not stripe_price_id:
                raise SystemExit(
                    f"{product_key}/{offer_key} has incomplete dynamic Stripe price metadata; refusing deployment"
                )
            print(f"commerce dynamic price staged: {product_key}/{offer_key} -> {currency.upper()} {amount_minor}")

        patch_page(
            page["path"],
            spec["checkout_key"],
            offer_key,
            page["currency"],
            payment_link,
            spec["staged_button"],
            page,
        )

        if product_key == "book":
            assert isbn13 is not None
            patch_book_isbn(page["path"], page["locale"], isbn13)

print("OOLITA EUR/GBP commerce, staged checkout and book ISBN validated successfully.")
