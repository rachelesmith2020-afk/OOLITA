#!/usr/bin/env python3
"""Validate the final Cabo de Gata direction after editorial transforms.

The live-origin reconstruction now already contains the approved direction layer,
and the final Spanish editorial pass runs during reconstruction. This gate must
therefore validate that final reader-facing state rather than rewrite it back to
older copy. It fails closed if required direction language disappears or if any
retired unsupported claim returns.
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

print("OOLITA Cabo de Gata direction v3 validated against final editorial state.")
