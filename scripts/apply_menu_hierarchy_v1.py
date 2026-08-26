#!/usr/bin/env python3
"""Reduce cognitive flattening in the homepage secondary navigation.

The three primary OOLITA entrances (01–03) already have their own visual class
and remain untouched. This pass groups the long secondary run without changing
current first-party link targets, numbering, credits or the wider visual system.
It also gives that existing index one stable anchor so internal pages can point
back to it without adding a conventional global menu.
"""
from __future__ import annotations

from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
BASE = "https://oolita.es"
LASTMOD = "2026-08-26"
CHANGED_PATHS = {"/", "/en/"}
INDEX_ID = "oolita-index"

STYLE = '''<style id="oolita-menu-hierarchy-style">
.menu-group-label{display:block;margin:clamp(1.5rem,3vw,2.25rem) 0 .45rem;opacity:.58;font-size:.72rem;letter-spacing:.08em;text-transform:uppercase}
.menu-group-label + .fila{border-top-width:1px}
@media(max-width:640px){.menu-group-label{margin-top:1.4rem}}
</style>'''


def page(path: str) -> tuple[Path, str]:
    target = ROOT / path
    if not target.is_file():
        raise SystemExit(f"Missing homepage for menu hierarchy: {path}")
    return target, target.read_text(encoding="utf-8")


def insert_before_href(text: str, href: str, label: str) -> str:
    marker = f'<span class="rot menu-group-label">{label}</span>'
    if marker in text:
        return text
    pattern = rf'(<a\b[^>]*href=["\']{re.escape(href)}["\'][^>]*class=["\'][^"\']*fila[^"\']*["\'][^>]*>|<a\b[^>]*class=["\'][^"\']*fila[^"\']*["\'][^>]*href=["\']{re.escape(href)}["\'][^>]*>)'
    match = re.search(pattern, text, flags=re.I)
    if not match:
        raise SystemExit(f"Could not place menu group before {href}")
    return text[:match.start()] + marker + "\n" + text[match.start():]


def ensure_index_anchor(text: str, label: str) -> str:
    """Put one stable id on the existing Explore/Explorar OOLITA label."""
    id_token = f'id="{INDEX_ID}"'
    if id_token in text:
        if text.count(id_token) != 1:
            raise SystemExit(f"Duplicate homepage index id: {INDEX_ID}")
        return text

    pattern = re.compile(
        rf'(<span\b(?=[^>]*class=["\'][^"\']*\brot\b[^"\']*["\'])[^>]*)(>\s*{re.escape(label)}\s*</span>)',
        flags=re.I,
    )
    match = pattern.search(text)
    if not match:
        raise SystemExit(f"Could not anchor homepage index label: {label}")
    return text[:match.start()] + match.group(1) + f' id="{INDEX_ID}"' + match.group(2) + text[match.end():]


def patch(path: str, *, language: str) -> None:
    target, text = page(path)
    en = language == "en"

    old_heading = "And also" if en else "Y además"
    new_heading = "Explore OOLITA" if en else "Explorar OOLITA"
    text = re.sub(
        rf'(<span\b[^>]*class=["\']rot["\'][^>]*>)\s*{re.escape(old_heading)}\s*(</span>)',
        rf'\1{new_heading}\2',
        text,
        count=1,
        flags=re.I,
    )
    text = ensure_index_anchor(text, new_heading)

    if en:
        groups = (
            ("/en/editions/", "Read and understand"),
            ("https://labyrinthlocator.org/labyrinth/oolita", "Elsewhere"),
            ("/en/about/", "Project"),
        )
    else:
        groups = (
            ("/ediciones/", "Leer y entender"),
            ("https://labyrinthlocator.org/labyrinth/oolita", "Fuera de este sitio"),
            ("/sobre-oolita/", "Proyecto"),
        )

    for href, label in groups:
        text = insert_before_href(text, href, label)

    if 'id="oolita-menu-hierarchy-style"' not in text:
        if "</head>" not in text:
            raise SystemExit(f"No </head> in {path}")
        text = text.replace("</head>", STYLE + "\n</head>", 1)

    target.write_text(text, encoding="utf-8")


if not ROOT.is_dir():
    raise SystemExit(f"Missing built site: {ROOT}")

patch("index.html", language="es")
patch("en/index.html", language="en")

required = {
    "index.html": [
        "Explorar OOLITA",
        f'id="{INDEX_ID}"',
        '<span class="rot menu-group-label">Leer y entender</span>',
        '<span class="rot menu-group-label">Fuera de este sitio</span>',
        '<span class="rot menu-group-label">Proyecto</span>',
        'href="/laberinto/"',
        'href="/domingos/"',
        'href="/cabo-de-gata/"',
    ],
    "en/index.html": [
        "Explore OOLITA",
        f'id="{INDEX_ID}"',
        '<span class="rot menu-group-label">Read and understand</span>',
        '<span class="rot menu-group-label">Elsewhere</span>',
        '<span class="rot menu-group-label">Project</span>',
        'href="/en/labyrinth/"',
        'href="/en/sundays/"',
        'href="/en/cabo-de-gata/"',
    ],
}
for rel, needles in required.items():
    _, text = page(rel)
    for needle in needles:
        if needle not in text:
            raise SystemExit(f"Menu hierarchy invariant missing in {rel}: {needle}")
    if text.count(f'id="{INDEX_ID}"') != 1:
        raise SystemExit(f"Homepage index anchor count wrong in {rel}")

# Hallazgo is now first-party. The live-origin mirror passes through the edge
# rewriter, so legacy Canva destinations must not be required by this validator.
# Both former Hallazgo links may resolve to the same first-party catalogue route;
# requiring that route once is sufficient while the strict final gate rejects
# every surviving Canva hostname later in the pipeline.
for rel, hrefs in {
    "index.html": (
        "/ediciones/", "/que-es-un-laberinto/", "/que-es-un-oolito/", "/carteles/",
        "https://labyrinthlocator.org/labyrinth/oolita", "https://www.instagram.com/oolita.es/",
        "/catalogo-hallazgo/", "/sobre-oolita/", "/colaborar/", "/mundo-3d/",
        "mailto:oolita@tutamail.com",
    ),
    "en/index.html": (
        "/en/editions/", "/en/what-is-a-labyrinth/", "/en/what-is-an-ooid/", "/en/posters/",
        "https://labyrinthlocator.org/labyrinth/oolita", "https://www.instagram.com/oolita.es/",
        "/en/hallazgo-catalogue/", "/en/about/", "/en/work-with-oolita/", "/en/3d-world/",
        "mailto:oolita@tutamail.com",
    ),
}.items():
    _, text = page(rel)
    for href in hrefs:
        if f'href="{href}"' not in text and f"href='{href}'" not in text:
            raise SystemExit(f"Menu destination lost from {rel}: {href}")

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
    if route not in CHANGED_PATHS:
        continue
    seen.add(route)
    lastmod = url_el.find("sm:lastmod", ns)
    if lastmod is None:
        lastmod = ET.SubElement(url_el, "{http://www.sitemaps.org/schemas/sitemap/0.9}lastmod")
    lastmod.text = LASTMOD
if seen != CHANGED_PATHS:
    raise SystemExit(f"Menu hierarchy URLs missing from sitemap: {sorted(CHANGED_PATHS-seen)}")
tree.write(sitemap, encoding="utf-8", xml_declaration=True)

print("OOLITA homepage menu hierarchy and stable index anchor validated successfully.")
