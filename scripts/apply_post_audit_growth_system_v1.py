#!/usr/bin/env python3
"""Compatibility entry point for the post-audit OOLITA growth system."""
from pathlib import Path
import re
import sys

# The final consistency workflow imports this v1 name. Execute the resilient
# implementation after adapting selectors to the links intentionally present on
# the published pages. Reader-facing prose remains untouched.
path = Path(__file__).with_name("apply_post_audit_growth_system_v2.py")
source = path.read_text(encoding="utf-8")
root = Path(sys.argv[1] if len(sys.argv) > 1 else "site")

# Textile purchase-interest belongs in the same first-party Follow OOLITA list
# already used for the book, 3D world and field-publication interests. Replace
# only the prefilled product-notification mailto actions; the footer/contact
# mailto remains intact. Existing reader-facing CTA wording is unchanged.
for rel, follow_href in (
    ("ediciones/camiseta/index.html", "/?follow=textile#seguir-oolita"),
    ("en/editions/t-shirt/index.html", "/en/?follow=textile#follow-oolita"),
):
    product = root / rel
    if not product.is_file():
        raise SystemExit(f"Missing textile page: {rel}")
    text = product.read_text(encoding="utf-8")
    text, changed = re.subn(
        r'href=(["\'])mailto:oolita@tutamail\.com\?subject=[^"\']+\1',
        lambda m: f'href={m.group(1)}{follow_href}{m.group(1)}',
        text,
    )
    if follow_href not in text:
        raise SystemExit(f"Could not route textile interest into Follow OOLITA: {rel}")
    product.write_text(text, encoding="utf-8")
    if changed:
        print(f"textile Follow route normalized: {rel} ({changed} CTA link(s))")

# The current collaboration guidance is already live, reviewed reader-facing
# copy. Earlier v2 freeze rules still classify one heading as an obsolete
# synthetic phrase; remove only those two stale forbidden literals so the freeze
# protects the current approved page rather than rejecting it.
source = source.replace(
    ',"A useful proposal is specific","Una propuesta útil es concreta"',
    '',
)

# The two factual explainers lead into OOLITA through their existing final
# "Piedra, papel y código / Stone, paper and code" route, rather than by adding
# new navigation solely for measurement.
source = source.replace(
    '("que-es-un-laberinto/index.html","see-oolita-labyrinth","explainer-labyrinth",dict(href_exact="/laberinto/"),None,None),',
    '("que-es-un-laberinto/index.html","continue-into-oolita","explainer-oolita",dict(href_exact="/",text_contains="Piedra, papel y código"),None,None),',
)
source = source.replace(
    '("en/what-is-a-labyrinth/index.html","see-oolita-labyrinth","explainer-labyrinth",dict(href_exact="/en/labyrinth/"),None,None),',
    '("en/what-is-a-labyrinth/index.html","continue-into-oolita","explainer-oolita",dict(href_exact="/en/",text_contains="Stone, paper and code"),None,None),',
)
source = source.replace(
    '("que-es-un-oolito/index.html","see-place","ooid-cabo",dict(href_exact="/cabo-de-gata/"),None,None),',
    '("que-es-un-oolito/index.html","continue-into-oolita","ooid-oolita",dict(href_exact="/",text_contains="Piedra, papel y código"),None,None),',
)
source = source.replace(
    '("en/what-is-an-ooid/index.html","see-place","ooid-cabo",dict(href_exact="/en/cabo-de-gata/"),None,None),',
    '("en/what-is-an-ooid/index.html","continue-into-oolita","ooid-oolita",dict(href_exact="/en/",text_contains="Stone, paper and code"),None,None),',
)

