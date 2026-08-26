#!/usr/bin/env python3
"""Clarify the OOLITA homepage follow proposition without adding marketing pressure.

The hero language, product routes and collaboration page already do their jobs.
This final reader-facing pass only answers the practical question left by the
subscription section: what the list covers and how often OOLITA writes.
"""
from __future__ import annotations

from html import unescape
from pathlib import Path
import re
import sys


ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")


def replace_state(rel: str, old: str, new: str) -> None:
    path = ROOT / rel
    if not path.is_file():
        raise SystemExit(f"Missing CTA page: {rel}")
    text = path.read_text(encoding="utf-8")
    if new in text:
        return
    if old not in text:
        raise SystemExit(f"Homepage follow proposition not found in {rel}: {old!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def remove_exact_phrase(rel: str, phrase: str) -> None:
    path = ROOT / rel
    if not path.is_file():
        raise SystemExit(f"Missing final-copy page: {rel}")
    text = path.read_text(encoding="utf-8")
    if phrase not in text:
        return
    text = text.replace(phrase, "", 1)
    if phrase in text:
        raise SystemExit(f"Duplicate stale phrase remains in {rel}: {phrase}")
    path.write_text(text, encoding="utf-8")


def visible(fragment: str) -> str:
    return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", " ", fragment))).strip()


def ensure_collaboration_detail_section(rel: str, *, language: str) -> None:
    """Restore the useful proposal-detail section after page regeneration."""
    path = ROOT / rel
    if not path.is_file():
        raise SystemExit(f"Missing collaboration page: {rel}")
    text = path.read_text(encoding="utf-8")

    if language == "es":
        heading = "Una propuesta útil es concreta."
        marker = 'data-collaboration-detail="final"'
        block = '''<section class="tramo" data-collaboration-detail="final"><span class="rot">ANTES DE ESCRIBIR</span><h2 class="grande">Una propuesta útil es concreta.</h2><p class="parr">Si eres una librería, indica dónde estás y qué tipo de publicación te interesaría tener. Si eres educador u organización cultural, describe el grupo, el lugar, el intervalo de fechas y el tipo de actividad que imaginas. Los artesanos o productores pueden explicar el material, el proceso y la escala con la que trabajan.</p><p class="parr">OOLITA busca colaboraciones pequeñas y claramente atribuidas: libros, actividades de campo, materiales y ediciones. No añade nombres de colaboradores de forma especulativa: autoría, producción, materiales, cantidades y responsabilidades se indican sólo cuando existe un acuerdo.</p><p class="parr">Cuando una propuesta afecta a Cabo de Gata, el punto de partida es sencillo: no recoger materiales del lugar y no crear un segundo laberinto OOLITA. El trabajo tiene que caber dentro de esos límites.</p><p class="parr">Un primer correo no tiene que ser formal. Unas frases, una ubicación y un enlace a trabajo relevante bastan para empezar.</p></section>'''
        required = (
            "OOLITA busca colaboraciones pequeñas y claramente atribuidas: libros, actividades de campo, materiales y ediciones.",
            "El trabajo tiene que caber dentro de esos límites.",
        )
        stale = ("práctica material", "La intención es ampliar la atención al territorio")
    else:
        heading = "A useful proposal is specific."
        marker = 'data-collaboration-detail="final"'
        block = '''<section class="tramo" data-collaboration-detail="final"><span class="rot">BEFORE WRITING</span><h2 class="grande">A useful proposal is specific.</h2><p class="parr">If you are a bookshop, say where you are and what kind of publication you would like to stock. If you are an educator or cultural organisation, describe the group, place, date range and the kind of activity you have in mind. Makers can explain the material, process and production scale they work with.</p><p class="parr">OOLITA is interested in small, clearly attributed collaborations: books, field activities, materials and editions. It does not add partner names speculatively: authorship, production, materials, quantities and responsibilities are stated only after an agreement exists.</p><p class="parr">When a proposal involves Cabo de Gata, the starting point is simple: take no material from the site and make no second OOLITA labyrinth. The work has to fit those limits.</p><p class="parr">A first email does not need to be formal. A few sentences, a location and a link to relevant work are enough to begin.</p></section>'''
        required = (
            "OOLITA is interested in small, clearly attributed collaborations: books, field activities, materials and editions.",
            "The work has to fit those limits.",
        )
        stale = ("material practice", "The aim is to extend attention to the place")

    section_re = re.compile(r'<section\b[^>]*>[\s\S]*?</section>', flags=re.I)
    matches = [
        match for match in section_re.finditer(text)
        if marker in match.group(0) or heading in visible(match.group(0))
    ]
    if len(matches) > 1:
        raise SystemExit(f"Duplicate collaboration detail sections in {rel}")
    if matches:
        match = matches[0]
        text = text[:match.start()] + text[match.end():]

    footer = re.search(r"<footer\b", text, flags=re.I)
    if not footer:
        raise SystemExit(f"Footer anchor missing in {rel}")
    text = text[:footer.start()] + block + "\n" + text[footer.start():]
    path.write_text(text, encoding="utf-8")

    final_visible = visible(text)
    if final_visible.count(heading) != 1:
        raise SystemExit(f"Collaboration detail heading count wrong in {rel}")
    for phrase in required:
        if phrase not in final_visible:
            raise SystemExit(f"Collaboration detail invariant missing in {rel}: {phrase}")
    for phrase in stale:
        if phrase in final_visible:
            raise SystemExit(f"Stale collaboration wording remains in {rel}: {phrase}")


def remove_generic_sunday03_note(rel: str, marker: str) -> None:
    path = ROOT / rel
    if not path.is_file():
        raise SystemExit(f"Missing Sunday 03 page: {rel}")
    text = path.read_text(encoding="utf-8")
    if marker not in text:
        return

    section_re = re.compile(r'<section\b[^>]*>[\s\S]*?</section>', flags=re.I)
    matches = [match for match in section_re.finditer(text) if marker in match.group(0)]
    if len(matches) == 1:
        match = matches[0]
        text = text[:match.start()] + text[match.end():]
    elif len(matches) == 0:
        paragraph_re = re.compile(r'<p\b[^>]*>[\s\S]*?</p>', flags=re.I)
        paragraphs = [match for match in paragraph_re.finditer(text) if marker in match.group(0)]
        if len(paragraphs) != 1:
            raise SystemExit(f"Could not isolate generic Sunday 03 note in {rel}")
        match = paragraphs[0]
        text = text[:match.start()] + text[match.end():]
    else:
        raise SystemExit(f"Generic Sunday 03 note appears in multiple sections: {rel}")

    if marker in text:
        raise SystemExit(f"Generic Sunday 03 note survived cleanup in {rel}")
    path.write_text(text, encoding="utf-8")


OLD_EN = "One list. Choose what you want to follow: the 3D world, books, field publications or textile editions."
NEW_EN = "One list. The 3D opening, books, field publications and textile editions. Choose what you want to hear about. We write when there is something to tell you."
OLD_ES = "Una sola lista. Elige lo que quieres seguir: mundo 3D, libros, publicaciones de campo o ediciones textiles."
NEW_ES = "Una sola lista. La apertura del mundo 3D, libros, publicaciones de campo y ediciones textiles. Elige lo que quieres recibir. Escribimos cuando hay algo que contar."

replace_state("en/index.html", OLD_EN, NEW_EN)
replace_state("index.html", OLD_ES, NEW_ES)

for rel, stale, final in (
    ("en/index.html", OLD_EN, NEW_EN),
    ("index.html", OLD_ES, NEW_ES),
):
    text = (ROOT / rel).read_text(encoding="utf-8")
    if stale in text:
        raise SystemExit(f"Stale follow proposition remains in {rel}")
    if final not in text:
        raise SystemExit(f"Final follow proposition missing in {rel}")

import apply_page_differentiation_v1  # noqa: E402,F401
import apply_commercial_clarity_v1  # noqa: E402,F401
import apply_environmental_alignment_v1  # noqa: E402,F401

ensure_collaboration_detail_section("colaborar/index.html", language="es")
ensure_collaboration_detail_section("en/work-with-oolita/index.html", language="en")

# The Hallazgo catalogue opener on the current production origin already begins
# with the approved concrete paragraph, followed by one generic curatorial tail.
# Remove only that tail so the final content-quality gate can prove it is gone.
remove_exact_phrase(
    "catalogo-hallazgo/index.html",
    " La edición funciona como archivo y como recorrido: deja que el paisaje actúe sobre cada obra y sobre la relación entre hallazgo, memoria y atención.",
)
remove_exact_phrase(
    "en/hallazgo-catalogue/index.html",
    " The edition works both as an archive and as a route through the work, allowing the landscape to act on each piece and on the relationship between finding, memory and attention.",
)

remove_generic_sunday03_note(
    "en/sundays/03-the-memory-of-the-sea/index.html",
    "continuing public record",
)
remove_generic_sunday03_note(
    "domingos/03-la-memoria-del-mar/index.html",
    "registro público en curso",
)

print("OOLITA final reader-facing clarity passes validated in Spanish and English.")
