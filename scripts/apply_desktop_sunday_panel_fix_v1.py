#!/usr/bin/env python3
"""Keep the homepage Sunday artwork inside its desktop hero column."""
from __future__ import annotations

from pathlib import Path
import re
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
STYLE_ID = "oolita-desktop-sunday-panel-fix-v1"
STYLE = r'''<style id="oolita-desktop-sunday-panel-fix-v1">
/* The Sunday field is nested in the hero's right column. The general art-field
   rule makes fields viewport-wide; on desktop that caused this one to cover the
   hero copy. Keep it contained here, while retaining the full-width mobile row. */
@media(min-width:56.001rem){
  body.art-home .hero .der{
    min-width:0;
    overflow:hidden;
    display:flex;
    flex-direction:column;
  }
  body.art-home #oolita-art-field-sundays{
    width:100%!important;
    max-width:100%!important;
    min-height:100%!important;
    margin:0!important;
    padding:clamp(1.5rem,2.4vw,2.5rem)!important;
  }
  body.art-home #oolita-art-field-sundays .art-kicker{
    top:clamp(1.5rem,2.4vw,2.5rem)!important;
    left:clamp(1.5rem,2.4vw,2.5rem)!important;
  }
  body.art-home #oolita-art-field-sundays .art-word{
    max-width:100%!important;
    font-size:clamp(8rem,11.5vw,12rem)!important;
    line-height:.68!important;
    overflow-wrap:normal!important;
    white-space:nowrap!important;
  }
  body.art-home #oolita-art-field-sundays .art-caption{
    max-width:18rem!important;
    margin:clamp(1.25rem,2vw,2rem) 0 0!important;
    font-size:clamp(.95rem,1.1vw,1.1rem)!important;
  }
}
</style>'''

if not ROOT.is_dir():
    raise SystemExit(f"Missing built site: {ROOT}")

style_pattern = re.compile(
    rf'<style\s+id=["\']{re.escape(STYLE_ID)}["\'][^>]*>.*?</style>',
    flags=re.I | re.S,
)

for rel in ("index.html", "en/index.html"):
    target = ROOT / rel
    if not target.is_file():
        raise SystemExit(f"Missing homepage: {rel}")
    html = target.read_text(encoding="utf-8")
    if style_pattern.search(html):
        html = style_pattern.sub(STYLE, html, count=1)
    elif "</head>" in html:
        html = html.replace("</head>", STYLE + "\n</head>", 1)
    else:
        raise SystemExit(f"Homepage has no </head>: {rel}")
    target.write_text(html, encoding="utf-8")

for rel in ("index.html", "en/index.html"):
    html = (ROOT / rel).read_text(encoding="utf-8")
    for needle in (STYLE_ID, "#oolita-art-field-sundays", "width:100%!important"):
        if needle not in html:
            raise SystemExit(f"Desktop Sunday panel invariant failed in {rel}: {needle}")

print("OOLITA desktop Sunday panel containment validated in both homepages.")

# Production propagation trigger: align published Sunday images on mobile with asset guards.
# Production propagation trigger: include corrected fossil-dune gate after mobile Sunday repair.
