#!/usr/bin/env python3
"""Final factual/SEO gate for OOLITA's labyrinth and fossil-dune wording.

The current v1 gate owns the comprehensive corrections and straggler checks:
- the labyrinth is on land beside the fossil dunes;
- the named Batería de San Felipe may stand on a fossil dune;
- calcarenite shorthand is removed in favour of loose stones;
- malformed singular/plural variants and wrong location claims fail closed;
- dedicated geology explainers remain free to discuss fossil dunes geologically.

This v2 entry point runs that current gate unchanged, then adds four explicit
principal-page assertions. It deliberately does not rewrite v1's source code or
depend on historical comment markers inside it.
"""
from pathlib import Path
import runpy
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
HERE = Path(__file__).resolve().parent
v1 = HERE / "normalize_labyrinth_fossil_dunes_v1.py"

if not ROOT.is_dir():
    raise SystemExit(f"Missing built site: {ROOT}")
if not v1.is_file():
    raise SystemExit(f"Missing v1 fossil-dune gate: {v1}")

# Preserve the caller's site argument while executing the maintained v1 gate as
# its own __main__ program. No source rewriting: the actual current validator is
# what is tested and deployed.
original_argv = sys.argv[:]
try:
    sys.argv = [str(v1), str(ROOT)]
    runpy.run_path(str(v1), run_name="__main__")
finally:
    sys.argv = original_argv

# Principal-page assertions remain explicit after the complete v1 gate.
for rel, phrase in (
    ("en/index.html", "beside the fossil dunes"),
    ("en/labyrinth/index.html", "beside the fossil dunes"),
    ("index.html", "junto a las dunas fósiles"),
    ("laberinto/index.html", "junto a las dunas fósiles"),
):
    path = ROOT / rel
    if not path.is_file():
        raise SystemExit(f"Missing principal location page: {rel}")
    text = path.read_text(encoding="utf-8").lower()
    if phrase not in text:
        raise SystemExit(f"Approved labyrinth location wording missing from {rel}: {phrase}")

print("OOLITA fossil-dunes v2 final gate passed.")
