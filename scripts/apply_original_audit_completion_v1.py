#!/usr/bin/env python3
"""Close the remaining original OOLITA audit items without adding filler.

This pass is deliberately small:
- make Hallazgo publication/access status self-contained;
- give Hallazgo its own Follow interest and deep-link preselection;
- remove accommodation-first collaboration framing;
- add compact authoritative source links to factual pages;
- verify Posters/Sundays already carry enough archive context, without padding them.
"""
from __future__ import annotations

from html import unescape
from pathlib import Path
import re
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")

JUNTA_GEOLOGY = "https://www.juntadeandalucia.es/medioambiente/portal/documents/20151/91690588/Sendero%2BGeol%C3%B3gico%2BEscullos-Isleta%2Bdel%2BMoro.pdf/0e2a21da-a176-e8cf-4e46-8e30164c300a?t=1688543739447"
IGME_AND082 = "https://info.igme.es/ielig/LIGInfo.aspx?codigo=AND082"
NIJAR_PATRIMONIO = "https://nijar.es/conoce-nijar/patrimonio/"
LABYRINTH_SOCIETY = "https://labyrinthsociety.org/labyrinths-overview/"


def read(rel: str) -> tuple[Path, str]:
    path = ROOT / rel
    if not path.is_file():
        raise SystemExit(f"Missing original-audit page: {rel}")
    return path, path.read_text(encoding="utf-8")


def visible(fragment: str) -> str:
    text = unescape(re.sub(r"<[^>]+>", "", fragment))
    return re.sub(r"\s+", " ", text).strip()


def replace_exact_paragraph(rel: str, old_visible: str, new_inner: str, done_marker: str) -> None:
    path, text = read(rel)
    if done_marker in text:
        return
    pattern = re.compile(r"(<p\b[^>]*>)(.*?)(</p>)", re.I | re.S)
    matches = [m for m in pattern.finditer(text) if visible(m.group(2)) == old_visible]
    if len(matches) != 1:
        raise SystemExit(f"Expected one paragraph in {rel}: {old_visible!r}; found {len(matches)}")
    m = matches[0]
    replacement = m.group(1) + new_inner + m.group(3)
    path.write_text(text[:m.start()] + replacement + text[m.end():], encoding="utf-8")


def replace_visible_text(rel: str, old: str, new: str) -> None:
    path, text = read(rel)
    if new in visible(text):
        return
    if old in text:
        path.write_text(text.replace(old, new, 1), encoding="utf-8")
        return
    pattern = re.compile(r"\s+".join(re.escape(piece) for piece in old.split()), re.S)
    matches = list(pattern.finditer(text))
    if len(matches) != 1:
        raise SystemExit(f"Expected one text occurrence in {rel}: {old!r}; found {len(matches)}")
    m = matches[0]
    path.write_text(text[:m.start()] + new + text[m.end():], encoding="utf-8")


def patch_follow_page(rel: str, language: str) -> None:
    path, text = read(rel)
    if language == "es":
        new_intro = "Una sola lista. Elige lo que quieres seguir: mundo 3D, libros, Hallazgo, publicaciones de campo o ediciones textiles."
        book_chip = '<label class="follow-chip"><input type="checkbox" name="interest" value="book"><span>Libros</span></label>'
        hallazgo_chip = '<label class="follow-chip"><input type="checkbox" name="interest" value="hallazgo"><span>Hallazgo</span></label>'
    else:
        new_intro = "One list. Choose what you want to follow: the 3D world, books, Hallazgo, field publications or textile editions."
        book_chip = '<label class="follow-chip"><input type="checkbox" name="interest" value="book"><span>Books</span></label>'
        hallazgo_chip = '<label class="follow-chip"><input type="checkbox" name="interest" value="hallazgo"><span>Hallazgo</span></label>'

    # Later voice/CTA layers are allowed to refine the Follow introduction. Do not
    # bind this final audit to any old sentence: replace the one glosa inside the
    # existing Follow intro structurally and leave the rest of the section intact.
    intro_pattern = re.compile(
        r'(<div\b[^>]*class=["\'][^"\']*\boolita-follow-intro\b[^"\']*["\'][^>]*>[\s\S]*?'
        r'<p\b[^>]*class=["\'][^"\']*\bglosa\b[^"\']*["\'][^>]*>)([\s\S]*?)(</p>)',
        re.I,
    )
    intro_matches = list(intro_pattern.finditer(text))
    if len(intro_matches) != 1:
        raise SystemExit(f"Expected one structural Follow intro in {rel}; found {len(intro_matches)}")
    m = intro_matches[0]
    text = text[:m.start()] + m.group(1) + new_intro + m.group(3) + text[m.end():]

    if hallazgo_chip not in text:
        if book_chip not in text:
            raise SystemExit(f"Book chip not found while adding Hallazgo in {rel}")
        text = text.replace(book_chip, book_chip + hallazgo_chip, 1)

    prefill_id = "oolita-follow-interest-prefill"
    if f'id="{prefill_id}"' not in text:
        script = (
            f'<script id="{prefill_id}">(function(){{try{{if(new URLSearchParams(location.search).get("interest")!=="hallazgo")return;'
            'document.querySelectorAll(".oolita-follow input[name=\\"interest\\"][value=\\"hallazgo\\"]").forEach(function(el){el.checked=true;});'
            '}catch(e){}})();</script>'
        )
        if "</body>" not in text:
            raise SystemExit(f"Missing </body> while adding Hallazgo prefill in {rel}")
        text = text.replace("</body>", script + "\n</body>", 1)

    path.write_text(text, encoding="utf-8")


