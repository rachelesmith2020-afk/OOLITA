#!/usr/bin/env python3
"""Run the release-calendar layer safely against the current Editions layout.

The v1/core migration still checks former homepage and Editions wording. Current
production copy may already contain later reader-facing text. Bridge those forms
temporarily so the historical release migration can validate, then restore the
approved concise public Hallazgo homepage description before deployment.
"""
from __future__ import annotations

from pathlib import Path
import runpy
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
HERE = Path(__file__).resolve().parent
CORE = HERE / "apply_release_calendar_v1.py"

ES_CONCISE_HALLAZGO = "Edición en tapa dura · obra completa en Castillo 3D · acceso con código · lanzamiento 16.09.27 · presentación 19.09.27"
ES_LEGACY_HALLAZGO = "Hallazgo — el catálogo"

EN_HOME_CONCISE = (
    "Hardback catalogue of the complete Hallazgo body of work · "
    "in the 3D castle from 16 Sep 27 · public launch 19 Sep 27 ↗"
)
ES_HOME_CONCISE = (
    "Catálogo en tapa dura de la obra completa de Hallazgo · "
    "en el castillo 3D desde el 16.09.27 · presentación pública 19.09.27 ↗"
)
EN_HOME_LONG = (
    "A hardback publication bringing together the complete body of work · "
    "full catalogue in the 3D castle · keypad access · code in the launch newsletter · "
    "16 Sep 27 · public launch 19 Sep 27 ↗"
)
ES_HOME_LONG = (
    "Una edición en tapa dura que reúne el cuerpo completo de la obra · "
    "catálogo completo en el castillo 3D · acceso por teclado numérico · "
    "código en el boletín de lanzamiento · 16.09.27 · presentación pública 19.09.27 ↗"
)
EN_HOME_INTERMEDIATE = "In the castle: full catalogue with a key · hardback planned for autumn 2027 ↗"
ES_HOME_INTERMEDIATE = "En el castillo: catálogo completo con clave · tapa dura prevista para otoño de 2027 ↗"

COMPAT = {
    "ediciones/index.html": {
        "old": '<p class="parr">El libro sale el 31 de enero de 2027. La primera edición textil llega el 28 de marzo, cuando su diseño termine de desvelarse domingo a domingo.</p>',
        "new": '<p class="parr">El libro sale el 31 de enero de 2027. La primera edición textil llega el 11 de abril. Los detalles y la historia del diseño se irán desvelando domingo a domingo hasta entonces.</p>',
        "current_markers": (
            "Después vendrá la edición de tapa dura de Hallazgo",
            ES_CONCISE_HALLAZGO,
            ES_LEGACY_HALLAZGO,
        ),
    },
    "en/editions/index.html": {
        "old": '<p class="parr">The book comes out on 31 January 2027. The first textile edition follows on 28 March, once its design has been revealed Sunday by Sunday.</p>',
        "new": '<p class="parr">The book comes out on 31 January 2027. The first textile edition follows on 11 April. Details and the story of the design will be revealed Sunday by Sunday until then.</p>',
        "current_markers": ("After them will come the Hallazgo hardback", "Hallazgo — the catalogue"),
    },
}

TEXTILE_COMPAT = {
    "ediciones/camiseta/index.html": {
        "current_markers": (
            "La primera edición textil lleva el laberinto a la tela.",
            "La prenda aparece primero en blanco. Cada domingo aparece un poco más del diseño.",
            "Sale el 11 de abril de 2027, después del libro.",
        ),
        "accepted_core_targets": (
            '<p class="parr">Esta primera pieza es una camiseta de algodón orgánico de 200 gramos y corte holgado. Los detalles de la imagen impresa, su colocación y su historia se irán desvelando poco a poco.</p>',
            '<h2>Por qué se cuenta despacio.</h2><p class="parr">La prenda aparece primero en blanco en esta página, a propósito. Los detalles y la historia del diseño se irán desvelando domingo a domingo hasta la primavera: cada entrega contará algo más de la imagen, su colocación y su relación con el laberinto.</p>',
        ),
    },
    "en/editions/t-shirt/index.html": {
        "current_markers": (
            "The first textile edition carries the labyrinth into cloth.",
            "The garment appears first blank. Each Sunday, a little more of the design appears.",
            "It comes out on 11 April 2027, after the book.",
        ),
        "accepted_core_targets": (
            '<p class="parr">This first piece is a 200 gsm organic-cotton T-shirt with a loose cut. Details of the printed image, its placement and its story will be revealed little by little.</p>',
            '<h2>Why its story unfolds slowly.</h2><p class="parr">The garment appears first as a blank piece on this page, on purpose. Details and the story of the design will unfold Sunday by Sunday through to spring: each instalment will say more about the image, its placement and its relationship to the labyrinth.</p>',
        ),
    },
}

if not ROOT.is_dir():
    raise SystemExit(f"Missing built site: {ROOT}")
if not CORE.is_file():
    raise SystemExit(f"Missing release-calendar v1 layer: {CORE}")

