#!/usr/bin/env python3
"""Keep the approved Hallazgo hardback sequence on both Editions pages and mark both routes fresh for search."""
from __future__ import annotations

from pathlib import Path
import sys
import xml.etree.ElementTree as ET

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
EN_PAGE = ROOT / "en/editions/index.html"
ES_PAGE = ROOT / "ediciones/index.html"
SITEMAP = ROOT / "sitemap.xml"
BASE = "https://oolita.es"
LASTMOD = "2026-08-25"

OLD_EN = (
    "The book and T-shirt are the first two editions. After them will come field publications and small collaborations made in Cabo de Gata.",
    "The book and T-shirt are the first OOLITA editions. They begin a wider series of field publications, small textile works and collaborations rooted in Cabo de Gata.",
)
NEW_EN = (
    "The book and T-shirt are the first two editions. After them will come the Hallazgo hardback, "
    "followed by field publications and small collaborations made in Cabo de Gata."
)
OLD_ES = (
    "El libro y la camiseta son las dos primeras ediciones. Después vendrán publicaciones de campo y pequeñas colaboraciones hechas en Cabo de Gata.",
    "El libro y la camiseta son las primeras ediciones OOLITA. Abren una serie más amplia de publicaciones de campo, pequeñas piezas textiles y colaboraciones arraigadas en Cabo de Gata.",
)
NEW_ES = (
    "El libro y la camiseta son las dos primeras ediciones. Después vendrá la edición de tapa dura de Hallazgo, "
    "seguida de publicaciones de campo y pequeñas colaboraciones hechas en Cabo de Gata."
)

DETAIL_REPLACEMENTS = {
    EN_PAGE: (
        (" sits apart from this sequence: a hardback publication bringing together the complete body of work.",
         " follows the first OOLITA book and T-shirt: a hardback publication bringing together the complete body of work."),
    ),
    ES_PAGE: (
        (" queda aparte de esta secuencia: una edición en tapa dura que reúne el cuerpo completo de la obra.",
         " llega después del libro y la camiseta de OOLITA: una edición en tapa dura que reúne el cuerpo completo de la obra."),
    ),
}

if not ROOT.is_dir():
    raise SystemExit(f"Missing built site: {ROOT}")
for page in (EN_PAGE, ES_PAGE):
    if not page.is_file():
        raise SystemExit(f"Missing Editions page: {page}")
if not SITEMAP.is_file():
    raise SystemExit(f"Missing sitemap: {SITEMAP}")


def update_intro(page: Path, old_forms: tuple[str, ...], new: str) -> None:
    text = page.read_text(encoding="utf-8")
    original = text
    if new not in text:
        for old in old_forms:
            if old in text:
                text = text.replace(old, new, 1)
                break
        else:
            raise SystemExit(f"Editions sequence source drifted; approved paragraph was not found: {page}")
    for old, replacement in DETAIL_REPLACEMENTS.get(page, ()):
        if old in text:
            text = text.replace(old, replacement, 1)
    if text.count(new) != 1:
        raise SystemExit(f"Editions sequence validation failed: approved Hallazgo sentence must appear exactly once: {page}")
    for old in old_forms:
        if old in text:
            raise SystemExit(f"Editions sequence validation failed: superseded wording remains: {page}")
    if text != original:
        page.write_text(text, encoding="utf-8")
        print(f"Editions sequence updated: {page.relative_to(ROOT)}")
    else:
        print(f"Editions sequence already current: {page.relative_to(ROOT)}")


update_intro(EN_PAGE, OLD_EN, NEW_EN)
update_intro(ES_PAGE, OLD_ES, NEW_ES)

# No obsolete or contradictory sequence wording may survive anywhere in the built HTML bundle.
STRAGGLER_PHRASES = OLD_EN + OLD_ES + (
    "sits apart from this sequence",
    "queda aparte de esta secuencia",
)
stragglers: list[str] = []
for html in sorted(ROOT.rglob("*.html")):
    body = html.read_text(encoding="utf-8")
    for old in STRAGGLER_PHRASES:
        if old in body:
            stragglers.append(f"{html.relative_to(ROOT).as_posix()}: {old}")
if stragglers:
    print("Superseded or contradictory Editions wording remains in the deployment bundle:")
    print("\n".join(stragglers))
    raise SystemExit(1)

# Refresh both Editions routes in the XML sitemap so search engines see the editorial update.
ET.register_namespace("", "http://www.sitemaps.org/schemas/sitemap/0.9")
tree = ET.parse(SITEMAP)
root = tree.getroot()
ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
expected_urls = {BASE + "/en/editions/", BASE + "/ediciones/"}
matched_urls: set[str] = set()
changed_sitemap = False
for url_el in root.findall("sm:url", ns):
    loc = url_el.find("sm:loc", ns)
    if loc is None or not loc.text:
        continue
    current = loc.text.strip()
    if current not in expected_urls:
        continue
    matched_urls.add(current)
    lastmod = url_el.find("sm:lastmod", ns)
    if lastmod is None:
        lastmod = ET.SubElement(url_el, "{http://www.sitemaps.org/schemas/sitemap/0.9}lastmod")
    if lastmod.text != LASTMOD:
        lastmod.text = LASTMOD
        changed_sitemap = True
if matched_urls != expected_urls:
    missing = sorted(expected_urls - matched_urls)
    raise SystemExit(f"Editions route(s) missing from sitemap: {missing}")
if changed_sitemap:
    tree.write(SITEMAP, encoding="utf-8", xml_declaration=True)
    print("Editions sitemap lastmod refreshed.")
else:
    print("Editions sitemap lastmod already current.")

print("Hallazgo hardback Editions gate passed: bilingual copy current, no stragglers, sitemap current.")