def add_sources(rel: str, key: str, language: str, links: list[tuple[str, str]]) -> None:
    path, text = read(rel)
    marker = f'data-oolita-sources="{key}"'
    if marker in text:
        return
    label = "FUENTES" if language == "es" else "SOURCES"
    rendered = " · ".join(
        f'<a href="{href}" rel="external noopener">{name} ↗</a>' for name, href in links
    )
    block = (
        f'<section class="tramo" {marker}>'
        f'<span class="rot">{label}</span>'
        f'<p class="glosa">{rendered}</p>'
        '</section>'
    )
    if "</main>" not in text:
        raise SystemExit(f"Missing </main> while adding sources in {rel}")
    text = text.replace("</main>", block + "\n</main>", 1)
    path.write_text(text, encoding="utf-8")


# 07 — Hallazgo: publication/access status belongs on the catalogue itself.
replace_exact_paragraph(
    "catalogo-hallazgo/index.html",
    "El proyecto continúa en el castillo 3D de Hallazgo, dentro del mundo de OOLITA. Puedes conocer el contexto del proyecto y seguir otras ediciones vinculadas a este trabajo.",
    '<strong data-hallazgo-status>PUBLICACIÓN · 16.09.27</strong><br>Edición en tapa dura. La obra completa estará también en el castillo 3D de Hallazgo. Acceso con código; se enviará a la lista de OOLITA en el lanzamiento. Presentación pública · 19.09.27. <a href="/?interest=hallazgo#seguir-oolita">SEGUIR HALLAZGO →</a>',
    "data-hallazgo-status",
)
replace_exact_paragraph(
    "en/hallazgo-catalogue/index.html",
    "The project continues in the Hallazgo 3D castle inside the OOLITA world. You can explore the wider context of the project and follow other editions connected to this body of work.",
    '<strong data-hallazgo-status>PUBLICATION · 16 SEP 27</strong><br>Hardback edition. The complete body of work will also be housed in the Hallazgo 3D castle. Access by code; it will be sent to the OOLITA list at launch. Public launch · 19 Sep 27. <a href="/en/?interest=hallazgo#follow-oolita">FOLLOW HALLAZGO →</a>',
    "data-hallazgo-status",
)

# 15 — Hallazgo gets its own subscriber preference, including deep-link preselection.
# Only the two homepages own Follow forms; 404 artifacts deliberately do not.
for rel, language in (
    ("index.html", "es"),
    ("en/index.html", "en"),
):
    patch_follow_page(rel, language)

# 16 — do not frame collaboration as an accommodation/tourism programme.
replace_visible_text(
    "colaborar/index.html",
    "Librerías, alojamientos, educadores, organizaciones culturales y artesanos pueden trabajar con OOLITA en libros, proyectos de campo y pequeñas ediciones.",
    "Librerías, educadores, organizaciones culturales y artesanos pueden trabajar con OOLITA en libros, proyectos de campo y pequeñas ediciones.",
)
replace_visible_text(
    "en/work-with-oolita/index.html",
    "Bookshops, places to stay, educators, cultural organisations and makers can work with OOLITA on books, field projects and small editions.",
    "Bookshops, educators, cultural organisations and makers can work with OOLITA on books, field projects and small editions.",
)

