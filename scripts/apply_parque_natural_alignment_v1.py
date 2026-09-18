#!/usr/bin/env python3
"""Parque Natural alignment pass (letter of 10 September 2026).

The visitor-pressure pass (#98) rewrote the reader-facing labyrinth pages and
stripped every published coordinate. It did not reach three places where the
site still presents the labyrinth as a free, permanent, sign-posted destination,
because none of them are body prose:

- the structured data shared by every page: a Place with a postal address, a
  hasMap value and isAccessibleForFree, plus a WebPage description that offers
  "Coordinates and access" and "Cómo llegar";
- poster 07 on /carteles/ and /en/posters/, whose caption is the plainest
  invitation left on the site ("público, permanente y siempre abierto"), and the
  same sentence in the reel bank;
- the geo meta block (ICBM / geo.position / geo.placename), which names the
  exact locality on 24 pages and was left holding an empty ";" after the
  coordinate strip.

It also carries two approved editorial changes: the 3D world stops being framed
as a substitute for people who cannot travel, and the independence statement
moves into the footer so it is present on whichever page is shared.

Runs after apply_visitor_pressure_v1.py, before audit_static_integrity_v1.py.
Fail closed: none of the retired wording may survive anywhere.
"""
from __future__ import annotations

from pathlib import Path
import json
import re
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
if not ROOT.is_dir():
    raise SystemExit(f"Missing built site: {ROOT}")

changed: list[str] = []


def edit(path: Path, fn) -> bool:
    text = path.read_text(encoding="utf-8")
    new = fn(text)
    if new != text:
        path.write_text(new, encoding="utf-8")
        return True
    return False


# --------------------------------------------------------------------------
# 1 — shared structured data: the Place stops being an addressable free venue.
# --------------------------------------------------------------------------
# The labyrinth's own Place node, shared by every page. Scoped edits only: the
# Sunday articles legitimately carry isAccessibleForFree on their own schema,
# which is about reading them, not about walking into a protected enclave.
LUGAR_NODE = re.compile(
    r'\{"@type":"Place","@id":"https://oolita\.es/#lugar".*?\}(?=,\{"@type"|\]|\})',
    re.S,
)
LUGAR_SUBS = (
    # a postal address is a map pin in another notation
    (re.compile(r'"address":\{"@type":"PostalAddress"[^{}]*\},?'), ""),
    # left mangled by the map-link strip; nothing should carry a map value
    (re.compile(r'"hasMap":"[^"]*",?'), ""),
    # "free and open to all" is the exact framing the Park objected to
    (re.compile(r'"isAccessibleForFree":\s*(?:true|false),?'), ""),
    ('"name":"Laberinto OOLITA — Los Escullos"', '"name":"Laberinto OOLITA"'),
    (", al sur del Castillo de San Felipe, Los Escullos, en el Parque Natural",
     ", en el Parque Natural"),
)

# /cabo-de-gata/ carries its own Place for the area. The page keeps Los Escullos
# in its prose; the machine layer drops to the locality without a postal record.
PLACE_SUBS = (
    ('"name":"Los Escullos","address":{"@type":"PostalAddress",'
     '"addressLocality":"Níjar","addressRegion":"Almería","addressCountry":"ES"}',
     '"name":"Los Escullos"'),
)


def clean_lugar(text: str) -> str:
    def fix(match: re.Match) -> str:
        node = match.group(0)
        for old, new in LUGAR_SUBS:
            node = old.sub(new, node) if isinstance(old, re.Pattern) else node.replace(old, new)
        return node

    text = LUGAR_NODE.sub(fix, text)

    # Parse nested nodes so access flags on the artwork and either language's
    # Place cannot escape the legacy string substitutions above.
    def clean_schema(match: re.Match) -> str:
        data = json.loads(match.group(2))
        changed = False

        def walk(value):
            nonlocal changed
            if isinstance(value, dict):
                if value.get('@id') in {'https://oolita.es/#lugar', 'https://oolita.es/#obra'}:
                    for key in ('publicAccess', 'isAccessibleForFree'):
                        if key in value:
                            del value[key]
                            changed = True
                for child in value.values():
                    walk(child)
            elif isinstance(value, list):
                for child in value:
                    walk(child)

        walk(data)
        if not changed:
            return match.group(0)
        return match.group(1) + json.dumps(data, ensure_ascii=False, separators=(',', ':')) + match.group(3)

    return re.sub(r'(<script\b[^>]*type=["\']application/ld\+json["\'][^>]*>)(.*?)(</script>)',
                  clean_schema, text, flags=re.S | re.I)


