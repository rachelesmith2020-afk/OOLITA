#!/usr/bin/env python3
"""Reduce homepage-concept repetition on About and Cabo de Gata.

The homepage owns the full stone/paper/code explanation. Internal pages should
use their space for what is specific to them: chronology and repeated return on
About; territory, limits and access on Cabo de Gata.
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
        raise SystemExit(f"Missing page-differentiation target: {rel}")
    return path, path.read_text(encoding="utf-8")


def rendered(fragment: str) -> str:
    text = unescape(re.sub(r"<[^>]+>", "", fragment))
    return re.sub(r"\s+", " ", text).strip()


def replace_element(rel: str, tags: tuple[str, ...], markers: tuple[str, ...], new_inner: str) -> None:
    path, text = read(rel)
    if new_inner in text:
        return

    tag_pat = "|".join(re.escape(tag) for tag in tags)
    pattern = re.compile(
        rf"(<(?P<tag>{tag_pat})\b[^>]*>)(?P<body>.*?)(</(?P=tag)>)",
        flags=re.I | re.S,
    )
    matches = []
    for match in pattern.finditer(text):
        visible = rendered(match.group("body"))
        if any(marker in visible for marker in markers):
            matches.append(match)

    if len(matches) != 1:
        raise SystemExit(
            f"Expected one page-differentiation target in {rel} for {markers[0]!r}; found {len(matches)}"
        )

    match = matches[0]
    replacement = match.group(1) + new_inner + match.group(4)
    path.write_text(text[: match.start()] + replacement + text[match.end() :], encoding="utf-8")


# ABOUT — replace the brand-mechanism recap with chronology. The page already
# carries authorship, Hallazgo and the return to Los Escullos; this paragraph now
# explains how the project actually developed instead of repeating the homepage.
replace_element(
    "en/about/index.html",
    ("h2", "h3", "h4"),
    ("Stone, paper and code.",),
    "What came first.",
)
replace_element(
    "en/about/index.html",
    ("p",),
    ("Stone is the original labyrinth. Paper is the bilingual fable",),
    "The labyrinth came first, in 2021. The book grew from walking it and drawing it again. The 3D world came later, when the same place needed another form of access. OOLITA has grown in that order.",
)
replace_element(
    "sobre-oolita/index.html",
    ("h2", "h3", "h4"),
    ("Piedra, papel y código.",),
    "Qué vino primero.",
)
replace_element(
    "sobre-oolita/index.html",
    ("p",),
    ("La piedra es el laberinto original. El papel es la fábula bilingüe",),
    "Primero fue el laberinto, en 2021. El libro creció de caminarlo y volver a dibujarlo. El mundo 3D llegó después, cuando el mismo lugar necesitó otra forma de acceso. OOLITA ha crecido en ese orden.",
)

# Trim the one remaining Spanish About sentence that recycles the material triad.
replace_element(
    "sobre-oolita/index.html",
    ("p",),
    ("Desde 2021 vuelvo al mismo punto para mirar qué cambia y qué permanece",),
    "Desde 2021 vuelvo al mismo punto para mirar qué cambia y qué permanece: la piedra, el viento, las huellas, el paso de la gente, el propio dibujo. OOLITA crece desde esa repetición. No intenta convertir Cabo de Gata en una marca. Intenta mantener una relación concreta con un lugar.",
)

# CABO DE GATA — the territory page should state why the physical work remains
# singular instead of repeating the homepage's three-material definition.
replace_element(
    "en/cabo-de-gata/index.html",
    ("h2", "h3", "h4"),
    ("The place changes material.",),
    "What stays here.",
)
replace_element(
    "en/cabo-de-gata/index.html",
    ("p",),
    ("Stone is the labyrinth. Paper is the bilingual fable. Code is the 3D world",),
    "The labyrinth stays at Los Escullos. The 3D world exists so the path can travel without building another labyrinth or sending more people here. Cabo de Gata is not scenery for the project. It is a protected place with limits, and OOLITA works from those limits.",
)
replace_element(
    "cabo-de-gata/index.html",
    ("h2", "h3", "h4"),
    ("El lugar cambia de material.",),
    "Lo que se queda aquí.",
)
replace_element(
    "cabo-de-gata/index.html",
    ("p",),
    ("La piedra es el laberinto. El papel es la fábula bilingüe. El código es el mundo 3D",),
    "El laberinto se queda en Los Escullos. El mundo 3D existe para que el camino pueda viajar sin construir otro laberinto ni traer más gente hasta aquí. Cabo de Gata no es un decorado para el proyecto. Es un lugar protegido con límites, y OOLITA trabaja desde esos límites.",
)


# Guard the published state. These are specifically the transplanted homepage
# explanations this pass is meant to remove; core motifs remain where they are
# the actual subject (labyrinth, 3D world, geology, book).
stale = {
    "en/about/index.html": (
        "Stone, paper and code.",
        "Stone is the original labyrinth. Paper is the bilingual fable",
    ),
    "sobre-oolita/index.html": (
        "Piedra, papel y código.",
        "La piedra es el laberinto original. El papel es la fábula bilingüe",
        "cada material —piedra, papel o código— conserve algo de esa relación",
    ),
    "en/cabo-de-gata/index.html": (
        "The place changes material.",
        "Stone is the labyrinth. Paper is the bilingual fable. Code is the 3D world",
    ),
    "cabo-de-gata/index.html": (
        "El lugar cambia de material.",
        "La piedra es el laberinto. El papel es la fábula bilingüe. El código es el mundo 3D",
    ),
}
for rel, phrases in stale.items():
    _, text = read(rel)
    visible = rendered(text)
    for phrase in phrases:
        if phrase in visible:
            raise SystemExit(f"Page-differentiation regression remains in {rel}: {phrase}")

required = {
    "en/about/index.html": ("What came first.", "The labyrinth came first, in 2021."),
    "sobre-oolita/index.html": ("Qué vino primero.", "Primero fue el laberinto, en 2021."),
    "en/cabo-de-gata/index.html": ("What stays here.", "Cabo de Gata is not scenery for the project."),
    "cabo-de-gata/index.html": ("Lo que se queda aquí.", "Cabo de Gata no es un decorado para el proyecto."),
}
for rel, phrases in required.items():
    _, text = read(rel)
    visible = rendered(text)
    for phrase in phrases:
        if phrase not in visible:
            raise SystemExit(f"Page-differentiation invariant missing in {rel}: {phrase}")

print("OOLITA page differentiation applied and validated successfully.")
