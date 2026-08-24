#!/usr/bin/env python3
"""Replace the awkward English 3D-world launch notice on the homepage."""
from pathlib import Path
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
PAGE = ROOT / "en/index.html"
OLD = "That day the link opens. If you want the notice, leave your email with OOLITA."
NEW = "Leave your email with OOLITA and we’ll let you know when it opens."

if not PAGE.is_file():
    raise SystemExit("Missing expected homepage: en/index.html")

text = PAGE.read_text(encoding="utf-8")
old_count = text.count(OLD)
new_count = text.count(NEW)

if old_count:
    PAGE.write_text(text.replace(OLD, NEW), encoding="utf-8")
    print(f"patched en/index.html launch notice: {old_count} occurrence(s)")
elif new_count:
    print(f"launch notice already reviewed: {new_count} occurrence(s)")
else:
    raise SystemExit("Unexpected launch-notice wording state in en/index.html")
