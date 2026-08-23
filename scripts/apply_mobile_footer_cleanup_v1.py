#!/usr/bin/env python3
"""Keep OOLITA footers readable and touch-friendly on narrow screens.

This final visual layer runs after the contemporary-art and spacing passes. It
changes only mobile footer layout: desktop presentation, content, links and
credits remain untouched.
"""
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
STYLE_ID = "oolita-mobile-footer-cleanup-v1"
STYLE = r'''<style id="oolita-mobile-footer-cleanup-v1">
@media(max-width:760px){
  body.art-restaged footer,
  body.art-restaged .pie{
    display:grid!important;
    grid-template-columns:minmax(0,1fr)!important;
    align-items:start!important;
    justify-items:start!important;
    gap:.85rem!important;
    width:100%!important;
    max-width:100%!important;
    box-sizing:border-box!important;
    padding-top:1.55rem!important;
    padding-bottom:1.8rem!important;
    line-height:1.45!important;
  }
  body.art-restaged footer *,
  body.art-restaged .pie *{
    min-width:0!important;
    max-width:100%!important;
    box-sizing:border-box!important;
  }
  body.art-restaged footer>*,
  body.art-restaged .pie>*{
    margin:0!important;
  }
  body.art-restaged footer .firma,
  body.art-restaged .pie .firma,
  body.art-restaged footer nav,
  body.art-restaged .pie nav{
    display:grid!important;
    grid-template-columns:minmax(0,1fr)!important;
    gap:.4rem!important;
    width:100%!important;
    align-items:start!important;
    justify-items:start!important;
  }
  body.art-restaged footer .rot,
  body.art-restaged .pie .rot{
    display:block!important;
    width:auto!important;
    max-width:100%!important;
    white-space:normal!important;
    overflow-wrap:anywhere!important;
    word-break:normal!important;
    line-height:1.42!important;
  }
  body.art-restaged footer a,
  body.art-restaged .pie a{
    display:flex!important;
    width:fit-content!important;
    max-width:100%!important;
    min-height:2.75rem!important;
    align-items:center!important;
    justify-content:flex-start!important;
    padding:.35rem 0!important;
    margin:0!important;
    white-space:normal!important;
    overflow-wrap:anywhere!important;
    word-break:normal!important;
    line-height:1.35!important;
  }
}
@media(max-width:420px){
  body.art-restaged footer,
  body.art-restaged .pie{
    gap:.72rem!important;
    padding-top:1.35rem!important;
    padding-bottom:1.55rem!important;
  }
  body.art-restaged footer .rot,
  body.art-restaged .pie .rot{
    letter-spacing:.08em!important;
  }
}
</style>'''

if not ROOT.is_dir():
    raise SystemExit(f"Missing built site: {ROOT}")
html_files = sorted(ROOT.rglob("*.html"))
if not html_files:
    raise SystemExit("No HTML pages found")

for target in html_files:
    html = target.read_text(encoding="utf-8")
    if f'id="{STYLE_ID}"' in html:
        continue
    if "</head>" not in html:
        raise SystemExit(f"Missing </head>: {target.relative_to(ROOT)}")
    html = html.replace("</head>", STYLE + "\n</head>", 1)
    target.write_text(html, encoding="utf-8")

for rel in ("index.html", "en/index.html"):
    target = ROOT / rel
    html = target.read_text(encoding="utf-8")
    if STYLE_ID not in html or "art-restaged" not in html:
        raise SystemExit(f"Mobile footer cleanup invariant failed: {rel}")

print(f"OOLITA mobile footer cleanup validated across {len(html_files)} HTML pages.")
