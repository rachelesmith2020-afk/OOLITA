#!/usr/bin/env python3
"""Route OOLITA's existing event hooks into a first-party analytics endpoint.

The browser sends only event name + local paths. No cookies, email addresses,
IP addresses, user agents or full referrers are collected by this script.

The pre-launch book checkout hook is retained only as inert, hidden markup so a
future production rebuild remains deterministic. It has no href and cannot be
used to purchase. A real checkout is accepted only when it is explicitly live
and points to Stripe.
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


def validate_book_checkout(rel: str, text: str) -> tuple[str, str]:
    """Validate one live or inert staged hook without changing its commerce state."""
    matches = list(BOOK_CHECKOUT_RE.finditer(text))
    if len(matches) > 1:
        raise SystemExit(f"Duplicate book checkout controls in {rel}")
    if not matches:
        # Older live output may lack the hidden hook; the reconstruction pass now
        # restores it before this layer. Keep this branch tolerant for one rollout.
        return text, "absent"

    anchor = matches[0].group(0)
    live = 'data-commerce-state="live"' in anchor
    staged = 'data-commerce-state="staged"' in anchor
    stripe = bool(re.search(r'href=["\']https://(?:buy|checkout)\.stripe\.com/', anchor, flags=re.I))

    if live:
        if not stripe:
            raise SystemExit(f"Live book checkout lacks a Stripe URL in {rel}")
        if 'data-oolita-event="book-interest"' not in anchor:
            raise SystemExit(f"Live book checkout lacks analytics hook in {rel}")
        return text, "live"

    if not staged:
        raise SystemExit(f"Book checkout is neither staged nor live in {rel}")
    if stripe:
        raise SystemExit(f"Staged book checkout unexpectedly contains a Stripe URL in {rel}")
    if 'href=' in anchor.lower():
        raise SystemExit(f"Staged book checkout unexpectedly has an href in {rel}")
    if 'aria-disabled="true"' not in anchor or 'tabindex="-1"' not in anchor:
        raise SystemExit(f"Staged book checkout is not inert in {rel}")
    if 'data-oolita-event="book-interest"' not in anchor:
        raise SystemExit(f"Staged book checkout analytics metadata missing in {rel}")
    if '.oolita-book-buy[data-commerce-state="staged"]{display:none!important}' not in text:
        raise SystemExit(f"Staged book checkout is not hidden in {rel}")
    return text, "staged"


count = 0
book_states = {"staged": 0, "live": 0, "absent": 0}
for p in ROOT.rglob("index.html"):
    s = p.read_text(encoding="utf-8")
    rel = p.relative_to(ROOT).as_posix()

    if rel in BOOK_PAGES:
        s, state = validate_book_checkout(rel, s)
        book_states[state] += 1

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
    "ediciones/libro/index.html": [],
    "en/editions/book/index.html": [],
    "ediciones/camiseta/index.html": [],
    "en/editions/t-shirt/index.html": [],
    "colaborar/index.html": ['data-oolita-event="partner-contact"'],
    "en/work-with-oolita/index.html": ['data-oolita-event="partner-contact"'],
}

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
            raise SystemExit(f"Duplicate book checkout controls after analytics pass in {path}")
        if checkouts:
            anchor = checkouts[0].group(0)
            state_live = 'data-commerce-state="live"' in anchor
            state_staged = 'data-commerce-state="staged"' in anchor
            stripe = bool(re.search(r'href=["\']https://(?:buy|checkout)\.stripe\.com/', anchor, flags=re.I))
            if state_live:
                if not stripe:
                    raise SystemExit(f"Live book checkout Stripe URL missing in {path}")
            elif state_staged:
                if stripe or 'href=' in anchor.lower():
                    raise SystemExit(f"Staged book checkout became actionable in {path}")
                if '.oolita-book-buy[data-commerce-state="staged"]{display:none!important}' not in s:
                    raise SystemExit(f"Staged book checkout is visible in {path}")
            else:
                raise SystemExit(f"Unexpected book checkout state in {path}")
            if 'data-oolita-event="book-interest"' not in anchor:
                raise SystemExit(f"Book checkout analytics metadata missing in {path}")

print(f"OOLITA first-party analytics layer validated across {count} pages.")
print(
    "Book checkout hooks: "
    f"{book_states['staged']} staged hidden, {book_states['live']} live, {book_states['absent']} absent."
)
