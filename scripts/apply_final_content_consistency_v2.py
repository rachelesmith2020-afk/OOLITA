#!/usr/bin/env python3
"""Final consistency compatibility wrapper for the researched release.

The legacy credibility pass inside apply_content_consistency_v1.py still expects
historical intermediate wording in two narrow places:
- the Los Escullos age range ordered as 100,000–128,000;
- a pre-edit Spanish cathedral-labyrinth timing sentence.

The researched/final reader wording is restored by the immediately following
geology and final Spanish editorial gates. This wrapper exists only for CI
compatibility and must never be the last reader-facing step.
"""
from __future__ import annotations

from pathlib import Path
import re
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
HERE = Path(__file__).resolve().parent
if not ROOT.is_dir():
    raise SystemExit(f"Missing built site: {ROOT}")

# Geology chronology compatibility.
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

# Spanish literary compatibility. The legacy credibility module must see its
# historical *source* paragraph so that it can perform and validate its own edit.
# A simple raw string replacement is insufficient because the same answer can
# also occur earlier in JSON-LD; normalise the visible FAQ paragraph explicitly.
labyrinth = ROOT / "que-es-un-laberinto/index.html"
if not labyrinth.is_file():
    raise SystemExit("Missing Spanish labyrinth compatibility page")
lab_text = labyrinth.read_text(encoding="utf-8")
historical_timing = (
    "Depende del tamaño. Un laberinto de tres metros se camina en unos pocos minutos; "
    "uno de catedral, de once o doce metros, puede llevar media hora si se va despacio."
)
legacy_timing = (
    "Depende del tamaño y del ritmo. Un laberinto de tres metros se puede recorrer "
    "en pocos minutos; uno de catedral, de once o doce metros, lleva más tiempo."
)
approved_timing = (
    "Depende del tamaño y del ritmo. Un laberinto de tres metros se puede recorrer "
    "en pocos minutos; un laberinto catedralicio, de once o doce metros, lleva más tiempo."
)

paragraph_re = re.compile(r'(<p\b[^>]*>)([\s\S]*?)(</p>)', flags=re.I)
matches = []
for match in paragraph_re.finditer(lab_text):
    rendered = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", match.group(2))).strip()
    if (
        "laberinto de tres metros" in rendered
        and (
            "puede llevar media hora si se va despacio" in rendered
            or "lleva más tiempo" in rendered
        )
    ):
        matches.append(match)

if len(matches) != 1:
    raise SystemExit(
        f"Could not uniquely locate Spanish labyrinth timing FAQ for compatibility bridge; found {len(matches)}"
    )
match = matches[0]
rendered = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", match.group(2))).strip()
if rendered != historical_timing:
    lab_text = (
        lab_text[:match.start()]
        + match.group(1)
        + historical_timing
        + match.group(3)
        + lab_text[match.end():]
    )
    labyrinth.write_text(lab_text, encoding="utf-8")
    print("bridged visible Spanish labyrinth timing FAQ to legacy credibility source state")

# Keep any structured FAQ copies in a state the old module already understands.
lab_text = labyrinth.read_text(encoding="utf-8")
if approved_timing in lab_text:
    labyrinth.write_text(lab_text.replace(approved_timing, legacy_timing), encoding="utf-8")

subprocess.run(
    [sys.executable, str(HERE / "apply_content_consistency_v1.py"), str(ROOT)],
    check=True,
)

# Prove the legacy pass reached its expected intermediate geology state. The
# workflow's next gates replace this with researched chronology before deploy.
for path, needle in (
    (ROOT / "que-es-un-oolito/index.html", "100.000 y 128.000 años"),
    (ROOT / "en/what-is-an-ooid/index.html", "100,000 and 128,000 years"),
):
    if needle not in path.read_text(encoding="utf-8"):
        raise SystemExit(
            f"Legacy consistency bridge did not reach expected intermediate state: {path.relative_to(ROOT)}"
        )

# Reader-facing book excerpt repair. The genuine book artwork was moved out of
# the old two-column excerpt wrapper; make the bilingual spread use the full
# reading width instead of leaving it trapped in the former figure column.
BOOK_READING_STYLE_ID = "oolita-book-reading-width-v1"
BOOK_READING_STYLE = r'''<style id="oolita-book-reading-width-v1">
#extracto-libro .book-excerpt-layout{display:block!important;width:100%!important;max-width:none!important}
#extracto-libro .book-excerpt-spread{width:100%!important;max-width:none!important;grid-template-columns:repeat(2,minmax(0,1fr))!important}
@media(max-width:760px){
  #extracto-libro .book-excerpt-spread{grid-template-columns:1fr!important}
  #extracto-libro .book-excerpt-page+.book-excerpt-page{border-left:0!important;border-top:1px solid rgba(45,78,35,.45)!important}
}
</style>'''

book_pages = (
    ROOT / "ediciones/libro/index.html",
    ROOT / "en/editions/book/index.html",
)
for path in book_pages:
    if not path.is_file():
        raise SystemExit(f"Missing book page for reading-width repair: {path.relative_to(ROOT)}")
    text = path.read_text(encoding="utf-8")
    if 'id="extracto-libro"' not in text or "book-excerpt-layout" not in text or "book-excerpt-spread" not in text:
        raise SystemExit(f"Book excerpt structure missing in {path.relative_to(ROOT)}")
    text = re.sub(
        r'<style\s+id=["\']oolita-book-reading-width-v1["\']>[\s\S]*?</style>',
        "",
        text,
        flags=re.I,
    )
    if "</head>" not in text:
        raise SystemExit(f"Book page has no </head>: {path.relative_to(ROOT)}")
    text = text.replace("</head>", BOOK_READING_STYLE + "\n</head>", 1)
    if text.count(f'id="{BOOK_READING_STYLE_ID}"') != 1:
        raise SystemExit(f"Book reading-width style was not installed exactly once in {path.relative_to(ROOT)}")
    path.write_text(text, encoding="utf-8")

# Mark the two changed book routes fresh for search crawlers. The normal static
# SEO gate still validates the resulting sitemap, canonicals and hreflang.
def touch_sitemap(routes: set[str]) -> None:
    sitemap = ROOT / "sitemap.xml"
    if not sitemap.is_file():
        raise SystemExit("Missing sitemap.xml while marking changed book routes")
    ns = "http://www.sitemaps.org/schemas/sitemap/0.9"
    ET.register_namespace("", ns)
    tree = ET.parse(sitemap)
    root = tree.getroot()
    seen: set[str] = set()
    for url in root.findall(f"{{{ns}}}url"):
        loc = url.find(f"{{{ns}}}loc")
        if loc is None or not loc.text:
            continue
        route = re.sub(r"^https://oolita\.es", "", loc.text.strip())
        if route not in routes:
            continue
        lastmod = url.find(f"{{{ns}}}lastmod")
        if lastmod is None:
            lastmod = ET.SubElement(url, f"{{{ns}}}lastmod")
        lastmod.text = "2026-08-28"
        seen.add(route)
    missing = routes - seen
    if missing:
        raise SystemExit(f"Changed book route(s) missing from sitemap: {sorted(missing)}")
    tree.write(sitemap, encoding="utf-8", xml_declaration=True)


touch_sitemap({"/ediciones/libro/", "/en/editions/book/"})

print(
    "OOLITA final consistency compatibility passed: "
    f"{changed} geology page(s) bridged plus Spanish labyrinth compatibility; "
    "book excerpt reading width repaired in ES/EN; final researched/editorial wording still pending."
)
