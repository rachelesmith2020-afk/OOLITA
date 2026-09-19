#!/usr/bin/env python3
"""Preserve OOLITA's Sunday archive while retiring the obsolete 22-Sundays launch framing.

The archive name is now simply Domingos / Sundays. The sequence begins on
9 August 2026 and continues every Sunday through the 3D-world launch on
23 May 2027: 42 Sundays in total. Existing published entries and URLs are
preserved. This final deployment layer removes obsolete 22-part framing and
updates launch-facing copy without rewriting legitimate Sunday publication dates.
"""
from __future__ import annotations

from datetime import date, timedelta
from html import escape
from pathlib import Path
import re
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
if not ROOT.is_dir():
    raise SystemExit(f"Missing built site: {ROOT}")

START = date(2026, 8, 9)
LAUNCH = date(2027, 5, 23)
TOTAL = 42
if START + timedelta(weeks=TOTAL - 1) != LAUNCH:
    raise SystemExit("Sunday calendar invariant failed")

ARCHIVE_PATHS = {
    "domingos/index.html": "es",
    "en/sundays/index.html": "en",
}

# These substitutions are safe outside the Sunday archive itself, where
# 03.01.27 remains a legitimate publication date for Sunday 22.
DATE_REPLACEMENTS = (
    ("2027-01-03T00:00:00+01:00", "2027-05-23T00:00:00+02:00"),
    ("2027-01-03T00:00:00Z", "2027-05-23T00:00:00+02:00"),
    ("2027-01-03", "2027-05-23"),
    ("03.01.2027", "23.05.2027"),
    ("03.01.27", "23.05.27"),
    ("03 JAN 27", "23 MAY 27"),
    ("03 ENE 27", "23 MAY 27"),
    ("3 January 2027", "23 May 2027"),
    ("3 January", "23 May"),
    ("3 de enero de 2027", "23 de mayo de 2027"),
    ("3 de enero", "23 de mayo"),
    ("3 Jan 2027", "23 May 2027"),
    ("3 Jan 27", "23 May 27"),
    ("2027-01-31T00:00:00+01:00", "2027-06-27T00:00:00+02:00"),
    ("2027-01-31", "2027-06-27"),
    ("31.01.2027", "27.06.2027"),
    ("31.01.27", "27.06.27"),
    ("31 JAN 27", "27 JUN 27"),
    ("31 ENE 27", "27 JUN 27"),
    ("31 January 2027", "27 June 2027"),
    ("31 January", "27 June"),
    ("31 de enero de 2027", "27 de junio de 2027"),
    ("31 de enero", "27 de junio"),
    ("2027-04-11T00:00:00+02:00", "2027-07-25T00:00:00+02:00"),
    ("2027-04-11", "2027-07-25"),
    ("11.04.2027", "25.07.2027"),
    ("11.04.27", "25.07.27"),
    ("11 APR 27", "25 JUL 27"),
    ("11 ABR 27", "25 JUL 27"),
    ("11 April 2027", "25 July 2027"),
    ("11 April", "25 July"),
    ("11 de abril de 2027", "25 de julio de 2027"),
    ("11 de abril", "25 de julio"),
    ("00:00 CET", "00:00 CEST"),
)

FRAMING_REPLACEMENTS = (
    ("22 domingos de OOLITA", "Domingos de OOLITA"),
    ("22 Sundays of OOLITA", "Sundays of OOLITA"),
    ("22 domingos", "Domingos"),
    ("22 Sundays", "Sundays"),
    ("22 SUNDAYS", "SUNDAYS"),
    ("22 DOMINGOS", "DOMINGOS"),
    ("22-Sunday", "Sunday"),
    ("22 Sunday", "Sunday"),
    ("twenty-two Sundays", "Sundays"),
    ("veintidós domingos", "domingos"),
    ("Las veintidós juntas hacen el recorrido.", "Juntas hacen el recorrido."),
    ("The twenty-two together make the walk.", "Together they make the walk."),
)

def sunday_dates():
    for n in range(1, TOTAL + 1):
        d = START + timedelta(weeks=n - 1)
        yield n, d, d.strftime("%d.%m")

