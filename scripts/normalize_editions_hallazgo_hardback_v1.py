#!/usr/bin/env python3
"""Keep the approved Hallazgo hardback sequence on the English Editions page and mark the route fresh for search."""
from __future__ import annotations

from pathlib import Path
import sys
import xml.etree.ElementTree as ET

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
PAGE = ROOT / "en/editions/index.html"
SITEMAP = ROOT / "sitemap.xml"
BASE = "https://oolita.es"
ROUTE = "/en/editions/"
LASTMOD = "2026-08-24"

OLD_FORMS = (
    "The book and T-shirt are the first two editions. After them will come field publications and small collaborations made in Cabo de Gata.",
    "The book and T-shirt are the first OOLITA editions. They begin a wider series of field publications, small textile works and collaborations rooted in Cabo de Gata.",
)
NEW = (
    "The book and T-shirt are the first two editions. After them will come the Hallazgo hardback, "
    "followed by field publications and small collaborations made in Cabo de Gata."
)

if not ROOT.is_dir():
    raise SystemExit(f"Missing built site: {ROOT}")
if not PAGE.is_file():
    raise SystemExit(f"Missing English Editions page: {PAGE}")
if not SITEMAP.is_file():
    raise SystemExit(f"Missing sitemap: {SITEMAP}")

text = PAGE.read_text(encoding="utf-8")
original = text

if NEW not in text:
    for old in OLD_FORMS:
        if old in text:
            text = text.replace(old, NEW, 1)
            break
    else:
        raise SystemExit("English Editions sequence source drifted; approved paragraph was not found.")

if text.count(NEW) != 1:
    raise SystemExit("English Editions sequence validation failed: approved Hallazgo sentence must appear exactly once.")

for old in OLD_FORMS:
    if old in text:
        raise SystemExit("English Editions sequence validation failed: superseded wording remains on the page.")

if text != original:
    PAGE.write_text(text, encoding="utf-8")
    print("English Editions sequence updated: Hallazgo hardback added.")
else:
    print("English Editions sequence already current.")

# No obsolete Editions sequence may survive elsewhere in the built HTML bundle.
stragglers: list[str] = []
for html in sorted(ROOT.rglob("*.html")):
    body = html.read_text(encoding="utf-8")
    for old in OLD_FORMS:
        if old in body:
            stragglers.append(f"{html.relative_to(ROOT).as_posix()}: {old}")
if stragglers:
    print("Superseded English Editions wording remains in the deployment bundle:")
    print("\n".join(stragglers))
    raise SystemExit(1)

# Refresh this route in the XML sitemap so search engines see the editorial update.
ET.register_namespace("", "http://www.sitemaps.org/schemas/sitemap/0.9")
tree = ET.parse(SITEMAP)
root = tree.getroot()
ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
expected = BASE + ROUTE
matched = False
changed_sitemap = False
for url_el in root.findall("sm:url", ns):
    loc = url_el.find("sm:loc", ns)
    if loc is None or not loc.text or loc.text.strip() != expected:
        continue
    matched = True
    lastmod = url_el.find("sm:lastmod", ns)
    if lastmod is None:
        lastmod = ET.SubElement(url_el, "{http://www.sitemaps.org/schemas/sitemap/0.9}lastmod")
    if lastmod.text != LASTMOD:
        lastmod.text = LASTMOD
        changed_sitemap = True
    break

if not matched:
    raise SystemExit(f"English Editions route missing from sitemap: {expected}")
if changed_sitemap:
    tree.write(SITEMAP, encoding="utf-8", xml_declaration=True)
    print("English Editions sitemap lastmod refreshed.")
else:
    print("English Editions sitemap lastmod already current.")

print("Hallazgo hardback Editions gate passed: copy current, no stragglers, sitemap current.")
