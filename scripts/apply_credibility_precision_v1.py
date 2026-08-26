#!/usr/bin/env python3
"""Final factual/credibility gate for OOLITA reader-facing copy.

Narrow by design: factual precision, one heritage date, timing language and two
Sunday archive defects. Authored Sunday text is not rewritten.
"""
from __future__ import annotations

from html import unescape
from pathlib import Path
import re
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
if not ROOT.is_dir():
    raise SystemExit(f"Missing built site: {ROOT}")


def read(rel: str) -> tuple[Path, str]:
    p = ROOT / rel
    if not p.is_file():
        raise SystemExit(f"Missing credibility page: {rel}")
    return p, p.read_text(encoding="utf-8")


def visible(fragment: str) -> str:
    return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", " ", fragment))).strip()


def replace_text(rel: str, pairs: tuple[tuple[str, str], ...]) -> None:
    p, text = read(rel)
    before = text
    for old, new in pairs:
        text = text.replace(old, new)
    if text != before:
        p.write_text(text, encoding="utf-8")


def replace_paragraph(rel: str, markers: tuple[str, ...], new_inner: str, *, required: bool = True) -> None:
    p, text = read(rel)
    paragraph_re = re.compile(r'(<p\b[^>]*>)([\s\S]*?)(</p>)', flags=re.I)
    matches = []
    for m in paragraph_re.finditer(text):
        rendered = visible(m.group(2))
        if any(marker in rendered for marker in markers):
            matches.append(m)
    if not matches:
        if new_inner in text:
            return
        if required:
            raise SystemExit(f"Could not locate credibility paragraph in {rel}: {markers[0]}")
        return
    if len(matches) != 1:
        raise SystemExit(f"Expected one credibility paragraph in {rel}, found {len(matches)}: {markers[0]}")
    m = matches[0]
    text = text[:m.start()] + m.group(1) + new_inner + m.group(3) + text[m.end():]
    p.write_text(text, encoding="utf-8")


# 1. Batería de San Felipe — 1765.
CASTLE = (
    ("Batería de San Felipe, 1771", "Batería de San Felipe, 1765"),
    ("Batería de San Felipe, de 1771", "Batería de San Felipe, de 1765"),
    ("Batería de San Felipe, built in 1771", "Batería de San Felipe, built in 1765"),
    ("1771 Batería de San Felipe", "1765 Batería de San Felipe"),
    ("the 1771 Batería de San Felipe", "the 1765 Batería de San Felipe"),
)
for html in ROOT.rglob("*.html"):
    text = html.read_text(encoding="utf-8")
    before = text
    for old, new in CASTLE:
        text = text.replace(old, new)
    if text != before:
        html.write_text(text, encoding="utf-8")


