#!/usr/bin/env python3
"""Apply non-critical SEO consistency fixes after reader-facing mutations.

This pass deliberately runs last. It fixes stale visible 44/48-page poster
copy, adds bilingual BreadcrumbList structured data to content/detail pages,
updates sitemap lastmod only for pages actually changed here, and validates
metadata without inventing edit dates.
"""
from __future__ import annotations

import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
BASE = "https://oolita.es"
LASTMOD = "2026-08-23"

if not ROOT.is_dir():
    raise SystemExit(f"Missing built site: {ROOT}")


def read(rel: str) -> tuple[Path, str]:
    path = ROOT / rel
    if not path.is_file():
        raise SystemExit(f"Missing SEO follow-up page: {rel}")
    return path, path.read_text(encoding="utf-8")


def write_if_changed(path: Path, before: str, after: str) -> bool:
    if before == after:
        return False
    path.write_text(after, encoding="utf-8")
    return True


changed_routes: set[str] = set()

# 1. Correct stale reader-visible page-count copy on the poster archive.
poster_fixes = {
    "carteles/index.html": (
        ("fábula bilingüe de 44 páginas", "fábula bilingüe de 48 páginas"),
        ("fábula bilingüe, 44 páginas", "fábula bilingüe, 48 páginas"),
        ("libro Oolita es una fábula bilingüe de 44 páginas", "libro Oolita es una fábula bilingüe de 48 páginas"),
        ("libro OOLITA es una fábula bilingüe de 44 páginas", "libro OOLITA es una fábula bilingüe de 48 páginas"),
    ),
    "en/posters/index.html": (
        ("44-page bilingual fable", "48-page bilingual fable"),
        ("44 page bilingual fable", "48-page bilingual fable"),
    ),
}

for rel, replacements in poster_fixes.items():
    path, text = read(rel)
    before = text
    for old, new in replacements:
        text = text.replace(old, new)
    if write_if_changed(path, before, text):
        changed_routes.add("/" + rel.removesuffix("index.html"))


# 2. Breadcrumb structured data.
BREADCRUMBS: dict[str, list[tuple[str, str]]] = {
    "laberinto/index.html": [("OOLITA", "/"), ("Laberinto", "/laberinto/")],
    "carteles/index.html": [("OOLITA", "/"), ("Carteles", "/carteles/")],
    "que-es-un-laberinto/index.html": [("OOLITA", "/"), ("Qué es un laberinto", "/que-es-un-laberinto/")],
    "que-es-un-oolito/index.html": [("OOLITA", "/"), ("Qué es un oolito", "/que-es-un-oolito/")],
    "ediciones/index.html": [("OOLITA", "/"), ("Ediciones", "/ediciones/")],
    "ediciones/libro/index.html": [("OOLITA", "/"), ("Ediciones", "/ediciones/"), ("Libro", "/ediciones/libro/")],
    "ediciones/camiseta/index.html": [("OOLITA", "/"), ("Ediciones", "/ediciones/"), ("Camiseta", "/ediciones/camiseta/")],
    "domingos/index.html": [("OOLITA", "/"), ("Domingos", "/domingos/")],
    "domingos/01-el-doble/index.html": [("OOLITA", "/"), ("Domingos", "/domingos/"), ("01 · El doble", "/domingos/01-el-doble/")],
    "domingos/02-el-gato-de-verdad/index.html": [("OOLITA", "/"), ("Domingos", "/domingos/"), ("02 · El gato de verdad", "/domingos/02-el-gato-de-verdad/")],
    "cabo-de-gata/index.html": [("OOLITA", "/"), ("Cabo de Gata", "/cabo-de-gata/")],
    "sobre-oolita/index.html": [("OOLITA", "/"), ("Sobre OOLITA", "/sobre-oolita/")],
    "colaborar/index.html": [("OOLITA", "/"), ("Colaborar", "/colaborar/")],
    "mundo-3d/index.html": [("OOLITA", "/"), ("Mundo 3D", "/mundo-3d/")],
    "en/labyrinth/index.html": [("OOLITA", "/en/"), ("Labyrinth", "/en/labyrinth/")],
    "en/posters/index.html": [("OOLITA", "/en/"), ("Posters", "/en/posters/")],
    "en/what-is-a-labyrinth/index.html": [("OOLITA", "/en/"), ("What is a labyrinth", "/en/what-is-a-labyrinth/")],
    "en/what-is-an-ooid/index.html": [("OOLITA", "/en/"), ("What is an ooid", "/en/what-is-an-ooid/")],
    "en/editions/index.html": [("OOLITA", "/en/"), ("Editions", "/en/editions/")],
    "en/editions/book/index.html": [("OOLITA", "/en/"), ("Editions", "/en/editions/"), ("Book", "/en/editions/book/")],
    "en/editions/t-shirt/index.html": [("OOLITA", "/en/"), ("Editions", "/en/editions/"), ("T-shirt", "/en/editions/t-shirt/")],
    "en/sundays/index.html": [("OOLITA", "/en/"), ("Sundays", "/en/sundays/")],
    "en/sundays/01-the-double/index.html": [("OOLITA", "/en/"), ("Sundays", "/en/sundays/"), ("01 · The double", "/en/sundays/01-the-double/")],
    "en/sundays/02-the-cat-for-real/index.html": [("OOLITA", "/en/"), ("Sundays", "/en/sundays/"), ("02 · The cat for real", "/en/sundays/02-the-cat-for-real/")],
    "en/cabo-de-gata/index.html": [("OOLITA", "/en/"), ("Cabo de Gata", "/en/cabo-de-gata/")],
    "en/about/index.html": [("OOLITA", "/en/"), ("About OOLITA", "/en/about/")],
    "en/work-with-oolita/index.html": [("OOLITA", "/en/"), ("Work with OOLITA", "/en/work-with-oolita/")],
    "en/3d-world/index.html": [("OOLITA", "/en/"), ("3D world", "/en/3d-world/")],
}

