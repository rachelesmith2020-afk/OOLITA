#!/usr/bin/env python3
"""Apply the approved 2027 OOLITA release calendar as the final site layer.

Approved public dates:
- 3D world: 23 May 2027, 00:00 CEST
- Book: 27 June 2027
- First textile edition: 25 July 2027
- Hallazgo hardback: 16 September 2027 (unchanged)
- Hallazgo public launch: 19 September 2027 (unchanged)

The poster pages and the 22 Sundays archive chronology remain held for a
separate editorial restructuring. Homepage language must nevertheless keep the
series chronology distinct from the 3D-world opening: oolita.es itself is not
described as opening on the series end date.
"""
from __future__ import annotations

from pathlib import Path
import hashlib
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")

if not ROOT.is_dir():
    raise SystemExit(f"Missing built site: {ROOT}")

HELD_PREFIXES = (
    "domingos/",
    "en/sundays/",
    "carteles/",
    "en/posters/",
)

REPLACEMENTS = (
    ("2027-01-03T00:00:00+01:00", "2027-05-23T00:00:00+02:00"),
    ("2027-01-31T00:00:00+01:00", "2027-06-27T00:00:00+02:00"),
    ("2027-01-31T00:00:00Z", "2027-06-27T00:00:00+02:00"),
    ("2027-04-11T00:00:00+02:00", "2027-07-25T00:00:00+02:00"),
    ("2027-01-03", "2027-05-23"),
    ("2027-01-31", "2027-06-27"),
    ("2027-04-11", "2027-07-25"),
    ("03.01.2027", "23.05.2027"),
    ("31.01.2027", "27.06.2027"),
    ("11.04.2027", "25.07.2027"),
    ("03.01.27", "23.05.27"),
    ("31.01.27", "27.06.27"),
    ("11.04.27", "25.07.27"),
    ("03 JAN 27", "23 MAY 27"),
    ("31 JAN 27", "27 JUN 27"),
    ("11 APR 27", "25 JUL 27"),
    ("03 ENE 27", "23 MAY 27"),
    ("31 ENE 27", "27 JUN 27"),
    ("11 ABR 27", "25 JUL 27"),
    ("3 Jan 2027", "23 May 2027"),
    ("31 Jan 2027", "27 Jun 2027"),
    ("11 Apr 2027", "25 Jul 2027"),
    ("3 Jan 27", "23 May 27"),
    ("31 Jan 27", "27 Jun 27"),
    ("11 Apr 27", "25 Jul 27"),
    ("3 January 2027", "23 May 2027"),
    ("31 January 2027", "27 June 2027"),
    ("11 April 2027", "25 July 2027"),
    ("3 January", "23 May"),
    ("31 January", "27 June"),
    ("11 April", "25 July"),
    ("3 de enero de 2027", "23 de mayo de 2027"),
    ("31 de enero de 2027", "27 de junio de 2027"),
    ("11 de abril de 2027", "25 de julio de 2027"),
    ("3 de enero", "23 de mayo"),
    ("31 de enero", "27 de junio"),
    ("11 de abril", "25 de julio"),
    ("00:00 CET", "00:00 CEST"),
)

HOME_HELD = {
    "index.html": (
        "09.08.26 → 03.01.27",
    ),
    "404.html": (
        "09.08.26 → 03.01.27",
    ),
    "404/index.html": (
        "09.08.26 → 03.01.27",
    ),
    "en/index.html": (
        "9 Aug 26 → 3 Jan 27",
    ),
}