# 2. Geology — sea first, wind-built fossil dune later. The physical labyrinth
# is described as beside the fossil dunes, not asserted to stand on the outcrop.
GEOLOGY = (
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
for html in ROOT.rglob("*.html"):
    text = html.read_text(encoding="utf-8")
    before = text
    for old, new in GEOLOGY:
        text = text.replace(old, new)
    if text != before:
        html.write_text(text, encoding="utf-8")


# Ooid formation: keep the generic statement cautious, then state the local
# Los Escullos sequence directly. Dates follow the Junta geological trail.
replace_paragraph(
    "que-es-un-oolito/index.html",
    ("Hacen falta condiciones muy concretas", "Muchos oolitos marinos se forman"),
    "Muchos oolitos marinos se forman en agua somera rica en carbonato. El movimiento mantiene los granos girando mientras el carbonato de calcio se acumula en capas alrededor de un núcleo. En Los Escullos, los oolitos se formaron en agua marina poco profunda, agitada por el oleaje.",
)
replace_paragraph(
    "que-es-un-oolito/index.html",
    ("El grano tiene que rodar para que el mineral",),
    "Muchos oolitos marinos se forman en agua somera rica en carbonato y en movimiento. En Los Escullos se formaron en agua marina poco profunda, agitada por el oleaje, mientras el carbonato se acumulaba en capas alrededor de un núcleo.",
)
replace_paragraph(
    "que-es-un-oolito/index.html",
    ("dunas de arena que el viento levantó hace",),
    "En Los Escullos, en la costa de Almería, hay un sistema de eolianitas fósiles de composición oolítica: dunas de arena que el viento levantó hace entre 100.000 y 128.000 años y que después se endurecieron hasta volverse piedra, con la estratificación cruzada del viento todavía visible en el corte.",
)
replace_paragraph(
    "que-es-un-oolito/index.html",
    ("Más de cien mil años", "Entre 100.000 y 128.000 años"),
    "Entre 100.000 y 128.000 años. Están catalogadas como AND082 en el Inventario Español de Lugares de Interés Geológico del IGME.",
)
replace_paragraph(
    "que-es-un-oolito/index.html",
    ("Es la misma figura a dos escalas", "El parentesco está en la forma"),
    "El proyecto se llama OOLITA por esa piedra. Un oolito crece por capas alrededor de un centro; un laberinto se recorre en círculos concéntricos hacia un centro. El parentesco está en la forma: capas, centro, tiempo.",
)
replace_paragraph(
    "en/what-is-an-ooid/index.html",
    ("It needs very particular conditions", "Many marine ooids form"),
    "Many marine ooids form in shallow water rich in carbonate. Movement keeps the grains turning while calcium carbonate builds in layers around a nucleus. At Los Escullos, the ooids formed in shallow seawater agitated by waves.",
)
replace_paragraph(
    "en/what-is-an-ooid/index.html",
    ("The grain has to roll for the mineral",),
    "Many marine ooids form in shallow, carbonate-rich water kept in motion. At Los Escullos they formed in shallow seawater agitated by waves, while carbonate built in layers around a nucleus.",
)
replace_paragraph(
    "en/what-is-an-ooid/index.html",
    ("sand dunes raised by wind more than a hundred thousand years ago", "sand dunes raised by wind between 100,000 and 128,000 years ago"),
    "At Los Escullos, on the coast of Almería in Spain, there is a system of fossil aeolianites of oolitic composition: sand dunes raised by wind between 100,000 and 128,000 years ago, later hardened into stone, with the wind's cross-bedding still visible in section.",
)
replace_paragraph(
    "en/what-is-an-ooid/index.html",
    ("More than a hundred thousand years", "Between 100,000 and 128,000 years"),
    "Between 100,000 and 128,000 years. They are catalogued as AND082 in Spain's national inventory of sites of geological interest (IGME).",
)
replace_paragraph(
    "en/what-is-an-ooid/index.html",
    ("It is the same figure at two scales", "The connection is in the form"),
    "The project is called OOLITA after that stone. An ooid grows in layers around a centre; a labyrinth is walked in concentric circuits towards a centre. The connection is in the form: layers, centre, time.",
)

# Exact FAQ strings inside JSON-LD, when present.
replace_text(
    "que-es-un-oolito/index.html",
    (
        ("En agua marina cálida, poco profunda, saturada de carbonato y en movimiento constante. El grano tiene que rodar para que el mineral se deposite de forma uniforme; por eso salen redondos.", "Muchos oolitos marinos se forman en agua somera rica en carbonato y en movimiento. En Los Escullos se formaron en agua marina poco profunda, agitada por el oleaje, mientras el carbonato se acumulaba en capas alrededor de un núcleo."),
        ("Más de cien mil años. Están catalogadas como AND082", "Entre 100.000 y 128.000 años. Están catalogadas como AND082"),
    ),
)
replace_text(
    "en/what-is-an-ooid/index.html",
    (
        ("In warm, shallow seawater that is saturated with carbonate and constantly moving. The grain has to roll for the mineral to be deposited evenly — that is why they come out round.", "Many marine ooids form in shallow, carbonate-rich water kept in motion. At Los Escullos they formed in shallow seawater agitated by waves, while carbonate built in layers around a nucleus."),
        ("More than a hundred thousand years. They are catalogued as AND082", "Between 100,000 and 128,000 years. They are catalogued as AND082"),
    ),
)


# 3. Labyrinth timing — same route/distance does not mean identical elapsed time.
replace_paragraph(
    "que-es-un-laberinto/index.html",
    ("la vuelta ocupa exactamente lo mismo que la ida",),
    "No hay una manera correcta. La única regla práctica es recorrer el camino entero: se entra, se llega al centro y se vuelve por la misma senda.",
)
replace_paragraph(
    "que-es-un-laberinto/index.html",
    ("Un laberinto de tres metros de diámetro se camina en unos pocos minutos",),
    "Un laberinto de tres metros de diámetro se puede recorrer en pocos minutos, según el ritmo, y cabe en un claro pequeño. Es la medida mínima en la que el camino sigue siendo un camino y no una decoración: hay sitio para poner un pie delante del otro sin pisar los bordes.",
)
replace_paragraph(
    "que-es-un-laberinto/index.html",
    ("regreso, que ocupa exactamente lo mismo que la ida",),
    "No hay una manera correcta. Se recorre el camino entero: hacia el centro, una pausa y el regreso por la misma senda. Conviene ir despacio.",
)
replace_paragraph(
    "que-es-un-laberinto/index.html",
    ("puede llevar media hora si se va despacio",),
    "Depende del tamaño y del ritmo. Un laberinto de tres metros se puede recorrer en pocos minutos; uno de catedral, de once o doce metros, lleva más tiempo.",
)
replace_paragraph(
    "en/what-is-a-labyrinth/index.html",
    ("the return takes exactly as long as the way in",),
    "There is no correct way. The only practical rule is to walk the whole path: in to the centre and back along the same route.",
)
replace_paragraph(
    "en/what-is-a-labyrinth/index.html",
    ("A three-metre labyrinth takes a few minutes to walk",),
    "A three-metre labyrinth can be walked in a few minutes, depending on pace, and fits in a small clearing. It is about the smallest size at which the path is still a path rather than a decoration: there is room to put one foot in front of the other without treading on the edges.",
)
replace_paragraph(
    "en/what-is-a-labyrinth/index.html",
    ("return, which takes exactly as long as the way in",),
    "There is no correct way. You walk the whole path: inward, a pause at the centre, and back along the same route. Slowly is better.",
)
replace_paragraph(
    "en/what-is-a-labyrinth/index.html",
    ("can take half an hour if you walk slowly",),
    "It depends on the size and the pace. A three-metre labyrinth can be walked in a few minutes; a cathedral labyrinth of eleven or twelve metres takes longer.",
)

# Keep FAQ structured data aligned with the corrected visible answers.
replace_text(
    "que-es-un-laberinto/index.html",
    (
        ("No hay una manera correcta. Se recorre el camino entero: hacia el centro, una pausa, y el regreso, que ocupa exactamente lo mismo que la ida. Conviene ir despacio.", "No hay una manera correcta. Se recorre el camino entero: hacia el centro, una pausa y el regreso por la misma senda. Conviene ir despacio."),
        ("Depende del tamaño. Un laberinto de tres metros se camina en unos pocos minutos; uno de catedral, de once o doce metros, puede llevar media hora si se va despacio.", "Depende del tamaño y del ritmo. Un laberinto de tres metros se puede recorrer en pocos minutos; uno de catedral, de once o doce metros, lleva más tiempo."),
    ),
)
replace_text(
    "en/what-is-a-labyrinth/index.html",
    (
        ("There is no correct way. You walk the whole path: inward, a pause at the centre, and the return, which takes exactly as long as the way in. Slowly is better.", "There is no correct way. You walk the whole path: inward, a pause at the centre, and back along the same route. Slowly is better."),
        ("It depends on the size. A three-metre labyrinth takes a few minutes; a cathedral labyrinth of eleven or twelve metres can take half an hour if you walk slowly.", "It depends on the size and the pace. A three-metre labyrinth can be walked in a few minutes; a cathedral labyrinth of eleven or twelve metres takes longer."),
    ),
)


# 4. Sunday archive — preserve the structure without a false circuit count.
replace_paragraph(
    "domingos/index.html",
    ("La serie tiene la forma del propio laberinto: una entrada, tres circuitos", "La serie toma la forma del propio laberinto"),
    "Del 9 de agosto de 2026 al 3 de enero de 2027 se publica una imagen cada domingo a las 19:00 en <a href=\"https://www.instagram.com/oolita.es/\">@oolita.es</a>, y queda aquí para siempre. La serie toma la forma del propio laberinto: una entrada, un camino hacia el centro, un regreso y una salida.",
)
replace_text(
    "domingos/index.html",
    (("Tres metros de piedras sueltas colocada a mano en 2021 en terreno junto a las dunas fósiles.", "Un laberinto de tres metros, colocado a mano con piedras sueltas en 2021, en terreno junto a las dunas fósiles."),),
)
replace_paragraph(
    "en/sundays/index.html",
    ("The series has the shape of the labyrinth itself: an entrance, three circuits", "The series takes the shape of the labyrinth itself"),
    "From 9 August 2026 to 3 January 2027, one image is published every Sunday at 19:00 Spanish time on <a href=\"https://www.instagram.com/oolita.es/\">@oolita.es</a>, and stays here. The series takes the shape of the labyrinth itself: an entrance, a path to the centre, a return and an exit.",
)


# 5. Sunday 03 — keep the authored article intact. Fix inherited navigation,
# image alt text and remove one later generic SEO/archive paragraph.
def fix_sunday03(rel: str, language: str) -> None:
    p, text = read(rel)
    if language == "es":
        old_href, new_href = "/domingos/01-el-doble/", "/domingos/02-el-gato-de-verdad/"
        label, old_title, new_title = "Domingo anterior", "El doble", "El gato, de verdad"
        new_alt = "Diagrama de cómo los granos de oolito formaron las dunas fósiles de Los Escullos, Cabo de Gata, junto al lugar donde está el laberinto OOLITA."
        generic = "El Domingo 03 forma parte de la secuencia de 22 domingos que conduce a la apertura de 2027."
    else:
        old_href, new_href = "/en/sundays/01-the-double/", "/en/sundays/02-the-cat-for-real/"
        label, old_title, new_title = "Previous Sunday", "The double", "The cat, for real"
        new_alt = "Diagram of how ooid grains formed the fossil dunes at Los Escullos, Cabo de Gata, beside the site of the OOLITA labyrinth."
        generic = "Sunday 03 belongs to the 22-Sunday publication sequence leading toward the 2027 opening."

    anchor_re = re.compile(r'<a\b[^>]*>[\s\S]*?</a>', flags=re.I)
    for m in list(anchor_re.finditer(text)):
        block = m.group(0)
        if label in visible(block) and old_href in block:
            block = block.replace(old_href, new_href, 1)
            block = re.sub(r'>\s*01\s*<', '>02<', block, count=1)
            block = block.replace(old_title, new_title, 1)
            text = text[:m.start()] + block + text[m.end():]
            break

    img_re = re.compile(r'<img\b[^>]*\bsrc=["\']/domingos/img/03(?:-[^"\']+)?\.(?:jpg|avif)["\'][^>]*>', flags=re.I)
    m = img_re.search(text)
    if m:
        tag = m.group(0)
        if re.search(r'\balt=["\'][^"\']*["\']', tag, flags=re.I):
            tag = re.sub(r'\balt=(["\'])[^"\']*\1', lambda a: f'alt={a.group(1)}{new_alt}{a.group(1)}', tag, count=1, flags=re.I)
        text = text[:m.start()] + tag + text[m.end():]

    section_re = re.compile(r'<section\b[^>]*>[\s\S]*?</section>', flags=re.I)
    for m in list(section_re.finditer(text)):
        if generic in visible(m.group(0)):
            text = text[:m.start()] + text[m.end():]
            break

    p.write_text(text, encoding="utf-8")


fix_sunday03("domingos/03-la-memoria-del-mar/index.html", "es")
fix_sunday03("en/sundays/03-the-memory-of-the-sea/index.html", "en")


# Final reader-facing invariants.
def require(rel: str, needle: str) -> None:
    _, text = read(rel)
    if needle not in text:
        raise SystemExit(f"Credibility invariant missing in {rel}: {needle}")


def reject(rel: str, needle: str) -> None:
    _, text = read(rel)
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

require("que-es-un-oolito/index.html", "100.000 y 128.000 años")
require("en/what-is-an-ooid/index.html", "100,000 and 128,000 years")
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

print("OOLITA credibility precision passed: heritage date, geology, timing and Sunday archive/navigation are current.")
