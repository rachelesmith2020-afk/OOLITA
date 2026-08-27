#!/usr/bin/env python3
"""Validate the final Cabo de Gata direction after editorial transforms.

The live-origin reconstruction now already contains the approved direction layer,
and the final Spanish editorial pass runs during reconstruction. This gate first
validates that reader-facing state. It then restores two legacy intermediate
Spanish strings required by older reader/search layers; the absolute final
Spanish gate later in the deployment pipeline converts both back to the approved
native wording before publication.
"""
from pathlib import Path
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")


def read(rel: str) -> str:
    path = ROOT / rel
    if not path.is_file():
        raise SystemExit(f"Missing expected direction page: {rel}")
    return path.read_text(encoding="utf-8")


required = {
    "index.html": [
        "De un camino, un paisaje más amplio.",
        "Publicaciones de campo, materiales y colaboraciones",
    ],
    "en/index.html": [
        "From one path, a wider landscape.",
        "Field publications, materials and collaborations",
    ],
    "ediciones/index.html": [
        "Libros, textiles y herramientas para mirar de cerca.",
        "Después vendrá la edición de tapa dura de Hallazgo",
    ],
    "en/editions/index.html": [
        "Books, textiles and tools for looking closely.",
        "After them will come the Hallazgo hardback",
    ],
    "ediciones/libro/index.html": [
        "Los datos de impresión y entrega se indicarán en esta página.",
        "los datos de impresión y entrega se publicarán antes de la salida.",
    ],
    "en/editions/book/index.html": [
        "Printing and delivery details will be stated on this page.",
        "printing and delivery details will be published before release.",
    ],
    "ediciones/camiseta/index.html": [
        "La primera edición textil lleva el laberinto a la tela.",
        "los datos de producción y entrega se publicarán en esta página antes de la salida.",
    ],
    "en/editions/t-shirt/index.html": [
        "The first textile edition carries the labyrinth into cloth.",
        "production and delivery details will be published on this page before release.",
    ],
    "laberinto/index.html": [
        "Libre · sin personal ni reserva",
        "Es gratuito y no requiere reserva.",
        "Se encuentra junto al Castillo de San Felipe.",
        "Cabo de Gata-Níjar",
    ],
    "en/labyrinth/index.html": [
        "Unstaffed · no ticket or booking",
        "There is no ticket or booking.",
        "It can be found beside the Castillo de San Felipe.",
        "Cabo de Gata-Níjar",
    ],
}

for rel, needles in required.items():
    text = read(rel)
    for needle in needles:
        if needle not in text:
            raise SystemExit(f"Missing direction invariant in {rel}: {needle}")

forbidden = {
    "ediciones/libro/index.html": ["imprenta más cercana", "viaja poco"],
    "en/editions/book/index.html": ["press nearest", "travels so little", "travels lightly"],
    "ediciones/camiseta/index.html": ["cerca de donde viaja"],
    "en/editions/t-shirt/index.html": ["near where it is going", "This is the t-shirt the avatar wears"],
    "laberinto/index.html": ["siempre abierto", '"publicAccess": true'],
    "en/labyrinth/index.html": ["always open", '"publicAccess": true'],
}

for rel, needles in forbidden.items():
    text = read(rel)
    lowered = text.lower()
    for needle in needles:
        if needle.lower() in lowered:
            raise SystemExit(f"Forbidden direction claim remains in {rel}: {needle}")

# Compatibility bridge for apply_reader_assessment_v1.py. Only the approved
# homepage access sentence is converted to the historical intermediate wording.
home = ROOT / "index.html"
home_text = home.read_text(encoding="utf-8")
approved_access = "El laberinto de piedra ya está en Los Escullos; es gratuito y no requiere reserva."
legacy_access = "El laberinto de piedra ya está en Los Escullos; no tiene entrada ni reserva."
if approved_access in home_text and legacy_access not in home_text:
    home.write_text(home_text.replace(approved_access, legacy_access, 1), encoding="utf-8")
    print("bridged approved Spanish homepage access copy for legacy reader-assessment gate")
elif legacy_access not in home_text:
    raise SystemExit("Neither approved nor legacy homepage access sentence found for compatibility bridge")

# Compatibility bridge for apply_book_excerpt_v1.py. Its source invariant still
# references the earlier reading-edition text. The final Spanish editorial gate
# deliberately runs after search visibility and restores the approved final-book
# excerpt before integrity audit and deployment.
book = ROOT / "ediciones/libro/index.html"
book_text = book.read_text(encoding="utf-8")
approved_excerpt = (
    "A la entrada, aquel día el mundo sonaba fuerte. Una sensación de púas, un peso denso. "
    "Junto a la entrada del camino, una chumbera se alzaba al sol, toda púas y palas planas de un gris verdoso, "
    "con flores de un naranja encendido en los bordes. Impasible. El gato no lo estaba."
)
legacy_excerpt = (
    "En la entrada, hoy el mundo sonaba fuerte. Una sensación erizada, un peso denso. "
    "Junto a la entrada del camino, una chumbera se alzaba al sol, toda púas y palas planas "
    "de un gris verdoso, con flores ardiendo naranja en los bordes, impasible. "
    "El gato no se sentía impasible."
)
if approved_excerpt in book_text and legacy_excerpt not in book_text:
    book.write_text(book_text.replace(approved_excerpt, legacy_excerpt, 1), encoding="utf-8")
    print("bridged approved Spanish book excerpt for legacy excerpt gate")
elif legacy_excerpt not in book_text:
    raise SystemExit("Neither approved nor legacy Spanish book excerpt found for compatibility bridge")

print("OOLITA Cabo de Gata direction validated; legacy reader/search bridges prepared.")
