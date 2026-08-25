#!/usr/bin/env python3
"""Final Hallazgo homepage/SEO/href gate.

Runs after the release-calendar and existing Hallazgo passes so later transforms
cannot reintroduce the retired Canva links or the former "castle with a key"
shorthand. Keeps Hallazgo Art pointed at the first-party 3D world and the
catalogue entry pointed at the first-party catalogue.
"""
from __future__ import annotations

from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
SITEMAP = ROOT / "sitemap.xml"
BASE = "https://oolita.es"
LASTMOD = "2026-08-25"
LEGACY_HOST = "hallazgo.my.canva.site"

HOME_COPY = {
    "en/index.html": {
        "old": "A hardback publication bringing together the complete body of work · full catalogue in the castle with a key · 16 Sep 27 · public launch 19 Sep 27 ↗",
        "new": "A hardback publication bringing together the complete body of work · full catalogue in the 3D castle · keypad access · code in the launch newsletter · 16 Sep 27 · public launch 19 Sep 27 ↗",
        "art_label": "Hallazgo · Art",
        "art_href": "/en/3d-world/",
        "catalogue_label": "Hallazgo — the catalogue",
        "catalogue_href": "/en/hallazgo-catalogue/",
        "route": "/en/",
    },
    "index.html": {
        "old": "Una edición en tapa dura que reúne el cuerpo completo de la obra · catálogo completo en el castillo con clave · 16.09.27 · presentación pública 19.09.27 ↗",
        "new": "Una edición en tapa dura que reúne el cuerpo completo de la obra · catálogo completo en el castillo 3D · acceso por teclado numérico · código en el boletín de lanzamiento · 16.09.27 · presentación pública 19.09.27 ↗",
        "art_label": "Hallazgo · Arte",
        "art_href": "/mundo-3d/",
        "catalogue_label": "Hallazgo — el catálogo",
        "catalogue_href": "/catalogo-hallazgo/",
        "route": "/",
    },
}

# The 404 page is a homepage-shell mirror in this deployment. It must not retain
# superseded Hallazgo wording even though it is intentionally non-indexable.
MIRROR_COPY = {
    "404/index.html": (
        "Una edición en tapa dura que reúne el cuerpo completo de la obra · catálogo completo en el castillo con clave · 16.09.27 · presentación pública 19.09.27 ↗",
        "Una edición en tapa dura que reúne el cuerpo completo de la obra · catálogo completo en el castillo 3D · acceso por teclado numérico · código en el boletín de lanzamiento · 16.09.27 · presentación pública 19.09.27 ↗",
    ),
}

OLD_FRAGMENTS = (
    "full catalogue in the castle with a key",
    "catálogo completo en el castillo con clave",
    "The full catalogue remains inside the castle, with a key.",
    "El catálogo completo permanece dentro del castillo, con clave.",
)

# Match one complete anchor without allowing the body matcher to cross another
# closing </a>. The former matcher used .*? and could begin at an earlier link,
# then consume across adjacent anchors until it found the Hallazgo label.
ANCHOR_RE = re.compile(
    r'<a\b(?P<attrs>[^>]*)>(?P<body>(?:(?!</a>).)*)</a>',
    flags=re.I | re.S,
)
HREF_RE = re.compile(r'(?P<prefix>\bhref\s*=\s*["\'])(?P<href>[^"\']+)(?P<suffix>["\'])', re.I)


def labelled_anchor_matches(text: str, label: str) -> list[re.Match[str]]:
    return [match for match in ANCHOR_RE.finditer(text) if label in match.group("body")]


def anchor_href(text: str, label: str, rel: str) -> str:
    matches = labelled_anchor_matches(text, label)
    if len(matches) != 1:
        raise SystemExit(f"Expected exactly one {label!r} anchor in {rel}; found {len(matches)}")
    href_match = HREF_RE.search(matches[0].group("attrs"))
    if not href_match:
        raise SystemExit(f"Hallazgo anchor {label!r} has no href in {rel}")
    return href_match.group("href")


def rewrite_anchor_href(text: str, label: str, href: str, rel: str) -> str:
    matches = labelled_anchor_matches(text, label)
    if len(matches) != 1:
        raise SystemExit(f"Expected exactly one {label!r} anchor in {rel}; found {len(matches)}")
    match = matches[0]
    anchor = match.group(0)
    href_match = HREF_RE.search(anchor)
    if not href_match:
        raise SystemExit(f"Hallazgo anchor {label!r} has no href in {rel}")
    if href_match.group("href") == href:
        return text
    fixed_anchor = (
        anchor[:href_match.start("href")]
        + href
        + anchor[href_match.end("href"):]
    )
    return text[:match.start()] + fixed_anchor + text[match.end():]


