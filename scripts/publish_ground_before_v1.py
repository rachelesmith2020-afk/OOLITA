#!/usr/bin/env python3
"""Publish the pre-labyrinth archival plate on both labyrinth pages.

The source is the original 2021 plate already carried by the reconstructed site.
Its handwritten caption is removed by cropping back to the untouched photograph;
the caption is then rebuilt in the site's actual Instrument Sans typography.

Placement is deliberately immediate after the labyrinth-page opening: the reader
meets the ground before the lineage/history and before any further explanation.
There is no added descriptive copy.
"""
from __future__ import annotations

from pathlib import Path
from html import escape
import re
import subprocess
import sys
import xml.etree.ElementTree as ET

root = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
source = root / "laberinto/el-suelo-antes.jpg"
photo = root / "laberinto/el-suelo-antes-photo.jpg"
lastmod = "2026-09-18"

if not source.is_file():
    raise SystemExit(f"Missing supplied archive image: {source}")

# The supplied 1380×1480 plate contains a 1200×1200 untouched photograph at
# x=90, y=90. Crop only that photographic field, then rebuild the cream frame
# and labels as native HTML so the typography is genuinely the site's own.
subprocess.run(
    [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-i", str(source),
        "-vf", "crop=1200:1200:90:90",
        "-q:v", "3",
        str(photo),
    ],
    check=True,
)
if not photo.is_file() or photo.stat().st_size < 50_000:
    raise SystemExit("Failed to create archival ground photograph crop")

style = """<style id="oolita-ground-before-style">
.oolita-ground-before-section{
  display:flex;
  justify-content:center;
  align-items:center;
}
.oolita-ground-before{
  width:min(100%,42rem);
  margin:0 auto;
}
.oolita-ground-before-frame{
  width:100%;
  box-sizing:border-box;
  background:#F4EDE3;
  padding:5.66% 6.30% 3.9%;
}
.oolita-ground-before img{
  display:block;
  width:100%;
  height:auto;
  object-fit:cover;
  margin:0!important;
  border:0!important;
  border-radius:0!important;
  box-shadow:none!important;
}
.oolita-ground-before figcaption{
  display:flex;
  align-items:baseline;
  justify-content:space-between;
  gap:1rem;
  width:100%;
  margin:0;
  padding:1rem 0 0;
  color:#4D4A46;
  font-family:"Instrument Sans",system-ui,sans-serif;
  font-style:normal;
}
.oolita-ground-before-title{
  margin:0;
  padding:0;
  font-size:clamp(1rem,2.25vw,1.2rem);
  line-height:1;
  font-weight:400;
  letter-spacing:-.035em;
  text-transform:lowercase;
  white-space:nowrap;
}
.oolita-ground-before-meta{
  margin:0 0 0 auto;
  padding:0;
  font-size:clamp(.58rem,1vw,.68rem);
  line-height:1;
  font-weight:400;
  letter-spacing:.045em;
  white-space:nowrap;
}
@media (max-width:560px){
  .oolita-ground-before{width:min(100%,34rem)}
  .oolita-ground-before figcaption{padding-top:.8rem}
}
</style>"""

pages = (
    (
        "laberinto/index.html",
        "El suelo antes de trazar el laberinto OOLITA, septiembre de 2021.",
    ),
    (
        "en/labyrinth/index.html",
        "The ground before the OOLITA labyrinth was laid, September 2021.",
    ),
)

archive = lambda alt: (
    '<section class="tramo oolita-ground-before-section" data-oolita-archive="true">'
    '<figure class="oolita-ground-before" data-oolita-ground-before="true" data-oolita-ground-before-version="flush-caption-v3">'
    '<div class="oolita-ground-before-frame">'
    f'<img src="/laberinto/el-suelo-antes-photo.jpg" width="1200" height="1200" '
    f'loading="lazy" decoding="async" alt="{escape(alt, quote=True)}">'
    '<figcaption>'
    '<span class="oolita-ground-before-title">el suelo antes</span>'
    '<span class="oolita-ground-before-meta">OOLITA · septiembre 2021</span>'
    '</figcaption>'
    '</div>'
    '</figure>'
    '</section>'
)

for rel, alt in pages:
    path = root / rel
    if not path.is_file():
        raise SystemExit(f"Missing labyrinth page: {rel}")
    page = path.read_text(encoding="utf-8")

    # Replace or install the style exactly once.
    page, style_count = re.subn(
        r'<style id="oolita-ground-before-style">.*?</style>',
        style,
        page,
        flags=re.S,
    )
    if style_count > 1:
        raise SystemExit(f"Duplicate archive styles: {rel}")
    if style_count == 0:
        if "</head>" not in page:
            raise SystemExit(f"Missing page head: {rel}")
        page = page.replace("</head>", style + "\n</head>", 1)

    # Remove any previous archive block, including the earlier flattened plate.
    page, old_count = re.subn(
        r'<section\b[^>]*data-oolita-archive="true"[^>]*>.*?</section>',
        "",
        page,
        flags=re.S | re.I,
    )
    if old_count > 1:
        raise SystemExit(f"Duplicate previous archive blocks: {rel}")

    # Best placement: immediately after the opening hero and before Lineage.
    pattern = r'(<section class="hero">.*?</section>)'
    page, count = re.subn(
        pattern,
        lambda match: match.group(1) + "\n" + archive(alt),
        page,
        count=1,
        flags=re.S,
    )
    if count != 1:
        raise SystemExit(f"Could not locate the labyrinth opening: {rel}")

    # Fail closed on structure and copy.
    if page.count('data-oolita-ground-before="true"') != 1:
        raise SystemExit(f"Archive figure count invalid: {rel}")
    if page.count('data-oolita-ground-before-version="flush-caption-v3"') != 1:
        raise SystemExit(f"Flush archive caption marker missing: {rel}")
    if page.count('/laberinto/el-suelo-antes-photo.jpg') != 1:
        raise SystemExit(f"Archive image src count invalid: {rel}")
    if page.count("el suelo antes") != 1:
        raise SystemExit(f"Archive title count invalid: {rel}")
    if page.count("OOLITA · septiembre 2021") != 1:
        raise SystemExit(f"Archive provenance count invalid: {rel}")

    path.write_text(page, encoding="utf-8")
    print(f"Native archival ground plate published on {rel}")

# Refresh sitemap dates for the two pages changed here.
sitemap = root / "sitemap.xml"
if not sitemap.is_file():
    raise SystemExit("Missing sitemap.xml")
ET.register_namespace("", "http://www.sitemaps.org/schemas/sitemap/0.9")
tree = ET.parse(sitemap)
ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
wanted = {
    "https://oolita.es/laberinto/",
    "https://oolita.es/en/labyrinth/",
}
seen = set()
for url_el in tree.getroot().findall("sm:url", ns):
    loc = url_el.find("sm:loc", ns)
    if loc is None or loc.text not in wanted:
        continue
    seen.add(loc.text)
    lm = url_el.find("sm:lastmod", ns)
    if lm is None:
        lm = ET.SubElement(url_el, "{http://www.sitemaps.org/schemas/sitemap/0.9}lastmod")
    lm.text = lastmod
if seen != wanted:
    raise SystemExit(f"Labyrinth sitemap URLs missing: {sorted(wanted-seen)}")
tree.write(sitemap, encoding="utf-8", xml_declaration=True)

print("OOLITA ground-before archive: original photograph, native site typography, bilingual placement and sitemap freshness verified.")
