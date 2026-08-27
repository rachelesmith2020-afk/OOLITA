#!/usr/bin/env python3
"""Resilient Cabo de Gata direction pass for OOLITA.

Runs the already-tested homepage/editions-index pass, tolerates its known stop
on product-page formatting, then finishes product and labyrinth edits with
semantic paragraph-level replacements and strict final invariants.
"""
from pathlib import Path
import re
import runpy
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
HERE = Path(__file__).resolve().parent

# Reuse all homepage + Editions-index changes already proven by v2.
old_argv = sys.argv[:]
sys.argv = [str(HERE / "apply_direction_v2.py"), str(ROOT)]
try:
    runpy.run_path(str(HERE / "apply_direction_v2.py"), run_name="__main__")
except SystemExit as exc:
    print(f"v2 partial pass stopped as expected; resilient finish continues: {exc}")
finally:
    sys.argv = old_argv


def text(path):
    p = ROOT / path
    if not p.is_file():
        raise SystemExit(f"Missing expected page: {path}")
    return p, p.read_text(encoding="utf-8")


def replace_regex(path, pattern, replacement, *, must_contain=None, flags=re.S):
    p, s = text(path)
    if must_contain and must_contain in s:
        print(f"already direction-reviewed {path}: {must_contain[:60]!r}")
        return
    ns, n = re.subn(pattern, replacement, s, count=1, flags=flags)
    if n != 1:
        raise SystemExit(f"Direction replacement failed in {path}: {pattern[:120]!r}; matches={n}")
    p.write_text(ns, encoding="utf-8")
    print(f"direction patched {path}: {pattern[:70]!r}")


def replace_all(path, old, new, *, optional=False):
    p, s = text(path)
    if old not in s:
        if new in s:
            print(f"already direction-reviewed {path}: {new[:60]!r}")
            return
        if optional:
            print(f"optional direction literal absent {path}: {old[:60]!r}")
            return
        raise SystemExit(f"Direction literal missing in {path}: {old[:120]!r}")
    p.write_text(s.replace(old, new), encoding="utf-8")
    print(f"direction patched {path}: {old[:70]!r}")


# ---- Book: remove unprovable workshop-proximity/travel claims ----
replace_regex(
    "ediciones/libro/index.html",
    r'<p class="parr">Sin almacenes[^<]*</p>',
    '<p class="parr">Sin almacenes y sin tiradas que sobran: cada ejemplar se produce después del pedido. Los datos de impresión y entrega se indicarán en esta página.</p>',
    must_contain="Los datos de impresión y entrega se indicarán en esta página.",
)
replace_regex(
    "ediciones/libro/index.html",
    r'<p class="parr">[^<]*(?:imprenta más cercana|viaja poco)[^<]*</p>',
    '<p class="parr">Al imprimirse de uno en uno, no hay stock que agotar ni reediciones que esperar. Cada ejemplar se produce después del pedido; los datos de impresión y entrega se publicarán antes de la salida.</p>',
    must_contain="los datos de impresión y entrega se publicarán antes de la salida.",
)
replace_regex(
    "en/editions/book/index.html",
    r'<p class="parr">No warehouses[^<]*</p>',
    '<p class="parr">No warehouses, no leftover print runs: each copy is produced after it is ordered. Printing and delivery details will be stated on this page.</p>',
    must_contain="Printing and delivery details will be stated on this page.",
)
replace_regex(
    "en/editions/book/index.html",
    r'<p class="parr">[^<]*(?:press nearest|travels so little|travels lightly)[^<]*</p>',
    '<p class="parr">Because it is printed one at a time, there is no stock to run out and no reprint to wait for. Each copy is produced after the order; printing and delivery details will be published before release.</p>',
    must_contain="printing and delivery details will be published before release.",
)

