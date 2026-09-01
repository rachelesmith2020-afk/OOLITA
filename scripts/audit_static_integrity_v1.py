#!/usr/bin/env python3
"""Fail-closed static integrity audit for the final OOLITA Pages bundle.

Checks the things that should never reach production:
- sitemap URLs without a built file;
- sitemap pages without one matching canonical;
- broken first-party anchors/hrefs after stripping query/fragment;
- first-party hreflang targets that do not exist;
- the retired /reels/ route still linked from reader-facing HTML;
- the bilingual geology pair losing its reciprocal language links;
- known fossil-dune grammar/location stragglers on principal pages.

External URLs are not crawled here; the live SEO audit handles network behaviour.
"""
from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlsplit
import re
import runpy
import sys
import xml.etree.ElementTree as ET

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
BASE = "https://oolita.es"
HOSTS = {"oolita.es", "www.oolita.es"}

if not ROOT.is_dir():
    raise SystemExit(f"Missing built site: {ROOT}")

# The textile choice is a final public product fact, so apply it immediately
# before every integrity audit. This audit runs both during reconstruction and
# again at the end of the production pipeline; the second run ensures later SEO
# or editorial passes cannot restore the former oversized-only page.
textile_script = Path(__file__).resolve().parent / "apply_textile_variants_v1.py"
if not textile_script.is_file():
    raise SystemExit(f"Missing textile variants layer: {textile_script}")
old_argv = sys.argv[:]
sys.argv = [str(textile_script), str(ROOT)]
try:
    runpy.run_path(str(textile_script), run_name="__main__")
finally:
    sys.argv = old_argv


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.hrefs: list[str] = []
        self.canonicals: list[str] = []
        self.alternates: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        data = {k.lower(): (v or "") for k, v in attrs}
        tag = tag.lower()
        if tag == "a" and data.get("href"):
            self.hrefs.append(data["href"].strip())
        if tag == "link" and data.get("href"):
            rel = {part.lower() for part in data.get("rel", "").split()}
            if "canonical" in rel:
                self.canonicals.append(data["href"].strip())
            if "alternate" in rel and data.get("hreflang"):
                self.alternates.append((data["hreflang"].strip().lower(), data["href"].strip()))


def normalize_route(path: str) -> str:
    path = re.sub(r"/+", "/", path or "/")
    if not path.startswith("/"):
        path = "/" + path
    return path


def file_for_route(path: str) -> Path:
    path = normalize_route(path)
    if path == "/":
        return ROOT / "index.html"
    rel = path.lstrip("/")
    candidate = ROOT / rel
    if path.endswith("/"):
        return candidate / "index.html"
    if Path(path).suffix:
        return candidate
    return candidate / "index.html"


def route_for_html(path: Path) -> str:
    rel = path.relative_to(ROOT).as_posix()
    if rel == "index.html":
        return "/"
    if rel.endswith("/index.html"):
        return "/" + rel.removesuffix("index.html")
    return "/" + rel


def first_party_path(href: str, page_url: str) -> str | None:
    if not href or href.startswith("#"):
        return None
    parsed = urlsplit(href)
    if parsed.scheme.lower() in {"mailto", "tel", "sms", "data", "javascript"}:
        return None
    if parsed.scheme and parsed.scheme.lower() not in {"http", "https"}:
        return None
    if parsed.netloc and parsed.netloc.lower() not in HOSTS:
        return None
    absolute = urlsplit(urljoin(page_url, href))
    if absolute.netloc and absolute.netloc.lower() not in HOSTS:
        return None
    return normalize_route(absolute.path or "/")


# Redirect sources are valid historical entry points, but reader-facing links
# should not deliberately point at the retired Reels route.
redirect_sources: set[str] = set()
redirect_file = ROOT / "_redirects"
if redirect_file.is_file():
    for raw in redirect_file.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if parts and parts[0].startswith("/") and "*" not in parts[0]:
            redirect_sources.add(normalize_route(parts[0]))


# Sitemap is the source of truth for indexable public pages.
sitemap = ROOT / "sitemap.xml"
if not sitemap.is_file():
    raise SystemExit("Missing sitemap.xml")
ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
tree = ET.parse(sitemap)
locs: list[str] = []
for loc in tree.getroot().findall("sm:url/sm:loc", ns):
    if loc.text:
        locs.append(loc.text.strip())
if not locs:
    raise SystemExit("No URLs in sitemap.xml")

errors: list[str] = []
parsers: dict[str, PageParser] = {}

