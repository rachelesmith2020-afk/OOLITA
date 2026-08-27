#!/usr/bin/env python3
"""Route OOLITA's existing event hooks into a first-party analytics endpoint.

The browser sends only event name + local paths. No cookies, email addresses,
IP addresses, user agents or full referrers are collected by this script.

Pre-launch book purchase controls are removed from the emitted HTML entirely.
A book checkout is retained only when it is a real live Stripe checkout.
"""
from pathlib import Path
import re
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")

SCRIPT = r'''<script id="oolita-event-layer">(function(){
function safePath(href){if(!href)return"";try{var u=new URL(href,location.href);return u.origin===location.origin?u.pathname:"";}catch(e){return"";}}
function post(detail){var body=JSON.stringify(detail);try{if(navigator.sendBeacon){navigator.sendBeacon('/api/event',body);return;}}catch(e){}try{fetch('/api/event',{method:'POST',headers:{'Content-Type':'text/plain;charset=UTF-8'},body:body,keepalive:true,credentials:'omit'});}catch(e){}}
function emit(name,el,extra){var detail={event:name,path:location.pathname,href:el&&el.href?safePath(el.href):""};if(extra&&typeof extra==='object'){for(var k in extra){if(Object.prototype.hasOwnProperty.call(extra,k)&&k!=='event'&&k!=='path'&&k!=='href')detail[k]=extra[k];}}window.dispatchEvent(new CustomEvent('oolita:event',{detail:detail}));window.dataLayer=window.dataLayer||[];window.dataLayer.push(Object.assign({event:'oolita_event'},detail));post(detail);}
window.OOLITA_EVENT=function(name,extra){emit(name,null,extra||{});};
document.addEventListener('click',function(e){var a=e.target.closest('[data-oolita-event]');if(a)emit(a.getAttribute('data-oolita-event'),a);});
emit('pageview',null);
})();</script>'''

BOOK_PAGES = {
    "ediciones/libro/index.html",
    "en/editions/book/index.html",
}
BOOK_CHECKOUT_RE = re.compile(
    r'<a\b(?=[^>]*\bdata-checkout=["\']book["\'])[^>]*>[\s\S]*?</a>',
    flags=re.I,
)


def strip_nonlive_book_checkout(rel: str, text: str) -> tuple[str, bool]:
    """Remove the pre-launch/staged Buy control; preserve only a real Stripe checkout."""
    matches = list(BOOK_CHECKOUT_RE.finditer(text))
    if len(matches) > 1:
        raise SystemExit(f"Duplicate book checkout controls in {rel}")
    if not matches:
        return text, False

    match = matches[0]
    anchor = match.group(0)
    live = 'data-commerce-state="live"' in anchor
    stripe = bool(re.search(r'href=["\']https://(?:buy|checkout)\.stripe\.com/', anchor, flags=re.I))

    if live:
        if not stripe:
            raise SystemExit(f"Live book checkout lacks a Stripe URL in {rel}")
        if 'data-oolita-event="book-interest"' not in anchor:
            raise SystemExit(f"Live book checkout lacks analytics hook in {rel}")
        return text, False

    if stripe:
        raise SystemExit(f"Non-live book checkout unexpectedly contains a Stripe URL in {rel}")

    text = text[:match.start()] + text[match.end():]
    return text, True


count = 0
removed_book_controls = 0
for p in ROOT.rglob("index.html"):
    s = p.read_text(encoding="utf-8")
    rel = p.relative_to(ROOT).as_posix()

    if rel in BOOK_PAGES:
        s, removed = strip_nonlive_book_checkout(rel, s)
        if removed:
            removed_book_controls += 1

    if 'id="oolita-event-layer"' not in s:
        raise SystemExit(f"Missing OOLITA event layer in {p.relative_to(ROOT)}")
    ns, n = re.subn(r'<script id="oolita-event-layer">[\s\S]*?</script>', SCRIPT, s, count=1)
    if n != 1:
        raise SystemExit(f"Could not replace OOLITA event layer in {p.relative_to(ROOT)}")
    p.write_text(ns, encoding="utf-8")
    count += 1

required = {
    "index.html": [
        'data-oolita-event="home-cabo-de-gata"',
        'data-oolita-event="home-editions"',
        'data-oolita-event="home-sundays"',
        'data-oolita-event="follow-submit"',
    ],
    "en/index.html": [
        'data-oolita-event="home-cabo-de-gata"',
        'data-oolita-event="home-editions"',
        'data-oolita-event="home-sundays"',
        'data-oolita-event="follow-submit"',
    ],
    "ediciones/index.html": ['data-oolita-event="field-book-interest"'],
    "en/editions/index.html": ['data-oolita-event="field-book-interest"'],
    # Book-interest is required only when an actual live Stripe checkout exists.
    "ediciones/libro/index.html": [],
    "en/editions/book/index.html": [],
    "ediciones/camiseta/index.html": [],
    "en/editions/t-shirt/index.html": [],
    "colaborar/index.html": ['data-oolita-event="partner-contact"'],
    "en/work-with-oolita/index.html": ['data-oolita-event="partner-contact"'],
}

# A rebuild starts from the current live output. The final growth layer renames
# the textile event from the earlier generic interest hook to the final follow
# journey hook. Both are semantically valid at this pre-growth analytics stage;
# require one of them rather than forcing the live site back to an obsolete name.
required_any = {
    "ediciones/camiseta/index.html": (
        'data-oolita-event="textile-interest"',
        'data-oolita-event="textile-follow"',
    ),
    "en/editions/t-shirt/index.html": (
        'data-oolita-event="textile-interest"',
        'data-oolita-event="textile-follow"',
    ),
}

for path, needles in required.items():
    p = ROOT / path
    if not p.is_file():
        raise SystemExit(f"Missing analytics page: {path}")
    s = p.read_text(encoding="utf-8")
    for needle in needles:
        if needle not in s:
            raise SystemExit(f"Missing analytics hook in {path}: {needle}")
    alternatives = required_any.get(path)
    if alternatives and not any(needle in s for needle in alternatives):
        raise SystemExit(f"Missing analytics hook in {path}: one of {alternatives}")
    if "navigator.sendBeacon('/api/event'" not in s:
        raise SystemExit(f"First-party analytics endpoint missing in {path}")

    if path in BOOK_PAGES:
        checkouts = list(BOOK_CHECKOUT_RE.finditer(s))
        if len(checkouts) > 1:
            raise SystemExit(f"Duplicate book checkout controls after cleanup in {path}")
        if checkouts:
            anchor = checkouts[0].group(0)
            if 'data-commerce-state="live"' not in anchor:
                raise SystemExit(f"Non-live book checkout survived cleanup in {path}")
            if 'data-oolita-event="book-interest"' not in anchor:
                raise SystemExit(f"Live book checkout analytics hook missing in {path}")
            if not re.search(r'href=["\']https://(?:buy|checkout)\.stripe\.com/', anchor, flags=re.I):
                raise SystemExit(f"Live book checkout Stripe URL missing in {path}")
        else:
            for label in (
                "Comprar el libro · próximamente",
                "Buy the book · coming soon",
            ):
                if label in s:
                    raise SystemExit(f"Staged book purchase label survived cleanup in {path}: {label}")

print(f"OOLITA first-party analytics layer validated across {count} pages.")
print(f"Pre-launch book purchase controls removed from {removed_book_controls} page(s).")
