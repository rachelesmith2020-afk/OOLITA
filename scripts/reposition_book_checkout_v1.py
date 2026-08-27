#!/usr/bin/env python3
"""Place the OOLITA book checkout hook beside the primary availability row.

The commerce pass owns whether checkout is staged or live. A production rebuild
can begin from a pre-launch page where the staged hook was previously removed;
in that case this pass recreates only an inert staged hook with known locale
metadata. The later commerce pass remains authoritative and is the only layer
allowed to turn it into a live Stripe checkout.
"""
from __future__ import annotations

from html import unescape
from pathlib import Path
import re
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")

PAGES = {
    "ediciones/libro/index.html": {
        "notify": "Avísame por correo",
        "staged_label": "Comprar el libro · próximamente",
        "live_label": "Comprar el libro",
        "staged_title": "Compra todavía no disponible",
        "page_marker": "48 páginas",
        "offer": "es_eur",
        "currency": "EUR",
    },
    "en/editions/book/index.html": {
        "notify": "Let me know by email",
        "staged_label": "Buy the book · coming soon",
        "live_label": "Buy the book",
        "staged_title": "Checkout is not active yet",
        "page_marker": "48 pages",
        "offer": "en_gbp",
        "currency": "GBP",
    },
}

STYLE = r'''<style id="oolita-book-buy-position-v1">
.oolita-book-buy{display:inline-flex;align-items:baseline;gap:.32em;margin-left:1rem;padding:0;border:0;background:none;color:inherit;text-decoration:underline;text-decoration-thickness:1px;text-underline-offset:.16em;font:inherit;line-height:inherit;white-space:nowrap;vertical-align:baseline}
.oolita-book-buy[data-commerce-state="staged"]{display:none!important}
.oolita-book-buy .oolita-book-buy-arrow{display:none}
.oolita-book-buy[data-commerce-state="live"]{opacity:1;cursor:pointer;text-decoration-style:solid}
@media (max-width:720px){.oolita-book-buy{margin-left:0;margin-top:.55rem}}
</style>'''


def rendered(fragment: str) -> str:
    return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", " ", fragment))).strip()


def attr(fragment: str, name: str) -> str | None:
    match = re.search(rf'\b{re.escape(name)}=["\']([^"\']+)["\']', fragment, flags=re.I)
    return match.group(1) if match else None


def find_anchor_with_text(text: str, phrase: str) -> re.Match[str]:
    matches = []
    for match in re.finditer(r'<a\b[^>]*>[\s\S]*?</a>', text, flags=re.I):
        if phrase in rendered(match.group(0)):
            matches.append(match)
    if len(matches) != 1:
        raise SystemExit(f"Expected exactly one anchor containing {phrase!r}; found {len(matches)}")
    return matches[0]


def build_checkout(original: str, spec: dict[str, str]) -> str:
    state = (attr(original, "data-commerce-state") or "").lower()
    offer = attr(original, "data-commerce-offer")
    currency = attr(original, "data-commerce-currency")
    analytics_event = attr(original, "data-oolita-event")
    if not offer or not currency:
        raise SystemExit("Book checkout is missing commerce offer/currency metadata")
    if analytics_event != "book-interest":
        raise SystemExit(f"Book checkout analytics hook is missing or unexpected: {analytics_event!r}")

    common = (
        f'class="oolita-book-buy" data-checkout="book" '
        f'data-commerce-offer="{offer}" data-commerce-currency="{currency}" '
        f'data-commerce-state="{state}" data-book-pages="{spec["page_marker"]}" '
        f'data-oolita-event="{analytics_event}"'
    )

    if state == "staged":
        label = spec["staged_label"]
        return (
            f'<a {common} role="button" aria-disabled="true" tabindex="-1" '
            f'title="{spec["staged_title"]}">'
            f'<span class="oolita-book-buy-arrow">→</span><span>{label}</span></a>'
        )

    if state == "live":
        href = attr(original, "href")
        if not href or not re.fullmatch(r'https://(?:buy|checkout)\.stripe\.com/.+', href):
            raise SystemExit("Live book checkout does not point to Stripe")
        label = spec["live_label"]
        return (
            f'<a {common} href="{href}" rel="nofollow noopener">'
            f'<span class="oolita-book-buy-arrow">→</span><span>{label}</span></a>'
        )

    raise SystemExit(f"Book checkout must already be staged or live before positioning; found {state!r}")


