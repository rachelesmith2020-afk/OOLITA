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
    "laberinto/index.html": (
        "¿Es gratis? ¿Hay que reservar?",
        "No hay entrada ni reserva. Es un lugar sin personal; si lo visitas, acércate con cuidado y respeto por el entorno.",
    ),
    "en/labyrinth/index.html": (
        "Is it free? Do I need to book?",
        "There is no ticket or booking. The labyrinth is unstaffed; if you visit, approach it lightly and respectfully.",
    ),
}


def patch(rel: str, question: str, answer: str) -> None:
    path = ROOT / rel
    if not path.is_file():
        raise SystemExit(f"Missing labyrinth FAQ page: {rel}")

    text = path.read_text(encoding="utf-8")
    question_json = json.dumps(question, ensure_ascii=False)
    answer_json = json.dumps(answer, ensure_ascii=False)

    # Anchor to the named FAQ item, then replace only its acceptedAnswer text.
    # The replacement deliberately writes the same indentation expected by the
    # existing apply_direction_v3.py idempotence check.
    pattern = re.compile(
        rf'("name"\s*:\s*{re.escape(question_json)}[\s\S]*?'
        rf'"acceptedAnswer"\s*:\s*\{{[\s\S]*?)'
        rf'^\s*"text"\s*:\s*"(?:\\.|[^"\\])*"',
        flags=re.I | re.M,
    )

    replacement_line = f'            "text": {answer_json}'
    updated, count = pattern.subn(
        lambda match: match.group(1) + replacement_line,
        text,
        count=1,
    )

    if count != 1:
        exact = replacement_line
        if exact in text:
            print(f"labyrinth FAQ already canonical in {rel}")
            return
        raise SystemExit(f"Could not normalize labyrinth access FAQ in {rel}")

    path.write_text(updated, encoding="utf-8")
    print(f"normalized labyrinth access FAQ in {rel}")


for rel, (question, answer) in CASES.items():
    patch(rel, question, answer)

# Final guard: obsolete open-access claims must not be reintroduced here.
for rel in CASES:
    text = (ROOT / rel).read_text(encoding="utf-8")
    lowered = text.lower()
    if "siempre abierto" in lowered or "always open" in lowered:
        raise SystemExit(f"Forbidden always-open claim remains in {rel}")

print("OOLITA labyrinth access FAQ normalization validated successfully.")
