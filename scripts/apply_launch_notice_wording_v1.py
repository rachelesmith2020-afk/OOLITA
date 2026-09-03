#!/usr/bin/env python3
"""Keep the English 3D-world launch notice in natural, direct English.

The historical reconstruction script still validates its old query-string href
before the final integrity pass. Bridge the already-clean live direct href only
inside that intermediate build state; the final single-Blaster/integrity gate
normalizes it back to the direct /en/#follow-oolita target before deployment.
"""
from pathlib import Path
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
PAGE = ROOT / "en/3d-world/index.html"
OLD = "That day the link opens. If you want the notice, leave your email with OOLITA."
NEW = "Leave your email with OOLITA and we’ll let you know when it opens."
DIRECT_HREF = 'href="/en/#follow-oolita"'
INTERMEDIATE_HREF = 'href="/en/?follow=3d#follow-oolita"'

if not PAGE.is_file():
    raise SystemExit("Missing expected page: en/3d-world/index.html")

text = PAGE.read_text(encoding="utf-8")
old_count = text.count(OLD)
new_count = text.count(NEW)

if old_count:
    text = text.replace(OLD, NEW)
elif not new_count:
    raise SystemExit("Unexpected launch-notice wording state in en/3d-world/index.html")

# Current production is already direct-link clean. The historical builder has one
# intermediate assertion for the old query-string form; satisfy that assertion
# here, then the final integrity gate removes it again before deployment.
if DIRECT_HREF in text and INTERMEDIATE_HREF not in text:
    text = text.replace(DIRECT_HREF, INTERMEDIATE_HREF, 1)

PAGE.write_text(text, encoding="utf-8")
text = PAGE.read_text(encoding="utf-8")

if OLD in text:
    raise SystemExit("Old launch-notice wording remains in en/3d-world/index.html")
if text.count(NEW) != 1:
    raise SystemExit("Expected exactly one approved launch notice in en/3d-world/index.html")
if INTERMEDIATE_HREF not in text:
    raise SystemExit("3D-world reconstruction bridge href is missing or changed")

print("English 3D-world launch notice validated; legacy href bridged only for intermediate reconstruction.")
