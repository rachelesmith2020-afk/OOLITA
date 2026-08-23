#!/usr/bin/env python3
"""Apply and validate OOLITA's confirmed 2026–27 release calendar.

This final content layer runs after Follow OOLITA has been activated. It keeps
the book specification, textile release, Sunday-series midpoint and Hallazgo
preview consistent across the bilingual site without enabling checkout or
claiming that the Hallazgo hardback is already on sale.
"""
from pathlib import Path
import sys


ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")


def page(path: str) -> tuple[Path, str]:
    target = ROOT / path
    if not target.is_file():
        raise SystemExit(f"Missing release-calendar page: {path}")
    return target, target.read_text(encoding="utf-8")


def replace_text(path: str, old: str, new: str) -> None:
    target, text = page(path)
    if old in text:
        count = text.count(old)
        target.write_text(text.replace(old, new), encoding="utf-8")
        print(f"release calendar patched {path}: {count} occurrence(s)")
        return
    if new not in text:
        raise SystemExit(
            f"Expected release-calendar source text missing in {path}: {old[:120]!r}"
        )


def replace_across_html(old: str, new: str) -> int:
    changed = 0
    for target in ROOT.rglob("*.html"):
        text = target.read_text(encoding="utf-8")
        if old not in text:
            continue
        count = text.count(old)
        target.write_text(text.replace(old, new), encoding="utf-8")
        changed += count
    if changed:
        print(f"release calendar replaced {old!r}: {changed} occurrence(s)")
    return changed


# The finished book is 48 pages. Keep prose, metadata, structured data and the
# bilingual poster archive aligned while leaving Hallazgo inventory IDs such
# as H044 untouched.
for old, new in (
    ("Forty-four pages", "Forty-eight pages"),
    ("forty-four pages", "forty-eight pages"),
    ("Cuarenta y cuatro páginas", "Cuarenta y ocho páginas"),
    ("cuarenta y cuatro páginas", "cuarenta y ocho páginas"),
    ("44-page", "48-page"),
    ("44 pages", "48 pages"),
    ("44 páginas", "48 páginas"),
):
    replace_across_html(old, new)


# Editions overview: 11 April release, with the details and story revealed
# Sunday by Sunday rather than pretending the complete design is invisible.
replace_text(
    "ediciones/index.html",
    '<p class="parr">El libro sale el 31 de enero de 2027. La primera edición textil llega el 28 de marzo, cuando su diseño termine de desvelarse domingo a domingo.</p>',
    '<p class="parr">El libro sale el 31 de enero de 2027. La primera edición textil llega el 11 de abril. Los detalles y la historia del diseño se irán desvelando domingo a domingo hasta entonces.</p>',
)
replace_text(
    "en/editions/index.html",
    '<p class="parr">The book comes out on 31 January 2027. The first textile edition follows on 28 March, once its design has been revealed Sunday by Sunday.</p>',
    '<p class="parr">The book comes out on 31 January 2027. The first textile edition follows on 11 April. Details and the story of the design will be revealed Sunday by Sunday until then.</p>',
)


