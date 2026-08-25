#!/usr/bin/env python3
"""Normalize final live wording before the strict release-calendar pass."""
from __future__ import annotations

from pathlib import Path
import runpy
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
HERE = Path(__file__).resolve().parent

EN_HOME_FINAL = (
    "A hardback publication bringing together the complete body of work · "
    "full catalogue in the 3D castle · keypad access · code in the launch newsletter · "
    "16 Sep 27 · public launch 19 Sep 27 ↗"
)
ES_HOME_FINAL = (
    "Una edición en tapa dura que reúne el cuerpo completo de la obra · "
    "catálogo completo en el castillo 3D · acceso por teclado numérico · "
    "código en el boletín de lanzamiento · 16.09.27 · presentación pública 19.09.27 ↗"
)
EN_INTERMEDIATE = "In the castle: full catalogue with a key · hardback planned for autumn 2027 ↗"
ES_INTERMEDIATE = "En el castillo: catálogo completo con clave · tapa dura prevista para otoño de 2027 ↗"

EN_ACCESS_FINAL = (
    "On the 3D site, the full catalogue of works is housed inside the castle — a digital replica "
    "of the 1771 Batería de San Felipe, standing on the fossil dune not far from the labyrinth at "
    "Los Escullos. The catalogue is secured by a keypad, and subscribers will receive the code in "
    "the launch newsletter."
)
ES_ACCESS_FINAL = (
    "En el sitio 3D, el catálogo completo de obras se encuentra dentro del castillo — una réplica "
    "digital de la Batería de San Felipe de 1771, situada sobre la duna fósil no lejos del laberinto "
    "de Los Escullos. El catálogo está protegido por un teclado numérico, y los suscriptores recibirán "
    "el código en el boletín de lanzamiento."
)

# A rebuilt site may begin from a live page on which later public-identity and
# reader-facing passes have already applied their final date/copy wording. Restore
# only the intermediate forms expected by the strict release-calendar core; later
# layers re-apply the final public wording after this pass.
normalise = {
    "en/index.html": (
        (
            "Virtual castle · free to enter · opens 16 May 27 · 19:00 CEST ↗",
            "Virtual castle · free to enter · opens 16.05.27 · 19:00 CEST ↗",
        ),
        (EN_HOME_FINAL, EN_INTERMEDIATE),
        (
            "A hardback publication bringing together the complete body of work · full catalogue in the castle with a key · 16 Sep 27 · public launch 19 Sep 27 ↗",
            EN_INTERMEDIATE,
        ),
        (
            "In the castle: full catalogue with a key · hardback 16 Sep 27 · public launch 19 Sep 27 ↗",
            EN_INTERMEDIATE,
        ),
        (
            "In the castle: full catalogue with a key · hardback 16.09.27 · public launch 19.09.27 ↗",
            EN_INTERMEDIATE,
        ),
    ),
    "index.html": (
        (ES_HOME_FINAL, ES_INTERMEDIATE),
        (
            "Una edición en tapa dura que reúne el cuerpo completo de la obra · catálogo completo en el castillo con clave · 16.09.27 · presentación pública 19.09.27 ↗",
            ES_INTERMEDIATE,
        ),
        (
            "En el castillo: catálogo completo con clave · tapa dura 16.09.27 · presentación pública 19.09.27 ↗",
            ES_INTERMEDIATE,
        ),
    ),
    "404/index.html": (
        (ES_HOME_FINAL, ES_INTERMEDIATE),
        (
            "Una edición en tapa dura que reúne el cuerpo completo de la obra · catálogo completo en el castillo con clave · 16.09.27 · presentación pública 19.09.27 ↗",
            ES_INTERMEDIATE,
        ),
        (
            "En el castillo: catálogo completo con clave · tapa dura 16.09.27 · presentación pública 19.09.27 ↗",
            ES_INTERMEDIATE,
        ),
    ),
}
for rel, replacements in normalise.items():
    target = ROOT / rel
    if not target.is_file():
        continue
    text = target.read_text(encoding="utf-8")
    for old, new in replacements:
        text = text.replace(old, new)
    target.write_text(text, encoding="utf-8")

core = HERE / "apply_release_calendar_core_v1.py"
if not core.is_file():
    raise SystemExit(f"Missing release-calendar core: {core}")
old_argv = sys.argv[:]
sys.argv = [str(core), str(ROOT)]
try:
    runpy.run_path(str(core), run_name="__main__")
finally:
    sys.argv = old_argv

# Hallazgo is already visible from the OOLITA directory. Give the catalogue the
# weight of a publication without turning the homepage into a sales page. Keep
# the 3D keypad/newsletter access and confirmed September dates in view.
final_hallazgo = {
    "en/index.html": (
        ("<span class=\"nom\">Catalogue</span>", "<span class=\"nom\">Hallazgo — the catalogue</span>"),
        (EN_INTERMEDIATE, EN_HOME_FINAL),
    ),
    "index.html": (
        ("<span class=\"nom\">Catálogo</span>", "<span class=\"nom\">Hallazgo — el catálogo</span>"),
        (ES_INTERMEDIATE, ES_HOME_FINAL),
    ),
}
for rel, replacements in final_hallazgo.items():
    target = ROOT / rel
    text = target.read_text(encoding="utf-8")
    for old, new in replacements:
        if old in text:
            text = text.replace(old, new, 1)
        elif new not in text:
            raise SystemExit(f"Expected Hallazgo catalogue wording missing in {rel}: {old!r}")
    target.write_text(text, encoding="utf-8")