# ---- T-shirt: make it the first textile edition, not avatar merchandise ----
replace_regex(
    "ediciones/camiseta/index.html",
    r'<h2>Primero la verás en el mundo\.</h2>.*?(?=<h2>Qué prenda es\.</h2>)',
    '<h2>La primera edición textil.</h2><p class="parr">La primera edición textil lleva el laberinto a la tela. Las futuras ediciones numeradas explorarán imágenes de Hallazgo, color natural y colaboraciones arraigadas en los materiales y saberes artesanos de Cabo de Gata.</p><p class="parr">Esta primera pieza es una camiseta de algodón orgánico de 200 gramos y corte holgado. La imagen impresa — y dónde va colocada — se irá desvelando poco a poco.</p>',
    must_contain="La primera edición textil lleva el laberinto a la tela.",
)
replace_regex(
    "ediciones/camiseta/index.html",
    r'<p class="parr">Sale el 28 de marzo de 2027[^<]*</p>',
    '<p class="parr">Sale el 28 de marzo de 2027, dos meses después del libro. Se imprime bajo demanda, de una en una; los datos de producción y entrega se publicarán en esta página antes de la salida.</p>',
    must_contain="los datos de producción y entrega se publicarán en esta página antes de la salida.",
)
replace_regex(
    "en/editions/t-shirt/index.html",
    r'<h2>You will see it in the world first\.</h2>.*?(?=<h2>Which garment it is\.</h2>)',
    '<h2>The first textile edition.</h2><p class="parr">The first textile edition carries the labyrinth into cloth. Future numbered editions will explore images from Hallazgo, natural colour and collaborations rooted in the materials and craft knowledge of Cabo de Gata.</p><p class="parr">This first piece is a 200 gsm organic-cotton T-shirt with a loose cut. The printed image — and where it sits — will be revealed little by little.</p>',
    must_contain="The first textile edition carries the labyrinth into cloth.",
)
replace_regex(
    "en/editions/t-shirt/index.html",
    r'<p class="parr">It comes out on 28 March 2027[^<]*</p>',
    '<p class="parr">It comes out on 28 March 2027, two months after the book. It is printed on demand, one at a time; production and delivery details will be published on this page before release.</p>',
    must_contain="production and delivery details will be published on this page before release.",
)

# ---- Labyrinth: remove unsupported always-open/public-access wording ----
for path, old, new in [
    ("laberinto/index.html", "Gratis y siempre abierto.", "Cómo llegar, qué esperar y cómo acercarse con cuidado."),
    ("en/labyrinth/index.html", "What to expect. Free, always open.", "How to find it and what to expect."),
]:
    p, s = text(path)
    if old in s:
        p.write_text(s.replace(old, new), encoding="utf-8")

for path in ("laberinto/index.html", "en/labyrinth/index.html"):
    p, s = text(path)
    s = s.replace('      "publicAccess": true,\n', '')
    p.write_text(s, encoding="utf-8")

