#!/usr/bin/env python3
"""Polish the three OOLITA pages still below the current SEO/content standard.

Runs near the end of the reader-facing pipeline so titles, descriptions,
hreflang and the About-page editorial addition survive mirrored-origin rebuilds.
The pass is intentionally narrow and idempotent.
"""
from __future__ import annotations

from html import escape
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
BASE = "https://oolita.es"
LASTMOD = "2026-08-24"

if not ROOT.is_dir():
    raise SystemExit(f"Missing built site: {ROOT}")

PAGES = {
    "mundo-3d/index.html": {
        "route": "/mundo-3d/",
        "title": "Mundo 3D de OOLITA · Los Escullos en el navegador",
        "description": "La tercera forma de OOLITA: un mundo 3D de Los Escullos hecho en Three.js para recorrer el mismo camino desde el navegador.",
        "es": "/mundo-3d/",
        "en": "/en/3d-world/",
    },
    "en/3d-world/index.html": {
        "route": "/en/3d-world/",
        "title": "OOLITA 3D world · Los Escullos in the browser",
        "description": "OOLITA’s third form: a Three.js world of Los Escullos, built to walk the same path in the browser with no download or account.",
        "es": "/mundo-3d/",
        "en": "/en/3d-world/",
    },
}

ABOUT_REL = "sobre-oolita/index.html"
ABOUT_ROUTE = "/sobre-oolita/"
ABOUT_BLOCK = '''<section class="tramo env" data-seo-place="about">
<span class="rot">Los Escullos</span><h2 class="grande">El lugar no es un fondo.</h2>
<p class="parr">El <a href="/laberinto/">laberinto de Los Escullos</a> está dentro del Parque Natural Cabo de Gata-Níjar, sobre una duna fósil frente al Mediterráneo. Ese suelo, su geología y la luz del lugar no son decorado. Son parte de cómo nació la obra y de por qué sigue allí.</p>
<p class="parr">Desde 2021 vuelvo al mismo punto para mirar qué cambia y qué permanece: la piedra, el viento, las huellas, el paso de la gente, el propio dibujo. OOLITA crece desde esa repetición. No intenta convertir <a href="/cabo-de-gata/">Cabo de Gata</a> en una marca. Intenta mantener una relación concreta con un lugar y dejar que cada material —piedra, papel o código— conserve algo de esa relación.</p>
</section>'''


def read(rel: str) -> tuple[Path, str]:
    path = ROOT / rel
    if not path.is_file():
        raise SystemExit(f"Missing SEO polish page: {rel}")
    return path, path.read_text(encoding="utf-8")


def set_title(text: str, title: str, rel: str) -> str:
    replacement = f"<title>{escape(title)}</title>"
    text, count = re.subn(r"<title>[\s\S]*?</title>", replacement, text, count=1, flags=re.I)
    if count != 1:
        raise SystemExit(f"Expected one title in {rel}; replaced {count}")
    return text


def set_meta(text: str, attr: str, key: str, value: str, rel: str) -> str:
    pattern = rf'<meta\b(?=[^>]*\b{re.escape(attr)}=["\']{re.escape(key)}["\'])[^>]*>'
    replacement = f'<meta {attr}="{key}" content="{escape(value, quote=True)}">'
    if re.search(pattern, text, flags=re.I):
        return re.sub(pattern, replacement, text, count=1, flags=re.I)
    if "</head>" not in text:
        raise SystemExit(f"Missing </head> while setting {key} in {rel}")
    return text.replace("</head>", replacement + "\n</head>", 1)


def set_hreflang(text: str, es_route: str, en_route: str, rel: str) -> str:
    text = re.sub(
        r'<link\b(?=[^>]*\brel=["\']alternate["\'])(?=[^>]*\bhreflang=["\'][^"\']+["\'])[^>]*>\s*',
        "",
        text,
        flags=re.I,
    )
    canonical = re.search(r'<link\b(?=[^>]*\brel=["\']canonical["\'])[^>]*>', text, flags=re.I)
    if not canonical:
        raise SystemExit(f"Canonical link missing in {rel}")
    block = (
        f'<link rel="alternate" hreflang="es" href="{BASE}{es_route}">\n'
        f'<link rel="alternate" hreflang="en" href="{BASE}{en_route}">\n'
        f'<link rel="alternate" hreflang="x-default" href="{BASE}{es_route}">'
    )
    return text[:canonical.end()] + "\n" + block + text[canonical.end():]


changed_routes: set[str] = set()

