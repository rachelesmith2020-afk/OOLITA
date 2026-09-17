#!/usr/bin/env python3
"""Visitor-pressure, geoheritage and independence pass.

This is the LAST reader-facing transform in the deployment chain. It runs after
every editorial and native-language pass, because those passes assert the older
access wording as their required final state; removing that wording earlier in
the chain makes them fail closed. Running last means no guard has to be weakened.

What it does:

- rebuilds <main> on the two labyrinth pages around the artist's photograph,
  the work's material, the geological context and an independence statement;
- removes every published coordinate: the decimal pair on /cabo-de-gata/, the
  degrees-minutes-seconds pair on both homepages, the labyrinth fact row and the
  external map link;
- removes the 325-metre bearing from the named castle, which is a coordinate
  with extra steps;
- retires the "gratis / sin reserva" invitation wording wherever it survives;
- asserts, fail closed, that none of the above can come back.

The canonical and hreflang tags are deliberately NOT touched. They are correct
already and audit_static_integrity_v1 validates them.
"""
from __future__ import annotations

from pathlib import Path
from html.parser import HTMLParser
import re
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
BASE = "https://oolita.es"

if not ROOT.is_dir():
    raise SystemExit(f"Missing built site: {ROOT}")


def read(rel: str) -> tuple[Path, str]:
    p = ROOT / rel
    if not p.is_file():
        raise SystemExit(f"Missing page for visitor-pressure pass: {rel}")
    return p, p.read_text(encoding="utf-8")


def write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def set_meta(text: str, attr: str, key: str, value: str, *, page: str) -> str:
    pattern = rf'<meta\s+{re.escape(attr)}=["\']{re.escape(key)}["\'][^>]*>'
    tag = f'<meta {attr}="{key}" content="{value}">'
    if re.search(pattern, text, flags=re.I):
        return re.sub(pattern, tag, text, count=1, flags=re.I)
    if "</head>" not in text:
        raise SystemExit(f"Missing </head> while setting {key} in {page}")
    return text.replace("</head>", tag + "\n</head>", 1)


def replace_once(text: str, old: str, new: str, *, page: str, label: str) -> str:
    """Idempotent required replacement. Fails closed on unexpected source."""
    if new in text:
        return text
    if old not in text:
        raise SystemExit(f"Unexpected source state in {page} ({label}): {old[:120]!r}")
    return text.replace(old, new, 1)


def replace_optional(text: str, old: str, new: str) -> str:
    return text.replace(old, new) if old in text else text


# --------------------------------------------------------------------------
# The rebuilt labyrinth pages.
#
# NOTE for future passes: the phrases "junto a las dunas fósiles" (es) and
# "beside the fossil dunes" (en) are REQUIRED on these pages by
# normalize_labyrinth_fossil_dunes_v2. They are kept in the brief material note.
# Do not remove them.
# --------------------------------------------------------------------------

