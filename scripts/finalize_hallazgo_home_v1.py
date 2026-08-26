#!/usr/bin/env python3
"""Final Hallazgo homepage/SEO/href gate.

Hallazgo has two deliberately separate public destinations:
- Hallazgo · Arte / Art -> the external Canva artwork site.
- El mundo 3D / The 3D world -> OOLITA's first-party Three.js world.

The Hallazgo catalogue remains first-party on oolita.es. This gate runs after
the legacy Hallazgo sanitizers, so it restores only the approved Hallazgo Art
Canva destination and rejects any other surviving Canva Hallazgo references.
"""
from __future__ import annotations

import html as html_lib
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
SITEMAP = ROOT / "sitemap.xml"
BASE = "https://oolita.es"
LASTMOD = "2026-08-26"
LEGACY_HOST = "hallazgo.my.canva.site"
HALLAZGO_ART_URL = "https://hallazgo.my.canva.site/hallazgo"

HOME_COPY = {
    "en/index.html": {
        "sources": (
            "A hardback publication bringing together the complete body of work · full catalogue in the castle with a key · 16 Sep 27 · public launch 19 Sep 27 ↗",
            "A hardback publication bringing together the complete body of work · full catalogue in the 3D castle · keypad access · code in the launch newsletter · 16 Sep 27 · public launch 19 Sep 27 ↗",
        ),
        "new": "Hardback catalogue of the complete Hallazgo body of work · in the 3D castle from 16 Sep 27 · public launch 19 Sep 27 ↗",
        "art_label": "Hallazgo · Art",
        "art_href": HALLAZGO_ART_URL,
        "catalogue_label": "Hallazgo — the catalogue",
        "catalogue_href": "/en/hallazgo-catalogue/",
        "three_d_href": "/en/3d-world/",
        "route": "/en/",
    },
    "index.html": {
        "sources": (
            "Una edición en tapa dura que reúne el cuerpo completo de la obra · catálogo completo en el castillo con clave · 16.09.27 · presentación pública 19.09.27 ↗",
            "Una edición en tapa dura que reúne el cuerpo completo de la obra · catálogo completo en el castillo 3D · acceso por teclado numérico · código en el boletín de lanzamiento · 16.09.27 · presentación pública 19.09.27 ↗",
        ),
        "new": "Catálogo en tapa dura de la obra completa de Hallazgo · en el castillo 3D desde el 16.09.27 · presentación pública 19.09.27 ↗",
        "art_label": "Hallazgo · Arte",
        "art_href": HALLAZGO_ART_URL,
        "catalogue_label": "Hallazgo — el catálogo",
        "catalogue_href": "/catalogo-hallazgo/",
        "three_d_href": "/mundo-3d/",
        "route": "/",
    },
}

OLD_FRAGMENTS = (
    "full catalogue in the castle with a key",
    "catálogo completo en el castillo con clave",
    "The full catalogue remains inside the castle, with a key.",
    "El catálogo completo permanece dentro del castillo, con clave.",
)

ANCHOR_RE = re.compile(
    r'<a\b(?P<attrs>[^>]*)>(?P<body>(?:(?!</a>).)*)</a>',
    flags=re.I | re.S,
)
HREF_RE = re.compile(r'(?P<prefix>\bhref\s*=\s*["\'])(?P<href>[^"\']+)(?P<suffix>["\'])', re.I)
TAG_RE = re.compile(r"<[^>]+>", re.S)


def visible_text(value: str) -> str:
    return " ".join(html_lib.unescape(TAG_RE.sub(" ", value)).split())


def labelled_anchor_matches(text: str, label: str) -> list[re.Match[str]]:
    needle = visible_text(label)
    return [
        match
        for match in ANCHOR_RE.finditer(text)
        if needle in visible_text(match.group("body"))
    ]


def anchor_body_text(text: str, label: str, rel: str) -> str:
    matches = labelled_anchor_matches(text, label)
    if len(matches) != 1:
        raise SystemExit(f"Expected exactly one {label!r} anchor in {rel}; found {len(matches)}")
    return visible_text(matches[0].group("body"))


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
    fixed_anchor = anchor[:href_match.start("href")] + href + anchor[href_match.end("href"):]
    return text[:match.start()] + fixed_anchor + text[match.end():]


def rendered_summary_count(text: str, label: str, summary: str, rel: str) -> int:
    return anchor_body_text(text, label, rel).count(visible_text(summary))


