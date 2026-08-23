#!/usr/bin/env python3
"""Pre-normalize mirrored shell copy, then run OOLITA public identity v2."""
from pathlib import Path
import runpy
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
HERE = Path(__file__).resolve().parent

# The production 404 is mirrored from the homepage and can carry stale
# Hallazgo release wording before the final identity validator runs.
for rel in ("404.html", "404/index.html"):
    path = ROOT / rel
    if not path.is_file():
        continue
    text = path.read_text(encoding="utf-8")
    text = text.replace(
        "tapa dura prevista para otoño de 2027",
        "tapa dura 16.09.27 · presentación pública 19.09.27",
    )
    text = text.replace(
        "hardback planned for autumn 2027",
        "hardback 16.09.27 · public launch 19.09.27",
    )
    path.write_text(text, encoding="utf-8")

script = HERE / "apply_public_identity_v2.py"
old_argv = sys.argv[:]
sys.argv = [str(script), str(ROOT)]
try:
    runpy.run_path(str(script), run_name="__main__")
finally:
    sys.argv = old_argv