def strip_total_from_entry_labels(text: str) -> str:
    text = re.sub(r"\bDomingo\s+(\d{1,2})\s+de\s+(?:los\s+)?22\b", r"Domingo \1", text, flags=re.I)
    text = re.sub(r"\bSunday\s+(\d{1,2})\s+of\s+(?:the\s+)?22\b", r"Sunday \1", text, flags=re.I)
    text = re.sub(r"\bdomingo\s+(\d{1,2})\s+de\s+veintid[oó]s\b", r"domingo \1", text, flags=re.I)
    text = re.sub(r"\bSunday\s+(\d{1,2})\s+of\s+twenty[- ]two\b", r"Sunday \1", text, flags=re.I)
    return text

def generic_framing(text: str) -> str:
    text = strip_total_from_entry_labels(text)
    for old, new in FRAMING_REPLACEMENTS:
        text = text.replace(old, new)
    return text

def replace_launch_dates(text: str) -> str:
    for old, new in DATE_REPLACEMENTS:
        text = text.replace(old, new)
    return text

def published_links(text: str, lang: str) -> dict[int, str]:
    segment = r"en/sundays" if lang == "en" else r"domingos"
    found: dict[int, str] = {}
    pattern = rf'href=["\']([^"\']*/{segment}/(\d{{2}})-[^"\']*/)["\']'
    for href, number in re.findall(pattern, text, flags=re.I):
        found[int(number)] = href
    return found

def build_field(lang: str, links: dict[int, str]) -> str:
    en = lang == "en"
    cells = []
    for n, d, short in sunday_dates():
        href = links.get(n)
        attrs = [
            'data-sunday-tile',
            f'data-sunday="{n}"',
            f'data-date="{d.isoformat()}"',
        ]
        classes = ["sunday-tile"]
        state = ""
        if href:
            classes.append("is-published")
            attrs.append(f'href="{escape(href, quote=True)}"')
            state = "open" if en else "abierto"
        else:
            attrs.append('aria-disabled="true"')
        cells.append(
            '<li><a class="' + " ".join(classes) + '" ' + " ".join(attrs) + '>'
            f'<span class="sunday-tile-n">{n:02d}</span>'
            f'<span class="sunday-tile-date">{short}</span>'
            f'<span class="sunday-tile-state" data-sunday-state>{state}</span>'
            '</a></li>'
        )
    progress = "published · one image every Sunday until launch" if en else "publicados · una imagen cada domingo hasta la apertura"
    note = "The archive continues to 23 May 2027." if en else "El archivo continúa hasta el 23 de mayo de 2027."
    aria = "Sundays archive" if en else "Archivo de domingos"
    return f'''<div class="sunday-field" id="sunday-field" data-sunday-field data-lang="{lang}">
  <div class="sunday-field-head">
    <p class="sunday-field-count"><strong data-sunday-count>{len(links)}</strong> / {TOTAL} · {progress}</p>
    <p class="sunday-field-note">{note}</p>
  </div>
  <ol class="sunday-field-grid" aria-label="{aria}">
    {''.join(cells)}
  </ol>
  <div class="sunday-field-axis" aria-hidden="true"><span>{'9 Aug 2026' if en else '9 ago 2026'}</span><span>{'23 May 2027' if en else '23 mayo 2027'}</span></div>
</div>'''

def pending_rows(lang: str, start_at: int = 23) -> str:
    en = lang == "en"
    rows = []
    for n, d, _ in sunday_dates():
        if n < start_at:
            continue
        display = d.strftime("%d.%m.%y")
        if n == TOTAL:
            name = "Launch" if en else "La apertura"
            gloss = "The 3D world opens at 00:00 CEST" if en else "El mundo 3D abre a las 00:00 CEST"
        else:
            name = "To come" if en else "Por venir"
            gloss = ""
        rows.append(
            f'<div class="fila espera"><span class="num">{n:02d}</span>'
            f'<span class="cuerpo"><span class="nombre">{name}</span>'
            f'<span class="glo">{gloss}</span></span>'
            f'<time class="cuando" datetime="{d.isoformat()}">{display}</time>'
            '<span class="flecha">·</span></div>'
        )
    return "\n".join(rows)

