#!/usr/bin/env python3
"""Final deployment safeguard for the retired Wednesday/Reels page.

Runs after all reader/SEO transforms so a mirrored legacy origin cannot restore
/reels/, its homepage/menu entry, sitemap URL, or its obsolete cache header.
Previously published Reels URLs are retained only as permanent redirects to the
canonical poster archive, preventing external links from becoming 404s.
"""
from __future__ import annotations

from pathlib import Path
import re
import shutil
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")

if not ROOT.is_dir():
    raise SystemExit(f"Missing built site: {ROOT}")

# Reverse exact legacy copy where it may still survive a mirrored-origin build.
replacements = {
    "index.html": (
        '\n  <a class="fila" href="/reels/"><span class="n">R</span><span class="nom">Los miércoles</span><span class="glo">Nueve carteles en movimiento · sin música</span></a>',
        "",
    ),
    "en/index.html": (
        '\n  <a class="fila" href="/reels/"><span class="n">R</span><span class="nom">The Wednesdays</span><span class="glo">Nine posters in motion · no music</span></a>',
        "",
    ),
    "carteles/index.html": (
        'Los carteles también se mueven: <a href="/reels/">nueve reels silenciosos, uno cada miércoles</a>. Después de los carteles, una imagen cada domingo hasta la apertura:',
        'Después de los carteles, una imagen cada domingo hasta la apertura:',
    ),
    "en/posters/index.html": (
        'The posters also move: <a href="/reels/">nine silent reels, one each Wednesday</a>. After the posters, one image every Sunday until the opening:',
        'After the posters, one image every Sunday until the opening:',
    ),
    "domingos/index.html": (
        'La serie no empezó aquí. Antes de los domingos hubo <a href="/carteles/">nueve carteles</a>, y esos carteles volvieron <a href="/reels/">en movimiento, uno cada miércoles</a>',
        'La serie no empezó aquí. Antes de los domingos hubo <a href="/carteles/">nueve carteles</a>',
    ),
    "en/sundays/index.html": (
        'The series did not start here. Before the Sundays there were <a href="/en/posters/">nine posters</a>, and those posters returned <a href="/reels/">in motion, one each Wednesday</a>',
        'The series did not start here. Before the Sundays there were <a href="/en/posters/">nine posters</a>',
    ),
}
for relative, (old, new) in replacements.items():
    path = ROOT / relative
    if not path.is_file():
        continue
    text = path.read_text(encoding="utf-8")
    if old in text:
        path.write_text(text.replace(old, new, 1), encoding="utf-8")

# Remove any remaining HTML link to the retired route, including absolute forms.
reels_anchor = re.compile(
    r'<a\b(?=[^>]*\bhref=["\'](?:https://(?:www\.)?oolita\.es)?/reels(?:/[^"\']*)?["\'])[^>]*>[\s\S]*?</a>\s*',
    flags=re.I,
)
for path in ROOT.rglob("*.html"):
    text = path.read_text(encoding="utf-8")
    cleaned = reels_anchor.sub("", text)
    if cleaned != text:
        path.write_text(cleaned, encoding="utf-8")

# Retire the page and all generated Reel assets from the deploy bundle.
shutil.rmtree(ROOT / "reels", ignore_errors=True)

# Remove all sitemap entries for the retired route, including any old variants.
sitemap = ROOT / "sitemap.xml"
if not sitemap.is_file():
    raise SystemExit("Missing sitemap.xml while retiring Reels")
sitemap_text = sitemap.read_text(encoding="utf-8")
sitemap_text = re.sub(
    r'\s*<url>\s*<loc>https://(?:www\.)?oolita\.es/reels(?:/[^<]*)?</loc>[\s\S]*?</url>\s*',
    "\n",
    sitemap_text,
    flags=re.I,
)
sitemap.write_text(sitemap_text, encoding="utf-8")

# Remove the obsolete cache header that was previously installed for Reel files.
headers = ROOT / "_headers"
if headers.is_file():
    text = headers.read_text(encoding="utf-8")
    text = re.sub(
        r'(?mi)^/reels/\*\s*\n(?:[ \t]+[^\n]+\n?)*',
        "",
        text,
    )
    headers.write_text(text.rstrip() + "\n", encoding="utf-8")

# Preserve external/backlink value and prevent 404s for both the page and any
# old direct Reel asset URL. Cloudflare Pages applies these as permanent 301s.
redirects = ROOT / "_redirects"
existing = redirects.read_text(encoding="utf-8") if redirects.is_file() else ""
lines = [line for line in existing.splitlines() if line.strip()]
for rule in (
    "/reels /carteles/ 301",
    "/reels/ /carteles/ 301",
    "/reels/* /carteles/ 301",
):
    if rule not in lines:
        lines.append(rule)
redirects.write_text("\n".join(lines) + "\n", encoding="utf-8")

# Final no-straggler gate after every build transform. _redirects is the sole
# intentional place where the old route may remain.
stragglers: list[str] = []
text_suffixes = {".html", ".xml", ".json", ".txt", ".js", ".css"}
for path in ROOT.rglob("*"):
    if not path.is_file() or path.name == "_redirects":
        continue
    if path.suffix.lower() not in text_suffixes and path.name != "_headers":
        continue
    text = path.read_text(encoding="utf-8", errors="ignore")
    for needle in (
        "/reels/",
        "https://oolita.es/reels",
        "https://www.oolita.es/reels",
        "The Wednesdays",
        "Los miércoles",
        "Nine posters in motion · no music",
        "Nueve carteles en movimiento · sin música",
    ):
        if needle in text:
            stragglers.append(f"{path.relative_to(ROOT)}: {needle}")

if (ROOT / "reels").exists():
    stragglers.append("reels/ directory still exists")
if not (ROOT / "carteles" / "index.html").is_file():
    stragglers.append("redirect target /carteles/ is missing")

redirect_text = redirects.read_text(encoding="utf-8")
for rule in (
    "/reels /carteles/ 301",
    "/reels/ /carteles/ 301",
    "/reels/* /carteles/ 301",
):
    if rule not in redirect_text.splitlines():
        stragglers.append(f"missing permanent redirect: {rule}")

if stragglers:
    print("Retired Reels stragglers found:")
    print("\n".join(stragglers))
    raise SystemExit(1)

print("Wednesday/Reels retirement final gate passed: no links, page, sitemap entry or stale header; legacy URLs 301 to /carteles/.")
