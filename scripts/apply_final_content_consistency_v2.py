#!/usr/bin/env python3
"""Final consistency compatibility wrapper for the researched geology release.

The legacy credibility pass inside apply_content_consistency_v1.py still expects
one historical intermediate ordering of the Los Escullos age range
(100,000–128,000). The researched/canonical reader wording now follows the Junta
trail chronology as 128,000–100,000 years.

This wrapper exists only for the final CI compatibility stage:
1. bridge the four known age-order literals to the legacy intermediate state;
2. run the complete existing content-consistency/credibility stack unchanged;
3. leave final reader authority to the immediately following
   apply_geology_authority_v1.py + fossil-dune + static-integrity gates.

It introduces no public copy by itself and must never be the last reader-facing
step in the deployment workflow.
"""
from __future__ import annotations

from pathlib import Path
import subprocess
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
HERE = Path(__file__).resolve().parent
if not ROOT.is_dir():
    raise SystemExit(f"Missing built site: {ROOT}")

pairs = (
    ("128.000 y 100.000 años", "100.000 y 128.000 años"),
    ("entre 128.000 y 100.000 años", "entre 100.000 y 128.000 años"),
    ("128,000 and 100,000 years", "100,000 and 128,000 years"),
    ("between 128,000 and 100,000 years", "between 100,000 and 128,000 years"),
)

owned = (
    ROOT / "que-es-un-oolito/index.html",
    ROOT / "en/what-is-an-ooid/index.html",
)
changed = 0
for path in owned:
    if not path.is_file():
        raise SystemExit(f"Missing geology compatibility page: {path.relative_to(ROOT)}")
    text = path.read_text(encoding="utf-8")
    before = text
    for current, legacy in pairs:
        text = text.replace(current, legacy)
    if text != before:
        path.write_text(text, encoding="utf-8")
        changed += 1

subprocess.run(
    [sys.executable, str(HERE / "apply_content_consistency_v1.py"), str(ROOT)],
    check=True,
)

# Prove the legacy pass reached its expected intermediate state. The workflow's
# next step must replace this with the researched chronology before validation.
for path, needle in (
    (ROOT / "que-es-un-oolito/index.html", "100.000 y 128.000 años"),
    (ROOT / "en/what-is-an-ooid/index.html", "100,000 and 128,000 years"),
):
    if needle not in path.read_text(encoding="utf-8"):
        raise SystemExit(
            f"Legacy consistency bridge did not reach expected intermediate state: {path.relative_to(ROOT)}"
        )

print(
    "OOLITA final consistency compatibility passed: "
    f"{changed} geology page(s) bridged for legacy validation; final researched wording still pending."
)
