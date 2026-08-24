#!/usr/bin/env python3
"""Bring public OOLITA editorial prose back to the voice of the book.

The book is the reference: concrete nouns, short sentences, physical detail,
repetition where it earns its place, and no synthetic connective language.
Published Sunday entries, book excerpts and legal/privacy copy are deliberately
left alone. This pass is idempotent and can run after every content-building
layer so later automation cannot quietly re-introduce generic marketing prose.
"""
from __future__ import annotations

from pathlib import Path
import re
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")

# Each tuple is (old variants, approved replacement). Variants allow the live
# mirror to contain either typographic or straight punctuation.
PATCHES: dict[str, list[tuple[tuple[str, ...], str]]] = {
    "index.html": [
        ((
            "OOLITA reúne la obra y la escritura de Raquel Costantini con la labor editorial de Vestini Tribe.",
        ),
         "Raquel Costantini hizo el laberinto y escribió el libro. Vestini Tribe publica OOLITA."),
        ((
            "Una imagen cada domingo. La obra se acumula hasta que se abra el camino digital.",
        ),
         "Una imagen cada domingo hasta que se abra el mundo."),
        ((
            "El tercero abre el 3 de enero de 2027 a las 00:00 CET. Un mundo en tres dimensiones que se camina desde el navegador, sin descarga, sin cuenta y sin coste: el mismo trazado, la misma costa y la misma luz baja de la tarde. Está hecho para quien no puede llegar hasta Almería —por distancia, por dinero o porque el cuerpo no lo permite— y aun así quiere caminarlo.",
            "El tercero abre el 3 de enero de 2027 a las 00:00 CET. Un mundo en tres dimensiones que se camina desde el navegador, sin descarga, sin cuenta y sin coste: el mismo trazado, la misma costa y la misma luz baja de la tarde. Está hecho para quien no puede llegar hasta Almería -por distancia, por dinero o porque el cuerpo no lo permite- y aun así quiere caminarlo.",
        ),
         "El tercero abre el 3 de enero de 2027 a las 00:00 CET. Se camina desde el navegador. Sin descarga. Sin cuenta. Sin coste. El mismo trazado. La misma costa. La misma luz baja de la tarde. No todo el mundo puede llegar a Almería. A veces es la distancia. A veces el dinero. A veces el cuerpo. El mismo camino queda abierto desde lejos."),
        ((
            "Piedra, papel y código recorren la misma senda. Un camino que no obliga a decidir nada deja la atención libre, y eso se ha vuelto difícil de encontrar. De ahí el subtítulo del libro, y de ahí la cuenta atrás: una fábula de laberinto para días ruidosos.",
        ),
         "Piedra. Papel. Código. Tres materiales, un camino. Un laberinto no pide decisiones. Sigues. El libro hace lo mismo. También la cuenta atrás: una fábula de laberinto para días ruidosos."),
        ((
            "OOLITA seguirá siendo un solo laberinto, en Los Escullos. Alrededor de ese camino desarrolla publicaciones de campo, ediciones textiles y colaboraciones arraigadas en Cabo de Gata.",
        ),
         "OOLITA seguirá teniendo un solo laberinto: el de Los Escullos. Alrededor de él vendrán publicaciones de campo, pequeñas ediciones textiles y colaboraciones hechas en Cabo de Gata."),
        ((
            "Crecerán despacio y sólo se presentarán cuando exista una forma concreta: para acompañar visitas más atentas, hacer visible el conocimiento local y cuidar el paisaje vivo.",
        ),
         "No se trata de llevar más gente al laberinto. Se trata de mirar Cabo de Gata más despacio, aprender de quien trabaja aquí y dejar el lugar como estaba."),
    ],
    "en/index.html": [
        ((
            "OOLITA brings together the art and writing of Raquel Costantini with the publishing work of Vestini Tribe.",
        ),
         "Raquel Costantini made the labyrinth and wrote the book. Vestini Tribe publishes OOLITA."),
        ((
            "One image each Sunday. The work accumulates until the digital path opens.",
        ),
         "One image each Sunday until the world opens."),
        ((
            "The third opens on 3 January 2027 at 00:00 CET. A three-dimensional world you walk from the browser — no download, no account, no cost: the same drawing, the same coastline, the same low afternoon light. It exists for anyone who cannot get to Almería because of distance, cost or accessibility, and still wants to walk it.",
            "The third opens on 3 January 2027 at 00:00 CET. A three-dimensional world you walk from the browser - no download, no account, no cost: the same drawing, the same coastline, the same low afternoon light. It exists for anyone who cannot get to Almería because of distance, cost or accessibility, and still wants to walk it.",
        ),
         "The third opens on 3 January 2027 at 00:00 CET. You walk it in the browser. No download. No account. No cost. The same drawing. The same coastline. The same low afternoon light. Not everyone can get to Almería. Sometimes it is distance. Sometimes money. Sometimes the body. The same path stays open from elsewhere."),
        ((
            "Stone, paper and code follow the same path. A path that asks you to decide nothing leaves your attention free, and that has become hard to come by. Hence the book’s subtitle, and hence the countdown: a labyrinth fable for loud days.",
            "Stone, paper and code follow the same path. A path that asks you to decide nothing leaves your attention free, and that has become hard to come by. Hence the book's subtitle, and hence the countdown: a labyrinth fable for loud days.",
        ),
         "Stone. Paper. Code. Three materials, one path. A labyrinth asks you to decide nothing. You follow. The book does the same. So does the countdown: a labyrinth fable for loud days."),
        ((
            "OOLITA will remain one labyrinth at Los Escullos. Around that path it is developing field publications, textile editions and collaborations rooted in Cabo de Gata.",
        ),
         "There will still be one OOLITA labyrinth: the one at Los Escullos. Around it will come field publications, small textile editions and collaborations made in Cabo de Gata."),
        ((
            "They will grow slowly and will only be presented when they take a concrete form: supporting more attentive visits, local knowledge and care for the living landscape.",
        ),
         "The point is not to bring more people to one labyrinth. It is to look at Cabo de Gata more slowly, learn from people who work here and leave the place as it was."),
    ],
    "sobre-oolita/index.html": [
        ((
            "OOLITA es el nombre público del proyecto que reúne una obra vinculada al lugar y la práctica editorial que crece a su alrededor. El laberinto de Los Escullos y el texto del libro OOLITA son obra de Raquel Costantini. Hallazgo es su práctica artística más amplia. Vestini Tribe publica el libro y las ediciones de OOLITA. Todo el proyecto se reúne en oolita.es.",
        ),
         "OOLITA tiene tres formas: el laberinto de Los Escullos, el libro y el mundo 3D. El laberinto y el texto del libro son obra de Raquel Costantini. Hallazgo es su práctica artística más amplia. Vestini Tribe publica el libro y las ediciones. Todo se reúne aquí: oolita.es."),
        ((
            "OOLITA forma parte de una práctica artística más amplia de Raquel Costantini. Hallazgo trabaja con observación, registro, objetos encontrados y paisaje. OOLITA toma esa atención y la convierte en camino, publicación, edición y trabajo de campo.",
        ),
         "OOLITA forma parte de la práctica artística de Raquel Costantini. Hallazgo trabaja con observación, registro, objetos encontrados y paisaje. En OOLITA, esa atención se vuelve camino, libro y trabajo de campo."),
    ],
    "en/about/index.html": [
        ((
            "OOLITA is the public identity of a project bringing together a place-based work and the publishing practice growing around it. The Los Escullos labyrinth and the text of the book OOLITA are works by Raquel Costantini. Hallazgo is her wider artistic practice. Vestini Tribe publishes the book and OOLITA editions. The whole project comes together at oolita.es.",
        ),
         "OOLITA has three forms: the labyrinth at Los Escullos, the book and the 3D world. The labyrinth and the text of the book are by Raquel Costantini. Hallazgo is her wider artistic practice. Vestini Tribe publishes the book and the editions. Everything meets here: oolita.es."),
        ((
            "OOLITA sits within Raquel Costantini's wider artistic practice. Hallazgo works with observation, recording, found objects and landscape. OOLITA turns that attention into path, publication, edition and fieldwork.",
        ),
         "OOLITA sits within Raquel Costantini's wider artistic practice. Hallazgo works with observation, recording, found objects and landscape. In OOLITA, that attention becomes a path, a book and fieldwork."),
    ],
    "ediciones/index.html": [
        ((
            "El libro y la camiseta son las primeras ediciones OOLITA. Abren una serie más amplia de publicaciones de campo, pequeñas piezas textiles y colaboraciones arraigadas en Cabo de Gata.",
        ),
         "El libro y la camiseta son las dos primeras ediciones. Después vendrán publicaciones de campo y pequeñas colaboraciones hechas en Cabo de Gata."),
        ((
            "Puede crecer hacia geología, viento y sombra, agua, salinas y aves, Posidonia, color, materiales locales y ejercicios de atención. No es una guía para recoger cosas: lo que se encuentra se observa y se deja donde pertenece.",
        ),
         "Puede incluir geología, viento y sombra, agua, salinas y aves, Posidonia, color y materiales locales. Cosas que mirar. Cosas que dibujar. Nada que llevarse."),
    ],
    "en/editions/index.html": [
        ((
            "The book and T-shirt are the first OOLITA editions. They begin a wider series of field publications, small textile works and collaborations rooted in Cabo de Gata.",
        ),
         "The book and T-shirt are the first two editions. After them will come field publications and small collaborations made in Cabo de Gata."),
        ((
            "It may grow across geology, wind and shadow, water, saltpans and birds, Posidonia, colour, local materials and exercises in attention. It is not a guide to collecting things: what is found is observed and left where it belongs.",
        ),
         "It may include geology, wind and shadow, water, saltpans and birds, Posidonia, colour and local materials. Things to notice. Things to draw. Nothing to take away."),
    ],
    "mundo-3d/index.html": [
        ((
            "El mundo digital no intenta sustituir ese lugar; da al mismo recorrido otro material, para que la distancia, el dinero o las posibilidades del cuerpo no decidan quién puede caminarlo.",
        ),
         "El mundo digital no sustituye Los Escullos. No todo el mundo puede llegar. A veces es la distancia. A veces el dinero. A veces el cuerpo. El mismo camino queda abierto en el navegador."),
        ((
            "Three.js no es el tema de OOLITA ni un efecto añadido a la obra: es la herramienta que permite que su tercera forma exista como espacio caminable en la web.",
        ),
         "Three.js es la herramienta que hace caminable la tercera forma en el navegador."),
        ((
            "La elección importa porque mantiene la entrada sencilla. El trabajo no necesita una aplicación propia ni una instalación: vive donde ya está oolita.es.",
        ),
         "Así la entrada sigue siendo sencilla. Sin aplicación. Sin instalación. Abres un enlace y caminas."),
        ((
            "El objetivo no es el realismo técnico por sí mismo, sino conservar suficiente lugar para que la atención pueda ir más despacio.",
        ),
         "No necesita parecer una fotografía. Necesita conservar suficiente lugar para que el camino funcione."),
        ((
            "Ninguno reemplaza a los otros: cada uno hace posible una forma distinta de recorrer la misma senda.",
            "Ninguno sustituye a los otros: cada uno hace posible una forma distinta de recorrer la misma senda.",
        ),
         "Ninguno sustituye a los otros. Cada uno deja recorrer el mismo camino en otro material."),
    ],
    "en/3d-world/index.html": [
        ((
            "The digital world does not try to replace that place; it gives the same path another material, so distance, money or physical access do not decide who can walk it.",
        ),
         "The digital world does not replace Los Escullos. Not everyone can get there. Sometimes it is distance. Sometimes money. Sometimes the body. The same path stays open in the browser."),
        ((
            "Three.js is not the subject of OOLITA and it is not an effect added to the work: it is the tool that allows its third form to exist as a walkable space on the web.",
        ),
         "Three.js is the tool that makes the third form walkable in the browser."),
        ((
            "That choice matters because it keeps the entrance simple. The work does not need its own app or an installation: it lives where oolita.es already lives.",
        ),
         "That keeps the entrance simple. No app. No installation. Open a link and walk."),
        ((
            "The aim is not technical realism for its own sake, but to preserve enough of the place for attention to slow down.",
        ),
         "It does not need to look photographic. It needs enough of the place for the walk to work."),
        ((
            "None replaces the others: each makes a different way of following the same path possible.",
        ),
         "None replaces the others. Each lets you follow the same path in another material."),
    ],
    "colaborar/index.html": [
        ((
            "Para librerías, alojamientos, educadores, organizaciones culturales y artesanos interesados en ediciones o proyectos de campo.",
        ),
         "Librerías, alojamientos, educadores, organizaciones culturales y artesanos pueden trabajar con OOLITA en libros, proyectos de campo y pequeñas ediciones."),
        ((
            "Distribución de publicaciones, encargos editoriales o educativos, actividades de observación y colaboraciones materiales de pequeña escala. Cada relación se define antes de nombrarla públicamente.",
        ),
         "Puede ser distribuir el libro, hacer una pequeña edición o preparar una actividad de campo para mirar, dibujar y registrar. Primero acordamos el trabajo. Después lo nombramos."),
        ((
            "OOLITA no ofrece una franquicia de laberintos. El laberinto de Los Escullos sigue siendo uno. Lo que puede crecer es la relación editorial con el territorio.",
        ),
         "Solo habrá un laberinto OOLITA: el de Los Escullos. Lo que puede viajar son los libros, el trabajo de campo y las colaboraciones."),
    ],
    "en/work-with-oolita/index.html": [
        ((
            "For bookshops, accommodation, educators, cultural organisations and makers interested in editions or field projects.",
        ),
         "Bookshops, places to stay, educators, cultural organisations and makers can work with OOLITA on books, field projects and small editions."),
        ((
            "Publication distribution, editorial or educational commissions, observation-based activities and small-scale material collaborations. Each relationship is agreed before it is named publicly.",
        ),
         "That might mean stocking the book, making a small edition, or building a field activity around looking, drawing and recording. We agree the work first. We name it afterwards."),
        ((
            "OOLITA does not offer a labyrinth franchise. The Los Escullos labyrinth remains one. What can grow is the editorial relationship with the territory.",
        ),
         "There will only be one OOLITA labyrinth: the one at Los Escullos. What can travel are the books, the fieldwork and the collaborations."),
    ],
    "cabo-de-gata/index.html": [
        ((
            "OOLITA empieza con un solo laberinto en Los Escullos. Alrededor de ese camino crece una práctica editorial y de trabajo de campo que mira Cabo de Gata a través del arte, la observación, los materiales y ediciones hechas con cuidado.",
        ),
         "OOLITA empieza con un solo laberinto en Los Escullos. Desde ese camino mira Cabo de Gata: la piedra, el viento, el agua, las aves, los materiales y la gente que trabaja aquí."),
        ((
            "Entre la piedra, el castillo y la orilla se forma el territorio que OOLITA observa y vuelve a registrar.",
        ),
         "Piedra, castillo y orilla. OOLITA vuelve a mirar el mismo lugar."),
        ((
            "Las ediciones textiles y los ensayos con color natural se desarrollarán despacio. Las colaboraciones con artesanos o productores locales sólo se nombrarán cuando exista un acuerdo real, y cada edición contará quién la hizo, dónde, con qué materiales y en qué cantidad.",
        ),
         "Las ediciones textiles y los ensayos con color natural irán despacio. Si una pieza se hace con alguien de aquí, se dirá quién la hizo, dónde, con qué materiales y cuántas hay."),
        ((
            "Con el tiempo, OOLITA podrá trabajar con librerías, alojamientos, educadores, organizaciones culturales y artesanos del territorio. Ninguna organización se presenta como socia hasta que exista un acuerdo.",
        ),
         "OOLITA puede trabajar con librerías, alojamientos, educadores, organizaciones culturales y artesanos de aquí. Primero se hace el trabajo. Después se nombra."),
    ],
    "en/cabo-de-gata/index.html": [
        ((
            "OOLITA begins with one labyrinth at Los Escullos. Around that path, a publishing and fieldwork practice is growing: looking at Cabo de Gata through art, observation, materials and carefully made editions.",
        ),
         "OOLITA begins with one labyrinth at Los Escullos. From that path it looks at Cabo de Gata: stone, wind, water, birds, materials and the people who work here."),
        ((
            "The stone, castle and shore form the territory OOLITA observes and records again.",
        ),
         "Stone, castle and shore. OOLITA looks at the same place again."),
        ((
            "Textile editions and experiments with natural colour will develop slowly. Collaborations with local makers or producers will only be named when a real agreement exists, and every edition will state who made it, where, with what materials and in what quantity.",
        ),
         "Textile editions and experiments with natural colour will go slowly. If something is made with someone here, it will say who made it, where, with what materials and how many there are."),
        ((
            "Over time, OOLITA may work with bookshops, accommodation, educators, cultural organisations and makers in the territory. No organisation is presented as a partner until an agreement exists.",
        ),
         "OOLITA may work with bookshops, places to stay, educators, cultural organisations and makers here. We do the work first. We name it afterwards."),
    ],
}


