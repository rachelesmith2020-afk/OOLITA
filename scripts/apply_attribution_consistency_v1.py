#!/usr/bin/env python3
"""Apply the final OOLITA authorship, publishing and digital-collaboration credits."""
from __future__ import annotations

from pathlib import Path
import re
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")

if not ROOT.is_dir():
    raise SystemExit(f"Missing built site: {ROOT}")

MAIN_ES = "OOLITA · Un proyecto de Raquel Costantini con Vestini Tribe"
MAIN_EN = "OOLITA · A project by Raquel Costantini with Vestini Tribe"
BUILD_ES = "Sitio y mundo 3D desarrollados en colaboración por Raquel Costantini y Vestini Tribe."
BUILD_EN = "Website and 3D world developed collaboratively by Raquel Costantini and Vestini Tribe."

HOME_OLD_ES = "OOLITA reúne la obra y la escritura de Raquel Costantini con la labor editorial de Vestini Tribe."
HOME_NEW_ES = "OOLITA reúne la obra y la escritura de Raquel Costantini con la edición del libro por Vestini Tribe y el desarrollo conjunto de oolita.es y del mundo 3D en Three.js."
HOME_OLD_EN = "OOLITA brings together the art and writing of Raquel Costantini with the publishing work of Vestini Tribe."
HOME_NEW_EN = "OOLITA brings together Raquel Costantini’s art and writing, the book published by Vestini Tribe, and the collaborative development of oolita.es and the Three.js world."

ABOUT_OLD_ES = "OOLITA es el nombre público del proyecto que reúne una obra vinculada al lugar y la práctica editorial que crece a su alrededor. El laberinto de Los Escullos y el texto del libro OOLITA son obra de Raquel Costantini. Hallazgo es su práctica artística más amplia. Vestini Tribe publica el libro y las ediciones de OOLITA. Todo el proyecto se reúne en oolita.es."
ABOUT_NEW_ES = "OOLITA es el nombre público del proyecto que reúne una obra vinculada al lugar y la práctica editorial que crece a su alrededor. El laberinto de Los Escullos y el texto del libro OOLITA son obra de Raquel Costantini. Hallazgo es su práctica artística más amplia. Vestini Tribe publica el libro y las ediciones de OOLITA. La web oolita.es y el mundo 3D en Three.js se desarrollan de forma colaborativa entre Raquel Costantini y Vestini Tribe. Todo el proyecto se reúne en oolita.es."
ABOUT_OLD_EN = "OOLITA is the public identity of a project bringing together a place-based work and the publishing practice growing around it. The Los Escullos labyrinth and the text of the book OOLITA are works by Raquel Costantini. Hallazgo is her wider artistic practice. Vestini Tribe publishes the book and OOLITA editions. The whole project comes together at oolita.es."
ABOUT_NEW_EN = "OOLITA is the public identity of a project bringing together a place-based work and the publishing practice growing around it. The Los Escullos labyrinth and the text of the book OOLITA are works by Raquel Costantini. Hallazgo is their wider artistic practice. Vestini Tribe publishes the book and OOLITA editions. The website oolita.es and the Three.js 3D world are developed collaboratively by Raquel Costantini and Vestini Tribe. The whole project comes together at oolita.es."


def is_english(text: str) -> bool:
    return bool(re.search(r'<html\s+lang=["\']en(?:-[^"\']+)?["\']', text, flags=re.I))


def replace_optional(text: str, old: str, new: str) -> str:
    return text.replace(old, new) if old in text else text


def patch_footer(path: Path, text: str) -> str:
    english = is_english(text)
    main = MAIN_EN if english else MAIN_ES
    build = BUILD_EN if english else BUILD_ES
    main_variants = (
        "OOLITA · A Vestini Tribe project · Raquel Costantini, artist and author",
        "OOLITA · Raquel Costantini, artist and author · Vestini Tribe, publisher",
        "OOLITA · Raquel Costantini",
    ) if english else (
        "OOLITA · Un proyecto de Vestini Tribe · Raquel Costantini, artista y autora",
        "OOLITA · Raquel Costantini, artista y autora · Vestini Tribe, editorial",
        "OOLITA · Raquel Costantini",
    )
    build_variants = (
        "Site and 3D world built by Vestini Tribe.",
        "Site and 3D world developed by Vestini Tribe.",
    ) if english else (
        "Sitio y mundo 3D construidos por Vestini Tribe.",
        "Sitio y mundo 3D desarrollados por Vestini Tribe.",
    )

    match = re.search(r'<footer\b[\s\S]*?</footer>', text, flags=re.I)
    if not match:
        raise SystemExit(f"Missing footer in {path.relative_to(ROOT)}")
    footer = match.group(0)

    if main not in footer:
        for old in main_variants:
            if old in footer:
                footer = footer.replace(old, main, 1)
                break
        else:
            raise SystemExit(f"Known OOLITA footer identity missing in {path.relative_to(ROOT)}")

    if build not in footer:
        replaced = False
        for old in build_variants:
            if old in footer:
                footer = footer.replace(old, build, 1)
                replaced = True
                break
        if not replaced:
            addition = f'<span class="rot oolita-build-credit">{build}</span>'
            if "</div></div></footer>" in footer:
                footer = footer.replace("</div></div></footer>", addition + "</div></div></footer>", 1)
            else:
                footer = footer.replace("</footer>", addition + "</footer>", 1)

    return text[:match.start()] + footer + text[match.end():]