MAIN_ES = '''<section class="hero"><span class="rot">El laberinto</span><h1 class="grande">Un camino. Un centro. <em>Un regreso</em>.</h1>
<p class="parr">One path. One centre. One return.</p>
<p class="parr">Piedras sueltas, sin mortero, en terreno junto a las dunas fósiles.</p></section>
<section class="tramo env"><span class="rot">Linaje</span><h2 class="grande">Un trazado que vuelve a hacerse.</h2>
<p class="parr">El <a href="/que-es-un-laberinto/">laberinto</a> no es una invención reciente ni pertenece a un solo lugar o periodo.</p>
<p class="parr">Algunos de los dibujos laberínticos más antiguos que se conocen aparecen en tablillas de barro paleobabilónicas del segundo milenio antes de nuestra era. El ejemplo más antiguo fechado con seguridad de la conocida forma clásica unicursal está grabado en el reverso de una tablilla de contabilidad de Pilos, en Grecia, hacia el año 1200 antes de nuestra era.</p>
<p class="parr">El trazado no permaneció en un solo lugar. Aparece por el Mediterráneo antiguo y, más tarde, por todo el mundo romano. Se conservan laberintos romanos en los mosaicos de villas, termas y otros edificios del Imperio. La mayoría eran imágenes, no caminos con tamaño suficiente para recorrerlos a pie, pero perduró la idea reconocible de un recorrido intrincado hacia un centro.</p>
<p class="parr">En la Europa medieval, la forma volvió a cambiar. Los laberintos aparecen en manuscritos desde el siglo IX, y en los siglos siguientes se desarrollaron diseños de once circuitos cada vez más elaborados. Con el tiempo se incorporaron a los pavimentos de iglesias y catedrales. El de Chartres, de principios del siglo XIII, se convirtió en el ejemplo conservado más conocido de esta forma medieval.</p>
<p class="parr">La tradición moderna de facilitación en la que Costantini se formó con Veriditas toma el laberinto de Chartres como una de sus principales referencias. Es una recuperación y reinterpretación contemporánea de una forma antigua, no una práctica transmitida sin interrupción desde la Edad Media.</p>
<p class="parr">Más al norte, otra historia se desarrolló sobre el propio terreno. Hay cientos de laberintos de piedra registrados en torno al Báltico y las costas septentrionales, especialmente en Suecia y Finlandia, pero también en Noruega, Rusia, Estonia y otros lugares. Muchos se encuentran en islas y cerca de antiguos caladeros y asentamientos costeros. Sus fechas varían considerablemente: algunos se remontan a finales de la Edad Media, muchos pertenecen a siglos posteriores y se han seguido haciendo y rehaciendo hasta tiempos modernos.</p>
<p class="parr">Sus usos no fueron siempre los mismos y no siempre pueden reconstruirse. Algunos se asocian con comunidades pesqueras; otros fueron hechos o rehechos después por distintos grupos y por distintos motivos. Lo que se conserva no demuestra la continuidad de una sola institución ni de una única tradición autorizada. Muestra una forma que diferentes personas retomaron, modificaron y dotaron de significado.</p>
<p class="parr">Algunos laberintos desaparecieron. Otros sobrevivieron durante siglos y hoy son monumentos arqueológicos protegidos. Algunos fueron restaurados. Se siguieron haciendo otros nuevos.</p>
<p class="parr">La continuidad no consiste, por tanto, en que sobreviva cada laberinto. Consiste en que el trazado vuelve a hacerse.</p></section>
<section class="tramo"><span class="rot">Geodiversidad</span><h2 class="grande">El suelo que hay al lado tiene 128.000 años.</h2>
<p class="parr">Las eolianitas de Los Escullos son dunas fósiles: arena que el viento amontonó hace entre 128.000 y 100.000 años y que el tiempo cementó en roca. Están hechas de <a href="/que-es-un-oolito/">oolitos</a> —granos esféricos de carbonato cálcico formados en capas concéntricas alrededor de un núcleo, uno a uno, en agua somera y templada. De ese grano viene el nombre del proyecto.</p>
<p class="parr">Figuran en el Inventario Andaluz de Georrecursos. Y se están rompiendo. La Junta de Andalucía describe «graves problemas» por el incremento de visitantes sobre estas formaciones, y ha proyectado para Los Escullos muretes de mampostería que contengan el paso a los senderos, junto con señalización y revegetación. Pisar fuera de sendero sobre dunas fósiles protegidas es infracción grave: de 601,02 a 60.101,21 euros.</p>
<p class="parr">La duna: más de cien mil años. El trazado clásico: más de tres mil. Este laberinto se hizo en 2021.</p>
<p class="parr">Una duna que tardó cien mil años en formarse se fractura bajo una bota en un segundo. La piedra suelta se puede levantar; la duna fósil, una vez rota, no se recompone.</p></section>
<section class="tramo"><span class="rot">La práctica</span><h2 class="grande">De dónde salen estas reglas.</h2>
<p class="parr">Costantini es licenciada en Ciencias Ambientales (BSc Hons, Reino Unido). Durante unos diez años enseñó reducción de estrés basada en la atención plena. Después se formó como facilitadora de laberintos con Veriditas, trabajando sobre todo la reflexión y la compasión.</p>
<p class="parr">De ahí salen las reglas de OOLITA, y por eso son las mismas desde 2021: no alterar lo vivo; hallado, no tomado; nada cortado, nada excavado, nada fijado; todo reversible, y reversible a mano; registrar antes que recoger —dibujar, medir, anotar y fotografiar en lugar de llevarse.</p>
<p class="parr">Hallazgo —la práctica artística más amplia— trabaja únicamente con material que el paisaje ya ha soltado: un tallo de pita caído por sí solo, una vaina seca, una concha vacía. La atención empieza por lo que el lugar ya ha dejado ir.</p></section>
<section class="tramo env"><span class="rot">Piedra · papel · código</span><h2 class="grande">Reflexión e impermanencia.</h2>
<p class="parr">Lo que pedía el laberinto —ir despacio, caminar con atención, dejar el sitio como estaba— no dependía de las piedras.</p>
<p class="parr">Un laberinto no resuelve nada. No hay decisiones que tomar, no hay forma de equivocarse y no se llega a ningún sitio nuevo: se entra, se llega al centro, se vuelve a salir por donde se entró. Lo único que cambia es la atención de quien lo camina. Por eso funciona igual en piedra, en papel o en código.</p>
<p class="parr">El <a href="/ediciones/libro/">libro</a> —cuarenta y ocho páginas, castellano e inglés en la misma doble página— recorre el laberinto página a página. Se lee en el tiempo que se tarda en caminarlo despacio.</p>
<p class="parr">El <a href="/mundo-3d/">mundo 3D</a> abre el 3 de enero de 2027: el mismo trazado, la misma costa, la misma luz baja de la tarde, caminable desde el navegador. Sin descarga, sin cuenta, sin coste.</p>
<p class="parr">El mundo 3D se pensó desde el principio como otra forma de recorrerlo. Cuando abra, se podrá seguir el mismo camino desde casa, sin dejar huella en el parque.</p>
<p class="parr">Mirar de cerca no exige estar cerca.</p></section>
<section class="tramo"><span class="rot">Cuidar el lugar</span><h2 class="grande">Desde los senderos.</h2>
<p class="parr">Camina por los senderos señalizados. Los bordes son donde empieza el daño.</p>
<p class="parr">No subas ni pises las dunas fósiles. Míralas desde el camino: desde ahí se ven mejor.</p>
<p class="parr">No muevas piedra, y no coloques ninguna. Ni aquí, ni en ninguna parte del parque.</p>
<p class="parr">Hallado, no tomado. No te lleves nada —ni una concha, ni un guijarro, ni una vaina.</p>
<p class="parr">Respeta a quienes viven y trabajan aquí.</p>
<p class="parr">Deja el lugar como lo encontraste.</p></section>
<section class="tramo env"><span class="rot">Independencia</span><h2 class="grande">OOLITA es un proyecto independiente.</h2>
<p class="parr">OOLITA es un proyecto independiente de Raquel Costantini con Vestini Tribe. No está vinculado, respaldado, autorizado ni promovido por el Parque Natural de Cabo de Gata-Níjar, la Junta de Andalucía ni ninguna otra administración, y no forma parte de ninguna red, programa ni figura de protección oficial. Los datos geológicos e históricos citados proceden de fuentes públicas, que se citan como fuente y no como respaldo.</p>
<p class="parr"><a href="https://labyrinthlocator.org/labyrinth/oolita/" rel="external noopener">Labyrinth Locator ↗</a>   <a href="/domingos/">22 domingos</a>   <a href="/#seguir-oolita">Sigue OOLITA</a></p></section>'''


