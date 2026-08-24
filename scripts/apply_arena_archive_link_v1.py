#!/usr/bin/env python3
"""Add the bilingual OOLITA Are.na process-archive link to About pages.

The public website remains the canonical work; Are.na is presented as the
research/process archive around it. The layer is deliberately narrow and
idempotent so the link survives future origin-mirror deployments.
"""
from __future__ import annotations

from pathlib import Path
import re
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
ARENA_URL = "https://www.are.na/raquel-costantini/oolita-piedra-papel-y-codigo-stone-paper-and-code"
MARKER = "data-arena-process-archive"


def visible_text(html: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html)).strip()


def strip_existing(text: str) -> str:
    return re.sub(
        rf'<p\b[^>]*\b{MARKER}\b[^>]*>[\s\S]*?</p>\s*',
        "",
        text,
        flags=re.I,
    )


def insert_after_paragraph(text: str, markers: tuple[str, ...], block: str) -> tuple[str, bool]:
    for match in re.finditer(r'<p\b[^>]*>[\s\S]*?</p>', text, flags=re.I):
        current = visible_text(match.group(0))
        if any(marker in current for marker in markers):
            return text[:match.end()] + "\n" + block + text[match.end():], True
    return text, False


def insert_in_material_section(text: str, headings: tuple[str, ...], block: str) -> tuple[str, bool]:
    for match in re.finditer(r'<section\b[^>]*>[\s\S]*?</section>', text, flags=re.I):
        current = visible_text(match.group(0))
        if any(heading in current for heading in headings):
            section = match.group(0)
            pos = section.lower().rfind("</section>")
            if pos < 0:
                continue
            section = section[:pos] + "\n" + block + "\n" + section[pos:]
            return text[:match.start()] + section + text[match.end():], True
    return text, False


PAGES = (
    {
        "rel": "sobre-oolita/index.html",
        "paragraph_markers": (
            "Ninguno sustituye al otro.",
            "Todo se reúne aquí: oolita.es.",
        ),
        "section_headings": (
            "Piedra, papel y código.",
            "Piedra, papel y código",
        ),
        "label": "Archivo de proceso · Are.na ↗",
        "aria": "Archivo de proceso de OOLITA en Are.na (se abre en una pestaña nueva)",
    },
    {
        "rel": "en/about/index.html",
        "paragraph_markers": (
            "None replaces the others.",
            "Everything meets here: oolita.es.",
        ),
        "section_headings": (
            "Stone, paper and code.",
            "Stone, paper and code",
        ),
        "label": "Process archive · Are.na ↗",
        "aria": "OOLITA process archive on Are.na (opens in a new tab)",
    },
)

if not ROOT.is_dir():
    raise SystemExit(f"Missing built site: {ROOT}")

for page in PAGES:
    path = ROOT / page["rel"]
    if not path.is_file():
        raise SystemExit(f"Missing About page: {page['rel']}")

    text = strip_existing(path.read_text(encoding="utf-8"))
    block = (
        f'<p class="parr oolita-arena-process" {MARKER}>'
        f'<a href="{ARENA_URL}" target="_blank" rel="noopener noreferrer external" '
        f'aria-label="{page["aria"]}">{page["label"]}</a>'
        "</p>"
    )

    text, inserted = insert_after_paragraph(text, page["paragraph_markers"], block)
    if not inserted:
        text, inserted = insert_in_material_section(text, page["section_headings"], block)
    if not inserted:
        raise SystemExit(f"Could not locate the stone/paper/code section in {page['rel']}")

    path.write_text(text, encoding="utf-8")

    final = path.read_text(encoding="utf-8")
    if final.count(MARKER) != 1:
        raise SystemExit(f"Expected one Are.na archive link in {page['rel']}")
    if final.count(ARENA_URL) != 1:
        raise SystemExit(f"Expected one canonical Are.na URL in {page['rel']}")
    if page["label"] not in final:
        raise SystemExit(f"Missing Are.na link label in {page['rel']}")

print("OOLITA Are.na process-archive links validated successfully.")