BREADCRUMB_MARKER = '"@type":"BreadcrumbList"'


def breadcrumb_json(items: list[tuple[str, str]]) -> str:
    payload = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": pos, "name": name, "item": BASE + route}
            for pos, (name, route) in enumerate(items, start=1)
        ],
    }
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


for rel, items in BREADCRUMBS.items():
    path, text = read(rel)
    before = text
    if BREADCRUMB_MARKER not in text:
        script = f'<script type="application/ld+json">{breadcrumb_json(items)}</script>'
        if "</head>" not in text:
            raise SystemExit(f"Missing </head> while adding breadcrumbs: {rel}")
        text = text.replace("</head>", script + "\n</head>", 1)
    if write_if_changed(path, before, text):
        changed_routes.add("/" + rel.removesuffix("index.html"))


# 3. Fix the single description that the built-site audit found over 160 chars.
META_DESCRIPTION_FIXES = {
    "que-es-un-laberinto/index.html": (
        "Un laberinto clásico tiene un solo camino: se entra, se llega al centro y se vuelve. "
        "Un laberinto multicursal tiene encrucijadas. Diferencias y recorrido."
    ),
}

for rel, description in META_DESCRIPTION_FIXES.items():
    if len(description) > 160:
        raise SystemExit(f"Configured meta description is too long in {rel}: {len(description)}")
    path, text = read(rel)
    before = text
    pattern = r'<meta\b(?=[^>]*\bname=["\']description["\'])[^>]*>'
    replacement = f'<meta name="description" content="{description}">'
    text, count = re.subn(pattern, replacement, text, count=1, flags=re.I)
    if count != 1:
        raise SystemExit(f"Expected one meta description in {rel}; replaced {count}")
    if write_if_changed(path, before, text):
        changed_routes.add("/" + rel.removesuffix("index.html"))


# 4. Update sitemap lastmod for files this pass actually changed.
sitemap = ROOT / "sitemap.xml"
if not sitemap.is_file():
    raise SystemExit("Missing sitemap.xml")
