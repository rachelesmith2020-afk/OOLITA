#!/usr/bin/env python3
"""Apply the reviewed OOLITA wording changes to a reconstructed Pages site.

Every replacement is exact and idempotent. If the expected old wording has
changed unexpectedly, the script stops instead of guessing.
"""
from pathlib import Path
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")


def r(path, old, new, expected=1):
    p = ROOT / path
    if not p.is_file():
        raise SystemExit(f"Missing expected page: {path}")
    text = p.read_text(encoding="utf-8")
    old_count = text.count(old)
    new_count = text.count(new)
    if old_count == expected:
        text = text.replace(old, new)
        p.write_text(text, encoding="utf-8")
        print(f"patched {path}: {old[:52]!r}")
    elif old_count == 0 and new_count >= expected:
        print(f"already reviewed {path}: {new[:52]!r}")
    else:
        raise SystemExit(
            f"Unexpected wording state in {path}: expected {expected} old, "
            f"found old={old_count}, new={new_count}: {old!r}"
        )

# Homepage — Spanish
r("index.html", "Caminar un laberinto sin ir hasta él.", "El mismo camino, hecho de luz.", 2)
r("index.html", "¿Te aviso cuando se abra la puerta? <!--email_off--><a href=\"mailto:oolita@tutamail.com\">Escríbeme</a><!--/email_off--> y te llamo de vuelta el 3 de enero.", "¿Quieres que te avise cuando se abra la puerta? <!--email_off--><a href=\"mailto:oolita@tutamail.com\">Escríbeme</a><!--/email_off-->. Te escribiré el 3 de enero.")
r("index.html", "El recorrido es <a href=\"/ediciones/libro/\">el libro</a> en otra forma.", "<a href=\"/ediciones/libro/\">El libro</a> recorre la misma senda sobre papel.")
r("index.html", "<span class=\"rot\">Piedra, papel y código</span>", "<span class=\"rot\">Piedra · papel · código</span>")
r("index.html", "La misma obra en tres materiales.", "La misma senda en tres materiales.")
r("index.html", "Está hecho para quien no puede llegar hasta Almería —por distancia, por dinero o por cuerpo— y quiere caminarlo igual.", "Está hecho para quien no puede llegar hasta Almería —por distancia, por dinero o porque el cuerpo no lo permite— y aun así quiere caminarlo.")
r("index.html", "Los tres dicen lo mismo de tres maneras.", "Piedra, papel y código recorren la misma senda.")
r("index.html", "Un solo camino, un centro y un regreso", "Un camino. Un centro. Un regreso.")

# Homepage — English
r("en/index.html", "Walk a labyrinth without going there.", "The same path, made of light.", 2)
r("en/index.html", "Want to be told when the door opens? <!--email_off--><a href=\"mailto:oolita@tutamail.com\">Write to me</a><!--/email_off--> and I will call you back on 3 January.", "Want me to let you know when the door opens? <!--email_off--><a href=\"mailto:oolita@tutamail.com\">Write to me</a><!--/email_off-->. I’ll write to you on 3 January.")
r("en/index.html", "The path is <a href=\"/en/editions/book/\">the book</a> in another form.", "<a href=\"/en/editions/book/\">The book</a> follows the same path on paper.")
r("en/index.html", "<span class=\"rot\">Stone, paper and code</span>", "<span class=\"rot\">Stone · paper · code</span>")
r("en/index.html", "The same work in three materials.", "The same path in three materials.")
r("en/index.html", "It exists for anyone who cannot get to Almería, whether for distance, money or body, and wants to walk it anyway.", "It exists for anyone who cannot get to Almería because of distance, cost or accessibility, and still wants to walk it.")
r("en/index.html", "The three say the same thing three ways.", "Stone, paper and code follow the same path.")
r("en/index.html", "One path, one centre, one return", "One path. One centre. One return.")

# What is a labyrinth — Spanish
p = "que-es-un-laberinto/index.html"
r(p, "Qué es un laberinto (y por qué no es un dédalo)", "Qué es un laberinto clásico", 4)
r(p, "Un laberinto clásico tiene un solo camino: se entra, se llega al centro y se vuelve. Un dédalo tiene encrucijadas. La diferencia y cómo se camina.", "Un laberinto clásico tiene un solo camino: se entra, se llega al centro y se vuelve. Un laberinto multicursal tiene encrucijadas. La diferencia y cómo se camina.", 4)
r(p, "Un solo camino, y es más largo de lo que parece.", "Un camino. Un centro. Un regreso.")
r(p, "One single path, and it is longer than it looks", "One path. One centre. One return.")
r(p, "Un dédalo —lo que en inglés se llama <i>maze</i>— es lo contrario:", "Un laberinto multicursal —lo que en inglés se llama <i>maze</i>— es lo contrario:")
r(p, "dédalo se resuelve un problema: hay que estar alerta, elegir, corregir.", "laberinto multicursal se resuelve un problema: hay que estar alerta, elegir, corregir.")
r(p, "¿Cuál es la diferencia entre un laberinto y un dédalo?", "¿Cuál es la diferencia entre un laberinto clásico y uno multicursal?", 2)
r(p, "Un laberinto clásico es unicursal: tiene un solo camino, sin bifurcaciones ni callejones sin salida, y es imposible perderse. Un dédalo (maze en inglés) es multicursal: está lleno de encrucijadas y caminos falsos, y está diseñado para desorientar. En castellano se usa «laberinto» para los dos, y de ahí la confusión.", "Un laberinto clásico es unicursal: tiene un solo camino, sin bifurcaciones ni callejones sin salida, y es imposible perderse. Un laberinto multicursal (maze en inglés) está lleno de encrucijadas y caminos falsos, y está diseñado para desorientar. En castellano se usa «laberinto» para los dos, y de ahí la confusión.", 2)
r(p, "El libro, la obra y la cuenta atrás", "Piedra, papel y código")