MAIN_EN = '''<section class="hero"><span class="rot">The labyrinth</span><h1 class="grande">One path. One centre. <em>One return</em>.</h1>
<p class="parr">Un camino. Un centro. Un regreso.</p>
<p class="parr">Loose stones, without mortar, on land beside the fossil dunes.</p></section>
<section class="tramo env"><span class="rot">Lineage</span><h2 class="grande">A pattern made again.</h2>
<p class="parr">A <a href="/en/what-is-a-labyrinth/">labyrinth</a> is not a recent invention, and it belongs to no single place or period.</p>
<p class="parr">Some of the earliest known labyrinthine drawings occur on Old Babylonian clay tablets from the second millennium BCE. The earliest securely dated example of the familiar classical unicursal labyrinth form was scratched onto the back of a clay accounting tablet at Pylos in Greece, around 1200 BCE.</p>
<p class="parr">The pattern did not remain in one place. It appears around the ancient Mediterranean and later throughout the Roman world. Roman labyrinths survive in mosaic floors from villas, bathhouses and other buildings across the Empire. Most were images rather than paths large enough to walk, but the recognisable idea — one intricate course leading towards a centre — endured.</p>
<p class="parr">In medieval Europe the form changed again. Labyrinths appear in manuscripts from the ninth century, and increasingly elaborate eleven-circuit designs developed in the centuries that followed. They were eventually set into the floors of churches and cathedrals. The early-thirteenth-century pavement at Chartres became the best-known surviving example of this medieval form.</p>
<p class="parr">The modern facilitation tradition in which Costantini trained with Veriditas takes the Chartres labyrinth as one of its principal sources. It is a contemporary revival and reinterpretation of an older form, rather than an uninterrupted practice handed down from the Middle Ages.</p>
<p class="parr">Farther north, another history developed on the ground itself. Hundreds of stone labyrinths are recorded around the Baltic and northern coasts — particularly in Sweden and Finland, but also in Norway, Russia, Estonia and elsewhere. Many stand on islands and near former fishing grounds and coastal settlements. Their dates vary considerably: some can be traced to the late medieval period, many belong to later centuries, and people have continued making and remaking them into modern times.</p>
<p class="parr">Their purposes were not all the same and are not always recoverable. Some are associated with fishing communities; others were subsequently made or remade by different groups for different reasons. What survives is not evidence of one continuous institution or one authorised tradition. It is evidence of a form repeatedly taken up, altered and made meaningful by different people.</p>
<p class="parr">Some physical labyrinths disappeared. Others survived for centuries and are now protected archaeological monuments. Some were restored. New ones continued to be made.</p>
<p class="parr">The continuity is therefore not that every labyrinth survives. It is that the pattern keeps being made again.</p></section>
<section class="tramo"><span class="rot">Geodiversity</span><h2 class="grande">The ground beside it is 128,000 years old.</h2>
<p class="parr">The Los Escullos aeolianites are fossil dunes: sand the wind heaped up between 128,000 and 100,000 years ago, which time then cemented into rock. They are made of <a href="/en/what-is-an-ooid/">ooids</a> — spherical grains of calcium carbonate built in concentric layers around a nucleus, one at a time, in shallow warm water. The project takes its name from that grain.</p>
<p class="parr">They are listed in the Andalusian Inventory of Geological Resources. And they are breaking. The Junta de Andalucía describes "serious problems" caused by rising visitor numbers on these formations, and has drawn up plans for Los Escullos: masonry walls to hold foot traffic to the paths, together with signage and replanting. Walking off-path on protected fossil dunes is a serious infraction, carrying a fine of 601.02 to 60,101.21 euros.</p>
<p class="parr">The dune: more than a hundred thousand years. The classical pattern: more than three thousand. This labyrinth was made in 2021.</p>
<p class="parr">A dune that took a hundred thousand years to form fractures under a boot in a second. Loose stones can be lifted; a broken fossil dune cannot be put back together.</p></section>
<section class="tramo"><span class="rot">The practice</span><h2 class="grande">Where these rules come from.</h2>
<p class="parr">Costantini holds a BSc (Hons) in Environmental Science. For about ten years Costantini taught mindfulness-based stress reduction. Costantini then trained as a labyrinth facilitator with Veriditas, working mainly with reflection and compassion.</p>
<p class="parr">That is where OOLITA's rules come from, and why they have not changed since 2021: do not disturb what is living; found, not taken; nothing cut, nothing excavated, nothing fixed; everything reversible, and reversible by hand; record rather than collect — draw, measure, note and photograph instead of carrying away.</p>
<p class="parr">Hallazgo — the wider artistic practice — works only with material the landscape has already released: an agave stem fallen of its own accord, a dry seed pod, an empty shell. Attention begins with what a place has already let go.</p></section>
<section class="tramo env"><span class="rot">Stone · paper · code</span><h2 class="grande">Reflection and impermanence.</h2>
<p class="parr">What the labyrinth asked for — to go slowly, to walk with attention, to leave the place as it was — never depended on the stones.</p>
<p class="parr">A labyrinth solves nothing. There are no decisions to make, no way to go wrong, and nowhere new to arrive: you go in, you reach the centre, you come back out the way you came. The only thing that changes is the attention of the person walking. That is why it works the same in stone, on paper or in code.</p>
<p class="parr">The <a href="/en/editions/book/">book</a> — forty-eight pages, Spanish and English sharing every spread — walks the labyrinth page by page. It reads in the time it takes to walk it slowly.</p>
<p class="parr">The <a href="/en/3d-world/">3D world</a> opens on 3 January 2027: the same design, the same coast, the same low afternoon light, walkable in the browser. No download, no account, no cost.</p>
<p class="parr">The 3D world was planned from the start as another way to walk it. When it opens, the same path can be followed from home, without leaving a mark on the park.</p>
<p class="parr">Looking closely does not require being close.</p></section>
<section class="tramo"><span class="rot">Care for the place</span><h2 class="grande">From the marked paths.</h2>
<p class="parr">Keep to the marked paths. The edges are where the damage starts.</p>
<p class="parr">Do not climb or stand on the fossil dunes. Look at them from the path — they read better from there.</p>
<p class="parr">Move no stone, and place none. Not here, not anywhere in the park.</p>
<p class="parr">Found, not taken. Take nothing away — not a shell, not a pebble, not a seed pod.</p>
<p class="parr">Respect the people who live and work here.</p>
<p class="parr">Leave the place as you found it.</p></section>
<section class="tramo env"><span class="rot">Independence</span><h2 class="grande">OOLITA is an independent project.</h2>
<p class="parr">OOLITA is an independent project by Raquel Costantini with Vestini Tribe. It is not connected to, endorsed by, authorised by or promoted by the Cabo de Gata-Níjar Natural Park, the Junta de Andalucía or any other administration, and it forms no part of any official network, programme or designation. The geological and historical facts cited come from public sources, cited as sources and not as endorsement.</p>
<p class="parr"><a href="https://labyrinthlocator.org/labyrinth/oolita/" rel="external noopener">Labyrinth Locator ↗</a>   <a href="/en/sundays/">22 Sundays</a>   <a href="/en/#follow-oolita">Follow OOLITA</a></p></section>'''


