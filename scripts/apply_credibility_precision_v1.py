#!/usr/bin/env python3
"""Final factual/credibility gate for OOLITA reader-facing copy.

This pass is deliberately narrow. It corrects factual overstatement, one heritage
date, timing claims and two archive defects after every other editorial layer has
run. It does not rewrite authored Sunday texts or flatten deliberate voice.
"""
from __future__ import annotations

from pathlib import Path
import re
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
if not ROOT.is_dir():
    raise SystemExit(f"Missing built site: {ROOT}")


def page(rel: str) -> tuple[Path, str]:
    path = ROOT / rel
    if not path.is_file():
        raise SystemExit(f"Missing credibility page: {rel}")
    return path, path.read_text(encoding="utf-8")


def replace_optional(rel: str, old: str, new: str) -> int:
    path, text = page(rel)
    count = text.count(old)
    if count:
        path.write_text(text.replace(old, new), encoding="utf-8")
    return count


def replace_many(rel: str, pairs: tuple[tuple[str, str], ...]) -> int:
    path, text = page(rel)
    before = text
    total = 0
    for old, new in pairs:
        count = text.count(old)
        if count:
            text = text.replace(old, new)
            total += count
    if text != before:
        path.write_text(text, encoding="utf-8")
    return total


# 1. SAN FELIPE — local-government heritage record gives 1765. Keep the
# correction factual and quiet; no explanatory paragraph is added to the site.
castle_pairs = (
    ("Batería de San Felipe, 1771", "Batería de San Felipe, 1765"),
    ("Batería de San Felipe, de 1771", "Batería de San Felipe, de 1765"),
    ("Batería de San Felipe, built in 1771", "Batería de San Felipe, built in 1765"),
    ("1771 Batería de San Felipe", "1765 Batería de San Felipe"),
    ("the 1771 Batería de San Felipe", "the 1765 Batería de San Felipe"),
)
castle_changes = 0
for html in ROOT.rglob("*.html"):
    text = html.read_text(encoding="utf-8")
    before = text
    for old, new in castle_pairs:
        text = text.replace(old, new)
    if text != before:
        html.write_text(text, encoding="utf-8")
        castle_changes += 1


# 2. GEOLOGY — distinguish the physical labyrinth site from the fossil-dune
# outcrop, and distinguish the former shallow sea from the later wind-built dune.
geology_common = (
    (", ground that was seabed a hundred thousand years ago", ""),
    (", terreno que hace cien mil años fue fondo del mar", ""),
    ("on land that was seabed a hundred thousand years ago", "on land beside the fossil dunes"),
    ("en terreno que hace cien mil años fue fondo del mar", "en terreno junto a las dunas fósiles"),
    ("sobre una duna fósil frente al Mediterráneo", "en terreno junto a las dunas fósiles frente al Mediterráneo"),
    ("on the Playa del Arco fossil dune", "on land beside the Playa del Arco fossil dunes"),
    ("sobre la duna fósil de la Playa del Arco", "en terreno junto a las dunas fósiles de la Playa del Arco"),
    ("stands on the same fossil dune", "stands on a fossil dune"),
    ("se levanta sobre la misma duna fósil", "se levanta sobre una duna fósil"),
)
geology_changes = 0
for html in ROOT.rglob("*.html"):
    text = html.read_text(encoding="utf-8")
    before = text
    for old, new in geology_common:
        text = text.replace(old, new)
    if text != before:
        html.write_text(text, encoding="utf-8")
        geology_changes += 1


# Los Escullos ooid page — explain the local sequence without turning one
# marine setting into a universal rule for every ooid.
replace_many(
    "que-es-un-oolito/index.html",
    (
        (
            "Hacen falta condiciones muy concretas: agua marina cálida, poco profunda, saturada de carbonato y en movimiento constante. El movimiento es lo esencial — el grano tiene que rodar para que el mineral se deposite de manera uniforme por toda la superficie. Un grano quieto no sale redondo.",
            "Muchos oolitos marinos se forman en agua somera rica en carbonato. El movimiento mantiene los granos girando mientras el carbonato de calcio se acumula en capas alrededor de un núcleo. En Los Escullos, los oolitos se formaron en agua marina poco profunda, agitada por el oleaje.",
        ),
        (
            "En agua marina cálida, poco profunda, saturada de carbonato y en movimiento constante. El grano tiene que rodar para que el mineral se deposite de forma uniforme; por eso salen redondos.",
            "Muchos oolitos marinos se forman en agua somera rica en carbonato y en movimiento. En Los Escullos se formaron en agua marina poco profunda, agitada por el oleaje, mientras el carbonato se acumulaba en capas alrededor de un núcleo.",
        ),
        ("hace más de cien mil años", "hace entre 100.000 y 128.000 años"),
        ("Más de cien mil años. Están catalogadas como AND082", "Entre 100.000 y 128.000 años. Están catalogadas como AND082"),
        (
            "Es la misma figura a dos escalas: una tarda cien mil años, la otra unos minutos.",
            "El parentesco está en la forma: capas, centro, tiempo.",
        ),
    ),
)
replace_many(
    "en/what-is-an-ooid/index.html",
    (
        (
            "It needs very particular conditions: warm, shallow seawater, saturated with carbonate and constantly moving. The movement is the essential part — the grain has to roll for the mineral to be laid down evenly across its whole surface. A grain that stays still will not become round.",
            "Many marine ooids form in shallow water rich in carbonate. Movement keeps the grains turning while calcium carbonate builds in layers around a nucleus. At Los Escullos, the ooids formed in shallow seawater agitated by waves.",
        ),
        (
            "In warm, shallow seawater that is saturated with carbonate and constantly moving. The grain has to roll for the mineral to be deposited evenly — that is why they come out round.",
            "Many marine ooids form in shallow, carbonate-rich water kept in motion. At Los Escullos they formed in shallow seawater agitated by waves, while carbonate built in layers around a nucleus.",
        ),
        ("more than a hundred thousand years ago", "between 100,000 and 128,000 years ago"),
        ("More than a hundred thousand years. They are catalogued as AND082", "Between 100,000 and 128,000 years. They are catalogued as AND082"),
        (
            "It is the same figure at two scales — one takes a hundred thousand years, the other a few minutes.",
            "The connection is in the form: layers, centre, time.",
        ),
    ),
)