# Concept pages — English and ooid cross-links
r("en/what-is-a-labyrinth/index.html", "One path, and it is longer than it looks.", "One path. One centre. One return.")
r("en/what-is-a-labyrinth/index.html", "Un solo camino, y es más largo de lo que parece", "Un camino. Un centro. Un regreso.")
r("en/what-is-a-labyrinth/index.html", "The book, the work and the countdown", "Stone, paper and code")
r("que-es-un-oolito/index.html", "El libro, la obra y la cuenta atrás", "Piedra, papel y código")
r("en/what-is-an-ooid/index.html", "The book, the work and the countdown", "Stone, paper and code")

# 22 Sundays archive framing — published Sunday entries themselves are untouched
r("domingos/index.html", "<h2>Un laberinto no es un dédalo.</h2>", "<h2>Un laberinto clásico tiene un solo camino.</h2>")
r("domingos/index.html", "Un dédalo se diseña para confundir: bifurcaciones, callejones sin salida, decisiones.", "Un laberinto multicursal —lo que en inglés se llama <i>maze</i>— se diseña para confundir: bifurcaciones, callejones sin salida, decisiones.")

# Physical labyrinth — Spanish
p = "laberinto/index.html"
r(p, "¿Me puedo perder?", "¿Puedo perderme?", 2)
r(p, "No. Un laberinto no es un acertijo: hay un solo camino, sin callejones sin salida — hacia dentro, despacio, y de vuelta.", "No. Hay un solo camino, sin bifurcaciones ni callejones sin salida — hacia dentro, despacio, y de vuelta.", 2)
r(p, "Un camino, un centro, <em>un regreso</em>.", "Un camino. Un centro. <em>Un regreso</em>.")
r(p, "One path, one centre, one return", "One path. One centre. One return.")
r(p, "Un laberinto no es un acertijo: no hay callejones sin salida ni forma de perderse.", "Este laberinto tiene un solo camino: no hay bifurcaciones ni callejones sin salida, y no hay forma de perderse.")
r(p, "El recorrido es <a href=\"/ediciones/libro/\">el libro</a> en otra forma: hacia dentro, despacio, y luego de vuelta.", "El <a href=\"/ediciones/libro/\">libro</a> recorre la misma senda: hacia dentro, despacio, y luego de vuelta.")
r(p, "¿Te aviso cuando se abra la puerta? <!--email_off--><a href=\"mailto:oolita@tutamail.com\">Escríbeme</a><!--/email_off--> y te llamo de vuelta el 3 de enero.", "¿Quieres que te avise cuando se abra la puerta? <!--email_off--><a href=\"mailto:oolita@tutamail.com\">Escríbeme</a><!--/email_off-->. Te escribiré el 3 de enero.")

# Physical labyrinth — English
p = "en/labyrinth/index.html"
r(p, "No. A labyrinth is not a maze: there is one path and no dead ends — inward, slowly, and back out.", "No. A labyrinth is not a maze: there is one path, with no forks or dead ends — inward, slowly, and back out.", 2)
r(p, "One path, one centre, <em>one return</em>.", "One path. One centre. <em>One return</em>.")
r(p, "Un camino, un centro, un regreso", "Un camino. Un centro. Un regreso.")
r(p, "A labyrinth is not a maze: there are no dead ends and no way to get lost.", "A labyrinth is not a maze: there are no forks, no dead ends and no way to get lost.")
r(p, "The walk is <a href=\"/en/editions/book/\">the book</a> in another form: inward, slowly, then back out.", "The <a href=\"/en/editions/book/\">book</a> follows the same path: inward, slowly, then back out.")
r(p, "Want to be told when the door opens? <!--email_off--><a href=\"mailto:oolita@tutamail.com\">Write to me</a><!--/email_off--> and I will call you back on 3 January.", "Want me to let you know when the door opens? <!--email_off--><a href=\"mailto:oolita@tutamail.com\">Write to me</a><!--/email_off-->. I’ll write to you on 3 January.")

# Posters — page count and Spanish labyrinth terminology
r("carteles/index.html", "44-page", "48-page", 2)
r("carteles/index.html", "Un laberinto no es un dédalo: un solo camino de entrada, hacia el centro y de vuelta.", "Un laberinto clásico tiene un solo camino: entrada, centro y regreso.")
r("carteles/index.html", "Un laberinto no es un dédalo. Tiene un solo camino de entrada, hacia el centro y de vuelta. No hay decisiones, atajos ni callejones sin salida.", "Un laberinto clásico tiene un solo camino de entrada, hacia el centro y de vuelta. No hay decisiones, atajos ni callejones sin salida.")
r("en/posters/index.html", "44-page", "48-page", 4)
r("en/posters/index.html", "Un laberinto no es un dédalo. Tiene un solo camino de entrada, hacia el centro y de vuelta. No hay decisiones, atajos ni callejones sin salida.", "Un laberinto clásico tiene un solo camino de entrada, hacia el centro y de vuelta. No hay decisiones, atajos ni callejones sin salida.")

print("OOLITA wording review applied successfully.")
