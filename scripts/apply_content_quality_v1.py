#!/usr/bin/env python3
"""Apply the reviewed OOLITA content-quality pass.

Surgical only: remove formulaic/curatorial wording while preserving the project's
physical structures, factual detail, site-rootedness and non-extractive rules.
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
        raise SystemExit(f"Missing content-quality page: {rel}")
    return path, path.read_text(encoding="utf-8")


def visible(fragment: str) -> str:
    text = unescape(re.sub(r"<[^>]+>", "", fragment))
    return re.sub(r"\s+", " ", text).strip()


def replace_tag_text(rel: str, tags: tuple[str, ...], old: str, new: str) -> None:
    path, text = read(rel)
    if old not in visible(text) and new in visible(text):
        return
    tag_group = "|".join(re.escape(t) for t in tags)
    pattern = re.compile(rf"<(?P<tag>{tag_group})\b(?P<attrs>[^>]*)>(?P<inner>.*?)</(?P=tag)>", re.I | re.S)
    matches = [m for m in pattern.finditer(text) if visible(m.group("inner")) == old]
    if len(matches) != 1:
        raise SystemExit(f"Expected one tag containing {old!r} in {rel}; found {len(matches)}")
    m = matches[0]
    replacement = f"<{m.group('tag')}{m.group('attrs')}>{new}</{m.group('tag')}>"
    path.write_text(text[:m.start()] + replacement + text[m.end():], encoding="utf-8")


def replace_block(rel: str, marker: str, new_inner: str) -> None:
    path, text = read(rel)
    if new_inner in text:
        return
    for tag in ("p", "li", "div", "blockquote"):
        pattern = re.compile(rf"(<{tag}\b[^>]*>)(.*?)(</{tag}>)", re.I | re.S)
        matches = [m for m in pattern.finditer(text) if marker in visible(m.group(2))]
        if len(matches) == 1:
            m = matches[0]
            replacement = m.group(1) + new_inner + m.group(3)
            path.write_text(text[:m.start()] + replacement + text[m.end():], encoding="utf-8")
            return
        if len(matches) > 1:
            raise SystemExit(f"Ambiguous {tag} blocks containing {marker!r} in {rel}; found {len(matches)}")
    raise SystemExit(f"Expected one content block containing {marker!r} in {rel}; found 0")


def replace_source_text(rel: str, old: str, new: str) -> None:
    """Replace one plain source text node, allowing source line wrapping.

    Collaboration copy is emitted as a text node rather than a paragraph element in
    the mirrored origin. This keeps the surrounding markup untouched.
    """
    path, text = read(rel)
    if new in visible(text):
        return
    if old in text:
        path.write_text(text.replace(old, new, 1), encoding="utf-8")
        return
    pattern = re.compile(r"\s+".join(re.escape(piece) for piece in old.split()), re.S)
    matches = list(pattern.finditer(text))
    if len(matches) != 1:
        raise SystemExit(f"Expected one source text node matching {old[:60]!r} in {rel}; found {len(matches)}")
    m = matches[0]
    path.write_text(text[:m.start()] + new + text[m.end():], encoding="utf-8")


def section_matches(text: str, marker: str) -> list[re.Match[str]]:
    pattern = re.compile(r"<section\b[^>]*>.*?</section>", re.I | re.S)
    return [m for m in pattern.finditer(text) if marker in visible(m.group(0))]


def remove_section(rel: str, marker: str) -> None:
    path, text = read(rel)
    if marker not in visible(text):
        return
    matches = section_matches(text, marker)
    if len(matches) != 1:
        raise SystemExit(f"Expected one section containing {marker!r} in {rel}; found {len(matches)}")
    m = matches[0]
    path.write_text(text[:m.start()] + text[m.end():], encoding="utf-8")


def insert_before_section(rel: str, marker: str, block: str, unique_marker: str) -> None:
    path, text = read(rel)
    if unique_marker in visible(text):
        return
    matches = section_matches(text, marker)
    if len(matches) != 1:
        raise SystemExit(f"Expected one insertion section containing {marker!r} in {rel}; found {len(matches)}")
    m = matches[0]
    path.write_text(text[:m.start()] + block + "\n" + text[m.start():], encoding="utf-8")


# ABOUT — start with the physical origin, not a three-noun project formula.
replace_tag_text("sobre-oolita/index.html", ("h1", "h2"), "Un camino, un lugar, una práctica.", "Primero fue un laberinto.")
replace_tag_text("en/about/index.html", ("h1", "h2"), "One path, one place, one practice.", "First there was a labyrinth.")
replace_block("sobre-oolita/index.html", "OOLITA nace de un laberinto de piedra colocado a mano", "Raquel Costantini lo colocó a mano en Los Escullos en septiembre de 2021.")
replace_block("en/about/index.html", "OOLITA begins with a stone labyrinth that Raquel Costantini laid by hand", "Raquel Costantini laid it by hand at Los Escullos in September 2021.")
replace_tag_text("sobre-oolita/index.html", ("h2", "h3"), "Qué vino primero.", "Después.")
replace_tag_text("en/about/index.html", ("h2", "h3"), "What came first.", "Then.")
replace_block("sobre-oolita/index.html", "Primero fue el laberinto, en 2021.", "El libro creció de caminarlo y volver a dibujarlo. El mundo 3D llegó después, cuando el mismo lugar necesitó otra forma de acceso. OOLITA ha crecido en ese orden.")
replace_block("en/about/index.html", "The labyrinth came first, in 2021.", "The book grew from walking it and drawing it again. The 3D world came later, when the same place needed another form of access. OOLITA has grown in that order.")

# English About: remove explanatory filler and restore the place section.
remove_section("en/about/index.html", "A public working rhythm.")
PLACE_EN = '''<section class="tramo" data-place-not-backdrop>
<span class="rot">LOS ESCULLOS</span><h2 class="grande">The place is not a backdrop.</h2>
<p class="parr">The labyrinth at Los Escullos is inside Cabo de Gata-Níjar Natural Park, on land beside the fossil dunes facing the Mediterranean. The ground, its geology and the light are not scenery. They are part of how the work began and why it remains there.</p>
<p class="parr">Since 2021 I have returned to the same point to see what changes and what stays: stone, wind, tracks, people passing, the drawing itself. OOLITA grows from that return. It does not turn Cabo de Gata into a brand. The work stays tied to the place where it began.</p>
</section>'''
insert_before_section("en/about/index.html", "Hallazgo and OOLITA.", PLACE_EN, "The place is not a backdrop.")
replace_block("sobre-oolita/index.html", "OOLITA forma parte de la práctica artística de Raquel Costantini. Hallazgo trabaja", "OOLITA forma parte de la práctica artística de Raquel Costantini. Hallazgo trabaja con observación, material encontrado, paisaje y la disciplina de no alterar lo vivo.")
replace_block("en/about/index.html", "OOLITA sits within Raquel Costantini's wider artistic practice. Hallazgo works", "OOLITA sits within Raquel Costantini’s wider practice. Hallazgo works with observation, found material, landscape and the discipline of leaving living things undisturbed.")

# HALLAZGO — stop after the concrete description.
replace_block("catalogo-hallazgo/index.html", "Hallazgo reúne 44 obras de Raquel Costantini", "Hallazgo reúne 44 obras de Raquel Costantini realizadas entre 2018 y 2026. El catálogo sigue cinco movimientos nacidos de caminar, observar y recoger señales del paisaje de Cabo de Gata: formas encontradas, materia erosionada, restos, piedras, plantas y gestos mínimos que pasan de la experiencia al objeto sin perder su origen.")
replace_block("en/hallazgo-catalogue/index.html", "Hallazgo brings together 44 works by Raquel Costantini", "Hallazgo brings together 44 works by Raquel Costantini made between 2018 and 2026. The catalogue follows five movements shaped by walking, observing and gathering signals from the landscape of Cabo de Gata: found forms, eroded matter, remains, stones, plants and small gestures that move from experience into objects without losing their origin.")

# CABO DE GATA — make the environmental position operational rather than adversarial.
replace_block("cabo-de-gata/index.html", "El laberinto se queda en Los Escullos.", "El laberinto se queda en Los Escullos. El mundo 3D permite seguir el camino desde otro lugar, sin construir otro laberinto. Cabo de Gata no es un decorado para el proyecto. Es un lugar protegido. Ese límite también forma parte de OOLITA.")
replace_block("en/cabo-de-gata/index.html", "The labyrinth stays at Los Escullos.", "The labyrinth stays at Los Escullos. The 3D world lets the path be followed from elsewhere, without building another labyrinth. Cabo de Gata is not scenery for the project. It is a protected place. That limit is part of OOLITA too.")

# COLLABORATION — these are plain source text nodes in the mirrored pages.
replace_source_text(
    "colaborar/index.html",
    "OOLITA busca colaboraciones pequeñas y claramente atribuidas, relacionadas con libros, observación, trabajo de campo y práctica material. No añade nombres de colaboradores de forma especulativa: autoría, producción, materiales, cantidades y responsabilidades se indican sólo cuando existe un acuerdo.",
    "OOLITA busca colaboraciones pequeñas y claramente atribuidas: libros, actividades de campo, materiales y ediciones. No añade nombres de colaboradores de forma especulativa: autoría, producción, materiales, cantidades y responsabilidades se indican sólo cuando existe un acuerdo.",
)
replace_source_text(
    "en/work-with-oolita/index.html",
    "OOLITA is interested in small, clearly attributed collaborations connected to books, observation, fieldwork and material practice. It does not add partner names speculatively: authorship, production, materials, quantities and responsibilities are stated only after an agreement exists.",
    "OOLITA is interested in small, clearly attributed collaborations: books, field activities, materials and editions. It does not add partner names speculatively: authorship, production, materials, quantities and responsibilities are stated only after an agreement exists.",
)
replace_source_text(
    "colaborar/index.html",
    "Cuando una propuesta afecta a Cabo de Gata, el punto de partida es un uso de bajo impacto: no recoger materiales del lugar y no crear un segundo laberinto OOLITA. La intención es ampliar la atención al territorio, no aumentar la presión sobre él.",
    "Cuando una propuesta afecta a Cabo de Gata, el punto de partida es sencillo: no recoger materiales del lugar y no crear un segundo laberinto OOLITA. El trabajo tiene que caber dentro de esos límites.",
)
replace_source_text(
    "en/work-with-oolita/index.html",
    "Where a proposal involves Cabo de Gata, the starting point is low-impact use: no collecting from the site and no second OOLITA labyrinth. The aim is to extend attention to the place, not increase pressure on it.",
    "When a proposal involves Cabo de Gata, the starting point is simple: take no material from the site and make no second OOLITA labyrinth. The work has to fit those limits.",
)

stale = {
    "sobre-oolita/index.html": ("Un camino, un lugar, una práctica.", "Qué vino primero.", "esa atención se vuelve camino"),
    "en/about/index.html": ("One path, one place, one practice.", "What came first.", "A public working rhythm.", "that attention becomes a path"),
    "catalogo-hallazgo/index.html": ("relación entre hallazgo, memoria y atención",),
    "en/hallazgo-catalogue/index.html": ("relationship between finding, memory and attention",),
    "cabo-de-gata/index.html": ("ni traer más gente hasta aquí",),
    "en/cabo-de-gata/index.html": ("or sending more people here",),
    "colaborar/index.html": ("La intención es ampliar la atención al territorio", "práctica material"),
    "en/work-with-oolita/index.html": ("The aim is to extend attention to the place", "material practice"),
}
for rel, phrases in stale.items():
    _, text = read(rel)
    page = visible(text)
    for phrase in phrases:
        if phrase in page:
            raise SystemExit(f"Content-quality straggler remains in {rel}: {phrase}")

required = {
    "sobre-oolita/index.html": ("Primero fue un laberinto.", "Después.", "disciplina de no alterar lo vivo"),
    "en/about/index.html": ("First there was a labyrinth.", "Then.", "The place is not a backdrop.", "leaving living things undisturbed"),
    "catalogo-hallazgo/index.html": ("sin perder su origen.",),
    "en/hallazgo-catalogue/index.html": ("without losing their origin.",),
    "cabo-de-gata/index.html": ("Ese límite también forma parte de OOLITA.",),
    "en/cabo-de-gata/index.html": ("That limit is part of OOLITA too.",),
    "colaborar/index.html": ("El trabajo tiene que caber dentro de esos límites.",),
    "en/work-with-oolita/index.html": ("The work has to fit those limits.",),
}
for rel, phrases in required.items():
    _, text = read(rel)
    page = visible(text)
    for phrase in phrases:
        if phrase not in page:
            raise SystemExit(f"Content-quality invariant missing in {rel}: {phrase}")

print("OOLITA reviewed content-quality/voice pass applied and validated successfully.")
