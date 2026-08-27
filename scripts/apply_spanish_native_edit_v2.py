#!/usr/bin/env python3
"""Final Spanish editorial pass for the public OOLITA site.

The pass is intentionally conservative: it changes only reviewed Spanish
reader-facing copy, never English, poster artwork copy, or published Sunday
entry bodies. Publication-critical wording is strict; a few optional micro-edits
on long concept pages are allowed to defer when inline markup has changed.
"""
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")


def replace_state(rel: str, old: str, new: str, label: str, *, required: bool = True) -> bool:
    path = ROOT / rel
    if not path.is_file():
        raise SystemExit(f"Missing Spanish editorial page: {rel}")
    text = path.read_text(encoding="utf-8")
    if new in text:
        return False
    if old in text:
        path.write_text(text.replace(old, new, 1), encoding="utf-8")
        return True
    if required:
        raise SystemExit(f"Unexpected Spanish copy state in {rel} ({label})")
    print(f"Optional Spanish micro-edit deferred because source/markup differs: {rel} ({label})")
    return False


required_rules = (
    ("index.html",
     "Un solo camino. Ninguna decisión y ninguna forma de perderse. OOLITA lleva ese camino a través de la piedra, el papel y el código.",
     "Un solo camino. Sin decisiones. Sin forma de perderse. OOLITA recorre ese mismo camino en piedra, papel y código.",
     "homepage path sentence"),
    ("index.html",
     "El laberinto de piedra ya está en Los Escullos; no tiene entrada ni reserva.",
     "El laberinto de piedra ya está en Los Escullos; es gratuito y no requiere reserva.",
     "homepage access wording"),
    ("index.html",
     "El laberinto ya está allí. Tres metros. Un camino. Sin entrada, sin cartel, sin reserva.",
     "El laberinto ya está allí. Tres metros. Un camino. Gratis. Sin cartel. Sin reserva.",
     "homepage stone card"),
    ("index.html",
     "Está colocado en seco y sin fijar — no hay mortero; no se ha cortado ni excavado nada.",
     "Está colocado en seco y sin fijar: no hay mortero y no se ha cortado ni excavado nada.",
     "homepage construction sentence"),
    ("laberinto/index.html",
     "Está colocado en seco y sin fijar — no hay mortero; no se ha cortado ni excavado nada.",
     "Está colocado en seco y sin fijar: no hay mortero y no se ha cortado ni excavado nada.",
     "labyrinth construction sentence"),
    ("laberinto/index.html",
     "No tiene personal ni entrada; recorrerlo es gratuito y conviene acercarse con cuidado y respeto por el lugar.",
     "No hay personal y no hace falta reservar; recorrerlo es gratuito y conviene acercarse con cuidado y respeto por el lugar.",
     "labyrinth access introduction"),
    ("laberinto/index.html",
     "Sin personal · sin entrada ni reserva",
     "Libre · sin personal ni reserva",
     "labyrinth access facts"),
    ("laberinto/index.html",
     "No hay entrada ni reserva. Es un lugar sin personal; si lo visitas, acércate con cuidado y respeto por el entorno.",
     "Es gratuito y no requiere reserva. No hay personal; si lo visitas, acércate con cuidado y respeto por el entorno.",
     "labyrinth FAQ access answer"),
    ("que-es-un-oolito/index.html",
     "No es un fragmento roto de otra cosa: se forma creciendo, capa sobre capa, alrededor de un núcleo diminuto.",
     "No es un fragmento roto de otra cosa: se forma por crecimiento, capa a capa, alrededor de un núcleo diminuto.",
     "ooid growth sentence"),
    ("que-es-un-oolito/index.html",
     "Cuando la duna que se endurece fue una duna de viento y no un depósito submarino, el nombre técnico es ",
     "Cuando la duna endurecida se formó por acción del viento y no como depósito submarino, el término técnico es ",
     "aeolianite definition"),
    ("sobre-oolita/index.html",
     "El libro creció de caminarlo y volver a dibujarlo.",
     "El libro nació de recorrerlo y volver a dibujarlo.",
     "About book origin"),
    ("sobre-oolita/index.html",
     "Esa forma — capas, centro, tiempo — conecta",
     "Esa forma —capas, centro, tiempo— conecta",
     "Spanish dash typography"),
    ("colaborar/index.html",
     "qué tipo de publicación te interesaría tener.",
     "qué tipo de publicación te interesa.",
     "collaboration enquiry wording"),
    ("mundo-3d/index.html",
     "en terreno junto a las dunas fósiles junto al Mediterráneo.",
     "en terreno junto a las dunas fósiles, frente al Mediterráneo.",
     "3D repeated junto"),
    ("ediciones/libro/index.html",
     "Sin almacenes y sin tiradas que sobran:",
     "Sin almacenes ni tiradas sobrantes:",
     "book POD sentence"),
    ("ediciones/libro/index.html",
     "Qué tarda en llegar.",
     "Cuánto tarda en llegar.",
     "book delivery heading"),
    ("ediciones/libro/index.html",
     "Al imprimirse de uno en uno, no hay stock que agotar ni reediciones que esperar.",
     "Como cada ejemplar se imprime por encargo, no hay stock que agotar ni reediciones que esperar.",
     "book POD delivery sentence"),
    ("ediciones/libro/index.html",
     "En la entrada, hoy el mundo sonaba fuerte. Una sensación erizada, un peso denso. Junto a la entrada del camino, una chumbera se alzaba al sol, toda púas y palas planas de un gris verdoso, con flores ardiendo naranja en los bordes, impasible. El gato no se sentía impasible.",
     "A la entrada, aquel día el mundo sonaba fuerte. Una sensación de púas, un peso denso. Junto a la entrada del camino, una chumbera se alzaba al sol, toda púas y palas planas de un gris verdoso, con flores de un naranja encendido en los bordes. Impasible. El gato no lo estaba.",
     "book excerpt sync with final interior"),
    ("ediciones/camiseta/index.html",
     "Blanca, de algodón orgánico de 200 gramos y corte oversized unisex.",
     "Blanca, de algodón orgánico de 200 g/m² y corte oversized unisex.",
     "T-shirt lead fabric weight"),
    ("ediciones/camiseta/index.html",
     "Esta primera pieza es una camiseta de algodón orgánico de 200 gramos y corte holgado.",
     "Esta primera pieza es una camiseta de algodón orgánico de 200 g/m² y corte holgado.",
     "T-shirt body fabric weight"),
    ("ediciones/camiseta/index.html",
     "no puede llegar de una fábrica opaca.",
     "no puede venir de una fábrica opaca.",
     "T-shirt sourcing idiom"),
)