DESTINATION_SUBS = (
    (', junto al Castillo de San Felipe,', ','),
    (', beside the Castillo de San Felipe,', ','),
    (', junto al Castillo de San Felipe en Los Escullos,', ', en Cabo de Gata-Níjar,'),
    (' beside the Castillo de San Felipe at Los Escullos,', ' in Cabo de Gata-Níjar,'),
    ('Se puede caminar hoy mismo: ', 'La misma senda continúa en papel y en el navegador: '),
    ('You can walk it today: ', 'The same path continues on paper and in the browser: '),
)


WEBPAGE_SUBS = (
    ('"name":"Laberinto de Los Escullos: cómo llegar · OOLITA"',
     '"name":"El laberinto · OOLITA"'),
    ('"name":"Los Escullos labyrinth: how to get there · OOLITA"',
     '"name":"The labyrinth · OOLITA"'),
    ("Cómo llegar, qué esperar y cómo acercarse con cuidado.",
     "No se señaliza, no se indica cómo llegar y no se promociona como destino."),
    ("Visit the three-metre stone labyrinth at Los Escullos, Cabo de Gata. "
     "Free, no booking, beside Castillo de San Felipe. Coordinates and access.",
     "A three-metre stone labyrinth in Cabo de Gata-Níjar, laid by hand in 2021. "
     "It is not signposted, not promoted as a destination, and no directions are given."),
    ("No se señaliza, no se indica cómo llegar y no se promociona como destino.",
     "El laberinto de piedra de OOLITA: piedras sueltas, dunas fósiles y cuidado del lugar."),
    ("A three-metre stone labyrinth in Cabo de Gata-Níjar, laid by hand in 2021. "
     "It is not signposted, not promoted as a destination, and no directions are given.",
     "OOLITA's stone labyrinth: loose stones, fossil dunes and care for the place."),
)

FAQ_SUBS = (
    ('"name":"¿Es gratis? ¿Hay que reservar?","acceptedAnswer":{"@type":"Answer",'
     '"text":"Es no se promociona como destino. No hay personal; si lo visitas, '
     'acércate con cuidado y respeto por el entorno."}',
     '"name":"¿Se puede visitar?","acceptedAnswer":{"@type":"Answer",'
     '"text":"OOLITA no promociona el laberinto como destino ni indica cómo llegar. '
     'No hay personal ni servicios; si llegas por tu cuenta, ve por sendero, '
     'no pises las dunas fósiles y no muevas piedras."}'),
    ('"name":"Is it free? Do I need to book?","acceptedAnswer":{"@type":"Answer",'
     '"text":"There is no ticket or booking. The labyrinth is unstaffed; if you visit, '
     'approach it lightly and respectfully."}',
     '"name":"Can it be visited?","acceptedAnswer":{"@type":"Answer",'
     '"text":"OOLITA does not promote the labyrinth as a destination and gives no '
     'directions. There are no staff and no facilities; if you find your own way there, '
     'keep to the path, stay off the fossil dunes and move no stones."}'),
    ('"text":"OOLITA no promociona el laberinto como destino ni indica cómo llegar. '
     'No hay personal ni servicios; si llegas por tu cuenta, ve por sendero, '
     'no pises las dunas fósiles y no muevas piedras."',
     '"text":"No damos indicaciones para llegar al laberinto. En el parque, permanece '
     'en los senderos; no pises las dunas fósiles ni muevas piedras."'),
    ('"text":"OOLITA does not promote the labyrinth as a destination and gives no '
     'directions. There are no staff and no facilities; if you find your own way there, '
     'keep to the path, stay off the fossil dunes and move no stones."',
     '"text":"We do not give directions to the labyrinth. In the park, keep to the '
     'marked paths; stay off the fossil dunes and move no stones."'),
)

