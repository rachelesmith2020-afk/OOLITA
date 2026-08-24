#!/usr/bin/env python3
"""Repair two mobile layout regressions found in the live OOLITA origin.

1. Keep the browser-world preview inside the mobile viewport.
2. Restore compact published tiles inside the 22-Sundays field when an older
   engagement pass has replaced those tiles with full archive-row markup.

The deployment is reconstructed from the live origin, so this pass is designed
as an idempotent final repair: it fixes either the broken inherited state or an
already-correct state without touching the detailed Sunday archive below it.
"""
from __future__ import annotations

from pathlib import Path
import re
import sys


ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
STYLE_ID = "oolita-mobile-layout-repairs-v1"

SUNDAYS = {
    1: ("2026-08-09", "09.08"),
    2: ("2026-08-16", "16.08"),
    3: ("2026-08-23", "23.08"),
    4: ("2026-08-30", "30.08"),
    5: ("2026-09-06", "06.09"),
    6: ("2026-09-13", "13.09"),
    7: ("2026-09-20", "20.09"),
    8: ("2026-09-27", "27.09"),
    9: ("2026-10-04", "04.10"),
    10: ("2026-10-11", "11.10"),
    11: ("2026-10-18", "18.10"),
    12: ("2026-10-25", "25.10"),
    13: ("2026-11-01", "01.11"),
    14: ("2026-11-08", "08.11"),
    15: ("2026-11-15", "15.11"),
    16: ("2026-11-22", "22.11"),
    17: ("2026-11-29", "29.11"),
    18: ("2026-12-06", "06.12"),
    19: ("2026-12-13", "13.12"),
    20: ("2026-12-20", "20.12"),
    21: ("2026-12-27", "27.12"),
    22: ("2027-01-03", "03.01"),
}

STYLE = r'''<style id="oolita-mobile-layout-repairs-v1">
/* Mobile browser-world still: keep the entire 4:5 image inside the viewport. */
@media(max-width:760px){
  body.art-home figure.oolita-world-preview,
  body.art-home figure[data-browser-world-preview]{
    box-sizing:border-box!important;
    display:block!important;
    width:calc(100vw - 2rem)!important;
    max-width:calc(100vw - 2rem)!important;
    margin:2.5rem 0 2.5rem calc(50% - 50vw + 1rem)!important;
    padding:0!important;
    position:relative!important;
    inset:auto!important;
    left:auto!important;
    right:auto!important;
    transform:none!important;
    overflow:hidden!important;
  }
  body.art-home figure.oolita-world-preview img,
  body.art-home figure[data-browser-world-preview] img{
    box-sizing:border-box!important;
    display:block!important;
    width:100%!important;
    max-width:100%!important;
    height:auto!important;
    max-height:none!important;
    margin:0!important;
    position:static!important;
    inset:auto!important;
    transform:none!important;
    object-fit:contain!important;
    object-position:center!important;
  }
  body.art-home figure.oolita-world-preview figcaption,
  body.art-home figure[data-browser-world-preview] figcaption{
    box-sizing:border-box!important;
    width:100%!important;
    max-width:100%!important;
    margin:.75rem 0 0!important;
  }
}

/* Compact archive field: each of the 22 cells must stay inside its grid track. */
@media(max-width:640px){
  .sunday-field{max-width:100%!important;overflow:visible!important}
  .sunday-field-grid{
    grid-template-columns:repeat(4,minmax(0,1fr))!important;
    width:100%!important;
    max-width:100%!important;
    gap:.45rem!important;
  }
  .sunday-field-grid>li{
    min-width:0!important;
    width:auto!important;
    max-width:100%!important;
    overflow:hidden!important;
  }
  .sunday-field-grid .sunday-tile{
    box-sizing:border-box!important;
    display:flex!important;
    width:100%!important;
    max-width:100%!important;
    min-width:0!important;
    aspect-ratio:1/1!important;
    padding:.55rem!important;
  }
}
</style>'''


def read(rel: str) -> tuple[Path, str]:
    path = ROOT / rel
    if not path.is_file():
        raise SystemExit(f"Missing mobile-repair page: {rel}")
    return path, path.read_text(encoding="utf-8")


