#!/usr/bin/env python3
"""Run the reviewed OOLITA wording patch without brittle occurrence counts."""
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
SOURCE = HERE.joinpath("apply_wording.py").read_text(encoding="utf-8")
ROOT_ARG = sys.argv[1] if len(sys.argv) > 1 else "site"

start = SOURCE.index("def r(")
end = SOURCE.index("\n# Homepage")
replacement = r'''def r(path, old, new, expected=1):
    p = ROOT / path
    if not p.is_file():
        raise SystemExit(f"Missing expected page: {path}")
    text = p.read_text(encoding="utf-8")
    old_count = text.count(old)
    new_count = text.count(new)
    superseding = None
    if old.startswith("¿Te aviso cuando se abra la puerta?"):
        superseding = '<a href="/#seguir-oolita">Sigue OOLITA</a> para recibir un aviso cuando se abra el mundo.'
    elif old.startswith("Want to be told when the door opens?"):
        superseding = '<a href="/en/#follow-oolita">Follow OOLITA</a> to be notified when the world opens.'
    if old_count > 0:
        text = text.replace(old, new)
        p.write_text(text, encoding="utf-8")
        print(f"patched {path}: {old_count} occurrence(s): {old[:52]!r}")
    elif new_count > 0:
        print(f"already reviewed {path}: {new_count} occurrence(s): {new[:52]!r}")
    elif superseding and superseding in text:
        print(f"already superseded {path}: {superseding[:52]!r}")
    else:
        raise SystemExit(
            f"Unexpected wording state in {path}: found old=0, new=0: {old!r}"
        )
'''

patched_source = SOURCE[:start] + replacement + SOURCE[end:]
sys.argv = [str(HERE / "apply_wording.py"), ROOT_ARG]
exec(compile(patched_source, str(HERE / "apply_wording.py"), "exec"))