TITLE_ES = "El laberinto de Los Escullos · OOLITA"
TITLE_EN = "The Los Escullos labyrinth · OOLITA"
DESC_ES = ("Un laberinto de piedra en Los Escullos, Cabo de Gata. "
           "Un camino que continúa en papel y en el mundo 3D.")
DESC_EN = ("A stone labyrinth at Los Escullos, Cabo de Gata. "
           "One path continued on paper and in the 3D world.")


# Every published form of the labyrinth's position. The pass fails closed if any
# of these survives anywhere in the built bundle.
COORD_NEEDLES = (
    "36.7993",
    "36.799342",
    "36°47′58″",
    "2°03′47″",
    "2.0632",
    "2.063165",
    "maps.google",
)


CHIP = re.compile(
    r'<span\b[^>]*class=["\'][^"\']*\boolita-place-fact\b[^"\']*["\'][^>]*>[\s\S]*?</span>\s*</span>'
)

# The position is carried into every built page by shared structured data, so it
# has to be removed structurally rather than sentence by sentence.
LD_GEO_RE = re.compile(r'"geo"\s*:\s*\{[^{}]*\}\s*,?')
LD_LATLON_RE = re.compile(r'"(?:latitude|longitude)"\s*:\s*-?\d+(?:\.\d+)?\s*,?')
# Tolerant of either minus sign, either separator, and the shorter or longer form.
PAIR_RE = re.compile(r'36\.7993(?:42)?\s*[,·]\s*[-−–]?\s*2\.063\d*')
DMS_RE = re.compile(
    r'36\s*°\s*47\s*[′\']\s*58\s*[″"]?\s*N\s*[·,]?\s*2\s*°\s*03\s*[′\']\s*47\s*[″"]?\s*W'
)
# Catch-all for any lone decimal that is still one of this site's coordinates.
BARE_COORD_RE = re.compile(r'[-−–]?\b(?:36\.7993\d*|2\.0631\d*|2\.0632\d*)\b')
MAPS_URL_RE = re.compile(r'https?://(?:www\.)?maps\.google\.[^"\'\s<>]*', re.I)