# --------------------------------------------------------------------------
# 2 — geo meta: the locality broadcast, and the empty pair left behind.
# --------------------------------------------------------------------------
GEO_META = re.compile(
    r'\s*<meta\s+name=["\'](?:ICBM|geo\.position|geo\.placename|geo\.region)["\'][^>]*>',
    re.I,
)

# --------------------------------------------------------------------------
# 3 — poster 07: the plainest invitation on the site, caption and metadata.
# --------------------------------------------------------------------------
POSTER_SUBS = (
    ("Oolita es un laberinto clásico de tres metros en Los Escullos. "
     "Es público, permanente y está siempre abierto. No hace falta reservar. "
     "Camina despacio y con respeto.",
     "Oolita es un laberinto clásico de tres metros, colocado a mano con piedra suelta. "
     "No se señaliza ni se promociona como destino. Camina despacio y con respeto."),
    ("Oolita is a three-metre classical labyrinth at Los Escullos. "
     "It is public, permanent and always open. No booking is required. "
     "Walk slowly and respectfully.",
     "Oolita is a three-metre classical labyrinth, laid by hand in loose stone. "
     "It is not signposted and not promoted as a destination. "
     "Walk slowly and respectfully."),
    ("Oolita es un laberinto clásico de tres metros en Los Escullos: "
     "público, permanente y siempre abierto.",
     "Oolita es un laberinto clásico de tres metros, colocado a mano con piedra suelta."),
    ("Oolita is a three-metre classical labyrinth at Los Escullos: "
     "public, permanent and always open.",
     "Oolita is a three-metre classical labyrinth, laid by hand in loose stone."),
    # the reel bank carries the same caption, line-broken
    ("Oolita es un laberinto clásico de piedra en Los Escullos. Es público, permanente "
     "y está siempre abierto. No hace falta reservar. Camina despacio y con respeto.",
     "Oolita es un laberinto clásico de piedra, colocado a mano con piedra suelta. "
     "No se señaliza ni se promociona como destino. Camina despacio y con respeto."),
    ("Oolita is a classical stone labyrinth at Los Escullos. It is public, permanent "
     "and always open. No booking is required. Walk slowly and respectfully.",
     "Oolita is a classical stone labyrinth, laid by hand in loose stone. "
     "It is not signposted and not promoted as a destination. "
     "Walk slowly and respectfully."),
    ("Oolita es un laberinto clásico de tres metros, colocado a mano con piedra suelta. "
     "No se señaliza ni se promociona como destino. Camina despacio y con respeto.",
     "Oolita es un laberinto clásico de tres metros, trazado a mano con piedras sueltas "
     "en 2021. El entorno es frágil: permanece en los senderos y deja las piedras "
     "donde están."),
    ("Oolita is a three-metre classical labyrinth, laid by hand in loose stone. "
     "It is not signposted and not promoted as a destination. "
     "Walk slowly and respectfully.",
     "Oolita is a three-metre classical labyrinth, laid by hand from loose stones "
     "in 2021. The ground around it is fragile: keep to the paths and leave the "
     "stones where they are."),
    ("Oolita es un laberinto clásico de piedra, colocado a mano con piedra suelta. "
     "No se señaliza ni se promociona como destino. Camina despacio y con respeto.",
     "Oolita es un laberinto clásico de piedra, trazado a mano con piedras sueltas "
     "en 2021. El entorno es frágil: permanece en los senderos y deja las piedras "
     "donde están."),
    ("Oolita is a classical stone labyrinth, laid by hand in loose stone. "
     "It is not signposted and not promoted as a destination. "
     "Walk slowly and respectfully.",
     "Oolita is a classical stone labyrinth, laid by hand from loose stones in "
     "2021. The ground around it is fragile: keep to the paths and leave the "
     "stones where they are."),
)

