#!/usr/bin/env python3
"""Reduce repeated negation/contrast rhetoric in key OOLITA reader-facing copy.

This pass deliberately preserves functional negatives (for example, no download / no
account) and the essential labyrinth-versus-maze distinction. It rewrites only the
repetitive rhetorical pattern identified in the editorial audit, in Spanish and English.
"""
from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")


def read(rel: str) -> tuple[Path, str]:
    path = ROOT / rel
    if not path.is_file():
        raise SystemExit(f"Missing voice-audit page: {rel}")
    return path, path.read_text(encoding="utf-8")


def replace_state(rel: str, old: str, new: str, *, accepted_final: tuple[str, ...] = ()) -> None:
    path, text = read(rel)
    if old in text:
        text = text.replace(old, new)
        path.write_text(text, encoding="utf-8")
        return
    if new in text:
        return
    if accepted_final and all(needle in text for needle in accepted_final):
        return
    raise SystemExit(f"Neither stale nor revised copy found in {rel}: {old!r}")


replace_state("index.html", "no como traducción sino como dos voces del mismo texto", "como dos voces del mismo texto")
replace_state("index.html", "Es una fábula ilustrada, y no explica el laberinto: lo recorre.", "Es una fábula ilustrada que recorre el laberinto página a página.")
replace_state("en/index.html", "not as translation but as two voices of one text", "as two voices of one text")
replace_state("en/index.html", "It is an illustrated fable, and it does not explain the labyrinth: it walks it.", "It is an illustrated fable that follows the labyrinth page by page.")

replace_state(
    "catalogo-hallazgo/index.html",
    "La edición funciona como archivo y como recorrido: no explica el paisaje, lo deja actuar sobre cada obra y sobre la relación entre hallazgo, memoria y atención.",
    "La edición funciona como archivo y como recorrido: deja que el paisaje actúe sobre cada obra y sobre la relación entre hallazgo, memoria y atención.",
    accepted_final=(
        "Hallazgo reúne 44 obras de Raquel Costantini realizadas entre 2018 y 2026.",
        "sin perder su origen.",
    ),
)
replace_state(
    "en/hallazgo-catalogue/index.html",
    "The edition works both as an archive and as a route through the work: it does not explain the landscape, but lets it act on each piece and on the relationship between finding, memory and attention.",
    "The edition works both as an archive and as a route through the work, allowing the landscape to act on each piece and on the relationship between finding, memory and attention.",
    accepted_final=(
        "Hallazgo brings together 44 works by Raquel Costantini made between 2018 and 2026.",
        "without losing their origin.",
    ),
)

replace_state("mundo-3d/index.html", "La tercera forma de OOLITA está hecha en código. No es una imagen del laberinto para mirar desde fuera: está construida para recorrerla — un camino hacia dentro, un centro y el mismo camino de regreso.", "La tercera forma de OOLITA está hecha en código. Es un espacio caminable en el navegador: un camino hacia dentro, un centro y el mismo camino de regreso.")
replace_state("en/3d-world/index.html", "The third form of OOLITA is made in code. It is not an image of the labyrinth to look at from outside: it is being built to be walked — one path inward, one centre and the same path back out.", "The third form of OOLITA is made in code. It is a walkable space in the browser: one path inward, one centre and the same path back out.")
replace_state("mundo-3d/index.html", "No todo el mundo puede llegar hasta allí. El mundo digital no sustituye Los Escullos. No todo el mundo puede llegar. A veces es la distancia. A veces el dinero. A veces el cuerpo. El mismo camino queda abierto en el navegador.", "El mundo digital lleva el mismo recorrido al navegador para personas separadas de Los Escullos por la distancia, el coste o la movilidad. El lugar sigue siendo Los Escullos; el acceso cambia de material.")
replace_state("en/3d-world/index.html", "Not everyone can get there. The digital world does not replace Los Escullos. Not everyone can get there. Sometimes it is distance. Sometimes money. Sometimes the body. The same path stays open in the browser.", "The digital world carries the same route into the browser for people separated from Los Escullos by distance, cost or mobility. Los Escullos remains the place; access changes material.")
replace_state("mundo-3d/index.html", "Reconstruir, no copiar.", "Reconstruir el lugar.")
replace_state("en/3d-world/index.html", "Reconstruct, not copy.", "Reconstruct the place.")
replace_state("mundo-3d/index.html", "El paisaje parte de mediciones del terreno real, pero no busca una réplica fotográfica.", "El paisaje parte de mediciones del terreno real.")
replace_state("mundo-3d/index.html", "No necesita parecer una fotografía. Necesita conservar suficiente lugar para que el camino funcione.", "La reconstrucción conserva los rasgos del lugar que sostienen la orientación, la escala y la atención durante el camino.")
replace_state("en/3d-world/index.html", "The landscape begins with measurements of the real terrain, but it is not trying to be a photographic replica.", "The landscape begins with measurements of the real terrain.")
replace_state("en/3d-world/index.html", "It does not need to look photographic. It needs enough of the place for the walk to work.", "The reconstruction keeps the features of the place that support orientation, scale and attention along the path.")
replace_state("mundo-3d/index.html", "Ninguno sustituye a los otros. Cada uno deja recorrer el mismo camino en otro material.", "Cada material ofrece una forma distinta de recorrer la misma senda.")
replace_state("en/3d-world/index.html", "None replaces the others. Each lets you follow the same path in another material.", "Each material offers a different way to follow the same path.")

stale = {
    "index.html": ("no como traducción sino como dos voces del mismo texto", "no explica el laberinto: lo recorre"),
    "en/index.html": ("not as translation but as two voices of one text", "does not explain the labyrinth: it walks it"),
    "catalogo-hallazgo/index.html": ("no explica el paisaje, lo deja actuar",),
    "en/hallazgo-catalogue/index.html": ("does not explain the landscape, but lets it act",),
    "mundo-3d/index.html": ("No es una imagen del laberinto para mirar desde fuera", "No todo el mundo puede llegar hasta allí. El mundo digital no sustituye Los Escullos. No todo el mundo puede llegar.", "Reconstruir, no copiar.", "pero no busca una réplica fotográfica", "No necesita parecer una fotografía.", "Ninguno sustituye a los otros."),
    "en/3d-world/index.html": ("It is not an image of the labyrinth to look at from outside", "Not everyone can get there. The digital world does not replace Los Escullos. Not everyone can get there.", "Reconstruct, not copy.", "but it is not trying to be a photographic replica", "It does not need to look photographic.", "None replaces the others."),
}
for rel, phrases in stale.items():
    _, text = read(rel)
    for phrase in phrases:
        if phrase in text:
            raise SystemExit(f"Voice-contrast regression remains in {rel}: {phrase}")

print("OOLITA repeated contrast phrasing revised and validated successfully.")

# Production propagation trigger: Hallazgo final trim accepted as a completed state.
