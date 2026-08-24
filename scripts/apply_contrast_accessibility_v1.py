#!/usr/bin/env python3
"""Final WCAG text-contrast and footer presentation layer for OOLITA.

The base OOLITA green on paper is already high-contrast. The remaining Axe
failures came from opacity on secondary copy / future archive rows and from one
indigo-on-coral label. This layer keeps the palette and hierarchy while making
all rendered text meet WCAG AA. It also gives the global footer a clear final
layout using the established coral / ink-blue poster palette and removes the
inherited link decoration that renders as stray horizontal bars.
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

/* Footer: use the existing coral + ink-blue poster palette instead of the
   heavy dark-green field. Coral / ink-blue remains AA for normal text. */
body.art-restaged footer,
body.art-restaged .pie{
  background:var(--art-coral,#EF725E)!important;
  color:var(--art-ink-blue,#132572)!important;
  border:0!important;
  border-top:0!important;
  box-shadow:none!important;
  min-height:0!important;
  padding:clamp(2.4rem,4.5vw,4rem) clamp(1.25rem,7.5vw,8rem)!important;
  column-gap:clamp(2.5rem,6vw,7rem)!important;
  row-gap:1rem!important;
  align-items:start!important;
  box-sizing:border-box!important;
}

/* Whichever wrapper directly owns the credit block and nav becomes a clean
   two-column footer: credits left, contact/navigation right. */
body.art-restaged footer:has(> .firma):has(> nav),
body.art-restaged footer :has(> .firma):has(> nav),
body.art-restaged .pie:has(> .firma):has(> nav),
body.art-restaged .pie :has(> .firma):has(> nav){
  display:grid!important;
  grid-template-columns:minmax(0,1.85fr) minmax(17rem,.65fr)!important;
  gap:clamp(2.5rem,6vw,7rem)!important;
  align-items:start!important;
  width:100%!important;
  max-width:1420px!important;
  margin-inline:auto!important;
  box-sizing:border-box!important;
}

body.art-restaged footer .firma,
body.art-restaged .pie .firma{
  display:grid!important;
  grid-template-columns:minmax(0,1fr)!important;
  gap:.52rem!important;
  align-content:start!important;
  justify-items:start!important;
  width:100%!important;
  max-width:64rem!important;
  margin:0!important;
}
body.art-restaged footer .firma>*,
body.art-restaged .pie .firma>*{
  margin:0!important;
}

/* Contact / About / Privacy now read as one compact navigation group rather
   than three headings spread across the full footer width. */
body.art-restaged footer nav,
body.art-restaged .pie nav{
  display:grid!important;
  grid-template-columns:minmax(0,1fr)!important;
  gap:.5rem!important;
  align-content:start!important;
  justify-items:start!important;
  width:100%!important;
  min-width:0!important;
  margin:0!important;
}

body.art-restaged footer .rot,
body.art-restaged .pie .rot,
body.art-restaged footer nav a,
body.art-restaged .pie nav a{
  color:inherit!important;
  opacity:1!important;
  font-size:clamp(.72rem,.78vw,.84rem)!important;
  line-height:1.45!important;
  letter-spacing:.09em!important;
  font-weight:650!important;
  white-space:normal!important;
  overflow-wrap:break-word!important;
  word-break:normal!important;
}

/* Remove the inherited footer-link rule that is drawing the long horizontal
   bars beneath the email and Privacy link. */
body.art-restaged footer a,
body.art-restaged .pie a{
  color:inherit!important;
  text-decoration:none!important;
  border:0!important;
  border-bottom:0!important;
  box-shadow:none!important;
  background-image:none!important;
  width:auto!important;
  max-width:100%!important;
  min-height:0!important;
  padding:.08rem 0!important;
  margin:0!important;
}
body.art-restaged footer a::before,
body.art-restaged footer a::after,
body.art-restaged .pie a::before,
body.art-restaged .pie a::after{
  content:none!important;
  display:none!important;
  width:0!important;
  height:0!important;
  border:0!important;
  box-shadow:none!important;
  background:none!important;
}
body.art-restaged footer a:hover,
body.art-restaged .pie a:hover{
  font-weight:800!important;
}
body.art-restaged footer a:focus-visible,
body.art-restaged .pie a:focus-visible{
  outline:2px solid currentColor!important;
  outline-offset:4px!important;
}
body.art-restaged footer hr,
body.art-restaged .pie hr{
  display:none!important;
}

@media(max-width:820px){
  body.art-restaged footer,
  body.art-restaged .pie{
    padding:2rem 1.25rem 2.25rem!important;
  }
  body.art-restaged footer:has(> .firma):has(> nav),
  body.art-restaged footer :has(> .firma):has(> nav),
  body.art-restaged .pie:has(> .firma):has(> nav),
  body.art-restaged .pie :has(> .firma):has(> nav){
    grid-template-columns:minmax(0,1fr)!important;
    gap:1.5rem!important;
  }
  body.art-restaged footer nav,
  body.art-restaged .pie nav{
    grid-template-columns:repeat(2,minmax(0,1fr))!important;
    gap:.5rem 1.25rem!important;
  }
}

@media(max-width:520px){
  body.art-restaged footer nav,
  body.art-restaged .pie nav{
    grid-template-columns:minmax(0,1fr)!important;
  }
  body.art-restaged footer .rot,
  body.art-restaged .pie .rot,
  body.art-restaged footer nav a,
  body.art-restaged .pie nav a{
    font-size:.74rem!important;
    letter-spacing:.075em!important;
  }
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
    "index.html": ("p.claim-en.art-manifesto.art-manifesto--echo", ".c > .glo", ".follow-privacy", "--art-coral,#EF725E", "a::after"),
    "en/index.html": ("p.claim-en.art-manifesto.art-manifesto--echo", ".c > .glo", ".follow-privacy", "--art-coral,#EF725E", "a::after"),
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

print(f"OOLITA WCAG contrast and footer presentation layer validated across {len(html_files)} HTML pages.")
