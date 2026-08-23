#!/usr/bin/env python3
"""Normalize final live wording before the strict release-calendar pass."""
from __future__ import annotations

from pathlib import Path
import runpy
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
HERE = Path(__file__).resolve().parent

# A rebuilt site may begin from a live page on which later public-identity and
# reader-facing passes have already applied their final date wording. Restore
# only the intermediate forms expected by the strict release-calendar core;
# later layers re-apply the final public wording after this pass.
normalise = {
    "en/index.html": (
        (
            "Virtual castle · free to enter · opens 16 May 27 · 19:00 CEST ↗",
            "Virtual castle · free to enter · opens 16.05.27 · 19:00 CEST ↗",
        ),
        (
            "In the castle: full catalogue with a key · hardback 16 Sep 27 · public launch 19 Sep 27 ↗",
            "In the castle: full catalogue with a key · hardback planned for autumn 2027 ↗",
        ),
        (
            "In the castle: full catalogue with a key · hardback 16.09.27 · public launch 19.09.27 ↗",
            "In the castle: full catalogue with a key · hardback planned for autumn 2027 ↗",
        ),
    ),
    "index.html": (
        (
            "En el castillo: catálogo completo con clave · tapa dura 16.09.27 · presentación pública 19.09.27 ↗",
            "En el castillo: catálogo completo con clave · tapa dura prevista para otoño de 2027 ↗",
        ),
    ),
}
for rel, replacements in normalise.items():
    target = ROOT / rel
    if not target.is_file():
        continue
    text = target.read_text(encoding="utf-8")
    for old, new in replacements:
        text = text.replace(old, new)
    target.write_text(text, encoding="utf-8")

core = HERE / "apply_release_calendar_core_v1.py"
if not core.is_file():
    raise SystemExit(f"Missing release-calendar core: {core}")
old_argv = sys.argv[:]
sys.argv = [str(core), str(ROOT)]
try:
    runpy.run_path(str(core), run_name="__main__")
finally:
    sys.argv = old_argv
