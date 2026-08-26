#!/usr/bin/env python3
"""Clarify the OOLITA homepage follow proposition without adding marketing pressure.

The hero language, product routes and collaboration page already do their jobs.
This final reader-facing pass only answers the practical question left by the
subscription section: what the list covers and how often OOLITA writes.
"""
from __future__ import annotations

from pathlib import Path
import re
import sys


ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")


def replace_state(rel: str, old: str, new: str) -> None:
    path = ROOT / rel
    if not path.is_file():
        raise SystemExit(f"Missing CTA page: {rel}")
    text = path.read_text(encoding="utf-8")
    if new in text:
        return
    if old not in text:
        raise SystemExit(f"Homepage follow proposition not found in {rel}: {old!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def remove_generic_sunday03_note(rel: str, marker: str) -> None:
    path = ROOT / rel
    if not path.is_file():
        raise SystemExit(f"Missing Sunday 03 page: {rel}")
    text = path.read_text(encoding="utf-8")
    if marker not in text:
        return

    section_re = re.compile(r'<section\b[^>]*>[\s\S]*?</section>', flags=re.I)
    matches = [match for match in section_re.finditer(text) if marker in match.group(0)]
    if len(matches) == 1:
        match = matches[0]
        text = text[:match.start()] + text[match.end():]
    elif len(matches) == 0:
        paragraph_re = re.compile(r'<p\b[^>]*>[\s\S]*?</p>', flags=re.I)
        paragraphs = [match for match in paragraph_re.finditer(text) if marker in match.group(0)]
        if len(paragraphs) != 1:
            raise SystemExit(f"Could not isolate generic Sunday 03 note in {rel}")
        match = paragraphs[0]
        text = text[:match.start()] + text[match.end():]
    else:
        raise SystemExit(f"Generic Sunday 03 note appears in multiple sections: {rel}")

    if marker in text:
        raise SystemExit(f"Generic Sunday 03 note survived cleanup in {rel}")
    path.write_text(text, encoding="utf-8")


OLD_EN = "One list. Choose what you want to follow: the 3D world, books, field publications or textile editions."
NEW_EN = "One list. The 3D opening, books, field publications and textile editions. Choose what you want to hear about. We write when there is something to tell you."
OLD_ES = "Una sola lista. Elige lo que quieres seguir: mundo 3D, libros, publicaciones de campo o ediciones textiles."
NEW_ES = "Una sola lista. La apertura del mundo 3D, libros, publicaciones de campo y ediciones textiles. Elige lo que quieres recibir. Escribimos cuando hay algo que contar."

replace_state("en/index.html", OLD_EN, NEW_EN)
replace_state("index.html", OLD_ES, NEW_ES)

for rel, stale, final in (
    ("en/index.html", OLD_EN, NEW_EN),
    ("index.html", OLD_ES, NEW_ES),
):
    text = (ROOT / rel).read_text(encoding="utf-8")
    if stale in text:
        raise SystemExit(f"Stale follow proposition remains in {rel}")
    if final not in text:
        raise SystemExit(f"Final follow proposition missing in {rel}")

# Final reader-facing passes live here so legacy reconstruction/migration
# validators remain untouched. They run before the final factual guard.
import apply_page_differentiation_v1  # noqa: E402,F401
import apply_commercial_clarity_v1  # noqa: E402,F401

# Environmental integrity is applied at the final editorial stage, after the
# older migration/search layers have finished. The language states access from
# a distance and leaves the limit implicit rather than announcing a position.
import apply_environmental_alignment_v1  # noqa: E402,F401

# Remove the later-added generic archive explainer from Sunday 03. It describes
# the page as a continuing public record rather than speaking in the project's
# authored voice. The article, image, place context and navigation remain intact.
remove_generic_sunday03_note(
    "en/sundays/03-the-memory-of-the-sea/index.html",
    "continuing public record",
)
remove_generic_sunday03_note(
    "domingos/03-la-memoria-del-mar/index.html",
    "registro público en curso",
)

print("OOLITA final reader-facing clarity passes validated in Spanish and English.")
