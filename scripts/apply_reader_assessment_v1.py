#!/usr/bin/env python3
"""Apply the 23 August 2026 reader-assessment priority fixes.

This pass deliberately runs after the public-identity/legal and SEO layers. It
changes only reader-facing hierarchy and factual presentation on the two
homepages and two book pages, plus the Follow form's initial/honeypot
presentation. It does not rewrite project credits, privacy/controller language,
or the wider visual system.
"""
from __future__ import annotations

from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
BASE = "https://oolita.es"
LASTMOD = "2026-08-23"
CHANGED_PATHS = {"/", "/en/", "/ediciones/libro/", "/en/editions/book/"}


def page(path: str) -> tuple[Path, str]:
    target = ROOT / path
    if not target.is_file():
        raise SystemExit(f"Missing reader-assessment page: {path}")
    return target, target.read_text(encoding="utf-8")


def replace_required(path: str, old: str, new: str) -> None:
    target, text = page(path)
    if new in text:
        return
    if old not in text:
        raise SystemExit(f"Reader-assessment source text missing in {path}: {old[:120]!r}")
    target.write_text(text.replace(old, new, 1), encoding="utf-8")


def regex_required(path: str, pattern: str, replacement: str, marker: str) -> None:
    target, text = page(path)
    if marker in text:
        return
    new_text, count = re.subn(pattern, replacement, text, count=1, flags=re.I | re.S)
    if count != 1:
        raise SystemExit(f"Reader-assessment regex failed in {path}: matches={count}; {pattern[:120]!r}")
    target.write_text(new_text, encoding="utf-8")


def patch_visible_dates(path: str, replacements: tuple[tuple[str, str], ...]) -> None:
    """Change visible text only; leave attributes, JSON-LD, JS and CSS untouched."""
    target, text = page(path)
    protected: list[str] = []

    def stash(match: re.Match[str]) -> str:
        protected.append(match.group(0))
        return f"@@OOLITA_PROTECTED_{len(protected)-1}@@"

    work = re.sub(r"<(?:script|style)\b[\s\S]*?</(?:script|style)>", stash, text, flags=re.I)
    parts = re.split(r"(<[^>]+>)", work)
    for i in range(0, len(parts), 2):
        for old, new in replacements:
            parts[i] = parts[i].replace(old, new)
    work = "".join(parts)
    for index, block in enumerate(protected):
        work = work.replace(f"@@OOLITA_PROTECTED_{index}@@", block)
    target.write_text(work, encoding="utf-8")


def patch_follow(path: str, *, language: str) -> None:
    target, text = page(path)
    loading = "Comprobando la lista…" if language == "es" else "Checking the list…"
    honeypot_label = "Sitio web" if language == "es" else "Website"

    text = text.replace(
        f'<p class="follow-status" data-follow-status aria-live="polite">{loading}</p>',
        '<p class="follow-status" data-follow-status aria-live="polite" hidden></p>',
        1,
    )

    old_honeypot = (
        f'<label style="position:absolute;left:-10000px" aria-hidden="true">{honeypot_label} '
        '<input type="text" name="website" tabindex="-1" autocomplete="off"></label>'
    )
    new_honeypot = (
        f'<label class="follow-honeypot" hidden aria-hidden="true">{honeypot_label} '
        '<input type="text" name="website" tabindex="-1" autocomplete="off"></label>'
    )
    if old_honeypot in text:
        text = text.replace(old_honeypot, new_honeypot, 1)
    elif new_honeypot not in text:
        raise SystemExit(f"Follow honeypot source missing in {path}")

    text, status_count = re.subn(
        r"if\(s\)s\.textContent=([^;]+);",
        r"if(s){s.hidden=false;s.textContent=\1;}",
        text,
    )
    if status_count == 0 and "s.hidden=false;s.textContent=" not in text:
        raise SystemExit(f"Follow status script could not be patched in {path}")

    target.write_text(text, encoding="utf-8")


