#!/usr/bin/env python3
"""Move the existing genuine OOLITA book illustration into the opening view.

This is a hierarchy-only pass: it does not invent artwork or copy. It reuses the
single book illustration already installed by apply_book_excerpt_v1.py, moves that
figure immediately after the page H1, and gives it restrained responsive sizing so
a visitor sees the object before the longer production explanation.
"""
from __future__ import annotations

from pathlib import Path
import re
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
STYLE_ID = "oolita-book-visual-first-v1"
FIGURE_CLASS = "oolita-book-hero-visual"
BOOK_MARKER = "Electro frente al trazado del laberinto Oolita"

STYLE = r'''<style id="oolita-book-visual-first-v1">
/* Genuine book artwork, moved into the opening reading area. */
.oolita-book-hero-visual{
  float:right;
  width:min(34vw,27rem);
  margin:-5.25rem 0 2.75rem clamp(2rem,5vw,5rem)!important;
  padding:0!important;
  clear:right;
}
.oolita-book-hero-visual img{
  display:block;
  width:100%!important;
  height:auto!important;
  margin:0!important;
  border-radius:0!important;
}
.oolita-book-hero-visual figcaption{
  margin:.65rem 0 0!important;
  max-width:100%!important;
}
@media(max-width:760px){
  .oolita-book-hero-visual{
    float:none;
    width:min(100%,24rem);
    margin:1.35rem 0 2.5rem!important;
    clear:both;
  }
}
</style>'''

PAGES = (
    "ediciones/libro/index.html",
    "en/editions/book/index.html",
)

if not ROOT.is_dir():
    raise SystemExit(f"Missing built site: {ROOT}")

style_re = re.compile(
    rf'<style\s+id=["\']{re.escape(STYLE_ID)}["\'][^>]*>[\s\S]*?</style>',
    flags=re.I,
)
figure_re = re.compile(r'<figure\b[^>]*>[\s\S]*?</figure>', flags=re.I)
h1_re = re.compile(r'<h1\b[^>]*>[\s\S]*?</h1>', flags=re.I)
hero_figure_re = re.compile(
    rf'<figure\b[^>]*class=["\'][^"\']*\b{re.escape(FIGURE_CLASS)}\b[^"\']*["\'][^>]*>[\s\S]*?</figure>',
    flags=re.I,
)


def add_class(tag: str, class_name: str) -> str:
    match = re.search(r'\bclass\s*=\s*(["\'])(.*?)\1', tag, flags=re.I | re.S)
    if match:
        classes = match.group(2).split()
        if class_name in classes:
            return tag
        updated = " ".join([*classes, class_name])
        return tag[:match.start(2)] + updated + tag[match.end(2):]
    return tag[:-1] + f' class="{class_name}">'


for rel in PAGES:
    path = ROOT / rel
    if not path.is_file():
        raise SystemExit(f"Missing book page: {rel}")
    html = path.read_text(encoding="utf-8")

    # Keep one canonical style block.
    if style_re.search(html):
        html = style_re.sub(STYLE, html, count=1)
    elif "</head>" in html:
        html = html.replace("</head>", STYLE + "\n</head>", 1)
    else:
        raise SystemExit(f"Book page has no </head>: {rel}")

    figures = [m for m in figure_re.finditer(html) if BOOK_MARKER in m.group(0)]
    if len(figures) != 1:
        raise SystemExit(
            f"Expected exactly one genuine OOLITA book illustration in {rel}; found {len(figures)}"
        )
    figure = figures[0]
    block = figure.group(0)
    opening = re.match(r'<figure\b[^>]*>', block, flags=re.I)
    if not opening:
        raise SystemExit(f"Malformed book figure in {rel}")
    block = add_class(opening.group(0), FIGURE_CLASS) + block[opening.end():]

    # Remove the existing occurrence before locating the final H1 position.
    html = html[:figure.start()] + html[figure.end():]
    h1 = h1_re.search(html)
    if not h1:
        raise SystemExit(f"Book page has no H1: {rel}")
    html = html[:h1.end()] + "\n" + block + "\n" + html[h1.end():]
    path.write_text(html, encoding="utf-8")

# Fail closed on duplicates or a later-page placement regression.
for rel in PAGES:
    html = (ROOT / rel).read_text(encoding="utf-8")
    if html.count(BOOK_MARKER) != 1:
        raise SystemExit(f"Book illustration marker is not unique in {rel}")
    if len(style_re.findall(html)) != 1:
        raise SystemExit(f"Book visual-first style is not unique in {rel}")
    hero_figures = list(hero_figure_re.finditer(html))
    if len(hero_figures) != 1:
        raise SystemExit(f"Book hero figure is not unique in {rel}: found {len(hero_figures)}")
    h1 = h1_re.search(html)
    hero = hero_figures[0]
    if not h1 or hero.start() <= h1.end():
        raise SystemExit(f"Book illustration is not positioned after the H1 in {rel}")
    if BOOK_MARKER not in hero.group(0):
        raise SystemExit(f"Book hero figure is not the genuine book illustration in {rel}")
    # The figure should enter before the first ordinary paragraph following H1.
    next_paragraph = re.search(r'<p\b', html[h1.end():], flags=re.I)
    if next_paragraph and hero.start() > h1.end() + next_paragraph.start():
        raise SystemExit(f"Book illustration does not lead the opening copy in {rel}")

print("OOLITA book visual-first hierarchy applied and validated in Spanish and English.")