def apply_patch(text: str, variants: tuple[str, ...], new: str) -> tuple[str, bool, str]:
    if new in text:
        return text, False, "already"
    for old in variants:
        if old in text:
            return text.replace(old, new), True, "patched"
    return text, False, "missing"


def dedupe_spanish_home_intro(text: str) -> tuple[str, int]:
    phrase = (
        "Junto al mar, en Los Escullos, hay un laberinto de piedra de tres metros. "
        "Un solo camino. Ninguna decisión y ninguna forma de perderse. "
        "OOLITA lleva ese camino a través de la piedra, el papel y el código."
    )
    pattern = re.compile(r"<p\b[^>]*>\s*" + re.escape(phrase) + r"\s*</p>", re.I)
    matches = list(pattern.finditer(text))
    if len(matches) <= 1:
        return text, 0
    seen = 0
    removed = 0

    def repl(match: re.Match[str]) -> str:
        nonlocal seen, removed
        seen += 1
        if seen == 1:
            return match.group(0)
        removed += 1
        return ""

    return pattern.sub(repl, text), removed


patched_pages = 0
changed_items = 0
missing_targets: list[str] = []

for rel, rules in PATCHES.items():
    page = ROOT / rel
    if not page.is_file():
        # Some optional editorial pages are not in older mirrors; the global
        # investigator below still covers every HTML file that is present.
        print(f"voice audit: optional page absent: {rel}")
        continue
    text = page.read_text(encoding="utf-8")
    original = text
    for variants, new in rules:
        text, changed, status = apply_patch(text, variants, new)
        if changed:
            changed_items += 1
        elif status == "missing":
            missing_targets.append(f"{rel}: {variants[0][:72]}")

    if rel == "index.html":
        text, removed = dedupe_spanish_home_intro(text)
        if removed:
            changed_items += removed
            print(f"voice audit: removed {removed} duplicate Spanish hero paragraph(s)")

    if text != original:
        page.write_text(text, encoding="utf-8")
        patched_pages += 1
        print(f"voice audit: patched {rel}")
    else:
        print(f"voice audit: reviewed {rel}")

