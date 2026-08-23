#!/usr/bin/env python3
"""Run the complete search/identity/reader pipeline, then add the genuine book excerpt."""
from __future__ import annotations

from pathlib import Path
import runpy
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
HERE = Path(__file__).resolve().parent


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