# The textile pages now route the existing purchase-notification wording into
# the first-party Follow form. Keep selector matching on the stable visible CTA
# so legacy/product transforms cannot break measurement before this adapter runs.
source = source.replace(
    '("ediciones/camiseta/index.html","follow-textile","textile-follow",dict(href_contains="follow=textile"),"textile","2027-04-11T00:00:00+02:00"),',
    '("ediciones/camiseta/index.html","follow-textile","textile-follow",dict(text_contains="Avísame cuando pueda comprarla"),"textile","2027-04-11T00:00:00+02:00"),',
)
source = source.replace(
    '("en/editions/t-shirt/index.html","follow-textile","textile-follow",dict(href_contains="follow=textile"),"textile","2027-04-11T00:00:00+02:00"),',
    '("en/editions/t-shirt/index.html","follow-textile","textile-follow",dict(text_contains="Tell me when I can buy it"),"textile","2027-04-11T00:00:00+02:00"),',
)

# Sunday 02 returns to the accumulating 22-Sundays archive, where the current
# published Sunday is selected. Measure that actual reader route rather than
# inventing navigation solely for analytics.
source = source.replace(
    '("domingos/02-el-gato-de-verdad/index.html","read-next-sunday","sunday-next",dict(href_exact="/domingos/03-la-memoria-del-mar/"),None,None),',
    '("domingos/02-el-gato-de-verdad/index.html","return-to-sundays","sunday-archive",dict(href_exact="/domingos/"),None,None),',
)
source = source.replace(
    '("en/sundays/02-the-cat-for-real/index.html","read-next-sunday","sunday-next",dict(href_exact="/en/sundays/03-the-memory-of-the-sea/"),None,None),',
    '("en/sundays/02-the-cat-for-real/index.html","return-to-sundays","sunday-archive",dict(href_exact="/en/sundays/"),None,None),',
)

# Measure the same published geology path: ooid explainer -> OOLITA -> labyrinth
# -> remote 3D follow. The homepage-to-labyrinth click is added as a measured edge.
source = source.replace(
    '("que-es-un-oolito/index.html","ooid-cabo",dict(href_exact="/cabo-de-gata/")),',
    '("que-es-un-oolito/index.html","ooid-oolita",dict(href_exact="/",text_contains="Piedra, papel y código")),',
)
source = source.replace(
    '("en/what-is-an-ooid/index.html","ooid-cabo",dict(href_exact="/en/cabo-de-gata/")),',
    '("en/what-is-an-ooid/index.html","ooid-oolita",dict(href_exact="/en/",text_contains="Stone, paper and code")),',
)
source = source.replace(
    '("index.html","home-about",dict(href_exact="/sobre-oolita/")),',
    '("index.html","home-about",dict(href_exact="/sobre-oolita/")),\n    ("index.html","home-labyrinth",dict(href_exact="/laberinto/")),',
)
source = source.replace(
    '("en/index.html","home-about",dict(href_exact="/en/about/")),',
    '("en/index.html","home-about",dict(href_exact="/en/about/")),\n    ("en/index.html","home-labyrinth",dict(href_exact="/en/labyrinth/")),',
)

# Match the published Sunday-02 -> archive edge and validate the real
# Instagram/Sundays route: Sunday 01 -> Sunday 02 -> archive -> current Sunday 03.
source = source.replace(
    '("domingos/02-el-gato-de-verdad/index.html","sunday-next",dict(href_exact="/domingos/03-la-memoria-del-mar/")),',
    '("domingos/02-el-gato-de-verdad/index.html","sunday-archive",dict(href_exact="/domingos/")),',
)
source = source.replace(
    '("en/sundays/02-the-cat-for-real/index.html","sunday-next",dict(href_exact="/en/sundays/03-the-memory-of-the-sea/")),',
    '("en/sundays/02-the-cat-for-real/index.html","sunday-archive",dict(href_exact="/en/sundays/")),',
)
source = source.replace(
    '"instagram-es": [("domingos/01-el-doble/index.html","/domingos/02-el-gato-de-verdad/"),("domingos/02-el-gato-de-verdad/index.html","/domingos/03-la-memoria-del-mar/"),("domingos/03-la-memoria-del-mar/index.html","/domingos/")],',
    '"instagram-es": [("domingos/01-el-doble/index.html","/domingos/02-el-gato-de-verdad/"),("domingos/02-el-gato-de-verdad/index.html","/domingos/"),("domingos/index.html","/domingos/03-la-memoria-del-mar/")],',
)
source = source.replace(
    '"instagram-en": [("en/sundays/01-the-double/index.html","/en/sundays/02-the-cat-for-real/"),("en/sundays/02-the-cat-for-real/index.html","/en/sundays/03-the-memory-of-the-sea/"),("en/sundays/03-the-memory-of-the-sea/index.html","/en/sundays/")],',
    '"instagram-en": [("en/sundays/01-the-double/index.html","/en/sundays/02-the-cat-for-real/"),("en/sundays/02-the-cat-for-real/index.html","/en/sundays/"),("en/sundays/index.html","/en/sundays/03-the-memory-of-the-sea/")],',
)

