#!/usr/bin/env python3
"""Final factual/SEO gate for OOLITA labyrinth location, stone wording and hrefs.

Approved facts:
- the labyrinth is on land beside the fossil dunes;
- the nearby Batería de San Felipe stands on a fossil dune;
- the labyrinth material is described as loose stones, not calcarenite.

The pass is deliberately idempotent because production rebuilds start from the
current live Pages origin. It updates sitemap freshness for changed routes and
rejects factual, grammar and internal-href stragglers before deployment.
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
LASTMOD = "2026-08-25"

if not ROOT.is_dir():
    raise SystemExit(f"Missing built site: {ROOT}")

GEOLOGY_EXEMPT = {
    "que-es-un-oolito/index.html",
    "en/what-is-an-ooid/index.html",
}

# Literal location corrections. Keep these specific and idempotent: never use a
# singular->plural substring replacement that can turn "dunes" into "duness".
LITERAL_LOCATION_REPLACEMENTS = (
    (
        "stands on the same fossil dune that names the labyrinth: stone that was once sea",
        "stands on a fossil dune",
    ),
    (
        "se levanta sobre la misma duna fósil que da nombre al laberinto: piedra que fue mar",
        "se levanta sobre una duna fósil",
    ),
    (
        "on a fossil dune that was seabed a hundred thousand years ago",
        "on land beside the fossil dunes, ground that was seabed a hundred thousand years ago",
    ),
    (
        "sobre una duna fósil que hace cien mil años fue fondo del mar",
        "en terreno junto a las dunas fósiles, terreno que hace cien mil años fue fondo del mar",
    ),
    ("on the Playa del Arco fossil dune", "on land beside the fossil dunes"),
    ("on the Los Escullos fossil dune", "on land beside the fossil dunes"),
    ("on the fossil dune", "on land beside the fossil dunes"),
    ("sobre la duna fósil de la Playa del Arco", "en terreno junto a las dunas fósiles"),
    ("sobre la duna fósil de Los Escullos", "en terreno junto a las dunas fósiles"),
    ("sobre la duna fósil", "en terreno junto a las dunas fósiles"),
    ("Piedras sueltas sobre duna fósil", "Piedras sueltas en terreno junto a las dunas fósiles"),
    ("piedras sueltas sobre duna fósil", "piedras sueltas en terreno junto a las dunas fósiles"),
    ("Loose stones on a fossil dune", "Loose stones on land beside the fossil dunes"),
    ("loose stones on a fossil dune", "loose stones on land beside the fossil dunes"),
    ('<span class="k">Ground</span><span class="v">Fossil dune · Playa del Arco</span>',
     '<span class="k">Ground</span><span class="v">Land beside the fossil dunes · Playa del Arco</span>'),
    ('<span class="k">Terreno</span><span class="v">Duna fósil · Playa del Arco</span>',
     '<span class="k">Terreno</span><span class="v">Terreno junto a las dunas fósiles · Playa del Arco</span>'),
)

MATERIAL_REPLACEMENTS = (
    ("Loose calcarenite", "Loose stones"),
    ("loose calcarenite", "loose stones"),
    ("Calcarenita suelta", "Piedras sueltas"),
    ("calcarenita suelta", "piedras sueltas"),
)

ANCHOR_LOCATION_REPLACEMENTS = (
    (
        re.compile(
            r'on a\s+(<a\b[^>]*>)\s*fossil[ -]dune\s*(</a>)\s+that was seabed a hundred thousand years ago',
            re.I,
        ),
        r'on land beside the \1fossil dunes\2, ground that was seabed a hundred thousand years ago',
    ),
    (
        re.compile(
            r'sobre una\s+(<a\b[^>]*>)\s*duna fósil\s*(</a>)\s+que hace cien mil años fue fondo del mar',
            re.I,
        ),
        r'en terreno junto a las \1dunas fósiles\2, terreno que hace cien mil años fue fondo del mar',
    ),
)


def repair_battery_context(text: str) -> str:
    """Restore the singular San Felipe fact only when the battery is named."""
    english_variants = (
        "stands beside the same fossil dunes",
        "stands on the same fossil dunes",
        "stands on land beside the fossil dunes",
        "stands on a fossil dunes",
        "stands on a fossil duness",
        "stands on a fossil dune",
    )
    spanish_variants = (
        "se levanta junto a las mismas dunas fósiles",
        "se levanta sobre las mismas dunas fósiles",
        "se levanta en terreno junto a las dunas fósiles",
        "se levanta sobre una dunas fósiles",
        "se levanta sobre una duna fósil",
    )
    for old in english_variants:
        pattern = re.compile(
            rf"(Bater[ií]a de San Felipe.{{0,320}}?){re.escape(old)}",
            re.I | re.S,
        )
        text = pattern.sub(lambda m: m.group(1) + "stands on a fossil dune", text)
    for old in spanish_variants:
        pattern = re.compile(
            rf"(Bater[ií]a de San Felipe.{{0,320}}?){re.escape(old)}",
            re.I | re.S,
        )
        text = pattern.sub(lambda m: m.group(1) + "se levanta sobre una duna fósil", text)
    return text


def normalize_non_geology_page(text: str) -> str:
    # Repair malformed output from the previous non-idempotent plural pass first.
    text = text.replace("fossil duness", "fossil dunes")
    text = text.replace("a fossil dunes", "a fossil dune")
    text = text.replace("dunas fósiless", "dunas fósiles")
    text = text.replace("una dunas fósiles", "una duna fósil")

    for old, new in MATERIAL_REPLACEMENTS:
        text = text.replace(old, new)
    for old, new in LITERAL_LOCATION_REPLACEMENTS:
        text = text.replace(old, new)
    for pattern, replacement in ANCHOR_LOCATION_REPLACEMENTS:
        text = pattern.sub(replacement, text)

    # Safe word-boundary fallbacks for noun phrases and material labels.
    text = re.sub(r"\bthe same fossil dune\b(?!s)", "the same fossil dunes", text, flags=re.I)
    text = re.sub(r"\bthe Playa del Arco fossil dune\b", "the fossil dunes at Playa del Arco", text, flags=re.I)
    text = re.sub(r"\bthe Los Escullos fossil dune\b", "the fossil dunes of Los Escullos", text, flags=re.I)
    text = re.sub(r"\bloose stone\b(?!s)", "loose stones", text, flags=re.I)
    text = re.sub(r"\bpiedra suelta\b", "piedras sueltas", text, flags=re.I)

    # Generic singular location claims for the labyrinth/work. The San Felipe
    # statement is restored contextually afterwards.
    text = re.sub(r"\bon a fossil[ -]dune\b(?!s)", "on land beside the fossil dunes", text, flags=re.I)
    text = re.sub(r"\bsobre una duna fósil\b(?!es)", "en terreno junto a las dunas fósiles", text, flags=re.I)

    text = re.sub(
        r'("artworkSurface"\s*:\s*")Fossil[ -]dune("\s*)',
        r'\1Land beside the fossil dunes\2',
        text,
        flags=re.I,
    )
    text = re.sub(
        r'("artworkSurface"\s*:\s*")Duna fósil("\s*)',
        r'\1Terreno junto a las dunas fósiles\2',
        text,
        flags=re.I,
    )

    return repair_battery_context(text)


changed: set[str] = set()
for path in sorted(ROOT.rglob("*.html")):
    rel = path.relative_to(ROOT).as_posix()
    text = path.read_text(encoding="utf-8")
    before = text

    # Material wording is global, including the geology explainers. Location
    # normalization is skipped on the dedicated geology pages themselves.
    for old, new in MATERIAL_REPLACEMENTS:
        text = text.replace(old, new)
    text = re.sub(r"\bloose stone\b(?!s)", "loose stones", text, flags=re.I)
    text = re.sub(r"\bpiedra suelta\b", "piedras sueltas", text, flags=re.I)
    if rel not in GEOLOGY_EXEMPT:
        text = normalize_non_geology_page(text)

    if text != before:
        path.write_text(text, encoding="utf-8")
        changed.add(rel)
        print(f"labyrinth factual wording normalized: {rel}")

# Global material and grammar straggler gates.
stragglers: list[str] = []
for path in sorted(ROOT.rglob("*.html")):
    rel = path.relative_to(ROOT).as_posix()
    text = path.read_text(encoding="utf-8")
    checks = (
        (r"\bloose\s+calcarenite\b", "loose calcarenite"),
        (r"\bcalcarenita\s+suelta\b", "calcarenita suelta"),
        (r"\ba\s+fossil[ -]dunes\b", "a fossil dunes"),
        (r"\bfossil[ -]duness\b", "fossil duness"),
        (r"\buna\s+dunas\s+fósiles\b", "una dunas fósiles"),
        (r"\bdunas\s+fósiless\b", "dunas fósiless"),
    )
    for pattern, label in checks:
        match = re.search(pattern, text, flags=re.I)
        if match:
            start = max(0, match.start() - 100)
            end = min(len(text), match.end() + 140)
            context = re.sub(r"\s+", " ", text[start:end]).strip()
            stragglers.append(f"{rel}: {label}: {context}")

if stragglers:
    print("Disallowed material/grammar stragglers remain:")
    print("\n".join(stragglers))
    raise SystemExit(1)

# Validate explicit location claims. A singular fossil dune may be discussed
# geologically, but outside the geology explainers the only allowed placement
# claim is the named San Felipe battery statement.
location_stragglers: list[str] = []
allowed_battery_patterns = (
    re.compile(r"Bater[ií]a de San Felipe.{0,320}?stands on a fossil[ -]dune(?!s)", re.I | re.S),
    re.compile(r"Bater[ií]a de San Felipe.{0,320}?se levanta sobre una duna fósil(?!es)", re.I | re.S),
)
BAD_LOCATION_PATTERNS = (
    (re.compile(r"\b(?:stands|sits|lies|is|laid|built|placed|occupies)\s+on\s+(?:an?\s+)?(?:<[^>]+>\s*)*fossil[ -]dune\b(?!s)", re.I | re.S), "English on-fossil-dune location claim"),
    (re.compile(r"\bon\s+(?:an?\s+)?(?:<[^>]+>\s*)*fossil[ -]dune\b(?!s)", re.I | re.S), "English on-fossil-dune location claim"),
    (re.compile(r"\b(?:se encuentra|se sitúa|está|ocupa|se levanta|fue colocado)\s+sobre\s+(?:una?\s+|la\s+)?(?:<[^>]+>\s*)*duna fósil\b(?!es)", re.I | re.S), "Spanish sobre-duna-fósil location claim"),
    (re.compile(r"\bsobre\s+(?:una?\s+|la\s+)?(?:<[^>]+>\s*)*duna fósil\b(?!es)", re.I | re.S), "Spanish sobre-duna-fósil location claim"),
    (re.compile(r'"artworkSurface"\s*:\s*"Fossil[ -]dune"', re.I), "English artworkSurface location claim"),
    (re.compile(r'"artworkSurface"\s*:\s*"Duna fósil"', re.I), "Spanish artworkSurface location claim"),
)

for path in sorted(ROOT.rglob("*.html")):
    rel = path.relative_to(ROOT).as_posix()
    if rel in GEOLOGY_EXEMPT:
        continue
    text = path.read_text(encoding="utf-8")
    allowed_spans: list[tuple[int, int]] = []
    for pattern in allowed_battery_patterns:
        allowed_spans.extend((m.start(), m.end()) for m in pattern.finditer(text))
    for pattern, label in BAD_LOCATION_PATTERNS:
        for match in pattern.finditer(text):
            if any(start <= match.start() < end for start, end in allowed_spans):
                continue
            start = max(0, match.start() - 100)
            end = min(len(text), match.end() + 140)
            context = re.sub(r"\s+", " ", text[start:end]).strip()
            location_stragglers.append(f"{rel}: {label}: {context}")

if location_stragglers:
    print("Incorrect labyrinth fossil-dune location wording remains:")
    print("\n".join(location_stragglers))
    raise SystemExit(1)

# Exact reader-facing invariants for the two labyrinth pages.
required_page_copy = {
    "en/labyrinth/index.html": (
        "on land beside the fossil dunes",
        "Batería de San Felipe",
        "stands on a fossil dune",
        "loose stones",
    ),
    "laberinto/index.html": (
        "en terreno junto a las dunas fósiles",
        "Batería de San Felipe",
        "se levanta sobre una duna fósil",
        "piedras sueltas",
    ),
}
for rel, required in required_page_copy.items():
    path = ROOT / rel
    if not path.is_file():
        raise SystemExit(f"Missing required labyrinth page: {rel}")
    lower = path.read_text(encoding="utf-8").lower()
    for phrase in required:
        if phrase.lower() not in lower:
            raise SystemExit(f"Required final copy missing from {rel}: {phrase}")

# Mark corrected public routes fresh for search engines and IndexNow.
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

# Static internal-href gate: reject links to routes/assets absent from the final
# Pages bundle. API endpoints and same-page fragments are dynamic/fragment-only.
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
            missing_hrefs.append(
                f"{current_rel}: {href} -> "
                f"{target.relative_to(ROOT) if target.is_relative_to(ROOT) else target}"
            )

if missing_hrefs:
    print("Broken internal hrefs found in final deployment bundle:")
    print("\n".join(sorted(set(missing_hrefs))))
    raise SystemExit(1)

print(
    f"OOLITA labyrinth wording normalized on {len(changed)} page(s); "
    f"{len(seen_routes)} sitemap route(s) refreshed; "
    "material/grammar/location straggler gates and internal href gate passed."
)