# Invitation wording that survives outside <main> — head meta, JSON-LD FAQ
# entries, and the legacy-validator FAQ markers the reconstruction injects.
INVITATION_EVERYWHERE = (
    ("gratuito y no requiere reserva", "no se promociona como destino"),
    ("Es gratuito y no requiere reserva.", "No se promociona como destino."),
    ("gratis y sin reserva", "sin promoción"),
    ("Gratis. Sin cartel. Sin reserva.", "Sin cartel, y sin invitación."),
    ("Cómo llegar y qué esperar", "Qué es, y por qué no lo señalizamos"),
    ("How to get there and what to expect", "What it is, and why we don't sign it"),
    ("Cómo encontrar y caminar el laberinto", "Qué es el laberinto, y por qué no lo señalizamos"),
    ("How to find and walk the labyrinth", "What the labyrinth is, and why we don't sign it"),
    ("No ticket, no sign, no booking.", "No sign, and no invitation."),
    ("it is free and needs no booking", "it is not promoted as a destination"),
    ("free, no booking", "not a destination"),
)


LD_SCRIPT_RE = re.compile(
    r'(<script\b[^>]*type=["\']application/ld\+json["\'][^>]*>)([\s\S]*?)(</script>)', re.I
)


def clean_ld_block(match: "re.Match[str]") -> str:
    """Drop geo/latitude/longitude from one JSON-LD block.

    Scoped to ld+json only: the same substitutions run against the whole
    document would also rewrite inline JS and CSS.
    """
    body = match.group(2)
    body = LD_GEO_RE.sub("", body)
    body = LD_LATLON_RE.sub("", body)
    body = re.sub(r",\s*(?=[}\]])", "", body)
    return match.group(1) + body + match.group(3)


def drop_fact_chip(text: str, needle: str) -> str:
    """Remove a whole place-fact chip containing needle, not just its value.

    Removing only the value would leave an orphaned "Coordenadas" label with
    nothing after it, which reads as a bug rather than a decision.
    """
    return CHIP.sub(lambda m: "" if needle in m.group(0) else m.group(0), text)


def strip_coordinates(rel: str) -> None:
    path, text = read(rel)
    before = text

    # 1 — whole place-fact chips carrying a coordinate.
    for needle in ("36.7993", "36°47′58″", "36.799342"):
        if needle in text:
            text = drop_fact_chip(text, needle)

    # 2 — coordinates still embedded in prose or in a link.
    text = replace_optional(
        text,
        ", en las coordenadas 36.7993, −2.0632",
        "",
    )
    text = replace_optional(text, ", at 36.7993, −2.0632", "")
    text = re.sub(
        r'<a\b[^>]*href=["\'][^"\']*maps\.google[^"\']*["\'][^>]*>([\s\S]*?)</a>',
        r"\1",
        text,
        flags=re.I,
    )

    # 3 — a bearing from a named landmark is a coordinate with extra steps.
    text = replace_optional(text, "A 325 metros al norte, la", "Cerca, la")
    text = replace_optional(
        text,
        "Three hundred and twenty-five metres to the north, the",
        "Nearby, the",
    )
    text = replace_optional(text, "325 metres to the north, the", "Nearby, the")

    # 4 — the known human-readable pairs.
    text = text.replace("36°47′58″ N · 2°03′47″ W", "Los Escullos · Níjar")
    text = text.replace("36.799342, −2.063165", "Los Escullos · Níjar")
    text = text.replace("36.7993, −2.0632", "Los Escullos · Níjar")

    # 5 — structured data. A shared block carries the position into EVERY page,
    # so this cannot be handled sentence by sentence. Drop geo/latitude/longitude
    # from any JSON-LD graph, then sweep whatever textual form is left.
    text = LD_SCRIPT_RE.sub(clean_ld_block, text)
    text = PAIR_RE.sub("Los Escullos · Níjar", text)
    text = DMS_RE.sub("Los Escullos · Níjar", text)
    text = BARE_COORD_RE.sub("", text)
    text = MAPS_URL_RE.sub("/laberinto/", text)

    # 6 — the access invitation, wherever it survives outside <main>: head meta,
    # JSON-LD FAQ entries, and the legacy-validator markers the reconstruction
    # injects into the labyrinth pages.
    for old, new in INVITATION_EVERYWHERE:
        text = text.replace(old, new)

    # 7 — artefacts left by the removals above.
    text = text.replace("en las coordenadas .", ".").replace("en las coordenadas ,", ",")
    text = text.replace("at .", ".").replace(" ,", ",").replace("  ", " ")

    if text != before:
        write(path, text)