# --------------------------------------------------------------------------
# 3b — the homepage fact table: a coordinate row that survived as a label with
# the locality for a value. Preserve the Labyrinth Locator directory link and
# its structured-data reference; the listing is being updated separately.
# Same block on /404/.
# --------------------------------------------------------------------------
FACT_ROW = re.compile(
    r'\s*<div><span class="k">(?:Coordenadas|Coordinates)</span>'
    r'<span class="v">.*?</span></div>',
    re.S,
)
FACT_SUBS = (
    ('<span class="k">Lugar</span><span class="v">Los Escullos, Níjar</span>',
     '<span class="k">Lugar</span><span class="v">Cabo de Gata-Níjar</span>'),
    ('<span class="k">Place</span><span class="v">Los Escullos, Níjar</span>',
     '<span class="k">Place</span><span class="v">Cabo de Gata-Níjar</span>'),
)

# --------------------------------------------------------------------------
# 3c — the artwork description on the homepage still placed the labyrinth in
# the UNESCO Geopark, which is the association the letter asks us to drop, and
# still said "sobre las dunas fósiles" after that wording was corrected to
# "junto a" everywhere else.
# --------------------------------------------------------------------------
ARTWORK_SUBS = (
    ("con piedras sueltas sobre las dunas fósiles de Los Escullos, en el Geoparque "
     "UNESCO de Cabo de Gata-Níjar.",
     "con piedras sueltas en terreno junto a las dunas fósiles, en Cabo de Gata-Níjar, "
     "Almería."),
    ("from stone on land beside the fossil dunes of Los Escullos, in the Cabo de "
     "Gata-Níjar UNESCO Geopark.",
     "from stone on land beside the fossil dunes, in Cabo de Gata-Níjar, Almería."),
)

# --------------------------------------------------------------------------
# 4 — the 3D world is an intended way to walk it, not a consolation prize.
# --------------------------------------------------------------------------
WORLD_SUBS = (
    ("El mundo digital lleva el mismo recorrido al navegador para personas separadas "
     "de Los Escullos por la distancia, el coste o la movilidad. El lugar sigue siendo "
     "Los Escullos; el acceso cambia de material.",
     "El mundo digital lleva el mismo recorrido al navegador. No sustituye a la piedra: "
     "es otra manera de caminarlo, pensada como tal desde el principio. El lugar sigue "
     "estando en Cabo de Gata-Níjar; el acceso cambia de material."),
    ("The digital world carries the same route into the browser for people separated "
     "from Los Escullos by distance, cost or mobility. Los Escullos remains the place; "
     "access changes material.",
     "The digital world carries the same route into the browser. It does not stand in "
     "for the stone: it is another way to walk it, intended as one from the start. "
     "The place remains in Cabo de Gata-Níjar; access changes material."),
    ("El mundo digital lleva el mismo recorrido al navegador. No sustituye a la piedra: "
     "es otra manera de caminarlo, pensada como tal desde el principio. El lugar sigue "
     "estando en Cabo de Gata-Níjar; el acceso cambia de material.",
     "El mundo digital se pensó desde el principio como otra forma de recorrer el mismo "
     "camino. Cabo de Gata-Níjar sigue siendo el lugar de la obra; en el navegador, "
     "el recorrido toma otra forma."),
    ("The digital world carries the same route into the browser. It does not stand in "
     "for the stone: it is another way to walk it, intended as one from the start. "
     "The place remains in Cabo de Gata-Níjar; access changes material.",
     "The digital world was planned from the start as another way to follow the same "
     "path. Cabo de Gata-Níjar remains the place of the work; in the browser, the "
     "path takes another form."),
)

# --------------------------------------------------------------------------
# 5 — the independence statement moves into the footer, on every page.
# --------------------------------------------------------------------------
FOOTER_ES = ('<div class="env" style="margin-top:1.4rem"><span class="rot oolita-independence" style="display:block;line-height:2">OOLITA es un proyecto independiente. '
             'No está vinculado, respaldado, autorizado ni promovido por el Parque Natural '
             'de Cabo de Gata-Níjar, la Junta de Andalucía ni ninguna otra '
             'administración.</span></div>')
FOOTER_EN = ('<div class="env" style="margin-top:1.4rem"><span class="rot oolita-independence" style="display:block;line-height:2">OOLITA is an independent project. '
             'It is not connected to, endorsed by, authorised by or promoted by the '
             'Cabo de Gata-Níjar Natural Park, the Junta de Andalucía or any other '
             'administration.</span></div>')


