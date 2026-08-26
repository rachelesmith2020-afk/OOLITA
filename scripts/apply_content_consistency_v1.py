#!/usr/bin/env python3
"""Apply and validate OOLITA reader-facing factual consistency fixes.

This narrow final pass runs after the other content transforms. It keeps the
published Sunday archive, Hallazgo work count, book page count, and Sunday 03
geology wording aligned across Spanish and English.
"""
from __future__ import annotations

from pathlib import Path
import re
import sys


ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")

# Reuse the already-reviewed archive-row renderer. When this script is invoked as
# `python3 scripts/apply_content_consistency_v1.py site`, the imported module sees
# the same argv and therefore uses the same built-site root.
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


# 1. The canonical Hallazgo catalogue states 44 works. Some poster pages carry
# only their primary-language paragraph while others carry both translations,
# so patch every stale occurrence but validate the primary copy separately.
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


# 2. Ooids accrete layers around a nucleus; they do not grow "inward". Preserve
# the short OOLITA cadence while making the process scientifically accurate.
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


# 3. Sunday 03 is already published in the compact 22-Sundays field. Rebuild the
# detailed archive rows with the same reviewed renderer so 03 cannot remain in
# the pending state below it.
engagement.patch_archive("domingos/index.html", "es")
engagement.patch_archive("en/sundays/index.html", "en")


# Final consistency guard. These exact stale statements should not survive
# anywhere in reader-facing HTML after this pass.
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
    "domingos/03-la-memoria-del-mar/index.html": (
        "Alrededor de cada grano crecía una capa tras otra",
    ),
    "en/sundays/03-the-memory-of-the-sea/index.html": (
        "Layer upon layer grew around each grain",
    ),
    "domingos/index.html": (
        'data-sunday-archive-row="3"',
        'href="/domingos/03-la-memoria-del-mar/"',
    ),
    "en/sundays/index.html": (
        'data-sunday-archive-row="3"',
        'href="/en/sundays/03-the-memory-of-the-sea/"',
    ),
}
for rel, needles in checks.items():
    _, text = read(rel)
    for needle in needles:
        if needle not in text:
            raise SystemExit(f"Consistency invariant missing in {rel}: {needle}")

# A pending detailed row for the already-published 23 August entry is forbidden.
# Inspect each pending row independently; do not let a regex span into a later row.
for rel in ("domingos/index.html", "en/sundays/index.html"):
    _, text = read(rel)
    pending_rows = re.findall(
        r'<div\b[^>]*class=["\'][^"\']*\bfila\b[^"\']*\bespera\b[^"\']*["\'][^>]*>[\s\S]*?</div>',
        text,
        flags=re.I,
    )
    for row in pending_rows:
        if re.search(r'<time\b[^>]*datetime=["\']2026-08-23["\']', row, flags=re.I):
            raise SystemExit(f"Sunday 03 still pending in detailed archive: {rel}")

print("OOLITA factual/content consistency validated successfully.")
