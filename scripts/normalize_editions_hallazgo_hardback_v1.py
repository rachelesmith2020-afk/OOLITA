#!/usr/bin/env python3
"""Keep the approved Hallazgo hardback sequence on the English Editions page."""
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
PAGE = ROOT / "en/editions/index.html"

OLD_FORMS = (
    "The book and T-shirt are the first two editions. After them will come field publications and small collaborations made in Cabo de Gata.",
    "The book and T-shirt are the first OOLITA editions. They begin a wider series of field publications, small textile works and collaborations rooted in Cabo de Gata.",
)
NEW = (
    "The book and T-shirt are the first two editions. After them will come the Hallazgo hardback, "
    "followed by field publications and small collaborations made in Cabo de Gata."
)

if not PAGE.is_file():
    raise SystemExit(f"Missing English Editions page: {PAGE}")

text = PAGE.read_text(encoding="utf-8")
original = text

if NEW not in text:
    for old in OLD_FORMS:
        if old in text:
            text = text.replace(old, NEW, 1)
            break
    else:
        raise SystemExit("English Editions sequence source drifted; approved paragraph was not found.")

if text.count(NEW) != 1:
    raise SystemExit("English Editions sequence validation failed: approved Hallazgo sentence must appear exactly once.")

for old in OLD_FORMS:
    if old in text:
        raise SystemExit("English Editions sequence validation failed: superseded wording remains.")

if text != original:
    PAGE.write_text(text, encoding="utf-8")
    print("English Editions sequence updated: Hallazgo hardback added.")
else:
    print("English Editions sequence already current.")
