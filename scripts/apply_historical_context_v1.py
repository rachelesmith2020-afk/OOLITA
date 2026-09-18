#!/usr/bin/env python3
"""Approved bilingual historical-context wording; preserves URLs and styling.

Run last, after earlier editorial passes. --restore provides their original
input when reconstructing from a previously published copy of this pass.
"""
from pathlib import Path
import sys
import re

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else 'site')
RESTORE = '--restore' in sys.argv
RULES = [
('OOLITA comienza con un laberinto clásico de tres metros, colocado a mano con piedras sueltas en Los Escullos, en terreno junto a las dunas fósiles. No lleva cartel ni nombre.', 'OOLITA nació de un laberinto clásico de tres metros, colocado a mano con piedras sueltas en Los Escullos en 2021, en terreno junto a las dunas fósiles.'),
('OOLITA begins with a three-metre classical labyrinth, laid by hand from stone at Los Escullos, on land beside the fossil dunes.', 'OOLITA grew from a three-metre classical labyrinth, laid by hand from stone at Los Escullos in 2021, on land beside the fossil dunes.'),
('Junto al mar, en Los Escullos, hay un laberinto de piedra de tres metros.', 'El laberinto de piedra de tres metros creado en Los Escullos en 2021 dio origen a OOLITA.'),
('Beside the sea at Los Escullos lies a three-metre stone labyrinth.', 'The three-metre stone labyrinth created at Los Escullos in 2021 was the beginning of OOLITA.'),
('El laberinto de piedra está en Los Escullos. No lo señalizamos ni lo promocionamos como destino: la misma senda se camina en el libro y, desde el 3 de enero, en el mundo 3D.', 'El laberinto es donde empezó OOLITA. No lo señalizamos ni lo promocionamos como destino. La misma senda continúa en el libro y, desde el 3 de enero, en el mundo 3D.'),
('The stone labyrinth is at Los Escullos. We do not sign it or promote it as a destination: the same path is walked in the book and, from 3 January, in the 3D world.', 'The labyrinth is where OOLITA began. We don’t signpost it or promote it as a destination. The same path continues in the book and, from 3 January, in the 3D world.'),
('AHORA · laberinto en Los Escullos · 22 domingos.', 'AHORA · 22 domingos.'),
('NOW · labyrinth at Los Escullos · 22 Sundays.', 'NOW · 22 Sundays.'),
('El laberinto caminable está en Los Escullos, dentro del ', 'El laberinto original se creó en 2021 en Los Escullos, dentro del '),
('The walkable labyrinth is at Los Escullos, inside the ', 'The original labyrinth was created in 2021 at Los Escullos, inside the '),
('Está colocado en seco y sin fijar:', 'Se colocó en seco y sin fijar:'),
('Está en terreno junto a las dunas fósiles. Se camina despacio.', 'Tres metros de trazado clásico en terreno junto a las dunas fósiles.'),
('It stands on land beside the fossil dunes. You walk it slowly.', 'Three metres of classical design on land beside the fossil dunes.'),
('El laberinto es el original y el más pequeño de los tres.', 'El laberinto de 2021 fue el punto de partida y el más pequeño de los tres.'),
('The labyrinth at Los Escullos is the original, and the smallest of the three.', 'The 2021 labyrinth at Los Escullos was the starting point, and the smallest of the three.'),
('Nada lo señala sobre el terreno: quien pasa por allí lo encuentra o no lo encuentra. ', ''),
('Nothing marks it on the ground: you either notice it or walk past. ', ''),
('OOLITA seguirá teniendo un solo laberinto: el de Los Escullos.', 'OOLITA tiene un solo laberinto y no hará otro.'),
('OOLITA will continue to have one labyrinth: the one at Los Escullos.', 'OOLITA has one labyrinth and will not make another.'),
('El laberinto está allí. El camino también puede seguirse desde lejos.', 'La historia del laberinto continúa en papel y en código.'),
('The labyrinth is there. The path can also be followed from a distance.', 'The story of the labyrinth continues on paper and in code.'),
('Qué es, y por qué no lo señalizamos', 'Historia del laberinto original'),
("What it is, and why we don't sign it", 'History of the original labyrinth'),
('Qué es el laberinto, y por qué no lo señalizamos', 'La historia del laberinto'),
("What the labyrinth is, and why we don't sign it", 'The history of the labyrinth'),
('qué es, y por qué no lo señalizamos', 'la historia del laberinto original'),
("what it is, and why we don't sign it", 'the history of the original labyrinth'),
('laberinto de piedra que se puede caminar en Los Escullos', 'laberinto de piedra creado en Los Escullos en 2021'),
('the stone labyrinth you can walk at Los Escullos', 'the stone labyrinth created at Los Escullos in 2021'),
('Caminar el laberinto →', 'Historia del laberinto →'),
('Walk the labyrinth →', 'History of the labyrinth →'),
('Seiscientos veinte metros de costa.', 'Un estudio de la costa para el mundo digital.'),
('Six hundred and twenty metres of coast.', 'A study of the coast for the digital world.'),
('La orilla, el castillo y el laberinto, casi en línea recta, de norte a sur.', 'Un collage de paisaje y memoria para desarrollar el mundo digital de OOLITA.'),
('The shore, the castle and the labyrinth, almost in a straight line, north to south.', 'A collage of landscape and memory for developing OOLITA’s digital world.'),
('Todo el mundo cabe en un paseo.', 'Un paisaje que toma forma en papel y en código.'),
('The whole world fits into one walk.', 'A landscape taking shape on paper and in code.'),
('Para información actual sobre la visita, consulta', 'Para conocer el contexto del proyecto, consulta'),
('For current visitor information, see', 'For the context of the project, see'),
('El laberinto ocupa tres metros en terreno junto a las dunas fósiles.', 'La obra de 2021 ocupaba tres metros en terreno junto a las dunas fósiles.'),
('The labyrinth occupies three metres on land beside the fossil dunes.', 'The 2021 work occupied three metres on land beside the fossil dunes.'),
('El laberinto se queda en Los Escullos.', 'OOLITA tiene un solo laberinto y no hará otro.'),
('The labyrinth stays at Los Escullos.', 'OOLITA has one labyrinth and will not make another.'),
('Lo que se queda aquí.', 'La memoria del lugar.'),
('What stays here.', 'The memory of the place.'),
('Solo habrá un laberinto OOLITA: el de Los Escullos.', 'El laberinto colocado en 2021 es el origen de OOLITA.'),
('There will only be one OOLITA labyrinth: the one at Los Escullos.', 'The 2021 labyrinth at Los Escullos is OOLITA’s documented starting point.'),
(' está dentro del Parque Natural Cabo de Gata-Níjar, en terreno junto a las dunas fósiles frente al Mediterráneo.', ' se creó en 2021 dentro del Parque Natural Cabo de Gata-Níjar, en terreno junto a las dunas fósiles frente al Mediterráneo.'),
('The labyrinth at Los Escullos is inside Cabo de Gata-Níjar Natural Park, on land beside the fossil dunes facing the Mediterranean.', 'The labyrinth at Los Escullos was created in 2021 inside Cabo de Gata-Níjar Natural Park, on land beside the fossil dunes facing the Mediterranean.'),
('Son parte de cómo nació la obra y de por qué sigue allí.', 'Son parte de cómo nació la obra.'),
('They are part of how the work began and why it remains there.', 'They are part of how the work began and how it is documented.'),
('OOLITA — laberinto caminable en Los Escullos, Cabo de Gata', 'OOLITA — arte, libro y mundo digital en Cabo de Gata'),
('Un laberinto de piedra caminable en Los Escullos (Cabo de Gata, Almería), una fábula ilustrada y un mundo 3D que abre el 3 de enero de 2027.', 'La historia del laberinto de OOLITA de 2021, una fábula ilustrada y un mundo 3D que abre el 3 de enero de 2027.'),
('OOLITA — a walkable stone labyrinth in Cabo de Gata, Spain', 'OOLITA — art, book and digital world in Cabo de Gata'),
('Laberinto clásico caminable de tres metros', 'Registro del laberinto clásico de tres metros creado en 2021'),
('A walkable three-metre classical labyrinth of loose stones', 'A record of the three-metre classical stone labyrinth created in 2021'),
('laberinto caminable, land art', 'archivo del laberinto, land art'),
('Oolita is a three-metre classical labyrinth, laid by hand from loose stones in 2021. The ground around it is fragile: keep to the paths and leave the stones where they are.', 'Oolita began with a three-metre classical labyrinth, laid by hand from loose stones in 2021. This archive records the original work; it does not offer access to the installation.'),
('Oolita es un laberinto clásico de tres metros, trazado a mano con piedras sueltas en 2021. El entorno es frágil: permanece en los senderos y deja las piedras donde están.', 'Oolita nació de un laberinto clásico de tres metros, trazado a mano con piedras sueltas en 2021. El entorno es frágil: permanece en los senderos y deja las piedras donde están.'),
]