# High-signal synthetic prose markers. This scans every public HTML file,
# including metadata and structured text, not only the pages above. Legal and
# archival wording may remain formal; these particular markers are not needed
# anywhere in OOLITA's voice.
BANNED = {
    "hence": re.compile(r"\bhence\b", re.I),
    "delve": re.compile(r"\bdelv(?:e|es|ed|ing)\b", re.I),
    "tapestry": re.compile(r"\btapestry\b", re.I),
    "seamlessly": re.compile(r"\bseamless(?:ly)?\b", re.I),
    "moreover": re.compile(r"\bmoreover\b", re.I),
    "furthermore": re.compile(r"\bfurthermore\b", re.I),
    "testament to": re.compile(r"\btestament to\b", re.I),
}

violations: list[str] = []
for page in sorted(ROOT.rglob("*.html")):
    text = page.read_text(encoding="utf-8")
    rel = page.relative_to(ROOT)
    for label, pattern in BANNED.items():
        if pattern.search(text):
            violations.append(f"{rel}: {label}")

if missing_targets:
    print("voice audit: source wording drifted for some optional exact targets:")
    for item in missing_targets:
        print("  -", item)

if violations:
    print("OOLITA voice audit failed; synthetic prose markers remain:")
    for item in violations:
        print("  -", item)
    raise SystemExit(1)

print(
    f"OOLITA voice audit passed: {patched_pages} page(s) changed, "
    f"{changed_items} edit(s); all HTML checked for synthetic prose markers."
)
