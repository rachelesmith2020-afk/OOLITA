#!/usr/bin/env python3
"""Add the bilingual OOLITA 3D-world explainer and permanent homepage routes.

Runs after the accessibility/audit pass so the generated pages inherit the
current audited visual shell, footer credits, language treatment and styles.
The pass is idempotent against a mirrored origin that already contains the
3D-world pages and links from an earlier deployment.
"""
from __future__ import annotations

from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
BASE = "https://oolita.es"
LASTMOD = "2026-08-23"


def read(path: str) -> tuple[Path, str]:
    p = ROOT / path
    if not p.is_file():
        raise SystemExit(f"Missing page: {path}")
    return p, p.read_text(encoding="utf-8")


def write(path: str, text: str) -> None:
    p = ROOT / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def set_meta(text: str, attr: str, key: str, value: str, *, page: str) -> str:
    pattern = rf'<meta\s+{re.escape(attr)}=["\']{re.escape(key)}["\'][^>]*>'
    tag = f'<meta {attr}="{key}" content="{value}">'
    if re.search(pattern, text, flags=re.I):
        return re.sub(pattern, tag, text, count=1, flags=re.I)
    if "</head>" not in text:
        raise SystemExit(f"Missing </head> while setting {key} in {page}")
    return text.replace("</head>", tag + "\n</head>", 1)


def make_page(
    source: str,
    dest: str,
    *,
    title: str,
    description: str,
    canonical: str,
    alt_es: str,
    alt_en: str,
    old_counterpart: str,
    new_counterpart: str,
    main_html: str,
) -> None:
    _, text = read(source)

    # Do not inherit source-page structured data that would describe the About page.
    text = re.sub(
        r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>[\s\S]*?</script>\s*',
        "",
        text,
        flags=re.I,
    )
    text = re.sub(r'<meta\s+property=["\']article:[^>]+>\s*', "", text, flags=re.I)

    text, count = re.subn(
        r"<title>[\s\S]*?</title>",
        f"<title>{title}</title>",
        text,
        count=1,
        flags=re.I,
    )
    if count != 1:
        raise SystemExit(f"Missing title in source while generating {dest}")

    text = set_meta(text, "name", "description", description, page=dest)
    for attr, key, value in [
        ("property", "og:type", "website"),
        ("property", "og:title", title),
        ("property", "og:description", description),
        ("property", "og:url", canonical),
        ("property", "og:image", f"{BASE}/og.png"),
        ("property", "og:image:secure_url", f"{BASE}/og.png"),
        ("name", "twitter:title", title),
        ("name", "twitter:description", description),
        ("name", "twitter:image", f"{BASE}/og.png"),
    ]:
        text = set_meta(text, attr, key, value, page=dest)

    canonical_tag = f'<link rel="canonical" href="{canonical}">'
    if re.search(r'<link\s+rel=["\']canonical["\'][^>]*>', text, flags=re.I):
        text = re.sub(
            r'<link\s+rel=["\']canonical["\'][^>]*>',
            canonical_tag,
            text,
            count=1,
            flags=re.I,
        )
    elif "</head>" in text:
        text = text.replace("</head>", canonical_tag + "\n</head>", 1)
    else:
        raise SystemExit(f"Missing </head> while setting canonical in {dest}")

    text = re.sub(r'<link\s+rel=["\']alternate["\'][^>]*hreflang=[^>]+>\s*', "", text, flags=re.I)
    alternates = (
        f'<link rel="alternate" hreflang="es" href="{alt_es}">\n'
        f'<link rel="alternate" hreflang="en" href="{alt_en}">\n'
        f'<link rel="alternate" hreflang="x-default" href="{alt_es}">'
    )
    if canonical_tag not in text:
        raise SystemExit(f"Canonical tag missing after rewrite in {dest}")
    text = text.replace(canonical_tag, canonical_tag + "\n" + alternates, 1)

    if old_counterpart in text:
        text = text.replace(old_counterpart, new_counterpart)
    elif new_counterpart not in text:
        raise SystemExit(f"Language counterpart route missing in source for {dest}")

    match = re.search(r'(<main\b[^>]*>)[\s\S]*?</main>', text, flags=re.I)
    if not match:
        raise SystemExit(f"Missing <main> shell while generating {dest}")
    replacement = match.group(1) + main_html + "</main>"
    text = text[: match.start()] + replacement + text[match.end() :]

    write(dest, text)
    print(f"3D world generated {dest}")


