#!/usr/bin/env python3
"""Finish the remaining OOLITA site-improvement list without inventing facts.

Runs after growth + commerce. It tightens product information, makes the
field-publication CTA explicit, adds a provider-ready Follow OOLITA block, and
adds a vendor-neutral analytics event layer. The Follow block may remain in its
safe pending state or be upgraded by the later Cloudflare Follow layer.
"""
from pathlib import Path
import re
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")


def read(path):
    p = ROOT / path
    if not p.is_file():
        raise SystemExit(f"Missing page: {path}")
    return p, p.read_text(encoding="utf-8")


def replace_once(path, old, new, marker=None):
    p, s = read(path)
    marker = marker or new
    if marker in s:
        print(f"list completion already present {path}: {marker[:64]!r}")
        return
    if old not in s:
        raise SystemExit(f"Expected source text missing in {path}: {old[:120]!r}")
    p.write_text(s.replace(old, new, 1), encoding="utf-8")
    print(f"list completion patched {path}")

# Product-specific field-publication CTA.
replace_once("ediciones/index.html", "<span class=\"nom\">Avísame cuando avance</span>", "<span class=\"nom\">Avísame cuando empiecen las publicaciones de campo</span>")
replace_once("en/editions/index.html", "<span class=\"nom\">Tell me when it develops</span>", "<span class=\"nom\">Tell me when field publications begin</span>")

# Pre-sale information categories, without inventing values.
product_notes = {
    "ediciones/libro/index.html": ("La venta todavía no está abierta.</p>", "La venta todavía no está abierta.</p><p class=\"parr venta-info\"><strong>Antes de abrir la venta:</strong> aquí se indicarán los destinos de envío, el plazo estimado de preparación y entrega, la política de devoluciones y cómo se muestran los impuestos en el pago.</p>", "destinos de envío"),
    "en/editions/book/index.html": ("Sales are not open yet.</p>", "Sales are not open yet.</p><p class=\"parr venta-info\"><strong>Before sales open:</strong> this page will state shipping territories, estimated preparation and delivery times, the returns policy, and how taxes are shown at checkout.</p>", "shipping territories"),
    "ediciones/camiseta/index.html": ("La venta todavía no está abierta.</p>", "La venta todavía no está abierta.</p><p class=\"parr venta-info\"><strong>Antes de abrir la venta:</strong> aquí se indicarán los destinos de envío, el plazo estimado de preparación y entrega, la política de devoluciones y cómo se muestran los impuestos en el pago.</p>", "destinos de envío"),
    "en/editions/t-shirt/index.html": ("Sales are not open yet.</p>", "Sales are not open yet.</p><p class=\"parr venta-info\"><strong>Before sales open:</strong> this page will state shipping territories, estimated preparation and delivery times, the returns policy, and how taxes are shown at checkout.</p>", "shipping territories"),
}
for path, (old, new, marker) in product_notes.items():
    replace_once(path, old, new, marker)

# Provider-ready Follow OOLITA block; the later Cloudflare Follow layer upgrades
# this block when first-party storage is actually available.
follow_es = '''<section class="tramo env" id="seguir-oolita"><span class="rot">Seguir OOLITA</span><h2 class="grande">Una lista, cuando esté lista.</h2><p class="glosa">La lista de OOLITA reunirá noticias del mundo 3D, el libro, las publicaciones de campo y las ediciones textiles.</p><form class="oolita-follow" data-oolita-follow="pending" aria-describedby="seguir-estado" autocomplete="off"><label>Correo electrónico <input type="email" name="email" autocomplete="off" inputmode="email" autocapitalize="none" spellcheck="false" disabled></label><fieldset disabled><legend>Me interesa</legend><label><input type="checkbox" name="interest" value="3d"> Mundo 3D</label><label><input type="checkbox" name="interest" value="book"> Libro</label><label><input type="checkbox" name="interest" value="field"> Publicaciones de campo</label><label><input type="checkbox" name="interest" value="textile"> Ediciones textiles</label></fieldset><label><input type="checkbox" name="consent" disabled> Quiero recibir correos de OOLITA y podré darme de baja en cualquier momento.</label><button type="submit" disabled>Seguir OOLITA</button><p class="parr" id="seguir-estado">La suscripción se activará cuando el servicio de lista esté conectado. Mientras tanto, el contacto directo sigue siendo <a href="mailto:oolita@tutamail.com">oolita@tutamail.com</a>.</p></form></section>'''
follow_en = '''<section class="tramo env" id="follow-oolita"><span class="rot">Follow OOLITA</span><h2 class="grande">One list, when it is ready.</h2><p class="glosa">The OOLITA list will bring together news about the 3D world, the book, field publications and textile editions.</p><form class="oolita-follow" data-oolita-follow="pending" aria-describedby="follow-status" autocomplete="off"><label>Email <input type="email" name="email" autocomplete="off" inputmode="email" autocapitalize="none" spellcheck="false" disabled></label><fieldset disabled><legend>I am interested in</legend><label><input type="checkbox" name="interest" value="3d"> 3D world</label><label><input type="checkbox" name="interest" value="book"> Book</label><label><input type="checkbox" name="interest" value="field"> Field publications</label><label><input type="checkbox" name="interest" value="textile"> Textile editions</label></fieldset><label><input type="checkbox" name="consent" disabled> I want to receive OOLITA emails and can unsubscribe at any time.</label><button type="submit" disabled>Follow OOLITA</button><p class="parr" id="follow-status">Signup will be activated when the mailing-list service is connected. Until then, direct contact remains <a href="mailto:oolita@tutamail.com">oolita@tutamail.com</a>.</p></form></section>'''
for path, block, marker in [("index.html", follow_es, 'id="seguir-oolita"'), ("en/index.html", follow_en, 'id="follow-oolita"')]:
    p, s = read(path)
    if marker not in s:
        if "</main>" not in s:
            raise SystemExit(f"No </main> in {path}")
        p.write_text(s.replace("</main>", block + "\n</main>", 1), encoding="utf-8")
        print(f"list completion added Follow OOLITA block to {path}")