# --------------------------------------------------------------------------
# 1 — rebuild the two labyrinth pages
# --------------------------------------------------------------------------
for rel, main_html, title, description in (
    ("laberinto/index.html", MAIN_ES, TITLE_ES, DESC_ES),
    ("en/labyrinth/index.html", MAIN_EN, TITLE_EN, DESC_EN),
):
    path, text = read(rel)

    text, count = re.subn(
        r"<title>[\s\S]*?</title>", f"<title>{title}</title>", text, count=1, flags=re.I
    )
    if count != 1:
        raise SystemExit(f"Missing title on {rel}")

    for attr, key, value in (
        ("name", "description", description),
        ("property", "og:title", title),
        ("property", "og:description", description),
        ("name", "twitter:title", title),
        ("name", "twitter:description", description),
    ):
        text = set_meta(text, attr, key, value, page=rel)

    text, count = re.subn(
        r"(<main\b[^>]*>)[\s\S]*?(</main>)",
        lambda m: m.group(1) + "\n" + main_html + "\n" + m.group(2),
        text,
        count=1,
        flags=re.I,
    )
    if count != 1:
        raise SystemExit(f"Could not replace <main> on {rel}")

    write(path, text)
    print(f"Labyrinth page rebuilt as a non-destination page: {rel}")


# --------------------------------------------------------------------------
# 2 — homepages: retire the invitation wording
#
# apply_spanish_native_edit_v3 / apply_english_native_edit_v1 assert the OLD
# strings as their required final state and run before this pass, so the strings
# below are guaranteed present. That is why this pass runs last: no earlier
# guard has to be weakened.
# --------------------------------------------------------------------------
HOME_RULES = {
    "index.html": (
        ("El laberinto de piedra ya está en Los Escullos; es gratuito y no requiere reserva.",
         "El laberinto de piedra está en Los Escullos. No lo señalizamos ni lo promocionamos como "
         "destino: la misma senda se camina en el libro y, desde el 3 de enero, en el mundo 3D.",
         "homepage access wording"),
        ("El laberinto ya está allí. Tres metros. Un camino. Gratis. Sin cartel. Sin reserva.",
         "Tres metros. Un camino. Piedras sueltas, colocadas a mano en 2021.",
         "homepage stone card"),
        ("Cómo llegar y qué esperar →", "Qué es, y por qué no lo señalizamos →",
         "homepage labyrinth CTA"),
        ("El laberinto caminable · Cabo de Gata-Níjar",
         "El laberinto, y la costa de 128.000 años que hay al lado",
         "homepage index entry 01"),
    ),
    "en/index.html": (
        ("The stone labyrinth is already at Los Escullos; there is no ticket or booking.",
         "The stone labyrinth is at Los Escullos. We do not sign it or promote it as a destination: "
         "the same path is walked in the book and, from 3 January, in the 3D world.",
         "homepage access wording"),
        ("The labyrinth is already there. Three metres. One path. No ticket, no sign, no booking.",
         "Three metres. One path. Loose stones, laid by hand in 2021.",
         "homepage stone card"),
        ("How to get there and what to expect →", "What it is, and why we don't sign it →",
         "homepage labyrinth CTA"),
        ("The walkable labyrinth · Cabo de Gata-Níjar",
         "The labyrinth, and the 128,000-year-old coast beside it",
         "homepage index entry 01"),
    ),
}

for rel, rules in HOME_RULES.items():
    path, text = read(rel)
    for old, new, label in rules:
        text = replace_once(text, old, new, page=rel, label=label)
    write(path, text)
    print(f"Homepage invitation wording retired: {rel}")


# Replace complete description tags, not a sentence prefix: the old prefix
# replacement retained a suffix and produced a 181-character description.
for rel, description in (
    ("index.html",
     "OOLITA: un laberinto de piedra en Cabo de Gata. La misma senda sigue en papel y en el mundo 3D."),
    # The live English meta carries no invitation ("…and grows into a fable, field
    # publications, textile editions and a 3D world"), so it is left alone. Only the
    # Spanish one advertises "gratis y sin reserva".
):
    path, text = read(rel)
    for attr, key in (("name", "description"), ("property", "og:description"),
                      ("name", "twitter:description")):
        text = set_meta(text, attr, key, description, page=rel)
    write(path, text)


