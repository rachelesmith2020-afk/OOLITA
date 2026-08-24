#!/usr/bin/env python3
"""Final OOLITA attribution pass, applied after the editorial voice audit.

Public truth:
- Raquel Costantini is the artist and author.
- Vestini Tribe publishes the book.
- oolita.es and the Three.js world are collaborative work by both.

Privacy-controller and copyright ownership statements are intentionally outside
this pass: those are separate legal questions, not inferred from production roles.
"""
from __future__ import annotations

from pathlib import Path
import re
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")

MAIN_ES = "OOLITA · Un proyecto de Raquel Costantini con Vestini Tribe"
MAIN_EN = "OOLITA · A project by Raquel Costantini with Vestini Tribe"
BUILD_ES = "Sitio y mundo 3D desarrollados en colaboración por Raquel Costantini y Vestini Tribe."
BUILD_EN = "Website and 3D world developed collaboratively by Raquel Costantini and Vestini Tribe."

HOME_ES = "Raquel Costantini hizo el laberinto y escribió el libro. Vestini Tribe publica el libro. La web oolita.es y el mundo 3D en Three.js se desarrollan en colaboración entre Raquel Costantini y Vestini Tribe."
HOME_EN = "Raquel Costantini made the labyrinth and wrote the book. Vestini Tribe publishes the book. The website oolita.es and the Three.js world are developed collaboratively by Raquel Costantini and Vestini Tribe."

ABOUT_ES = "OOLITA tiene tres formas: el laberinto de Los Escullos, el libro y el mundo 3D. El laberinto y el texto del libro son obra de Raquel Costantini. Hallazgo es su práctica artística más amplia. Vestini Tribe publica el libro y las ediciones. La web oolita.es y el mundo 3D en Three.js se desarrollan en colaboración entre Raquel Costantini y Vestini Tribe. Todo se reúne aquí: oolita.es."
ABOUT_EN = "OOLITA has three forms: the labyrinth at Los Escullos, the book and the 3D world. The labyrinth and the text of the book are by Raquel Costantini. Hallazgo is their wider artistic practice. Vestini Tribe publishes the book and the editions. The website oolita.es and the Three.js world are developed collaboratively by Raquel Costantini and Vestini Tribe. Everything meets here: oolita.es."

THREE_ES = "Three.js es la herramienta que hace caminable la tercera forma en el navegador. El mundo 3D se desarrolla en colaboración entre Raquel Costantini y Vestini Tribe."
THREE_EN = "Three.js is the tool that makes the third form walkable in the browser. The 3D world is developed collaboratively by Raquel Costantini and Vestini Tribe."

LEGACY_HOME_ES = "OOLITA reúne la obra y la escritura de Raquel Costantini con la labor editorial de Vestini Tribe."
LEGACY_HOME_EN = "OOLITA brings together the art and writing of Raquel Costantini with the publishing work of Vestini Tribe."
LEGACY_ABOUT_ES = "OOLITA es el nombre público del proyecto"
LEGACY_ABOUT_EN = "OOLITA is the public identity of a project"


def english(text: str) -> bool:
    return bool(re.search(r'<html\s+lang=["\']en(?:-[^"\']+)?["\']', text, flags=re.I))


def visible_text(html: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html)).strip()


def replace_paragraph_containing(text: str, marker: str, replacement: str) -> tuple[str, bool]:
    if replacement in text:
        return text, True
    for match in re.finditer(r'(<p\b[^>]*>)([\s\S]*?)(</p>)', text, flags=re.I):
        if marker in visible_text(match.group(2)):
            return text[:match.start()] + match.group(1) + replacement + match.group(3) + text[match.end():], True
    return text, False


def remove_paragraphs_containing(text: str, markers: tuple[str, ...]) -> str:
    """Remove stale duplicate credit paragraphs without touching surrounding copy."""
    matches = list(re.finditer(r'<p\b[^>]*>[\s\S]*?</p>', text, flags=re.I))
    for match in reversed(matches):
        visible = visible_text(match.group(0))
        if any(marker in visible for marker in markers):
            text = text[:match.start()] + text[match.end():]
    return text


def patch_footer(path: Path, text: str) -> str:
    match = re.search(r'<footer\b[\s\S]*?</footer>', text, flags=re.I)
    if not match:
        return text

    is_en = english(text)
    main = MAIN_EN if is_en else MAIN_ES
    build = BUILD_EN if is_en else BUILD_ES
    footer = match.group(0)

    main_variants = (
        "OOLITA · A Vestini Tribe project · Raquel Costantini, artist and author",
        "OOLITA · Raquel Costantini, artist and author · Vestini Tribe, publisher",
        "OOLITA · Raquel Costantini",
    ) if is_en else (
        "OOLITA · Un proyecto de Vestini Tribe · Raquel Costantini, artista y autora",
        "OOLITA · Raquel Costantini, artista y autora · Vestini Tribe, editorial",
        "OOLITA · Raquel Costantini",
    )
    build_variants = (
        "Site and 3D world built by Vestini Tribe.",
        "Site and 3D world developed by Vestini Tribe.",
    ) if is_en else (
        "Sitio y mundo 3D construidos por Vestini Tribe.",
        "Sitio y mundo 3D desarrollados por Vestini Tribe.",
    )

    if main not in footer:
        for old in main_variants:
            if old in footer:
                footer = footer.replace(old, main, 1)
                break

    if build not in footer:
        for old in build_variants:
            if old in footer:
                footer = footer.replace(old, build, 1)
                break
        else:
            addition = f'<span class="rot oolita-build-credit">{build}</span>'
            if "</div></div></footer>" in footer:
                footer = footer.replace("</div></div></footer>", addition + "</div></div></footer>", 1)
            else:
                footer = footer.replace("</footer>", addition + "</footer>", 1)

    return text[:match.start()] + footer + text[match.end():]


