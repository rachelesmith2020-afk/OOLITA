#!/usr/bin/env python3
"""Normalize the labyrinth access FAQ before the legacy direction validator.

Production is reconstructed from the current live origin. The visible access
copy is already correct, but older deployment code still expects one exact
JSON-LD FAQ answer. Keep only that structured answer canonical so the existing
strict no-"always open" invariants remain meaningful and idempotent.
"""
from __future__ import annotations

from pathlib import Path
import json
import re
import sys


ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")

CASES = {
    "laberinto/index.html": {
        "answer": "No hay entrada ni reserva. Es un lugar sin personal; si lo visitas, acércate con cuidado y respeto por el entorno.",
        "needles": ("reserva", "siempre abierto"),
    },
    "en/labyrinth/index.html": {
        "answer": "There is no ticket or booking. The labyrinth is unstaffed; if you visit, approach it lightly and respectfully.",
        "needles": ("booking", "always open"),
    },
}

# JSON-LD on the live pages is pretty-printed. Match JSON string properties
# called "text" independently of the FAQ question wording, because that label
# has changed over time while the access answer remains semantically stable.
TEXT_LINE = re.compile(
    r'(?m)^(?P<indent>[ \t]*)"text"\s*:\s*"(?P<value>(?:\\.|[^"\\])*)"(?P<suffix>\s*,?)[ \t]*$'
)


def decode_json_string(value: str) -> str:
    return json.loads('"' + value + '"')


def patch(rel: str, answer: str, needles: tuple[str, ...]) -> None:
    path = ROOT / rel
    if not path.is_file():
        raise SystemExit(f"Missing labyrinth FAQ page: {rel}")

    text = path.read_text(encoding="utf-8")
    matches = []
    for match in TEXT_LINE.finditer(text):
        try:
            value = decode_json_string(match.group("value"))
        except json.JSONDecodeError:
            continue
        lowered = value.lower()
        if any(needle in lowered for needle in needles):
            matches.append(match)

    if len(matches) != 1:
        canonical_line = f'            "text": {json.dumps(answer, ensure_ascii=False)}'
        if canonical_line in text and not any(
            forbidden in text.lower() for forbidden in ("siempre abierto", "always open")
        ):
            print(f"labyrinth FAQ already canonical in {rel}")
            return
        raise SystemExit(
            f"Expected one labyrinth access JSON-LD answer in {rel}; found {len(matches)}"
        )

    match = matches[0]
    replacement = (
        f'            "text": {json.dumps(answer, ensure_ascii=False)}'
        f'{match.group("suffix")}'
    )
    updated = text[: match.start()] + replacement + text[match.end() :]
    path.write_text(updated, encoding="utf-8")
    print(f"normalized labyrinth access FAQ in {rel}")


for rel, data in CASES.items():
    patch(rel, data["answer"], data["needles"])

# Final guard: obsolete open-access claims must not be reintroduced here.
for rel in CASES:
    text = (ROOT / rel).read_text(encoding="utf-8")
    lowered = text.lower()
    if "siempre abierto" in lowered or "always open" in lowered:
        raise SystemExit(f"Forbidden always-open claim remains in {rel}")

print("OOLITA labyrinth access FAQ normalization validated successfully.")
