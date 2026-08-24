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

# Hallazgo is already visible from the OOLITA directory. Give the catalogue the
# weight of a publication without turning the homepage into a sales page. Keep
# the reading-room key and the confirmed September dates in view.
final_hallazgo = {
    "en/index.html": (
        ("<span class=\"nom\">Catalogue</span>", "<span class=\"nom\">Hallazgo — the catalogue</span>"),
        (
            "In the castle: full catalogue with a key · hardback planned for autumn 2027 ↗",
            "A hardback publication bringing together the complete body of work · full catalogue in the castle with a key · 16 Sep 27 · public launch 19 Sep 27 ↗",
        ),
    ),
    "index.html": (
        ("<span class=\"nom\">Catálogo</span>", "<span class=\"nom\">Hallazgo — el catálogo</span>"),
        (
            "En el castillo: catálogo completo con clave · tapa dura prevista para otoño de 2027 ↗",
            "Una edición en tapa dura que reúne el cuerpo completo de la obra · catálogo completo en el castillo con clave · 16.09.27 · presentación pública 19.09.27 ↗",
        ),
    ),
}
for rel, replacements in final_hallazgo.items():
    target = ROOT / rel
    text = target.read_text(encoding="utf-8")
    for old, new in replacements:
        if old in text:
            text = text.replace(old, new, 1)
        elif new not in text:
            raise SystemExit(f"Expected Hallazgo catalogue wording missing in {rel}: {old!r}")
    target.write_text(text, encoding="utf-8")

required_final = {
    "en/index.html": (
        "Hallazgo — the catalogue",
        "A hardback publication bringing together the complete body of work",
        "full catalogue in the castle with a key",
        "16 Sep 27",
        "public launch 19 Sep 27",
    ),
    "index.html": (
        "Hallazgo — el catálogo",
        "Una edición en tapa dura que reúne el cuerpo completo de la obra",
        "catálogo completo en el castillo con clave",
        "16.09.27",
        "presentación pública 19.09.27",
    ),
}
for rel, needles in required_final.items():
    text = (ROOT / rel).read_text(encoding="utf-8")
    for needle in needles:
        if needle not in text:
            raise SystemExit(f"Hallazgo catalogue validation failed in {rel}: {needle!r}")

print("Hallazgo catalogue publication wording validated in Spanish and English.")