def build_staged_checkout(spec: dict[str, str]) -> str:
    """Recreate only the inert pre-launch hook when production HTML lacks it."""
    return (
        f'<a class="oolita-book-buy" data-checkout="book" '
        f'data-commerce-offer="{spec["offer"]}" data-commerce-currency="{spec["currency"]}" '
        f'data-commerce-state="staged" data-book-pages="{spec["page_marker"]}" '
        f'data-oolita-event="book-interest" role="button" aria-disabled="true" tabindex="-1" '
        f'title="{spec["staged_title"]}">'
        f'<span class="oolita-book-buy-arrow">→</span><span>{spec["staged_label"]}</span></a>'
    )


def reposition(rel: str, spec: dict[str, str]) -> None:
    path = ROOT / rel
    if not path.is_file():
        raise SystemExit(f"Missing book page: {rel}")
    text = path.read_text(encoding="utf-8")

    checkout_re = re.compile(
        r'<a\b(?=[^>]*\bdata-checkout=["\']book["\'])[^>]*>[\s\S]*?</a>',
        flags=re.I,
    )
    checkout_matches = list(checkout_re.finditer(text))
    if len(checkout_matches) > 1:
        raise SystemExit(f"Expected at most one book checkout in {rel}; found {len(checkout_matches)}")

    if checkout_matches:
        original = checkout_matches[0].group(0)
        compact = build_checkout(original, spec)
        text = text[:checkout_matches[0].start()] + text[checkout_matches[0].end():]
    else:
        # The current live pre-launch page may intentionally contain no checkout
        # anchor. Rehydrate an inert staged hook so the deterministic commerce
        # pipeline can validate it. There is deliberately no href or Stripe URL.
        compact = build_staged_checkout(spec)
        print(f"book checkout bootstrap restored inert staged hook: {rel}")

    notify = find_anchor_with_text(text, spec["notify"])
    text = text[:notify.end()] + "\n" + compact + text[notify.end():]

    if 'id="oolita-book-buy-position-v1"' not in text:
        if "</head>" not in text:
            raise SystemExit(f"Missing </head> in {rel}")
        text = text.replace("</head>", STYLE + "\n</head>", 1)

    path.write_text(text, encoding="utf-8")

    final = path.read_text(encoding="utf-8")
    if len(list(checkout_re.finditer(final))) != 1:
        raise SystemExit(f"Book checkout count changed unexpectedly in {rel}")
    final_notify = find_anchor_with_text(final, spec["notify"])
    checkout = checkout_re.search(final)
    assert checkout is not None
    if checkout.start() <= final_notify.end() or checkout.start() - final_notify.end() > 700:
        raise SystemExit(f"Book checkout is not adjacent to availability notification in {rel}")
    if final.count('id="oolita-book-buy-position-v1"') != 1:
        raise SystemExit(f"Book checkout positioning style duplicated in {rel}")
    if spec["page_marker"] not in final:
        raise SystemExit(f"Book page-count invariant missing after checkout placement in {rel}")
    if 'data-oolita-event="book-interest"' not in checkout.group(0):
        raise SystemExit(f"Book analytics hook missing after checkout placement in {rel}")
    if 'data-commerce-state="staged"' in checkout.group(0):
        if re.search(r'href=["\']https://(?:buy|checkout)\.stripe\.com/', checkout.group(0), flags=re.I):
            raise SystemExit(f"Staged checkout unexpectedly points to Stripe in {rel}")
        if '.oolita-book-buy[data-commerce-state="staged"]{display:none!important}' not in final:
            raise SystemExit(f"Staged checkout is not hidden in {rel}")
    print(f"book checkout positioned beside availability: {rel}")


for rel, spec in PAGES.items():
    reposition(rel, spec)

print("OOLITA book checkout placement validated on both language routes.")