optional_rules = (
    ("domingos/index.html",
     "y ese lugar se dice en la propia página del domingo.",
     "y ese lugar se indica en la propia página de cada domingo.",
     "Sunday archive route wording"),
    ("que-es-un-laberinto/index.html",
     "es lo contrario: multicursal, hecho de encrucijadas y caminos falsos, diseñado expresamente para desorientar.",
     "es lo contrario: un trazado de encrucijadas y caminos falsos, diseñado expresamente para desorientar.",
     "maze definition redundancy"),
    ("que-es-un-laberinto/index.html",
     "De la Edad Media es el otro gran tipo, el de once circuitos en cuatro cuadrantes que se encuentra en el suelo de varias catedrales góticas",
     "El otro gran tipo procede de la Edad Media: el de once circuitos en cuatro cuadrantes que se encuentra en el suelo de varias catedrales góticas",
     "medieval labyrinth sentence"),
    ("que-es-un-laberinto/index.html",
     "uno de catedral, de once o doce metros, lleva más tiempo.",
     "un laberinto catedralicio, de once o doce metros, lleva más tiempo.",
     "cathedral labyrinth wording"),
)

changed = 0
for rel, old, new, label in required_rules:
    changed += int(replace_state(rel, old, new, label, required=True))
for rel, old, new, label in optional_rules:
    changed += int(replace_state(rel, old, new, label, required=False))

# Publication invariant: the website excerpt must match the corrected Spanish
# interior rather than an earlier translation state.
book_page = (ROOT / "ediciones/libro/index.html").read_text(encoding="utf-8")
final_excerpt = (
    "A la entrada, aquel día el mundo sonaba fuerte. Una sensación de púas, un peso denso. "
    "Junto a la entrada del camino, una chumbera se alzaba al sol, toda púas y palas planas de un gris verdoso, "
    "con flores de un naranja encendido en los bordes. Impasible. El gato no lo estaba."
)
if book_page.count(final_excerpt) != 1:
    raise SystemExit("Final Spanish book excerpt missing or duplicated on ediciones/libro")

# Voice anchors that this pass must never normalise away.
protected = {
    "sobre-oolita/index.html": ("Primero fue un laberinto.", "El lugar no es un fondo."),
    "index.html": ("Piedra. Papel. Código.",),
}
for rel, anchors in protected.items():
    text = (ROOT / rel).read_text(encoding="utf-8")
    for anchor in anchors:
        if anchor not in text:
            raise SystemExit(f"Protected OOLITA voice anchor missing in {rel}: {anchor}")

print(f"OOLITA final Spanish editorial pass complete: {changed} edit(s) applied; protected voice anchors intact.")
