#!/usr/bin/env python3
"""Replace the provider-ready disabled list form with a clean transitional CTA.

A real consent-based form will replace this once the mailing-list provider is
connected. Until then the public site stays honest and usable rather than
showing disabled controls.
"""
from pathlib import Path
from urllib.parse import quote
import re
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
EMAIL = "oolita@tutamail.com"


def mailto(subject, body):
    return f"mailto:{EMAIL}?subject={quote(subject)}&body={quote(body)}"


def swap(path, section_id, replacement, marker):
    p = ROOT / path
    if not p.is_file():
        raise SystemExit(f"Missing page: {path}")
    s = p.read_text(encoding="utf-8")
    if marker in s:
        print(f"follow transition already present {path}")
        return
    pattern = rf'<section class="tramo env" id="{re.escape(section_id)}">[\s\S]*?</section>'
    ns, n = re.subn(pattern, replacement, s, count=1)
    if n != 1:
        raise SystemExit(f"Could not replace Follow OOLITA block in {path}")
    p.write_text(ns, encoding="utf-8")
    print(f"follow transition patched {path}")

es = f'''<section class="tramo env" id="seguir-oolita" data-oolita-follow="pending"><span class="rot">Seguir OOLITA</span><h2 class="grande">Seguir el proyecto.</h2><p class="glosa">La lista reunirá noticias del mundo 3D, el libro, las publicaciones de campo y las ediciones textiles. El formulario de suscripción se activará cuando el servicio de lista esté conectado.</p><a class="fila" data-oolita-event="follow-email" href="{mailto('OOLITA · seguir el proyecto', 'Hola. Quiero seguir OOLITA. Me interesa: [mundo 3D / libro / publicaciones de campo / ediciones textiles].')}" rel="nofollow"><span class="n">→</span><span class="nom">Mientras tanto, escríbeme</span><span class="glo">{EMAIL}</span></a></section>'''
en = f'''<section class="tramo env" id="follow-oolita" data-oolita-follow="pending"><span class="rot">Follow OOLITA</span><h2 class="grande">Follow the project.</h2><p class="glosa">The list will bring together news about the 3D world, the book, field publications and textile editions. The signup form will be activated when the mailing-list service is connected.</p><a class="fila" data-oolita-event="follow-email" href="{mailto('OOLITA · follow the project', 'Hello. I want to follow OOLITA. I am interested in: [3D world / book / field publications / textile editions].')}" rel="nofollow"><span class="n">→</span><span class="nom">For now, write to me</span><span class="glo">{EMAIL}</span></a></section>'''

swap("index.html", "seguir-oolita", es, "Mientras tanto, escríbeme")
swap("en/index.html", "follow-oolita", en, "For now, write to me")

for path, needle in [("index.html", 'data-oolita-follow="pending"'), ("en/index.html", 'data-oolita-follow="pending"')]:
    s = (ROOT / path).read_text(encoding="utf-8")
    if needle not in s or 'data-oolita-event="follow-email"' not in s:
        raise SystemExit(f"Follow transition invariant missing in {path}")
    if '<input type="email"' in s:
        raise SystemExit(f"Disabled email form should not be public in {path}")

print("OOLITA Follow transition validated successfully.")
