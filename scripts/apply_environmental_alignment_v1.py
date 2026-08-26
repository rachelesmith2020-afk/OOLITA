#!/usr/bin/env python3
"""Align OOLITA's environmental position with its interface and structured data.

This pass is deliberately narrow. It does not add environmental branding or hide
the physical labyrinth. It makes the existing principle structural:
- remote engagement comes before physical access in the homepage actions;
- the Cabo de Gata paragraph keeps the limit without tourism-sector rhetoric;
- the labyrinth is not classified to search engines as a TouristAttraction.
"""
from __future__ import annotations

from html import unescape
import json
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
BASE = "https://oolita.es"
LASTMOD = "2026-08-26"

if not ROOT.is_dir():
    raise SystemExit(f"Missing built site: {ROOT}")


def read(rel: str) -> tuple[Path, str]:
    path = ROOT / rel
    if not path.is_file():
        raise SystemExit(f"Missing environmental-alignment page: {rel}")
    return path, path.read_text(encoding="utf-8")


def visible(fragment: str) -> str:
    text = re.sub(r"<[^>]+>", " ", fragment)
    return re.sub(r"\s+", " ", unescape(text)).strip()


FINAL_ENV = {
    "index.html": (
        "El laberinto está allí. El camino también puede seguirse desde lejos. "
        "Mira más despacio. Aprende de la gente que vive y trabaja aquí. "
        "Deja el lugar como lo encontraste."
    ),
    "en/index.html": (
        "The labyrinth is there. The path can also be followed from a distance. "
        "Look more slowly. Learn from the people who live and work here. "
        "Leave the place as you found it."
    ),
}

ENV_NEEDLES = {
    "index.html": (
        "llevar más gente al laberinto",
        "llevar más gente a un solo laberinto",
        "llevar más gente a un solo punto",
        "no hace falta que todo termine en una visita",
    ),
    "en/index.html": (
        "bring more people to one labyrinth",
        "bring more people to a single labyrinth",
        "bring more people to one point",
        "not everything needs to end in a visit",
    ),
}

PARAGRAPH_RE = re.compile(r"(?P<open><p\b[^>]*>)(?P<body>[\s\S]*?)(?P<close></p>)", flags=re.I)


def patch_environment_paragraph(rel: str) -> None:
    path, text = read(rel)
    final = FINAL_ENV[rel]
    if text.count(final) == 1:
        return
    if text.count(final) > 1:
        raise SystemExit(f"Final environmental paragraph duplicated in {rel}")

    candidates: list[re.Match[str]] = []
    for match in PARAGRAPH_RE.finditer(text):
        paragraph = visible(match.group(0)).lower()
        if any(needle.lower() in paragraph for needle in ENV_NEEDLES[rel]):
            candidates.append(match)

    if len(candidates) != 1:
        raise SystemExit(
            f"Expected one environmental-limit paragraph in {rel}; found {len(candidates)}"
        )

    match = candidates[0]
    replacement = match.group("open") + final + match.group("close")
    text = text[:match.start()] + replacement + text[match.end():]
    path.write_text(text, encoding="utf-8")


for rel in FINAL_ENV:
    patch_environment_paragraph(rel)


ANCHOR_RE = re.compile(r"<a\b[^>]*>[\s\S]*?</a>", flags=re.I)