required_final = {
    "en/index.html": (
        "Hallazgo — the catalogue",
        "A hardback publication bringing together the complete body of work",
        "full catalogue in the 3D castle",
        "keypad access",
        "code in the launch newsletter",
        "16 Sep 27",
        "public launch 19 Sep 27",
    ),
    "index.html": (
        "Hallazgo — el catálogo",
        "Una edición en tapa dura que reúne el cuerpo completo de la obra",
        "catálogo completo en el castillo 3D",
        "acceso por teclado numérico",
        "código en el boletín de lanzamiento",
        "16.09.27",
        "presentación pública 19.09.27",
    ),
}
for rel, needles in required_final.items():
    text = (ROOT / rel).read_text(encoding="utf-8")
    for needle in needles:
        if needle not in text:
            raise SystemExit(f"Hallazgo catalogue validation failed in {rel}: {needle!r}")

# The Editions pages acknowledge Hallazgo without folding it into the numbered
# OOLITA edition sequence or implying that the hardback is already on sale. This
# is now first-party at source and is deliberately idempotent on live-origin rebuilds.
ES_INSERTION_POINT = (
    "Ninguna de las dos es un recuerdo. El libro lleva el camino al papel; la primera edición textil, "
    "a la tela. Las siguientes mirarán también más allá del trazado, hacia el territorio que lo rodea."
)
EN_INSERTION_POINT = (
    "Neither is a souvenir. The book carries the path into paper; the first textile edition carries it "
    "into cloth. Future editions will look beyond the path to the wider territory around it."
)
ES_EDITIONS_FINAL = (
    ES_INSERTION_POINT
    + "\n<p class=\"parr\"><a href=\"/catalogo-hallazgo/\">Hallazgo — el catálogo ↗</a> queda aparte de esta secuencia: "
    "una edición en tapa dura que reúne el cuerpo completo de la obra. Se publica el 16 de septiembre de 2027; "
    "presentación pública, 19 de septiembre. "
    + ES_ACCESS_FINAL
    + "</p>"
)
EN_EDITIONS_FINAL = (
    EN_INSERTION_POINT
    + "\n<p class=\"parr\"><a href=\"/en/hallazgo-catalogue/\">Hallazgo — the catalogue ↗</a> sits apart from this sequence: "
    "a hardback publication bringing together the complete body of work. Published 16 September 2027; "
    "public launch, 19 September. "
    + EN_ACCESS_FINAL
    + "</p>"
)

editions_hallazgo = {
    "ediciones/index.html": (ES_INSERTION_POINT, ES_EDITIONS_FINAL),
    "en/editions/index.html": (EN_INSERTION_POINT, EN_EDITIONS_FINAL),
}
for rel, (old, new) in editions_hallazgo.items():
    target = ROOT / rel
    if not target.is_file():
        raise SystemExit(f"Missing Editions page for Hallazgo publication: {rel}")
    text = target.read_text(encoding="utf-8")
    label = "Hallazgo — el catálogo" if rel.startswith("ediciones/") else "Hallazgo — the catalogue"
    if text.count(label) > 1:
        raise SystemExit(f"Hallazgo Editions entry duplicated before release pass in {rel}")
    if new not in text:
        # A clean block from a previous deployment may differ only in surrounding
        # whitespace. If Hallazgo is already present once, validate it below rather
        # than inserting a second copy.
        if text.count(label) == 0:
            if old not in text:
                raise SystemExit(f"Expected Editions insertion point missing in {rel}")
            text = text.replace(old, new, 1)
            target.write_text(text, encoding="utf-8")

required_editions = {
    "ediciones/index.html": (
        "Hallazgo — el catálogo",
        "una edición en tapa dura que reúne el cuerpo completo de la obra",
        "16 de septiembre de 2027",
        "19 de septiembre",
        ES_ACCESS_FINAL,
        'href="/catalogo-hallazgo/"',
    ),
    "en/editions/index.html": (
        "Hallazgo — the catalogue",
        "a hardback publication bringing together the complete body of work",
        "16 September 2027",
        "19 September",
        EN_ACCESS_FINAL,
        'href="/en/hallazgo-catalogue/"',
    ),
}
for rel, needles in required_editions.items():
    text = (ROOT / rel).read_text(encoding="utf-8")
    for needle in needles:
        if needle not in text:
            raise SystemExit(f"Hallazgo Editions validation failed in {rel}: {needle!r}")
    label = "Hallazgo — el catálogo" if rel.startswith("ediciones/") else "Hallazgo — the catalogue"
    if text.count(label) != 1:
        raise SystemExit(f"Hallazgo Editions entry duplicated in {rel}")
    if "hallazgo.my.canva.site" in text.lower():
        raise SystemExit(f"Legacy Hallazgo Canva href remains in {rel}")

print("Hallazgo catalogue publication wording validated on home and Editions in Spanish and English; first-party and idempotent.")
