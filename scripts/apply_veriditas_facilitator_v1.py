#!/usr/bin/env python3
"""Add Raquel Costantini's public Veriditas facilitator credential to OOLITA.

The credential is deliberately kept off the homepage. It appears only where it
adds provenance and practical context: the bilingual About and Labyrinth pages.
This final content layer also removes the build-only compatibility marker used
by the legacy direction validator before anything is published.
"""
from __future__ import annotations

from pathlib import Path
import re
import sys


ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
VERIDITAS_URL = "https://veriditas.org/Directory"
MARKER = "data-veriditas-credential"
FAQ_COMPAT_MARKER = "oolita-direction-faq-compat"


ABOUT = {
    "sobre-oolita/index.html": (
        "Raquel Costantini es <a href=\"https://veriditas.org/Directory\" target=\"_blank\" rel=\"noopener noreferrer external\">facilitadora de laberintos formada por Veriditas ↗</a>.",
        "Hallazgo y OOLITA",
    ),
    "en/about/index.html": (
        "Raquel Costantini is a <a href=\"https://veriditas.org/Directory\" target=\"_blank\" rel=\"noopener noreferrer external\">Veriditas Trained Labyrinth Facilitator ↗</a>.",
        "Hallazgo and OOLITA",
    ),
}

LABYRINTH = {
    "laberinto/index.html": (
        "Facilitación",
        "Facilitadora de laberintos formada por Veriditas ↗",
        "Directorio",
    ),
    "en/labyrinth/index.html": (
        "Facilitation",
        "Veriditas Trained Labyrinth Facilitator ↗",
        "Directory",
    ),
}


def read(rel: str) -> tuple[Path, str]:
    path = ROOT / rel
    if not path.is_file():
        raise SystemExit(f"Missing Veriditas target page: {rel}")
    return path, path.read_text(encoding="utf-8")


def remove_existing(text: str) -> str:
    # Idempotence across deployments reconstructed from the current live origin.
    text = re.sub(
        rf'<p\b[^>]*\b{MARKER}\b[^>]*>[\s\S]*?</p>\s*',
        "",
        text,
        flags=re.I,
    )
    text = re.sub(
        rf'<div\b[^>]*\b{MARKER}\b[^>]*>[\s\S]*?</div>\s*',
        "",
        text,
        flags=re.I,
    )
    text = re.sub(
        rf'<!--\s*{re.escape(FAQ_COMPAT_MARKER)}[\s\S]*?-->\s*',
        "",
        text,
        flags=re.I,
    )
    return text


def patch_about(rel: str, body: str, heading: str) -> None:
    path, text = read(rel)
    text = remove_existing(text)
    pattern = re.compile(
        rf'(<h2\b[^>]*>\s*{re.escape(heading)}\.?\s*</h2>)',
        flags=re.I,
    )
    match = pattern.search(text)
    if not match:
        raise SystemExit(f"Could not locate Raquel/Hallazgo heading in {rel}")
    credential = f'<p class="parr" {MARKER}>{body}</p>'
    text = text[: match.end()] + credential + text[match.end() :]
    path.write_text(text, encoding="utf-8")


def patch_labyrinth(rel: str, label: str, value: str, directory_label: str) -> None:
    path, text = read(rel)
    text = remove_existing(text)

    # The facts table is deliberately matched by its semantic label and the
    # existing Labyrinth Locator link rather than by surrounding layout classes.
    patterns = (
        re.compile(
            rf'(<div\b[^>]*>[\s\S]*?<span\b[^>]*class=["\'][^"\']*\bk\b[^"\']*["\'][^>]*>\s*{re.escape(directory_label)}\s*</span>[\s\S]*?Labyrinth Locator[\s\S]*?</div>)',
            flags=re.I,
        ),
        re.compile(
            rf'(<a\b[^>]*>[\s\S]*?<span\b[^>]*class=["\'][^"\']*\bk\b[^"\']*["\'][^>]*>\s*{re.escape(directory_label)}\s*</span>[\s\S]*?Labyrinth Locator[\s\S]*?</a>)',
            flags=re.I,
        ),
    )
    match = next((m for pattern in patterns if (m := pattern.search(text))), None)
    if not match:
        raise SystemExit(f"Could not locate Labyrinth Locator fact row in {rel}")

    credential = (
        f'<div {MARKER}><span class="k">{label}</span>'
        f'<span class="v"><a href="{VERIDITAS_URL}" target="_blank" '
        f'rel="noopener noreferrer external">{value}</a></span></div>'
    )
    text = text[: match.end()] + credential + text[match.end() :]
    path.write_text(text, encoding="utf-8")


for rel, (body, heading) in ABOUT.items():
    patch_about(rel, body, heading)

for rel, (label, value, directory_label) in LABYRINTH.items():
    patch_labyrinth(rel, label, value, directory_label)


# Strict final invariants: exactly one credential and one Veriditas directory
# link on each intended page; no homepage is touched by this layer.
for rel in (*ABOUT.keys(), *LABYRINTH.keys()):
    _, text = read(rel)
    if text.count(MARKER) != 1:
        raise SystemExit(f"Unexpected Veriditas marker count in {rel}: {text.count(MARKER)}")
    if text.count(VERIDITAS_URL) != 1:
        raise SystemExit(f"Unexpected Veriditas link count in {rel}: {text.count(VERIDITAS_URL)}")
    if FAQ_COMPAT_MARKER in text:
        raise SystemExit(f"Build-only FAQ compatibility marker leaked into {rel}")

if "Veriditas Trained Labyrinth Facilitator" not in read("en/about/index.html")[1]:
    raise SystemExit("Official English Veriditas designation missing from About page")
if "Veriditas Trained Labyrinth Facilitator" not in read("en/labyrinth/index.html")[1]:
    raise SystemExit("Official English Veriditas designation missing from Labyrinth page")
if "facilitadora de laberintos formada por Veriditas" not in read("sobre-oolita/index.html")[1]:
    raise SystemExit("Spanish Veriditas designation missing from About page")

print("OOLITA Veriditas facilitator credential links validated successfully.")
