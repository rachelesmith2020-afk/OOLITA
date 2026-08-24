#!/usr/bin/env python3
"""Corrected final gate: preserve the labyrinth beside the fossil dunes while
restoring the Batería de San Felipe exception only in its own context."""
from pathlib import Path
import re
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
HERE = Path(__file__).resolve().parent
v1 = HERE / "normalize_labyrinth_fossil_dunes_v1.py"
source = v1.read_text(encoding="utf-8")

# v1's only deployment-breaking defect is that the San Felipe restoration loop
# applies globally. Disable that loop while retaining all of v1's factual, SEO,
# sitemap and href checks.
needle = "        for old, new in BATTERY_REPLACEMENTS:\n            text = text.replace(old, new)\n"
replacement = "        # San Felipe restoration is context-scoped by v2 after v1 completes.\n        pass\n"
if needle not in source:
    raise SystemExit("Could not locate v1 battery-restoration loop")
source = source.replace(needle, replacement, 1)
namespace = {"__name__": "__main__", "__file__": str(v1)}
exec(compile(source, str(v1), "exec"), namespace)

# Restore only the historically correct nearby battery statement. Never apply a
# bare global replacement, because that was what moved the labyrinth back onto
# a fossil dune.
for path in ROOT.rglob("*.html"):
    text = path.read_text(encoding="utf-8")
    before = text
    text = re.sub(
        r"(Bater[ií]a de San Felipe.{0,320}?)(?:stands on land beside the fossil dunes|stands beside the same fossil dunes|stands on the same fossil dunes)",
        r"\1stands on a fossil dune",
        text,
        flags=re.I | re.S,
    )
    text = re.sub(
        r"(Bater[ií]a de San Felipe.{0,320}?)(?:se levanta en terreno junto a las dunas fósiles|se levanta junto a las mismas dunas fósiles|se levanta sobre las mismas dunas fósiles)",
        r"\1se levanta sobre una duna fósil",
        text,
        flags=re.I | re.S,
    )
    if text != before:
        path.write_text(text, encoding="utf-8")
        print(f"San Felipe fossil-dune exception restored: {path.relative_to(ROOT)}")

# Final principal-page assertions after the exception restoration.
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
