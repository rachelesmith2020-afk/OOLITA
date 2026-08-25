#!/usr/bin/env python3
"""Final Spanish Editions voice pass for OOLITA.

Keeps the Editions page in the same concrete, spare register as the book and
runs idempotently after the broader voice audit. The Hallazgo hardback sequence
is now part of the approved final state, so live-origin rebuilds may already
contain it before the later sequence gate runs.
"""
from pathlib import Path
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
PAGE = ROOT / "ediciones/index.html"
if not PAGE.is_file():
    raise SystemExit("Missing Spanish editions page: ediciones/index.html")

text = PAGE.read_text(encoding="utf-8")

rules = (
    (
        (
            "El libro y la camiseta son las primeras ediciones de OOLITA. Abren una serie más amplia de publicaciones de campo, pequeñas piezas textiles y colaboraciones arraigadas en Cabo de Gata.",
            "El libro y la camiseta son las primeras ediciones OOLITA. Abren una serie más amplia de publicaciones de campo, pequeñas piezas textiles y colaboraciones arraigadas en Cabo de Gata.",
            "El libro y la camiseta son las dos primeras ediciones. Después vendrán publicaciones de campo y pequeñas colaboraciones hechas en Cabo de Gata.",
        ),
        "El libro y la camiseta son las dos primeras ediciones. Después vendrá la edición de tapa dura de Hallazgo, seguida de publicaciones de campo y pequeñas colaboraciones hechas en Cabo de Gata.",
    ),
    (
        (
            "Puede crecer hacia geología, viento y sombra, agua, salinas y aves, Posidonia, color, materiales locales y ejercicios de atención. No es una guía para coleccionar cosas: lo encontrado se mira y se deja donde pertenece.",
        ),
        "Puede incluir geología, viento y sombra, agua, salinas y aves, Posidonia, color y materiales locales. Cosas que mirar. Cosas que dibujar. Nada que llevarse.",
    ),
)

changed = 0
for old_forms, new in rules:
    if new in text:
        continue
    for old in old_forms:
        if old in text:
            text = text.replace(old, new, 1)
            changed += 1
            break
    else:
        raise SystemExit(f"Unexpected Spanish Editions wording state: {old_forms[0][:90]}")

PAGE.write_text(text, encoding="utf-8")

verified = PAGE.read_text(encoding="utf-8")
for _, new in rules:
    if verified.count(new) != 1:
        raise SystemExit("Spanish Editions voice replacement missing or duplicated")

print(f"Spanish Editions voice audit passed: {changed} edit(s) applied; Hallazgo sequence current.")
