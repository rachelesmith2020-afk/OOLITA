#!/usr/bin/env python3
"""Final public-identity, release-date and provenance-safe wording pass for OOLITA."""
from pathlib import Path
import re
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")

if not ROOT.is_dir():
    raise SystemExit(f"Missing built site: {ROOT}")


def read(path: str):
    p = ROOT / path
    if not p.is_file():
        raise SystemExit(f"Missing expected page: {path}")
    return p, p.read_text(encoding="utf-8")


def replace_optional(text: str, old: str, new: str) -> str:
    return text.replace(old, new) if old in text else text


def patch_footer(path: Path, text: str) -> str:
    lang_en = bool(re.search(r'<html\s+lang=["\']en(?:-[^"\']+)?["\']', text, flags=re.I))
    if lang_en:
        main_credit = "OOLITA · A Vestini Tribe project · Raquel Costantini, artist and author"
        build_credit = "Site and 3D world built by Vestini Tribe."
        copyright_credit = "© Vestini Tribe. Texts and artworks © Raquel Costantini."
        old_credits = [
            "OOLITA · Raquel Costantini, artist and author · Vestini Tribe, publisher",
            "OOLITA · Raquel Costantini",
        ]
    else:
        main_credit = "OOLITA · Un proyecto de Vestini Tribe · Raquel Costantini, artista y autora"
        build_credit = "Sitio y mundo 3D construidos por Vestini Tribe."
        copyright_credit = "© Vestini Tribe. Textos y obras © Raquel Costantini."
        old_credits = [
            "OOLITA · Raquel Costantini, artista y autora · Vestini Tribe, editorial",
            "OOLITA · Raquel Costantini",
        ]

    m = re.search(r'<footer\b[\s\S]*?</footer>', text, flags=re.I)
    if not m:
        raise SystemExit(f"Missing footer in {path.relative_to(ROOT)}")
    footer = m.group(0)
    for old in old_credits:
        if old in footer:
            footer = footer.replace(old, main_credit, 1)
            break
    if main_credit not in footer:
        raise SystemExit(f"Could not set main footer credit in {path.relative_to(ROOT)}")

    if 'class="rot oolita-build-credit"' not in footer:
        additions = (
            f'<span class="rot oolita-build-credit">{build_credit}</span>'
            f'<span class="rot oolita-copyright-credit">{copyright_credit}</span>'
        )
        if "</div></div></footer>" in footer:
            footer = footer.replace("</div></div></footer>", additions + "</div></div></footer>", 1)
        else:
            footer = footer.replace("</footer>", additions + "</footer>", 1)
    text = text[:m.start()] + footer + text[m.end():]
    return text


# Global year-range typography, controller line, footer identity and credits.
for p in sorted(ROOT.rglob("*.html")):
    text = p.read_text(encoding="utf-8")
    text = re.sub(r'2026\s*[—–-]\s*2027', '2026–2027', text)
    text = text.replace("Controller: Raquel Costantini (OOLITA).", "Controller: Vestini Tribe.")
    text = text.replace("Responsable: Raquel Costantini (OOLITA).", "Responsable: Vestini Tribe.")
    text = text.replace("un laberinto hecho con piedra recogida del suelo", "un laberinto colocado en seco y sin fijar")
    text = text.replace("a labyrinth made from stone gathered from the ground", "a dry-laid, unfixed labyrinth")
    text = text.replace("a labyrinth made of stone gathered from the ground", "a dry-laid, unfixed labyrinth")
    text = patch_footer(p, text)
    p.write_text(text, encoding="utf-8")


# Privacy policy: Vestini Tribe is the controller.
for path, replacements in {
    "privacidad/index.html": [
        ("Raquel Costantini · OOLITA.", "Vestini Tribe."),
        ("Raquel Costantini, en Almería, España, es la responsable del tratamiento.", "Vestini Tribe es el responsable del tratamiento."),
    ],
    "en/privacy/index.html": [
        ("Raquel Costantini · OOLITA.", "Vestini Tribe."),
        ("Raquel Costantini, in Almería, Spain, is the data controller.", "Vestini Tribe is the data controller."),
    ],
}.items():
    p, text = read(path)
    for old, new in replacements:
        text = replace_optional(text, old, new)
    p.write_text(text, encoding="utf-8")


