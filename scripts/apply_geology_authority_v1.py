#!/usr/bin/env python3
"""Refine OOLITA's existing geology pages without turning them into SEO copy.

This pass is deliberately narrow and idempotent. It:
- keeps the existing /que-es-un-oolito/ and /en/what-is-an-ooid/ routes;
- aligns the English page with the better current Spanish geology wording;
- distinguishes ooid (grain), oolite (rock) and aeolianite (lithified dune);
- uses the Junta de Andalucia Los Escullos interpretation for the local sequence
  and 128,000–100,000 year range;
- fixes the About-page shorthand so oolite is not described as a grain;
- does not add a new page, keyword block, tourism language or visitor promotion.

The physical labyrinth is a separate artwork on land beside the fossil dunes.
This script makes no claim that the labyrinth occupies the geological outcrop.
"""
from __future__ import annotations

from html import unescape
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
BASE = "https://oolita.es"
LASTMOD = "2026-08-26"

if not ROOT.is_dir():
    raise SystemExit(f"Missing built site: {ROOT}")


def visible(fragment: str) -> str:
    return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", " ", fragment))).strip()


def read(rel: str) -> tuple[Path, str]:
    path = ROOT / rel
    if not path.is_file():
        raise SystemExit(f"Missing geology authority page: {rel}")
    return path, path.read_text(encoding="utf-8")


P_RE = re.compile(r"(<p\b[^>]*>)(?P<body>[\s\S]*?)(</p>)", flags=re.I)
changed: set[str] = set()


def replace_paragraph(rel: str, markers: tuple[str, ...], new_inner: str) -> None:
    """Replace one paragraph by visible marker, accepting old or already-new states."""
    path, text = read(rel)
    expected = visible(new_inner)
    paragraphs = [(m, visible(m.group("body"))) for m in P_RE.finditer(text)]
    if any(rendered == expected for _, rendered in paragraphs):
        return

    for marker in markers:
        matches = [m for m, rendered in paragraphs if marker in rendered]
        if not matches:
            continue
        if len(matches) != 1:
            raise SystemExit(
                f"Expected one paragraph in {rel} for marker {marker!r}; found {len(matches)}"
            )
        match = matches[0]
        replacement = match.group(1) + new_inner + match.group(3)
        text = text[: match.start()] + replacement + text[match.end() :]
        path.write_text(text, encoding="utf-8")
        changed.add(rel)
        return

    raise SystemExit(f"Could not locate geology paragraph in {rel}: {markers!r}")


def replace_literals(rel: str, pairs: tuple[tuple[str, str], ...]) -> None:
    path, text = read(rel)
    before = text
    for old, new in pairs:
        text = text.replace(old, new)
    if text != before:
        path.write_text(text, encoding="utf-8")
        changed.add(rel)


# The Spanish page is already the stronger editorial model. Keep its tone while
# fixing the date order to mirror the official Junta range and ensuring local
# formation language remains cautious rather than universal.
replace_paragraph(
    "que-es-un-oolito/index.html",
    ("Muchos oolitos marinos se forman", "Hacen falta condiciones muy concretas"),
    "Muchos oolitos marinos se forman en agua somera rica en carbonato. El movimiento mantiene los granos girando mientras el carbonato de calcio se acumula en capas alrededor de un núcleo. En Los Escullos, los oolitos se formaron en agua marina poco profunda, agitada por el oleaje.",
)
replace_paragraph(
    "que-es-un-oolito/index.html",
    ("En Los Escullos, en la costa de Almería",),
    "En Los Escullos, en la costa de Almería, hay un sistema de eolianitas fósiles de composición oolítica: dunas de arena que el viento levantó hace entre 128.000 y 100.000 años y que después se endurecieron hasta volverse piedra, con la estratificación cruzada del viento todavía visible en el corte.",
)
replace_paragraph(
    "que-es-un-oolito/index.html",
    ("Entre 100.000 y 128.000 años", "Entre 128.000 y 100.000 años", "Más de cien mil años"),
    "Entre 128.000 y 100.000 años. Están catalogadas como AND082 en el Inventario Español de Lugares de Interés Geológico del IGME.",
)
replace_paragraph(
    "que-es-un-oolito/index.html",
    ("El proyecto se llama OOLITA por esa piedra",),
    "El proyecto se llama OOLITA por esa piedra. Un oolito crece por capas alrededor de un centro; un laberinto se recorre en círculos concéntricos hacia un centro. El parentesco está en la forma: capas, centro, tiempo.",
)

# English: match the factual restraint of the Spanish page and remove the neat
# but misleading claim that one scale simply 'takes a hundred thousand years'.
replace_paragraph(
    "en/what-is-an-ooid/index.html",
    ("It needs very particular conditions", "Many marine ooids form"),
    "Many marine ooids form in shallow water rich in carbonate. Movement keeps the grains turning while calcium carbonate builds in layers around a nucleus. At Los Escullos, the ooids formed in shallow seawater agitated by waves.",
)
replace_paragraph(
    "en/what-is-an-ooid/index.html",
    ("At Los Escullos, on the coast of Almería",),
    "At Los Escullos, on the coast of Almería in Spain, there is a system of fossil aeolianites of oolitic composition: sand dunes raised by wind between 128,000 and 100,000 years ago, later hardened into stone, with the wind's cross-bedding still visible in section.",
)
replace_paragraph(
    "en/what-is-an-ooid/index.html",
    ("More than a hundred thousand years", "Between 100,000 and 128,000 years", "Between 128,000 and 100,000 years"),
    "Between 128,000 and 100,000 years. They are catalogued as AND082 in Spain's national inventory of sites of geological interest (IGME).",
)
replace_paragraph(
    "en/what-is-an-ooid/index.html",
    ("The project is called OOLITA after that stone",),
    "The project is called OOLITA after that stone. An ooid grows in layers around a centre; a labyrinth is walked in concentric circuits towards a centre. The connection is in the form: layers, centre, time.",
)