HOME_BODY_REPLACEMENTS = {
    "index.html": (
        ("2027-01-03T00:00:00+01:00", "2027-05-23T00:00:00+02:00"),
        ("2027-01-31T00:00:00+01:00", "2027-06-27T00:00:00+02:00"),
        ("2027-04-11T00:00:00+02:00", "2027-07-25T00:00:00+02:00"),
        ("2027-01-03", "2027-05-23"),
        ("2027-01-31", "2027-06-27"),
        ("2027-04-11", "2027-07-25"),
        ("03.01.2027", "23.05.2027"),
        ("03 ENE 27", "23 MAY 27"),
        ("31 ENE 27", "27 JUN 27"),
        ("11 ABR 27", "25 JUL 27"),
        ("31.01.27", "27.06.27"),
        ("11.04.27", "25.07.27"),
        ("Seguir el camino hasta el 3 de enero", "Seguir la apertura del mundo 3D · 23 de mayo"),
        ("Los Escullos en 3D, desde el 3 de enero.", "Los Escullos en 3D, desde el 23 de mayo."),
        (
            "Hasta entonces, 22 domingos: una imagen cada semana, un recorrido desde Los Escullos hasta la apertura de oolita.es. Del 09.08.26 al 03.01.27 en ",
            "22 domingos: una imagen cada semana desde Los Escullos. La serie va del 09.08.26 al 03.01.27 en ",
        ),
        ("desde el 3 de enero, en el mundo 3D.", "desde el 23 de mayo, en el mundo 3D."),
        (
            "Desde el 3 de enero se podrá leer entero, gratis, dentro del mundo 3D; "
            "en papel estará disponible desde el 31 de enero de 2027.",
            "Desde el 23 de mayo se podrá leer entero, gratis, dentro del mundo 3D; "
            "en papel estará disponible desde el 27 de junio de 2027.",
        ),
        (
            "El tercero abre el 3 de enero de 2027 a las 00:00 CET.",
            "El tercero abre el 23 de mayo de 2027 a las 00:00 CEST.",
        ),
        (
            "El mundo 3D abre el 3 de enero de 2027 a las 00:00 CET",
            "El mundo 3D abre el 23 de mayo de 2027 a las 00:00 CEST",
        ),
        ("el camino completo abre el 3 de enero.", "el camino completo abre el 23 de mayo."),
        ("abre 03.01.27", "abre 23.05.27"),
        ("00:00 CET", "00:00 CEST"),
    ),
    "404.html": (),
    "404/index.html": (),
    "en/index.html": (
        ("2027-01-03T00:00:00+01:00", "2027-05-23T00:00:00+02:00"),
        ("2027-01-31T00:00:00+01:00", "2027-06-27T00:00:00+02:00"),
        ("2027-04-11T00:00:00+02:00", "2027-07-25T00:00:00+02:00"),
        ("2027-01-03", "2027-05-23"),
        ("2027-01-31", "2027-06-27"),
        ("2027-04-11", "2027-07-25"),
        ("3 Jan 2027", "23 May 2027"),
        ("03 JAN 27", "23 MAY 27"),
        ("31 JAN 27", "27 JUN 27"),
        ("11 APR 27", "25 JUL 27"),
        ("31.01.27", "27.06.27"),
        ("11.04.27", "25.07.27"),
        ("Follow the path to 3 January", "Follow the 3D world opening · 23 May"),
        ("Los Escullos in 3D, from 3 January.", "Los Escullos in 3D, from 23 May."),
        (
            "Until then, 22 Sundays: one image a week, a path leading from Los Escullos to the opening of oolita.es. From 9 Aug 26 to 3 Jan 27 on ",
            "22 Sundays: one image a week from Los Escullos. The series runs from 9 Aug 26 to 3 Jan 27 on ",
        ),
        ("from 3 January, in the 3D world.", "from 23 May, in the 3D world."),
        (
            "From 3 January the whole book can be read free inside the 3D world; "
            "in print it will be available from 31 January 2027.",
            "From 23 May the whole book can be read free inside the 3D world; "
            "in print it will be available from 27 June 2027.",
        ),
        (
            "The third opens on 3 January 2027 at 00:00 CET.",
            "The third opens on 23 May 2027 at 00:00 CEST.",
        ),
        (
            "The 3D world opens on 3 January 2027 at 00:00 CET",
            "The 3D world opens on 23 May 2027 at 00:00 CEST",
        ),
        (
            "The 3D world opens at 00:00 CET on 3 January 2027",
            "The 3D world opens at 00:00 CEST on 23 May 2027",
        ),
        ("the full path opens on 3 January.", "the full path opens on 23 May."),
        ("opens 3 Jan 27", "opens 23 May 27"),
        ("00:00 CET", "00:00 CEST"),
    ),
}