# Fix the remaining 44/48-page specification-row mismatch without touching Hallazgo IDs.
for path, old, new in [
    ("ediciones/libro/index.html", '<span class="k">Páginas</span><span class="v">44</span>', '<span class="k">Páginas</span><span class="v">48</span>'),
    ("en/editions/book/index.html", '<span class="k">Pages</span><span class="v">44</span>', '<span class="k">Pages</span><span class="v">48</span>'),
]:
    p, text = read(path)
    text = replace_optional(text, old, new)
    p.write_text(text, encoding="utf-8")


# Remove the local-stone provenance claim while retaining material, construction and place facts.
for path, replacements in {
    "index.html": [
        (
            "Es un trazado clásico de tres metros, hecho a mano en 2021 con calcarenita suelta sobre una duna fósil que hace cien mil años fue fondo del mar.",
            "Es un laberinto clásico de tres metros, colocado a mano en 2021. Está colocado en seco y sin fijar — no hay mortero; no se ha cortado ni excavado nada. Está sobre una duna fósil que hace cien mil años fue fondo del mar.",
        ),
        (
            "Piedra recogida a pocos pasos de donde ahora está, colocada a mano en septiembre de 2021, sin cemento, sin excavación y sin cimiento.",
            "Colocado a mano en 2021, en seco y sin fijar — no hay mortero; no se ha cortado ni excavado nada.",
        ),
    ],
    "en/index.html": [
        (
            "It is a classical three-metre pattern, laid by hand in 2021 from loose calcarenite on a fossil dune that was seabed a hundred thousand years ago.",
            "It is a classical three-metre labyrinth, laid by hand in 2021. Dry-laid and unfixed — nothing bedded, cut or excavated. It stands on a fossil dune that was seabed a hundred thousand years ago.",
        ),
        (
            "Stone gathered within a few paces of where it now lies, laid by hand in September 2021 — no cement, no digging, no foundation.",
            "Laid by hand in 2021, dry-laid and unfixed — nothing bedded, cut or excavated.",
        ),
    ],
}.items():
    p, text = read(path)
    for old, new in replacements:
        text = replace_optional(text, old, new)
    p.write_text(text, encoding="utf-8")


# Labyrinth page hero and visitor instruction, bilingual.
lab_es_old = '<p class="glosa">Un <a href="/que-es-un-laberinto/">laberinto clásico</a> de tres metros, hecho a mano en septiembre de 2021 con calcarenita suelta — piedra recogida a pocos pasos de donde ahora está — sobre una <a href="/que-es-un-oolito/">duna fósil</a> que hace cien mil años fue fondo del mar. Este laberinto tiene un solo camino: no hay bifurcaciones ni callejones sin salida, y no hay forma de perderse. Se camina despacio. Se encuentra junto al Castillo de San Felipe. No tiene personal ni entrada; recorrerlo es gratuito y conviene acercarse con cuidado y respeto por el lugar.</p>'
lab_es_new = '<p class="glosa">Un <a href="/que-es-un-laberinto/">laberinto clásico</a> de tres metros, colocado a mano en 2021. Está colocado en seco y sin fijar — no hay mortero; no se ha cortado ni excavado nada. Se encuentra sobre una <a href="/que-es-un-oolito/">duna fósil</a> que hace cien mil años fue fondo del mar. Este laberinto tiene un solo camino: no hay bifurcaciones ni callejones sin salida, y no hay forma de perderse. Se camina despacio. Se encuentra junto al Castillo de San Felipe. No tiene personal ni entrada; recorrerlo es gratuito y conviene acercarse con cuidado y respeto por el lugar.</p>'
lab_en_old = '<p class="glosa">A three-metre <a href="/en/what-is-a-labyrinth/">classical labyrinth</a>, laid by hand in September 2021 from loose calcarenite — stone gathered within a few paces of where it now lies — on a <a href="/en/what-is-an-ooid/">fossil dune</a> that was seabed a hundred thousand years ago. A labyrinth is not a maze: there are no forks, no dead ends and no way to get lost. You walk it slowly. It can be found beside the Castillo de San Felipe. It is unstaffed, free to encounter and should be approached lightly and respectfully.</p>'
lab_en_new = '<p class="glosa">A three-metre <a href="/en/what-is-a-labyrinth/">classical labyrinth</a>, laid by hand in 2021. Dry-laid and unfixed — nothing bedded, cut or excavated. It stands on a <a href="/en/what-is-an-ooid/">fossil dune</a> that was seabed a hundred thousand years ago. A labyrinth is not a maze: there are no forks, no dead ends and no way to get lost. You walk it slowly. It can be found beside the Castillo de San Felipe. It is unstaffed, free to encounter and should be approached lightly and respectfully.</p>'
for path, old, new, visitor_old, visitor_new in [
    ("laberinto/index.html", lab_es_old, lab_es_new, "Piedra suelta sobre roca viva: pisa el camino, no los bordes.", "Camina por la senda, no por los bordes, y deja las piedras donde están."),
    ("en/labyrinth/index.html", lab_en_old, lab_en_new, "Loose stone on living rock: step on the path, not the edges.", "Please walk the path, not the edges, and leave the stones where they lie."),
]:
    p, text = read(path)
    text = replace_optional(text, old, new)
    text = replace_optional(text, visitor_old, visitor_new)
    p.write_text(text, encoding="utf-8")


