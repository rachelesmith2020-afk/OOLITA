#!/usr/bin/env python3
"""Add the reviewed OOLITA editorial internal links without changing visible copy.

This pass is intentionally narrow. It connects the existing place, geology and
labyrinth pages through phrases that already occur in the published prose. It
adds no new copy, no footer/link blocks, no keyword lists and no styling.

The script fails closed if a target paragraph has drifted, if a phrase is
ambiguous, or if adding a link would alter the rendered text.
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


def rendered(fragment: str) -> str:
    text = unescape(re.sub(r"<[^>]+>", "", fragment))
    return re.sub(r"\s+", " ", text).strip()


def read(rel: str) -> tuple[Path, str]:
    path = ROOT / rel
    if not path.is_file():
        raise SystemExit(f"Missing editorial-link target: {rel}")
    return path, path.read_text(encoding="utf-8")


def route_for(rel: str) -> str:
    if rel == "index.html":
        return "/"
    if rel.endswith("index.html"):
        return "/" + rel.removesuffix("index.html")
    raise SystemExit(f"Editorial-link target is not an index page: {rel}")


P_RE = re.compile(r"(<p\b[^>]*>)(?P<body>.*?)(</p>)", flags=re.I | re.S)
A_RE = re.compile(r"<a\b(?P<attrs>[^>]*)>(?P<body>.*?)</a>", flags=re.I | re.S)
changed_routes: set[str] = set()
changes: list[tuple[str, str, str]] = []


def find_target(text: str, rel: str, markers: tuple[str, ...]) -> re.Match[str]:
    matches: list[re.Match[str]] = []
    for match in P_RE.finditer(text):
        visible = rendered(match.group("body"))
        if all(marker in visible for marker in markers):
            matches.append(match)
    if len(matches) != 1:
        raise SystemExit(
            f"Expected one editorial-link paragraph in {rel} for {markers!r}; found {len(matches)}"
        )
    return matches[0]


def existing_exact_link(body: str, phrase: str, href: str) -> bool:
    for anchor in A_RE.finditer(body):
        attrs = anchor.group("attrs")
        href_match = re.search(r"\bhref\s*=\s*([\"'])(.*?)\1", attrs, flags=re.I | re.S)
        if href_match and href_match.group(2) == href and rendered(anchor.group("body")) == phrase:
            return True
    return False


def link_phrase(rel: str, markers: tuple[str, ...], phrase: str, href: str) -> None:
    path, text = read(rel)
    match = find_target(text, rel, markers)
    body = match.group("body")
    before_visible = rendered(body)

    if existing_exact_link(body, phrase, href):
        return

    if phrase not in before_visible:
        raise SystemExit(f"Phrase {phrase!r} is not visible in the target paragraph in {rel}")

    raw_count = body.count(phrase)
    if raw_count != 1:
        raise SystemExit(
            f"Expected one raw occurrence of {phrase!r} in target paragraph {rel}; found {raw_count}"
        )

    new_body = body.replace(phrase, f'<a href="{href}">{phrase}</a>', 1)
    after_visible = rendered(new_body)
    if after_visible != before_visible:
        raise SystemExit(
            f"Editorial link changed visible copy in {rel}: {before_visible!r} -> {after_visible!r}"
        )

    replacement = match.group(1) + new_body + match.group(3)
    new_text = text[: match.start()] + replacement + text[match.end() :]
    path.write_text(new_text, encoding="utf-8")

    _, verified_text = read(rel)
    verified_match = find_target(verified_text, rel, markers)
    if not existing_exact_link(verified_match.group("body"), phrase, href):
        raise SystemExit(f"Editorial link verification failed in {rel}: {phrase!r} -> {href}")
    if rendered(verified_match.group("body")) != before_visible:
        raise SystemExit(f"Visible-copy invariant failed after write in {rel}")

    changed_routes.add(route_for(rel))
    changes.append((rel, phrase, href))


link_phrase(
    "index.html",
    ("El laberinto caminable está en Los Escullos", "Parque Natural de Cabo de Gata-Níjar"),
    "Parque Natural de Cabo de Gata-Níjar",
    "/cabo-de-gata/",
)
link_phrase(
    "en/index.html",
    ("The walkable labyrinth is at Los Escullos", "Cabo de Gata-Níjar Natural Park"),
    "Cabo de Gata-Níjar Natural Park",
    "/en/cabo-de-gata/",
)

link_phrase(
    "laberinto/index.html",
    ("Desde el aparcamiento de Los Escullos", "Parque Natural de Cabo de Gata-Níjar"),
    "Parque Natural de Cabo de Gata-Níjar",
    "/cabo-de-gata/",
)
link_phrase(
    "en/labyrinth/index.html",
    ("From the Los Escullos car park", "Cabo de Gata-Níjar Natural Park"),
    "Cabo de Gata-Níjar Natural Park",
    "/en/cabo-de-gata/",
)

link_phrase(
    "cabo-de-gata/index.html",
    ("OOLITA empieza", "Los Escullos"),
    "laberinto",
    "/que-es-un-laberinto/",
)
link_phrase(
    "en/cabo-de-gata/index.html",
    ("OOLITA begins", "Los Escullos"),
    "labyrinth",
    "/en/what-is-a-labyrinth/",
)

link_phrase(
    "que-es-un-laberinto/index.html",
    ("Un laberinto de tres metros de diámetro", "se puede recorrer"),
    "Un laberinto de tres metros de diámetro",
    "/laberinto/",
)
link_phrase(
    "en/what-is-a-labyrinth/index.html",
    ("A three-metre labyrinth", "small clearing"),
    "A three-metre labyrinth",
    "/en/labyrinth/",
)

link_phrase(
    "que-es-un-oolito/index.html",
    ("En Los Escullos", "eolianitas fósiles"),
    "Los Escullos",
    "/cabo-de-gata/",
)
link_phrase(
    "en/what-is-an-ooid/index.html",
    ("At Los Escullos", "fossil aeolianites"),
    "Los Escullos",
    "/en/cabo-de-gata/",
)

# About can be reached twice in the deployment sequence: once while the mirrored
# source still carries the older "oolito" shorthand, and again after the geology
# pass has corrected it to "oolita". Accept exactly those two known states, link
# whichever term is actually present, and still fail closed on any other drift.
ABOUT_ES = ("geología de Los Escullos", "dibujo del laberinto")
_, about_es_text = read("sobre-oolita/index.html")
about_es_match = find_target(about_es_text, "sobre-oolita/index.html", ABOUT_ES)
about_es_visible = rendered(about_es_match.group("body"))
if "El nombre viene de la oolita" in about_es_visible:
    about_es_term = "oolita"
elif "El nombre viene del oolito" in about_es_visible:
    about_es_term = "oolito"
else:
    raise SystemExit("Unexpected Spanish About geology source state")
link_phrase("sobre-oolita/index.html", ABOUT_ES, about_es_term, "/que-es-un-oolito/")
link_phrase("sobre-oolita/index.html", ABOUT_ES, "Los Escullos", "/cabo-de-gata/")
link_phrase("sobre-oolita/index.html", ABOUT_ES, "laberinto", "/que-es-un-laberinto/")

ABOUT_EN = ("The name comes from oolite", "geology of Los Escullos", "drawing of the labyrinth")
link_phrase("en/about/index.html", ABOUT_EN, "oolite", "/en/what-is-an-ooid/")
link_phrase("en/about/index.html", ABOUT_EN, "Los Escullos", "/en/cabo-de-gata/")
link_phrase("en/about/index.html", ABOUT_EN, "labyrinth", "/en/what-is-a-labyrinth/")


if changed_routes:
    sitemap = ROOT / "sitemap.xml"
    if not sitemap.is_file():
        raise SystemExit("Missing sitemap.xml")

    ET.register_namespace("", "http://www.sitemaps.org/schemas/sitemap/0.9")
    tree = ET.parse(sitemap)
    xml_root = tree.getroot()
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    seen: set[str] = set()

    for url_el in xml_root.findall("sm:url", ns):
        loc = url_el.find("sm:loc", ns)
        if loc is None or not loc.text:
            continue
        url = loc.text.strip()
        if not url.startswith(BASE):
            continue
        route = url[len(BASE) :] or "/"
        if route not in changed_routes:
            continue
        seen.add(route)
        lastmod = url_el.find("sm:lastmod", ns)
        if lastmod is None:
            lastmod = ET.SubElement(url_el, "{http://www.sitemaps.org/schemas/sitemap/0.9}lastmod")
        lastmod.text = LASTMOD

    missing = sorted(changed_routes - seen)
    if missing:
        raise SystemExit(f"Editorial-link routes missing from sitemap: {missing}")

    tree.write(sitemap, encoding="utf-8", xml_declaration=True)

print(
    f"OOLITA editorial internal links validated: {len(changes)} anchors added across "
    f"{len(changed_routes)} routes; visible copy unchanged."
)