if not ROOT.is_dir():
    raise SystemExit(f"Missing built site: {ROOT}")
if not SITEMAP.is_file():
    raise SystemExit("Missing sitemap.xml")

changed_routes: set[str] = set()
for rel, cfg in HOME_COPY.items():
    page = ROOT / rel
    if not page.is_file():
        raise SystemExit(f"Missing Hallazgo homepage: {rel}")
    text = page.read_text(encoding="utf-8")
    before = text

    if cfg["new"] not in text:
        if text.count(cfg["old"]) != 1:
            raise SystemExit(f"Hallazgo homepage source drifted in {rel}")
        text = text.replace(cfg["old"], cfg["new"], 1)

    text = rewrite_anchor_href(text, cfg["art_label"], cfg["art_href"], rel)
    text = rewrite_anchor_href(text, cfg["catalogue_label"], cfg["catalogue_href"], rel)

    if text != before:
        page.write_text(text, encoding="utf-8")
        changed_routes.add(cfg["route"])
        print(f"Hallazgo homepage copy/hrefs finalized: {rel}")

    final = page.read_text(encoding="utf-8")
    if cfg["new"] not in final:
        raise SystemExit(f"Hallazgo homepage copy invariant missing in {rel}")
    if anchor_href(final, cfg["art_label"], rel) != cfg["art_href"]:
        raise SystemExit(f"Hallazgo Art href incorrect in {rel}")
    if anchor_href(final, cfg["catalogue_label"], rel) != cfg["catalogue_href"]:
        raise SystemExit(f"Hallazgo catalogue href incorrect in {rel}")

for rel, (old, new) in MIRROR_COPY.items():
    page = ROOT / rel
    if not page.is_file():
        continue
    text = page.read_text(encoding="utf-8")
    if old in text:
        page.write_text(text.replace(old, new, 1), encoding="utf-8")
        print(f"Hallazgo 404 mirror wording finalized: {rel}")

# Absolute no-straggler gate across every reader-facing HTML file.
stragglers: list[str] = []
for html in sorted(ROOT.rglob("*.html")):
    rel = html.relative_to(ROOT).as_posix()
    text = html.read_text(encoding="utf-8")
    lower = text.lower()
    if LEGACY_HOST in lower:
        stragglers.append(f"{rel}: retired Canva Hallazgo host")
    for fragment in OLD_FRAGMENTS:
        if fragment.lower() in lower:
            stragglers.append(f"{rel}: superseded Hallazgo wording: {fragment}")
if stragglers:
    print("Hallazgo stragglers remain:")
    print("\n".join(stragglers))
    raise SystemExit(1)

# Explicit no-404 gate for every first-party Hallazgo destination introduced or
# enforced here.
for route in (
    "/mundo-3d/",
    "/en/3d-world/",
    "/catalogo-hallazgo/",
    "/en/hallazgo-catalogue/",
):
    target = ROOT / route.lstrip("/") / "index.html"
    if not target.is_file():
        raise SystemExit(f"Hallazgo internal href would 404: {route}")

# Refresh changed home routes and verify all Hallazgo destinations are discoverable.
ET.register_namespace("", "http://www.sitemaps.org/schemas/sitemap/0.9")
tree = ET.parse(SITEMAP)
root = tree.getroot()
ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
expected_routes = {
    "/",
    "/en/",
    "/mundo-3d/",
    "/en/3d-world/",
    "/catalogo-hallazgo/",
    "/en/hallazgo-catalogue/",
    "/ediciones/",
    "/en/editions/",
}
seen: set[str] = set()
for url_el in root.findall("sm:url", ns):
    loc = url_el.find("sm:loc", ns)
    if loc is None or not loc.text:
        continue
    url = loc.text.strip()
    if not url.startswith(BASE):
        continue
    route = url[len(BASE):] or "/"
    if route not in expected_routes:
        continue
    seen.add(route)
    if route in changed_routes:
        lastmod = url_el.find("sm:lastmod", ns)
        if lastmod is None:
            lastmod = ET.SubElement(url_el, "{http://www.sitemaps.org/schemas/sitemap/0.9}lastmod")
        lastmod.text = LASTMOD

missing = expected_routes - seen
if missing:
    raise SystemExit(f"Hallazgo sitemap routes missing: {sorted(missing)}")

tree.write(SITEMAP, encoding="utf-8", xml_declaration=True)
print(
    "Hallazgo final homepage gate passed: exact Art anchors point to 3D; exact catalogue anchors point to catalogue; "
    "keypad/newsletter wording current; no Canva or keyed-castle stragglers; no internal 404s; sitemap valid."
)