def inject_style(text: str, *, rel: str) -> str:
    pattern = re.compile(
        rf'<style\s+id=["\']{re.escape(STYLE_ID)}["\'][^>]*>[\s\S]*?</style>',
        flags=re.I,
    )
    if pattern.search(text):
        return pattern.sub(STYLE, text, count=1)
    if "</head>" not in text:
        raise SystemExit(f"Missing </head> while applying mobile repair: {rel}")
    return text.replace("</head>", STYLE + "\n</head>", 1)


def compact_tile(number: int, href: str, *, language: str) -> str:
    iso_date, short_date = SUNDAYS[number]
    if language == "en":
        aria = f"Sunday {number:02d} · published"
        state = "open"
    else:
        aria = f"Domingo {number:02d} · publicado"
        state = "abierto"
    return (
        f'<a class="sunday-tile is-published" href="{href}" data-sunday-tile '
        f'data-sunday="{number}" data-date="{iso_date}" aria-label="{aria}">'
        f'<span class="sunday-tile-n">{number:02d}</span>'
        f'<span class="sunday-tile-date">{short_date}</span>'
        f'<span class="sunday-tile-state" data-sunday-state>{state}</span></a>'
    )


def repair_sunday_field(rel: str, *, language: str) -> None:
    path, text = read(rel)
    field_match = re.search(
        r'(<ol\b[^>]*class=["\'][^"\']*\bsunday-field-grid\b[^"\']*["\'][^>]*>)([\s\S]*?)(</ol>)',
        text,
        flags=re.I,
    )
    if not field_match:
        raise SystemExit(f"Sunday compact field missing in {rel}")

    inner = field_match.group(2)
    repaired = 0

    rich_pattern = re.compile(
        r'<a\b(?=[^>]*\bdata-sunday-archive-row=["\'](\d{1,2})["\'])(?=[^>]*\bhref=["\']([^"\']+)["\'])[^>]*>[\s\S]*?</a>',
        flags=re.I,
    )

    def replace_rich(match: re.Match[str]) -> str:
        nonlocal repaired
        number = int(match.group(1))
        href = match.group(2)
        if number not in SUNDAYS:
            raise SystemExit(f"Unexpected Sunday number {number} inside compact field in {rel}")
        repaired += 1
        return compact_tile(number, href, language=language)

    inner = rich_pattern.sub(replace_rich, inner)

    # A malformed rich row must never survive inside the compact 22-cell field.
    if "data-sunday-archive-row" in inner:
        raise SystemExit(f"Archive-row markup remains inside compact Sunday field in {rel}")

    text = text[:field_match.start(2)] + inner + text[field_match.end(2):]
    text = inject_style(text, rel=rel)
    path.write_text(text, encoding="utf-8")

    # Published Sundays 01–03 should now be genuine compact tiles.
    _, verified = read(rel)
    field = re.search(
        r'<ol\b[^>]*class=["\'][^"\']*\bsunday-field-grid\b[^"\']*["\'][^>]*>[\s\S]*?</ol>',
        verified,
        flags=re.I,
    )
    if not field:
        raise SystemExit(f"Sunday field disappeared after repair in {rel}")
    block = field.group(0)
    for number in (1, 2, 3):
        if not re.search(
            rf'<a\b[^>]*class=["\'][^"\']*\bsunday-tile\b[^"\']*["\'][^>]*data-sunday=["\']{number}["\']',
            block,
            flags=re.I,
        ):
            raise SystemExit(f"Published compact Sunday {number:02d} missing in {rel}")
    print(f"mobile Sunday field repaired {rel}: {repaired} malformed row(s) restored")


def repair_home_preview(rel: str) -> None:
    path, text = read(rel)
    if "data-browser-world-preview" not in text:
        raise SystemExit(f"Browser-world preview missing in {rel}")
    text = inject_style(text, rel=rel)
    path.write_text(text, encoding="utf-8")
    print(f"mobile browser-world preview constrained in {rel}")


if not ROOT.is_dir():
    raise SystemExit(f"Missing built site: {ROOT}")

repair_home_preview("index.html")
repair_home_preview("en/index.html")
repair_sunday_field("domingos/index.html", language="es")
repair_sunday_field("en/sundays/index.html", language="en")

for rel in ("index.html", "en/index.html", "domingos/index.html", "en/sundays/index.html"):
    _, text = read(rel)
    if STYLE_ID not in text:
        raise SystemExit(f"Mobile repair style missing in {rel}")

print("OOLITA mobile preview and Sunday-field repairs validated successfully.")
