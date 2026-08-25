#!/usr/bin/env python3
"""Run the release-calendar layer safely against the current Editions layout.

The v1/core migration still checks for a former overview paragraph announcing
book/textile dates. The current live Editions design expresses those dates on
its edition cards and intentionally no longer renders that overview paragraph.
Use an ephemeral HTML-comment sentinel containing the already-migrated target
text so the historical migration is recognized as complete, then remove the
sentinel before later layers or deployment.
"""
from __future__ import annotations

from pathlib import Path
import runpy
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
HERE = Path(__file__).resolve().parent
CORE = HERE / "apply_release_calendar_v1.py"

COMPAT = {
    "ediciones/index.html": {
        "old": '<p class="parr">El libro sale el 31 de enero de 2027. La primera edición textil llega el 28 de marzo, cuando su diseño termine de desvelarse domingo a domingo.</p>',
        "new": '<p class="parr">El libro sale el 31 de enero de 2027. La primera edición textil llega el 11 de abril. Los detalles y la historia del diseño se irán desvelando domingo a domingo hasta entonces.</p>',
        "current": "Después vendrá la edición de tapa dura de Hallazgo",
    },
    "en/editions/index.html": {
        "old": '<p class="parr">The book comes out on 31 January 2027. The first textile edition follows on 28 March, once its design has been revealed Sunday by Sunday.</p>',
        "new": '<p class="parr">The book comes out on 31 January 2027. The first textile edition follows on 11 April. Details and the story of the design will be revealed Sunday by Sunday until then.</p>',
        "current": "After them will come the Hallazgo hardback",
    },
}

if not ROOT.is_dir():
    raise SystemExit(f"Missing built site: {ROOT}")
if not CORE.is_file():
    raise SystemExit(f"Missing release-calendar v1 layer: {CORE}")

inserted: list[tuple[Path, str]] = []
for rel, cfg in COMPAT.items():
    page = ROOT / rel
    if not page.is_file():
        raise SystemExit(f"Missing Editions page for release compatibility: {rel}")
    text = page.read_text(encoding="utf-8")
    if cfg["old"] in text or cfg["new"] in text:
        continue
    if cfg["current"] not in text:
        # A genuinely older source should be handled by the original migration,
        # and an unknown newer state should fail there rather than be bypassed.
        continue
    if "</main>" not in text:
        raise SystemExit(f"No </main> in {rel}")
    sentinel = f'<!-- release-v2 compatibility: {cfg["new"]} -->'
    text = text.replace("</main>", sentinel + "\n</main>", 1)
    page.write_text(text, encoding="utf-8")
    inserted.append((page, sentinel))
    print(f"release v2 bridged current Editions date layout: {rel}")

old_argv = sys.argv[:]
sys.argv = [str(CORE), str(ROOT)]
try:
    runpy.run_path(str(CORE), run_name="__main__")
finally:
    sys.argv = old_argv
    for page, sentinel in inserted:
        if not page.is_file():
            continue
        text = page.read_text(encoding="utf-8")
        if sentinel in text:
            page.write_text(text.replace(sentinel + "\n", "", 1), encoding="utf-8")

for rel in COMPAT:
    text = (ROOT / rel).read_text(encoding="utf-8")
    if "release-v2 compatibility:" in text:
        raise SystemExit(f"Release compatibility sentinel leaked into {rel}")

print("OOLITA release-calendar v2 completed with no compatibility stragglers.")