# Publish the confirmed Hallazgo dates on OOLITA; keep checkout/preorder claims off the site.
for path, old, new in [
    ("index.html", "En el castillo: catálogo completo con clave · tapa dura prevista para otoño de 2027 ↗", "En el castillo: catálogo completo con clave · tapa dura 16.09.27 · presentación pública 19.09.27 ↗"),
    ("en/index.html", "In the castle: full catalogue with a key · hardback planned for autumn 2027 ↗", "In the castle: full catalogue with a key · hardback 16.09.27 · public launch 19.09.27 ↗"),
]:
    p, text = read(path)
    text = replace_optional(text, old, new)
    p.write_text(text, encoding="utf-8")


# Strict public-facing invariants.
checks = {
    "index.html": [
        "03.01.2027", "31 de enero de 2027", "16.05.27", "16.09.27", "19.09.27",
        "OOLITA · Un proyecto de Vestini Tribe · Raquel Costantini, artista y autora",
        "Sitio y mundo 3D construidos por Vestini Tribe.",
        "© Vestini Tribe. Textos y obras © Raquel Costantini.",
    ],
    "en/index.html": [
        "03.01.2027", "31 January 2027", "16.05.27", "16.09.27", "19.09.27",
        "OOLITA · A Vestini Tribe project · Raquel Costantini, artist and author",
        "Site and 3D world built by Vestini Tribe.",
        "© Vestini Tribe. Texts and artworks © Raquel Costantini.",
    ],
    "ediciones/camiseta/index.html": ["11.04.27"],
    "en/editions/t-shirt/index.html": ["11.04.27"],
    "privacidad/index.html": ["Vestini Tribe es el responsable del tratamiento."],
    "en/privacy/index.html": ["Vestini Tribe is the data controller."],
    "ediciones/libro/index.html": ['<span class="k">Páginas</span><span class="v">48</span>'],
    "en/editions/book/index.html": ['<span class="k">Pages</span><span class="v">48</span>'],
    "en/labyrinth/index.html": ["Dry-laid and unfixed — nothing bedded, cut or excavated.", "leave the stones where they lie"],
}
for path, needles in checks.items():
    _, text = read(path)
    for needle in needles:
        if needle not in text:
            raise SystemExit(f"Public identity/date invariant missing in {path}: {needle}")

forbidden = [
    "stone gathered within a few paces",
    "piedra recogida a pocos pasos",
    "stone gathered from the ground",
    "piedra recogida del suelo",
    "Controller: Raquel Costantini (OOLITA).",
    "Responsable: Raquel Costantini (OOLITA).",
    "hardback planned for autumn 2027",
    "tapa dura prevista para otoño de 2027",
    "2026—2027",
    "2026 — 2027",
]
for p in ROOT.rglob("*.html"):
    text = p.read_text(encoding="utf-8")
    for needle in forbidden:
        if needle in text:
            raise SystemExit(f"Forbidden public wording remains in {p.relative_to(ROOT)}: {needle}")

print("OOLITA public identity, dates and provenance-safe wording validated successfully.")