if not ROOT.is_dir():
    raise SystemExit(f"Missing built site: {ROOT}")

# 1 · Correct the one remaining bare book-spec value.
regex_required(
    "ediciones/libro/index.html",
    r'(<span class="k">Páginas</span>\s*<span class="v">)44(</span>)',
    r"\g<1>48\2",
    '<span class="k">Páginas</span><span class="v">48</span>',
)
regex_required(
    "en/editions/book/index.html",
    r'(<span class="k">Pages</span>\s*<span class="v">)44(</span>)',
    r"\g<1>48\2",
    '<span class="k">Pages</span><span class="v">48</span>',
)

# 2 · Use unambiguous English display dates. Machine-readable dates are unchanged.
ENGLISH_DATES = (
    ("03.01.2027", "3 Jan 2027"),
    ("03.01.27", "3 Jan 27"),
    ("09.08.26", "9 Aug 26"),
    ("31.01.27", "31 Jan 27"),
    ("16.05.27", "16 May 27"),
    ("16.09.27", "16 Sep 27"),
    ("19.09.27", "19 Sep 27"),
    ("11.04.27", "11 Apr 27"),
)
patch_visible_dates("en/index.html", ENGLISH_DATES)
patch_visible_dates("en/editions/book/index.html", ENGLISH_DATES)

# 3 · Follow form: no loading flash and no human-visible honeypot.
patch_follow("index.html", language="es")
patch_follow("en/index.html", language="en")

# 4 · Homepage: show the object before classifying the project.
regex_required(
    "index.html",
    r'<p class="parr definicion">[\s\S]*?</p>',
    '<p class="parr definicion">OOLITA comienza con un laberinto clásico de tres metros, colocado a mano con calcarenita suelta en Los Escullos, sobre una duna fósil que hace cien mil años fue fondo del mar. No lleva cartel ni nombre.</p>',
    "OOLITA comienza con un laberinto clásico de tres metros",
)
regex_required(
    "en/index.html",
    r'<p class="parr definicion">[\s\S]*?</p>',
    '<p class="parr definicion">OOLITA begins with a three-metre classical labyrinth, laid by hand from stone at Los Escullos, on a fossil dune that was seabed a hundred thousand years ago. No sign, no name.</p>',
    "OOLITA begins with a three-metre classical labyrinth",
)

# 5 · Book page: answer what the fable is about, without making the cat the whole project.
regex_required(
    "ediciones/libro/index.html",
    r'<p class="glosa">(?=[\s\S]{0,500}Cuarenta y ocho páginas)[\s\S]*?</p>',
    '<p class="glosa">Cuarenta y ocho páginas, en español y en inglés a la vez. La fábula sigue a un gato de verdad, nacido junto al mar, que vive cerca de la senda y a veces camina hasta la bahía siguiente antes de volver. El laberinto de Los Escullos es el camino que atraviesa el libro.</p>',
    "La fábula sigue a un gato de verdad",
)
regex_required(
    "en/editions/book/index.html",
    r'<p class="glosa">(?=[\s\S]{0,500}Forty-eight pages)[\s\S]*?</p>',
    '<p class="glosa">Forty-eight pages, in Spanish and English at once. The fable follows a real cat, born beside the sea, who lives near the path and sometimes walks as far as the next bay before turning for home. The Los Escullos labyrinth is the path running through the book.</p>',
    "The fable follows a real cat",
)

# 6 · Put the free complete digital reading before the print wait.
replace_required(
    "index.html",
    "En papel no estará disponible hasta el 31 de enero de 2027.",
    "Desde el 3 de enero se podrá leer entero, gratis, dentro del mundo 3D; en papel estará disponible desde el 31 de enero de 2027.",
)
replace_required(
    "en/index.html",
    "In print it will not be available until 31 January 2027.",
    "From 3 January the whole book can be read free inside the 3D world; in print it will be available from 31 January 2027.",
)