PAGE_SPECIFIC = {
    "ediciones/libro/index.html": (
        ("un mes después de que abra el mundo en tres dimensiones.", "cinco semanas después de que abra el mundo en tres dimensiones."),
    ),
    "en/editions/book/index.html": (
        ("a month after the three-dimensional world opens.", "five weeks after the three-dimensional world opens."),
    ),
    "ediciones/camiseta/index.html": (
        ("domingo a domingo hasta la primavera.", "domingo a domingo hasta el verano."),
    ),
    "en/editions/t-shirt/index.html": (
        ("Sunday by Sunday through to spring.", "Sunday by Sunday through to summer."),
    ),
}

OBSOLETE = (
    "2027-01-03",
    "2027-01-31",
    "2027-04-11",
    "03.01.2027",
    "31.01.2027",
    "11.04.2027",
    "03 JAN 27",
    "31 JAN 27",
    "11 APR 27",
    "03 ENE 27",
    "31 ENE 27",
    "11 ABR 27",
    "31.01.27",
    "11.04.27",
    "3 January 2027",
    "31 January 2027",
    "11 April 2027",
    "3 de enero de 2027",
    "31 de enero de 2027",
    "11 de abril de 2027",
    "00:00 CET",
)

def is_held(rel: str) -> bool:
    return rel.startswith(HELD_PREFIXES)

def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

held_before = {
    path.relative_to(ROOT).as_posix(): digest(path)
    for path in ROOT.rglob("*.html")
    if is_held(path.relative_to(ROOT).as_posix())
}
held_home_before: dict[str, dict[str, int]] = {}
for rel, phrases in HOME_HELD.items():
    page = ROOT / rel
    if not page.is_file():
        raise SystemExit(f"Missing homepage shell before calendar pass: {rel}")
    text = page.read_text(encoding="utf-8")
    held_home_before[rel] = {phrase: text.count(phrase) for phrase in phrases}

changed: list[str] = []
for path in ROOT.rglob("*.html"):
    rel = path.relative_to(ROOT).as_posix()
    if is_held(rel):
        continue

    text = path.read_text(encoding="utf-8")
    original = text

    if rel in HOME_HELD:
        if "</head>" not in text:
            raise SystemExit(f"Homepage shell lacks </head>: {rel}")
        head, body = text.split("</head>", 1)
        for old, new in REPLACEMENTS:
            head = head.replace(old, new)
        text = head + "</head>" + body

        body_rules = HOME_BODY_REPLACEMENTS.get(rel, ())
        if rel in ("404.html", "404/index.html"):
            body_rules = HOME_BODY_REPLACEMENTS["index.html"]
        head, body = text.split("</head>", 1)
        for old, new in body_rules:
            body = body.replace(old, new)
        text = head + "</head>" + body
    else:
        for old, new in REPLACEMENTS:
            text = text.replace(old, new)

    for old, new in PAGE_SPECIFIC.get(rel, ()):
        text = text.replace(old, new)

    if text != original:
        path.write_text(text, encoding="utf-8")
        changed.append(rel)

held_after = {
    path.relative_to(ROOT).as_posix(): digest(path)
    for path in ROOT.rglob("*.html")
    if is_held(path.relative_to(ROOT).as_posix())
}
if held_before != held_after:
    altered = sorted(set(held_before) | set(held_after))
    altered = [rel for rel in altered if held_before.get(rel) != held_after.get(rel)]
    raise SystemExit(f"Held posters/Sundays files changed unexpectedly: {altered}")

for rel, phrases in HOME_HELD.items():
    page = ROOT / rel
    if not page.is_file():
        raise SystemExit(f"Missing homepage shell after calendar pass: {rel}")
    text = page.read_text(encoding="utf-8")
    after_counts = {phrase: text.count(phrase) for phrase in phrases}
    if after_counts != held_home_before[rel]:
        changed_phrases = {
            phrase: (held_home_before[rel][phrase], after_counts[phrase])
            for phrase in phrases
            if held_home_before[rel][phrase] != after_counts[phrase]
        }
        raise SystemExit(
            f"Held homepage chronology changed unexpectedly in {rel}: {changed_phrases!r}"
        )

