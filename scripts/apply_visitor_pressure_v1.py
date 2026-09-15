#!/usr/bin/env python3
"""Visitor-pressure, geoheritage and independence pass.

This is the LAST reader-facing transform in the deployment chain. It runs after
every editorial and native-language pass, because those passes assert the older
access wording as their required final state; removing that wording earlier in
the chain makes them fail closed. Running last means no guard has to be weakened.

What it does:

- rebuilds <main> on the two labyrinth pages: the "how to get there" page becomes
  a "this is not a destination" page, with the existing-clearing fact, the
  128,000-year geoheritage case, the visitor-pressure case, the method grounding
  and an explicit non-affiliation statement;
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
# normalize_labyrinth_fossil_dunes_v2. They are kept in the opening paragraph.
# Do not remove them.
# --------------------------------------------------------------------------

MAIN_ES = '''<section class="hero"><span class="rot">El laberinto</span><h1 class="grande">Un camino. Un centro. <em>Un regreso</em>.</h1>
<p class="parr">One path. One centre. One return.</p>
<p class="parr">Un laberinto clásico de tres metros, colocado a mano en 2021 con piedras sueltas, en terreno junto a las dunas fósiles. En seco y sin fijar: no hay mortero, no se ha cortado nada, no se ha excavado nada. Un solo camino —sin bifurcaciones, sin callejones sin salida, sin forma de perderse. Se camina despacio.</p>
<p class="parr"><small>Trazado clásico · 3 m · piedras sueltas · 2021</small></p></section>
<section class="tramo env"><span class="rot">El origen</span><h2 class="grande">El claro que ya estaba.</h2>
<p class="parr">El laberinto no abrió el suelo donde está. Lo encontró abierto.</p>
<p class="parr">En 2021, en un año en que casi nadie se movía, se colocó sobre un claro que ya existía: terreno descubierto, sin vegetación, ya pisado. No se desbrozó. No se cortó ninguna planta. No se movió tierra. No se abrió suelo nuevo. Las piedras se pusieron en seco, sueltas, sin mortero y sin fijación —se levantan a mano en una mañana y el claro vuelve a ser exactamente lo que era.</p>
<p class="parr">Esa fue toda la decisión de diseño: que el sitio pudiera deshacerse sin dejar rastro.</p></section>
<section class="tramo"><span class="rot">El lugar</span><h2 class="grande">No es un destino.</h2>
<p class="parr">Esta página explicaba antes cómo llegar. Ya no lo hace.</p>
<p class="parr">No hay coordenadas, ni indicaciones desde el aparcamiento, ni distancias desde el castillo, ni un punto en el mapa. El laberinto no es un secreto: sencillamente no necesita visitas, y el lugar donde está necesita menos aún.</p>
<p class="parr">Tres metros de piedra no justifican un viaje. Lo que hay debajo sí merece que se sepa. Es distinto.</p></section>
<section class="tramo env"><span class="rot">Geodiversidad</span><h2 class="grande">Lo que hay debajo tiene 128.000 años.</h2>
<p class="parr">Las eolianitas de Los Escullos son dunas fósiles: arena que el viento amontonó hace entre 128.000 y 100.000 años y que el tiempo cementó en roca. Están hechas de <a href="/que-es-un-oolito/">oolitos</a> —granos esféricos de carbonato cálcico formados en capas concéntricas alrededor de un núcleo, uno a uno, en agua somera y templada. De ese grano viene el nombre del proyecto.</p>
<p class="parr">Figuran en el Inventario Andaluz de Georrecursos. Y se están rompiendo.</p>
<p class="parr">La Junta de Andalucía describe «graves problemas» por el incremento de visitantes sobre estas formaciones, y ha proyectado para Los Escullos muretes de mampostería de 40 × 40 cm que contengan el paso a los senderos, junto con señalización y revegetación. Pisar fuera de sendero sobre dunas fósiles protegidas es infracción grave: de 601,02 a 60.101,21 euros.</p>
<p class="parr">Una duna que tardó cien mil años en formarse se fractura bajo una bota en un segundo. No hay restauración posible. Esa es toda la aritmética.</p></section>
<section class="tramo"><span class="rot">Biodiversidad</span><h2 class="grande">Un lugar que ya recibe demasiado.</h2>
<p class="parr"><a href="/cabo-de-gata/">Cabo de Gata-Níjar</a> protege más de 49.000 hectáreas, de las cuales más de 12.000 son marinas.</p>
<p class="parr">Bajo el agua: praderas de <em>Posidonia oceanica</em> y <em>Cymodocea nodosa</em>, ambas hábitats de interés comunitario. Diecinueve cuevas marinas inventariadas, alguna de más de cuarenta metros. Más de 150 comunidades marinas distintas —la mayor diversidad de los quince espacios protegidos estudiados en el proyecto LIFE IP Intemares. Arrecifes de <em>Dendropoma lebeche</em>, catalogado como amenazado. La lapa ferruginosa, en peligro.</p>
<p class="parr">Fuera del agua: cormorán moñudo, gaviota de Audouin, flamencos en las salinas.</p>
<p class="parr">Y encima de todo eso, la presión. En agosto de 2026 el Parque ya había superado las denuncias de todo 2025 por actividades organizadas sin autorización. Se debate una tasa turística. Las calas soportan cada verano más gente de la que pueden sostener.</p>
<p class="parr">Ninguna de esas cifras necesita un visitante más por un laberinto de tres metros.</p></section>
<section class="tramo env"><span class="rot">El método</span><h2 class="grande">De dónde salen estas reglas.</h2>
<p class="parr">Raquel Costantini tiene formación en Ciencias Ambientales (BSc, Reino Unido) y trabajo de campo en conservación de hábitats, flora y fauna. No es un adorno biográfico: es de donde vienen las reglas de OOLITA, y por qué son las mismas desde 2021.</p>
<p class="parr">No alterar lo vivo. Hallado, no tomado. Nada cortado, nada excavado, nada fijado. Todo reversible, y reversible a mano. Registrar antes que recoger: dibujar, medir, anotar y fotografiar en lugar de llevarse.</p>
<p class="parr">Hallazgo —la práctica artística más amplia— trabaja únicamente con material que el paisaje ya ha soltado: un tallo de pita caído por sí solo, una vaina seca, una concha vacía. La atención empieza por lo que el lugar ya ha dejado ir.</p>
<p class="parr">El laberinto sigue la misma regla, y por eso está hecho de piedras sueltas sobre un claro que ya estaba.</p></section>
<section class="tramo"><span class="rot">Piedra · papel · código</span><h2 class="grande">Por eso OOLITA se hizo en tres materiales.</h2>
<p class="parr">El <a href="/ediciones/libro/">libro</a> —cuarenta y ocho páginas, castellano e inglés en la misma doble página— recorre el <a href="/que-es-un-laberinto/">laberinto</a> página a página. Se lee en el tiempo que se tarda en caminarlo despacio.</p>
<p class="parr">El <a href="/mundo-3d/">mundo 3D</a> abre el 3 de enero de 2027: el mismo trazado, la misma costa, la misma luz baja de la tarde, caminable desde el navegador. Sin descarga, sin cuenta, sin coste.</p>
<p class="parr">No es un premio de consolación para quien no puede viajar. Es la forma prevista de recorrerlo. A veces es la distancia, a veces el dinero, a veces el cuerpo —y a veces, sencillamente, es que el lugar está mejor sin nosotros. Caminar el laberinto desde casa no deja ninguna huella sobre una duna de cien mil años.</p>
<p class="parr">Las publicaciones de campo hacen lo mismo con lo demás: geología, viento, sombra, agua, salinas, aves, Posidonia, color y tiempo. Dibujar, escuchar, medir, anotar y fotografiar sin llevarse nada.</p>
<p class="parr">Mirar de cerca no exige estar cerca.</p></section>
<section class="tramo env"><span class="rot">Si vienes</span><h2 class="grande">Ven por el lugar, no por el laberinto.</h2>
<p class="parr">Camina por los senderos señalizados. Los bordes son donde empieza el daño.</p>
<p class="parr">No subas ni pises las dunas fósiles. Míralas desde el camino: desde ahí se ven mejor.</p>
<p class="parr">No muevas piedra. Ni aquí, ni en ninguna parte del parque.</p>
<p class="parr">Hallado, no tomado. No te lleves nada —ni una concha, ni un guijarro, ni una vaina.</p>
<p class="parr">Aprende de la gente que vive y trabaja aquí. Llegaron antes.</p>
<p class="parr">Deja el lugar como lo encontraste.</p></section>
<section class="tramo"><span class="rot">Independencia</span><h2 class="grande">OOLITA es un proyecto independiente.</h2>
<p class="parr">OOLITA es un proyecto independiente de Raquel Costantini con Vestini Tribe.</p>
<p class="parr">No está vinculado, respaldado, autorizado ni promovido por el Parque Natural de Cabo de Gata-Níjar, la Junta de Andalucía ni ninguna otra administración, y no forma parte de ninguna red, programa ni figura de protección oficial. Los datos geológicos y ecológicos citados en esta página proceden de fuentes públicas que se citan como fuente y no como respaldo.</p>
<p class="parr"><a href="/domingos/">22 domingos</a> &nbsp; <a href="/#seguir-oolita">Sigue OOLITA</a></p></section>'''


MAIN_EN = '''<section class="hero"><span class="rot">The labyrinth</span><h1 class="grande">One path. One centre. <em>One return</em>.</h1>
<p class="parr">Un camino. Un centro. Un regreso.</p>
<p class="parr">A three-metre classical labyrinth, laid by hand in 2021 from loose stones, on land beside the fossil dunes. Dry-laid and unfixed: no mortar, nothing cut, nothing excavated. One path only — no forks, no dead ends, no way to get lost. You walk it slowly.</p>
<p class="parr"><small>Classical design · 3 m · loose stones · 2021</small></p></section>
<section class="tramo env"><span class="rot">The origin</span><h2 class="grande">The clearing that was already there.</h2>
<p class="parr">The labyrinth did not open the ground it stands on. It found it open.</p>
<p class="parr">In 2021, in a year when almost nobody was moving, it was laid on a clearing that already existed: bare ground, no vegetation, already walked. Nothing was cleared. No plant was cut. No earth was moved. No new ground was opened. The stones were set dry, loose, without mortar and without fixing — they lift by hand in a morning, and the clearing goes back to being exactly what it was.</p>
<p class="parr">That was the whole design decision: that the thing could be undone without a trace.</p></section>
<section class="tramo"><span class="rot">The place</span><h2 class="grande">It is not a destination.</h2>
<p class="parr">This page used to explain how to get there. It no longer does.</p>
<p class="parr">There are no coordinates, no directions from the car park, no distances from the castle, no pin on a map. The labyrinth is not a secret — it simply does not need visitors, and the place it stands in needs them less.</p>
<p class="parr">Three metres of stone do not justify a journey. What lies underneath is worth knowing about. That is a different thing.</p></section>
<section class="tramo env"><span class="rot">Geodiversity</span><h2 class="grande">What lies underneath is 128,000 years old.</h2>
<p class="parr">The Los Escullos aeolianites are fossil dunes: sand the wind heaped up between 128,000 and 100,000 years ago, which time then cemented into rock. They are made of <a href="/en/what-is-an-ooid/">ooids</a> — spherical grains of calcium carbonate built in concentric layers around a nucleus, one at a time, in shallow warm water. The project takes its name from that grain.</p>
<p class="parr">They are listed in the Andalusian Inventory of Geological Resources. And they are breaking.</p>
<p class="parr">The Junta de Andalucía describes "serious problems" caused by rising visitor numbers on these formations, and has drawn up plans for Los Escullos: 40 × 40 cm masonry walls to hold foot traffic to the paths, together with signage and replanting. Walking off-path on protected fossil dunes is a serious infraction, carrying a fine of 601.02 to 60,101.21 euros.</p>
<p class="parr">A dune that took a hundred thousand years to form fractures under a boot in a second. It cannot be repaired. That is the whole arithmetic.</p></section>
<section class="tramo"><span class="rot">Biodiversity</span><h2 class="grande">A place that already gets too much.</h2>
<p class="parr"><a href="/en/cabo-de-gata/">Cabo de Gata-Níjar</a> protects more than 49,000 hectares, over 12,000 of them marine.</p>
<p class="parr">Below the water: meadows of <em>Posidonia oceanica</em> and <em>Cymodocea nodosa</em>, both Habitats of Community Interest. Nineteen inventoried sea caves, some over forty metres long. More than 150 distinct marine communities — the greatest diversity of the fifteen protected areas studied under the LIFE IP Intemares project. Reefs of <em>Dendropoma lebeche</em>, listed as threatened. The ferruginous limpet, endangered.</p>
<p class="parr">Above it: shag, Audouin's gull, flamingos on the salt pans.</p>
<p class="parr">And on top of all of it, pressure. By August 2026 the park had already passed the whole of 2025's total of complaints about organised activity run without authorisation. A visitor tax is under discussion. Every summer the coves carry more people than they can hold.</p>
<p class="parr">None of those numbers needs one more visitor for a three-metre labyrinth.</p></section>
<section class="tramo env"><span class="rot">The method</span><h2 class="grande">Where these rules come from.</h2>
<p class="parr">Raquel Costantini trained in Environmental Sciences (BSc, United Kingdom), with field work in the conservation of habitats, flora and fauna. That is not biographical decoration: it is where OOLITA's rules come from, and why they have not changed since 2021.</p>
<p class="parr">Do not disturb what is living. Found, not taken. Nothing cut, nothing excavated, nothing fixed. Everything reversible, and reversible by hand. Record rather than collect: draw, measure, note and photograph instead of carrying away.</p>
<p class="parr">Hallazgo — the wider artistic practice — works only with material the landscape has already released: an agave stem fallen of its own accord, a dry seed pod, an empty shell. Attention begins with what a place has already let go.</p>
<p class="parr">The labyrinth follows the same rule. That is why it is made of loose stones on a clearing that was already there.</p></section>
<section class="tramo"><span class="rot">Stone · paper · code</span><h2 class="grande">This is why OOLITA was made in three materials.</h2>
<p class="parr">The <a href="/en/editions/book/">book</a> — forty-eight pages, Spanish and English sharing every spread — walks the <a href="/en/what-is-a-labyrinth/">labyrinth</a> page by page. It reads in the time it takes to walk it slowly.</p>
<p class="parr">The <a href="/en/3d-world/">3D world</a> opens on 3 January 2027: the same design, the same coast, the same low afternoon light, walkable in the browser. No download, no account, no cost.</p>
<p class="parr">It is not a consolation prize for people who cannot travel. It is the intended way to walk it. Sometimes it is the distance, sometimes the money, sometimes the body — and sometimes it is simply that the place does better without us. Walking the labyrinth from home leaves no mark on a hundred-thousand-year-old dune.</p>
<p class="parr">The field publications do the same for everything else: geology, wind, shade, water, salt pans, birds, Posidonia, colour and time. Draw, listen, measure, note and photograph — and take nothing.</p>
<p class="parr">Looking closely does not require being close.</p></section>
<section class="tramo env"><span class="rot">If you come</span><h2 class="grande">Come for the place, not for the labyrinth.</h2>
<p class="parr">Keep to the marked paths. The edges are where the damage starts.</p>
<p class="parr">Do not climb or stand on the fossil dunes. Look at them from the path — they read better from there.</p>
<p class="parr">Move no stone. Not here, not anywhere in the park.</p>
<p class="parr">Found, not taken. Take nothing away — not a shell, not a pebble, not a seed pod.</p>
<p class="parr">Learn from the people who live and work here. They were here first.</p>
<p class="parr">Leave the place as you found it.</p></section>
<section class="tramo"><span class="rot">Independence</span><h2 class="grande">OOLITA is an independent project.</h2>
<p class="parr">OOLITA is an independent project by Raquel Costantini with Vestini Tribe.</p>
<p class="parr">It is not connected to, endorsed by, authorised by or promoted by the Cabo de Gata-Níjar Natural Park, the Junta de Andalucía or any other administration, and it forms no part of any official network, programme or designation. The geological and ecological facts cited on this page come from public sources, cited as sources and not as endorsement.</p>
<p class="parr"><a href="/en/sundays/">22 Sundays</a> &nbsp; <a href="/en/#follow-oolita">Follow OOLITA</a></p></section>'''


TITLE_ES = "El laberinto de Los Escullos · OOLITA"
TITLE_EN = "The Los Escullos labyrinth · OOLITA"
DESC_ES = ("Un laberinto de piedra de tres metros sobre un claro que ya existía, en Cabo de Gata. "
           "No es un destino: la misma senda se camina en papel y en 3D, sin viaje y sin huella.")
DESC_EN = ("A three-metre stone labyrinth laid on a clearing that was already there, in Cabo de Gata. "
           "Not a destination: the same path opens on paper and in 3D, with no journey and no trace.")


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

    # 4 — anything left: neutralise rather than leave a decimal on the page.
    text = text.replace("36°47′58″ N · 2°03′47″ W", "Los Escullos · Níjar")
    text = text.replace("36.799342, −2.063165", "Los Escullos · Níjar")
    text = text.replace("36.7993, −2.0632", "Los Escullos · Níjar")

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
         "Tres metros. Un camino. Colocado a mano en 2021 sobre un claro que ya estaba. Sin cartel, "
         "y sin invitación.",
         "homepage stone card"),
        ("Cómo llegar y qué esperar →", "Qué es, y por qué no lo señalizamos →",
         "homepage labyrinth CTA"),
        ("El laberinto caminable · Cabo de Gata-Níjar",
         "El laberinto, y el suelo de 128.000 años que hay debajo",
         "homepage index entry 01"),
    ),
    "en/index.html": (
        ("The stone labyrinth is already at Los Escullos; there is no ticket or booking.",
         "The stone labyrinth is at Los Escullos. We do not sign it or promote it as a destination: "
         "the same path is walked in the book and, from 3 January, in the 3D world.",
         "homepage access wording"),
        ("The labyrinth is already there. Three metres. One path. No ticket, no sign, no booking.",
         "Three metres. One path. Laid by hand in 2021 on a clearing that was already there. "
         "No sign, and no invitation.",
         "homepage stone card"),
        ("How to get there and what to expect →", "What it is, and why we don't sign it →",
         "homepage labyrinth CTA"),
        ("The walkable labyrinth · Cabo de Gata-Níjar",
         "The labyrinth, and the 128,000-year-old ground beneath it",
         "homepage index entry 01"),
    ),
}

for rel, rules in HOME_RULES.items():
    path, text = read(rel)
    for old, new, label in rules:
        text = replace_once(text, old, new, page=rel, label=label)
    write(path, text)
    print(f"Homepage invitation wording retired: {rel}")


# Homepage meta descriptions.
for rel, old_desc, new_desc in (
    ("index.html",
     "Laberinto caminable de piedra en Los Escullos, Cabo de Gata: gratis y sin reserva.",
     "OOLITA: un laberinto de piedra en Cabo de Gata, colocado sobre un claro que ya existía. "
     "No es un destino."),
    # The live English meta carries no invitation ("…and grows into a fable, field
    # publications, textile editions and a 3D world"), so it is left alone. Only the
    # Spanish one advertises "gratis y sin reserva".
):
    path, text = read(rel)
    text = replace_optional(text, old_desc, new_desc)
    write(path, text)


# --------------------------------------------------------------------------
# 3 — /cabo-de-gata/: the clearing, and no exact position
# --------------------------------------------------------------------------
for rel, old, new, label in (
    ("cabo-de-gata/index.html",
     "Fue colocado a mano en 2021 con piedras sueltas, sin cortar, fijar ni excavar.",
     "Fue colocado a mano en 2021 sobre un claro que ya existía, con piedras sueltas, sin "
     "desbrozar, cortar, fijar ni excavar. No publicamos su posición exacta: el lugar no "
     "necesita más pisadas.",
     "cabo labyrinth sentence"),
    ("en/cabo-de-gata/index.html",
     "It was laid by hand in 2021 with loose stones: nothing cut, fixed or excavated.",
     "It was laid by hand in 2021 on a clearing that already existed, with loose stones: nothing "
     "cleared, cut, fixed or excavated. We do not publish its exact position: the place does not "
     "need more footfall.",
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
for rel, old, new, label in (
    ("sobre-oolita/index.html",
     "Raquel Costantini es facilitadora de laberintos formada por Veriditas",
     "Raquel Costantini tiene formación en Ciencias Ambientales (BSc, Reino Unido) y trabajo de "
     "campo en conservación de hábitats, flora y fauna. Esa formación es la que fija el método: "
     "no alterar lo vivo, hallado no tomado, nada cortado ni excavado ni fijado, todo reversible. "
     "El laberinto se colocó en 2021 sobre un claro que ya existía. OOLITA es un proyecto "
     "independiente: no está vinculado, respaldado ni promovido por el Parque Natural, la Junta "
     "de Andalucía ni ninguna otra administración. Es además facilitadora de laberintos formada "
     "por Veriditas",
     "about practitioner grounding"),
    ("en/about/index.html",
     "Raquel Costantini is a Veriditas Trained Labyrinth Facilitator",
     "Raquel Costantini trained in Environmental Sciences (BSc, United Kingdom), with field work "
     "in the conservation of habitats, flora and fauna. That training is what sets the method: do "
     "not disturb what is living, found not taken, nothing cut or excavated or fixed, everything "
     "reversible. The labyrinth was laid in 2021 on a clearing that already existed. OOLITA is an "
     "independent project: it is not connected to, endorsed by or promoted by the Natural Park, "
     "the Junta de Andalucía or any other administration. She is also a Veriditas Trained "
     "Labyrinth Facilitator",
     "about practitioner grounding"),
):
    path, text = read(rel)
    text = replace_once(text, old, new, page=rel, label=label)
    write(path, text)


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
)

leaks: list[str] = []
for page in sorted(ROOT.rglob("*.html")):
    rel = page.relative_to(ROOT).as_posix()
    text = page.read_text(encoding="utf-8")
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