# 7 · Balance future-facing asks with the thing that already exists.
regex_required(
    "index.html",
    r'(<p class="parr">(?=[\s\S]{0,650}Hasta entonces, 22 domingos:)[\s\S]*?</p>)',
    r'\1<p class="parr">El laberinto de piedra ya está en Los Escullos; no tiene entrada ni reserva.</p>',
    "El laberinto de piedra ya está en Los Escullos",
)
regex_required(
    "en/index.html",
    r'(<p class="parr">(?=[\s\S]{0,650}Until then, 22 Sundays:)[\s\S]*?</p>)',
    r'\1<p class="parr">The stone labyrinth is already at Los Escullos; there is no ticket or booking.</p>',
    "The stone labyrinth is already at Los Escullos",
)

required = {
    "index.html": [
        "OOLITA comienza con un laberinto clásico de tres metros",
        "Desde el 3 de enero se podrá leer entero, gratis, dentro del mundo 3D",
        "El laberinto de piedra ya está en Los Escullos; no tiene entrada ni reserva.",
        'data-follow-status aria-live="polite" hidden',
        'class="follow-honeypot" hidden aria-hidden="true"',
        "s.hidden=false;s.textContent=",
    ],
    "en/index.html": [
        "OOLITA begins with a three-metre classical labyrinth",
        "From 3 January the whole book can be read free inside the 3D world",
        "The stone labyrinth is already at Los Escullos; there is no ticket or booking.",
        "3 Jan 2027",
        "9 Aug 26",
        'data-follow-status aria-live="polite" hidden',
        'class="follow-honeypot" hidden aria-hidden="true"',
        "s.hidden=false;s.textContent=",
    ],
    "ediciones/libro/index.html": [
        '<span class="k">Páginas</span><span class="v">48</span>',
        "La fábula sigue a un gato de verdad",
    ],
    "en/editions/book/index.html": [
        '<span class="k">Pages</span><span class="v">48</span>',
        "The fable follows a real cat",
        "31 Jan 27",
    ],
}
for path, needles in required.items():
    _, text = page(path)
    for needle in needles:
        if needle not in text:
            raise SystemExit(f"Reader-assessment invariant missing in {path}: {needle}")

for path, forbidden in {
    "index.html": ["Comprobando la lista…"],
    "en/index.html": ["Checking the list…"],
    "ediciones/libro/index.html": ['<span class="k">Páginas</span><span class="v">44</span>'],
    "en/editions/book/index.html": ['<span class="k">Pages</span><span class="v">44</span>'],
}.items():
    _, text = page(path)
    for needle in forbidden:
        if needle in text:
            raise SystemExit(f"Reader-assessment obsolete text remains in {path}: {needle}")

sitemap = ROOT / "sitemap.xml"
if not sitemap.is_file():
    raise SystemExit("Missing sitemap.xml")
ET.register_namespace("", "http://www.sitemaps.org/schemas/sitemap/0.9")
tree = ET.parse(sitemap)
root = tree.getroot()
ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
seen: set[str] = set()
for url_el in root.findall("sm:url", ns):
    loc = url_el.find("sm:loc", ns)
    if loc is None or not loc.text:
        continue
    url = loc.text.strip()
    if not url.startswith(BASE):
        continue
    route = url[len(BASE):] or "/"
    if route not in CHANGED_PATHS:
        continue
    seen.add(route)
    lastmod = url_el.find("sm:lastmod", ns)
    if lastmod is None:
        lastmod = ET.SubElement(url_el, "{http://www.sitemaps.org/schemas/sitemap/0.9}lastmod")
    lastmod.text = LASTMOD

missing = sorted(CHANGED_PATHS - seen)
if missing:
    raise SystemExit(f"Reader-assessment changed URLs missing from sitemap: {missing}")
tree.write(sitemap, encoding="utf-8", xml_declaration=True)

print("OOLITA reader-assessment priority fixes validated successfully.")