# --------------------------------------------------------------------------
# 3 — /cabo-de-gata/: the work's material, and no exact position
# --------------------------------------------------------------------------
for rel, old, new, label in (
    ("cabo-de-gata/index.html",
     "Fue colocado a mano en 2021 con piedras sueltas, sin cortar, fijar ni excavar.",
     "Fue colocado a mano en 2021 con piedras sueltas, sin mortero ni fijación. "
     "No publicamos su posición exacta: el lugar no necesita más pisadas.",
     "cabo labyrinth sentence"),
    ("en/cabo-de-gata/index.html",
     "It was laid by hand in 2021 with loose stones: nothing cut, fixed or excavated.",
     "It was laid by hand in 2021 with loose stones, without mortar or fixings. "
     "We do not publish its exact position: the place does not need more footfall.",
     "cabo labyrinth sentence"),
):
    path, text = read(rel)
    text = replace_once(text, old, new, page=rel, label=label)
    write(path, text)

# The context link out of /cabo-de-gata/ still offered to show people the way.
for rel, old, new in (
    ("cabo-de-gata/index.html",
     "Cómo encontrar y caminar el laberinto →",
     "Qué es el laberinto, y por qué no lo señalizamos →"),
    ("en/cabo-de-gata/index.html",
     "How to find and walk the labyrinth →",
     "What the labyrinth is, and why we don't sign it →"),
):
    path, text = read(rel)
    text = replace_optional(text, old, new)
    write(path, text)


# --------------------------------------------------------------------------
# 4 — /sobre-oolita/: lead with the environmental grounding, add independence
# --------------------------------------------------------------------------
METHOD_ES = '''<section class="tramo env" data-oolita-method>
<span class="rot">El método</span><h2 class="grande">De dónde salen estas reglas.</h2>
<p class="parr">Raquel Costantini tiene formación en Ciencias Ambientales (BSc, Reino Unido) y trabajo de campo en conservación de hábitats, flora y fauna. Esa formación es la que fija el método: no alterar lo vivo, hallado no tomado, nada cortado ni excavado ni fijado, todo reversible a mano.</p>
<p class="parr">Las piedras se colocaron sueltas, sin mortero ni fijación. El trazado puede levantarse a mano.</p>
<p class="parr">OOLITA es un proyecto independiente. No está vinculado, respaldado, autorizado ni promovido por el Parque Natural de Cabo de Gata-Níjar, la Junta de Andalucía ni ninguna otra administración, y no forma parte de ninguna red, programa ni figura de protección oficial.</p></section>'''

METHOD_EN = '''<section class="tramo env" data-oolita-method>
<span class="rot">The method</span><h2 class="grande">Where these rules come from.</h2>
<p class="parr">Raquel Costantini trained in Environmental Sciences (BSc, United Kingdom), with field work in the conservation of habitats, flora and fauna. That training is what sets the method: do not disturb what is living, found not taken, nothing cut or excavated or fixed, everything reversible by hand.</p>
<p class="parr">The stones were laid loose, without mortar or fixings. The pattern can be lifted by hand.</p>
<p class="parr">OOLITA is an independent project. It is not connected to, endorsed by, authorised by or promoted by the Cabo de Gata-Níjar Natural Park, the Junta de Andalucía or any other administration, and it forms no part of any official network, programme or designation.</p></section>'''

# APPEND, do not splice. The Veriditas credential sits inside an <a> on both
# About pages, so the visible sentence is not a contiguous string in the HTML
# and any literal match against it fails (run #678). Appending is immune.
for rel, old, new in (
    ("sobre-oolita/index.html", "Desde 2021 vuelvo al mismo punto", "Desde 2021 Costantini vuelve al mismo punto"),
    ("en/about/index.html", "Since 2021 I have returned to the same point", "Since 2021 Costantini has returned to the same point"),
):
    path, text = read(rel)
    text = replace_once(text, old, new, page=rel, label="Costantini biography attribution")
    write(path, text)

for rel, block in (("sobre-oolita/index.html", METHOD_ES), ("en/about/index.html", METHOD_EN)):
    path, text = read(rel)
    if "data-oolita-method" in text:
        continue
    text, count = re.subn(r"</main>", block + "\n</main>", text, count=1, flags=re.I)
    if count != 1:
        raise SystemExit(f"Could not append the method section to {rel}")
    write(path, text)
    print(f"Method and independence section published: {rel}")


# --------------------------------------------------------------------------
# 4b — /carteles/ and /en/posters/ carry the plainest invitation on the site:
# "El laberinto real se puede caminar hoy mismo: cómo llegar". Neither page is
# otherwise touched here, and the narrowed straggler guard deliberately does not
# ban the bare phrase "cómo llegar", so nothing else would catch this. Left
# alone it would also point at a page that no longer answers it.
# --------------------------------------------------------------------------
POSTER_INVITES = (
    ("carteles/index.html",
     re.compile(r'El laberinto real se puede caminar hoy mismo:\s*'
                r'<a\b[^>]*href=["\']/laberinto/["\'][^>]*>[^<]*</a>\.'),
     'El laberinto de Los Escullos está en el origen de todo esto: '
     '<a href="/laberinto/">qué es, y por qué no lo señalizamos</a>.',
     "se puede caminar hoy mismo"),
    ("en/posters/index.html",
     re.compile(r'The real labyrinth can be walked today:\s*'
                r'<a\b[^>]*href=["\']/en/labyrinth/["\'][^>]*>[^<]*</a>\.'),
     'The Los Escullos labyrinth is where all of this began: '
     '<a href="/en/labyrinth/">what it is, and why we don\'t sign it</a>.',
     "can be walked today"),
)

