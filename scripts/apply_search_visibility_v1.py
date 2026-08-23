#!/usr/bin/env python3
"""Run the complete search/identity/reader pipeline, then add the genuine book excerpt."""
from __future__ import annotations

from pathlib import Path
import runpy
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
HERE = Path(__file__).resolve().parent


# A deployment rebuild starts from the current live origin. The later
# reader-facing pass may therefore already have converted English display dates
# to month-name forms. The public-identity layer inside the search core validates
# its canonical dotted intermediate forms, so restore only those display strings
# before running the core. The reader layer converts them back afterwards.
ENGLISH_DATE_NORMALISATION = (
    ("3 Jan 2027", "03.01.2027"),
    ("3 Jan 27", "03.01.27"),
    ("9 Aug 26", "09.08.26"),
    ("31 Jan 27", "31.01.27"),
    ("16 May 27", "16.05.27"),
    ("16 Sep 27", "16.09.27"),
    ("19 Sep 27", "19.09.27"),
    ("11 Apr 27", "11.04.27"),
)
for rel in ("en/index.html", "en/editions/book/index.html"):
    target = ROOT / rel
    if not target.is_file():
        continue
    text = target.read_text(encoding="utf-8")
    for reader_form, canonical_form in ENGLISH_DATE_NORMALISATION:
        text = text.replace(reader_form, canonical_form)
    target.write_text(text, encoding="utf-8")


def run_layer(filename: str) -> None:
    script = HERE / filename
    if not script.is_file():
        raise SystemExit(f"Missing deployment layer: {script}")
    old_argv = sys.argv[:]
    sys.argv = [str(script), str(ROOT)]
    try:
        runpy.run_path(str(script), run_name="__main__")
    finally:
        sys.argv = old_argv


run_layer("apply_search_visibility_core_v1.py")
run_layer("apply_book_excerpt_v1.py")
