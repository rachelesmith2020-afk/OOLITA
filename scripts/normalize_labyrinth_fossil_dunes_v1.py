#!/usr/bin/env python3
"""Final factual/SEO gate for the OOLITA labyrinth location.

The labyrinth is on land beside the fossil dunes, not on a fossil dune.
This pass runs after every reader-facing transform, updates sitemap freshness for
changed pages, and rejects internal hrefs that would point at missing static
routes in the deployment bundle.
"""
from __future__ import annotations

from pathlib import Path
import posixpath
import re
import sys
from urllib.parse import unquote, urlsplit
import xml.etree.ElementTree as ET

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
BASE = "https://oolita.es"
LASTMOD = "2026-08-24"

if not ROOT.is_dir():
    raise SystemExit(f"Missing built site: {ROOT}")

# These two geology pages correctly discuss fossil dunes as geological objects.
# The location correction applies everywhere else the public site describes the
# labyrinth or its setting.
GEOLOGY_EXEMPT = {
    "que-es-un-oolito/index.html",
    "en/what-is-an-ooid/index.html",
}

# Most-specific first. The approved English wording is deliberately consistent:
# "on land beside the fossil dunes". Spanish uses the equivalent
# "en terreno junto a las dunas fósiles".
REPLACEMENTS = (
    (
        "stands on the same fossil dune that names the labyrinth: stone that was once sea",
        "stands beside the same fossil dunes",
    ),
    (
        "se levanta sobre la misma duna fósil que da nombre al laberinto: piedra que fue mar",
        "se levanta junto a las mismas dunas fósiles",
    ),
    (
        "on a fossil dune that was seabed a hundred thousand years ago",
        "on land beside the fossil dunes",
    ),
    (
        "sobre una duna fósil que hace cien mil años fue fondo del mar",
        "en terreno junto a las dunas fósiles",
    ),
    (
        "on a fossil dune beside the Mediterranean",
        "on land beside the fossil dunes, by the Mediterranean",
    ),
    (
        "sobre una duna fósil junto al Mediterráneo",
        "en terreno junto a las dunas fósiles, frente al Mediterráneo",
    ),
    ("on the Playa del Arco fossil dune", "on land beside the fossil dunes"),
    ("on the Los Escullos fossil dune", "on land beside the fossil dunes"),
    ("on the fossil dune", "on land beside the fossil dunes"),
    ("on a fossil dune", "on land beside the fossil dunes"),
    ("sobre la duna fósil de la Playa del Arco", "en terreno junto a las dunas fósiles"),
    ("sobre la duna fósil de Los Escullos", "en terreno junto a las dunas fósiles"),
    ("sobre la duna fósil", "en terreno junto a las dunas fósiles"),
    ("sobre una duna fósil", "en terreno junto a las dunas fósiles"),
    # Noun-phrase fallbacks for alt/caption/metadata variants that do not carry
    # a locating preposition.
    ("the Playa del Arco fossil dune", "the fossil dunes at Playa del Arco"),
    ("the Los Escullos fossil dune", "the fossil dunes of Los Escullos"),
    ("the same fossil dune", "the same fossil dunes"),
    ("la duna fósil de la Playa del Arco", "las dunas fósiles de la Playa del Arco"),
    ("la duna fósil de Los Escullos", "las dunas fósiles de Los Escullos"),
    ("la misma duna fósil", "las mismas dunas fósiles"),
)

changed: set[str] = set()
for path in sorted(ROOT.rglob("*.html")):
    rel = path.relative_to(ROOT).as_posix()
    if rel in GEOLOGY_EXEMPT:
        continue
    text = path.read_text(encoding="utf-8")
    before = text
    for old, new in REPLACEMENTS:
        text = text.replace(old, new)
    if text != before:
        path.write_text(text, encoding="utf-8")
        changed.add(rel)
        print(f"fossil-dune location corrected: {rel}")

# No singular fossil-dune location wording may survive outside the dedicated
# geology explainer pages. This catches hidden metadata, JSON-LD, alt text and
# future copy variants rather than only the paragraphs visible in screenshots.
stragglers: list[str] = []
for path in sorted(ROOT.rglob("*.html")):
    rel = path.relative_to(ROOT).as_posix()
    if rel in GEOLOGY_EXEMPT:
        continue
    text = path.read_text(encoding="utf-8")
    for pattern, label in (
        (r"\bfossil[ -]dune\b(?!s)", "fossil dune"),
        (r"\bduna fósil\b(?!es)", "duna fósil"),
    ):
        match = re.search(pattern, text, flags=re.I)
        if match:
            start = max(0, match.start() - 90)
            end = min(len(text), match.end() + 120)
            context = re.sub(r"\s+", " ", text[start:end]).strip()
            stragglers.append(f"{rel}: {label}: {context}")