def patch_archive(path: Path, lang: str) -> None:
    if not path.is_file():
        raise SystemExit(f"Missing Sunday archive page: {path.relative_to(ROOT)}")
    text = path.read_text(encoding="utf-8")
    en = lang == "en"

    # Preserve the weekly chronology itself, including Sunday 22 on 3 January.
    text = generic_framing(text)
    text = text.replace("09.08.2026 — 03.01.2027", "09.08.2026 — 23.05.2027")
    text = text.replace("del 9 de agosto de 2026 al 3 de enero de 2027", "del 9 de agosto de 2026 al 23 de mayo de 2027")
    text = text.replace("From 9 August 2026 to 3 January 2027", "From 9 August 2026 to 23 May 2027")
    text = text.replace("hasta enero 2027", "hasta la apertura")
    text = text.replace("until January 2027", "until launch")
    text = re.sub(r"\b22\s+imágenes\b", "42 domingos", text, flags=re.I)
    text = re.sub(r"\b22\s+images\b", "42 Sundays", text, flags=re.I)

    # Retire the old 22-part labyrinth arithmetic without losing the series.
    es_old = (
        "Los Domingos siguen ese mismo trazado. Los domingos once y doce contienen el giro: "
        "el once llega al centro; el doce comienza el regreso. Los anteriores llevan hacia dentro; "
        "los posteriores vuelven hacia la salida. El último, el 3 de enero, es la salida."
    )
    es_new = (
        "La serie conserva el ritmo del laberinto: una imagen cada domingo, sin saltos. "
        "El archivo continúa hasta el 23 de mayo de 2027, cuando abre el mundo 3D."
    )
    en_old = (
        "The Sundays follow that same drawing. Sundays eleven and twelve hold the turn: "
        "eleven arrives at the centre; twelve begins the return. The earlier Sundays lead inward; "
        "the later ones return towards the exit. The last, on 3 January, is the exit."
    )
    en_new = (
        "The series keeps the labyrinth's measured pace: one image every Sunday, without gaps. "
        "The archive continues until 23 May 2027, when the 3D world opens."
    )
    text = text.replace(es_old, es_new).replace(en_old, en_new)
    text = re.sub(
        r"La numeración no es decorativa\..*?Caminar el laberinto y leer la serie son el mismo gesto a distinta velocidad\.",
        "La numeración conserva el orden de publicación: cada domingo ocupa su fecha y permanece en el archivo. Leer la serie es recorrer el proyecto a otra velocidad.",
        text,
        flags=re.S,
    )
    text = re.sub(
        r"The numbering is not decorative\..*?Walking the labyrinth and reading the series are the same gesture at a different speed\.",
        "The numbering preserves publication order: each Sunday keeps its date and remains in the archive. Reading the series is another way of moving through the project.",
        text,
        flags=re.S,
    )
    text = text.replace("el archivo va creciendo hacia el 3 de enero", "el archivo va creciendo hacia el 23 de mayo")
    text = text.replace("the archive grows towards 3 January", "the archive grows towards 23 May")

    # Sunday 22 is no longer launch day.
    text = text.replace("22 La apertura El mundo abre a las 00:00 CET", "22 Por venir")
    text = text.replace("22 Launch The world opens at 00:00 CET", "22 To come")

    # Rebuild the visual field to all 42 Sundays.
    links = published_links(text, lang)
    field = build_field(lang, links)
    marker = '<span class="rot">Detailed archive</span>' if en else '<span class="rot">Archivo detallado</span>'
    start = text.find('<div class="sunday-field"')
    end = text.find(marker)
    if start >= 0 and end > start:
        text = text[:start] + field + "\n" + text[end:]
    elif end >= 0:
        text = text[:end] + field + "\n" + text[end:]
    else:
        raise SystemExit(f"Detailed archive marker missing in {path.relative_to(ROOT)}")

    # Add future rows 23-42 once. These become real links as posts are published.
    if 'class="num">23</span>' not in text:
        match = re.search(
            r'(<div class="fila[^"]*">\s*<span class="num">22</span>.*?</div>)',
            text,
            flags=re.S,
        )
        if not match:
            raise SystemExit(f"Sunday 22 row missing in {path.relative_to(ROOT)}")
        rows = pending_rows(lang)
        text = text[:match.end()] + "\n" + rows + text[match.end():]

    # Current-facing headings and metadata.
    title = "Sundays — OOLITA archive to launch" if en else "Domingos — archivo OOLITA hasta la apertura"
    text = re.sub(r"<title>.*?</title>", f"<title>{title}</title>", text, count=1, flags=re.S)
    text = re.sub(r'(<meta\s+name="description"\s+content=")[^"]*(")', lambda m: m.group(1) + (
        "One image every Sunday from 9 August 2026 to the OOLITA 3D-world launch on 23 May 2027. Bilingual archive."
        if en else
        "Una imagen cada domingo desde el 9 de agosto de 2026 hasta la apertura del mundo 3D de OOLITA el 23 de mayo de 2027. Archivo bilingüe."
    ) + m.group(2), text, count=1)

    path.write_text(text, encoding="utf-8")

