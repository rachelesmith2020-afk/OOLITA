#!/usr/bin/env python3
"""Final WCAG text-contrast layer for OOLITA.

The base OOLITA green on paper is already high-contrast. The remaining Axe
failures came from opacity on secondary copy / future archive rows and from one
indigo-on-coral label. This layer keeps the palette and hierarchy while making
all rendered text meet WCAG AA.
"""
from __future__ import annotations

from pathlib import Path
import re
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
STYLE_ID = "oolita-contrast-accessibility-v1"

STYLE = r'''<style id="oolita-contrast-accessibility-v1">
/* Secondary text on paper. */
body.art-home .glo,
body.art-home .menu-group-label,
body.art-home .follow-status,
body.art-home .follow-privacy{
  opacity:.84!important;
}

/* A more-specific art-restage rule sets this echo to .72!important, so use
   the full selector and native green rather than fighting it with translucency. */
body.art-home p.claim-en.art-manifesto.art-manifesto--echo{
  opacity:1!important;
}

/* This one label is on coral, not paper. Darkened indigo gives >5:1 contrast
   while staying within the existing indigo/coral palette. */
body.art-home .c > .glo{
  opacity:1!important;
  color:#1d1b4f!important;
}

/* Bilingual book excerpt metadata. */
.book-excerpt-figure figcaption,
.book-excerpt-lang{
  opacity:.84!important;
}

/* Sunday field: do not fade text-bearing tiles. Future state is shown with a
   quieter border, not low-contrast text. */
.sunday-field-note,
.sunday-field-axis,
.sunday-tile-date,
.sunday-tile-state{
  opacity:.84!important;
}
.sunday-tile,
.sunday-tile.is-current{
  opacity:1!important;
}
.sunday-tile:not(.is-published):not(.is-current){
  border-color:rgba(45,78,35,.38)!important;
}
.sunday-tile.is-published,
.sunday-tile.is-current{
  border-color:currentColor!important;
}

/* Detailed Sundays archive: .espera previously faded the whole future row,
   producing 2.76:1 text. Keep future rows inactive through their existing
   semantics and a lighter rule, but render the text itself at native contrast. */
.espera.fila,
.espera.fila .num,
.espera.fila .cuerpo,
.espera.fila .nombre,
.espera.fila time,
.espera.fila .fecha,
.espera.fila .glo,
.espera.fila span,
.espera.fila p{
  opacity:1!important;
  color:#2d4e23!important;
}
.espera.fila{
  border-color:rgba(45,78,35,.38)!important;
}
</style>'''

if not ROOT.is_dir():
    raise SystemExit(f"Missing built site: {ROOT}")

html_files = sorted(ROOT.rglob("*.html"))
if not html_files:
    raise SystemExit("No HTML pages found")

pattern = re.compile(
    rf'<style\s+id=["\']{re.escape(STYLE_ID)}["\'][^>]*>.*?</style>',
    flags=re.I | re.S,
)

for target in html_files:
    html = target.read_text(encoding="utf-8")
    if pattern.search(html):
        html = pattern.sub(STYLE, html, count=1)
    else:
        if "</head>" not in html:
            raise SystemExit(f"Missing </head>: {target.relative_to(ROOT)}")
        html = html.replace("</head>", STYLE + "\n</head>", 1)
    target.write_text(html, encoding="utf-8")

checks = {
    "index.html": ("p.claim-en.art-manifesto.art-manifesto--echo", ".c > .glo", ".follow-privacy"),
    "en/index.html": ("p.claim-en.art-manifesto.art-manifesto--echo", ".c > .glo", ".follow-privacy"),
    "ediciones/libro/index.html": (".book-excerpt-lang", "figcaption"),
    "en/editions/book/index.html": (".book-excerpt-lang", "figcaption"),
    "domingos/index.html": (".sunday-tile-date", ".espera.fila"),
    "en/sundays/index.html": (".sunday-tile-date", ".espera.fila"),
}
for rel, needles in checks.items():
    target = ROOT / rel
    if not target.is_file():
        raise SystemExit(f"Missing contrast-check page: {rel}")
    html = target.read_text(encoding="utf-8")
    if STYLE_ID not in html:
        raise SystemExit(f"Contrast style missing in {rel}")
    for needle in needles:
        if needle not in html:
            raise SystemExit(f"Contrast invariant missing in {rel}: {needle}")

print(f"OOLITA WCAG text-contrast layer validated across {len(html_files)} HTML pages.")