# Product-page editorial copy and metadata.
for path, changes in {
    "ediciones/camiseta/index.html": (
        (
            "Blanca, de algodón orgánico de 200 gramos, de corte oversized unisex. Por ahora, sólo la prenda desnuda: el diseño se irá desvelando, domingo a domingo,…",
            "Blanca, de algodón orgánico de 200 gramos y corte oversized unisex. Los detalles y la historia del diseño se irán contando domingo a domingo hasta la primavera.",
        ),
        (
            '<p class="pieimg">El diseño se desvela pronto</p>',
            '<p class="pieimg">Detalles del diseño · domingo a domingo</p>',
        ),
        (
            '<p class="glosa">Blanca, de algodón orgánico de 200 gramos, de corte oversized unisex. Por ahora, sólo la prenda desnuda: el diseño se irá desvelando, domingo a domingo, hasta la primavera.</p>',
            '<p class="glosa">Blanca, de algodón orgánico de 200 gramos y corte oversized unisex. Los detalles y la historia del diseño se irán contando domingo a domingo hasta la primavera.</p>',
        ),
        (
            '<p class="parr">Esta primera pieza es una camiseta de algodón orgánico de 200 gramos y corte holgado. La imagen impresa — y dónde va colocada — se irá desvelando poco a poco.</p>',
            '<p class="parr">Esta primera pieza es una camiseta de algodón orgánico de 200 gramos y corte holgado. Los detalles de la imagen impresa, su colocación y su historia se irán desvelando poco a poco.</p>',
        ),
        (
            '<h2>Por qué se desvela despacio.</h2><p class="parr">Por ahora sólo está la prenda desnuda, y a propósito. El diseño se irá viendo domingo a domingo hasta la primavera, al mismo ritmo que la serie de las imágenes: cada domingo se ve un poco más de lo que va impreso y de dónde va colocado.</p>',
            '<h2>Por qué se cuenta despacio.</h2><p class="parr">La prenda aparece primero en blanco en esta página, a propósito. Los detalles y la historia del diseño se irán desvelando domingo a domingo hasta la primavera: cada entrega contará algo más de la imagen, su colocación y su relación con el laberinto.</p>',
        ),
        (
            '<p class="parr">Sale el 28 de marzo de 2027, dos meses después del libro. Se imprime bajo demanda, de una en una; los datos de producción y entrega se publicarán en esta página antes de la salida.</p>',
            '<p class="parr">Sale el 11 de abril de 2027, después del libro. Se imprime bajo demanda, de una en una; los datos de producción y entrega se publicarán en esta página antes de la salida.</p>',
        ),
        (
            '<div><span class="k">Diseño</span><span class="v">Se desvela pronto</span></div>',
            '<div><span class="k">Diseño</span><span class="v">Detalles e historia · domingo a domingo</span></div>',
        ),
    ),
    "en/editions/t-shirt/index.html": (
        (
            "White, 200 gsm organic cotton, an oversized unisex fit. For now just the bare garment: the design is unveiled Sunday by Sunday, through to spring.",
            "White, 200 gsm organic cotton with an oversized unisex fit. Details and the story of the design will unfold Sunday by Sunday through to spring.",
        ),
        (
            '<p class="pieimg">The design is revealed soon</p>',
            '<p class="pieimg">Design details · Sunday by Sunday</p>',
        ),
        (
            '<p class="glosa">White, 200 gsm organic cotton, an oversized unisex fit. For now just the bare garment: the design is unveiled Sunday by Sunday, through to spring.</p>',
            '<p class="glosa">White, 200 gsm organic cotton with an oversized unisex fit. Details and the story of the design will unfold Sunday by Sunday through to spring.</p>',
        ),
        (
            '<p class="parr">This first piece is a 200 gsm organic-cotton T-shirt with a loose cut. The printed image — and where it sits — will be revealed little by little.</p>',
            '<p class="parr">This first piece is a 200 gsm organic-cotton T-shirt with a loose cut. Details of the printed image, its placement and its story will be revealed little by little.</p>',
        ),
        (
            '<h2>Why it is revealed slowly.</h2><p class="parr">For now there is only the bare garment, and that is on purpose. The design will be revealed Sunday by Sunday through to spring, at the same pace as the image series: each Sunday shows a little more of what is printed and where it sits.</p>',
            '<h2>Why its story unfolds slowly.</h2><p class="parr">The garment appears first as a blank piece on this page, on purpose. Details and the story of the design will unfold Sunday by Sunday through to spring: each instalment will say more about the image, its placement and its relationship to the labyrinth.</p>',
        ),
        (
            '<p class="parr">It comes out on 28 March 2027, two months after the book. It is printed on demand, one at a time; production and delivery details will be published on this page before release.</p>',
            '<p class="parr">It comes out on 11 April 2027, after the book. It is printed on demand, one at a time; production and delivery details will be published on this page before release.</p>',
        ),
        (
            '<div><span class="k">Design</span><span class="v">Revealed soon</span></div>',
            '<div><span class="k">Design</span><span class="v">Details and story · Sunday by Sunday</span></div>',
        ),
    ),
}.items():
    for old, new in changes:
        replace_text(path, old, new)


# Catch date labels and cards after the editorial paragraphs have been fixed.
for old, new in (
    ("28.03.27", "11.04.27"),
    ("28 de marzo de 2027", "11 de abril de 2027"),
    ("28 March 2027", "11 April 2027"),
    ("28 de marzo", "11 de abril"),
    ("28 March", "11 April"),
):
    replace_across_html(old, new)


# A 22-part series turns between entries 11 and 12, not on one entry alone.
replace_text(
    "domingos/index.html",
    '<p class="parr">Los veintidós domingos siguen ese mismo trazado. Los primeros llevan hacia dentro. El domingo once es el centro. Los que vienen después son el regreso, que en un laberinto ocupa exactamente lo mismo que la ida. El último, el 3 de enero, es la salida.</p>',
    '<p class="parr">Los veintidós domingos siguen ese mismo trazado. Los domingos once y doce contienen el giro: el once llega al centro; el doce comienza el regreso. Los anteriores llevan hacia dentro; los posteriores vuelven hacia la salida. El último, el 3 de enero, es la salida.</p>',
)
replace_text(
    "en/sundays/index.html",
    '<p class="parr">The twenty-two Sundays follow that same drawing. The early ones lead inward. Sunday eleven is the centre. The ones after it are the return, which in a labyrinth takes exactly as long as the way in. The last, on 3 January, is the exit.</p>',
    '<p class="parr">The twenty-two Sundays follow that same drawing. Sundays eleven and twelve hold the turn: eleven arrives at the centre; twelve begins the return. The earlier Sundays lead inward; the later ones return towards the exit. The last, on 3 January, is the exit.</p>',
)


