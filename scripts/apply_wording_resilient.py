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

# Homepage — English: keep the material description deliberately plain.
homepage = Path(ROOT_ARG) / "en/index.html"
if not homepage.is_file():
    raise SystemExit("Missing expected page: en/index.html")
text = homepage.read_text(encoding="utf-8")
old = "from loose calcarenite"
new = "from stone"
old_count = text.count(old)
new_count = text.count(new)
if old_count > 0:
    homepage.write_text(text.replace(old, new), encoding="utf-8")
    print(f"patched en/index.html: {old_count} occurrence(s): {old!r} -> {new!r}")
elif new_count > 0:
    print(f"already reviewed en/index.html: {new_count} occurrence(s): {new!r}")
else:
    raise SystemExit(
        f"Unexpected homepage material wording: found neither {old!r} nor {new!r}"
    )

# Site header — show only the launch year. Mobile and desktop share the same
# markup, so changing the header source applies to both layouts. Apply this to
# every Spanish and English HTML page that carries the global header, while
# leaving any date ranges in page content untouched.
root = Path(ROOT_ARG)
old_years = ("· 2026–2027", "· 2026—2027", "· 2026-2027")
patched_headers = 0
reviewed_headers = 0
for page in sorted(root.rglob("*.html")):
    text = page.read_text(encoding="utf-8")
    boundaries = [pos for token in ("<main", "<h1", "<article") if (pos := text.find(token)) >= 0]
    header_end = min(boundaries) if boundaries else min(len(text), 12000)
    head = text[:header_end]
    tail = text[header_end:]

    changed = False
    for old_year in old_years:
        if old_year in head:
            head = head.replace(old_year, "· 2027", 1)
            changed = True
            break

    rel = page.relative_to(root)
    if changed:
        page.write_text(head + tail, encoding="utf-8")
        patched_headers += 1
        print(f"patched {rel}: site header year -> 2027")
    elif "· 2027" in head:
        reviewed_headers += 1
        print(f"already reviewed {rel}: site header year is 2027")

if patched_headers + reviewed_headers < 2:
    raise SystemExit("Global Spanish/English header year was not found on enough pages")

print(
    f"site header year verified: {patched_headers} patched, "
    f"{reviewed_headers} already 2027"
)

# Propagation trigger: 2026-08-24 14:04 Europe/London — global header year 2027.
