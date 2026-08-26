#!/usr/bin/env python3
"""Align OOLITA's environmental position with its interface and structured data.

This is deliberately narrow. It does not add environmental branding or hide the
physical labyrinth. It changes three things only:
- the homepage's first actions favour remote engagement before physical access;
- the Cabo de Gata paragraph states restraint without tourism-sector language;
- the labyrinth is no longer described to search engines as a TouristAttraction.
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


def replace_state(rel: str, old: str, new: str) -> None:
    path, text = read(rel)
    if old in text:
        path.write_text(text.replace(old, new, 1), encoding="utf-8")
        return
    if new in text:
        return
    raise SystemExit(f"Neither old nor final environmental copy found in {rel}")


ENV_COPY = {
    "index.html": (
        "No se trata de llevar más gente al laberinto. Cabo de Gata no necesita más presión turística. Mira más despacio. Aprende de la gente que vive y trabaja aquí. Deja el lugar como lo encontraste.",
        "El laberinto está allí. No hace falta que todo termine en una visita. El camino también se puede seguir desde lejos. Mira más despacio. Aprende de la gente que vive y trabaja aquí. Deja el lugar como lo encontraste.",
    ),
    "en/index.html": (
        "The point is not to bring more people to one labyrinth. Cabo de Gata does not need more tourism pressure. Look more slowly. Learn from the people who live and work here. Leave the place as you found it.",
        "The labyrinth is there. Not everything needs to end in a visit. The path can be followed from a distance too. Look more slowly. Learn from the people who live and work here. Leave the place as you found it.",
    ),
}

for rel, (old, new) in ENV_COPY.items():
    replace_state(rel, old, new)


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

    lab_html = lab_match.group(0)
    if old_lab.upper() in visible(lab_html).upper():
        revised, count = re.subn(re.escape(old_lab), final_lab, lab_html, count=1, flags=re.I)
        if count != 1:
            raise SystemExit(f"Could not relabel labyrinth hero action in {rel}")
        lab_html = revised

    selected = sorted((lab_match, follow_match, book_match), key=lambda m: m.start())
    first, last = selected[0], selected[-1]

    # These are the three adjacent hero actions. Refuse to move them if another
    # element has been inserted between them: that would require a fresh review.
    cursor = first.end()
    for match in selected[1:]:
        gap = text[cursor:match.start()]
        if gap.strip():
            raise SystemExit(f"Hero actions are no longer adjacent in {rel}")
        cursor = match.end()

    replacement = "\n".join((follow_match.group(0), book_match.group(0), lab_html))
    text = text[:first.start()] + replacement + text[last.end():]
    path.write_text(text, encoding="utf-8")

    # Final order must be remote path, book, physical labyrinth.
    _, final_text = read(rel)
    anchors = [(m.start(), visible(m.group(0)).upper()) for m in ANCHOR_RE.finditer(final_text)]

    def one_pos(label: str) -> int:
        positions = [pos for pos, value in anchors if label.upper() in value]
        if len(positions) != 1:
            raise SystemExit(f"Final hero action {label!r} missing or duplicated in {rel}")
        return positions[0]

    p_follow = one_pos(follow)
    p_book = one_pos(book)
    p_lab = one_pos(final_lab)
    if not (p_follow < p_book < p_lab):
        raise SystemExit(f"Final hero action order is wrong in {rel}")
    if old_lab.upper() in visible(final_text).upper():
        raise SystemExit(f"Old visit-led labyrinth CTA remains in {rel}")


hero_actions("index.html", language="es")
hero_actions("en/index.html", language="en")


JSONLD_RE = re.compile(
    r'(?P<open><script\b(?=[^>]*\btype=["\']application/ld\+json["\'])[^>]*>)(?P<body>[\s\S]*?)(?P<close></script>)',
    flags=re.I,
)


def remove_tourism_schema(rel: str) -> None:
    path, text = read(rel)
    changed = 0

    def transform(match: re.Match[str]) -> str:
        nonlocal changed
        body = match.group("body")
        if "TouristAttraction" not in body:
            return match.group(0)
        try:
            data = json.loads(body)
        except json.JSONDecodeError as exc:
            raise SystemExit(f"Invalid JSON-LD while removing TouristAttraction in {rel}: {exc}")

        local_changes = 0

        def walk(node):
            nonlocal local_changes
            if isinstance(node, dict):
                kind = node.get("@type")
                if kind == "TouristAttraction":
                    node["@type"] = "Place"
                    local_changes += 1
                elif isinstance(kind, list) and "TouristAttraction" in kind:
                    revised = ["Place" if item == "TouristAttraction" else item for item in kind]
                    deduped = []
                    for item in revised:
                        if item not in deduped:
                            deduped.append(item)
                    node["@type"] = deduped
                    local_changes += 1
                # touristType has no place in the final non-tourism classification.
                if "touristType" in node:
                    node.pop("touristType", None)
                    local_changes += 1
                for value in node.values():
                    walk(value)
            elif isinstance(node, list):
                for value in node:
                    walk(value)

        walk(data)
        if local_changes == 0:
            raise SystemExit(f"TouristAttraction text found but no schema type changed in {rel}")
        changed += local_changes
        rendered = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
        return match.group("open") + rendered + match.group("close")

    text = JSONLD_RE.sub(transform, text)
    if changed == 0:
        # Reconstructed pages after the first successful deployment are already final.
        if "TouristAttraction" in text:
            raise SystemExit(f"TouristAttraction remains outside parseable JSON-LD in {rel}")
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


# Refresh only the four routes materially changed here.
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


for rel, (_, final_copy) in ENV_COPY.items():
    _, text = read(rel)
    if text.count(final_copy) != 1:
        raise SystemExit(f"Final restrained environmental copy missing or duplicated in {rel}")

for rel in ("index.html", "en/index.html", "laberinto/index.html", "en/labyrinth/index.html"):
    _, text = read(rel)
    if "TouristAttraction" in text:
        raise SystemExit(f"Tourism schema regression in {rel}")

print("OOLITA environmental alignment validated: remote-first actions, restrained copy, no TouristAttraction schema.")