# Direct people to the active first-party Follow section instead of asking for
# an individual email. This works from the homepage, 404 mirror and labyrinth.
replace_across_html(
    '¿Quieres que te avise cuando se abra la puerta? <!--email_off--><a href="mailto:oolita@tutamail.com">Escríbeme</a><!--/email_off-->. Te escribiré el 3 de enero.',
    '<a href="/#seguir-oolita">Sigue OOLITA</a> para recibir un aviso cuando se abra el mundo.',
)
replace_across_html(
    'Want me to let you know when the door opens? <!--email_off--><a href="mailto:oolita@tutamail.com">Write to me</a><!--/email_off-->. I’ll write to you on 3 January.',
    '<a href="/en/#follow-oolita">Follow OOLITA</a> to be notified when the world opens.',
)


# The OOLITA site can publish the Hallazgo sequence now. The castle remains
# free; the full catalogue in its reading room needs a key. The hardback is a
# plan for autumn, not a live product or checkout claim.
hallazgo_pages = {
    "index.html": (
        ("Obra de Raquel Costantini ↗", "Castillo virtual · entrada libre · abre 16.05.27 · 19:00 CEST ↗"),
        ("Registro ilustrado de la obra de Hallazgo ↗", "En el castillo: catálogo completo con clave · tapa dura prevista para otoño de 2027 ↗"),
    ),
    "en/index.html": (
        ("Work by Raquel Costantini ↗", "Virtual castle · free to enter · opens 16.05.27 · 19:00 CEST ↗"),
        ("Illustrated record of the Hallazgo works ↗", "In the castle: full catalogue with a key · hardback planned for autumn 2027 ↗"),
    ),
}
error_page = next((path for path in ("404.html", "404/index.html") if (ROOT / path).is_file()), None)
if error_page:
    hallazgo_pages[error_page] = (
        ("Obra de Raquel Costantini ↗", "Castillo virtual · entrada libre · abre 16.05.27 · 19:00 CEST ↗"),
        ("Registro ilustrado de la obra de Hallazgo ↗", "En el castillo: catálogo completo con clave · tapa dura prevista para otoño de 2027 ↗"),
    )
for path, changes in hallazgo_pages.items():
    for old, new in changes:
        replace_text(path, old, new)


# Strict release checks prevent a clean-origin rebuild from restoring old copy.
required = {
    "index.html": [
        "Cuarenta y ocho páginas",
        'href="/#seguir-oolita">Sigue OOLITA</a>',
        "Castillo virtual · entrada libre · abre 16.05.27 · 19:00 CEST",
        "tapa dura prevista para otoño de 2027",
    ],
    "en/index.html": [
        "Forty-eight pages",
        'href="/en/#follow-oolita">Follow OOLITA</a>',
        "Virtual castle · free to enter · opens 16.05.27 · 19:00 CEST",
        "hardback planned for autumn 2027",
    ],
    "ediciones/libro/index.html": ["Cuarenta y ocho páginas", "48 páginas"],
    "en/editions/book/index.html": ["Forty-eight pages", "48 pages"],
    "ediciones/camiseta/index.html": ["11.04.27", "Sale el 11 de abril de 2027", "detalles y la historia del diseño"],
    "en/editions/t-shirt/index.html": ["11.04.27", "It comes out on 11 April 2027", "Details and the story of the design"],
    "domingos/index.html": ["el once llega al centro; el doce comienza el regreso"],
    "en/sundays/index.html": ["eleven arrives at the centre; twelve begins the return"],
}
for path, needles in required.items():
    _, text = page(path)
    for needle in needles:
        if needle not in text:
            raise SystemExit(f"Release-calendar invariant missing in {path}: {needle!r}")

forbidden = (
    "Forty-four pages",
    "forty-four pages",
    "Cuarenta y cuatro páginas",
    "cuarenta y cuatro páginas",
    "44-page",
    "44 pages",
    "44 páginas",
    "28.03.27",
    "28 March 2027",
    "28 de marzo de 2027",
    "Sunday eleven is the centre",
    "El domingo once es el centro",
    "once its design has been revealed Sunday by Sunday",
    "The design will be revealed Sunday by Sunday through to spring",
    "diseño se irá viendo domingo a domingo hasta la primavera",
)
for target in ROOT.rglob("*.html"):
    text = target.read_text(encoding="utf-8")
    for phrase in forbidden:
        if phrase in text:
            raise SystemExit(f"Stale release copy in {target.relative_to(ROOT)}: {phrase!r}")

print("OOLITA 2026–27 release calendar validated successfully.")