main_es = '''<section class="hero"><span class="rot">Mundo 3D · 03.01.27</span><h1 class="grande">La misma senda, reconstruida con luz.</h1><p class="glosa">La tercera forma de OOLITA está hecha en código. No es una imagen del laberinto para mirar desde fuera: está construida para recorrerla — un camino hacia dentro, un centro y el mismo camino de regreso.</p></section>
<section class="tramo"><span class="rot">Por qué código</span><h2 class="grande">Un lugar que puede llegar hasta ti.</h2><p class="parr">El laberinto de piedra pertenece a un lugar preciso: Los Escullos, sobre una duna fósil junto al Mediterráneo. No todo el mundo puede llegar hasta allí. El mundo digital no intenta sustituir ese lugar; da al mismo recorrido otro material, para que la distancia, el dinero o las posibilidades del cuerpo no decidan quién puede caminarlo.</p><p class="parr">Funciona directamente en el navegador: sin descarga y sin cuenta. Un enlace basta para entrar.</p></section>
<section class="tramo env"><span class="rot">Three.js</span><h2 class="grande">El navegador como material.</h2><p class="parr">El mundo se construye con <strong>Three.js</strong>, una biblioteca de JavaScript para crear escenas tridimensionales en el navegador. Three.js no es el tema de OOLITA ni un efecto añadido a la obra: es la herramienta que permite que su tercera forma exista como espacio caminable en la web.</p><p class="parr">La elección importa porque mantiene la entrada sencilla. El trabajo no necesita una aplicación propia ni una instalación: vive donde ya está oolita.es.</p></section>
<section class="tramo"><span class="rot">Los Escullos</span><h2 class="grande">Reconstruir, no copiar.</h2><p class="parr">El paisaje parte de mediciones del terreno real, pero no busca una réplica fotográfica. Piedra, mar, escala, horizonte, sonido y la luz baja de Cabo de Gata se reducen a lo que necesita el recorrido. El objetivo no es el realismo técnico por sí mismo, sino conservar suficiente lugar para que la atención pueda ir más despacio.</p></section>
<section class="tramo env"><span class="rot">Piedra · papel · código</span><h2 class="grande">Tres materiales, una obra.</h2><p class="parr">La piedra es el laberinto original de Los Escullos. El papel es la fábula bilingüe. El código es este mundo caminable. Ninguno reemplaza a los otros: cada uno hace posible una forma distinta de recorrer la misma senda.</p><a class="fila" href="/laberinto/"><span class="n">01</span><span class="nom">El laberinto</span><span class="glo">Piedra · Los Escullos · 2021</span></a><a class="fila" href="/ediciones/libro/"><span class="n">02</span><span class="nom">El libro</span><span class="glo">Papel · fábula bilingüe · 31.01.27</span></a><a class="fila" href="/"><span class="n">03</span><span class="nom">El mundo 3D</span><span class="glo">Código · Three.js · abre 03.01.27</span></a></section>'''