NOTICE_ES = '<p class="parr" data-oolita-archive-context>OOLITA no señaliza el laberinto ni organiza visitas. La misma senda se camina en el libro y en el mundo 3D.</p>'
NOTICE_EN = '<p class="parr" data-oolita-archive-context>OOLITA does not signpost the labyrinth or arrange visits. The same walk continues in the book and in the 3D world.</p>'
changed = 0
for path in sorted(ROOT.rglob('*.html')):
    text = original = path.read_text(encoding='utf-8')
    if RESTORE:
        for notice in (NOTICE_ES, NOTICE_EN):
            text = text.replace(notice, '')
        for old, new in reversed(RULES):
            text = text.replace(new, old)
    else:
        for old, new in RULES:
            text = text.replace(old, new)
        rel = path.relative_to(ROOT).as_posix()
        if rel in ('laberinto/index.html', 'en/labyrinth/index.html') and 'data-oolita-archive-context' not in text:
            notice = NOTICE_EN if rel.startswith('en/') else NOTICE_ES
            text, count = re.subn(r'(<section class="hero">[\s\S]*?)(</section>)', lambda m: m[1]+notice+m[2], text, count=1)
            if count != 1:
                raise SystemExit(f'Missing hero in {rel}')
        # These are retired invitations and directions, including metadata.
        for needle in ('you can walk at Los Escullos', 'que se puede caminar en Los Escullos', 'Walk the labyrinth →', 'Caminar el laberinto →', 'Six hundred and twenty metres', 'Seiscientos veinte metros', 'almost in a straight line, north to south', 'casi en línea recta, de norte a sur', 'The labyrinth stays at Los Escullos', 'El laberinto se queda en Los Escullos'):
            if needle in text:
                raise SystemExit(f'Retired wording remains in {rel}: {needle}')
    if text != original:
        path.write_text(text, encoding='utf-8')
        changed += 1
print(f'Historical context: {changed} pages updated; restore={RESTORE}')
