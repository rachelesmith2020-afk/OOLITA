#!/usr/bin/env python3
"""Bring the existing OOLITA browser-world still into the opening 3D page view.

This is a hierarchy-only pass. It reuses the established first-party 3D preview
already published on the homepage, inserts it immediately after the H1 on both
language pages, and keeps the technical explanation after the visual encounter.
"""
from __future__ import annotations

from pathlib import Path
import re
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
STYLE_ID = "oolita-3d-visual-first-v1"
FIGURE_CLASS = "oolita-3d-hero-visual"
PREVIEW_SRC = "/img/oolita-browser-world-preview.jpg?v=green-fit-20260828-1202"

STYLE = r'''<style id="oolita-3d-visual-first-v1">
.oolita-3d-hero-visual{
  width:min(100%,72rem);
  margin:clamp(1.75rem,4vw,3.5rem) 0 clamp(3rem,7vw,6rem)!important;
  padding:0!important;
}
.oolita-3d-hero-visual img{
  display:block;
  width:100%!important;
  height:auto!important;
  margin:0!important;
  border-radius:0!important;
}
.oolita-3d-hero-visual figcaption{
  margin:.75rem 0 0 auto!important;
  max-width:38rem!important;
}
@media(max-width:760px){
  .oolita-3d-hero-visual{
    width:100%;
    margin:1.4rem 0 3rem!important;
  }
}
</style>'''

PAGES = {
    "mundo-3d/index.html": {
        "alt": "Vista previa del mundo 3D de OOLITA: Los Escullos reconstruido en el navegador.",
        "caption": "Los Escullos levantado en el navegador. Una imagen; el camino completo abre el 3 de enero.",
    },
    "en/3d-world/index.html": {
        "alt": "Preview of the OOLITA 3D world: Los Escullos reconstructed in the browser.",
        "caption": "Los Escullos raised in the browser. One still; the full path opens on 3 January.",
    },
}

if not ROOT.is_dir():
    raise SystemExit(f"Missing built site: {ROOT}")

style_re = re.compile(
    rf'<style\s+id=["\']{re.escape(STYLE_ID)}["\'][^>]*>[\s\S]*?</style>',
    flags=re.I,
)
h1_re = re.compile(r'<h1\b[^>]*>[\s\S]*?</h1>', flags=re.I)
figure_re = re.compile(
    rf'<figure\b[^>]*class=["\'][^"\']*\b{re.escape(FIGURE_CLASS)}\b[^"\']*["\'][^>]*>[\s\S]*?</figure>',
    flags=re.I,
)

for rel, copy in PAGES.items():
    path = ROOT / rel
    if not path.is_file():
        raise SystemExit(f"Missing 3D page: {rel}")
    html = path.read_text(encoding="utf-8")

    # Keep one canonical style block.
    if style_re.search(html):
        html = style_re.sub(STYLE, html, count=1)
    elif "</head>" in html:
        html = html.replace("</head>", STYLE + "\n</head>", 1)
    else:
        raise SystemExit(f"3D page has no </head>: {rel}")

    # Remove a previous canonical hero figure, if present, before reinserting.
    html = figure_re.sub("", html)
    h1 = h1_re.search(html)
    if not h1:
        raise SystemExit(f"3D page has no H1: {rel}")

    figure = (
        f'<figure class="{FIGURE_CLASS}">'
        f'<img src="{PREVIEW_SRC}" alt="{copy["alt"]}" loading="eager" decoding="async">'
        f'<figcaption>{copy["caption"]}</figcaption>'
        '</figure>'
    )
    html = html[:h1.end()] + "\n" + figure + "\n" + html[h1.end():]
    path.write_text(html, encoding="utf-8")

# Fail closed on duplicates, missing asset references, or placement regressions.
for rel, copy in PAGES.items():
    html = (ROOT / rel).read_text(encoding="utf-8")
    if len(style_re.findall(html)) != 1:
        raise SystemExit(f"3D visual-first style is not unique in {rel}")
    figures = list(figure_re.finditer(html))
    if len(figures) != 1:
        raise SystemExit(f"3D hero figure is not unique in {rel}: found {len(figures)}")
    hero = figures[0]
    if PREVIEW_SRC not in hero.group(0):
        raise SystemExit(f"3D hero does not use the approved first-party preview in {rel}")
    if copy["alt"] not in hero.group(0) or copy["caption"] not in hero.group(0):
        raise SystemExit(f"3D hero accessibility/editorial copy missing in {rel}")
    h1 = h1_re.search(html)
    if not h1 or hero.start() <= h1.end():
        raise SystemExit(f"3D hero is not positioned after H1 in {rel}")
    first_p = re.search(r'<p\b', html[h1.end():], flags=re.I)
    if first_p and hero.start() > h1.end() + first_p.start():
        raise SystemExit(f"3D hero does not precede the opening explanation in {rel}")

print("OOLITA 3D visual-first hierarchy applied and validated in Spanish and English.")