# First update non-archive HTML. Sunday entry pages keep their actual publication
# dates but lose the obsolete total-count framing.
for page in sorted(ROOT.rglob("*.html")):
    rel = page.relative_to(ROOT).as_posix()
    if rel in ARCHIVE_PATHS:
        continue
    text = page.read_text(encoding="utf-8")
    original = text
    text = generic_framing(text)
    # Existing Sunday entry pages 01-06 do not use 3 Jan as their publication
    # date, so launch-date replacement is safe there. Future entries are not yet
    # present in the build.
    text = replace_launch_dates(text)

    # Poster 03 is the obsolete baked "22 DOMINGOS / 22 SUNDAYS" campaign art.
    # Retire that one card without touching the Sunday publications themselves.
    if rel in {"carteles/index.html", "en/posters/index.html"}:
        for tag in ("article", "li", "figure"):
            text = re.sub(
                rf'<{tag}\\b[^>]*>.*?cartel-03\\.(?:avif|webp|png).*?</{tag}>',
                "",
                text,
                flags=re.I | re.S,
            )
    text = re.sub(
        r'/carteles/img/cartel-03\\.(avif|webp|png)',
        lambda m: f'/carteles/img/cartel-01.{m.group(1).lower()}',
        text,
        flags=re.I,
    )

    if text != original:
        page.write_text(text, encoding="utf-8")

for ext in ("avif", "webp", "png"):
    (ROOT / "carteles" / "img" / f"cartel-03.{ext}").unlink(missing_ok=True)

for rel, lang in ARCHIVE_PATHS.items():
    patch_archive(ROOT / rel, lang)

# Remove only the obsolete redirect rules. The archive URLs must resolve to
# their own pages again.
redirects = ROOT / "_redirects"
if redirects.is_file():
    old = redirects.read_text(encoding="utf-8")
    kept = []
    for line in old.splitlines():
        stripped = line.strip()
        if re.match(r"^/(?:domingos|en/sundays)(?:/|\s|\*)", stripped):
            continue
        kept.append(line)
    redirects.write_text("\n".join(kept).rstrip() + "\n", encoding="utf-8")

# Positive deployment guard.
required = {
    "domingos/index.html": ("Domingos", "23.05.2027", 'data-sunday="42"', "/ 42"),
    "en/sundays/index.html": ("Sundays", "23.05.2027", 'data-sunday="42"', "/ 42"),
}
for rel, needles in required.items():
    page = ROOT / rel
    if not page.is_file():
        raise SystemExit(f"Missing preserved archive: {rel}")
    data = page.read_text(encoding="utf-8")
    for needle in needles:
        if needle not in data:
            raise SystemExit(f"Sunday preservation validation failed in {rel}: missing {needle!r}")

# All currently published entry pages must survive as files.
published_routes = (
    "domingos/01-el-doble/index.html",
    "domingos/02-el-gato-de-verdad/index.html",
    "domingos/03-la-memoria-del-mar/index.html",
    "domingos/04-el-guardian/index.html",
    "domingos/05-el-mundo/index.html",
    "domingos/06-el-mapa/index.html",
    "en/sundays/01-the-double/index.html",
    "en/sundays/02-the-cat-for-real/index.html",
    "en/sundays/03-the-memory-of-the-sea/index.html",
    "en/sundays/04-the-guardian/index.html",
    "en/sundays/05-the-world/index.html",
    "en/sundays/06-the-map/index.html",
)
missing = [rel for rel in published_routes if not (ROOT / rel).is_file()]
if missing:
    raise SystemExit(f"Published Sunday pages missing from build: {missing}")

print("OOLITA Sundays preserved and reframed.")
print("Archive name: Domingos / Sundays.")
print("Sequence: 42 Sundays, 9 Aug 2026 through 23 May 2027.")
print("Existing published Sunday URLs preserved; obsolete homepage redirects removed.")
