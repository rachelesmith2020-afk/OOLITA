#!/usr/bin/env python3
"""Apply OOLITA's final reader-facing clarity without adding marketing pressure.

This pass keeps the homepage follow proposition factual, restores the reviewed
collaboration detail, removes the remaining generic archive/curatorial tails,
and gives direct-entry pages one quiet route back to the existing OOLITA index.
It deliberately does not add a conventional global menu.
"""
from __future__ import annotations

from html import unescape
from pathlib import Path
import re
import sys


ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
INDEX_ID = "oolita-index"

BILINGUAL_PAIRS = (
    ("/", "/en/"),
    ("/laberinto/", "/en/labyrinth/"),
    ("/carteles/", "/en/posters/"),
    ("/que-es-un-laberinto/", "/en/what-is-a-labyrinth/"),
    ("/que-es-un-oolito/", "/en/what-is-an-ooid/"),
    ("/ediciones/", "/en/editions/"),
    ("/ediciones/libro/", "/en/editions/book/"),
    ("/ediciones/camiseta/", "/en/editions/t-shirt/"),
    ("/domingos/", "/en/sundays/"),
    ("/domingos/01-el-doble/", "/en/sundays/01-the-double/"),
    ("/domingos/02-el-gato-de-verdad/", "/en/sundays/02-the-cat-for-real/"),
    ("/domingos/03-la-memoria-del-mar/", "/en/sundays/03-the-memory-of-the-sea/"),
    ("/cabo-de-gata/", "/en/cabo-de-gata/"),
    ("/sobre-oolita/", "/en/about/"),
    ("/colaborar/", "/en/work-with-oolita/"),
    ("/privacidad/", "/en/privacy/"),
    ("/mundo-3d/", "/en/3d-world/"),
    ("/catalogo-hallazgo/", "/en/hallazgo-catalogue/"),
)


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


def route_to_rel(route: str) -> str:
    if route == "/":
        return "index.html"
    return route.lstrip("/") + "index.html"


def has_href(text: str, route: str) -> bool:
    """Accept the site's normal root-relative form or its absolute equivalent."""
    return bool(re.search(
        rf'href=["\'](?:https://oolita\.es)?{re.escape(route)}["\']',
        text,
        flags=re.I,
    ))


def ensure_footer_index_link(rel: str) -> None:
    """Add one quiet footer route to the existing homepage index."""
    path = ROOT / rel
    if not path.is_file():
        raise SystemExit(f"Missing direct-entry page: {rel}")
    text = path.read_text(encoding="utf-8")
    en = rel.startswith("en/")
    href = f'/en/#{INDEX_ID}' if en else f'/#{INDEX_ID}'
    label = "OOLITA · INDEX" if en else "OOLITA · ÍNDICE"
    marker = 'data-oolita-index-link="true"'

    footer_match = re.search(r'<footer\b[^>]*>[\s\S]*?</footer>', text, flags=re.I)
    if not footer_match:
        raise SystemExit(f"Footer missing from direct-entry page: {rel}")
    footer = footer_match.group(0)

    if marker in footer:
        if footer.count(marker) != 1 or href not in footer or label not in visible(footer):
            raise SystemExit(f"Existing OOLITA index footer link is malformed in {rel}")
        return

    privacy_route = "/en/privacy/" if en else "/privacidad/"
    privacy_re = re.compile(
        rf'<a\b[^>]*href=["\'](?:https://oolita\.es)?{re.escape(privacy_route)}["\'][^>]*>',
        flags=re.I,
    )
    privacy_links = list(privacy_re.finditer(footer))
    if len(privacy_links) != 1:
        raise SystemExit(f"Expected one footer privacy anchor in {rel}; found {len(privacy_links)}")

    anchor = privacy_links[0]
    index_link = f'<a href="{href}" data-oolita-index-link="true">{label}</a>'
    footer = footer[:anchor.start()] + index_link + "\n" + footer[anchor.start():]
    text = text[:footer_match.start()] + footer + text[footer_match.end():]
    path.write_text(text, encoding="utf-8")


def validate_direct_entry_navigation() -> None:
    """Prove all published bilingual routes have orientation without a top menu."""
    es_home = (ROOT / "index.html").read_text(encoding="utf-8")
    en_home = (ROOT / "en/index.html").read_text(encoding="utf-8")
    for rel, text in (("index.html", es_home), ("en/index.html", en_home)):
        if text.count(f'id="{INDEX_ID}"') != 1:
            raise SystemExit(f"Stable OOLITA index anchor missing or duplicated in {rel}")

    for es_route, en_route in BILINGUAL_PAIRS:
        es_rel = route_to_rel(es_route)
        en_rel = route_to_rel(en_route)
        es_path = ROOT / es_rel
        en_path = ROOT / en_rel
        if not es_path.is_file() or not en_path.is_file():
            raise SystemExit(f"Bilingual route pair missing: {es_route} ↔ {en_route}")
        es_text = es_path.read_text(encoding="utf-8")
        en_text = en_path.read_text(encoding="utf-8")
        if not has_href(es_text, en_route):
            raise SystemExit(f"Spanish page lacks direct English counterpart href: {es_route} → {en_route}")
        if not has_href(en_text, es_route):
            raise SystemExit(f"English page lacks direct Spanish counterpart href: {en_route} → {es_route}")

        if es_route != "/":
            footer = re.search(r'<footer\b[^>]*>[\s\S]*?</footer>', es_text, flags=re.I)
            if not footer or footer.group(0).count('data-oolita-index-link="true"') != 1:
                raise SystemExit(f"Spanish direct-entry index route missing or duplicated: {es_route}")
            if f'href="/#{INDEX_ID}"' not in footer.group(0) or "OOLITA · ÍNDICE" not in visible(footer.group(0)):
                raise SystemExit(f"Spanish direct-entry index route malformed: {es_route}")
        if en_route != "/en/":
            footer = re.search(r'<footer\b[^>]*>[\s\S]*?</footer>', en_text, flags=re.I)
            if not footer or footer.group(0).count('data-oolita-index-link="true"') != 1:
                raise SystemExit(f"English direct-entry index route missing or duplicated: {en_route}")
            if f'href="/en/#{INDEX_ID}"' not in footer.group(0) or "OOLITA · INDEX" not in visible(footer.group(0)):
                raise SystemExit(f"English direct-entry index route malformed: {en_route}")


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

# Direct-entry orientation: every published internal page gets one small footer
# route back to the existing homepage index. Page-specific links stay untouched.
for es_route, en_route in BILINGUAL_PAIRS:
    if es_route != "/":
        ensure_footer_index_link(route_to_rel(es_route))
    if en_route != "/en/":
        ensure_footer_index_link(route_to_rel(en_route))
validate_direct_entry_navigation()

print("OOLITA final reader-facing clarity and direct-entry navigation validated in Spanish and English.")
