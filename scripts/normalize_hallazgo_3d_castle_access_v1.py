#!/usr/bin/env python3
"""Publish and validate Hallazgo's first-party 3D-castle access explanation."""
from __future__ import annotations

from pathlib import Path
import re
import runpy
import sys
import xml.etree.ElementTree as ET

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
SITEMAP = ROOT / "sitemap.xml"
BASE = "https://oolita.es"
LASTMOD = "2026-08-25"
LEGACY_HOST = "hallazgo.my.canva.site"
LEGACY_HREF_RE = re.compile(
    r'(?P<prefix>href\s*=\s*["\'])https?://hallazgo\.my\.canva\.site[^"\']*(?P<suffix>["\'])',
    flags=re.I,
)

PAGES = {
    "en/editions/index.html": {
        "old": "The full catalogue remains inside the castle, with a key.",
        "new": "On the 3D site, the full catalogue of works is housed inside the castle — a digital replica of the 1771 Batería de San Felipe, standing on the fossil dune not far from the labyrinth at Los Escullos. The catalogue is secured by a keypad, and subscribers will receive the code in the launch newsletter.",
        "route": "/en/editions/",
        "canonical": "https://oolita.es/en/editions/",
        "alternates": {"en": "https://oolita.es/en/editions/", "es": "https://oolita.es/ediciones/"},
        "anchor": "Hallazgo — the catalogue",
        "href": "/en/hallazgo-catalogue/",
        "final_paragraph": (
            '<p class="parr"><a href="/en/hallazgo-catalogue/">Hallazgo — the catalogue ↗</a> '
            'follows the first OOLITA book and T-shirt: a hardback publication bringing together the complete body of work. '
            'Published 16 September 2027; public launch, 19 September. '
            'On the 3D site, the full catalogue of works is housed inside the castle — a digital replica of the 1771 Batería de San Felipe, '
            'standing on the fossil dune not far from the labyrinth at Los Escullos. The catalogue is secured by a keypad, and subscribers '
            'will receive the code in the launch newsletter.</p>'
        ),
    },
    "ediciones/index.html": {
        "old": "El catálogo completo permanece dentro del castillo, con clave.",
        "new": "Edición en tapa dura · obra completa en Castillo 3D · acceso con código · lanzamiento 16.09.27 · presentación 19.09.27",
        "route": "/ediciones/",
        "canonical": "https://oolita.es/ediciones/",
        "alternates": {"en": "https://oolita.es/en/editions/", "es": "https://oolita.es/ediciones/"},
        "anchor": "Edición en tapa dura · obra completa en Castillo 3D · acceso con código · lanzamiento 16.09.27 · presentación 19.09.27",
        "legacy_anchor": "Hallazgo — el catálogo",
        "href": "/catalogo-hallazgo/",
        "stragglers": (
            "llega después del libro y la camiseta de OOLITA: una edición en tapa dura que reúne el cuerpo completo de la obra.",
            "Se publica el 16 de septiembre de 2027; presentación pública, 19 de septiembre.",
            "En el sitio 3D, el catálogo completo de obras se encuentra dentro del castillo",
            "El catálogo está protegido por un teclado numérico, y los suscriptores recibirán el código en el boletín de lanzamiento.",
        ),
        "final_paragraph": (
            '<p class="parr"><a href="/catalogo-hallazgo/">'
            'Edición en tapa dura · obra completa en Castillo 3D · acceso con código · lanzamiento 16.09.27 · presentación 19.09.27 ↗'
            '</a></p>'
        ),
    },
}

CATALOGUE_PAGES = {
    "en/hallazgo-catalogue/index.html": {
        "route": "/en/hallazgo-catalogue/",
        "canonical": "https://oolita.es/en/hallazgo-catalogue/",
        "alternates": {"en": "https://oolita.es/en/hallazgo-catalogue/", "es": "https://oolita.es/catalogo-hallazgo/"},
    },
    "catalogo-hallazgo/index.html": {
        "route": "/catalogo-hallazgo/",
        "canonical": "https://oolita.es/catalogo-hallazgo/",
        "alternates": {"en": "https://oolita.es/en/hallazgo-catalogue/", "es": "https://oolita.es/catalogo-hallazgo/"},
    },
}

