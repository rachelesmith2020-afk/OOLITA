#!/usr/bin/env python3
"""Run the reviewed OOLITA wording patch without brittle occurrence counts."""
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
SOURCE = HERE.joinpath("apply_wording.py").read_text(encoding="utf-8")
ROOT_ARG = sys.argv[1] if len(sys.argv) > 1 else "site"

start = SOURCE.index("def r(")
end = SOURCE.index("\n# Homepage")
replacement = r"""def r(path, old, new, expected=1):
    p = ROOT / path
    if not p.is_file():
        raise SystemExit(f"Missing expected page: {path}")
    text = p.read_text(encoding="utf-8")
    old_count = text.count(old)
    new_count = text.count(new)
    superseding = None
    if old == "Caminar un laberinto sin ir hasta él.":
        superseding = "El camino, domingo a domingo."
    elif old == "Walk a labyrinth without going there.":
        superseding = "The path, one Sunday at a time."
    elif old.startswith("¿Te aviso cuando se abra la puerta?"):
        superseding = '<a href="/#seguir-oolita">Sigue OOLITA</a> para recibir un aviso cuando se abra el mundo.'
    elif old.startswith("Want to be told when the door opens?"):
        superseding = '<a href="/en/#follow-oolita">Follow OOLITA</a> to be notified when the world opens.'
    elif old.startswith("Está hecho para quien no puede llegar hasta Almería"):
        superseding = "No todo el mundo puede llegar a Almería. A veces es la distancia. A veces el dinero. A veces el cuerpo."
    elif old.startswith("It exists for anyone who cannot get to Almería"):
        superseding = "Not everyone can get to Almería. Sometimes it is distance. Sometimes money. Sometimes the body."
    elif old == "Los tres dicen lo mismo de tres maneras.":
        superseding = "Piedra. Papel. Código. Tres materiales, un camino."
    elif old == "The three say the same thing three ways.":
        superseding = "Stone. Paper. Code. Three materials, one path."
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
"""

patched_source = SOURCE[:start] + replacement + SOURCE[end:]
sys.argv = [str(HERE / "apply_wording.py"), ROOT_ARG]
exec(compile(patched_source, str(HERE / "apply_wording.py"), "exec"))

# Homepage — English: keep the material description deliberately plain.
homepage = Path(ROOT_ARG) / "en/index.html"
if not homepage.is_file():
    raise SystemExit("Missing expected homepage: en/index.html")
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

# Homepage wording consistency.
def replace_homepage_copy(rel_path, old, new, superseding=None):
    page = root / rel_path
    if not page.is_file():
        raise SystemExit(f"Missing expected homepage: {rel_path}")
    text = page.read_text(encoding="utf-8")
    old_count = text.count(old)
    new_count = text.count(new)
    if old_count > 0:
        page.write_text(text.replace(old, new), encoding="utf-8")
        print(f"patched {rel_path}: {old_count} occurrence(s): {old!r} -> {new!r}")
    elif new_count > 0:
        print(f"already reviewed {rel_path}: {new_count} occurrence(s): {new!r}")
    elif superseding and superseding in text:
        print(f"already superseded {rel_path}: {superseding[:52]!r}")
    else:
        raise SystemExit(
            f"Unexpected homepage wording in {rel_path}: "
            f"found neither {old!r} nor {new!r}"
        )

replace_homepage_copy(
    "en/index.html",
    "No sign, no name.",
    "No sign marks it.",
    "OOLITA begins with a three-metre classical labyrinth, laid by hand from stone at Los Escullos, on land that was seabed a hundred thousand years ago.",
)
replace_homepage_copy(
    "en/index.html",
    "There is no sign, no name, nothing marking it on the ground:",
    "Nothing marks it on the ground:",
)
replace_homepage_copy(
    "index.html",
    "No lleva cartel, ni nombre, ni nada que lo señale sobre el terreno:",
    "Nada lo señala sobre el terreno:",
)

# Final approved English homepage opening. Remove the signage sentence and use
# "land" rather than locating the labyrinth itself on a fossil dune.
replace_homepage_copy(
    "en/index.html",
    "OOLITA begins with a three-metre classical labyrinth, laid by hand from stone at Los Escullos, on a fossil dune that was seabed a hundred thousand years ago. No sign marks it.",
    "OOLITA begins with a three-metre classical labyrinth, laid by hand from stone at Los Escullos, on land that was seabed a hundred thousand years ago.",
)

# Final approved English Cabo de Gata homepage wording: include the people who
# live as well as work there, and use the agreed land-care phrasing.
replace_homepage_copy(
    "en/index.html",
    "The point is not to bring more people to one labyrinth. It is to look at Cabo de Gata more slowly, learn from people who work here and leave the place as it was.",
    "The point is not to bring more people to one labyrinth. It is to look at Cabo de Gata more slowly, learn from the people who live and work here, and leave the land as you found it.",
)

# 22 Sundays homepage heading: keep it concrete and tied to the weekly series.
replace_homepage_copy(
    "en/index.html",
    "The same path, made of light.",
    "The path, one Sunday at a time.",
)
replace_homepage_copy(
    "index.html",
    "El mismo camino, hecho de luz.",
    "El camino, domingo a domingo.",
)

# Work with OOLITA — English: use the collective project voice.
replace_homepage_copy(
    "en/work-with-oolita/index.html",
    "Tell me what you have in mind.",
    "Tell us what you have in mind.",
)

# SEO consistency: if the old geological wording is present anywhere in the
# English homepage <head> (description, Open Graph, Twitter or JSON-LD), keep
# the metadata aligned with the approved visible copy without rewriting any
# unrelated metadata.
seo_page = root / "en/index.html"
seo_text = seo_page.read_text(encoding="utf-8")
head_end = seo_text.lower().find("</head>")
if head_end < 0:
    raise SystemExit("Missing </head> in en/index.html")
head_end += len("</head>")
seo_head = seo_text[:head_end]
seo_tail = seo_text[head_end:]
seo_old = "on a fossil dune that was seabed a hundred thousand years ago"
seo_new = "on land that was seabed a hundred thousand years ago"
seo_count = seo_head.count(seo_old)
if seo_count:
    seo_page.write_text(seo_head.replace(seo_old, seo_new) + seo_tail, encoding="utf-8")
    print(f"patched en/index.html SEO head: {seo_count} occurrence(s): {seo_old!r} -> {seo_new!r}")
else:
    print("en/index.html SEO head already contains no old fossil-dune placement wording")

# Production deployment trigger: 2026-08-24 14:15 Europe/London — global header year 2027.
# Compatibility trigger: final OOLITA book-voice copy, 2026-08-24.
# Production deployment trigger: labyrinth name consistency, 2026-08-24.
# Production deployment trigger: homepage land wording + SEO consistency, 2026-08-24.
# Production deployment trigger: Cabo de Gata live-and-work wording, 2026-08-24.
# Production deployment trigger: 22 Sundays homepage heading, 2026-08-24.
# Production deployment trigger: Work with OOLITA collective voice, 2026-08-24.
