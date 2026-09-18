#!/usr/bin/env python3
"""Final bilingual homepage precision pass for OOLITA.

Runs after every legacy/editorial transform. It removes repetition without
changing the site's visual system, routes, release logic, forms or conservation
stance, then updates homepage metadata and sitemap freshness.

Fail closed: if the expected live wording has drifted, do not guess.
"""
from __future__ import annotations

from pathlib import Path
from html import unescape
import re
import sys
import xml.etree.ElementTree as ET

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
BASE = "https://oolita.es"
LASTMOD = "2026-09-18"

P_RE = re.compile(r"<p\b[^>]*>.*?</p>", re.I | re.S)
TAG_RE = re.compile(r"<[^>]+>", re.S)


def plain(block: str) -> str:
    return " ".join(unescape(TAG_RE.sub(" ", block)).split())


def read(rel: str) -> tuple[Path, str]:
    path = ROOT / rel
    if not path.is_file():
        raise SystemExit(f"Missing homepage: {rel}")
    return path, path.read_text(encoding="utf-8")


def replace_para_containing(text: str, needle: str, new_inner: str, *, page: str) -> str:
    matches = [m for m in P_RE.finditer(text) if needle in plain(m.group(0))]
    if len(matches) != 1:
        raise SystemExit(f"{page}: expected exactly one paragraph containing {needle!r}, found {len(matches)}")
    m = matches[0]
    block = m.group(0)
    opening = re.match(r"<p\b[^>]*>", block, re.I)
    if not opening:
        raise SystemExit(f"{page}: malformed paragraph for {needle!r}")
    replacement = opening.group(0) + new_inner + "</p>"
    return text[:m.start()] + replacement + text[m.end():]


def remove_para_containing(text: str, needle: str, *, page: str, required: bool = True) -> str:
    matches = [m for m in P_RE.finditer(text) if needle in plain(m.group(0))]
    if required and len(matches) != 1:
        raise SystemExit(f"{page}: expected exactly one removable paragraph containing {needle!r}, found {len(matches)}")
    if not matches:
        return text
    if len(matches) > 1:
        raise SystemExit(f"{page}: ambiguous removable paragraph containing {needle!r}: {len(matches)} matches")
    m = matches[0]
    return text[:m.start()] + text[m.end():]


def dedupe_exact_paragraph(text: str, target: str, *, page: str) -> str:
    matches = [m for m in P_RE.finditer(text) if plain(m.group(0)).rstrip(".") == target.rstrip(".")]
    if len(matches) < 1:
        raise SystemExit(f"{page}: manifesto line missing: {target!r}")
    if len(matches) == 1:
        return text
    keep = matches[0]
    pieces = []
    cursor = 0
    for m in matches[1:]:
        pieces.append(text[cursor:m.start()])
        cursor = m.end()
    pieces.append(text[cursor:])
    # The first match lies before every removed match; reconstruction above keeps it.
    out = "".join(pieces)
    if sum(1 for m in P_RE.finditer(out) if plain(m.group(0)).rstrip(".") == target.rstrip(".")) != 1:
        raise SystemExit(f"{page}: failed to reduce manifesto line to one occurrence: {target!r}")
    return out


def set_meta(text: str, attr: str, key: str, value: str, *, page: str) -> str:
    pattern = re.compile(
        rf'''<meta\b(?=[^>]*\b{re.escape(attr)}=["']{re.escape(key)}["'])[^>]*>''',
        re.I,
    )
    matches = list(pattern.finditer(text))
    if len(matches) != 1:
        raise SystemExit(f"{page}: expected one {attr}={key} meta tag, found {len(matches)}")
    tag = matches[0].group(0)
    if re.search(r'''\bcontent=["'][^"']*["']''', tag, re.I):
        new_tag = re.sub(
            r'''\bcontent=(["'])[^"']*\1''',
            lambda m: f"content={m.group(1)}{value}{m.group(1)}",
            tag,
            count=1,
            flags=re.I,
        )
    else:
        new_tag = tag[:-1] + f' content="{value}">'
    return text[:matches[0].start()] + new_tag + text[matches[0].end():]


