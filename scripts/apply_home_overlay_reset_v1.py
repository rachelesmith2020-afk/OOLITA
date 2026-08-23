#!/usr/bin/env python3
"""Remove the homepage handwritten/overlay treatment and use clean typography.

The manifesto copy remains in the document, but it is returned to the normal
flow with a restrained sans-serif treatment. This is deliberately applied to
both language homepages and at all viewport widths so desktop, laptop and
mobile cannot inherit the old script/overlay styling again.
"""
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
STYLE_ID = "oolita-home-overlay-reset-v1"
STYLE = r'''<style id="oolita-home-overlay-reset-v1">
/* Final homepage typography reset: no handwriting, overlays or decorative strokes. */
body.art-home .art-manifesto,
body.art-home .art-manifesto *{
  font-family:Arial,Helvetica,sans-serif!important;
  font-style:normal!important;
  text-decoration:none!important;
  text-shadow:none!important;
  transform:none!important;
  writing-mode:horizontal-tb!important;
}
body.art-home .art-manifesto{
  display:block!important;
  position:static!important;
  inset:auto!important;
  float:none!important;
  clear:both!important;
  z-index:auto!important;
  width:auto!important;
  max-width:26ch!important;
  margin:.75rem 0 1rem!important;
  padding:0!important;
  background:none!important;
  border:0!important;
  mix-blend-mode:normal!important;
  opacity:1!important;
  font-size:clamp(1.7rem,3vw,2.8rem)!important;
  line-height:1.08!important;
  letter-spacing:-.025em!important;
  font-weight:600!important;
  text-wrap:balance!important;
  overflow:visible!important;
}
body.art-home .art-manifesto.art-manifesto--echo{
  display:block!important;
  position:static!important;
  width:auto!important;
  max-width:38ch!important;
  margin:0 0 clamp(2.75rem,5vw,4.5rem)!important;
  padding:0!important;
  font-size:clamp(.95rem,1.25vw,1.15rem)!important;
  line-height:1.42!important;
  letter-spacing:.01em!important;
  font-weight:500!important;
  opacity:.72!important;
  text-wrap:pretty!important;
}
body.art-home .art-manifesto::before,
body.art-home .art-manifesto::after,
body.art-home .art-manifesto *::before,
body.art-home .art-manifesto *::after{
  content:none!important;
  display:none!important;
}
@media(max-width:760px){
  body.art-home .art-manifesto{
    max-width:22ch!important;
    margin:.7rem 0 .9rem!important;
    font-size:clamp(1.6rem,7.2vw,2.25rem)!important;
    line-height:1.1!important;
  }
  body.art-home .art-manifesto.art-manifesto--echo{
    max-width:32ch!important;
    margin:0 0 2.75rem!important;
    font-size:1rem!important;
    line-height:1.45!important;
  }
}
</style>'''

if not ROOT.is_dir():
    raise SystemExit(f"Missing built site: {ROOT}")

for rel in ("index.html", "en/index.html"):
    target = ROOT / rel
    if not target.is_file():
        raise SystemExit(f"Missing homepage: {rel}")
    html = target.read_text(encoding="utf-8")
    if f'id="{STYLE_ID}"' not in html:
        if "</head>" not in html:
            raise SystemExit(f"Homepage has no </head>: {rel}")
        html = html.replace("</head>", STYLE + "\n</head>", 1)
        target.write_text(html, encoding="utf-8")

for rel in ("index.html", "en/index.html"):
    html = (ROOT / rel).read_text(encoding="utf-8")
    for needle in (STYLE_ID, "art-manifesto", "font-family:Arial,Helvetica,sans-serif!important"):
        if needle not in html:
            raise SystemExit(f"Homepage overlay reset invariant failed in {rel}: {needle}")

print("OOLITA homepage handwritten overlay removed on desktop, laptop and mobile.")
