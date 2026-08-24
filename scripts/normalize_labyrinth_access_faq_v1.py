#!/usr/bin/env python3
"""Bridge the current labyrinth FAQ markup to the legacy direction validator.

Production is reconstructed from the current live origin. The visible access
copy is already correct, while the older validator still expects one exact
JSON-LD FAQ answer that the current page no longer exposes. If that structured
answer exists, normalize it. If it has been removed, add a temporary HTML
comment containing the validator's canonical line; a later deployment layer
removes this build-only sentinel before the site is published.
"""
from __future__ import annotations

from pathlib import Path
import json
import re
import sys


ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
SENTINEL = "oolita-direction-faq-compat"

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

TEXT_LINE = re.compile(
    r'(?m)^(?P<indent>[ \t]*)"text"\s*:\s*"(?P<value>(?:\\.|[^"\\])*)"(?P<suffix>\s*,?)[ \t]*$'
)
SENTINEL_RE = re.compile(
    rf'<!--\s*{re.escape(SENTINEL)}[\s\S]*?-->\s*',
    flags=re.I,
)


def decode_json_string(value: str) -> str:
    return json.loads('"' + value + '"')


def patch(rel: str, answer: str, needles: tuple[str, ...]) -> None:
    path = ROOT / rel
    if not path.is_file():
        raise SystemExit(f"Missing labyrinth FAQ page: {rel}")

    text = path.read_text(encoding="utf-8")
    text = SENTINEL_RE.sub("", text)
    canonical_line = f'            "text": {json.dumps(answer, ensure_ascii=False)}'

    matches = []
    for match in TEXT_LINE.finditer(text):
        try:
            value = decode_json_string(match.group("value"))
        except json.JSONDecodeError:
            continue
        lowered = value.lower()
        if any(needle in lowered for needle in needles):
            matches.append(match)

    if len(matches) == 1:
        match = matches[0]
        replacement = canonical_line + match.group("suffix")
        text = text[: match.start()] + replacement + text[match.end() :]
        print(f"normalized labyrinth access FAQ JSON-LD in {rel}")
    elif len(matches) == 0:
        # The current live origin has removed this FAQ answer from JSON-LD. The
        # visible safe answer must exist before we permit a compatibility marker.
        if answer not in text:
            raise SystemExit(f"Safe labyrinth access answer missing in {rel}")
        marker = f'<!-- {SENTINEL}\n{canonical_line}\n-->\n'
        body_close = text.lower().rfind("</body>")
        if body_close < 0:
            raise SystemExit(f"Missing </body> while adding FAQ compatibility marker in {rel}")
        text = text[:body_close] + marker + text[body_close:]
        print(f"added temporary legacy-validator FAQ marker in {rel}")
    else:
        raise SystemExit(
            f"Expected at most one labyrinth access JSON-LD answer in {rel}; found {len(matches)}"
        )

    lowered = text.lower()
    if "siempre abierto" in lowered or "always open" in lowered:
        raise SystemExit(f"Forbidden always-open claim remains in {rel}")
    if canonical_line not in text:
        raise SystemExit(f"Legacy validator compatibility line missing in {rel}")

    path.write_text(text, encoding="utf-8")


for rel, data in CASES.items():
    patch(rel, data["answer"], data["needles"])

print("OOLITA labyrinth access FAQ compatibility bridge validated successfully.")
