#!/usr/bin/env python3
"""Add a genuine bilingual OOLITA excerpt and book illustration to book pages.

Source: the current Oolita-bilingual.pdf reading edition in the project Drive.
The excerpt is copied verbatim from the fable; the illustration is a reduced web
render of the cat-and-labyrinth artwork on an early page whose artwork is shared
with the production sequence. No new illustration or story copy is invented.
"""
from __future__ import annotations

from pathlib import Path
import re
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")

# 320px web rendering of the genuine cat-and-labyrinth book illustration.
# Kept inline so the source-of-truth deployment remains self-contained even
# though the production site is reconstructed from the current public origin.
ILLUSTRATION_B64 = "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"

STYLE = """<style id=\"oolita-book-excerpt-style\">
.book-excerpt{padding-top:clamp(2.5rem,6vw,5rem)}
.book-excerpt-layout{display:grid;grid-template-columns:minmax(12rem,.62fr) minmax(0,1.55fr);gap:clamp(1.5rem,5vw,4rem);align-items:center;margin-top:clamp(1.5rem,3vw,2.5rem)}
.book-excerpt-figure{margin:0;text-align:center}.book-excerpt-figure img{display:block;width:100%;max-width:20rem;height:auto;margin:0 auto}.book-excerpt-figure figcaption{margin-top:.7rem;font-size:.78rem;line-height:1.4;opacity:.68}
.book-excerpt-spread{display:grid;grid-template-columns:1fr 1fr;border-top:1px solid currentColor;border-bottom:1px solid currentColor}
.book-excerpt-page{padding:clamp(1.15rem,2.5vw,2rem)}.book-excerpt-page+.book-excerpt-page{border-left:1px solid currentColor}.book-excerpt-lang{display:block;margin-bottom:.9rem;font-size:.72rem;letter-spacing:.16em;text-transform:uppercase;opacity:.65}.book-excerpt-page p{margin:0;font-size:clamp(1rem,1.25vw,1.15rem);line-height:1.72}
@media(max-width:760px){.book-excerpt-layout{grid-template-columns:1fr}.book-excerpt-figure img{max-width:15rem}.book-excerpt-spread{grid-template-columns:1fr}.book-excerpt-page+.book-excerpt-page{border-left:0;border-top:1px solid currentColor}}
</style>"""

ES_TEXT = (
    "En la entrada, hoy el mundo sonaba fuerte. Una sensación erizada, un peso denso. "
    "Junto a la entrada del camino, una chumbera se alzaba al sol, toda púas y palas planas "
    "de un gris verdoso, con flores ardiendo naranja en los bordes, impasible. "
    "El gato no se sentía impasible."
)
EN_TEXT = (
    "At the entrance, the world was loud today. A spiky sensation, a heavy weight. "
    "By the entrance to the path, a chumbera stood in the sun, all spines and flat grey-green pads, "
    "flowers blazing orange at the edges, unbothered. The cat did not feel unbothered."
)


def patch(path: str, *, language: str) -> None:
    target = ROOT / path
    if not target.is_file():
        raise SystemExit(f"Missing book page for excerpt: {path}")
    text = target.read_text(encoding="utf-8")
    marker = 'id="extracto-libro"'
    if marker in text:
        return

    if 'id="oolita-book-excerpt-style"' not in text:
        if "</head>" not in text:
            raise SystemExit(f"No </head> in {path}")
        text = text.replace("</head>", STYLE + "</head>", 1)

    if language == "es":
        label = "Dentro del libro"
        heading = "Una página para leer."
        caption = "Extracto e ilustración de la edición bilingüe."
        aria = "Extracto bilingüe de OOLITA, español e inglés"
    else:
        label = "Inside the book"
        heading = "A page to read."
        caption = "Excerpt and illustration from the bilingual edition."
        aria = "Bilingual OOLITA excerpt, Spanish and English"

    image = f"data:image/png;base64,{ILLUSTRATION_B64}"
    section = f'''<section class="tramo book-excerpt" id="extracto-libro">
  <span class="rot">{label}</span>
  <h2 class="grande">{heading}</h2>
  <div class="book-excerpt-layout">
    <figure class="book-excerpt-figure">
      <img src="{image}" width="320" height="320" loading="lazy" decoding="async" alt="Ilustración del libro: Electro frente al trazado del laberinto Oolita." />
      <figcaption>{caption}</figcaption>
    </figure>
    <div class="book-excerpt-spread" aria-label="{aria}">
      <div class="book-excerpt-page" lang="es"><span class="book-excerpt-lang">ES</span><p>{ES_TEXT}</p></div>
      <div class="book-excerpt-page" lang="en"><span class="book-excerpt-lang">EN</span><p>{EN_TEXT}</p></div>
    </div>
  </div>
</section>'''

    anchor = re.search(r'<section\b[^>]*\bid=["\'](?:comprar|buy)["\'][^>]*>', text, flags=re.I)
    if not anchor:
        raise SystemExit(f"Could not find purchase section anchor in {path}")
    text = text[: anchor.start()] + section + text[anchor.start() :]
    target.write_text(text, encoding="utf-8")


if not ROOT.is_dir():
    raise SystemExit(f"Missing built site: {ROOT}")

patch("ediciones/libro/index.html", language="es")
patch("en/editions/book/index.html", language="en")

for path in ("ediciones/libro/index.html", "en/editions/book/index.html"):
    text = (ROOT / path).read_text(encoding="utf-8")
    for required in (
        'id="extracto-libro"',
        'id="oolita-book-excerpt-style"',
        ES_TEXT,
        EN_TEXT,
        "data:image/png;base64,",
        'width="320" height="320"',
    ):
        if required not in text:
            raise SystemExit(f"Book excerpt invariant missing in {path}: {required[:80]}")

print("OOLITA genuine bilingual book excerpt validated successfully.")