# Explicit event names on key navigation routes.
EVENT_LINKS = {
    "index.html": [('href="/cabo-de-gata/"', 'data-oolita-event="home-cabo-de-gata" href="/cabo-de-gata/"'), ('href="/ediciones/"', 'data-oolita-event="home-editions" href="/ediciones/"'), ('href="/domingos/"', 'data-oolita-event="home-sundays" href="/domingos/"')],
    "en/index.html": [('href="/en/cabo-de-gata/"', 'data-oolita-event="home-cabo-de-gata" href="/en/cabo-de-gata/"'), ('href="/en/editions/"', 'data-oolita-event="home-editions" href="/en/editions/"'), ('href="/en/sundays/"', 'data-oolita-event="home-sundays" href="/en/sundays/"')],
}
for path, changes in EVENT_LINKS.items():
    p, s = read(path)
    changed = False
    for old, new in changes:
        if new in s:
            continue
        if old not in s:
            raise SystemExit(f"Missing analytics link in {path}: {old}")
        s = s.replace(old, new, 1)
        changed = True
    if changed:
        p.write_text(s, encoding="utf-8")
        print(f"list completion instrumented {path}")

# Vendor-neutral event layer: emits CustomEvents and pushes to dataLayer if/when
# an analytics provider is attached. It does not claim central collection yet.
analytics_js = r'''<script id="oolita-event-layer">(function(){function emit(name,el){var detail={event:name,path:location.pathname,href:el&&el.href?el.href:null};window.dispatchEvent(new CustomEvent('oolita:event',{detail:detail}));window.dataLayer=window.dataLayer||[];window.dataLayer.push(Object.assign({event:'oolita_event'},detail));}document.addEventListener('click',function(e){var a=e.target.closest('[data-oolita-event]');if(a)emit(a.getAttribute('data-oolita-event'),a);});window.dispatchEvent(new CustomEvent('oolita:pageview',{detail:{path:location.pathname}}));})();</script>'''
for p in ROOT.rglob("index.html"):
    s = p.read_text(encoding="utf-8")
    if 'id="oolita-event-layer"' in s or "</body>" not in s:
        continue
    p.write_text(s.replace("</body>", analytics_js + "\n</body>", 1), encoding="utf-8")

# Quiet collaborator/stockist footer route.
footer_links = {"index.html": '<span class="rot"><a href="/colaborar/">Para colaboradores / puntos de venta</a></span>', "en/index.html": '<span class="rot"><a href="/en/work-with-oolita/">For collaborators / stockists</a></span>'}
for path, link in footer_links.items():
    p, s = read(path)
    if link in s:
        continue
    marker = "</div></div></footer>"
    if marker not in s:
        raise SystemExit(f"Footer shell not found in {path}")
    p.write_text(s.replace(marker, link + marker, 1), encoding="utf-8")
    print(f"list completion added footer collaborator link to {path}")

required = {
    "index.html": ["proyecto editorial y de trabajo de campo", 'href="/cabo-de-gata/"', 'id="seguir-oolita"', 'data-oolita-event="home-cabo-de-gata"'],
    "en/index.html": ["place-based publishing and fieldwork project", 'href="/en/cabo-de-gata/"', 'id="follow-oolita"', 'data-oolita-event="home-cabo-de-gata"'],
    "ediciones/index.html": ["Avísame cuando empiecen las publicaciones de campo"],
    "en/editions/index.html": ["Tell me when field publications begin"],
    "ediciones/libro/index.html": ["destinos de envío"],
    "en/editions/book/index.html": ["shipping territories"],
}
for path, needles in required.items():
    _, s = read(path)
    for needle in needles:
        if needle not in s:
            raise SystemExit(f"List-completion invariant missing in {path}: {needle}")
for path in ("index.html", "en/index.html"):
    _, s = read(path)
    if 'data-oolita-follow="pending"' not in s and 'data-oolita-follow="cloudflare"' not in s:
        raise SystemExit(f"Follow OOLITA must be pending or Cloudflare-managed in {path}")

print("OOLITA improvement-list completion layer validated successfully.")
