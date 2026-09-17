#!/usr/bin/env python3
"""Held passage: the labyrinth has been removed.

NOT wired into any workflow. It publishes nothing until a step is added to
deploy-cloudflare-pages.yml after apply_parque_natural_alignment_v1.py, which
should only happen once the removal is confirmed — the Dirección del Parque
Natural announced it on 10 September 2026 but had not carried it out as of
17 September.

It appends one section to both labyrinth pages. It does not argue, does not
name a grievance, and does not ask anyone to go and look.
"""
from __future__ import annotations

from pathlib import Path
import re
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
if not ROOT.is_dir():
    raise SystemExit(f"Missing built site: {ROOT}")

SECTION_ES = '''<section class="tramo env" data-oolita-removal="true">
<span class="rot">Si un día no está</span>
<h2 class="grande">La piedra vuelve al claro.</h2>
<p class="parr">La Dirección del Parque Natural comunicó que retiraría el laberinto, y lo ha hecho. No hay nada que reclamar. Se colocó con piedra suelta sobre un claro que ya existía, sin mortero y sin excavar, para poder deshacerse sin dejar rastro. Eso es exactamente lo que ha ocurrido: el claro vuelve a ser el claro.</p>
<p class="parr">Un laberinto no es su piedra. Este trazado tiene unos tres mil años y ha viajado en tablillas de arcilla, en suelos de catedral, en césped, en arena y en la costa escandinava, donde más de seiscientos laberintos de piedra se rehicieron y se perdieron a lo largo de siglos. Ser borrado y vuelto a trazar forma parte de su manera de durar. Este es un borrado más.</p>
<p class="parr">La senda sigue en dos materiales: cuarenta y ocho páginas en papel, y el mismo recorrido caminable en el navegador. No dependía del sitio.</p>
</section>'''

SECTION_EN = '''<section class="tramo env" data-oolita-removal="true">
<span class="rot">If one day it is gone</span>
<h2 class="grande">The stone returns to the clearing.</h2>
<p class="parr">The Natural Park management said it would remove the labyrinth, and it has. There is nothing to contest. It was laid in loose stone on a clearing that already existed, with no mortar and no digging, so that it could be undone without leaving a trace. That is exactly what has happened: the clearing is a clearing again.</p>
<p class="parr">A labyrinth is not its stone. This pattern is some three thousand years old and has travelled on clay tablets, across cathedral floors, through turf and sand, and along the Scandinavian coast, where more than six hundred stone labyrinths were remade and lost over centuries. Being erased and drawn again is part of how it lasts. This is one more erasure.</p>
<p class="parr">The path continues in two materials: forty-eight pages on paper, and the same walk in the browser. It never depended on the site.</p>
</section>'''

for rel, section in (("laberinto/index.html", SECTION_ES),
                     ("en/labyrinth/index.html", SECTION_EN)):
    path = ROOT / rel
    if not path.is_file():
        raise SystemExit(f"Missing page for removal notice: {rel}")
    text = path.read_text(encoding="utf-8")
    if 'data-oolita-removal="true"' in text:
        continue
    text, count = re.subn(r"</main>", section + "\n</main>", text, count=1, flags=re.I)
    if count != 1:
        raise SystemExit(f"Could not append the removal section to {rel}")
    path.write_text(text, encoding="utf-8")
    print(f"Removal passage published: {rel}")

print("OOLITA removal passage applied to both labyrinth pages.")