if not ROOT.is_dir():
    raise SystemExit(f"Missing built site: {ROOT}")
if not SITEMAP.is_file():
    raise SystemExit("Missing sitemap.xml")


def validate_links(rel: str, text: str, canonical: str, alternates: dict[str, str]) -> None:
    tags = re.findall(r'<link\b[^>]*>', text, flags=re.I)
    canonical_ok = any(
        re.search(r'\brel=["\']canonical["\']', tag, flags=re.I)
        and re.search(rf'\bhref=["\']{re.escape(canonical)}["\']', tag, flags=re.I)
        for tag in tags
    )
    if not canonical_ok:
        raise SystemExit(f"Canonical missing or incorrect in {rel}")
    for lang, url in alternates.items():
        alternate_ok = any(
            re.search(rf'\bhreflang=["\']{re.escape(lang)}["\']', tag, flags=re.I)
            and re.search(rf'\bhref=["\']{re.escape(url)}["\']', tag, flags=re.I)
            for tag in tags
        )
        if not alternate_ok:
            raise SystemExit(f"hreflang {lang} missing or incorrect in {rel}")


changed_routes: set[str] = set()
for rel, cfg in PAGES.items():
    page = ROOT / rel
    if not page.is_file():
        raise SystemExit(f"Missing Hallazgo Editions page: {rel}")
    text = page.read_text(encoding="utf-8")
    before = text

    # This gate runs after the geological and Editions-sequence normalizers. Those
    # passes can legitimately alter words inside the already-current Hallazgo
    # paragraph, so exact old/new sentence matching is not a reliable source test.
    # Isolate the single Hallazgo paragraph by either its final linked label or
    # the legacy catalogue label still present on the current production mirror.
    # This keeps the pass idempotent across the first concise-copy deployment and
    # every rebuild that starts from that already-updated live origin.
    paragraph_labels = tuple(
        dict.fromkeys((cfg["anchor"], cfg.get("legacy_anchor", cfg["anchor"])))
    )
    paragraph_label_pattern = "|".join(re.escape(label) for label in paragraph_labels)
    paragraph_re = re.compile(
        rf'<p\b[^>]*class=["\'][^"\']*\bparr\b[^"\']*["\'][^>]*>.*?(?:{paragraph_label_pattern}).*?</p>',
        flags=re.I | re.S,
    )
    matches = list(paragraph_re.finditer(text))
    if len(matches) != 1:
        raise SystemExit(f"Expected exactly one Hallazgo Editions paragraph in {rel}; found {len(matches)}")
    match = matches[0]
    if match.group(0) != cfg["final_paragraph"]:
        text = text[:match.start()] + cfg["final_paragraph"] + text[match.end():]

    if text != before:
        page.write_text(text, encoding="utf-8")
        changed_routes.add(cfg["route"])
        print(f"Hallazgo final Editions paragraph normalized: {rel}")

    text = page.read_text(encoding="utf-8")
    if text.count(cfg["final_paragraph"]) != 1:
        raise SystemExit(f"Hallazgo final Editions paragraph missing or duplicated in {rel}")
    if text.count(cfg["new"]) != 1:
        raise SystemExit(f"Hallazgo final access explanation must appear exactly once in {rel}")
    if cfg["old"] in text:
        raise SystemExit(f"Hallazgo keyed-castle sentence remains in {rel}")
    final_anchor = re.search(
        rf'<a\b[^>]*\bhref=["\']{re.escape(cfg["href"])}["\'][^>]*>\s*{re.escape(cfg["anchor"])}\s*↗?\s*</a>',
        text,
        flags=re.I,
    )
    if not final_anchor:
        raise SystemExit(f"Hallazgo first-party catalogue href missing in {rel}")
    validate_links(rel, text, cfg["canonical"], cfg["alternates"])

# Rewrite any remaining reader-facing Canva catalogue href to the first-party
# OOLITA route, matching the edge middleware but leaving no stale HTML hrefs in
# the deployed bundle.
for html in sorted(ROOT.rglob("*.html")):
    rel = html.relative_to(ROOT).as_posix()
    text = html.read_text(encoding="utf-8")
    target = "/en/hallazgo-catalogue/" if rel.startswith("en/") else "/catalogo-hallazgo/"
    rewritten = LEGACY_HREF_RE.sub(lambda m: m.group("prefix") + target + m.group("suffix"), text)
    if rewritten != text:
        html.write_text(rewritten, encoding="utf-8")
        print(f"Hallazgo Canva href retired: {rel}")