if stragglers:
    print("Incorrect singular fossil-dune wording remains outside the geology pages:")
    print("\n".join(stragglers))
    raise SystemExit(1)

# Every corrected English page must use the approved location wording rather
# than merely deleting the incorrect statement.
for rel in sorted(changed):
    if rel.startswith("en/"):
        text = (ROOT / rel).read_text(encoding="utf-8")
        if "fossil dunes" in text.lower() and "beside the fossil dunes" not in text.lower():
            raise SystemExit(f"English location wording lacks approved 'beside the fossil dunes' phrase: {rel}")

# Mark corrected public routes fresh for search engines and the existing
# IndexNow submission step.
def route_for_html(rel: str) -> str:
    if rel == "index.html":
        return "/"
    if rel.endswith("/index.html"):
        return "/" + rel[: -len("index.html")]
    return "/" + rel

sitemap = ROOT / "sitemap.xml"
if not sitemap.is_file():
    raise SystemExit("Missing sitemap.xml")
ET.register_namespace("", "http://www.sitemaps.org/schemas/sitemap/0.9")
tree = ET.parse(sitemap)
root = tree.getroot()
ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
changed_routes = {route_for_html(rel) for rel in changed}
seen_routes: set[str] = set()
for url_el in root.findall("sm:url", ns):
    loc = url_el.find("sm:loc", ns)
    if loc is None or not loc.text:
        continue
    url = loc.text.strip()
    if not url.startswith(BASE):
        continue
    route = url[len(BASE):] or "/"
    if route not in changed_routes:
        continue
    seen_routes.add(route)
    lastmod = url_el.find("sm:lastmod", ns)
    if lastmod is None:
        lastmod = ET.SubElement(url_el, "{http://www.sitemaps.org/schemas/sitemap/0.9}lastmod")
    lastmod.text = LASTMOD
if changed_routes:
    tree.write(sitemap, encoding="utf-8", xml_declaration=True)

# Static internal-href gate: reject links to routes/assets that are not present
# in the final Pages bundle. API endpoints and same-page fragments are dynamic
# or fragment-only and are intentionally excluded.
HREF_RE = re.compile(r"\bhref\s*=\s*([\"'])(.*?)\1", flags=re.I | re.S)
INTERNAL_HOSTS = {"oolita.es", "www.oolita.es"}
missing_hrefs: list[str] = []


def resolve_internal_href(current_rel: str, href: str) -> Path | None:
    href = href.strip()
    if not href or href.startswith("#"):
        return None
    parsed = urlsplit(href)
    if parsed.scheme and parsed.scheme.lower() not in {"http", "https"}:
        return None
    if parsed.netloc and parsed.netloc.lower() not in INTERNAL_HOSTS:
        return None
    if parsed.scheme.lower() in {"http", "https"} and parsed.netloc.lower() not in INTERNAL_HOSTS:
        return None
    raw_path = unquote(parsed.path or "/")
    if raw_path.startswith("/api/"):
        return None
    if raw_path.startswith("/"):
        rel_path = raw_path.lstrip("/")
    else:
        base_dir = posixpath.dirname(current_rel)
        rel_path = posixpath.normpath(posixpath.join(base_dir, raw_path))
        if rel_path == ".":
            rel_path = ""
        if rel_path == ".." or rel_path.startswith("../"):
            return ROOT / "__outside_site__"

    candidate = ROOT / rel_path
    if raw_path.endswith("/") or not rel_path:
        return candidate / "index.html"
    if candidate.is_file():
        return candidate
    if Path(rel_path).suffix:
        return candidate
    return candidate / "index.html"


for page in sorted(ROOT.rglob("*.html")):
    current_rel = page.relative_to(ROOT).as_posix()
    text = page.read_text(encoding="utf-8")
    for match in HREF_RE.finditer(text):
        href = match.group(2)
        target = resolve_internal_href(current_rel, href)
        if target is None:
            continue
        if not target.is_file():
            missing_hrefs.append(f"{current_rel}: {href} -> {target.relative_to(ROOT) if target.is_relative_to(ROOT) else target}")

if missing_hrefs:
    print("Broken internal hrefs found in final deployment bundle:")
    print("\n".join(sorted(set(missing_hrefs))))
    raise SystemExit(1)

print(
    f"OOLITA labyrinth location normalized on {len(changed)} page(s); "
    f"{len(seen_routes)} sitemap route(s) refreshed; internal href gate passed."
)
