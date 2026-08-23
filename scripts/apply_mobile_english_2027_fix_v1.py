#!/usr/bin/env python3
"""Prevent the mobile English homepage rule from crossing the 3 Jan 2027 date."""
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
target = ROOT / "en" / "index.html"
if not target.is_file():
    raise SystemExit(f"Missing English homepage: {target}")

html = target.read_text(encoding="utf-8")
STYLE_ID = "oolita-mobile-2027-fix-v1"
STYLE = '''<style id="oolita-mobile-2027-fix-v1">
@media (max-width:760px){
  body.art-home .mobile-2027-clear{
    display:inline-block!important;
    position:relative!important;
    z-index:20!important;
    text-decoration:none!important;
    background:var(--art-paper,#F1E7D4)!important;
    padding-inline:.06em!important;
    margin-inline:-.06em!important;
  }
  body.art-home .mobile-2027-clear::before,
  body.art-home .mobile-2027-clear::after{
    content:none!important;
    display:none!important;
  }
}
</style>'''

# The affected date is reader-facing copy on the English homepage. Turning it
# into an atomic inline box prevents inherited/decorative rules from painting
# through the year on narrow screens while leaving desktop layout unchanged.
if 'class="mobile-2027-clear"' not in html:
    if "3 Jan 2027" not in html:
        raise SystemExit("Could not find the English homepage date: 3 Jan 2027")
    html = html.replace("3 Jan 2027", '3 Jan <span class="mobile-2027-clear">2027</span>', 1)

if f'id="{STYLE_ID}"' not in html:
    if "</head>" not in html:
        raise SystemExit("English homepage has no </head>")
    html = html.replace("</head>", STYLE + "\n</head>", 1)

target.write_text(html, encoding="utf-8")

final = target.read_text(encoding="utf-8")
for needle in (STYLE_ID, 'class="mobile-2027-clear">2027</span>'):
    if needle not in final:
        raise SystemExit(f"Mobile 2027 fix invariant missing: {needle}")
print("OOLITA mobile English homepage 2027 line fix validated successfully.")