# The first-party catalogue routes must exist physically in the Pages bundle,
# and their SEO link relationships must be correct.
for rel, cfg in CATALOGUE_PAGES.items():
    page = ROOT / rel
    if not page.is_file():
        raise SystemExit(f"First-party Hallazgo catalogue route missing: {rel}")
    text = page.read_text(encoding="utf-8")
    validate_links(rel, text, cfg["canonical"], cfg["alternates"])

# No former Editions sentence or Canva href may survive in reader-facing HTML.
stragglers: list[str] = []
for html in sorted(ROOT.rglob("*.html")):
    rel = html.relative_to(ROOT).as_posix()
    body = html.read_text(encoding="utf-8")
    for cfg in PAGES.values():
        if cfg["old"] in body:
            stragglers.append(f"{rel}: {cfg['old']}")
        for stale in cfg.get("stragglers", ()):
            if stale in body:
                stragglers.append(f"{rel}: {stale}")
    if LEGACY_HOST.lower() in body.lower():
        stragglers.append(f"{rel}: obsolete Canva Hallazgo URL")
if stragglers:
    print("Superseded Hallazgo wording/hrefs remain:")
    print("\n".join(stragglers))
    raise SystemExit(1)

# Explicit no-404 gate for the new first-party hrefs introduced by this pass.
for route in ("/en/hallazgo-catalogue/", "/catalogo-hallazgo/"):
    target = ROOT / route.lstrip("/") / "index.html"
    if not target.is_file():
        raise SystemExit(f"Hallazgo internal href would 404: {route}")

# Refresh the Editions routes and ensure the new catalogue routes are present in
# sitemap.xml for search discovery and the existing IndexNow deployment step.
ET.register_namespace("", "http://www.sitemaps.org/schemas/sitemap/0.9")
tree = ET.parse(SITEMAP)
root = tree.getroot()
ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
expected_urls = {
    BASE + cfg["route"] for cfg in PAGES.values()
} | {
    BASE + cfg["route"] for cfg in CATALOGUE_PAGES.values()
}
seen: set[str] = set()
for url_el in root.findall("sm:url", ns):
    loc = url_el.find("sm:loc", ns)
    if loc is None or not loc.text:
        continue
    url = loc.text.strip()
    if url not in expected_urls:
        continue
    seen.add(url)
    lastmod = url_el.find("sm:lastmod", ns)
    if lastmod is None:
        lastmod = ET.SubElement(url_el, "{http://www.sitemaps.org/schemas/sitemap/0.9}lastmod")
    lastmod.text = LASTMOD

for url in sorted(expected_urls - seen):
    url_el = ET.SubElement(root, "{http://www.sitemaps.org/schemas/sitemap/0.9}url")
    loc = ET.SubElement(url_el, "{http://www.sitemaps.org/schemas/sitemap/0.9}loc")
    loc.text = url
    lastmod = ET.SubElement(url_el, "{http://www.sitemaps.org/schemas/sitemap/0.9}lastmod")
    lastmod.text = LASTMOD
    print(f"Hallazgo sitemap route added: {url}")

tree.write(SITEMAP, encoding="utf-8", xml_declaration=True)
print(
    "Hallazgo 3D-castle access gate passed: approved bilingual copy current; "
    "first-party hrefs and routes valid; Canva hrefs and old key sentence absent; "
    "canonical/hreflang valid; sitemap current."
)

# The release-calendar layer can still recreate the shorter homepage keyed-castle
# wording and the legacy edge rewrite can make Hallazgo Art point at the catalogue.
# Run the absolute homepage gate last so the deployable bundle cannot contain
# either straggler and both first-party destinations are validated as real files.
finalizer = Path(__file__).resolve().parent / "finalize_hallazgo_home_v1.py"
if not finalizer.is_file():
    raise SystemExit(f"Missing Hallazgo homepage finalizer: {finalizer}")
old_argv = sys.argv[:]
sys.argv = [str(finalizer), str(ROOT)]
try:
    runpy.run_path(str(finalizer), run_name="__main__")
finally:
    sys.argv = old_argv