main_en = '''<section class="hero"><span class="rot">3D world · 03.01.27</span><h1 class="grande">The same path, rebuilt in light.</h1><p class="glosa">The third form of OOLITA is made in code. It is not an image of the labyrinth to look at from outside: it is being built to be walked — one path inward, one centre and the same path back out.</p></section>
<section class="tramo"><span class="rot">Why code</span><h2 class="grande">A place that can reach you.</h2><p class="parr">The stone labyrinth belongs to a precise place: Los Escullos, on a fossil dune beside the Mediterranean. Not everyone can get there. The digital world does not try to replace that place; it gives the same path another material, so distance, money or physical access do not decide who can walk it.</p><p class="parr">It runs directly in the browser: no download and no account. A link is enough to enter.</p></section>
<section class="tramo env"><span class="rot">Three.js</span><h2 class="grande">The browser as material.</h2><p class="parr">The world is built with <strong>Three.js</strong>, a JavaScript library for creating three-dimensional scenes in the browser. Three.js is not the subject of OOLITA and it is not an effect added to the work: it is the tool that allows its third form to exist as a walkable space on the web.</p><p class="parr">That choice matters because it keeps the entrance simple. The work does not need its own app or an installation: it lives where oolita.es already lives.</p></section>
<section class="tramo"><span class="rot">Los Escullos</span><h2 class="grande">Reconstruct, not copy.</h2><p class="parr">The landscape begins with measurements of the real terrain, but it is not trying to be a photographic replica. Stone, sea, scale, horizon, sound and the low light of Cabo de Gata are reduced to what the walk needs. The aim is not technical realism for its own sake, but to preserve enough of the place for attention to slow down.</p></section>
<section class="tramo env"><span class="rot">Stone · paper · code</span><h2 class="grande">Three materials, one work.</h2><p class="parr">Stone is the original labyrinth at Los Escullos. Paper is the bilingual fable. Code is this walkable world. None replaces the others: each makes a different way of following the same path possible.</p><a class="fila" href="/en/labyrinth/"><span class="n">01</span><span class="nom">The labyrinth</span><span class="glo">Stone · Los Escullos · 2021</span></a><a class="fila" href="/en/editions/book/"><span class="n">02</span><span class="nom">The book</span><span class="glo">Paper · bilingual fable · 31.01.27</span></a><a class="fila" href="/en/"><span class="n">03</span><span class="nom">The 3D world</span><span class="glo">Code · Three.js · opens 03.01.27</span></a></section>'''

make_page(
    "sobre-oolita/index.html",
    "mundo-3d/index.html",
    title="El mundo 3D · OOLITA",
    description="Por qué la tercera forma de OOLITA está hecha con Three.js: un mundo caminable de Los Escullos que vive directamente en el navegador.",
    canonical=f"{BASE}/mundo-3d/",
    alt_es=f"{BASE}/mundo-3d/",
    alt_en=f"{BASE}/en/3d-world/",
    old_counterpart="/en/about/",
    new_counterpart="/en/3d-world/",
    main_html=main_es,
)
make_page(
    "en/about/index.html",
    "en/3d-world/index.html",
    title="The 3D world · OOLITA",
    description="Why OOLITA's third form is built with Three.js: a walkable world of Los Escullos that lives directly in the browser.",
    canonical=f"{BASE}/en/3d-world/",
    alt_es=f"{BASE}/mundo-3d/",
    alt_en=f"{BASE}/en/3d-world/",
    old_counterpart="/sobre-oolita/",
    new_counterpart="/mundo-3d/",
    main_html=main_en,
)


# Add one permanent row to the homepage directory. Keep the existing numeric
# sequence untouched because earlier audited passes intentionally reserve
# Contact as row 14; "3D" is a meaningful label rather than another number.
for path, href, label, gloss, contact_label in [
    ("index.html", "/mundo-3d/", "El mundo 3D", "Código · Three.js · abre 03.01.27", "Contacto"),
    ("en/index.html", "/en/3d-world/", "The 3D world", "Code · Three.js · opens 03.01.27", "Contact"),
]:
    p, text = read(path)
    marker = f'href="{href}"'
    if marker not in text:
        addition = (
            f'<a class="fila" data-oolita-event="home-3d-world" href="{href}">'
            f'<span class="n">3D</span><span class="nom">{label}</span>'
            f'<span class="glo">{gloss}</span></a>\n  '
        )
        contact_pattern = (
            r'((?:<!--email_off-->)?<a class="fila" href="mailto:oolita@tutamail\.com">'
            r'<span class="n">14</span><span class="nom">' + re.escape(contact_label) + r'</span>)'
        )
        match = re.search(contact_pattern, text)
        if not match:
            raise SystemExit(f"Homepage Contact row 14 missing while adding 3D directory link in {path}")
        text = text[: match.start()] + addition + text[match.start() :]
        p.write_text(text, encoding="utf-8")
        print(f"3D world added homepage directory link to {path}")


