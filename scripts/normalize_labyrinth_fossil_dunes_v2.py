#!/usr/bin/env python3
"""Final factual/SEO gate with a narrow English location-phrase assertion.

The v1 gate already rejects actual wrong labyrinth-on-fossil-dune claims across
all HTML and scopes the San Felipe exception to battery context. This wrapper
retains those checks but limits the additional exact-wording assertion to the
principal English location pages, so geology/story pages are not rejected merely
for mentioning both the labyrinth and fossil dunes.
"""
from pathlib import Path
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
HERE = Path(__file__).resolve().parent
v1 = HERE / "normalize_labyrinth_fossil_dunes_v1.py"
source = v1.read_text(encoding="utf-8")

start_marker = "# Every corrected English page that discusses the labyrinth's fossil-dune"
end_marker = "# Mark corrected public routes fresh for search engines and the existing"
start = source.find(start_marker)
end = source.find(end_marker, start)
if start < 0 or end < 0:
    raise SystemExit("Could not locate v1 English exact-wording assertion block")

narrow_check = '''# Require the approved exact phrase only on principal English location pages.
# The BAD_LOCATION_PATTERNS gate above already rejects actual wrong location
# claims everywhere, including Sunday/geology pages.
ENGLISH_LOCATION_PAGES = {
    "en/index.html",
    "en/labyrinth/index.html",
    "en/cabo-de-gata/index.html",
    "en/3d-world/index.html",
}
for rel in sorted(changed & ENGLISH_LOCATION_PAGES):
    text = (ROOT / rel).read_text(encoding="utf-8").lower()
    if "beside the fossil dunes" not in text:
        raise SystemExit(
            f"English location wording lacks approved 'beside the fossil dunes' phrase: {rel}"
        )

'''
source = source[:start] + narrow_check + source[end:]
namespace = {"__name__": "__main__", "__file__": str(v1)}
exec(compile(source, str(v1), "exec"), namespace)

# Principal-page assertions remain explicit after the complete v1 gate.
for rel, phrase in (
    ("en/index.html", "beside the fossil dunes"),
    ("en/labyrinth/index.html", "beside the fossil dunes"),
    ("index.html", "junto a las dunas fósiles"),
    ("laberinto/index.html", "junto a las dunas fósiles"),
):
    text = (ROOT / rel).read_text(encoding="utf-8").lower()
    if phrase not in text:
        raise SystemExit(f"Approved labyrinth location wording missing from {rel}")

print("OOLITA fossil-dunes v2 final gate passed.")
