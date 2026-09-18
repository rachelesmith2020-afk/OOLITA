#!/usr/bin/env python3
"""Retire the obsolete 22-Sundays / 3-January campaign from the built OOLITA site.

This is a final deployment layer. Older historical build scripts may still contain
the former campaign for reconstruction compatibility, but nothing reader-facing
may ship with that chronology or its routes.

Current public calendar:
- 3D world + book pre-orders + full in-world book: 23 May 2027, 00:00 CEST
- Book general sale: 27 June 2027
- First textile edition: 25 July 2027
- Hallazgo hardback: 16 September 2027
- Hallazgo presentation: 19 September 2027
"""
from __future__ import annotations

from pathlib import Path
import re
import shutil
import sys
import xml.etree.ElementTree as ET

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
if not ROOT.is_dir():
    raise SystemExit(f"Missing built site: {ROOT}")

TEXT_SUFFIXES = {".html", ".xml", ".json", ".js", ".css", ".txt"}

DATE_REPLACEMENTS = (
    ("2027-01-03T00:00:00+01:00", "2027-05-23T00:00:00+02:00"),
    ("2027-01-03", "2027-05-23"),
    ("03.01.2027", "23.05.2027"),
    ("03.01.27", "23.05.27"),
    ("03 JAN 27", "23 MAY 27"),
    ("03 ENE 27", "23 MAY 27"),
    ("3 Jan 2027", "23 May 2027"),
    ("3 Jan 27", "23 May 27"),
    ("3 January 2027", "23 May 2027"),
    ("3 January", "23 May"),
    ("3 de enero de 2027", "23 de mayo de 2027"),
    ("3 de enero", "23 de mayo"),
    ("2027-01-31T00:00:00+01:00", "2027-06-27T00:00:00+02:00"),
    ("2027-01-31T00:00:00Z", "2027-06-27T00:00:00+02:00"),
    ("2027-01-31", "2027-06-27"),
    ("31.01.2027", "27.06.2027"),
    ("31.01.27", "27.06.27"),
    ("31 JAN 27", "27 JUN 27"),
    ("31 ENE 27", "27 JUN 27"),
    ("31 Jan 2027", "27 Jun 2027"),
    ("31 Jan 27", "27 Jun 27"),
    ("31 January 2027", "27 June 2027"),
    ("31 January", "27 June"),
    ("31 de enero de 2027", "27 de junio de 2027"),
    ("31 de enero", "27 de junio"),
    ("2027-04-11T00:00:00+02:00", "2027-07-25T00:00:00+02:00"),
    ("2027-04-11", "2027-07-25"),
    ("11.04.2027", "25.07.2027"),
    ("11.04.27", "25.07.27"),
    ("11 APR 27", "25 JUL 27"),
    ("11 ABR 27", "25 JUL 27"),
    ("11 Apr 2027", "25 Jul 2027"),
    ("11 Apr 27", "25 Jul 27"),
    ("11 April 2027", "25 July 2027"),
    ("11 April", "25 July"),
    ("11 de abril de 2027", "25 de julio de 2027"),
    ("11 de abril", "25 de julio"),
    ("00:00 CET", "00:00 CEST"),
)

# Campaign-specific phrases that identify a whole block as obsolete.
CAMPAIGN_MARKERS = (
    "22 Sundays",
    "22 SUNDAYS",
    "22 domingos",
    "22 DOMINGOS",
    "twenty-two Sundays",
    "veintidós domingos",
    "The path, one Sunday at a time",
    "El camino, domingo a domingo",
    "one image every Sunday",
    "una imagen cada domingo",
    "archive grows each Sunday",
    "archivo crece cada domingo",
    "/en/sundays/",
    "/domingos/",
)

