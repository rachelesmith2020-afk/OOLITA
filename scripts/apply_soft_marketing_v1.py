#!/usr/bin/env python3
"""Strengthen OOLITA's invitation without making its voice commercial.

This final reader-facing layer removes taxonomy-first duplication, makes the
January opening the principal invitation, gives Follow a concrete editorial
promise, keeps speculative future work concise, and makes collaboration
enquiries actionable. It also labels elapsed, unpublished Sundays honestly.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET
from zoneinfo import ZoneInfo

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
BASE = "https://oolita.es"
LASTMOD = "2026-08-24"
CHANGED_PATHS = {
    "/", "/en/", "/laberinto/", "/en/labyrinth/",
    "/domingos/", "/en/sundays/", "/colaborar/",
    "/en/work-with-oolita/",
}


def read(path: str) -> tuple[Path, str]:
    target = ROOT / path
    if not target.is_file():
        raise SystemExit(f"Missing soft-marketing page: {path}")
    return target, target.read_text(encoding="utf-8")


def replace_all(path: str, old: str, new: str, *, required: bool = True) -> None:
    target, text = read(path)
    if old not in text:
        if new in text or not required:
            return
        raise SystemExit(f"Soft-marketing source missing in {path}: {old[:100]!r}")
    target.write_text(text.replace(old, new), encoding="utf-8")


def insert_before_contact(path: str, block: str, marker: str) -> None:
    target, text = read(path)
    if marker in text:
        return
    match = re.search(
        r'<section\b[^>]*>\s*<span\b[^>]*class=["\'][^"\']*\brot\b[^"\']*["\'][^>]*>\s*(?:Contacto|Contact)\s*</span>',
        text,
        flags=re.I,
    )
    if not match:
        raise SystemExit(f"Contact section anchor missing in {path}")
    target.write_text(text[:match.start()] + block + text[match.start():], encoding="utf-8")


def replace_reminder(path: str, language: str) -> None:
    """Replace the reminder paragraph while tolerating an inline mail link."""
    target, text = read(path)
    marker = "te avisaré cuando se abra" if language == "es" else "let you know when it opens"
    if marker in text:
        return
    phrase = r"¿Te aviso cuando se abra la puerta\?" if language == "es" else r"Would you like me to let you know when the door opens\?"
    pattern = rf'<p\b[^>]*class=["\'][^"\']*\bparr\b[^"\']*["\'][^>]*>(?=[\s\S]{{0,500}}{phrase})[\s\S]*?</p>'
    if language == "es":
        replacement = '<p class="parr">¿Quieres que te avise cuando se abra? <a href="mailto:oolita@tutamail.com?subject=OOLITA%20%C2%B7%20apertura%203D">Déjame tu correo</a> y te avisaré el 3 de enero.</p>'
    else:
        replacement = '<p class="parr">Would you like to know when it opens? <a href="mailto:oolita@tutamail.com?subject=OOLITA%20%C2%B7%203D%20opening">Leave your email</a> and I will let you know on 3 January.</p>'
    new_text, count = re.subn(pattern, replacement, text, count=1, flags=re.I | re.S)
    if count != 1:
        raise SystemExit(f"Reminder paragraph not found in {path}")
    target.write_text(new_text, encoding="utf-8")


# Put the visitor's experience before the institutional classification.
for path, definition in (
    ("index.html", '<p class="parr definicion">OOLITA es un proyecto editorial y de trabajo de campo arraigado en Los Escullos, Cabo de Gata.</p>'),
    ("en/index.html", '<p class="parr definicion">OOLITA is a place-based publishing and fieldwork project rooted in Los Escullos, Cabo de Gata.</p>'),
):
    replace_all(path, definition, "", required=False)

replace_all(
    "index.html",
    "OOLITA comienza con un laberinto clásico de tres metros, colocado a mano con calcarenita suelta en Los Escullos, sobre una duna fósil que hace cien mil años fue fondo del mar. No lleva cartel ni nombre.",
    "Junto al mar, en Los Escullos, hay un laberinto de piedra de tres metros. Un solo camino. Ninguna decisión y ninguna forma de perderse. OOLITA lleva ese camino a través de la piedra, el papel y el código.",
)
replace_all(
    "en/index.html",
    "OOLITA begins with a three-metre classical labyrinth, built from stone at Los Escullos, on a fossil dune that was seabed a hundred thousand years ago. No sign, no name.",
    "Beside the sea at Los Escullos lies a three-metre stone labyrinth. One path. No decisions and no way to get lost. OOLITA carries that path through stone, paper and code.",
)

# Make following the journey to 3 January the clear recurring invitation.
replace_all("index.html", "Seguir la apertura", "Seguir el camino hasta el 3 de enero")
replace_all("en/index.html", "Follow the opening", "Follow the path to 3 January")

# State what subscribers will actually receive, in the project's own register.
replace_all(
    "index.html",
    "Una sola lista. Elige lo que quieres seguir: mundo 3D, libro, publicaciones de campo o ediciones textiles.",
    "Notas ocasionales desde Los Escullos: los domingos, la apertura del mundo 3D, el libro y las ediciones de campo. Tú eliges qué seguir.",
)
replace_all(
    "en/index.html",
    "One list. Choose what you want to follow: the 3D world, book, field publications or textile editions.",
    "Occasional notes from Los Escullos: the Sundays, the 3D opening, the book and field editions. You choose what to follow.",
)
replace_all("index.html", "Sin publicidad · baja cuando quieras", "Sólo cuando haya algo que contar · baja cuando quieras")
replace_all("en/index.html", "No advertising · unsubscribe any time", "Only when there is something to share · unsubscribe any time")

# Keep future directions real but subordinate to the work that already exists.
replace_all(
    "index.html",
    "OOLITA seguirá siendo un solo laberinto, en Los Escullos. Alrededor de ese camino, el proyecto empieza a crecer en publicaciones de campo, ediciones textiles y colaboraciones que invitan a niños y adultos a mirar Cabo de Gata más despacio y más de cerca.",
    "OOLITA seguirá siendo un solo laberinto, en Los Escullos. Alrededor de ese camino desarrolla publicaciones de campo, ediciones textiles y colaboraciones arraigadas en Cabo de Gata.",
)
replace_all(
    "index.html",
    "Entre las líneas en desarrollo hay cuadernos para recorrer el territorio en familia, ensayos con color natural y posibles colaboraciones con artesanos locales en torno a saberes materiales como la fibra de pita.",
    "Crecerán despacio y sólo se presentarán cuando exista una forma concreta: para acompañar visitas más atentas, hacer visible el conocimiento local y cuidar el paisaje vivo.",
)
replace_all("index.html", "La intención no es llevar más gente a un solo punto. Es acompañar visitas más lentas, hacer visible el conocimiento local y cuidar el paisaje vivo.", "")
replace_all(
    "en/index.html",
    "OOLITA will remain one labyrinth at Los Escullos. Around that path, the project is growing into field publications, textile editions and collaborations that help children and adults look more closely at Cabo de Gata.",
    "OOLITA will remain one labyrinth at Los Escullos. Around that path it is developing field publications, textile editions and collaborations rooted in Cabo de Gata.",
)
replace_all(
    "en/index.html",
    "Directions in development include field books for family visits, experiments with natural colour, and possible collaborations with local makers around material traditions such as pita fibre.",
    "They will grow slowly and will only be presented when they take a concrete form: supporting more attentive visits, local knowledge and care for the living landscape.",
)
replace_all("en/index.html", "The aim is not to bring more people to one point. It is to support slower visits, local knowledge and care for the living landscape.", "")

# Replace the telephone-like reminder wording with the action actually offered.
replace_reminder("laberinto/index.html", "es")
replace_reminder("en/labyrinth/index.html", "en")

# Turn the collaboration page into three specific, quiet routes.
collab_es = '''<section class="tramo env" id="formas-de-colaborar" data-soft-marketing-collaboration>
<span class="rot">Tres formas de empezar</span><h2 class="grande">Una conversación concreta.</h2>
<p class="parr">Escribe con el nombre de tu organización, lugar, público y calendario aproximado. No hace falta preparar una propuesta formal.</p>
<a class="fila" href="mailto:oolita@tutamail.com?subject=OOLITA%20%C2%B7%20librer%C3%ADa%20o%20distribuci%C3%B3n"><span class="n">01</span><span class="nom">Librerías y distribución</span><span class="glo">Libro · ediciones · puntos de venta</span></a>
<a class="fila" href="mailto:oolita@tutamail.com?subject=OOLITA%20%C2%B7%20educaci%C3%B3n%20o%20cultura"><span class="n">02</span><span class="nom">Educación y cultura</span><span class="glo">Encargos · actividades · publicaciones</span></a>
<a class="fila" href="mailto:oolita@tutamail.com?subject=OOLITA%20%C2%B7%20materiales%20y%20oficios"><span class="n">03</span><span class="nom">Materiales y oficios</span><span class="glo">Colaboraciones locales de pequeña escala</span></a>
</section>'''
collab_en = '''<section class="tramo env" id="ways-to-work" data-soft-marketing-collaboration>
<span class="rot">Three ways to begin</span><h2 class="grande">A specific conversation.</h2>
<p class="parr">Write with the name of your organisation, location, audience and approximate timing. There is no need to prepare a formal proposal.</p>
<a class="fila" href="mailto:oolita@tutamail.com?subject=OOLITA%20%C2%B7%20bookshop%20or%20distribution"><span class="n">01</span><span class="nom">Bookshops and distribution</span><span class="glo">Book · editions · stockists</span></a>
<a class="fila" href="mailto:oolita@tutamail.com?subject=OOLITA%20%C2%B7%20education%20or%20culture"><span class="n">02</span><span class="nom">Education and culture</span><span class="glo">Commissions · activities · publications</span></a>
<a class="fila" href="mailto:oolita@tutamail.com?subject=OOLITA%20%C2%B7%20materials%20and%20making"><span class="n">03</span><span class="nom">Materials and making</span><span class="glo">Small-scale local collaborations</span></a>
</section>'''
insert_before_contact("colaborar/index.html", collab_es, 'id="formas-de-colaborar"')
insert_before_contact("en/work-with-oolita/index.html", collab_en, 'id="ways-to-work"')


def patch_overdue_sundays(path: str, language: str) -> None:
    target, text = read(path)
    today = datetime.now(ZoneInfo("Europe/Madrid")).date().isoformat()
    pending = "awaiting publication" if language == "en" else "pendiente de publicación"

    def cell(match: re.Match[str]) -> str:
        tag = match.group(0)
        if "is-published" in tag:
            return tag
        date_match = re.search(r'data-date="(\d{4}-\d{2}-\d{2})"', tag)
        if not date_match or date_match.group(1) >= today:
            return tag
        tag = tag.replace(" is-current", "")
        tag = re.sub(r'(<span class="sunday-tile-state" data-sunday-state>)[^<]*(</span>)', rf'\1{pending}\2', tag)
        return tag

    text = re.sub(r'<a\b[^>]*data-sunday-tile[^>]*>[\s\S]*?</a>', cell, text, flags=re.I)
    # Upgrade the client-side state calculation for future elapsed Sundays.
    if "const isPast=tile.dataset.date<today;" not in text:
        text = text.replace(
            "const isToday=tile.dataset.date===today;\n    const state=",
            "const isToday=tile.dataset.date===today;\n    const isPast=tile.dataset.date<today;\n    const state=",
        )
        if language == "en":
            text = text.replace(
                "state.textContent=isToday?(lang==='en'?'today':'hoy'):'';",
                "state.textContent=isToday?'today':(isPast?'awaiting publication':'');",
            )
        else:
            # The same embedded bilingual script exists on both pages.
            text = text.replace(
                "state.textContent=isToday?(lang==='en'?'today':'hoy'):'';",
                "state.textContent=isToday?(lang==='en'?'today':'hoy'):(isPast?(lang==='en'?'awaiting publication':'pendiente de publicación'):'');",
            )
    target.write_text(text, encoding="utf-8")


patch_overdue_sundays("domingos/index.html", "es")
patch_overdue_sundays("en/sundays/index.html", "en")

# Regression checks.
required = {
    "index.html": ["Junto al mar, en Los Escullos", "Seguir el camino hasta el 3 de enero", "Notas ocasionales desde Los Escullos", "Sólo cuando haya algo que contar"],
    "en/index.html": ["Beside the sea at Los Escullos", "Follow the path to 3 January", "Occasional notes from Los Escullos", "Only when there is something to share"],
    "laberinto/index.html": ["te avisaré el 3 de enero"],
    "en/labyrinth/index.html": ["I will let you know on 3 January"],
    "colaborar/index.html": ['id="formas-de-colaborar"', "Librerías y distribución", "Educación y cultura", "Materiales y oficios"],
    "en/work-with-oolita/index.html": ['id="ways-to-work"', "Bookshops and distribution", "Education and culture", "Materials and making"],
    "domingos/index.html": ["const isPast=tile.dataset.date<today;"],
    "en/sundays/index.html": ["const isPast=tile.dataset.date<today;"],
}
for path, needles in required.items():
    _, text = read(path)
    for needle in needles:
        if needle not in text:
            raise SystemExit(f"Soft-marketing invariant missing in {path}: {needle}")

for path, forbidden in {
    "index.html": ["proyecto editorial y de trabajo de campo arraigado", "Sin publicidad · baja cuando quieras"],
    "en/index.html": ["place-based publishing and fieldwork project rooted", "No advertising · unsubscribe any time"],
}.items():
    _, text = read(path)
    for needle in forbidden:
        if needle in text:
            raise SystemExit(f"Soft-marketing obsolete copy remains in {path}: {needle}")

sitemap = ROOT / "sitemap.xml"
if not sitemap.is_file():
    raise SystemExit("Missing sitemap.xml")
ET.register_namespace("", "http://www.sitemaps.org/schemas/sitemap/0.9")
tree = ET.parse(sitemap)
root = tree.getroot()
ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
seen: set[str] = set()
for url_el in root.findall("sm:url", ns):
    loc = url_el.find("sm:loc", ns)
    if loc is None or not loc.text or not loc.text.strip().startswith(BASE):
        continue
    route = loc.text.strip()[len(BASE):] or "/"
    if route not in CHANGED_PATHS:
        continue
    seen.add(route)
    lastmod = url_el.find("sm:lastmod", ns)
    if lastmod is None:
        lastmod = ET.SubElement(url_el, "{http://www.sitemaps.org/schemas/sitemap/0.9}lastmod")
    lastmod.text = LASTMOD
missing = sorted(CHANGED_PATHS - seen)
if missing:
    raise SystemExit(f"Soft-marketing URLs missing from sitemap: {missing}")
tree.write(sitemap, encoding="utf-8", xml_declaration=True)

print("OOLITA soft-marketing engagement pass validated successfully.")
