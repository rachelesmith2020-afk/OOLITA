#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")

REPLACEMENTS = {
    "index.html": [
        (
            "OOLITA — Piedra, papel y código en Cabo de Gata",
            "OOLITA — Laberinto de Los Escullos · Cabo de Gata",
        ),
        (
            "OOLITA empieza con un laberinto de piedra en Los Escullos, Cabo de Gata, y crece en una fábula, publicaciones de campo, ediciones textiles y un mundo 3D.",
            "Laberinto caminable de piedra en Los Escullos, Cabo de Gata: gratis y sin reserva. OOLITA continúa en un libro bilingüe, publicaciones de campo y un mundo 3D.",
        ),
    ],
    "domingos/index.html": [
        (
            "22 domingos — el camino hacia la apertura de OOLITA",
            "22 domingos de OOLITA — archivo hasta enero 2027",
        ),
        (
            "Una imagen cada domingo, del 9 de agosto de 2026 al 3 de enero de 2027: la serie que acompaña la apertura del laberinto OOLITA de Los Escullos.",
            "Una imagen cada domingo hasta el 3 de enero de 2027. Archivo bilingüe del camino de OOLITA desde Los Escullos hasta la apertura del mundo 3D.",
        ),
        ('<img src="/domingos/img/01-180.jpg" alt=""', '<img src="/domingos/img/01-180.jpg" alt="Domingo 01 · El doble — imagen de la serie OOLITA"'),
        ('<img src="/domingos/img/02-180.jpg" alt=""', '<img src="/domingos/img/02-180.jpg" alt="Domingo 02 · El gato, de verdad — imagen de la serie OOLITA"'),
        ('<img src="/domingos/img/03-180.jpg" alt=""', '<img src="/domingos/img/03-180.jpg" alt="Domingo 03 · La memoria del mar — imagen de la serie OOLITA"'),
    ],
    "en/sundays/index.html": [
        ('<img src="/domingos/img/01-180.jpg" alt=""', '<img src="/domingos/img/01-180.jpg" alt="Sunday 01 · The Double — OOLITA series image"'),
        ('<img src="/domingos/img/02-180.jpg" alt=""', '<img src="/domingos/img/02-180.jpg" alt="Sunday 02 · The Cat, for Real — OOLITA series image"'),
        ('<img src="/domingos/img/03-180.jpg" alt=""', '<img src="/domingos/img/03-180.jpg" alt="Sunday 03 · The Memory of the Sea — OOLITA series image"'),
    ],
    "carteles/index.html": [
        (
            "Los nueve carteles — la apertura de OOLITA",
            "Carteles OOLITA — piedra, papel y código · Cabo de Gata",
        ),
        (
            "Los nueve carteles tipográficos que abren OOLITA: piedra, papel y código — el laberinto de Los Escullos, el libro y el mundo 3D que abre el 3 de enero de 2027.",
            "Nueve carteles de OOLITA: la serie visual que presentó el laberinto de Los Escullos, el libro bilingüe y el mundo 3D en Cabo de Gata.",
        ),
    ],
    "laberinto/index.html": [
        (
            "Laberinto OOLITA en Los Escullos, Cabo de Gata: un camino de piedras sueltas en terreno junto a las dunas fósiles, sin entrada ni reserva.",
            "Visita el laberinto de piedra de tres metros en Los Escullos, Cabo de Gata. Gratis, sin reserva, junto al Castillo de San Felipe. Coordenadas y acceso.",
        ),
    ],
    "en/labyrinth/index.html": [
        (
            "A 3-metre classical stone labyrinth, laid by hand in 2021 on land beside the fossil dunes at Los Escullos, Cabo de Gata. How to find it and what to expect.",
            "Visit the three-metre stone labyrinth at Los Escullos, Cabo de Gata. Free, no booking, beside Castillo de San Felipe. Coordinates and access.",
        ),
    ],
}

changed = 0
for rel, pairs in REPLACEMENTS.items():
    path = ROOT / rel
    if not path.is_file():
        raise SystemExit(f"Missing expected page: {rel}")
    text = path.read_text(encoding="utf-8")
    original = text
    for old, new in pairs:
        if old not in text:
            raise SystemExit(f"Expected source text not found in {rel}: {old[:90]}")
        text = text.replace(old, new)
    if text != original:
        path.write_text(text, encoding="utf-8")
        changed += 1

# Safety gates: preserve canonical behavior and ensure archive images carry useful text alternatives.
for rel in ("index.html", "domingos/index.html", "en/sundays/index.html", "carteles/index.html", "laberinto/index.html", "en/labyrinth/index.html"):
    text = (ROOT / rel).read_text(encoding="utf-8")
    if '<link rel="canonical"' not in text:
        raise SystemExit(f"Canonical missing after edit: {rel}")

for rel in ("domingos/index.html", "en/sundays/index.html"):
    text = (ROOT / rel).read_text(encoding="utf-8")
    for n in ("01", "02", "03"):
        if f'/domingos/img/{n}-180.jpg" alt=""' in text:
            raise SystemExit(f"Empty Sunday thumbnail alt remains in {rel}: {n}")

print(f"Search snippet + Sunday alt repair applied to {changed} page(s)")