def patch_home(rel: str, *, en: bool) -> None:
    path, text = read(rel)

    if en:
        hero_needle = "OOLITA grew from a three-metre classical labyrinth"
        hero_new = (
            "OOLITA began in 2021 with a three-metre classical labyrinth, laid by hand in stone at "
            "Los Escullos, beside the fossil dunes. One path, one centre, one return: the same route "
            "now moves through paper and code."
        )
        duplicate_origin = "The three-metre stone labyrinth created at Los Escullos in 2021"
        manifesto_a = "A labyrinth fable for loud days"
        manifesto_b = "Una fábula de laberinto para días ruidosos"
        sunday_caption = "Los Escullos in 3D, from 3 January."
        sunday_follow = "to be notified when the world opens"
        stone_caption_old = "Three metres. One path. Loose stones, laid by hand in 2021."
        stone_caption_new = "Loose stone, laid by hand. 2021."
        stone_detail = "The original labyrinth was created in 2021 at Los Escullos"
        stone_detail_new = (
            "The original is at Los Escullos, inside Cabo de Gata-Níjar Natural Park, Almería. "
            "Three metres of classical design, dry-laid in loose stone: no mortar, cutting or "
            "excavation. It is not signposted or promoted as a destination."
        )
        material_stone = "The 2021 labyrinth at Los Escullos was the starting point"
        digital_needle = "The third opens on 3 January 2027 at 00:00 CET."
        digital_new = (
            "The 3D world opens at 00:00 CET on 3 January 2027 and runs directly in the browser, "
            "with no download or account. It carries the path and the coast’s low light into another "
            "material, so distance, cost or mobility do not decide who can enter."
        )
        material_summary = "Stone. Paper. Code. Three materials, one path."
        paper_caption = "Forty-eight pages. Spanish and English together. The same path carried onto paper."
        paper_caption_new = "48 pages · Spanish and English."
        follow_needle = "One list. Choose what you want to follow:"
        follow_new = (
            "A short list for the 3D world, the book, field publications and textile editions. "
            "Choose only what you want to receive."
        )
        description = (
            "OOLITA began with a stone labyrinth in Cabo de Gata. The path continues through a "
            "bilingual book and a 3D world opening on 3 January 2027."
        )
    else:
        hero_needle = "OOLITA nació de un laberinto clásico de tres metros"
        hero_new = (
            "OOLITA nació en 2021 de un laberinto clásico de tres metros, trazado a mano con piedra "
            "en Los Escullos, junto a las dunas fósiles. Un camino, un centro, un regreso: la misma "
            "senda pasa ahora al papel y al código."
        )
        duplicate_origin = "El laberinto de piedra de tres metros creado en Los Escullos en 2021"
        manifesto_a = "Una fábula de laberinto para días ruidosos"
        manifesto_b = "A labyrinth fable for loud days"
        sunday_caption = "Los Escullos en 3D, desde el 3 de enero."
        sunday_follow = "para recibir un aviso cuando se abra el mundo"
        stone_caption_old = "Tres metros. Un camino. Piedras sueltas, colocadas a mano en 2021."
        stone_caption_new = "Piedra suelta, colocada a mano. 2021."
        stone_detail = "El laberinto original se creó en 2021 en Los Escullos"
        stone_detail_new = (
            "El original está en Los Escullos, dentro del Parque Natural de Cabo de Gata-Níjar "
            "(Almería). Tres metros de trazado clásico, piedra suelta colocada en seco: sin mortero, "
            "cortes ni excavación. No se señaliza ni se promociona como destino."
        )
        material_stone = "El laberinto de 2021 fue el punto de partida"
        digital_needle = "El tercero abre el 3 de enero de 2027 a las 00:00 CET."
        digital_new = (
            "El mundo 3D abre el 3 de enero de 2027 a las 00:00 CET y se recorre directamente en el "
            "navegador, sin descarga ni cuenta. Traslada el trazado y la luz baja de la costa a otra "
            "materia para que la distancia, el coste o la movilidad no decidan quién puede entrar."
        )
        material_summary = "Piedra. Papel. Código. Tres materiales, un camino."
        paper_caption = "Cuarenta y ocho páginas. Español e inglés juntos. La misma senda llevada al papel."
        paper_caption_new = "48 páginas · español e inglés."
        follow_needle = "Una sola lista. Elige lo que quieres seguir:"
        follow_new = (
            "Una lista breve para avisos del mundo 3D, el libro, las publicaciones de campo y las "
            "ediciones textiles. Elige sólo lo que quieras recibir."
        )
        description = (
            "OOLITA nace de un laberinto de piedra en Cabo de Gata. La senda continúa en un libro "
            "bilingüe y en un mundo 3D que abre el 3 de enero de 2027."
        )

    text = replace_para_containing(text, hero_needle, hero_new, page=rel)
    text = remove_para_containing(text, duplicate_origin, page=rel)
    text = dedupe_exact_paragraph(text, manifesto_a, page=rel)
    text = dedupe_exact_paragraph(text, manifesto_b, page=rel)

    text = remove_para_containing(text, sunday_caption, page=rel)
    text = remove_para_containing(text, sunday_follow, page=rel)

    text = replace_para_containing(text, stone_caption_old, stone_caption_new, page=rel)
    text = replace_para_containing(text, stone_detail, stone_detail_new, page=rel)
    text = remove_para_containing(text, material_stone, page=rel)
    text = replace_para_containing(text, digital_needle, digital_new, page=rel)
    text = remove_para_containing(text, material_summary, page=rel)
    text = replace_para_containing(text, paper_caption, paper_caption_new, page=rel)
    text = replace_para_containing(text, follow_needle, follow_new, page=rel)

    if en:
        text, count = re.subn(r"<h2\b([^>]*)>\s*Oolita\s*</h2>", r"<h2\1>Los Escullos</h2>", text, count=1, flags=re.I)
        if count != 1:
            raise SystemExit(f"{rel}: expected English homepage labyrinth H2 'Oolita' exactly once")
    else:
        # Spanish already carries the intended place-name heading; assert it.
        if not re.search(r"<h2\b[^>]*>\s*Los Escullos\s*</h2>", text, re.I):
            raise SystemExit(f"{rel}: expected Spanish homepage labyrinth H2 'Los Escullos'")

    for attr, key in (
        ("name", "description"),
        ("property", "og:description"),
        ("name", "twitter:description"),
    ):
        text = set_meta(text, attr, key, description, page=rel)

    path.write_text(text, encoding="utf-8")


