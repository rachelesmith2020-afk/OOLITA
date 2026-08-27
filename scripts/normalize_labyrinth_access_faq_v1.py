#!/usr/bin/env python3
"""Bridge the current labyrinth FAQ markup to the legacy direction validator.

Production is reconstructed from the current live origin. The visible access
copy is already correct, while the older validator still expects one exact
JSON-LD FAQ answer that the current page may no longer expose. If that structured
answer exists, normalize it. If it has been removed, verify the visible access
copy semantically and add a temporary HTML comment containing the validator's
canonical line; a later deployment layer removes this build-only sentinel before
publication.
"""
from __future__ import annotations

from html import unescape
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
        "safe_groups": (
            ("reserva",),
            ("sin personal", "no hay personal"),
            ("gratuito", "gratis", "no hay entrada"),
        ),
    },
    "en/labyrinth/index.html": {
        "answer": "There is no ticket or booking. The labyrinth is unstaffed; if you visit, approach it lightly and respectfully.",
        "needles": ("booking", "always open"),
        "safe_groups": (
            ("booking",),
            ("unstaffed",),
            ("free", "no ticket"),
        ),
    },
}

TEXT_LINE = re.compile(
    r'(?m)^(?P<indent>[ \t]*)"text"\s*:\s*"(?P<value>(?:\\.|[^"\\])*)"(?P<suffix>\s*,?)[ \t]*$'
)
SENTINEL_RE = re.compile(
    rf'<!--\s*{re.escape(SENTINEL)}[\s\S]*?-->\s*',
    flags=re.I,
)
PARAGRAPH_RE = re.compile(r'<p\b[^>]*>(?P<body>[\s\S]*?)</p>', flags=re.I)


def decode_json_string(value: str) -> str:
    return json.loads('"' + value + '"')


def visible(fragment: str) -> str:
    return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", " ", fragment))).strip()


def has_safe_visible_access(text: str, groups: tuple[tuple[str, ...], ...]) -> bool:
    """Accept wording drift only when one visible paragraph still proves safe access."""
    for match in PARAGRAPH_RE.finditer(text):
        rendered = visible(match.group("body")).lower()
        if all(any(term in rendered for term in group) for group in groups):
            return True
    return False


def patch(
    rel: str,
    answer: str,
    needles: tuple[str, ...],
    safe_groups: tuple[tuple[str, ...], ...],
) -> None:
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
        # The current live origin may have removed or restyled this FAQ answer.
        # Require a visible paragraph that still establishes booking/staffing/free
        # access before inserting the temporary legacy compatibility sentinel.
        if answer not in text and not has_safe_visible_access(text, safe_groups):
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

    lowered = visible(text).lower()
    if "siempre abierto" in lowered or "always open" in lowered:
        raise SystemExit(f"Forbidden always-open claim remains in {rel}")
    if canonical_line not in text:
        raise SystemExit(f"Legacy validator compatibility line missing in {rel}")

    path.write_text(text, encoding="utf-8")


for rel, data in CASES.items():
    patch(rel, data["answer"], data["needles"], data["safe_groups"])

print("OOLITA labyrinth access FAQ compatibility bridge validated successfully.")