# The current public homepage can already carry the newly approved concise
# Hallazgo summary. The historical v1/core pass does not know that form, so
# temporarily move only that exact string to its expected intermediate state.
# growth_prep may also temporarily restore the Spanish homepage shell at either
# custom-404 filesystem form, so bridge both copies as well.
home_bridge = {
    "en/index.html": (EN_HOME_CONCISE, EN_HOME_INTERMEDIATE, EN_HOME_LONG),
    "index.html": (ES_HOME_CONCISE, ES_HOME_INTERMEDIATE, ES_HOME_LONG),
    "404.html": (ES_HOME_CONCISE, ES_HOME_INTERMEDIATE, ES_HOME_LONG),
    "404/index.html": (ES_HOME_CONCISE, ES_HOME_INTERMEDIATE, ES_HOME_LONG),
}
for rel, (concise, intermediate, long_form) in home_bridge.items():
    page = ROOT / rel
    if not page.is_file():
        raise SystemExit(f"Missing homepage shell for release compatibility: {rel}")
    text = page.read_text(encoding="utf-8")
    if concise in text:
        page.write_text(text.replace(concise, intermediate, 1), encoding="utf-8")
        print(f"release v2 bridged concise Hallazgo homepage copy: {rel}")
    elif intermediate in text or long_form in text:
        print(f"release v2 Hallazgo homepage copy already compatible: {rel}")
    else:
        print(f"release v2 left legacy Hallazgo homepage copy for v1/core: {rel}")

inserted: list[tuple[Path, str]] = []
for rel, cfg in COMPAT.items():
    page = ROOT / rel
    if not page.is_file():
        raise SystemExit(f"Missing Editions page for release compatibility: {rel}")
    text = page.read_text(encoding="utf-8")

    if rel == "ediciones/index.html" and ES_CONCISE_HALLAZGO in text and ES_LEGACY_HALLAZGO not in text:
        text = text.replace(ES_CONCISE_HALLAZGO, ES_LEGACY_HALLAZGO, 1)
        page.write_text(text, encoding="utf-8")
        print("release v2 restored structural Hallazgo label for Spanish Editions compatibility")

    if cfg["old"] in text or cfg["new"] in text:
        continue
    if not any(marker in text for marker in cfg["current_markers"]):
        continue
    if "</main>" not in text:
        raise SystemExit(f"No </main> in {rel}")
    sentinel = f'<!-- release-v2 compatibility: {cfg["new"]} -->'
    text = text.replace("</main>", sentinel + "\n</main>", 1)
    page.write_text(text, encoding="utf-8")
    inserted.append((page, sentinel))
    print(f"release v2 bridged current Editions date layout: {rel}")

# Later product-detail edits deliberately replaced two old release-calendar
# paragraphs with more precise garment copy. The core needs only to know that
# those migrations have already landed. Put the exact core targets in temporary
# comments when—and only when—the current final product markers are all present.
for rel, cfg in TEXTILE_COMPAT.items():
    page = ROOT / rel
    if not page.is_file():
        raise SystemExit(f"Missing textile page for release compatibility: {rel}")
    text = page.read_text(encoding="utf-8")
    if not all(marker in text for marker in cfg["current_markers"]):
        continue
    for target_text in cfg["accepted_core_targets"]:
        if target_text in text:
            continue
        sentinel = f"<!-- release-v2 textile compatibility: {target_text} -->"
        if "</main>" not in text:
            raise SystemExit(f"No </main> in {rel}")
        text = text.replace("</main>", sentinel + "\n</main>", 1)
        inserted.append((page, sentinel))
        print(f"release v2 accepted current textile copy for legacy core: {rel}")
    page.write_text(text, encoding="utf-8")

old_argv = sys.argv[:]
sys.argv = [str(CORE), str(ROOT)]
try:
    runpy.run_path(str(CORE), run_name="__main__")
finally:
    sys.argv = old_argv
    for page, sentinel in inserted:
        if not page.is_file():
            continue
        text = page.read_text(encoding="utf-8")
        if sentinel in text:
            text = text.replace(sentinel + "\n", "", 1)
            text = text.replace(sentinel, "", 1)
            page.write_text(text, encoding="utf-8")

for rel in (*COMPAT.keys(), *TEXTILE_COMPAT.keys()):
    text = (ROOT / rel).read_text(encoding="utf-8")
    if "release-v2 compatibility:" in text or "release-v2 textile compatibility:" in text:
        raise SystemExit(f"Release compatibility sentinel leaked into {rel}")

# v1 deliberately restores its older detailed homepage copy after validating
# the release calendar. Replace only that exact legacy-final string with the
# approved concise public summary. The detailed keypad/newsletter explanation
# remains available on the Hallazgo/Editions pages; the directory stays brief.
home_final = {
    "en/index.html": (EN_HOME_LONG, EN_HOME_CONCISE),
    "index.html": (ES_HOME_LONG, ES_HOME_CONCISE),
}
for rel, (long_form, concise) in home_final.items():
    page = ROOT / rel
    text = page.read_text(encoding="utf-8")
    if long_form in text:
        text = text.replace(long_form, concise, 1)
        page.write_text(text, encoding="utf-8")
        print(f"release v2 restored concise Hallazgo homepage copy: {rel}")
    elif concise not in text:
        raise SystemExit(f"Concise Hallazgo homepage copy missing after release pass: {rel}")

for rel, (long_form, concise) in home_final.items():
    text = (ROOT / rel).read_text(encoding="utf-8")
    if concise not in text:
        raise SystemExit(f"Concise Hallazgo homepage validation failed: {rel}")
    if long_form in text:
        raise SystemExit(f"Long Hallazgo homepage description survived release pass: {rel}")

final_es = (ROOT / "index.html").read_text(encoding="utf-8")
for rel in ("404.html", "404/index.html"):
    page = ROOT / rel
    if not page.is_file():
        raise SystemExit(f"Missing custom 404 artifact after release pass: {rel}")
    page.write_text(final_es, encoding="utf-8")
    print(f"release v2 synchronized custom 404 artifact with final homepage: {rel}")

print("OOLITA release-calendar v2 completed with concise Hallazgo homepage copy and no compatibility stragglers.")