if not ROOT.is_dir():
    raise SystemExit(f"Missing built site: {ROOT}")

patch_home("index.html", en=False)
patch_home("en/index.html", en=True)

# Sitemap freshness for the only two pages changed by this pass.
sitemap = ROOT / "sitemap.xml"
if not sitemap.is_file():
    raise SystemExit("Missing sitemap.xml")
ET.register_namespace("", "http://www.sitemaps.org/schemas/sitemap/0.9")
tree = ET.parse(sitemap)
root = tree.getroot()
ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
wanted = {"/", "/en/"}
seen: set[str] = set()
for url_el in root.findall("sm:url", ns):
    loc = url_el.find("sm:loc", ns)
    if loc is None or not loc.text or not loc.text.startswith(BASE):
        continue
    route = loc.text[len(BASE):] or "/"
    if route not in wanted:
        continue
    seen.add(route)
    lastmod = url_el.find("sm:lastmod", ns)
    if lastmod is None:
        lastmod = ET.SubElement(url_el, "{http://www.sitemaps.org/schemas/sitemap/0.9}lastmod")
    lastmod.text = LASTMOD
if seen != wanted:
    raise SystemExit(f"Homepage URLs missing from sitemap: {sorted(wanted-seen)}")
tree.write(sitemap, encoding="utf-8", xml_declaration=True)

# Final editorial + SEO guards.
checks = {
    "index.html": {
        "must": (
            "Un camino, un centro, un regreso: la misma senda pasa ahora al papel y al código.",
            "Piedra suelta, colocada a mano. 2021.",
            "No se señaliza ni se promociona como destino.",
            "48 páginas · español e inglés.",
            "Elige sólo lo que quieras recibir.",
        ),
        "banned": (
            "El laberinto de piedra de tres metros creado en Los Escullos en 2021",
            "El laberinto de 2021 fue el punto de partida y el más pequeño de los tres.",
            "Piedra. Papel. Código. Tres materiales, un camino.",
            "Los Escullos en 3D, desde el 3 de enero.",
            "para recibir un aviso cuando se abra el mundo",
        ),
        "manifestos": (
            "Una fábula de laberinto para días ruidosos",
            "A labyrinth fable for loud days",
        ),
    },
    "en/index.html": {
        "must": (
            "One path, one centre, one return: the same route now moves through paper and code.",
            "Loose stone, laid by hand. 2021.",
            "It is not signposted or promoted as a destination.",
            "48 pages · Spanish and English.",
            "Choose only what you want to receive.",
            ">Los Escullos</h2>",
        ),
        "banned": (
            "The three-metre stone labyrinth created at Los Escullos in 2021",
            "The 2021 labyrinth at Los Escullos was the starting point, and the smallest of the three.",
            "Stone. Paper. Code. Three materials, one path.",
            "Los Escullos in 3D, from 3 January.",
            "to be notified when the world opens",
            ">Oolita</h2>",
        ),
        "manifestos": (
            "A labyrinth fable for loud days",
            "Una fábula de laberinto para días ruidosos",
        ),
    },
}

for rel, spec in checks.items():
    _, text = read(rel)
    for needle in spec["must"]:
        if needle not in text:
            raise SystemExit(f"{rel}: final required wording missing: {needle}")
    for needle in spec["banned"]:
        if needle in text:
            raise SystemExit(f"{rel}: repetitive/obsolete wording survived: {needle}")
    paragraphs = [plain(m.group(0)).rstrip(".") for m in P_RE.finditer(text)]
    for target in spec["manifestos"]:
        count = paragraphs.count(target.rstrip("."))
        if count != 1:
            raise SystemExit(f"{rel}: manifesto {target!r} occurs {count} times, expected 1")
    if len(re.findall(r"<h1\b", text, re.I)) != 1:
        raise SystemExit(f"{rel}: homepage must contain exactly one H1")
    meta = re.search(r'''<meta\b(?=[^>]*\bname=["']description["'])[^>]*\bcontent=["']([^"']*)["'][^>]*>''', text, re.I)
    if not meta:
        raise SystemExit(f"{rel}: meta description missing")
    if len(unescape(meta.group(1))) > 160:
        raise SystemExit(f"{rel}: meta description exceeds 160 characters")

print("OOLITA bilingual homepage precision pass applied: repetition removed, EN/ES aligned, metadata refreshed.")
