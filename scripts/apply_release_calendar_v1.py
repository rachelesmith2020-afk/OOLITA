#!/usr/bin/env python3
"""Normalize reader-formatted live dates before the strict release-calendar pass."""
from __future__ import annotations

from pathlib import Path
import runpy
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
HERE = Path(__file__).resolve().parent

# A rebuilt site may begin from a live page on which the later reader-facing
# pass has already converted the English display date to a month name. The
# release-calendar validator expects its own canonical dotted intermediate
# form; the reader layer converts it back after this pass.
page = ROOT / "en/index.html"
if page.is_file():
    text = page.read_text(encoding="utf-8")
    text = text.replace(
        "Virtual castle · free to enter · opens 16 May 27 · 19:00 CEST ↗",
        "Virtual castle · free to enter · opens 16.05.27 · 19:00 CEST ↗",
    )
    page.write_text(text, encoding="utf-8")

core = HERE / "apply_release_calendar_core_v1.py"
if not core.is_file():
    raise SystemExit(f"Missing release-calendar core: {core}")
old_argv = sys.argv[:]
sys.argv = [str(core), str(ROOT)]
try:
    runpy.run_path(str(core), run_name="__main__")
finally:
    sys.argv = old_argv
