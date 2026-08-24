#!/usr/bin/env python3
"""Pre-sanitize legacy Hallazgo URLs, then run the strict v1 access gate.

The live-origin rebuild can contain old Canva URLs outside href attributes (for
example metadata or structured data). v1 correctly rewrites reader-facing hrefs
but then rejects any remaining legacy host string. This wrapper converts every
remaining absolute Canva catalogue URL to the matching first-party OOLITA
catalogue URL before v1 performs its copy, SEO, sitemap and no-404 validation.
"""
from __future__ import annotations

from pathlib import Path
import re
import runpy
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
HERE = Path(__file__).resolve().parent
V1 = HERE / "normalize_hallazgo_3d_castle_access_v1.py"
BASE = "https://oolita.es"
LEGACY_URL_RE = re.compile(
    r'https?://hallazgo\.my\.canva\.site[^\s"\'<>]*',
    flags=re.I,
)

if not ROOT.is_dir():
    raise SystemExit(f"Missing built site: {ROOT}")
if not V1.is_file():
    raise SystemExit(f"Missing Hallazgo v1 gate: {V1}")

changed = 0
for html in sorted(ROOT.rglob("*.html")):
    rel = html.relative_to(ROOT).as_posix()
    target = (
        BASE + "/en/hallazgo-catalogue/"
        if rel.startswith("en/")
        else BASE + "/catalogo-hallazgo/"
    )
    text = html.read_text(encoding="utf-8")
    rewritten = LEGACY_URL_RE.sub(target, text)
    if rewritten != text:
        html.write_text(rewritten, encoding="utf-8")
        changed += 1
        print(f"Hallazgo legacy absolute URL pre-sanitized: {rel}")

old_argv = sys.argv[:]
sys.argv = [str(V1), str(ROOT)]
try:
    runpy.run_path(str(V1), run_name="__main__")
finally:
    sys.argv = old_argv

print(f"Hallazgo v2 access gate passed after pre-sanitizing {changed} page(s).")