if not ROOT.is_dir():
    raise SystemExit(f"Missing built site: {ROOT}")

# Global footer identity and digital-production credit.
for path in sorted(ROOT.rglob("*.html")):
    text = path.read_text(encoding="utf-8")
    text = patch_footer(path, text)
    path.write_text(text, encoding="utf-8")

# Homepage credit paragraph and role label.
for rel, marker, final, old_role, new_role, legacy in (
    ("index.html", "Raquel Costantini hizo el laberinto", HOME_ES, "Vestini Tribe — editorial", "Vestini Tribe — editorial del libro", LEGACY_HOME_ES),
    ("en/index.html", "Raquel Costantini made the labyrinth", HOME_EN, "Vestini Tribe — publisher", "Vestini Tribe — book publisher", LEGACY_HOME_EN),
):
    path = ROOT / rel
    text = path.read_text(encoding="utf-8")
    text, found = replace_paragraph_containing(text, marker, final)
    if not found:
        fallback = "OOLITA reúne la obra y la escritura" if rel == "index.html" else "OOLITA brings together the art and writing"
        text, found = replace_paragraph_containing(text, fallback, final)
    if not found:
        raise SystemExit(f"Could not locate homepage project credit in {rel}")
    # A reconstructed live origin can already contain both the older summary and
    # the final credit. Keep one authoritative statement, not two adjacent versions.
    text = remove_paragraphs_containing(text, (legacy,))
    text = text.replace(old_role, new_role)
    path.write_text(text, encoding="utf-8")

# About: preserve the voice-audited paragraph, add the actual digital collaboration,
# and use the user's requested English pronoun.
for rel, marker, final, legacy in (
    ("sobre-oolita/index.html", "OOLITA tiene tres formas:", ABOUT_ES, LEGACY_ABOUT_ES),
    ("en/about/index.html", "OOLITA has three forms:", ABOUT_EN, LEGACY_ABOUT_EN),
):
    path = ROOT / rel
    text = path.read_text(encoding="utf-8")
    text, found = replace_paragraph_containing(text, marker, final)
    if not found:
        text, found = replace_paragraph_containing(text, legacy, final)
    if not found:
        raise SystemExit(f"Could not locate About project credit in {rel}")
    # Remove a stale institutional-version paragraph if an earlier deployment
    # left it alongside the voice-audited version.
    if final in text:
        text = remove_paragraphs_containing(text, (legacy,))
    path.write_text(text, encoding="utf-8")

# 3D explainer: say explicitly who develops the browser world.
for rel, marker, final in (
    ("mundo-3d/index.html", "Three.js es la herramienta que hace caminable", THREE_ES),
    ("en/3d-world/index.html", "Three.js is the tool that makes the third form walkable", THREE_EN),
):
    path = ROOT / rel
    if not path.is_file():
        raise SystemExit(f"Missing 3D page: {rel}")
    text = path.read_text(encoding="utf-8")
    text, found = replace_paragraph_containing(text, marker, final)
    if not found and final not in text:
        raise SystemExit(f"Could not locate Three.js explanatory paragraph in {rel}")
    path.write_text(text, encoding="utf-8")

# Final invariants.
for rel, needles in {
    "index.html": (HOME_ES, MAIN_ES, BUILD_ES, "Vestini Tribe — editorial del libro"),
    "en/index.html": (HOME_EN, MAIN_EN, BUILD_EN, "Vestini Tribe — book publisher"),
    "sobre-oolita/index.html": (ABOUT_ES, MAIN_ES, BUILD_ES),
    "en/about/index.html": (ABOUT_EN, MAIN_EN, BUILD_EN),
    "mundo-3d/index.html": (THREE_ES, MAIN_ES, BUILD_ES),
    "en/3d-world/index.html": (THREE_EN, MAIN_EN, BUILD_EN),
}.items():
    text = (ROOT / rel).read_text(encoding="utf-8")
    for needle in needles:
        if needle not in text:
            raise SystemExit(f"Attribution invariant missing in {rel}: {needle}")

for rel, obsolete in {
    "index.html": LEGACY_HOME_ES,
    "en/index.html": LEGACY_HOME_EN,
    "sobre-oolita/index.html": LEGACY_ABOUT_ES,
    "en/about/index.html": LEGACY_ABOUT_EN,
}.items():
    text = (ROOT / rel).read_text(encoding="utf-8")
    if obsolete in visible_text(text):
        raise SystemExit(f"Legacy duplicate attribution remains in {rel}: {obsolete}")

for path in sorted(ROOT.rglob("*.html")):
    text = path.read_text(encoding="utf-8")
    footer = re.search(r'<footer\b[\s\S]*?</footer>', text, flags=re.I)
    if not footer:
        continue
    f = footer.group(0)
    for obsolete in (
        "A Vestini Tribe project",
        "Un proyecto de Vestini Tribe",
        "Site and 3D world built by Vestini Tribe.",
        "Sitio y mundo 3D construidos por Vestini Tribe.",
    ):
        if obsolete in f:
            raise SystemExit(f"Obsolete attribution remains in {path.relative_to(ROOT)}: {obsolete}")

print("OOLITA final attribution consistency validated successfully.")