# Safe copy substitutions where the containing block should remain.
COPY_REPLACEMENTS = (
    ("Seguir el camino hasta el 3 de enero", "Entrar el 23 de mayo"),
    ("Follow the path to 3 January", "Enter on 23 May"),
    ("@oolita.es · una imagen cada domingo ↗", "@oolita.es ↗"),
    ("@oolita.es · one image every Sunday ↗", "@oolita.es ↗"),
    ("Los nueve carteles de la apertura de la cuenta", "La serie de carteles de OOLITA"),
    ("The nine posters that opened the account", "The OOLITA poster series"),
    ("Los nueve carteles — la apertura de OOLITA", "Los carteles — piedra, papel y código"),
    ("The nine posters — the opening of OOLITA", "The posters — stone, paper and code"),
    ("nueve carteles", "la serie de carteles"),
    ("nine posters", "the poster series"),
)

ROUTE_RE = re.compile(r'''href=(["'])(?:https://oolita\.es)?/(?:en/sundays|domingos)(?:/[^"']*)?\1''', re.I)
ANCHOR_RE = re.compile(r'<a\b[^>]*>.*?</a>', re.I | re.S)
SECTION_RE = re.compile(r'<section\b[^>]*>.*?</section>', re.I | re.S)
ARTICLE_RE = re.compile(r'<article\b[^>]*>.*?</article>', re.I | re.S)
FIGURE_RE = re.compile(r'<figure\b[^>]*>.*?</figure>', re.I | re.S)
LI_RE = re.compile(r'<li\b[^>]*>.*?</li>', re.I | re.S)
INLINE_RE = re.compile(r'<(?:p|span|h1|h2|h3|h4)\b[^>]*>.*?</(?:p|span|h1|h2|h3|h4)>', re.I | re.S)
TAG_RE = re.compile(r'<[^>]+>', re.S)


def has_campaign(block: str) -> bool:
    plain = TAG_RE.sub(" ", block)
    return any(marker.lower() in (block + " " + plain).lower() for marker in CAMPAIGN_MARKERS)


def remove_matching(pattern: re.Pattern[str], text: str) -> str:
    while True:
        changed = False
        def repl(match: re.Match[str]) -> str:
            nonlocal changed
            block = match.group(0)
            if has_campaign(block):
                changed = True
                return ""
            return block
        new = pattern.sub(repl, text)
        text = new
        if not changed:
            return text


def patch_html(rel: str, text: str) -> str:
    original = text

    # Poster 03 contains the retired campaign in the image itself. Remove that
    # card before general text substitutions, so the baked "22 Sundays" artwork
    # is not published.
    if rel in {"carteles/index.html", "en/posters/index.html"}:
        for pattern in (ARTICLE_RE, FIGURE_RE, LI_RE):
            text = remove_matching(pattern, text)

    # Remove dedicated campaign sections and links anywhere else.
    text = remove_matching(SECTION_RE, text)
    text = remove_matching(ARTICLE_RE, text)

    def drop_route_anchor(match: re.Match[str]) -> str:
        block = match.group(0)
        return "" if ROUTE_RE.search(block) else block
    text = ANCHOR_RE.sub(drop_route_anchor, text)

    # Remove remaining small campaign labels/captions, but preserve unrelated
    # paragraphs that merely contain a newly corrected release date.
    text = remove_matching(INLINE_RE, text)

    for old, new in COPY_REPLACEMENTS:
        text = text.replace(old, new)
    for old, new in DATE_REPLACEMENTS:
        text = text.replace(old, new)

    # Clean gaps created by retired navigation rows.
    text = re.sub(r'\n{3,}', '\n\n', text)

    if text != original:
        return text
    return original


changed: list[str] = []
for path in sorted(ROOT.rglob("*")):
    if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
        continue
    rel = path.relative_to(ROOT).as_posix()
    text = path.read_text(encoding="utf-8", errors="ignore")
    new = patch_html(rel, text) if path.suffix.lower() == ".html" else text
    for old, replacement in DATE_REPLACEMENTS:
        new = new.replace(old, replacement)
    for old, replacement in COPY_REPLACEMENTS:
        new = new.replace(old, replacement)
    if new != text:
        path.write_text(new, encoding="utf-8")
        changed.append(rel)

