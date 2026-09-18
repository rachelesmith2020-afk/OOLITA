#!/usr/bin/env python3
"""Restore the bilingual OOLITA poster archive after retirement of poster 03.

The live site is the reconstruction origin. Because the retired campaign removes
poster 03 and the Sunday archive, the poster archive must have a stable source
representation in the repository rather than depend on a previous live page.
"""
from __future__ import annotations

from pathlib import Path
import re
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
if not ROOT.is_dir():
    raise SystemExit(f"Missing built site: {ROOT}")

POSTERS = (
    {
        "n": "01",
        "alt_es": "Cartel azul vivo con OOLITA intacto en grandes letras amarillo sol",
        "alt_en": "Bright-blue poster with OOLITA intact in large sun-yellow letters",
        "title_es": "OOLITA",
        "title_en": "OOLITA",
        "text_es": "Un laberinto de piedra en Los Escullos, Cabo de Gata. Un camino. Un centro. Un regreso.",
        "text_en": "A stone labyrinth in Los Escullos, Cabo de Gata. One path. One centre. One return.",
    },
    {
        "n": "02",
        "alt_es": "Cartel amarillo sol que dice PIEDRA / PAPEL / CÓDIGO en cobalto, cada línea sobre el mismo eje izquierdo",
        "alt_en": "Sun-yellow poster reading PIEDRA / PAPEL / CÓDIGO — STONE / PAPER / CODE — in cobalt, every line on the same left axis",
        "title_es": "Piedra / Papel / Código",
        "title_en": "Stone / Paper / Code",
        "text_es": "Tres materiales sostienen esta serie. Piedra: el laberinto, puesto a mano en 2021. Papel: una fábula bilingüe de 48 páginas. Código: un mundo caminable, todavía en construcción.",
        "text_en": "Three materials hold this series. Stone: the labyrinth, laid by hand in 2021. Paper: a 48-page bilingual fable. Code: a walkable world, still under construction.",
    },
    {
        "n": "04",
        "alt_es": "Cartel calcáreo cálido que dice Un camino. Un centro. Un regreso. en azul sobre un eje izquierdo",
        "alt_en": "Warm-limestone poster reading One path. One centre. One return. in blue on one left axis",
        "title_es": "Un camino. Un centro. Un regreso.",
        "title_en": "One path. One centre. One return.",
        "text_es": "Un laberinto clásico tiene un solo camino de entrada, hacia el centro y de vuelta. No hay decisiones, atajos ni callejones sin salida.",
        "text_en": "A labyrinth is not a maze. It has one path in, to the centre and back out. There are no choices, shortcuts or dead ends.",
    },
    {
        "n": "05",
        "alt_es": "Cartel verde fresco que dice La memoria del mar en grandes letras blanco cálido sobre un eje izquierdo",
        "alt_en": "Fresh-green poster reading The memory of the sea in large warm-white type on one left axis",
        "title_es": "La memoria del mar",
        "title_en": "The memory of the sea",
        "text_es": "Oolita toma su nombre de las dunas fósiles oolíticas de Los Escullos. En agua cálida y poco profunda, granos sueltos se redondearon capa sobre capa hasta formar oolitos. El viento levantó las dunas; las dunas se endurecieron en piedra.",
        "text_en": "Oolita takes its name from the oolitic fossil dunes of Los Escullos. In warm shallow water, loose grains rounded layer by layer into ooids. Wind built the dunes; the dunes hardened into stone.",
    },
    {
        "n": "06",
        "alt_es": "Cartel amarillo sol que dice Hallado, no tomado en grandes letras coral sobre un eje izquierdo",
        "alt_en": "Sun-yellow poster reading Found, not taken in large coral type on one left axis",
        "title_es": "Hallado, no tomado",
        "title_en": "Found, not taken",
        "text_es": "Nada entra en Hallazgo si su ciclo no ha terminado: flores caídas, vainas secas, plumas mudadas, conchas vaciadas por el mar. No se corta nada vivo. No se rompe ninguna rama. Hallazgo reúne 44 obras, registradas de H001 a H044.",
        "text_en": "Nothing enters Hallazgo unless its cycle is complete: fallen flowers, dry pods, shed feathers, shells emptied by the sea. Nothing living is cut. No branch is broken. Hallazgo brings together 44 works, registered H001 to H044.",
    },
    {
        "n": "07",
        "alt_es": "Cartel coral que dice Hecho para caminar en grandes letras calcáreas sobre un eje izquierdo",
        "alt_en": "Coral poster reading Made to be walked in large warm-limestone type on one left axis",
        "title_es": "Hecho para caminar",
        "title_en": "Made to be walked",
        "text_es": "Oolita nació de un laberinto clásico de tres metros, trazado a mano con piedras sueltas en 2021. El entorno es frágil: permanece en los senderos y deja las piedras donde están.",
        "text_en": "Oolita began with a three-metre classical labyrinth, laid by hand from loose stones in 2021. This archive records the original work; it does not offer access to the installation.",
    },
    {
        "n": "08",
        "alt_es": "Cartel azul vivo que dice En construcción, en código en letras blanco cálido sobre un eje izquierdo",
        "alt_en": "Bright-blue poster reading Being built in code in warm-white type on one left axis",
        "title_es": "En construcción, en código",
        "title_en": "Being built in code",
        "text_es": "Una Oolita digital se está construyendo a partir de mediciones del terreno real de Los Escullos. Todavía no está abierta. El mundo 3D de OOLITA abre el 23 de mayo de 2027.",
        "text_en": "A digital Oolita is being built from measurements of the real terrain at Los Escullos. It is not open yet. The OOLITA 3D world opens on 23 May 2027.",
    },
    {
        "n": "09",
        "alt_es": "Cartel calcáreo cálido que dice Para los días en que el mundo suena demasiado fuerte en verde sobre un eje izquierdo",
        "alt_en": "Warm-limestone poster reading For the days when the world feels too loud in green on one left axis",
        "title_es": "Para los días en que el mundo suena demasiado fuerte",
        "title_en": "For the days when the world feels too loud",
        "text_es": "El libro Oolita es una fábula bilingüe de 48 páginas. Electro, un gato real de esta costa, camina el laberinto. Disponible en papel desde el 27 de junio de 2027.",
        "text_en": "The Oolita book is a 48-page bilingual fable. Electro, a real cat from this coast, walks the labyrinth. Available in print from 27 June 2027.",
    },
)

