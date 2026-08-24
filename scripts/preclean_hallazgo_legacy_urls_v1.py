#!/usr/bin/env python3
"""Remove retired Canva Hallazgo URLs before the final Hallazgo gate."""
from pathlib import Path
import re
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
if not ROOT.is_dir():
    raise SystemExit(f"Missing built site: {ROOT}")

legacy = re.compile(r"https?://hallazgo\.my\.canva\.site(?:/[^\"'<>\s)]*)?", re.I)
changed = 0
for page in sorted(ROOT.rglob("*.html")):
    rel = page.relative_to(ROOT).as_posix()
    target = "/en/hallazgo-catalogue/" if rel.startswith("en/") else "/catalogo-hallazgo/"
    text = page.read_text(encoding="utf-8")
    rewritten = legacy.sub(target, text)
    if rewritten != text:
        page.write_text(rewritten, encoding="utf-8")
        changed += 1
        print(f"precleaned retired Hallazgo Canva URL: {rel}")

remaining = []
for page in sorted(ROOT.rglob("*.html")):
    if "hallazgo.my.canva.site" in page.read_text(encoding="utf-8").lower():
        remaining.append(page.relative_to(ROOT).as_posix())
if remaining:
    raise SystemExit("Legacy Hallazgo Canva host remains: " + ", ".join(remaining))
print(f"Hallazgo legacy-URL preclean passed: {changed} page(s) changed; no Canva-host stragglers.")