# 3. LABYRINTH TIMING — the route back is the same distance, not necessarily the
# same number of minutes. Keep the language physical rather than adding caveats.
replace_many(
    "que-es-un-laberinto/index.html",
    (
        (
            "No hay una manera correcta. La única regla práctica es que el camino se recorre entero: se entra, se llega al centro, y la vuelta ocupa exactamente lo mismo que la ida.",
            "No hay una manera correcta. La única regla práctica es recorrer el camino entero: se entra, se llega al centro y se vuelve por la misma senda.",
        ),
        (
            "Un laberinto de tres metros de diámetro se camina en unos pocos minutos y cabe en un claro pequeño.",
            "Un laberinto de tres metros de diámetro se puede recorrer en pocos minutos, según el ritmo, y cabe en un claro pequeño.",
        ),
        (
            "No hay una manera correcta. Se recorre el camino entero: hacia el centro, una pausa, y el regreso, que ocupa exactamente lo mismo que la ida. Conviene ir despacio.",
            "No hay una manera correcta. Se recorre el camino entero: hacia el centro, una pausa y el regreso por la misma senda. Conviene ir despacio.",
        ),
        (
            "Depende del tamaño. Un laberinto de tres metros se camina en unos pocos minutos; uno de catedral, de once o doce metros, puede llevar media hora si se va despacio.",
            "Depende del tamaño y del ritmo. Un laberinto de tres metros se puede recorrer en pocos minutos; uno de catedral, de once o doce metros, lleva más tiempo.",
        ),
    ),
)
replace_many(
    "en/what-is-a-labyrinth/index.html",
    (
        (
            "There is no correct way. The only practical rule is that you walk the whole path: in, to the centre, and back — and the return takes exactly as long as the way in.",
            "There is no correct way. The only practical rule is to walk the whole path: in to the centre and back along the same route.",
        ),
        (
            "A three-metre labyrinth takes a few minutes to walk and fits in a small clearing.",
            "A three-metre labyrinth can be walked in a few minutes, depending on pace, and fits in a small clearing.",
        ),
        (
            "There is no correct way. You walk the whole path: inward, a pause at the centre, and the return, which takes exactly as long as the way in. Slowly is better.",
            "There is no correct way. You walk the whole path: inward, a pause at the centre, and back along the same route. Slowly is better.",
        ),
        (
            "It depends on the size. A three-metre labyrinth takes a few minutes; a cathedral labyrinth of eleven or twelve metres can take half an hour if you walk slowly.",
            "It depends on the size and the pace. A three-metre labyrinth can be walked in a few minutes; a cathedral labyrinth of eleven or twelve metres takes longer.",
        ),
    ),
)


# 4. SUNDAY ARCHIVE — 22 entries do not divide into a literal three-circuit
# count. Keep the structural idea and fix the one Spanish agreement error.
replace_many(
    "domingos/index.html",
    (
        (
            "La serie tiene la forma del propio laberinto: una entrada, tres circuitos, un centro, un regreso y una salida.",
            "La serie toma la forma del propio laberinto: una entrada, un camino hacia el centro, un regreso y una salida.",
        ),
        (
            "Tres metros de piedras sueltas colocada a mano en 2021 en terreno junto a las dunas fósiles.",
            "Un laberinto de tres metros, colocado a mano con piedras sueltas en 2021, en terreno junto a las dunas fósiles.",
        ),
    ),
)
replace_many(
    "en/sundays/index.html",
    (
        (
            "The series has the shape of the labyrinth itself: an entrance, three circuits, a centre, a return and an exit.",
            "The series takes the shape of the labyrinth itself: an entrance, a path to the centre, a return and an exit.",
        ),
    ),
)


