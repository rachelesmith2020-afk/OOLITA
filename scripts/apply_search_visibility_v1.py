#!/usr/bin/env python3
"""Prepare OOLITA for recrawling without claiming search-engine control.

- Publishes the IndexNow ownership key at the site root.
- Ensures robots.txt advertises the sitemap.
- Updates <lastmod> for pages materially changed on 2026-08-22.
"""
from __future__ import annotations

import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
KEY_FILE = Path("search/indexnow-key.txt")
LASTMOD = "2026-08-22"
BASE = "https://oolita.es"

CHANGED_PATHS = {
    "/",
    "/en/",
    "/cabo-de-gata/",
    "/en/cabo-de-gata/",
    "/ediciones/",
    "/en/editions/",
    "/ediciones/libro/",
    "/en/editions/book/",
    "/ediciones/camiseta/",
    "/en/editions/t-shirt/",
    "/sobre-oolita/",
    "/en/about/",
    "/colaborar/",
    "/en/work-with-oolita/",
    "/laberinto/",
    "/en/labyrinth/",
    "/carteles/",
    "/en/posters/",
}

if not ROOT.is_dir():
    raise SystemExit(f"Missing built site: {ROOT}")
if not KEY_FILE.is_file():
    raise SystemExit(f"Missing IndexNow key file: {KEY_FILE}")

key = KEY_FILE.read_text(encoding="utf-8").strip()
if not re.fullmatch(r"[A-Za-z0-9-]{8,128}", key):
    raise SystemExit("Invalid IndexNow key format")
(ROOT / f"{key}.txt").write_text(key + "\n", encoding="utf-8")
print(f"search visibility: published IndexNow key {key}.txt")

robots = ROOT / "robots.txt"
robots_text = robots.read_text(encoding="utf-8") if robots.is_file() else "User-agent: *\nAllow: /\n"
sitemap_line = f"Sitemap: {BASE}/sitemap.xml"
if sitemap_line not in robots_text:
    if robots_text and not robots_text.endswith("\n"):
        robots_text += "\n"
    robots_text += sitemap_line + "\n"
robots.write_text(robots_text, encoding="utf-8")

sitemap = ROOT / "sitemap.xml"
if not sitemap.is_file():
    raise SystemExit("Missing sitemap.xml")
ET.register_namespace("", "http://www.sitemaps.org/schemas/sitemap/0.9")
tree = ET.parse(sitemap)
root = tree.getroot()
ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
seen = set()
for url_el in root.findall("sm:url", ns):
    loc = url_el.find("sm:loc", ns)
    if loc is None or not loc.text:
        continue
    url = loc.text.strip()
    if not url.startswith(BASE):
        continue
    path = url[len(BASE):] or "/"
    if path in CHANGED_PATHS:
        seen.add(path)
        lastmod = url_el.find("sm:lastmod", ns)
        if lastmod is None:
            lastmod = ET.SubElement(url_el, "{http://www.sitemaps.org/schemas/sitemap/0.9}lastmod")
        lastmod.text = LASTMOD

missing = sorted(CHANGED_PATHS - seen)
if missing:
    raise SystemExit(f"Changed URLs missing from sitemap: {missing}")
tree.write(sitemap, encoding="utf-8", xml_declaration=True)

if sitemap_line not in robots.read_text(encoding="utf-8"):
    raise SystemExit("robots.txt sitemap invariant missing")
if not (ROOT / f"{key}.txt").is_file():
    raise SystemExit("IndexNow key invariant missing")

print(f"search visibility: marked {len(seen)} changed URLs with lastmod {LASTMOD}")
print("OOLITA search visibility layer validated successfully.")