# FAQ structured data can carry stale copies of the same answers even after the
# visible paragraph is corrected. Keep it in step without changing page shape.
replace_literals(
    "que-es-un-oolito/index.html",
    (
        (
            "Entre 100.000 y 128.000 años. Están catalogadas como AND082",
            "Entre 128.000 y 100.000 años. Están catalogadas como AND082",
        ),
        (
            "Más de cien mil años. Están catalogadas como AND082",
            "Entre 128.000 y 100.000 años. Están catalogadas como AND082",
        ),
    ),
)
replace_literals(
    "en/what-is-an-ooid/index.html",
    (
        (
            "More than a hundred thousand years. They are catalogued as AND082",
            "Between 128,000 and 100,000 years. They are catalogued as AND082",
        ),
        (
            "Between 100,000 and 128,000 years. They are catalogued as AND082",
            "Between 128,000 and 100,000 years. They are catalogued as AND082",
        ),
    ),
)

# About: correct the category error without making the sentence more academic.
# Keep the surrounding place/labyrinth phrases so the restrained editorial-link
# pass can still connect the concepts without adding a link block.
replace_paragraph(
    "sobre-oolita/index.html",
    ("El nombre viene del oolito", "El nombre viene de la oolita"),
    "El nombre viene de la oolita: una roca formada por oolitos, pequeños granos de carbonato que crecen por capas alrededor de un centro. Esa forma — capas, centro, tiempo — conecta la geología de Los Escullos con el dibujo del laberinto.",
)
replace_paragraph(
    "en/about/index.html",
    ("The name comes from oolite",),
    "The name comes from oolite: rock made largely of ooids, small carbonate grains that grow in layers around a centre. That form — layers, centre, time — connects the geology of Los Escullos with the drawing of the labyrinth.",
)

# Reader-facing invariants. These are deliberately phrased as content facts,
# not keyword counts.
required = {
    "que-es-un-oolito/index.html": (
        "128.000 y 100.000 años",
        "eolianitas fósiles de composición oolítica",
        "estratificación cruzada",
        "AND082",
        "Oolita es la roca formada por oolitos",
    ),
    "en/what-is-an-ooid/index.html": (
        "128,000 and 100,000 years",
        "fossil aeolianites of oolitic composition",
        "cross-bedding",
        "AND082",
        "Oolite is rock made of ooids",
    ),
    "sobre-oolita/index.html": (
        "El nombre viene de la oolita",
        "roca formada por oolitos",
        "geología de Los Escullos",
    ),
    "en/about/index.html": (
        "The name comes from oolite",
        "rock made largely of ooids",
        "geology of Los Escullos",
    ),
}
for rel, phrases in required.items():
    _, text = read(rel)
    rendered = visible(text)
    for phrase in phrases:
        if phrase not in rendered:
            raise SystemExit(f"Required geology wording missing from {rel}: {phrase}")

# Reject the two category errors that prompted this pass.
for rel, bad in (
    ("sobre-oolita/index.html", "El nombre viene del oolito: una roca"),
    ("en/about/index.html", "The name comes from oolite: rock made from tiny grains"),
):
    _, text = read(rel)
    if bad in visible(text):
        raise SystemExit(f"Stale geology shorthand remains in {rel}: {bad}")

# Freshen only the four routes this pass owns. No new URLs are introduced.
def route_for(rel: str) -> str:
    if rel.endswith("index.html"):
        return "/" + rel.removesuffix("index.html")
    raise SystemExit(f"Unexpected geology route: {rel}")

owned_routes = {route_for(rel) for rel in required}
sitemap = ROOT / "sitemap.xml"
if not sitemap.is_file():
    raise SystemExit("Missing sitemap.xml")

ET.register_namespace("", "http://www.sitemaps.org/schemas/sitemap/0.9")
tree = ET.parse(sitemap)
ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
seen: set[str] = set()
for url_el in tree.getroot().findall("sm:url", ns):
    loc = url_el.find("sm:loc", ns)
    if loc is None or not loc.text or not loc.text.startswith(BASE):
        continue
    route = loc.text[len(BASE):] or "/"
    if route not in owned_routes:
        continue
    seen.add(route)
    lastmod = url_el.find("sm:lastmod", ns)
    if lastmod is None:
        lastmod = ET.SubElement(url_el, "{http://www.sitemaps.org/schemas/sitemap/0.9}lastmod")
    lastmod.text = LASTMOD

missing = sorted(owned_routes - seen)
if missing:
    raise SystemExit(f"Geology authority routes missing from sitemap: {missing}")

tree.write(sitemap, encoding="utf-8", xml_declaration=True)

print(
    "OOLITA geology authority validated: existing bilingual geology/about routes refined; "
    f"{len(changed)} files changed; no new public route created."
)