# 5. SUNDAY 03 — the article stays untouched. Repair only inherited navigation,
# the geological alt text, and a later generic archive-explainer paragraph.
def fix_sunday03(rel: str, language: str) -> None:
    path, text = page(rel)

    if language == "es":
        old_href = "/domingos/01-el-doble/"
        new_href = "/domingos/02-el-gato-de-verdad/"
        label = "Domingo anterior"
        body_pairs = (("01", "02"), ("El doble", "El gato, de verdad"))
        old_alt = "Diagrama de cómo los granos de oolito formaron la duna fósil de calcarenita oolítica de Los Escullos, Cabo de Gata: la piedra sobre la que se traza el laberinto de OOLITA."
        new_alt = "Diagrama de cómo los granos de oolito formaron las dunas fósiles de Los Escullos, Cabo de Gata, junto al lugar donde está el laberinto OOLITA."
        generic_marker = "El Domingo 03 forma parte de la secuencia de 22 domingos que conduce a la apertura de 2027."
    else:
        old_href = "/en/sundays/01-the-double/"
        new_href = "/en/sundays/02-the-cat-for-real/"
        label = "Previous Sunday"
        body_pairs = (("01", "02"), ("The double", "The cat, for real"))
        old_alt = "Diagrama de cómo los granos de oolito formaron la duna fósil de calcarenita oolítica de Los Escullos, Cabo de Gata: la piedra sobre la que se traza el laberinto de OOLITA. · Diagram of how ooid grains formed the oolitic calcarenite fossil dune at Los Escullos, Cabo de Gata — the stone the OOLITA labyrinth is laid from."
        new_alt = "Diagram of how ooid grains formed the fossil dunes at Los Escullos, Cabo de Gata, beside the site of the OOLITA labyrinth."
        generic_marker = "Sunday 03 belongs to the 22-Sunday publication sequence leading toward the 2027 opening."

    anchor_re = re.compile(
        rf'(<a\b[^>]*href=["\']{re.escape(old_href)}["\'][^>]*>)([\s\S]*?{re.escape(label)}[\s\S]*?)(</a>)',
        flags=re.I,
    )
    match = anchor_re.search(text)
    if match:
        start, body, end = match.groups()
        start = start.replace(old_href, new_href)
        for old, new in body_pairs:
            body = body.replace(old, new, 1)
        text = text[:match.start()] + start + body + end + text[match.end():]

    text = text.replace(old_alt, new_alt)

    # Remove only the added generic section that describes the archive as a
    # "public record". The authored Sunday article and its place-context block remain.
    section_re = re.compile(r'<section\b[^>]*>[\s\S]*?</section>', flags=re.I)
    for match in list(section_re.finditer(text)):
        if generic_marker in match.group(0):
            text = text[:match.start()] + text[match.end():]
            break

    path.write_text(text, encoding="utf-8")


fix_sunday03("domingos/03-la-memoria-del-mar/index.html", "es")
fix_sunday03("en/sundays/03-the-memory-of-the-sea/index.html", "en")


# Final guards. These are reader-facing credibility invariants, not stylistic
# normalisation rules.
def require(rel: str, needle: str) -> None:
    _, text = page(rel)
    if needle not in text:
        raise SystemExit(f"Credibility invariant missing in {rel}: {needle}")


def reject(rel: str, needle: str) -> None:
    _, text = page(rel)
    if needle in text:
        raise SystemExit(f"Credibility straggler remains in {rel}: {needle}")


for html in ROOT.rglob("*.html"):
    text = html.read_text(encoding="utf-8")
    for bad in (
        "Batería de San Felipe, 1771",
        "Batería de San Felipe, de 1771",
        "1771 Batería de San Felipe",
        "the 1771 Batería de San Felipe",
        "ground that was seabed a hundred thousand years ago",
        "terreno que hace cien mil años fue fondo del mar",
    ):
        if bad in text:
            raise SystemExit(f"Credibility straggler remains in {html.relative_to(ROOT)}: {bad}")

require("que-es-un-oolito/index.html", "entre 100.000 y 128.000 años")
require("en/what-is-an-ooid/index.html", "between 100,000 and 128,000 years ago")
reject("que-es-un-oolito/index.html", "Un grano quieto no sale redondo")
reject("en/what-is-an-ooid/index.html", "A grain that stays still will not become round")
reject("que-es-un-laberinto/index.html", "ocupa exactamente lo mismo que la ida")
reject("en/what-is-a-labyrinth/index.html", "takes exactly as long as the way in")
reject("domingos/index.html", "tres circuitos")
reject("en/sundays/index.html", "three circuits")
require("domingos/03-la-memoria-del-mar/index.html", "/domingos/02-el-gato-de-verdad/")
require("en/sundays/03-the-memory-of-the-sea/index.html", "/en/sundays/02-the-cat-for-real/")
reject("domingos/03-la-memoria-del-mar/index.html", "registro público en curso")
reject("en/sundays/03-the-memory-of-the-sea/index.html", "continuing public record")

print(
    "OOLITA credibility precision passed: heritage date, geology, timing and Sunday archive/navigation are current."
)