def hero_actions(rel: str, *, language: str) -> None:
    path, text = read(rel)
    if language == "es":
        old_lab = "VISITAR EL LABERINTO"
        final_lab = "EL LABERINTO · LOS ESCULLOS"
        follow = "SEGUIR EL CAMINO HASTA EL 3 DE ENERO"
        book = "VER EL LIBRO"
    else:
        old_lab = "VISIT THE LABYRINTH"
        final_lab = "THE LABYRINTH · LOS ESCULLOS"
        follow = "FOLLOW THE PATH TO 3 JANUARY"
        book = "VIEW THE BOOK"

    matches = list(ANCHOR_RE.finditer(text))

    def find_anchor(phrases: tuple[str, ...]) -> re.Match[str]:
        found = []
        for match in matches:
            label = visible(match.group(0)).upper()
            if any(phrase.upper() in label for phrase in phrases):
                found.append(match)
        if len(found) != 1:
            raise SystemExit(
                f"Expected one hero action matching {phrases!r} in {rel}; found {len(found)}"
            )
        return found[0]

    lab_match = find_anchor((old_lab, final_lab))
    follow_match = find_anchor((follow,))
    book_match = find_anchor((book,))

    if (
        follow_match.start() < book_match.start() < lab_match.start()
        and final_lab.upper() in visible(lab_match.group(0)).upper()
    ):
        return

    lab_html = lab_match.group(0)
    if old_lab.upper() in visible(lab_html).upper():
        lab_html, count = re.subn(re.escape(old_lab), final_lab, lab_html, count=1, flags=re.I)
        if count != 1:
            raise SystemExit(f"Could not relabel labyrinth hero action in {rel}")

    selected = sorted((lab_match, follow_match, book_match), key=lambda m: m.start())
    first, last = selected[0], selected[-1]
    cursor = first.end()
    for match in selected[1:]:
        if text[cursor:match.start()].strip():
            raise SystemExit(f"Hero actions are no longer adjacent in {rel}")
        cursor = match.end()

    replacement = "\n".join((follow_match.group(0), book_match.group(0), lab_html))
    text = text[:first.start()] + replacement + text[last.end():]
    path.write_text(text, encoding="utf-8")

    _, final_text = read(rel)
    final_matches = list(ANCHOR_RE.finditer(final_text))

    def one_pos(label: str) -> int:
        positions = [
            match.start()
            for match in final_matches
            if label.upper() in visible(match.group(0)).upper()
        ]
        if len(positions) != 1:
            raise SystemExit(f"Final hero action {label!r} missing or duplicated in {rel}")
        return positions[0]

    if not (one_pos(follow) < one_pos(book) < one_pos(final_lab)):
        raise SystemExit(f"Final hero action order is wrong in {rel}")


hero_actions("index.html", language="es")
hero_actions("en/index.html", language="en")


JSONLD_RE = re.compile(
    r'(?P<open><script\b(?=[^>]*\btype=["\']application/ld\+json["\'])[^>]*>)'
    r'(?P<body>[\s\S]*?)(?P<close></script>)',
    flags=re.I,
)


def remove_tourism_schema(rel: str) -> None:
    path, text = read(rel)

    def transform(match: re.Match[str]) -> str:
        body = match.group("body")
        if "TouristAttraction" not in body:
            return match.group(0)
        try:
            data = json.loads(body)
        except json.JSONDecodeError as exc:
            raise SystemExit(f"Invalid JSON-LD while removing TouristAttraction in {rel}: {exc}")

        changed = 0

        def walk(node) -> None:
            nonlocal changed
            if isinstance(node, dict):
                kind = node.get("@type")
                if kind == "TouristAttraction":
                    node["@type"] = "Place"
                    changed += 1
                elif isinstance(kind, list) and "TouristAttraction" in kind:
                    revised = ["Place" if item == "TouristAttraction" else item for item in kind]
                    deduped = []
                    for item in revised:
                        if item not in deduped:
                            deduped.append(item)
                    node["@type"] = deduped
                    changed += 1
                if "touristType" in node:
                    node.pop("touristType", None)
                    changed += 1
                for value in node.values():
                    walk(value)
            elif isinstance(node, list):
                for value in node:
                    walk(value)

        walk(data)
        if changed == 0:
            raise SystemExit(f"TouristAttraction text found but no schema type changed in {rel}")
        return match.group("open") + json.dumps(
            data, ensure_ascii=False, separators=(",", ":")
        ) + match.group("close")

    text = JSONLD_RE.sub(transform, text)
    if "TouristAttraction" in text:
        raise SystemExit(f"TouristAttraction remains in {rel}")
    path.write_text(text, encoding="utf-8")


for rel in (
    "index.html",
    "en/index.html",
    "laberinto/index.html",
    "en/labyrinth/index.html",
):
    remove_tourism_schema(rel)


changed_routes = {"/", "/en/", "/laberinto/", "/en/labyrinth/"}
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
    raise SystemExit(f"Environmental-alignment routes missing from sitemap: {sorted(missing)}")
tree.write(sitemap, encoding="utf-8", xml_declaration=True)


for rel, final in FINAL_ENV.items():
    _, text = read(rel)
    if text.count(final) != 1:
        raise SystemExit(f"Final restrained environmental copy missing or duplicated in {rel}")

for rel in ("index.html", "en/index.html", "laberinto/index.html", "en/labyrinth/index.html"):
    _, text = read(rel)
    if "TouristAttraction" in text:
        raise SystemExit(f"Tourism schema regression in {rel}")

print("OOLITA environmental alignment validated: remote-first actions, implicit limit, no TouristAttraction schema.")