required = {
    "index.html": (
        "23.05.2027", "00:00 CEST", "27 JUN 27", "25 JUL 27",
        "23 de mayo de 2027", "27 de junio de 2027",
        "Seguir la apertura del mundo 3D · 23 de mayo",
        "Los Escullos en 3D, desde el 23 de mayo.",
        "La serie va del 09.08.26 al 03.01.27",
        "desde el 23 de mayo, en el mundo 3D.",
    ),
    "en/index.html": (
        "23 May 2027", "00:00 CEST", "27 JUN 27", "25 JUL 27", "27 June 2027",
        "Follow the 3D world opening · 23 May",
        "Los Escullos in 3D, from 23 May.",
        "The series runs from 9 Aug 26 to 3 Jan 27",
        "from 23 May, in the 3D world.",
    ),
    "mundo-3d/index.html": ("23.05.27", "23 de mayo"),
    "en/3d-world/index.html": ("23.05.27", "23 May"),
    "ediciones/libro/index.html": ("27.06.27", "27 de junio de 2027", "cinco semanas"),
    "en/editions/book/index.html": ("27 Jun 27", "27 June 2027", "five weeks"),
    "ediciones/camiseta/index.html": ("25.07.27", "25 de julio de 2027", "hasta el verano"),
    "en/editions/t-shirt/index.html": ("25.07.27", "25 July 2027", "through to summer"),
    "catalogo-hallazgo/index.html": ("16.09.27", "19.09.27"),
    "en/hallazgo-catalogue/index.html": ("16 SEP 27", "19 Sep 27"),
}
for rel, needles in required.items():
    page = ROOT / rel
    if not page.is_file():
        raise SystemExit(f"Missing calendar target page: {rel}")
    text = page.read_text(encoding="utf-8")
    for needle in needles:
        if needle not in text:
            raise SystemExit(f"Calendar validation failed in {rel}: missing {needle!r}")

AMBIGUOUS_HOME_OPENING = {
    "index.html": (
        "apertura de oolita.es",
        "Seguir el camino hasta el 3 de enero",
        "Los Escullos en 3D, desde el 3 de enero.",
        "desde el 3 de enero, en el mundo 3D.",
    ),
    "404.html": (
        "apertura de oolita.es",
        "Seguir el camino hasta el 3 de enero",
        "Los Escullos en 3D, desde el 3 de enero.",
        "desde el 3 de enero, en el mundo 3D.",
    ),
    "404/index.html": (
        "apertura de oolita.es",
        "Seguir el camino hasta el 3 de enero",
        "Los Escullos en 3D, desde el 3 de enero.",
        "desde el 3 de enero, en el mundo 3D.",
    ),
    "en/index.html": (
        "opening of oolita.es",
        "Follow the path to 3 January",
        "Los Escullos in 3D, from 3 January.",
        "from 3 January, in the 3D world.",
    ),
}

for path in ROOT.rglob("*.html"):
    rel = path.relative_to(ROOT).as_posix()
    if is_held(rel):
        continue
    text = path.read_text(encoding="utf-8")
    for phrase in AMBIGUOUS_HOME_OPENING.get(rel, ()):
        if phrase in text:
            raise SystemExit(f"Ambiguous site-opening wording survived in {rel}: {phrase!r}")
    if rel in HOME_HELD:
        for phrase in HOME_HELD[rel]:
            text = text.replace(phrase, "")
    for token in OBSOLETE:
        if token in text:
            raise SystemExit(f"Obsolete release token survived in {rel}: {token!r}")

print("OOLITA master release calendar applied.")
print("3D world: 23 May 2027 00:00 CEST")
print("Book: 27 June 2027")
print("Textile: 25 July 2027")
print("Hallazgo: 16/19 September 2027 unchanged")
print(f"Updated HTML files: {len(changed)}")