for rel, spec in PAGES.items():
    path, text = read(rel)
    before = text
    text = set_title(text, spec["title"], rel)
    text = set_meta(text, "name", "description", spec["description"], rel)
    text = set_meta(text, "property", "og:title", spec["title"], rel)
    text = set_meta(text, "property", "og:description", spec["description"], rel)
    text = set_meta(text, "name", "twitter:title", spec["title"], rel)
    text = set_meta(text, "name", "twitter:description", spec["description"], rel)
    text = set_hreflang(text, spec["es"], spec["en"], rel)
    if text != before:
        path.write_text(text, encoding="utf-8")
        changed_routes.add(spec["route"])

# Add one concrete, place-based section to the Spanish About page. Replace our
# own prior block if present so repeated deployment runs remain stable.
about_path, about = read(ABOUT_REL)
before_about = about
about = re.sub(
    r'<section\b[^>]*data-seo-place=["\']about["\'][^>]*>[\s\S]*?</section>\s*',
    "",
    about,
    flags=re.I,
)
anchor = re.search(
    r'<section\b[^>]*>[\s\S]{0,700}?<span\b[^>]*class=["\'][^"\']*\brot\b[^"\']*["\'][^>]*>\s*Raquel Costantini\s*</span>',
    about,
    flags=re.I,
)
if anchor:
    about = about[:anchor.start()] + ABOUT_BLOCK + "\n" + about[anchor.start():]
else:
    footer = re.search(r"<footer\b", about, flags=re.I)
    if not footer:
        raise SystemExit("Could not locate About insertion point or footer")
    about = about[:footer.start()] + ABOUT_BLOCK + "\n" + about[footer.start():]
if about != before_about:
    about_path.write_text(about, encoding="utf-8")
    changed_routes.add(ABOUT_ROUTE)

# Give the changed routes a current sitemap lastmod so the deploy's IndexNow
# submission and subsequent crawls receive an accurate freshness signal.
sitemap = ROOT / "sitemap.xml"
if not sitemap.is_file():
    raise SystemExit("Missing sitemap.xml")
ET.register_namespace("", "http://www.sitemaps.org/schemas/sitemap/0.9")
tree = ET.parse(sitemap)
root = tree.getroot()
ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
seen: set[str] = set()
for url_el in root.findall("sm:url", ns):
    loc = url_el.find("sm:loc", ns)
    if loc is None or not loc.text:
        continue
    url = loc.text.strip()
    if not url.startswith(BASE):
        continue
    route = url[len(BASE):] or "/"
    if route not in changed_routes:
        continue
    seen.add(route)
    lastmod = url_el.find("sm:lastmod", ns)
    if lastmod is None:
        lastmod = ET.SubElement(url_el, "{http://www.sitemaps.org/schemas/sitemap/0.9}lastmod")
    lastmod.text = LASTMOD

missing = changed_routes - seen
if missing:
    raise SystemExit(f"Changed SEO routes missing from sitemap: {sorted(missing)}")
tree.write(sitemap, encoding="utf-8", xml_declaration=True)

# Narrow final checks: titles/descriptions are substantive, hreflang is singular,
# and the About addition contains the intended internal paths.
for rel, spec in PAGES.items():
    _, text = read(rel)
    if f"<title>{escape(spec['title'])}</title>" not in text:
        raise SystemExit(f"Final title missing in {rel}")
    if spec["description"] not in text and escape(spec["description"], quote=True) not in text:
        raise SystemExit(f"Final description missing in {rel}")
    alternate_tags = re.findall(
        r'<link\b(?=[^>]*\brel=["\']alternate["\'])[^>]*>',
        text,
        flags=re.I,
    )
    hreflangs = []
    for tag in alternate_tags:
        match = re.search(r'\bhreflang=["\']([^"\']+)["\']', tag, flags=re.I)
        if match:
            hreflangs.append(match.group(1).lower())
    if hreflangs.count("es") != 1 or hreflangs.count("en") != 1 or hreflangs.count("x-default") != 1 or len(hreflangs) != 3:
        raise SystemExit(f"Hreflang link count wrong in {rel}: {hreflangs}")

_, about = read(ABOUT_REL)
if about.count('data-seo-place="about"') != 1:
    raise SystemExit("About place section count wrong")
for href in ('href="/laberinto/"', 'href="/cabo-de-gata/"'):
    if href not in about:
        raise SystemExit(f"About internal link missing: {href}")

print("OOLITA three-page SEO/content polish installed and validated.")
