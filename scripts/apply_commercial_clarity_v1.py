#!/usr/bin/env python3
"""Make OOLITA availability and release status immediately legible.

This is not a conversion layer. It keeps the existing voice and product pages,
but makes the higher-level routes answer four practical questions at a glance:
what exists now, what opens free, when the book goes on sale, and when the first
textile edition goes on sale.
"""
from __future__ import annotations

from html import unescape
from pathlib import Path
import re
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")


def read(rel: str) -> tuple[Path, str]:
    path = ROOT / rel
    if not path.is_file():
        raise SystemExit(f"Missing commercial-clarity target: {rel}")
    return path, path.read_text(encoding="utf-8")


def rendered(fragment: str) -> str:
    text = unescape(re.sub(r"<[^>]+>", "", fragment))
    return re.sub(r"\s+", " ", text).strip()


def replace_once(rel: str, old: str, new: str) -> None:
    path, text = read(rel)
    if new in text:
        return
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"Expected one commercial-status source in {rel}: {old!r}; found {count}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def replace_paragraph(rel: str, marker: str, new_inner: str) -> None:
    path, text = read(rel)
    if new_inner in text:
        return
    pattern = re.compile(r"(<p\b[^>]*>)(.*?)(</p>)", flags=re.I | re.S)
    matches = [m for m in pattern.finditer(text) if marker in rendered(m.group(2))]
    if len(matches) != 1:
        raise SystemExit(f"Expected one paragraph in {rel} for {marker!r}; found {len(matches)}")
    match = matches[0]
    replacement = match.group(1) + new_inner + match.group(3)
    path.write_text(text[: match.start()] + replacement + text[match.end() :], encoding="utf-8")


def insert_status_after_paragraph(rel: str, marker: str, status: str) -> None:
    path, text = read(rel)
    if status in rendered(text):
        return
    pattern = re.compile(r"(<p\b[^>]*>)(.*?)(</p>)", flags=re.I | re.S)
    matches = [m for m in pattern.finditer(text) if marker in rendered(m.group(2))]
    if len(matches) != 1:
        raise SystemExit(f"Expected one status anchor in {rel} for {marker!r}; found {len(matches)}")
    match = matches[0]
    # A plain paragraph is intentional: this is factual status, not another CTA.
    insertion = match.group(0) + "\n<p>" + status + "</p>"
    path.write_text(text[: match.start()] + insertion + text[match.end() :], encoding="utf-8")


STATUS_EN = (
    "NOW · labyrinth at Los Escullos · 22 Sundays. "
    "03 JAN 27 · 3D world opens · free. "
    "31 JAN 27 · book goes on sale. "
    "11 APR 27 · first textile edition goes on sale."
)
STATUS_ES = (
    "AHORA · laberinto en Los Escullos · 22 domingos. "
    "03 ENE 27 · abre el mundo 3D · gratis. "
    "31 ENE 27 · el libro sale a la venta. "
    "11 ABR 27 · sale a la venta la primera edición textil."
)

# HOMEPAGE — the dates already existed, but were scattered through long sections.
# Put the current/future state in one factual line beside the existing 'already
# there' statement. No new sales CTA is added.
insert_status_after_paragraph(
    "en/index.html",
    "The stone labyrinth is already at Los Escullos; there is no ticket or booking.",
    STATUS_EN,
)
insert_status_after_paragraph(
    "index.html",
    "El laberinto de piedra ya está en Los Escullos",
    STATUS_ES,
)

# EDITIONS — use one status vocabulary. 'Available' and 'Coming' implied different
# commercial states even though neither product is currently for sale.
replace_once("en/editions/index.html", "Available 31.01.27", "On sale · 31.01.27")
replace_once("en/editions/index.html", "Coming · 11.04.27", "On sale · 11.04.27")
replace_once("ediciones/index.html", "Disponible 31.01.27", "A la venta · 31.01.27")
replace_once("ediciones/index.html", "Próximamente · 11.04.27", "A la venta · 11.04.27")

# FIELD BOOK — future, but not dated. Say that instead of making the reader infer it.
replace_paragraph(
    "en/editions/index.html",
    "A bilingual publication for children and families",
    "In development. No release date yet. A bilingual publication for children and families: observe, draw, listen and record without collecting or disturbing anything.",
)
replace_paragraph(
    "ediciones/index.html",
    "Una publicación bilingüe para niños y familias",
    "En desarrollo. Aún no hay fecha de publicación. Una publicación bilingüe para niños y familias: observar, dibujar, escuchar y registrar sin recoger ni alterar nada.",
)

# Regression/positive guards. Product detail pages deliberately remain untouched:
# they already say sales are not open yet and carry the fuller publication detail.
required = {
    "en/index.html": (STATUS_EN,),
    "index.html": (STATUS_ES,),
    "en/editions/index.html": (
        "On sale · 31.01.27",
        "On sale · 11.04.27",
        "In development. No release date yet.",
    ),
    "ediciones/index.html": (
        "A la venta · 31.01.27",
        "A la venta · 11.04.27",
        "En desarrollo. Aún no hay fecha de publicación.",
    ),
}
stale = {
    "en/editions/index.html": ("Available 31.01.27", "Coming · 11.04.27"),
    "ediciones/index.html": ("Disponible 31.01.27", "Próximamente · 11.04.27"),
}
for rel, phrases in required.items():
    _, text = read(rel)
    visible = rendered(text)
    for phrase in phrases:
        if phrase not in visible:
            raise SystemExit(f"Commercial-clarity invariant missing in {rel}: {phrase}")
for rel, phrases in stale.items():
    _, text = read(rel)
    visible = rendered(text)
    for phrase in phrases:
        if phrase in visible:
            raise SystemExit(f"Stale commercial status remains in {rel}: {phrase}")

print("OOLITA commercial availability/status clarity applied and validated successfully.")