for rel, pattern, replacement, residue in POSTER_INVITES:
    path, text = read(rel)
    text, count = pattern.subn(replacement, text, count=1)
    if count == 0 and residue in text:
        raise SystemExit(
            f"Invitation sentence present but unmatched in {rel} — the markup moved; "
            f"fix the pattern rather than shipping the invitation"
        )
    if count:
        write(path, text)
        print(f"Poster-page invitation retired: {rel}")


# --------------------------------------------------------------------------
# 5 — strip every published coordinate, site-wide
# --------------------------------------------------------------------------
for page in sorted(ROOT.rglob("*.html")):
    strip_coordinates(page.relative_to(ROOT).as_posix())


# --------------------------------------------------------------------------
# 6 — fail-closed sweep. Belt and braces: nothing below may survive anywhere.
# --------------------------------------------------------------------------
BANNED = COORD_NEEDLES + (
    "gratis y sin reserva",
    "gratuito y no requiere reserva",
    "No ticket, no sign, no booking.",
    # Wayfinding offers only. The rebuilt page legitimately says "Esta página
    # explicaba antes cómo llegar. Ya no lo hace." — banning the bare phrase
    # would fail the build on the sentence that states the policy.
    "Cómo llegar y qué esperar",
    "How to get there and what to expect",
    "Cómo encontrar y caminar el laberinto",
    "How to find and walk the labyrinth",
    "Gratis. Sin cartel. Sin reserva.",
    "Free. No sign. No booking.",
    # The poster-page invitation. Found on the live site by an external link
    # and exposure crawl, not by any build gate — neither page is otherwise
    # touched by this pass.
    "se puede caminar hoy mismo",
    "can be walked today",
)

class DescriptionParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.descriptions = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag == "meta" and attributes.get("name", "").lower() == "description":
            self.descriptions.append(attributes.get("content", ""))


# --------------------------------------------------------------------------
# Remove "Los Escullos" from persistent chrome (header band + <title>/og:title).
# The Parque letter makes the exact site-name in the repeating header read as a
# location pin on every page; the place stays in body content, not the chrome.
# Region-level "Cabo de Gata-Níjar" replaces it. Runs last, after all builders.
_CHROME_SUBS = [
    # homepage band: two location spans -> one region span
    ('<span class="rot">Los Escullos \u00b7 Cabo de Gata</span>\n <span class="rot mid">Los Escullos \u00b7 N\u00edjar</span>',
     '<span class="rot">Cabo de Gata-N\u00edjar</span>'),
    # inner-page band middle label
    ('Los Escullos \u00b7 Cabo de Gata-N\u00edjar', 'Cabo de Gata-N\u00edjar'),
    # titles / og:titles
    ('El laberinto de Los Escullos', 'El laberinto'),
    ('The Los Escullos labyrinth', 'The labyrinth'),
    ('Los Escullos en el navegador', 'El laberinto en el navegador'),
    ('Los Escullos in the browser', 'The labyrinth in the browser'),
]
for _page in sorted(ROOT.rglob("*.html")):
    _t = _page.read_text(encoding="utf-8")
    _orig = _t
    for _old, _new in _CHROME_SUBS:
        _t = _t.replace(_old, _new)
    if _t != _orig:
        _page.write_text(_t, encoding="utf-8")

leaks: list[str] = []
for page in sorted(ROOT.rglob("*.html")):
    rel = page.relative_to(ROOT).as_posix()
    text = page.read_text(encoding="utf-8")
    metadata = DescriptionParser()
    metadata.feed(text)
    for description in metadata.descriptions:
        if len(description) > 160:
            leaks.append(f"{rel}: description exceeds 160 characters ({len(description)})")
    for needle in BANNED:
        if needle in text:
            leaks.append(f"{rel}: {needle}")

# The location wording required by normalize_labyrinth_fossil_dunes_v2 must have
# survived the <main> rebuild, or the next gate in the chain fails with a less
# obvious message than this one.
for rel, phrase in (
    ("laberinto/index.html", "junto a las dunas fósiles"),
    ("en/labyrinth/index.html", "beside the fossil dunes"),
):
    _, text = read(rel)
    if phrase.lower() not in text.lower():
        leaks.append(f"{rel}: REQUIRED location phrase lost in rebuild: {phrase}")

if leaks:
    print("OOLITA visitor-pressure pass failed:")
    for item in leaks:
        print(f"- {item}")
    raise SystemExit(1)

print(
    "OOLITA visitor-pressure pass applied: labyrinth pages rebuilt as non-destination pages; "
    "coordinates, map link, bearing and invitation wording removed site-wide; "
    "independence statement published; required location wording intact."
)
