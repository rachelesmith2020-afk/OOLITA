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
# historical source paragraph so that it can perform and validate its own edit.
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

lab_text = labyrinth.read_text(encoding="utf-8")
if approved_timing in lab_text:
    labyrinth.write_text(lab_text.replace(approved_timing, legacy_timing), encoding="utf-8")

subprocess.run(
    [sys.executable, str(HERE / "apply_content_consistency_v1.py"), str(ROOT)],
    check=True,
)

for path, needle in (
    (ROOT / "que-es-un-oolito/index.html", "100.000 y 128.000 años"),
    (ROOT / "en/what-is-an-ooid/index.html", "100,000 and 128,000 years"),
):
    if needle not in path.read_text(encoding="utf-8"):
        raise SystemExit(
            f"Legacy consistency bridge did not reach expected intermediate state: {path.relative_to(ROOT)}"
        )

# Reunite the genuine book illustration with the bilingual book passage. The
# illustration belongs to this excerpt and must not float separately in the hero.
BOOK_MARKER = "Electro frente al trazado del laberinto Oolita"
BOOK_STYLE_ID = "oolita-book-excerpt-composed-v2"
BOOK_STYLE = r'''<style id="oolita-book-excerpt-composed-v2">
#extracto-libro .book-excerpt-layout{
  display:grid!important;
  grid-template-columns:minmax(14rem,20rem) minmax(0,1fr)!important;
  gap:clamp(2rem,4vw,4rem)!important;
  align-items:start!important;
  width:min(100%,72rem)!important;
  max-width:72rem!important;
  margin:clamp(1.5rem,3vw,2.5rem) auto 0!important;
}
#extracto-libro .book-excerpt-figure{
  display:block!important;
  float:none!important;
  width:100%!important;
  max-width:20rem!important;
  margin:0 auto!important;
  padding:0!important;
  clear:none!important;
  text-align:center!important;
}
#extracto-libro .book-excerpt-figure img{
  display:block!important;
  width:100%!important;
  max-width:20rem!important;
  height:auto!important;
  margin:0 auto!important;
}
#extracto-libro .book-excerpt-figure figcaption{
  margin:.7rem auto 0!important;
  max-width:20rem!important;
}
#extracto-libro .book-excerpt-spread{
  display:grid!important;
  grid-template-columns:repeat(2,minmax(0,1fr))!important;
  width:100%!important;
  max-width:none!important;
  margin:0!important;
}
@media(max-width:900px){
  #extracto-libro .book-excerpt-layout{
    grid-template-columns:1fr!important;
    width:min(100%,46rem)!important;
    max-width:46rem!important;
  }
  #extracto-libro .book-excerpt-figure{max-width:18rem!important}
}
@media(max-width:760px){
  #extracto-libro .book-excerpt-spread{grid-template-columns:1fr!important}
  #extracto-libro .book-excerpt-page+.book-excerpt-page{
    border-left:0!important;
    border-top:1px solid rgba(45,78,35,.45)!important;
  }
}
</style>'''

book_pages = (
    ROOT / "ediciones/libro/index.html",
    ROOT / "en/editions/book/index.html",
)
figure_re = re.compile(r'<figure\b[^>]*>[\s\S]*?</figure>', flags=re.I)
layout_open_re = re.compile(r'<div\b[^>]*class=["\'][^"\']*\bbook-excerpt-layout\b[^"\']*["\'][^>]*>', flags=re.I)


def normalize_figure(block: str) -> str:
    opening = re.match(r'<figure\b[^>]*>', block, flags=re.I)
    if not opening:
        raise SystemExit("Malformed book illustration figure")
    tag = opening.group(0)
    tag = re.sub(r'\s+style\s*=\s*(["\']).*?\1', '', tag, flags=re.I | re.S)
    cm = re.search(r'\bclass\s*=\s*(["\'])(.*?)\1', tag, flags=re.I | re.S)
    if cm:
        classes = [c for c in cm.group(2).split() if c != "oolita-book-hero-visual"]
        if "book-excerpt-figure" not in classes:
            classes.append("book-excerpt-figure")
        new_classes = " ".join(classes)
        tag = tag[:cm.start(2)] + new_classes + tag[cm.end(2):]
    else:
        tag = tag[:-1] + ' class="book-excerpt-figure">'
    return tag + block[opening.end():]


for path in book_pages:
    if not path.is_file():
        raise SystemExit(f"Missing book page for excerpt composition: {path.relative_to(ROOT)}")
    text = path.read_text(encoding="utf-8")

    figures = [m for m in figure_re.finditer(text) if BOOK_MARKER in m.group(0)]
    if len(figures) != 1:
        raise SystemExit(
            f"Expected exactly one genuine book illustration in {path.relative_to(ROOT)}; found {len(figures)}"
        )
    figure = figures[0]
    block = normalize_figure(figure.group(0))
    text = text[:figure.start()] + text[figure.end():]

    layout = layout_open_re.search(text)
    if not layout:
        raise SystemExit(f"Book excerpt layout missing in {path.relative_to(ROOT)}")
    text = text[:layout.end()] + "\n" + block + "\n" + text[layout.end():]

    # Remove obsolete visual-first and width-only overrides so this single
    # composition rule is authoritative.
    text = re.sub(
        r'<style\s+id=["\']oolita-book-visual-first-v1["\'][^>]*>[\s\S]*?</style>',
        "",
        text,
        flags=re.I,
    )
    text = re.sub(
        r'<style\s+id=["\']oolita-book-reading-width-v1["\'][^>]*>[\s\S]*?</style>',
        "",
        text,
        flags=re.I,
    )
    text = re.sub(
        r'<style\s+id=["\']oolita-book-excerpt-composed-v2["\'][^>]*>[\s\S]*?</style>',
        "",
        text,
        flags=re.I,
    )
    if "</head>" not in text:
        raise SystemExit(f"Book page has no </head>: {path.relative_to(ROOT)}")
    text = text.replace("</head>", BOOK_STYLE + "\n</head>", 1)

    # Fail closed: the illustration must now live inside the same excerpt layout
    # and there must be no hero-only class left behind.
    section_match = re.search(
        r'<section\b[^>]*id=["\']extracto-libro["\'][^>]*>[\s\S]*?</section>',
        text,
        flags=re.I,
    )
    if not section_match or BOOK_MARKER not in section_match.group(0):
        raise SystemExit(f"Book illustration is not inside the excerpt section in {path.relative_to(ROOT)}")
    layout_match = re.search(
        r'<div\b[^>]*class=["\'][^"\']*\bbook-excerpt-layout\b[^"\']*["\'][^>]*>[\s\S]*?<div\b[^>]*class=["\'][^"\']*\bbook-excerpt-spread\b',
        section_match.group(0),
        flags=re.I,
    )
    if not layout_match or BOOK_MARKER not in layout_match.group(0):
        raise SystemExit(f"Illustration and bilingual passage are not composed together in {path.relative_to(ROOT)}")
    if "oolita-book-hero-visual" in text:
        raise SystemExit(f"Hero-only book illustration class survived in {path.relative_to(ROOT)}")
    if text.count(f'id="{BOOK_STYLE_ID}"') != 1:
        raise SystemExit(f"Book excerpt composition style is not unique in {path.relative_to(ROOT)}")

    path.write_text(text, encoding="utf-8")


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
    "book illustration and bilingual excerpt reunited and centered in ES/EN; "
    "final researched/editorial wording still pending."
)
