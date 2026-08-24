#!/usr/bin/env python3
"""Normalize known homepage source paragraphs before the legacy soft-marketing pass.

The reconstructed site can contain inline markup or small wording drift inside
paragraphs that an older transformer compares as literal strings. Normalize only
unique, already-approved source paragraphs before that transformer runs.
"""
from __future__ import annotations

from html import unescape
from pathlib import Path
import re
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")

SOURCES = {
    "index.html": (
        "OOLITA seguirá siendo un solo laberinto, en Los Escullos. Alrededor de ese camino, el proyecto empieza a crecer en publicaciones de campo, ediciones textiles y colaboraciones que invitan a niños y adultos a mirar Cabo de Gata más despacio y más de cerca.",
        "Entre las líneas en desarrollo hay cuadernos para recorrer el territorio en familia, ensayos con color natural y posibles colaboraciones con artesanos locales en torno a saberes materiales como la fibra de pita.",
        "La intención no es llevar más gente a un solo punto. Es acompañar visitas más lentas, hacer visible el conocimiento local y cuidar el paisaje vivo.",
    ),
    "en/index.html": (
        "OOLITA will remain one labyrinth at Los Escullos. Around that path, the project is growing into field publications, textile editions and collaborations that help children and adults look more closely at Cabo de Gata.",
        "Directions in development include field books for family visits, experiments with natural colour, and possible collaborations with local makers around material traditions such as pita fibre.",
        "The aim is not to bring more people to one point. It is to support slower visits, local knowledge and care for the living landscape.",
    ),
}

UNIQUE_CUES = {
    ("index.html", SOURCES["index.html"][1]): ("cuadernos", "color natural", "fibra de pita"),
    ("en/index.html", SOURCES["en/index.html"][1]): ("field books", "natural colour", "pita fibre"),
}


def visible(html: str) -> str:
    return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", " ", html))).strip()


if not ROOT.is_dir():
    raise SystemExit(f"Missing built site: {ROOT}")

for rel, sources in SOURCES.items():
    path = ROOT / rel
    if not path.is_file():
        raise SystemExit(f"Missing homepage: {rel}")
    text = path.read_text(encoding="utf-8")
    for source in sources:
        if source in text:
            continue
        cues = UNIQUE_CUES.get((rel, source))
        matched = False
        for match in list(re.finditer(r'(<p\b[^>]*>)([\s\S]*?)(</p>)', text, flags=re.I)):
            rendered = visible(match.group(2))
            rendered_l = rendered.lower()
            equivalent = rendered == source
            uniquely_identified = bool(cues) and all(cue in rendered_l for cue in cues)
            if equivalent or uniquely_identified:
                text = text[:match.start()] + match.group(1) + source + match.group(3) + text[match.end():]
                matched = True
                break
        if matched:
            print(f"normalized homepage source in {rel}: {source[:70]}")
    path.write_text(text, encoding="utf-8")

print("OOLITA soft-marketing source compatibility normalization complete.")