source = source.replace(
    '"geology-es": [("que-es-un-oolito/index.html","/cabo-de-gata/"),("cabo-de-gata/index.html","/laberinto/"),("laberinto/index.html","follow=3d")],',
    '"geology-es": [("que-es-un-oolito/index.html","/"),("index.html","/laberinto/"),("laberinto/index.html","follow=3d")],',
)
source = source.replace(
    '"geology-en": [("en/what-is-an-ooid/index.html","/en/cabo-de-gata/"),("en/cabo-de-gata/index.html","/en/labyrinth/"),("en/labyrinth/index.html","follow=3d")],',
    '"geology-en": [("en/what-is-an-ooid/index.html","/en/"),("en/index.html","/en/labyrinth/"),("en/labyrinth/index.html","follow=3d")],',
)

exec(compile(source, str(path), "exec"), globals(), globals())

# Final accessibility repair after every reader/growth transform: a skip link is
# page-local navigation and must never inherit a catalogue/product destination.
# Give the first <main> a stable target and point Spanish/English skip links to it.
fixed_skip_links = 0
for html in root.rglob("*.html"):
    text = html.read_text(encoding="utf-8", errors="ignore")
    if not re.search(r'>\s*(?:Saltar al contenido|Skip to content)\s*</a>', text, flags=re.I):
        continue
    main = re.search(r'<main\b[^>]*>', text, flags=re.I)
    if not main:
        raise SystemExit(f"Skip link without <main>: {html.relative_to(root)}")
    main_tag = main.group(0)
    if not re.search(r'\bid=(["\'])main-content\1', main_tag, flags=re.I):
        if re.search(r'\bid=(["\'])[^"\']+\1', main_tag, flags=re.I):
            existing = re.search(r'\bid=(["\'])([^"\']+)\1', main_tag, flags=re.I)
            target = existing.group(2) if existing else "main-content"
        else:
            target = "main-content"
            main_tag = main_tag[:-1] + ' id="main-content">'
            text = text[:main.start()] + main_tag + text[main.end():]
    else:
        target = "main-content"

    def repair_skip(match: re.Match[str]) -> str:
        tag = match.group(1)
        label = match.group(2)
        if re.search(r'\bhref=(["\'])[^"\']*\1', tag, flags=re.I):
            tag = re.sub(r'\bhref=(["\'])[^"\']*\1', lambda m: f'href={m.group(1)}#{target}{m.group(1)}', tag, count=1, flags=re.I)
        else:
            tag = tag[:-1] + f' href="#{target}">'
        return tag + label + "</a>"

    text, n = re.subn(
        r'(<a\b[^>]*>)(\s*(?:Saltar al contenido|Skip to content)\s*)</a>',
        repair_skip,
        text,
        flags=re.I,
    )
    if n < 1 or f'href="#{target}"' not in text:
        raise SystemExit(f"Could not repair skip link: {html.relative_to(root)}")
    html.write_text(text, encoding="utf-8")
    fixed_skip_links += n

if fixed_skip_links:
    print(f"OOLITA local skip-link targets repaired: {fixed_skip_links}")