# The campaign archive itself is retired, not left as an orphan.
shutil.rmtree(ROOT / "domingos", ignore_errors=True)
shutil.rmtree(ROOT / "en" / "sundays", ignore_errors=True)

# Poster 03 is the baked "22 Sundays" artwork. Remove its public image encodings.
for asset in (ROOT / "carteles" / "img").glob("cartel-03.*"):
    if asset.is_file():
        asset.unlink()
        changed.append(asset.relative_to(ROOT).as_posix())

# Remove retired routes from the sitemap.
sitemap = ROOT / "sitemap.xml"
if sitemap.is_file():
    ET.register_namespace("", "http://www.sitemaps.org/schemas/sitemap/0.9")
    tree = ET.parse(sitemap)
    root = tree.getroot()
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    removed = 0
    for url_el in list(root.findall("sm:url", ns)):
        loc = url_el.find("sm:loc", ns)
        value = (loc.text or "") if loc is not None else ""
        if "/domingos/" in value or "/en/sundays/" in value:
            root.remove(url_el)
            removed += 1
    tree.write(sitemap, encoding="utf-8", xml_declaration=True)
    if removed:
        changed.append("sitemap.xml")

# Old URLs resolve cleanly to the current language home rather than surviving as
# a discoverable archive.
redirects = ROOT / "_redirects"
existing = redirects.read_text(encoding="utf-8") if redirects.is_file() else ""
rules = (
    "/domingos / 301",
    "/domingos/ / 301",
    "/domingos/* / 301",
    "/en/sundays /en/ 301",
    "/en/sundays/ /en/ 301",
    "/en/sundays/* /en/ 301",
)
lines = [line for line in existing.splitlines() if line.strip()]
for rule in rules:
    if rule not in lines:
        lines.append(rule)
redirects.write_text("\n".join(lines) + "\n", encoding="utf-8")

# Final fail-closed sweep. These tokens must not be public anywhere in the build.
BANNED = (
    "22 Sundays", "22 SUNDAYS", "22 domingos", "22 DOMINGOS",
    "/domingos/", "/en/sundays/",
    "03.01.2027", "03.01.27", "03 JAN 27", "03 ENE 27",
    "3 January", "3 de enero", "2027-01-03",
    "31.01.2027", "31.01.27", "31 JAN 27", "31 ENE 27",
    "31 January", "31 de enero", "2027-01-31",
    "11.04.2027", "11.04.27", "11 APR 27", "11 ABR 27",
    "11 April", "11 de abril", "2027-04-11",
)

leaks: list[str] = []
for path in sorted(ROOT.rglob("*")):
    if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
        continue
    rel = path.relative_to(ROOT).as_posix()
    text = path.read_text(encoding="utf-8", errors="ignore")
    for token in BANNED:
        if token in text:
            leaks.append(f"{rel}: {token}")

for route in ("domingos", "en/sundays"):
    if (ROOT / route).exists():
        leaks.append(f"{route}/ still exists")

for rel in ("index.html", "en/index.html"):
    page = ROOT / rel
    if not page.is_file():
        leaks.append(f"{rel}: homepage missing")
        continue
    text = page.read_text(encoding="utf-8")
    if "00:00 CEST" not in text:
        leaks.append(f"{rel}: countdown timezone is not CEST")
    if not any(token in text for token in ("23.05.2027", "23 May 2027", "23 de mayo de 2027")):
        leaks.append(f"{rel}: 23 May 2027 countdown date missing")

if leaks:
    print("OOLITA campaign retirement failed:")
    for item in leaks:
        print(f"- {item}")
    raise SystemExit(1)

print(
    "OOLITA obsolete campaign retired: Sunday archive/routes removed, poster 03 "
    "withdrawn, old launch dates replaced, countdown aligned to 23 May 2027 "
    "00:00 CEST, sitemap/redirects cleaned, and final residue guard passed."
)
print(f"Changed/removed artifacts: {len(set(changed))}")