for path in sorted(ROOT.rglob("*.html")):
    text = path.read_text(encoding="utf-8")
    text = patch_footer(path, text)
    path.write_text(text, encoding="utf-8")

# Homepage: distinguish authorship, book publishing and shared digital work.
for rel, old_credit, new_credit, old_role, new_role in (
    ("index.html", HOME_OLD_ES, HOME_NEW_ES, "Vestini Tribe — editorial", "Vestini Tribe — editorial del libro"),
    ("en/index.html", HOME_OLD_EN, HOME_NEW_EN, "Vestini Tribe — publisher", "Vestini Tribe — book publisher"),
):
    path = ROOT / rel
    if not path.is_file():
        raise SystemExit(f"Missing homepage: {rel}")
    text = path.read_text(encoding="utf-8")
    text = replace_optional(text, old_credit, new_credit)
    text = replace_optional(text, old_role, new_role)
    if new_credit not in text:
        raise SystemExit(f"Final homepage attribution missing in {rel}")
    path.write_text(text, encoding="utf-8")

# About: keep artistic authorship, publishing and digital collaboration explicit.
for rel, old_credit, new_credit in (
    ("sobre-oolita/index.html", ABOUT_OLD_ES, ABOUT_NEW_ES),
    ("en/about/index.html", ABOUT_OLD_EN, ABOUT_NEW_EN),
):
    path = ROOT / rel
    if not path.is_file():
        raise SystemExit(f"Missing About page: {rel}")
    text = path.read_text(encoding="utf-8")
    text = replace_optional(text, old_credit, new_credit)
    if new_credit not in text:
        raise SystemExit(f"Final About attribution missing in {rel}")
    path.write_text(text, encoding="utf-8")

# 3D page: the browser world itself is a collaboration, not a Vestini-only build.
for rel, old, new in (
    (
        "mundo-3d/index.html",
        "El mundo se construye con Three.js, una biblioteca de JavaScript para crear escenas tridimensionales en el navegador.",
        "El mundo se desarrolla de forma colaborativa entre Raquel Costantini y Vestini Tribe con Three.js, una biblioteca de JavaScript para crear escenas tridimensionales en el navegador.",
    ),
    (
        "en/3d-world/index.html",
        "The world is built with Three.js, a JavaScript library for creating three-dimensional scenes in the browser.",
        "The world is developed collaboratively by Raquel Costantini and Vestini Tribe with Three.js, a JavaScript library for creating three-dimensional scenes in the browser.",
    ),
):
    path = ROOT / rel
    if not path.is_file():
        continue
    text = path.read_text(encoding="utf-8")
    text = replace_optional(text, old, new)
    path.write_text(text, encoding="utf-8")

# Legal controller language is intentionally untouched: attribution and data-controller
# responsibility are separate questions. Existing copyright ownership lines are also
# left unchanged because this pass does not infer legal ownership from collaboration.

for path in sorted(ROOT.rglob("*.html")):
    text = path.read_text(encoding="utf-8")
    footer = re.search(r'<footer\b[\s\S]*?</footer>', text, flags=re.I)
    if not footer:
        continue
    footer_text = footer.group(0)
    if "A Vestini Tribe project" in footer_text or "Un proyecto de Vestini Tribe" in footer_text:
        raise SystemExit(f"Vestini-only project credit remains in {path.relative_to(ROOT)}")
    if "Site and 3D world built by Vestini Tribe." in footer_text or "Sitio y mundo 3D construidos por Vestini Tribe." in footer_text:
        raise SystemExit(f"Vestini-only digital build credit remains in {path.relative_to(ROOT)}")

print("OOLITA attribution consistency validated: artist/author, book publisher, and collaborative digital work are distinct.")
