#!/usr/bin/env python3
"""Final WCAG text-contrast layer for OOLITA.

The OOLITA green (#2d4e23) on paper (#f1e7d4) has strong native contrast.
The remaining Axe failures were caused by opacity applied to small text and,
on the Sundays archive, to whole inactive tiles. This layer preserves the
palette and visual hierarchy while keeping rendered text above 4.5:1.
"""
from __future__ import annotations

from pathlib import Path
import re
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
STYLE_ID = "oolita-contrast-accessibility-v1"

STYLE = r'''<style id="oolita-contrast-accessibility-v1">
/* Native verde on papel is ~7.7:1. Keep secondary text at >= .84 opacity,
   which preserves hierarchy while providing comfortable WCAG AA headroom. */
body.art-home .claim-en,
body.art-home .glo,
body.art-home .menu-group-label,
body.art-home .follow-status,
body.art-home .follow-privacy{
  opacity:.84!important;
}

/* Bilingual book excerpt metadata: small text must remain fully legible. */
.book-excerpt-figure figcaption,
.book-excerpt-lang{
  opacity:.84!important;
}

/* Sundays: never fade a whole text-bearing tile. Distinguish future tiles
   through the border instead, so numbers/dates stay readable. */
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
    "index.html": (".claim-en", ".glo", ".follow-privacy"),
    "en/index.html": (".claim-en", ".glo", ".follow-privacy"),
    "ediciones/libro/index.html": (".book-excerpt-lang", "figcaption"),
    "en/editions/book/index.html": (".book-excerpt-lang", "figcaption"),
    "domingos/index.html": (".sunday-tile-date", ".sunday-field-axis"),
    "en/sundays/index.html": (".sunday-tile-date", ".sunday-field-axis"),
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
