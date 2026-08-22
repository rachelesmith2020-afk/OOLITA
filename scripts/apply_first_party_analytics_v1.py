#!/usr/bin/env python3
"""Route OOLITA's existing event hooks into a first-party analytics endpoint.

The browser sends only event name + local paths. No cookies, email addresses,
IP addresses, user agents or full referrers are collected by this script.
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

count = 0
for p in ROOT.rglob("index.html"):
    s = p.read_text(encoding="utf-8")
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
    "ediciones/libro/index.html": ['data-oolita-event="book-interest"'],
    "en/editions/book/index.html": ['data-oolita-event="book-interest"'],
    "ediciones/camiseta/index.html": ['data-oolita-event="textile-interest"'],
    "en/editions/t-shirt/index.html": ['data-oolita-event="textile-interest"'],
    "colaborar/index.html": ['data-oolita-event="partner-contact"'],
    "en/work-with-oolita/index.html": ['data-oolita-event="partner-contact"'],
}
for path, needles in required.items():
    p = ROOT / path
    if not p.is_file():
        raise SystemExit(f"Missing analytics page: {path}")
    s = p.read_text(encoding="utf-8")
    for needle in needles:
        if needle not in s:
            raise SystemExit(f"Missing analytics hook in {path}: {needle}")
    if "navigator.sendBeacon('/api/event'" not in s:
        raise SystemExit(f"First-party analytics endpoint missing in {path}")

print(f"OOLITA first-party analytics layer validated across {count} pages.")
