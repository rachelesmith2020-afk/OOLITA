#!/usr/bin/env python3
"""Apply and validate OOLITA reader-facing final consistency fixes.

This final pre-publish pass applies the reviewed voice and English editorial cleanup,
then keeps the published Sunday archive, Hallazgo work count, book page count, and
Sunday 03 geology wording aligned across Spanish and English.
"""
from __future__ import annotations

from pathlib import Path
import re
import sys


ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")

# Run the editorial cleanup at the same final deployment stage so later transforms
# cannot reintroduce the audited language problems before publication. The English
# pass is deliberately tolerant of inline markup while its regression guards remain strict.
import apply_voice_contrast_v1  # noqa: E402,F401
import apply_english_native_edit_v1  # noqa: E402,F401

# Reuse only the already-reviewed detailed archive row renderer. Do not call its
# broad archive patcher: Sunday 03 is already linked in the compact archive, so a
# generic href match can select that correct top tile instead of the stale lower row.
import apply_engagement_depth_v1 as engagement  # noqa: E402


def read(rel: str) -> tuple[Path, str]:
    path = ROOT / rel
    if not path.is_file():
        raise SystemExit(f"Missing consistency page: {rel}")
    return path, path.read_text(encoding="utf-8")


def replace_state(rel: str, old: str, new: str) -> None:
    path, text = read(rel)
    if old in text:
        path.write_text(text.replace(old, new), encoding="utf-8")
        return
    if new in text:
        return
    raise SystemExit(f"Neither stale nor corrected copy found in {rel}: {old!r}")


def replace_if_present(rel: str, old: str, new: str) -> None:
    path, text = read(rel)
    if old in text:
        path.write_text(text.replace(old, new), encoding="utf-8")


def matching_div_end(text: str, start: int) -> int:
    token_re = re.compile(r'</?div\b[^>]*>', flags=re.I)
    depth = 0
    for match in token_re.finditer(text, start):
        token = match.group(0)
        if token.lower().startswith("</div"):
            depth -= 1
            if depth == 0:
                return match.end()
        else:
            depth += 1
    raise SystemExit("Unclosed <div> while locating Sunday archive row")


def pending_sunday03_blocks(text: str) -> list[tuple[int, int]]:
    starts: list[tuple[int, int]] = []
    start_re = re.compile(r'<div\b[^>]*class=["\'][^"\']*\bfila\b[^"\']*\bespera\b[^"\']*["\'][^>]*>', flags=re.I)
    for match in start_re.finditer(text):
        end = matching_div_end(text, match.start())
        block = text[match.start():end]
        if re.search(r'<time\b[^>]*datetime=["\']2026-08-23["\']', block, flags=re.I):
            starts.append((match.start(), end))
    return starts


def publish_detailed_sunday03(rel: str, language: str) -> None:
    path, text = read(rel)
    blocks = pending_sunday03_blocks(text)
    if blocks:
        if len(blocks) != 1:
            raise SystemExit(f"Expected one pending Sunday 03 detailed row in {rel}, found {len(blocks)}")
        start, end = blocks[0]
        row = engagement.archive_row(3, language)
        text = text[:start] + row + text[end:]
        path.write_text(text, encoding="utf-8")
        return

    expected_route = "/en/sundays/03-the-memory-of-the-sea/" if language == "en" else "/domingos/03-la-memoria-del-mar/"
    if 'data-sunday-archive-row="3"' in text and f'href="{expected_route}"' in text:
        return
    raise SystemExit(f"Could not locate pending or published detailed Sunday 03 row in {rel}")


for rel in ("carteles/index.html", "en/posters/index.html"):
    replace_if_present(
        rel,
        "Hallazgo reúne 42 obras, registradas de H001 a H044.",
        "Hallazgo reúne 44 obras, registradas de H001 a H044.",
    )
    replace_if_present(
        rel,
        "Hallazgo brings together 42 works, registered H001 to H044.",
        "Hallazgo brings together 44 works, registered H001 to H044.",
    )


for rel in (
    "domingos/03-la-memoria-del-mar/index.html",
    "en/sundays/03-the-memory-of-the-sea/index.html",
):
    replace_state(
        rel,
        "Cada grano se redondeaba hacia dentro, capa sobre capa, hasta volverse una esfera diminuta.",
        "Alrededor de cada grano crecía una capa tras otra, hasta volverlo una esfera diminuta.",
    )
    replace_state(
        rel,
        "Each grain rounded inward, layer upon layer, until it became a tiny sphere.",
        "Layer upon layer grew around each grain until it became a tiny sphere.",
    )


publish_detailed_sunday03("domingos/index.html", "es")
publish_detailed_sunday03("en/sundays/index.html", "en")


stale_strings = (
    "Hallazgo reúne 42 obras, registradas de H001 a H044.",
    "Hallazgo brings together 42 works, registered H001 to H044.",
    "Cada grano se redondeaba hacia dentro, capa sobre capa, hasta volverse una esfera diminuta.",
    "Each grain rounded inward, layer upon layer, until it became a tiny sphere.",
    "una fábula bilingüe de 44 páginas",
    "a 44-page bilingual fable",
    "Forty-four pages",
    "Cuarenta y cuatro páginas",
)
violations: list[str] = []
for html in ROOT.rglob("*.html"):
    text = html.read_text(encoding="utf-8", errors="ignore")
    for stale in stale_strings:
        if stale in text:
            violations.append(f"{html.relative_to(ROOT)}: {stale}")
if violations:
    raise SystemExit("Stale factual copy remains:\n" + "\n".join(violations))


checks = {
    "carteles/index.html": (
        "Hallazgo reúne 44 obras, registradas de H001 a H044.",
        "una fábula bilingüe de 48 páginas",
    ),
    "en/posters/index.html": (
        "Hallazgo brings together 44 works, registered H001 to H044.",
        "a 48-page bilingual fable",
    ),
    "catalogo-hallazgo/index.html": ("Hallazgo reúne 44 obras",),
    "en/hallazgo-catalogue/index.html": ("Hallazgo brings together 44 works",),
    "domingos/03-la-memoria-del-mar/index.html": ("Alrededor de cada grano crecía una capa tras otra",),
    "en/sundays/03-the-memory-of-the-sea/index.html": ("Layer upon layer grew around each grain",),
    "domingos/index.html": ('data-sunday-archive-row="3"', 'href="/domingos/03-la-memoria-del-mar/"'),
    "en/sundays/index.html": ('data-sunday-archive-row="3"', 'href="/en/sundays/03-the-memory-of-the-sea/"'),
}
for rel, needles in checks.items():
    _, text = read(rel)
    for needle in needles:
        if needle not in text:
            raise SystemExit(f"Consistency invariant missing in {rel}: {needle}")

for rel in ("domingos/index.html", "en/sundays/index.html"):
    _, text = read(rel)
    if pending_sunday03_blocks(text):
        raise SystemExit(f"Sunday 03 still pending in detailed archive: {rel}")

print("OOLITA factual/content consistency validated successfully.")