# The FAQ JSON-LD has changed shape on the live origin over time. Treat these
# exact legacy literals as optional while keeping the final required/forbidden
# invariants below strict. The Spanish target here is the approved native edit,
# not the older direction-pass wording.
replace_all(
    "laberinto/index.html",
    '            "text": "Sí, es gratis, y no: está al aire libre, siempre abierto, sin entradas ni horarios."',
    '            "text": "Es gratuito y no requiere reserva. No hay personal; si lo visitas, acércate con cuidado y respeto por el entorno."',
    optional=True,
)
replace_all(
    "en/labyrinth/index.html",
    '            "text": "Yes, it is free, and no: it is in the open air, always open, no tickets and no opening hours."',
    '            "text": "There is no ticket or booking. The labyrinth is unstaffed; if you visit, approach it lightly and respectfully."',
    optional=True,
)
replace_regex(
    "laberinto/index.html",
    r'<p class="glosa">(?=[\s\S]*?Gratis, siempre abierto\.)[\s\S]*?</p>',
    '<p class="glosa">Un <a href="/que-es-un-laberinto/">laberinto clásico</a> de tres metros, hecho a mano en septiembre de 2021 con calcarenita suelta — piedra recogida a pocos pasos de donde ahora está — sobre una <a href="/que-es-un-oolito/">duna fósil</a> que hace cien mil años fue fondo del mar. Este laberinto tiene un solo camino: no hay bifurcaciones ni callejones sin salida, y no hay forma de perderse. Se camina despacio. Se encuentra junto al Castillo de San Felipe. No tiene personal ni entrada; recorrerlo es gratuito y conviene acercarse con cuidado y respeto por el lugar.</p>',
    must_contain="Se encuentra junto al Castillo de San Felipe.",
)
replace_regex(
    "en/labyrinth/index.html",
    r'<p class="glosa">(?=[\s\S]*?Free, always open\.)[\s\S]*?</p>',
    '<p class="glosa">A three-metre <a href="/en/what-is-a-labyrinth/">classical labyrinth</a>, laid by hand in September 2021 from loose calcarenite — stone gathered within a few paces of where it now lies — on a <a href="/en/what-is-an-ooid/">fossil dune</a> that was seabed a hundred thousand years ago. A labyrinth is not a maze: there are no forks, no dead ends and no way to get lost. You walk it slowly. It can be found beside the Castillo de San Felipe. It is unstaffed, free to encounter and should be approached lightly and respectfully.</p>',
    must_contain="It can be found beside the Castillo de San Felipe.",
)
for path, old, new in [
    ("laberinto/index.html", '<span class="rot">Geoparque UNESCO</span>', '<span class="rot">Cabo de Gata-Níjar</span>'),
    ("en/labyrinth/index.html", '<span class="rot">UNESCO Geopark</span>', '<span class="rot">Cabo de Gata-Níjar</span>'),
    ("laberinto/index.html", '<div><span class="k">Acceso</span><span class="v">Libre y gratuito, todo el año</span></div>', '<div><span class="k">Acceso</span><span class="v">Libre · sin personal ni reserva</span></div>'),
    ("en/labyrinth/index.html", '<div><span class="k">Access</span><span class="v">Free and open, all year</span></div>', '<div><span class="k">Access</span><span class="v">Unstaffed · no ticket or booking</span></div>'),
    ("laberinto/index.html", '<p class="parr">Sí, es gratis, y no: está al aire libre, siempre abierto, sin entradas ni horarios.</p>', '<p class="parr">Es gratuito y no requiere reserva. No hay personal; si lo visitas, acércate con cuidado y respeto por el entorno.</p>'),
    ("en/labyrinth/index.html", '<p class="parr">Yes, it is free, and no: it is in the open air, always open, no tickets and no opening hours.</p>', '<p class="parr">There is no ticket or booking. The labyrinth is unstaffed; if you visit, approach it lightly and respectfully.</p>'),
]:
    replace_all(path, old, new)

# ---- Strict final checks ----
required = {
    "index.html": ["De un camino, un paisaje más amplio.", "Publicaciones de campo, materiales y colaboraciones"],
    "en/index.html": ["From one path, a wider landscape.", "Field publications, materials and collaborations"],
    "ediciones/index.html": [
        "Libros, textiles y herramientas para mirar de cerca.",
        "Después vendrá la edición de tapa dura de Hallazgo",
    ],
    "en/editions/index.html": [
        "Books, textiles and tools for looking closely.",
        "After them will come the Hallazgo hardback",
    ],
    "ediciones/libro/index.html": ["Los datos de impresión y entrega se indicarán en esta página."],
    "en/editions/book/index.html": ["Printing and delivery details will be stated on this page."],
    "ediciones/camiseta/index.html": ["La primera edición textil lleva el laberinto a la tela."],
    "en/editions/t-shirt/index.html": ["The first textile edition carries the labyrinth into cloth."],
    "laberinto/index.html": ["Libre · sin personal ni reserva"],
    "en/labyrinth/index.html": ["Unstaffed · no ticket or booking"],
}
for path, needles in required.items():
    _, s = text(path)
    for needle in needles:
        if needle not in s:
            raise SystemExit(f"Missing direction invariant in {path}: {needle}")

forbidden = {
    "ediciones/libro/index.html": ["imprenta más cercana", "viaja poco"],
    "en/editions/book/index.html": ["press nearest", "travels so little", "travels lightly"],
    "ediciones/camiseta/index.html": ["cerca de donde viaja"],
    "en/editions/t-shirt/index.html": ["near where it is going", "This is the t-shirt the avatar wears"],
    "laberinto/index.html": ["siempre abierto", "publicAccess"],
    "en/labyrinth/index.html": ["always open", "publicAccess"],
}
for path, needles in forbidden.items():
    _, s = text(path)
    for needle in needles:
        if needle in s:
            raise SystemExit(f"Forbidden claim remains in {path}: {needle}")

print("OOLITA Cabo de Gata direction v3 validated successfully.")