def apply_page(path: Path) -> None:
    rel = path.relative_to(ROOT).as_posix()
    english = rel == "en/index.html" or rel.startswith("en/")

    def transform(text: str) -> str:
        text = clean_lugar(text)
        for old, new in (PLACE_SUBS + WEBPAGE_SUBS + FAQ_SUBS + POSTER_SUBS
                         + WORLD_SUBS + FACT_SUBS + ARTWORK_SUBS + DESTINATION_SUBS):
            text = old.sub(new, text) if isinstance(old, re.Pattern) else text.replace(old, new)
        text = GEO_META.sub("", text)
        text = FACT_ROW.sub("", text)
        text = re.sub(r'"sameAs":\[\]\s*,?', '', text)
        # tidy any comma the JSON removals left doubled or dangling
        text = re.sub(r',\s*,', ',', text)
        text = re.sub(r',\s*\}', '}', text)
        if "oolita-independence" not in text and "</footer>" in text:
            line = FOOTER_EN if english else FOOTER_ES
            text = text.replace("</footer>", line + "</footer>", 1)
        return text

    if edit(path, transform):
        changed.append(rel)


for page in sorted(ROOT.rglob("*.html")):
    apply_page(page)

for data in sorted(ROOT.rglob("*.json")):
    def transform(text: str) -> str:
        for old, new in POSTER_SUBS:
            text = text.replace(old, new)
        return text

    if edit(data, transform):
        changed.append(data.relative_to(ROOT).as_posix())

# --------------------------------------------------------------------------
# 6 — fail-closed sweep.
# --------------------------------------------------------------------------
BANNED = (
    "streetAddress",
    "público, permanente",
    "public, permanent",
    "No hace falta reservar",
    "No booking is required",
    "¿Es gratis? ¿Hay que reservar?",
    "Is it free? Do I need to book?",
    "Cómo llegar, qué esperar",
    "Coordinates and access",
    "Si no puedes llegar a Los Escullos",
    "If you cannot get to Los Escullos",
    "cómo llegar · OOLITA",
    "how to get there · OOLITA",
    "Se puede caminar hoy mismo",
    "You can walk it today",
    "junto al Castillo de San Felipe",
    "beside the Castillo de San Felipe",
    'name="ICBM"',
    'name="geo.position"',
    'name="geo.placename"',
    'name="geo.region"',
    "separadas de Los Escullos por la distancia",
    "separated from Los Escullos by distance",
    "Geoparque UNESCO",
    "UNESCO Geopark",
    "sobre las dunas fósiles",
    '<span class="k">Coordenadas</span>',
    '<span class="k">Coordinates</span>',
)

leaks: list[str] = []
pages = sorted(ROOT.rglob("*.html"))
for page in pages:
    rel = page.relative_to(ROOT).as_posix()
    text = page.read_text(encoding="utf-8")
    for needle in BANNED:
        if needle in text:
            leaks.append(f"{rel}: {needle}")
    if "</footer>" in text and "oolita-independence" not in text:
        leaks.append(f"{rel}: footer independence statement missing")
    for node in LUGAR_NODE.findall(text):
        for forbidden in ("PostalAddress", '"hasMap"', "isAccessibleForFree", '"publicAccess"'):
            if forbidden in node:
                leaks.append(f"{rel}: labyrinth Place node still carries {forbidden}")

for data in sorted(ROOT.rglob("*.json")):
    text = data.read_text(encoding="utf-8")
    for needle in ("público, permanente", "public, permanent",
                   "No hace falta reservar", "No booking is required"):
        if needle in text:
            leaks.append(f"{data.relative_to(ROOT).as_posix()}: {needle}")

if leaks:
    print("OOLITA Parque Natural alignment pass failed:")
    for item in leaks:
        print(f"- {item}")
    raise SystemExit(1)

print(
    f"OOLITA Parque Natural alignment pass applied to {len(changed)} files: "
    "Place address, map value and free-access flag removed from structured data; "
    "wayfinding titles and descriptions retired; poster 07 and the reel caption no longer "
    "advertise a permanent open destination; locality geo meta removed; 3D world reframed; "
    "independence statement published in the footer of every page."
)