def figure(item: dict[str, str], *, en: bool) -> str:
    n = item["n"]
    primary = "en" if en else "es"
    secondary = "es" if en else "en"
    secondary_lang = "es" if en else "en"
    loading = ' fetchpriority="high"' if n == "01" else ' loading="lazy"'
    return f'''<figure class="cartel">
<span class="num">{n}</span>
<picture>
<source srcset="/carteles/img/cartel-{n}.avif" type="image/avif">
<source srcset="/carteles/img/cartel-{n}.webp" type="image/webp">
<img src="/carteles/img/cartel-{n}.png" alt="{item[f"alt_{primary}"]}" width="1080" height="1350" decoding="async"{loading}>
</picture>
<figcaption>
<p class="titulo">{item[f"title_{primary}"]}</p>
<p class="texto">{item[f"text_{primary}"]}</p>
<p class="texto-en" lang="{secondary_lang}">{item[f"text_{secondary}"]}</p>
</figcaption>
</figure>'''

def main_markup(*, en: bool) -> str:
    if en:
        intro = '''<section class="tramo">
<span class="rot">The opening of the account</span>
<h1 class="grande">The posters</h1>
<p class="lema">Stone, paper and code, <em>announced in a series of plates</em>.</p>
<p class="lema-en" lang="es">Piedra, papel y código, anunciados en una serie de láminas</p>
<p class="glosa">These typographic posters opened the <a href="https://www.instagram.com/oolita.es/">@oolita.es</a> account in August 2026: the introduction of the Los Escullos labyrinth, <a href="/en/editions/book/">the book</a>, and the 3D world. The 3D world opens on 23 May 2027.</p>
<p class="parr"><strong>Archive:</strong> this selection keeps the posters that remain part of the project. For the current context, see <a href="/en/labyrinth/">The labyrinth</a>.</p>
<div class="datos"><span class="rot">Bilingual archive</span><span class="rot">Bilingual</span><span class="rot">August 2026</span></div>
</section>'''
        label = "The series"
    else:
        intro = '''<section class="tramo">
<span class="rot">La apertura de la cuenta</span>
<h1 class="grande">Los carteles</h1>
<p class="lema">Piedra, papel y código, <em>anunciados en una serie de láminas</em>.</p>
<p class="lema-en" lang="en">Stone, paper and code, announced in a series of plates</p>
<p class="glosa">Con estos carteles tipográficos abrió la cuenta <a href="https://www.instagram.com/oolita.es/">@oolita.es</a> en agosto de 2026: la presentación del laberinto de Los Escullos, <a href="/ediciones/libro/">del libro</a> y del mundo 3D. El mundo 3D abre el 23 de mayo de 2027.</p>
<p class="parr"><strong>Archivo:</strong> esta selección conserva los carteles que siguen formando parte del proyecto. Para el contexto actual, consulta <a href="/laberinto/">El laberinto</a>.</p>
<div class="datos"><span class="rot">Archivo bilingüe</span><span class="rot">Bilingüe</span><span class="rot">Agosto 2026</span></div>
</section>'''
        label = "La serie"
    figures = "\n".join(figure(item, en=en) for item in POSTERS)
    return f'''<main id="contenido" data-page-purpose="poster-archive" data-primary-event="posters">
{intro}
<section class="tramo">
<span class="rot">{label}</span>
{figures}
</section>
</main>'''

def patch(rel: str, *, en: bool) -> None:
    path = ROOT / rel
    if not path.is_file():
        raise SystemExit(f"Missing poster archive shell: {rel}")
    text = path.read_text(encoding="utf-8")
    main_re = re.compile(r"<main\b[^>]*>.*?</main>", re.I | re.S)
    if not main_re.search(text):
        raise SystemExit(f"Poster archive has no main element: {rel}")
    text = main_re.sub(main_markup(en=en), text, count=1)
    text = text.replace("The nine typographic posters", "The typographic posters")
    text = text.replace("Los nueve carteles tipográficos", "Los carteles tipográficos")
    path.write_text(text, encoding="utf-8")

    final = path.read_text(encoding="utf-8")
    if final.count('<figure class="cartel">') != 8:
        raise SystemExit(f"{rel}: expected 8 retained posters")
    banned = (
        "22 Sundays", "22 domingos", "3 January", "3 de enero",
        "31 January", "31 de enero", "11 April", "11 de abril",
        "Mayuary", "every Sunday", "cada domingo", "cartel-03.",
        "/domingos/", "/en/sundays/",
    )
    for needle in banned:
        if needle.lower() in final.lower():
            raise SystemExit(f"{rel}: obsolete poster chronology survived: {needle}")
    for needle in ("23 May 2027", "27 June 2027") if en else ("23 de mayo de 2027", "27 de junio de 2027"):
        if needle not in final:
            raise SystemExit(f"{rel}: required current date missing: {needle}")

patch("carteles/index.html", en=False)
patch("en/posters/index.html", en=True)
print("OOLITA poster archive restored: 8 retained posters, current 2027 dates, no Sunday campaign.")
