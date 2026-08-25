#!/usr/bin/env python3
"""Bridge current reader-facing contact headings into the final low-severity SEO pass.

The live site is the deployment source, and voice edits can legitimately change
contact headings (for example, "Tell me" -> "Tell us") without changing the
section's meaning. This helper inserts the already-approved depth blocks using
stable structural/contact markers, so the strict final SEO gate stays rebuild-safe.
"""
from __future__ import annotations

from pathlib import Path
import re
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
if not ROOT.is_dir():
    raise SystemExit(f"Missing built site: {ROOT}")

ABOUT_EN_BLOCK = '''<section class="tramo" id="working-rhythm"><span class="rot">22 Sundays</span><h2 class="grande">A public working rhythm.</h2><p class="parr">The 22 Sundays are the public rhythm of OOLITA: each release adds an image, a short text and another route into the place. The editions and the 3D world develop alongside that sequence, while the labyrinth at Los Escullos remains the physical starting point. The archive keeps those stages visible rather than presenting the project as a finished object.</p></section>'''

WORK_EN_BLOCK = '''<section class="tramo" id="before-writing"><span class="rot">Before writing</span><h2 class="grande">A useful proposal is specific.</h2><p class="parr">If you are a bookshop, say where you are and what kind of publication you would like to stock. If you are an educator or cultural organisation, describe the group, place, date range and the kind of activity you have in mind. Makers can explain the material, process and production scale they work with.</p><p class="parr">OOLITA is interested in small, clearly attributed collaborations connected to books, observation, fieldwork and material practice. It does not add partner names speculatively: authorship, production, materials, quantities and responsibilities are stated only after an agreement exists.</p><p class="parr">Where a proposal involves Cabo de Gata, the starting point is low-impact use: no collecting from the site and no second OOLITA labyrinth. The aim is to extend attention to the place, not increase pressure on it.</p><p class="parr">A first email does not need to be formal. A few sentences, a location and a link to relevant work are enough to begin.</p></section>'''

WORK_ES_BLOCK = '''<section class="tramo" id="antes-de-escribir"><span class="rot">Antes de escribir</span><h2 class="grande">Una propuesta útil es concreta.</h2><p class="parr">Si eres una librería, indica dónde estás y qué tipo de publicación te interesaría tener. Si eres educador u organización cultural, describe el grupo, el lugar, el intervalo de fechas y el tipo de actividad que imaginas. Los artesanos o productores pueden explicar el material, el proceso y la escala con la que trabajan.</p><p class="parr">OOLITA busca colaboraciones pequeñas y claramente atribuidas, relacionadas con libros, observación, trabajo de campo y práctica material. No añade nombres de colaboradores de forma especulativa: autoría, producción, materiales, cantidades y responsabilidades se indican sólo cuando existe un acuerdo.</p><p class="parr">Cuando una propuesta afecta a Cabo de Gata, el punto de partida es un uso de bajo impacto: no recoger materiales del lugar y no crear un segundo laberinto OOLITA. La intención es ampliar la atención al territorio, no aumentar la presión sobre él.</p><p class="parr">Un primer correo no tiene que ser formal. Unas frases, una ubicación y un enlace a trabajo relevante bastan para empezar.</p></section>'''

TARGETS = {
    "en/about/index.html": (
        'id="working-rhythm"',
        ABOUT_EN_BLOCK,
        re.compile(
            r'<section\b[^>]*class=["\'][^"\']*\btramo\b[^"\']*["\'][^>]*>\s*'
            r'<span\b[^>]*class=["\'][^"\']*\brot\b[^"\']*["\'][^>]*>\s*Contact\s*</span>\s*'
            r'<h2\b[^>]*class=["\'][^"\']*\bgrande\b[^"\']*["\'][^>]*>\s*Write\.?\s*</h2>',
            re.I | re.S,
        ),
    ),
    "en/work-with-oolita/index.html": (
        'id="before-writing"',
        WORK_EN_BLOCK,
        re.compile(
            r'<section\b[^>]*class=["\'][^"\']*\btramo\b[^"\']*\benv\b[^"\']*["\'][^>]*>\s*'
            r'<span\b[^>]*class=["\'][^"\']*\brot\b[^"\']*["\'][^>]*>\s*Contact\s*</span>\s*'
            r'<h2\b[^>]*class=["\'][^"\']*\bgrande\b[^"\']*["\'][^>]*>\s*Tell\s+(?:me|us)\s+what\s+you\s+have\s+in\s+mind\.?\s*</h2>',
            re.I | re.S,
        ),
    ),
    "colaborar/index.html": (
        'id="antes-de-escribir"',
        WORK_ES_BLOCK,
        re.compile(
            r'<section\b[^>]*class=["\'][^"\']*\btramo\b[^"\']*\benv\b[^"\']*["\'][^>]*>\s*'
            r'<span\b[^>]*class=["\'][^"\']*\brot\b[^"\']*["\'][^>]*>\s*Contacto\s*</span>\s*'
            r'<h2\b[^>]*class=["\'][^"\']*\bgrande\b[^"\']*["\'][^>]*>\s*Cuéntame\s+qué\s+tienes\s+en\s+mente\.?\s*</h2>',
            re.I | re.S,
        ),
    ),
}

for rel, (marker, block, anchor_re) in TARGETS.items():
    page = ROOT / rel
    if not page.is_file():
        raise SystemExit(f"Missing low-severity bridge page: {rel}")
    text = page.read_text(encoding="utf-8")
    if marker in text:
        print(f"low-severity bridge already present: {rel}")
        continue
    match = anchor_re.search(text)
    if not match:
        raise SystemExit(f"Stable contact-section anchor missing in {rel}")
    text = text[:match.start()] + block + "\n" + text[match.start():]
    page.write_text(text, encoding="utf-8")
    if marker not in page.read_text(encoding="utf-8"):
        raise SystemExit(f"Low-severity bridge marker missing after insertion: {rel}")
    print(f"low-severity bridge inserted before current contact heading: {rel}")

print("OOLITA low-severity contact-anchor bridge passed.")
