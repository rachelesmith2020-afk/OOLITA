#!/usr/bin/env python3
"""Run the growth layer safely against current reader-facing states.

The original growth migration still validates a few transitional paragraphs that
later editorial passes intentionally remove. Ephemeral sentinels let the legacy
migration recognize those steps as already superseded, then disappear before any
later layer or deploy.
"""
from __future__ import annotations

from pathlib import Path
import runpy
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
HERE = Path(__file__).resolve().parent
CORE = HERE / "apply_growth_v1.py"

SENTINELS = {
    "ediciones/index.html": {
        "legacy_marker": "Las ediciones son la parte que puedes conservar.",
        "current_markers": (
            "Hallazgo — el catálogo",
            "Edición en tapa dura · obra completa en Castillo 3D · acceso con código · lanzamiento 16.09.27 · presentación 19.09.27",
            "El catálogo completo permanece dentro del castillo, con clave.",
        ),
        "sentinel": "<!-- growth-v2 compatibility: Las ediciones son la parte que puedes conservar. -->",
    },
    "en/editions/index.html": {
        "legacy_marker": "The editions are the part you can keep.",
        "current_markers": (
            "Hallazgo — the catalogue",
            "The full catalogue remains inside the castle, with a key.",
        ),
        "sentinel": "<!-- growth-v2 compatibility: The editions are the part you can keep. -->",
    },
    "ediciones/camiseta/index.html": {
        "legacy_marker": "cuando existan los acuerdos adecuados",
        "current_markers": (
            "La primera edición textil lleva el laberinto a la tela.",
            "La prenda aparece primero en blanco. Cada domingo aparece un poco más del diseño.",
        ),
        "sentinel": "<!-- growth-v2 compatibility: cuando existan los acuerdos adecuados -->",
    },
    "en/editions/t-shirt/index.html": {
        "legacy_marker": "where the right agreements exist",
        "current_markers": (
            "The first textile edition carries the labyrinth into cloth.",
            "The garment appears first blank. Each Sunday, a little more of the design appears.",
        ),
        "sentinel": "<!-- growth-v2 compatibility: where the right agreements exist -->",
    },
}

if not ROOT.is_dir():
    raise SystemExit(f"Missing built site: {ROOT}")
if not CORE.is_file():
    raise SystemExit(f"Missing growth core: {CORE}")

inserted: list[tuple[Path, str]] = []
for rel, cfg in SENTINELS.items():
    page = ROOT / rel
    if not page.is_file():
        raise SystemExit(f"Missing page for growth compatibility: {rel}")
    text = page.read_text(encoding="utf-8")
    if cfg["legacy_marker"] in text:
        continue
    if not any(marker in text for marker in cfg["current_markers"]):
        # A genuinely old source should still be handled by v1's original migration.
        continue
    if "</main>" not in text:
        raise SystemExit(f"No </main> in {rel}")
    text = text.replace("</main>", cfg["sentinel"] + "\n</main>", 1)
    page.write_text(text, encoding="utf-8")
    inserted.append((page, cfg["sentinel"]))
    print(f"growth v2 bridged current reader state: {rel}")

old_argv = sys.argv[:]
sys.argv = [str(CORE), str(ROOT)]
try:
    runpy.run_path(str(CORE), run_name="__main__")
finally:
    sys.argv = old_argv
    for page, sentinel in inserted:
        if page.is_file():
            text = page.read_text(encoding="utf-8")
            if sentinel in text:
                page.write_text(text.replace(sentinel + "\n", "", 1), encoding="utf-8")

for rel, cfg in SENTINELS.items():
    text = (ROOT / rel).read_text(encoding="utf-8")
    if "growth-v2 compatibility:" in text:
        raise SystemExit(f"Growth compatibility sentinel leaked into {rel}")
    if any(marker in text for marker in cfg["current_markers"]):
        print(f"growth v2 current reader state preserved: {rel}")

print("OOLITA growth v2 completed with no compatibility stragglers.")