# Give the existing 'three materials' section a direct route to the explainer.
for path, href, paragraph_pattern, label, gloss in [
    (
        "index.html",
        "/mundo-3d/",
        r'(<p class="parr">El tercero abre el 3 de enero de 2027[\s\S]*?</p>)',
        "Por qué está hecho en código",
        "Three.js · el navegador como material",
    ),
    (
        "en/index.html",
        "/en/3d-world/",
        r'(<p class="parr">The third opens on 3 January 2027[\s\S]*?</p>)',
        "Why it is built in code",
        "Three.js · the browser as material",
    ),
]:
    p, text = read(path)
    event_marker = 'data-oolita-event="home-3d-world-material"'
    if event_marker not in text:
        match = re.search(paragraph_pattern, text, flags=re.I)
        if not match:
            raise SystemExit(f"Three-materials paragraph missing in {path}")
        row = (
            f'<a class="fila" data-oolita-event="home-3d-world-material" href="{href}">'
            f'<span class="n">→</span><span class="nom">{label}</span>'
            f'<span class="glo">{gloss}</span></a>'
        )
        text = text[: match.end()] + row + text[match.end() :]
        p.write_text(text, encoding="utf-8")
        print(f"3D world linked from three-materials section in {path}")


# Add the bilingual routes to the existing sitemap without disturbing entries
# managed by the earlier growth/search passes.
sitemap = ROOT / "sitemap.xml"
if not sitemap.is_file():
    raise SystemExit("Missing sitemap.xml")
ET.register_namespace("", "http://www.sitemaps.org/schemas/sitemap/0.9")
tree = ET.parse(sitemap)
root = tree.getroot()
ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
existing: dict[str, ET.Element] = {}
for url_el in root.findall("sm:url", ns):
    loc = url_el.find("sm:loc", ns)
    if loc is not None and loc.text:
        existing[loc.text.strip()] = url_el

for url in [f"{BASE}/mundo-3d/", f"{BASE}/en/3d-world/"]:
    url_el = existing.get(url)
    if url_el is None:
        url_el = ET.SubElement(root, "{http://www.sitemaps.org/schemas/sitemap/0.9}url")
        loc = ET.SubElement(url_el, "{http://www.sitemaps.org/schemas/sitemap/0.9}loc")
        loc.text = url
    lastmod = url_el.find("sm:lastmod", ns)
    if lastmod is None:
        lastmod = ET.SubElement(url_el, "{http://www.sitemaps.org/schemas/sitemap/0.9}lastmod")
    lastmod.text = LASTMOD

tree.write(sitemap, encoding="utf-8", xml_declaration=True)


required = {
    "index.html": ['href="/mundo-3d/"', 'data-oolita-event="home-3d-world-material"', '<span class="n">14</span><span class="nom">Contacto</span>'],
    "en/index.html": ['href="/en/3d-world/"', 'data-oolita-event="home-3d-world-material"', '<span class="n">14</span><span class="nom">Contact</span>'],
    "mundo-3d/index.html": ["Three.js", "La misma senda, reconstruida con luz.", f'{BASE}/mundo-3d/'],
    "en/3d-world/index.html": ["Three.js", "The same path, rebuilt in light.", f'{BASE}/en/3d-world/'],
}
for path, needles in required.items():
    _, text = read(path)
    for needle in needles:
        if needle not in text:
            raise SystemExit(f"3D-world invariant missing in {path}: {needle}")

sitemap_text = sitemap.read_text(encoding="utf-8")
for needle in [f"{BASE}/mundo-3d/", f"{BASE}/en/3d-world/"]:
    if needle not in sitemap_text:
        raise SystemExit(f"3D-world sitemap invariant missing: {needle}")

print("OOLITA 3D-world layer validated successfully.")