# 18 — factual pages cite the specialist/public bodies behind their factual claims.
add_sources(
    "que-es-un-laberinto/index.html",
    "labyrinth",
    "es",
    [("The Labyrinth Society · Labyrinths Overview", LABYRINTH_SOCIETY)],
)
add_sources(
    "en/what-is-a-labyrinth/index.html",
    "labyrinth",
    "en",
    [("The Labyrinth Society · Labyrinths Overview", LABYRINTH_SOCIETY)],
)
add_sources(
    "que-es-un-oolito/index.html",
    "ooid",
    "es",
    [
        ("Junta de Andalucía · Sendero geológico Escullos–Isleta del Moro", JUNTA_GEOLOGY),
        ("IGME · AND082 Eolianitas de los Escullos", IGME_AND082),
    ],
)
add_sources(
    "en/what-is-an-ooid/index.html",
    "ooid",
    "en",
    [
        ("Junta de Andalucía · Escullos–Isleta del Moro geological trail", JUNTA_GEOLOGY),
        ("IGME · AND082 Eolianitas de los Escullos", IGME_AND082),
    ],
)
add_sources(
    "cabo-de-gata/index.html",
    "cabo",
    "es",
    [
        ("Ayuntamiento de Níjar · Castillo de San Felipe", NIJAR_PATRIMONIO),
        ("Junta de Andalucía · Sendero geológico Escullos–Isleta del Moro", JUNTA_GEOLOGY),
        ("IGME · AND082 Eolianitas de los Escullos", IGME_AND082),
    ],
)
add_sources(
    "en/cabo-de-gata/index.html",
    "cabo",
    "en",
    [
        ("Níjar Council · Castillo de San Felipe", NIJAR_PATRIMONIO),
        ("Junta de Andalucía · Escullos–Isleta del Moro geological trail", JUNTA_GEOLOGY),
        ("IGME · AND082 Eolianitas de los Escullos", IGME_AND082),
    ],
)

# 10 — these archive pages already have concrete date/account/current-info context.
# Validate it; do not inflate them to satisfy a word-count idea of SEO.
archive_checks = {
    "carteles/index.html": ("@oolita.es", "/domingos/", "/laberinto/"),
    "en/posters/index.html": ("@oolita.es", "/en/sundays/", "/en/labyrinth/"),
    "domingos/index.html": ("09.08.2026", "03.01.2027", "@oolita.es"),
    "en/sundays/index.html": ("09.08.2026", "03.01.2027", "@oolita.es"),
}
for rel, needles in archive_checks.items():
    _, text = read(rel)
    for needle in needles:
        if needle not in text:
            raise SystemExit(f"Archive context invariant missing in {rel}: {needle}")

# Final fail-closed checks.
required = {
    "catalogo-hallazgo/index.html": ("PUBLICACIÓN · 16.09.27", "interest=hallazgo", "Presentación pública · 19.09.27"),
    "en/hallazgo-catalogue/index.html": ("PUBLICATION · 16 SEP 27", "interest=hallazgo", "Public launch · 19 Sep 27"),
    "index.html": ('value="hallazgo"', "Hallazgo, publicaciones de campo"),
    "en/index.html": ('value="hallazgo"', "Hallazgo, field publications"),
    "colaborar/index.html": ("Librerías, educadores, organizaciones culturales y artesanos",),
    "en/work-with-oolita/index.html": ("Bookshops, educators, cultural organisations and makers",),
    "que-es-un-oolito/index.html": ('data-oolita-sources="ooid"', IGME_AND082),
    "en/what-is-an-ooid/index.html": ('data-oolita-sources="ooid"', IGME_AND082),
    "cabo-de-gata/index.html": ('data-oolita-sources="cabo"', NIJAR_PATRIMONIO),
    "en/cabo-de-gata/index.html": ('data-oolita-sources="cabo"', NIJAR_PATRIMONIO),
}
for rel, needles in required.items():
    _, text = read(rel)
    for needle in needles:
        if needle not in text:
            raise SystemExit(f"Original-audit completion invariant missing in {rel}: {needle}")

for rel in ("colaborar/index.html", "en/work-with-oolita/index.html"):
    _, text = read(rel)
    page = visible(text)
    for stale in ("alojamientos", "places to stay"):
        if stale in page:
            raise SystemExit(f"Tourism-framing straggler remains in {rel}: {stale}")

print("OOLITA original audit remainder closed: Hallazgo status/follow mapping, collaboration framing, factual sources and archive context validated.")
