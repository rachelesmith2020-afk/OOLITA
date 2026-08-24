#!/usr/bin/env python3
"""Keep the English 3D-world launch notice in natural, direct English."""
from pathlib import Path
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
PAGE = ROOT / "en/3d-world/index.html"
OLD = "That day the link opens. If you want the notice, leave your email with OOLITA."
NEW = "Leave your email with OOLITA and we’ll let you know when it opens."
FOLLOW_HREF = 'href="/en/?follow=3d#follow-oolita"'

if not PAGE.is_file():
    raise SystemExit("Missing expected page: en/3d-world/index.html")

text = PAGE.read_text(encoding="utf-8")
old_count = text.count(OLD)
new_count = text.count(NEW)

if old_count:
    text = text.replace(OLD, NEW)
    PAGE.write_text(text, encoding="utf-8")
    print(f"patched en/3d-world/index.html launch notice: {old_count} occurrence(s)")
elif new_count:
    print(f"launch notice already reviewed: {new_count} occurrence(s)")
else:
    raise SystemExit("Unexpected launch-notice wording state in en/3d-world/index.html")

text = PAGE.read_text(encoding="utf-8")
if OLD in text:
    raise SystemExit("Old launch-notice wording remains in en/3d-world/index.html")
if text.count(NEW) != 1:
    raise SystemExit("Expected exactly one approved launch notice in en/3d-world/index.html")
if FOLLOW_HREF not in text:
    raise SystemExit("3D-world Follow OOLITA href is missing or changed")

print("English 3D-world launch notice and follow href validated.")
