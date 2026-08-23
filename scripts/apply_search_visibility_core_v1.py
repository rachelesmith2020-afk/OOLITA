#!/usr/bin/env python3
"""Prepare OOLITA for recrawling without claiming search-engine control.

- Publishes the IndexNow ownership key at the site root.
- Ensures robots.txt advertises the sitemap.
- Updates <lastmod> for pages materially changed on 2026-08-22.
- Builds the permanent bilingual 3D-world explainer before sitemap checks.
- Applies the final public identity, release-date and provenance-safe wording layer.
- Applies the 23 Aug live SEO audit repair as the last bundle mutation.
- Applies the agreed reader-assessment priority fixes after the SEO repair.
"""
from __future__ import annotations

import re
import runpy
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
HERE = Path(__file__).resolve().parent
KEY_FILE = Path("search/indexnow-key.txt")
LASTMOD = "2026-08-22"
BASE = "https://oolita.es"

# Deployment gate: public identity must validate before sitemap/IndexNow publication.
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
    "/privacidad/",
    "/en/privacy/",
    "/laberinto/",
    "/en/labyrinth/",
    "/carteles/",
    "/en/posters/",
}

if not ROOT.is_dir():
    raise SystemExit(f"Missing built site: {ROOT}")
if not KEY_FILE.is_file():
    raise SystemExit(f"Missing IndexNow key file: {KEY_FILE}")

# The 3D-world page is part of the permanent site layer. Running it here means
# it inherits all earlier direction, commerce, Follow, accessibility and
# first-party analytics transforms, and its sitemap entries then pass through
# the normal search-visibility checks below.
three_d_script = HERE / "apply_3d_world_v1.py"
if not three_d_script.is_file():
    raise SystemExit(f"Missing 3D-world build layer: {three_d_script}")
old_argv = sys.argv[:]
sys.argv = [str(three_d_script), str(ROOT)]
try:
    runpy.run_path(str(three_d_script), run_name="__main__")
finally:
    sys.argv = old_argv

# This is the final public-content pass. It runs after the 3D page exists so
# the same footer/legal identity applies to every public HTML route, including
# the mirrored 404 shell, before sitemap and IndexNow publication.
identity_script = HERE / "apply_public_identity_v3.py"
if not identity_script.is_file():
    raise SystemExit(f"Missing public identity layer: {identity_script}")
old_argv = sys.argv[:]
sys.argv = [str(identity_script), str(ROOT)]
try:
    runpy.run_path(str(identity_script), run_name="__main__")
finally:
    sys.argv = old_argv

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
for route in ("mundo-3d/index.html", "en/3d-world/index.html"):
    if not (ROOT / route).is_file():
        raise SystemExit(f"3D-world route missing after search layer: {route}")

print(f"search visibility: marked {len(seen)} changed URLs with lastmod {LASTMOD}")
print("OOLITA search visibility layer validated successfully.")

# The live-audit repair must run after every other content transformer. In
# particular, growth and identity expect the mirrored 404 shell; this pass
# replaces it only once those validators have finished.
seo_repair_script = HERE / "apply_seo_audit_2026_08_23.py"
if not seo_repair_script.is_file():
    raise SystemExit(f"Missing 23 Aug SEO audit repair layer: {seo_repair_script}")
old_argv = sys.argv[:]
sys.argv = [str(seo_repair_script), str(ROOT)]
try:
    runpy.run_path(str(seo_repair_script), run_name="__main__")
finally:
    sys.argv = old_argv

# Reader-facing hierarchy/factual changes come last so neither the identity nor
# SEO normalisation pass can restore the copy the reader audit is replacing.
reader_script = HERE / "apply_reader_assessment_v1.py"
if not reader_script.is_file():
    raise SystemExit(f"Missing reader-assessment layer: {reader_script}")
old_argv = sys.argv[:]
sys.argv = [str(reader_script), str(ROOT)]
try:
    runpy.run_path(str(reader_script), run_name="__main__")
finally:
    sys.argv = old_argv
