#!/usr/bin/env python3
"""Remove the last pieces of explanatory website prose from OOLITA.

This pass is deliberately small. It does not smooth the project's oddness or
rewrite its core motifs. It only removes repetition, speculation and abstract
connective language where the concrete material already says enough.
"""
from __future__ import annotations

from html import unescape
from pathlib import Path
import re
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")


def read(rel: str) -> tuple[Path, str]:
    path = ROOT / rel
    if not path.is_file():
        raise SystemExit(f"Missing connective-copy page: {rel}")
    return path, path.read_text(encoding="utf-8")


def visible(fragment: str) -> str:
    text = unescape(re.sub(r"<[^>]+>", " ", fragment))
    return re.sub(r"\s+", " ", text).strip()


def paragraph_matches(text: str, marker: str) -> list[re.Match[str]]:
    pattern = re.compile(r"<p\b[^>]*>.*?</p>", flags=re.I | re.S)
    return [m for m in pattern.finditer(text) if marker in visible(m.group(0))]


def replace_paragraph(rel: str, marker: str, new_inner: str) -> None:
    path, text = read(rel)
    matches = paragraph_matches(text, marker)
    if len(matches) != 1:
        raise SystemExit(f"Expected one paragraph containing {marker!r} in {rel}; found {len(matches)}")
    match = matches[0]
    opening = re.match(r"<p\b[^>]*>", match.group(0), flags=re.I)
    if not opening:
        raise SystemExit(f"Could not preserve paragraph opening in {rel}")
    replacement = opening.group(0) + new_inner + "</p>"
    path.write_text(text[:match.start()] + replacement + text[match.end():], encoding="utf-8")


def remove_paragraph(rel: str, marker: str) -> None:
    path, text = read(rel)
    if marker not in visible(text):
        return
    matches = paragraph_matches(text, marker)
    if len(matches) != 1:
        raise SystemExit(f"Expected one removable paragraph containing {marker!r} in {rel}; found {len(matches)}")
    match = matches[0]
    path.write_text(text[:match.start()] + text[match.end():], encoding="utf-8")


# TEXTILE EDITION — the product page was explaining the same reveal three times
# and speculating about future editions. Keep the material fact and the Sunday
# reveal; remove the brand-plan paragraph around them.
replace_paragraph(
    "en/editions/t-shirt/index.html",
    "The first textile edition carries the labyrinth into cloth.",
    "The first textile edition carries the labyrinth into cloth.",
)
replace_paragraph(
    "ediciones/camiseta/index.html",
    "La primera edición textil lleva el laberinto a la tela.",
    "La primera edición textil lleva el laberinto a la tela.",
)
remove_paragraph(
    "en/editions/t-shirt/index.html",
    "This first piece is a 200 gsm organic-cotton T-shirt",
)
remove_paragraph(
    "ediciones/camiseta/index.html",
    "Esta primera pieza es una camiseta de algodón orgánico de 200 gramos",
)
replace_paragraph(
    "en/editions/t-shirt/index.html",
    "The garment appears first",
    "The garment appears first blank. Each Sunday, a little more of the design appears.",
)
replace_paragraph(
    "ediciones/camiseta/index.html",
    "La prenda aparece primero en blanco",
    "La prenda aparece primero en blanco. Cada domingo aparece un poco más del diseño.",
)

# 3D WORLD — keep the terrain measurements and material reduction; drop the
# abstract 'attention' tail. The physical requirements are enough.
replace_paragraph(
    "en/3d-world/index.html",
    "The landscape begins with measurements of the real terrain.",
    "The landscape begins with measurements of the real terrain. Stone, sea, scale, horizon, sound and the low light of Cabo de Gata are reduced to what the walk needs. Only what is needed remains: orientation and scale.",
)
replace_paragraph(
    "mundo-3d/index.html",
    "El paisaje parte de mediciones del terreno real.",
    "El paisaje parte de mediciones del terreno real. Piedra, mar, escala, horizonte, sonido y la luz baja de Cabo de Gata se reducen a lo que necesita el recorrido. Solo queda lo necesario: orientación y escala.",
)

# 22 SUNDAYS — the images themselves are strong. Do not tell the reader how the
# archive ought to be read; stop after the concrete relation between one and 22.
replace_paragraph(
    "en/sundays/index.html",
    "The images do not illustrate",
    'The images do not illustrate <a href="/en/editions/book/">the book</a>, and they do not document the labyrinth. They are something else: stone, water, light, shadow, an animal, a page. Each one stands on its own. The twenty-two together make the walk.',
)
replace_paragraph(
    "domingos/index.html",
    "Las imágenes no ilustran",
    'Las imágenes no ilustran <a href="/ediciones/libro/">el libro</a> ni documentan el laberinto. Son otra cosa: piedra, agua, luz, sombra, un animal, una página. Cada una se sostiene sola. Las veintidós juntas hacen el recorrido.',
)

stale = {
    "en/editions/t-shirt/index.html": (
        "Future numbered editions may explore images from Hallazgo",
        "collaborations rooted in the materials and craft knowledge of Cabo de Gata",
        "its relationship to the labyrinth",
        "This first piece is a 200 gsm organic-cotton T-shirt",
    ),
    "ediciones/camiseta/index.html": (
        "Las futuras ediciones numeradas podrán explorar imágenes de Hallazgo",
        "colaboraciones arraigadas en los materiales y saberes artesanos de Cabo de Gata",
        "su relación con el laberinto",
        "Esta primera pieza es una camiseta de algodón orgánico de 200 gramos",
    ),
    "en/3d-world/index.html": (
        "support orientation, scale and attention along the path",
    ),
    "mundo-3d/index.html": (
        "sostienen la orientación, la escala y la atención durante el camino",
    ),
    "en/sundays/index.html": (
        "the archive reads as well opened at random as it does from the beginning",
    ),
    "domingos/index.html": (
        "el archivo se lee igual de bien empezando por el uno que abriendo cualquiera al azar",
    ),
}
required = {
    "en/editions/t-shirt/index.html": (
        "The first textile edition carries the labyrinth into cloth.",
        "The garment appears first blank. Each Sunday, a little more of the design appears.",
        "Stanley/Stella Blaster 2.0",
    ),
    "ediciones/camiseta/index.html": (
        "La primera edición textil lleva el laberinto a la tela.",
        "La prenda aparece primero en blanco. Cada domingo aparece un poco más del diseño.",
        "Stanley/Stella Blaster 2.0",
    ),
    "en/3d-world/index.html": (
        "Only what is needed remains: orientation and scale.",
    ),
    "mundo-3d/index.html": (
        "Solo queda lo necesario: orientación y escala.",
    ),
    "en/sundays/index.html": (
        "Each one stands on its own. The twenty-two together make the walk.",
    ),
    "domingos/index.html": (
        "Cada una se sostiene sola. Las veintidós juntas hacen el recorrido.",
    ),
}

for rel, phrases in stale.items():
    _, text = read(rel)
    page = visible(text)
    for phrase in phrases:
        if phrase in page:
            raise SystemExit(f"Weak connective-copy straggler remains in {rel}: {phrase}")

for rel, phrases in required.items():
    _, text = read(rel)
    page = visible(text)
    for phrase in phrases:
        if phrase not in page:
            raise SystemExit(f"Connective-copy invariant missing in {rel}: {phrase}")

print("OOLITA final connective-copy precision pass applied and validated successfully.")