def normalize_summary(
    text: str,
    sources: tuple[str, ...],
    final: str,
    label: str,
    rel: str,
) -> str:
    if rendered_summary_count(text, label, final, rel) == 1:
        return text

    exact_final = text.count(final)
    if exact_final == 1:
        return text
    if exact_final > 1:
        raise SystemExit(f"Hallazgo homepage summary duplicated in {rel}")

    matches = [(source, text.count(source)) for source in sources if text.count(source)]
    total = sum(count for _, count in matches)
    if total == 1:
        source, count = matches[0]
        if count != 1:
            raise SystemExit(f"Hallazgo homepage source duplicated in {rel}")
        return text.replace(source, final, 1)

    state = anchor_body_text(text, label, rel)
    raise SystemExit(f"Hallazgo homepage source drifted in {rel}: {state[:500]}")


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

    text = normalize_summary(
        text,
        cfg["sources"],
        cfg["new"],
        cfg["catalogue_label"],
        rel,
    )
    text = rewrite_anchor_href(text, cfg["art_label"], cfg["art_href"], rel)
    text = rewrite_anchor_href(text, cfg["catalogue_label"], cfg["catalogue_href"], rel)

    if text != before:
        page.write_text(text, encoding="utf-8")
        changed_routes.add(cfg["route"])
        print(f"Hallazgo homepage copy/hrefs finalized: {rel}")

    final_html = page.read_text(encoding="utf-8")
    if rendered_summary_count(final_html, cfg["catalogue_label"], cfg["new"], rel) != 1:
        raise SystemExit(f"Hallazgo homepage concise copy invariant missing in {rel}")
    if anchor_href(final_html, cfg["art_label"], rel) != HALLAZGO_ART_URL:
        raise SystemExit(f"Hallazgo Art must point to Canva in {rel}")
    if anchor_href(final_html, cfg["catalogue_label"], rel) != cfg["catalogue_href"]:
        raise SystemExit(f"Hallazgo catalogue href incorrect in {rel}")
    if f'href="{cfg["three_d_href"]}"' not in final_html and f"href='{cfg['three_d_href']}'" not in final_html:
        raise SystemExit(f"Standalone OOLITA 3D-world href missing in {rel}")
    if final_html.count(HALLAZGO_ART_URL) != 1:
        raise SystemExit(f"Approved Hallazgo Canva URL missing or duplicated in {rel}")

# No retired keyed-castle wording may survive. The Canva host is allowed only
# once on each language homepage, as the Hallazgo Art destination restored above.
stragglers: list[str] = []
for html_page in sorted(ROOT.rglob("*.html")):
    rel = html_page.relative_to(ROOT).as_posix()
    text = html_page.read_text(encoding="utf-8")
    rendered_lower = visible_text(text).lower()
    for fragment in OLD_FRAGMENTS:
        if visible_text(fragment).lower() in rendered_lower:
            stragglers.append(f"{rel}: superseded Hallazgo wording: {fragment}")
    if LEGACY_HOST in text.lower() and rel not in HOME_COPY:
        stragglers.append(f"{rel}: unapproved Canva Hallazgo reference")
if stragglers:
    print("Hallazgo stragglers remain:")
    print("\n".join(stragglers))
    raise SystemExit(1)

# The OOLITA 3D world remains a separate first-party destination; the catalogue
# remains first-party too. All four routes must continue to exist physically.
for route in (
    "/mundo-3d/",
    "/en/3d-world/",
    "/catalogo-hallazgo/",
    "/en/hallazgo-catalogue/",
):
    target = ROOT / route.lstrip("/") / "index.html"
    if not target.is_file():
        raise SystemExit(f"Hallazgo/OOLITA internal href would 404: {route}")

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
            lastmod = ET.SubElement(
                url_el,
                "{http://www.sitemaps.org/schemas/sitemap/0.9}lastmod",
            )
        lastmod.text = LASTMOD

missing = expected_routes - seen
if missing:
    raise SystemExit(f"Hallazgo sitemap routes missing: {sorted(missing)}")

tree.write(SITEMAP, encoding="utf-8", xml_declaration=True)
print(
    "Hallazgo final homepage gate passed: Hallazgo Art -> Canva; OOLITA 3D world "
    "remains separate; catalogue stays first-party; no unapproved Canva refs or "
    "keyed-castle stragglers; internal routes and sitemap valid."
)