ET.register_namespace("", "http://www.sitemaps.org/schemas/sitemap/0.9")
tree = ET.parse(sitemap)
xml_root = tree.getroot()
ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
seen_changed: set[str] = set()
for url_el in xml_root.findall("sm:url", ns):
    loc = url_el.find("sm:loc", ns)
    if loc is None or not loc.text:
        continue
    url = loc.text.strip()
    if not url.startswith(BASE):
        continue
    route = url[len(BASE):] or "/"
    if route not in changed_routes:
        continue
    seen_changed.add(route)
    lastmod = url_el.find("sm:lastmod", ns)
    if lastmod is None:
        lastmod = ET.SubElement(url_el, "{http://www.sitemaps.org/schemas/sitemap/0.9}lastmod")
    lastmod.text = LASTMOD

missing_changed = sorted(changed_routes - seen_changed)
if missing_changed:
    raise SystemExit(f"SEO follow-up changed routes missing from sitemap: {missing_changed}")
tree.write(sitemap, encoding="utf-8", xml_declaration=True)


# 5. Validate breadcrumbs and stale page-count removal.
for rel, expected_items in BREADCRUMBS.items():
    _, text = read(rel)
    blocks = re.findall(
        r'<script\b[^>]*type=["\']application/ld\+json["\'][^>]*>([\s\S]*?)</script>',
        text,
        flags=re.I,
    )
    parsed = []
    for block in blocks:
        try:
            obj = json.loads(block.strip())
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict) and obj.get("@type") == "BreadcrumbList":
            parsed.append(obj)
    if len(parsed) != 1:
        raise SystemExit(f"Expected exactly one BreadcrumbList in {rel}; found {len(parsed)}")
    positions = parsed[0].get("itemListElement") or []
    if len(positions) != len(expected_items):
        raise SystemExit(f"Breadcrumb item count mismatch in {rel}")

for rel, stale in {
    "carteles/index.html": ("fábula bilingüe de 44 páginas", "fábula bilingüe, 44 páginas"),
    "en/posters/index.html": ("44-page bilingual fable", "44 page bilingual fable"),
}.items():
    _, text = read(rel)
    for needle in stale:
        if needle in text:
            raise SystemExit(f"Stale 44-page poster copy remains in {rel}: {needle}")


# 6. Metadata audit: validate lengths and report non-actionable signals.
long_descriptions: list[tuple[str, int, str]] = []
domain_mentions: list[tuple[str, str]] = []
updated_times: list[tuple[str, str]] = []
for path in sorted(ROOT.rglob("*.html")):
    rel = str(path.relative_to(ROOT))
    text = path.read_text(encoding="utf-8")
    m = re.search(r'<meta\b(?=[^>]*\bname=["\']description["\'])[^>]*\bcontent=["\']([^"\']*)["\'][^>]*>', text, flags=re.I)
    if m:
        value = m.group(1).strip()
        if len(value) > 160:
            long_descriptions.append((rel, len(value), value))
        if "oolita.es" in value.lower():
            domain_mentions.append((rel, value))
    for stamp in re.findall(r'<meta\b(?=[^>]*\bproperty=["\']og:updated_time["\'])[^>]*\bcontent=["\']([^"\']+)["\'][^>]*>', text, flags=re.I):
        updated_times.append((rel, stamp.strip()))

if long_descriptions:
    for rel, length, value in long_descriptions:
        print(f"Overlong meta description: {rel}: {length} chars :: {value}")
    raise SystemExit(f"SEO follow-up found {len(long_descriptions)} descriptions over 160 characters")
print("SEO follow-up metadata review: no descriptions over 160 characters.")

if domain_mentions:
    print("SEO follow-up metadata review: literal oolita.es appears in descriptions:")
    for rel, value in domain_mentions:
        print(f"  {rel}: {value}")
else:
    print("SEO follow-up metadata review: no literal-domain repetition in descriptions.")

if updated_times:
    print("SEO follow-up metadata review: og:updated_time values present (not modified):")
    for rel, stamp in updated_times:
        print(f"  {rel}: {stamp}")
else:
    print("SEO follow-up metadata review: no og:updated_time values present.")

print(
    f"OOLITA SEO follow-up validated: breadcrumbs={len(BREADCRUMBS)}; "
    f"changed_routes={len(changed_routes)}; long_descriptions={len(long_descriptions)}; "
    f"domain_mentions={len(domain_mentions)}; og_updated_time={len(updated_times)}"
)