for loc in locs:
    parsed = urlsplit(loc)
    if parsed.scheme != "https" or parsed.netloc.lower() != "oolita.es":
        errors.append(f"Non-canonical sitemap host/scheme: {loc}")
        continue
    route = normalize_route(parsed.path or "/")
    file = file_for_route(route)
    if not file.is_file():
        errors.append(f"Sitemap 404 candidate: {loc} -> {file.relative_to(ROOT)}")
        continue
    if file.suffix.lower() != ".html":
        continue
    parser = PageParser()
    parser.feed(file.read_text(encoding="utf-8", errors="strict"))
    parsers[route] = parser

    expected_canonical = BASE + route
    if len(parser.canonicals) != 1:
        errors.append(f"Canonical count {len(parser.canonicals)} on {route}")
    elif parser.canonicals[0] != expected_canonical:
        errors.append(
            f"Canonical mismatch on {route}: {parser.canonicals[0]!r} != {expected_canonical!r}"
        )


# Check every built reader-facing HTML file, not only sitemap pages, for local
# link integrity. 404 itself is allowed to have recovery links but is not a target.
html_files = sorted({p for p in ROOT.rglob("*.html") if p.is_file()})
checked_hrefs = 0
for file in html_files:
    route = route_for_html(file)
    page_url = BASE + route
    parser = PageParser()
    parser.feed(file.read_text(encoding="utf-8", errors="strict"))

    for href in parser.hrefs:
        target = first_party_path(href, page_url)
        if target is None or target.startswith("/api/"):
            continue
        checked_hrefs += 1
        if target == "/reels" or target.startswith("/reels/"):
            errors.append(f"Retired Reels href survives in {route}: {href}")
            continue
        candidate = file_for_route(target)
        if not candidate.is_file() and target not in redirect_sources:
            errors.append(f"Broken first-party href in {route}: {href} -> {target}")

    for lang, href in parser.alternates:
        target = first_party_path(href, page_url)
        if target is None:
            continue
        candidate = file_for_route(target)
        if not candidate.is_file():
            errors.append(f"Broken hreflang {lang} in {route}: {href} -> {target}")


# The geology pair is strategically important and must remain reciprocally paired.
def alternates_for(route: str) -> dict[str, str]:
    parser = parsers.get(route)
    if parser is None:
        errors.append(f"Geology route absent from sitemap/parser set: {route}")
        return {}
    return {lang: href for lang, href in parser.alternates}

es_route = "/que-es-un-oolito/"
en_route = "/en/what-is-an-ooid/"
es_alts = alternates_for(es_route)
en_alts = alternates_for(en_route)
expected_pairs = (
    (es_route, es_alts, "es", BASE + es_route),
    (es_route, es_alts, "en", BASE + en_route),
    (en_route, en_alts, "es", BASE + es_route),
    (en_route, en_alts, "en", BASE + en_route),
)
for route, mapping, lang, expected in expected_pairs:
    if mapping.get(lang) != expected:
        errors.append(
            f"Geology hreflang mismatch on {route}: {lang}={mapping.get(lang)!r}, expected {expected!r}"
        )


# Final known-straggler scan on principal project pages. Legitimate geological
# descriptions on the ooid pages are intentionally not treated as labyrinth claims.
principal = (
    "index.html",
    "en/index.html",
    "laberinto/index.html",
    "en/labyrinth/index.html",
    "sobre-oolita/index.html",
    "en/about/index.html",
    "cabo-de-gata/index.html",
    "en/cabo-de-gata/index.html",
)
for rel in principal:
    file = ROOT / rel
    if not file.is_file():
        errors.append(f"Missing principal page: {rel}")
        continue
    text = file.read_text(encoding="utf-8")
    for bad in (
        "stands on a fossil dunes",
        "stand on a fossil dunes",
        "the labyrinth sits on a fossil dune",
        "the labyrinth stands on a fossil dune",
        "el laberinto se asienta sobre una duna fósil",
        "el laberinto está sobre una duna fósil",
        "loose calcarenite",
        "calcarenita suelta",
    ):
        if bad.lower() in text.lower():
            errors.append(f"Known factual/grammar straggler in {rel}: {bad}")

if errors:
    print("OOLITA static integrity audit failed:")
    for item in errors:
        print(f"- {item}")
    raise SystemExit(1)

print(
    f"OOLITA static integrity passed: {len(locs)} sitemap URLs, "
    f"{len(html_files)} HTML files, {checked_hrefs} first-party hrefs checked; "
    "canonicals and geology hreflang pair valid; no known stragglers."
)
