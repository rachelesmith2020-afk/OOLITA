#!/usr/bin/env python3
"""OOLITA growth layer: clarify the practice, add Cabo de Gata/About/Work pages,
and prepare product-interest CTAs without inventing prices or checkout.

Runs after apply_direction_v3.py. Idempotent: a rebuilt site may already contain
some or all of these changes.
"""
from pathlib import Path
from urllib.parse import quote
import re
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
EMAIL = "oolita@tutamail.com"


def read(path):
    p = ROOT / path
    if not p.is_file():
        raise SystemExit(f"Missing page: {path}")
    return p, p.read_text(encoding="utf-8")


def write(path, text):
    p = ROOT / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def replace_once(path, old, new, already=None):
    p, s = read(path)
    marker = already or new
    markers = marker if isinstance(marker, (tuple, list)) else (marker,)
    matched = next((item for item in markers if item and item in s), None)
    if matched:
        print(f"growth already present {path}: {matched[:70]!r}")
        return
    if old not in s:
        raise SystemExit(f"Growth source text missing in {path}: {old[:120]!r}")
    p.write_text(s.replace(old, new, 1), encoding="utf-8")
    print(f"growth patched {path}: {old[:70]!r}")


def regex_once(path, pattern, replacement, marker):
    p, s = read(path)
    if marker in s:
        print(f"growth already present {path}: {marker[:70]!r}")
        return
    ns, n = re.subn(pattern, replacement, s, count=1, flags=re.S)
    if n != 1:
        raise SystemExit(f"Growth regex failed in {path}: matches={n}; {pattern[:120]!r}")
    p.write_text(ns, encoding="utf-8")
    print(f"growth patched {path}: {marker[:70]!r}")


def mailto(subject, body):
    return f"mailto:{EMAIL}?subject={quote(subject)}&body={quote(body)}"


# 1) One-sentence definition near the top of each homepage.
regex_once(
    "index.html",
    r'(<p class="glosa">(?=[\s\S]{0,800}Un libro y un laberinto caminable)[\s\S]*?</p>)',
    r'\1<p class="parr definicion">OOLITA es un proyecto editorial y de trabajo de campo arraigado en Los Escullos, Cabo de Gata.</p>',
    "OOLITA es un proyecto editorial y de trabajo de campo arraigado en Los Escullos, Cabo de Gata.",
)
regex_once(
    "en/index.html",
    r'(<p class="glosa">(?=[\s\S]{0,800}A book and a walkable labyrinth)[\s\S]*?</p>)',
    r'\1<p class="parr definicion">OOLITA is a place-based publishing and fieldwork project rooted in Los Escullos, Cabo de Gata.</p>',
    "OOLITA is a place-based publishing and fieldwork project rooted in Los Escullos, Cabo de Gata.",
)

# 2) Cabo de Gata becomes a real destination, not only an on-page anchor.
replace_once(
    "index.html",
    '<a class="pilar c" href="#cabo-de-gata"><span class="n">03</span><h3>Cabo de Gata</h3>',
    '<a class="pilar c" href="/cabo-de-gata/"><span class="n">03</span><h3>Cabo de Gata</h3>',
    'href="/cabo-de-gata/"><span class="n">03</span><h3>Cabo de Gata</h3>',
)
replace_once(
    "en/index.html",
    '<a class="pilar c" href="#cabo-de-gata"><span class="n">03</span><h3>Cabo de Gata</h3>',
    '<a class="pilar c" href="/en/cabo-de-gata/"><span class="n">03</span><h3>Cabo de Gata</h3>',
    'href="/en/cabo-de-gata/"><span class="n">03</span><h3>Cabo de Gata</h3>',
)

# 3) Future directions are explicitly exploratory until agreements exist.
replace_once(
    "index.html",
    'Vendrán cuadernos para recorrer el territorio en familia, ensayos con color natural y trabajo con artesanos locales en torno a saberes materiales como la fibra de pita.',
    'Entre las líneas en desarrollo hay cuadernos para recorrer el territorio en familia, ensayos con color natural y posibles colaboraciones con artesanos locales en torno a saberes materiales como la fibra de pita.',
    (
        'Entre las líneas en desarrollo hay cuadernos para recorrer el territorio en familia',
        'Alrededor de ese camino desarrolla publicaciones de campo, ediciones textiles y colaboraciones arraigadas en Cabo de Gata.',
    ),
)
replace_once(
    "en/index.html",
    'Next will come field books for family visits, experiments with natural colour, and work with local makers around material traditions such as pita fibre.',
    'Directions in development include field books for family visits, experiments with natural colour, and possible collaborations with local makers around material traditions such as pita fibre.',
    (
        'Directions in development include field books for family visits',
        'Around that path it is developing field publications, textile editions and collaborations rooted in Cabo de Gata.',
    ),
)
replace_once(
    "ediciones/camiseta/index.html",
    'Las futuras ediciones numeradas explorarán imágenes de Hallazgo, color natural y colaboraciones arraigadas en los materiales y saberes artesanos de Cabo de Gata.',
    'Las futuras ediciones numeradas podrán explorar imágenes de Hallazgo, color natural y colaboraciones arraigadas en los materiales y saberes artesanos de Cabo de Gata, cuando existan los acuerdos adecuados.',
    'cuando existan los acuerdos adecuados',
)
replace_once(
    "en/editions/t-shirt/index.html",
    'Future numbered editions will explore images from Hallazgo, natural colour and collaborations rooted in the materials and craft knowledge of Cabo de Gata.',
    'Future numbered editions may explore images from Hallazgo, natural colour and collaborations rooted in the materials and craft knowledge of Cabo de Gata, where the right agreements exist.',
    'where the right agreements exist',
)

# 4) Explain the free encounter / paid editions model on Editions.
regex_once(
    "ediciones/index.html",
    r'(<p class="glosa">El libro y la camiseta son las primeras ediciones de OOLITA\.[\s\S]*?</p>)',
    r'\1<p class="parr"><strong>El laberinto no tiene entrada ni reserva, y el mundo digital será gratuito. Las ediciones son la parte que puedes conservar.</strong></p>',
    "Las ediciones son la parte que puedes conservar.",
)
regex_once(
    "en/editions/index.html",
    r'(<p class="glosa">The book and T-shirt are the first OOLITA editions\.[\s\S]*?</p>)',
    r'\1<p class="parr"><strong>There is no ticket or booking for the labyrinth, and the digital world will be free. The editions are the part you can keep.</strong></p>',
    "The editions are the part you can keep.",
)

# 5) Field-book concept appears as a concrete work in development.
field_es = f'''<section class="tramo env" id="cuaderno-campo"><span class="rot">En desarrollo</span><h2 class="grande">Cuaderno de campo · Cabo de Gata.</h2><p class="glosa">Una publicación bilingüe para niños y familias: observar, dibujar, escuchar y registrar sin recoger ni alterar nada.</p><p class="parr">Puede crecer hacia geología, viento y sombra, agua, salinas y aves, Posidonia, color, materiales locales y ejercicios de atención. No es una guía para coleccionar cosas: lo encontrado se mira y se deja donde pertenece.</p><a class="fila" data-oolita-event="field-book-interest" href="{mailto('OOLITA · cuaderno de campo', 'Quiero que me avises cuando haya noticias del cuaderno de campo de Cabo de Gata.')}" rel="nofollow"><span class="n">→</span><span class="nom">Avísame cuando avance</span><span class="glo">Por ahora, por correo · {EMAIL}</span></a></section>'''
field_en = f'''<section class="tramo env" id="field-book"><span class="rot">In development</span><h2 class="grande">Cabo de Gata field book.</h2><p class="glosa">A bilingual publication for children and families: observe, draw, listen and record without collecting or disturbing anything.</p><p class="parr">It may grow across geology, wind and shadow, water, saltpans and birds, Posidonia, colour, local materials and exercises in attention. It is not a guide to collecting things: what is found is observed and left where it belongs.</p><a class="fila" data-oolita-event="field-book-interest" href="{mailto('OOLITA · Cabo de Gata field book', 'Please let me know when there is news about the Cabo de Gata field book.')}" rel="nofollow"><span class="n">→</span><span class="nom">Tell me when it develops</span><span class="glo">For now, by email · {EMAIL}</span></a></section>'''
for path, block, marker in [
    ("ediciones/index.html", field_es, 'id="cuaderno-campo"'),
    ("en/editions/index.html", field_en, 'id="field-book"'),
]:
    p, s = read(path)
    if marker not in s:
        if "</main>" not in s:
            raise SystemExit(f"No </main> in {path}")
        p.write_text(s.replace("</main>", block + "\n</main>", 1), encoding="utf-8")
        print(f"growth added field-book block to {path}")

# 6) Product pages get pre-sale CTAs and future checkout hooks, without invented prices.
def add_product_cta(path, marker, block):
    p, s = read(path)
    if marker in s:
        print(f"growth already has product CTA {path}")
        return
    if "</main>" not in s:
        raise SystemExit(f"No </main> in {path}")
    p.write_text(s.replace("</main>", block + "\n</main>", 1), encoding="utf-8")

book_es = f'''<section class="tramo" id="comprar"><span class="rot">31.01.27</span><h2 class="grande">El papel es para quedárselo.</h2><p class="parr">Precio por anunciar antes de la salida. La venta todavía no está abierta.</p><!-- CHECKOUT book: replace mailto href with commerce URL when connected --><a class="fila" data-checkout="book" data-oolita-event="book-interest" href="{mailto('OOLITA · reservar el libro', 'Quiero que me avises cuando pueda comprar el libro OOLITA.')}" rel="nofollow"><span class="n">→</span><span class="nom">Avísame cuando pueda comprarlo</span><span class="glo">Libro bilingüe · 48 páginas · tapa dura</span></a></section>'''
book_en = f'''<section class="tramo" id="buy"><span class="rot">31.01.27</span><h2 class="grande">Paper is for keeping.</h2><p class="parr">Price will be announced before release. Sales are not open yet.</p><!-- CHECKOUT book: replace mailto href with commerce URL when connected --><a class="fila" data-checkout="book" data-oolita-event="book-interest" href="{mailto('OOLITA · book purchase', 'Please let me know when I can buy the OOLITA book.')}" rel="nofollow"><span class="n">→</span><span class="nom">Tell me when I can buy it</span><span class="glo">Bilingual book · 48 pages · hardcover</span></a></section>'''
tee_es = f'''<section class="tramo" id="comprar"><span class="rot">28.03.27</span><h2 class="grande">Primera edición textil.</h2><p class="parr">Precio por anunciar antes de la salida. La venta todavía no está abierta.</p><!-- CHECKOUT textile: replace mailto href with commerce URL when connected --><a class="fila" data-checkout="textile-01" data-oolita-event="textile-interest" href="{mailto('OOLITA · primera edición textil', 'Quiero que me avises cuando pueda comprar la primera edición textil de OOLITA.')}" rel="nofollow"><span class="n">→</span><span class="nom">Avísame cuando pueda comprarla</span><span class="glo">Primera edición textil · 28.03.27</span></a></section>'''
tee_en = f'''<section class="tramo" id="buy"><span class="rot">28.03.27</span><h2 class="grande">The first textile edition.</h2><p class="parr">Price will be announced before release. Sales are not open yet.</p><!-- CHECKOUT textile: replace mailto href with commerce URL when connected --><a class="fila" data-checkout="textile-01" data-oolita-event="textile-interest" href="{mailto('OOLITA · first textile edition', 'Please let me know when I can buy the first OOLITA textile edition.')}" rel="nofollow"><span class="n">→</span><span class="nom">Tell me when I can buy it</span><span class="glo">First textile edition · 28.03.27</span></a></section>'''
add_product_cta("ediciones/libro/index.html", 'data-checkout="book"', book_es)
add_product_cta("en/editions/book/index.html", 'data-checkout="book"', book_en)
add_product_cta("ediciones/camiseta/index.html", 'data-checkout="textile-01"', tee_es)
add_product_cta("en/editions/t-shirt/index.html", 'data-checkout="textile-01"', tee_en)

# 7) Posters are explicitly an archive; current access information lives elsewhere.
for path, needle, note, marker in [
    ("carteles/index.html", "Con estos nueve carteles tipográficos abrió", '<p class="parr"><strong>Archivo:</strong> estos carteles documentan la campaña de apertura de 2026 y no se reescriben. Para información actual sobre la visita, consulta <a href="/laberinto/">El laberinto</a>.</p>', "estos carteles documentan la campaña de apertura de 2026"),
    ("en/posters/index.html", "These nine typographic posters opened", '<p class="parr"><strong>Archive:</strong> these posters document the 2026 opening campaign and are not rewritten. For current visitor information, see <a href="/en/labyrinth/">The labyrinth</a>.</p>', "these posters document the 2026 opening campaign"),
]:
    p, s = read(path)
    if marker not in s:
        m = re.search(r'(<p class="glosa">(?=[\s\S]{0,900}' + re.escape(needle) + r')[\s\S]*?</p>)', s, flags=re.S)
        if not m:
            # fall back to the first paragraph containing the opening sentence
            m = re.search(r'(<p[^>]*>[^<]*' + re.escape(needle) + r'[\s\S]*?</p>)', s, flags=re.S)
        if not m:
            raise SystemExit(f"Could not place archive note in {path}")
        s = s[:m.end()] + note + s[m.end():]
        p.write_text(s, encoding="utf-8")
        print(f"growth added archive note to {path}")

# 8) Build dedicated pages from the existing visual shell.
def make_page(source, dest, *, title, desc, canonical, alt_es, alt_en, old_counterpart, new_counterpart, main_html, replace_labels=()):
    srcp, s = read(source)
    # Remove source-specific structured data rather than carrying incorrect schema.
    s = re.sub(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>[\s\S]*?</script>', '', s, flags=re.I)
    # The visual shell comes from the ooid article. Replace every inherited
    # discovery/social field so generated pages never identify themselves as
    # that source article when shared or crawled.
    s = re.sub(r'<meta\s+property=["\']article:[^>]+>\s*', '', s, flags=re.I)
    s = re.sub(r'<title>[\s\S]*?</title>', f'<title>{title}</title>', s, count=1, flags=re.I)
    if re.search(r'<meta\s+name=["\']description["\'][^>]*>', s, flags=re.I):
        s = re.sub(r'<meta\s+name=["\']description["\'][^>]*>', f'<meta name="description" content="{desc}">', s, count=1, flags=re.I)
    else:
        s = s.replace('</head>', f'<meta name="description" content="{desc}">\n</head>', 1)
    s = re.sub(r'<link\s+rel=["\']canonical["\'][^>]*>', f'<link rel="canonical" href="{canonical}">', s, count=1, flags=re.I)
    s = re.sub(r'<link\s+rel=["\']alternate["\'][^>]*hreflang=[^>]+>\s*', '', s, flags=re.I)
    canon_tag = f'<link rel="canonical" href="{canonical}">'
    alternates = f'\n<link rel="alternate" hreflang="es" href="{alt_es}">\n<link rel="alternate" hreflang="en" href="{alt_en}">\n<link rel="alternate" hreflang="x-default" href="{alt_es}">'
    if canon_tag in s:
        s = s.replace(canon_tag, canon_tag + alternates, 1)

    def set_meta(attr, key, value):
        nonlocal s
        pattern = rf'<meta\s+{re.escape(attr)}=["\']{re.escape(key)}["\'][^>]*>'
        tag = f'<meta {attr}="{key}" content="{value}">'
        if re.search(pattern, s, flags=re.I):
            s = re.sub(pattern, tag, s, count=1, flags=re.I)
        elif '</head>' in s:
            s = s.replace('</head>', tag + '\n</head>', 1)
        else:
            raise SystemExit(f"Missing </head> while setting {key} in {dest}")

    social_alt = "OOLITA — un proyecto de Raquel Costantini en Cabo de Gata"
    if "/en/" in canonical:
        social_alt = "OOLITA — a project by Raquel Costantini in Cabo de Gata"
    for attr, key, value in [
        ("property", "og:type", "website"),
        ("property", "og:title", title),
        ("property", "og:description", desc),
        ("property", "og:url", canonical),
        ("property", "og:image", "https://oolita.es/og.png"),
        ("property", "og:image:secure_url", "https://oolita.es/og.png"),
        ("property", "og:image:alt", social_alt),
        ("name", "twitter:title", title),
        ("name", "twitter:description", desc),
        ("name", "twitter:image", "https://oolita.es/og.png"),
        ("name", "twitter:image:alt", social_alt),
    ]:
        set_meta(attr, key, value)
    s = s.replace(old_counterpart, new_counterpart)
    for old, new in replace_labels:
        s = s.replace(old, new)
    ns, n = re.subn(r'(<main\b[^>]*>)[\s\S]*?(</main>)', lambda m: m.group(1) + '\n' + main_html + '\n' + m.group(2), s, count=1, flags=re.I)
    if n != 1:
        raise SystemExit(f"Could not replace <main> in shell {source} for {dest}")
    write(dest, ns)
    print(f"growth generated {dest}")

cabo_es = f'''<section class="hero"><span class="rot">Cabo de Gata</span><h1 class="grande">Mirar de cerca.</h1><p class="lema">Un territorio, muchas formas de <em>atender</em>.</p><p class="lema-en" lang="en">Look closely</p><p class="glosa">OOLITA empieza con un solo laberinto en Los Escullos. Alrededor de ese camino crece una práctica editorial y de trabajo de campo que mira Cabo de Gata a través del arte, la observación, los materiales y ediciones hechas con cuidado.</p></section><section class="tramo"><span class="rot">Observar</span><h2 class="grande">Observar sin recoger ni alterar nada.</h2><p class="parr">Publicaciones de campo para niños, familias y visitantes: geología, viento, sombra, agua, salinas, aves, Posidonia, color y tiempo. Dibujar, escuchar, medir, anotar y fotografiar sin llevarse nada.</p><a class="fila" href="/ediciones/#cuaderno-campo"><span class="n">01</span><span class="nom">Cuaderno de campo</span><span class="glo">Bilingüe · en desarrollo</span></a></section><section class="tramo env"><span class="rot">Hacer</span><h2 class="grande">Materiales con procedencia.</h2><p class="parr">Las ediciones textiles y los ensayos con color natural se desarrollarán despacio. Las colaboraciones con artesanos o productores locales sólo se nombrarán cuando exista un acuerdo real, y cada edición contará quién la hizo, dónde, con qué materiales y en qué cantidad.</p></section><section class="tramo"><span class="rot">Cuidar</span><h2 class="grande">Hallado, no tomado.</h2><p class="parr">OOLITA no propone convertir el paisaje en recuerdo. La regla es observar sin extraer: seguir los caminos, reducir ruido y residuos, respetar la vida silvestre y dejar cada cosa donde pertenece.</p></section><section class="tramo env"><span class="rot">Conectar</span><h2 class="grande">Relaciones reales, no logotipos.</h2><p class="parr">Con el tiempo, OOLITA podrá trabajar con librerías, alojamientos, educadores, organizaciones culturales y artesanos del territorio. Ninguna organización se presenta como socia hasta que exista un acuerdo.</p><a class="fila" href="/colaborar/"><span class="n">→</span><span class="nom">Trabajar con OOLITA</span><span class="glo">Librerías · educación · cultura · materiales</span></a></section>'''
cabo_en = f'''<section class="hero"><span class="rot">Cabo de Gata</span><h1 class="grande">Look closely.</h1><p class="lema">One territory, many ways of <em>paying attention</em>.</p><p class="lema-en" lang="es">Mirar de cerca</p><p class="glosa">OOLITA begins with one labyrinth at Los Escullos. Around that path, a publishing and fieldwork practice is growing: looking at Cabo de Gata through art, observation, materials and carefully made editions.</p></section><section class="tramo"><span class="rot">Observe</span><h2 class="grande">Observe without collecting or disturbing anything.</h2><p class="parr">Field publications for children, families and visitors: geology, wind, shadow, water, saltpans, birds, Posidonia, colour and time. Draw, listen, measure, record and photograph without taking anything away.</p><a class="fila" href="/en/editions/#field-book"><span class="n">01</span><span class="nom">Cabo de Gata field book</span><span class="glo">Bilingual · in development</span></a></section><section class="tramo env"><span class="rot">Make</span><h2 class="grande">Materials with provenance.</h2><p class="parr">Textile editions and experiments with natural colour will develop slowly. Collaborations with local makers or producers will only be named when a real agreement exists, and every edition will state who made it, where, with what materials and in what quantity.</p></section><section class="tramo"><span class="rot">Care</span><h2 class="grande">Found, not taken.</h2><p class="parr">OOLITA does not propose turning the landscape into a souvenir. The rule is to observe without extracting: stay on paths, reduce noise and waste, respect wildlife and leave each thing where it belongs.</p></section><section class="tramo env"><span class="rot">Connect</span><h2 class="grande">Real relationships, not logos.</h2><p class="parr">Over time, OOLITA may work with bookshops, accommodation, educators, cultural organisations and makers in the territory. No organisation is presented as a partner until an agreement exists.</p><a class="fila" href="/en/work-with-oolita/"><span class="n">→</span><span class="nom">Work with OOLITA</span><span class="glo">Bookshops · education · culture · materials</span></a></section>'''
about_es = f'''<section class="hero"><span class="rot">Sobre OOLITA</span><h1 class="grande">Un camino, un lugar, una práctica.</h1><p class="glosa">OOLITA nace de un laberinto de piedra colocado a mano por Raquel Costantini en Los Escullos en septiembre de 2021.</p></section><section class="tramo"><span class="rot">Procedencia</span><h2 class="grande">Piedra, papel y código.</h2><p class="parr">La piedra es el laberinto original. El papel es la fábula bilingüe que recorre el mismo camino. El código es el mundo 3D que permitirá caminarlo desde el navegador. Ninguno sustituye al otro.</p><p class="parr">El nombre viene del oolito: una roca hecha de pequeños granos que crecen por capas alrededor de un centro. Esa forma — capas, centro, tiempo — conecta la geología de Los Escullos con el dibujo del laberinto.</p></section><section class="tramo env"><span class="rot">Raquel Costantini</span><h2 class="grande">Hallazgo y OOLITA.</h2><p class="parr">OOLITA forma parte de una práctica artística más amplia de Raquel Costantini. Hallazgo trabaja con observación, registro, objetos encontrados y paisaje. OOLITA toma esa atención y la convierte en camino, publicación, edición y trabajo de campo.</p><a class="fila" href="https://hallazgo.my.canva.site/hallazgo"><span class="n">↗</span><span class="nom">Hallazgo</span><span class="glo">Obra de Raquel Costantini</span></a></section><section class="tramo"><span class="rot">Contacto</span><h2 class="grande">Escribir.</h2><a class="fila" href="mailto:{EMAIL}"><span class="n">→</span><span class="nom">{EMAIL}</span><span class="glo">OOLITA · Los Escullos · Cabo de Gata</span></a></section>'''
about_en = f'''<section class="hero"><span class="rot">About OOLITA</span><h1 class="grande">One path, one place, one practice.</h1><p class="glosa">OOLITA begins with a stone labyrinth laid by hand by Raquel Costantini at Los Escullos in September 2021.</p></section><section class="tramo"><span class="rot">Provenance</span><h2 class="grande">Stone, paper and code.</h2><p class="parr">Stone is the original labyrinth. Paper is the bilingual fable that follows the same path. Code is the 3D world that will make it walkable in the browser. None replaces the others.</p><p class="parr">The name comes from oolite: rock made from tiny grains that grow in layers around a centre. That form — layers, centre, time — connects the geology of Los Escullos with the drawing of the labyrinth.</p></section><section class="tramo env"><span class="rot">Raquel Costantini</span><h2 class="grande">Hallazgo and OOLITA.</h2><p class="parr">OOLITA sits within Raquel Costantini's wider artistic practice. Hallazgo works with observation, recording, found objects and landscape. OOLITA turns that attention into path, publication, edition and fieldwork.</p><a class="fila" href="https://hallazgo.my.canva.site/hallazgo"><span class="n">↗</span><span class="nom">Hallazgo</span><span class="glo">Work by Raquel Costantini</span></a></section><section class="tramo"><span class="rot">Contact</span><h2 class="grande">Write.</h2><a class="fila" href="mailto:{EMAIL}"><span class="n">→</span><span class="nom">{EMAIL}</span><span class="glo">OOLITA · Los Escullos · Cabo de Gata</span></a></section>'''
work_es = f'''<section class="hero"><span class="rot">Colaborar</span><h1 class="grande">Trabajar con OOLITA.</h1><p class="glosa">Para librerías, alojamientos, educadores, organizaciones culturales y artesanos interesados en ediciones o proyectos de campo.</p></section><section class="tramo"><span class="rot">Qué puede tener sentido</span><h2 class="grande">Ediciones, educación, materiales.</h2><p class="parr">Distribución de publicaciones, encargos editoriales o educativos, actividades de observación y colaboraciones materiales de pequeña escala. Cada relación se define antes de nombrarla públicamente.</p><p class="parr">OOLITA no ofrece una franquicia de laberintos. El laberinto de Los Escullos sigue siendo uno. Lo que puede crecer es la relación editorial con el territorio.</p></section><section class="tramo env"><span class="rot">Contacto</span><h2 class="grande">Cuéntame qué tienes en mente.</h2><a class="fila" data-oolita-event="partner-contact" href="{mailto('OOLITA · colaboración', 'Hola. Me gustaría hablar sobre una posible colaboración con OOLITA.')}" rel="nofollow"><span class="n">→</span><span class="nom">Escribir sobre una colaboración</span><span class="glo">{EMAIL}</span></a></section>'''
work_en = f'''<section class="hero"><span class="rot">Collaborate</span><h1 class="grande">Work with OOLITA.</h1><p class="glosa">For bookshops, accommodation, educators, cultural organisations and makers interested in editions or field projects.</p></section><section class="tramo"><span class="rot">What may fit</span><h2 class="grande">Editions, education, materials.</h2><p class="parr">Publication distribution, editorial or educational commissions, observation-based activities and small-scale material collaborations. Each relationship is agreed before it is named publicly.</p><p class="parr">OOLITA does not offer a labyrinth franchise. The Los Escullos labyrinth remains one. What can grow is the editorial relationship with the territory.</p></section><section class="tramo env"><span class="rot">Contact</span><h2 class="grande">Tell me what you have in mind.</h2><a class="fila" data-oolita-event="partner-contact" href="{mailto('OOLITA · collaboration', 'Hello. I would like to discuss a possible collaboration with OOLITA.')}" rel="nofollow"><span class="n">→</span><span class="nom">Write about a collaboration</span><span class="glo">{EMAIL}</span></a></section>'''

make_page("que-es-un-oolito/index.html", "cabo-de-gata/index.html", title="Cabo de Gata · OOLITA", desc="OOLITA en Cabo de Gata: publicaciones de campo, materiales, cuidado del paisaje y colaboraciones que nacen de un solo laberinto en Los Escullos.", canonical="https://oolita.es/cabo-de-gata/", alt_es="https://oolita.es/cabo-de-gata/", alt_en="https://oolita.es/en/cabo-de-gata/", old_counterpart="/en/what-is-an-ooid/", new_counterpart="/en/cabo-de-gata/", main_html=cabo_es, replace_labels=(("Qué es un oolito", "Cabo de Gata"),))
make_page("en/what-is-an-ooid/index.html", "en/cabo-de-gata/index.html", title="Cabo de Gata · OOLITA", desc="OOLITA in Cabo de Gata: field publications, materials, care for the landscape and collaborations growing from one labyrinth at Los Escullos.", canonical="https://oolita.es/en/cabo-de-gata/", alt_es="https://oolita.es/cabo-de-gata/", alt_en="https://oolita.es/en/cabo-de-gata/", old_counterpart="/que-es-un-oolito/", new_counterpart="/cabo-de-gata/", main_html=cabo_en, replace_labels=(("What is an ooid", "Cabo de Gata"),))
make_page("que-es-un-oolito/index.html", "sobre-oolita/index.html", title="Sobre OOLITA · Raquel Costantini", desc="La procedencia de OOLITA: el laberinto de Los Escullos, piedra, papel y código, y la práctica de Raquel Costantini en Cabo de Gata.", canonical="https://oolita.es/sobre-oolita/", alt_es="https://oolita.es/sobre-oolita/", alt_en="https://oolita.es/en/about/", old_counterpart="/en/what-is-an-ooid/", new_counterpart="/en/about/", main_html=about_es, replace_labels=(("Qué es un oolito", "Sobre OOLITA"),))
make_page("en/what-is-an-ooid/index.html", "en/about/index.html", title="About OOLITA · Raquel Costantini", desc="The provenance of OOLITA: the Los Escullos labyrinth, stone, paper and code, and Raquel Costantini's practice in Cabo de Gata.", canonical="https://oolita.es/en/about/", alt_es="https://oolita.es/sobre-oolita/", alt_en="https://oolita.es/en/about/", old_counterpart="/que-es-un-oolito/", new_counterpart="/sobre-oolita/", main_html=about_en, replace_labels=(("What is an ooid", "About OOLITA"),))
make_page("que-es-un-oolito/index.html", "colaborar/index.html", title="Colaborar con OOLITA · Cabo de Gata", desc="Información para librerías, educadores, organizaciones culturales, alojamientos y artesanos interesados en trabajar con OOLITA.", canonical="https://oolita.es/colaborar/", alt_es="https://oolita.es/colaborar/", alt_en="https://oolita.es/en/work-with-oolita/", old_counterpart="/en/what-is-an-ooid/", new_counterpart="/en/work-with-oolita/", main_html=work_es, replace_labels=(("Qué es un oolito", "Colaborar"),))
make_page("en/what-is-an-ooid/index.html", "en/work-with-oolita/index.html", title="Work with OOLITA · Cabo de Gata", desc="For bookshops, educators, cultural organisations, accommodation and makers interested in working with OOLITA.", canonical="https://oolita.es/en/work-with-oolita/", alt_es="https://oolita.es/colaborar/", alt_en="https://oolita.es/en/work-with-oolita/", old_counterpart="/que-es-un-oolito/", new_counterpart="/colaborar/", main_html=work_en, replace_labels=(("What is an ooid", "Work with OOLITA"),))

# 9) Add About / collaboration routes to the homepage link index.
for path, contact_marker, addition, marker in [
    ("index.html", '<!--email_off--><a class="fila" href="mailto:oolita@tutamail.com">', '  <a class="fila" href="/sobre-oolita/"><span class="n">12</span><span class="nom">Sobre OOLITA</span><span class="glo">Raquel Costantini · procedencia y práctica</span></a>\n  <a class="fila" href="/colaborar/"><span class="n">13</span><span class="nom">Colaborar</span><span class="glo">Librerías · educación · cultura · materiales</span></a>\n  ', 'href="/sobre-oolita/"'),
    ("en/index.html", '<!--email_off--><a class="fila" href="mailto:oolita@tutamail.com">', '  <a class="fila" href="/en/about/"><span class="n">12</span><span class="nom">About OOLITA</span><span class="glo">Raquel Costantini · provenance and practice</span></a>\n  <a class="fila" href="/en/work-with-oolita/"><span class="n">13</span><span class="nom">Work with OOLITA</span><span class="glo">Bookshops · education · culture · materials</span></a>\n  ', 'href="/en/about/"'),
]:
    p, s = read(path)
    if marker not in s:
        if contact_marker not in s:
            raise SystemExit(f"Contact link marker missing in {path}")
        p.write_text(s.replace(contact_marker, addition + contact_marker, 1), encoding="utf-8")
        s = p.read_text(encoding="utf-8")

    old_contact = contact_marker + '<span class="n">12</span>'
    new_contact = contact_marker + '<span class="n">14</span>'
    plain_contact_14 = '<a class="fila" href="mailto:oolita@tutamail.com"><span class="n">14</span>'
    if old_contact in s:
        p.write_text(s.replace(old_contact, new_contact, 1), encoding="utf-8")
    elif new_contact not in s and plain_contact_14 not in s:
        raise SystemExit(f"Could not assign contact number 14 in {path}")

# About and collaboration now occupy rows 12 and 13, so Contact is row 14.
for path, old, new in [
    ("index.html", '<span class="n">12</span><span class="nom">Contacto</span>', '<span class="n">14</span><span class="nom">Contacto</span>'),
    ("en/index.html", '<span class="n">12</span><span class="nom">Contact</span>', '<span class="n">14</span><span class="nom">Contact</span>'),
]:
    p, s = read(path)
    if old in s:
        p.write_text(s.replace(old, new, 1), encoding="utf-8")
    elif new not in s:
        raise SystemExit(f"Contact row could not be renumbered in {path}")

error_page = next((path for path in ("404.html", "404/index.html") if (ROOT / path).is_file()), None)
if error_page:
    p, s = read(error_page)
    old = '<span class="n">12</span><span class="nom">Contacto</span>'
    new = '<span class="n">14</span><span class="nom">Contacto</span>'
    if old in s:
        p.write_text(s.replace(old, new, 1), encoding="utf-8")
    elif new not in s:
        raise SystemExit(f"Contact row could not be renumbered in {error_page}")

# 10) Add new URLs to sitemap so search engines can discover them.
p, sm = read("sitemap.xml")
new_urls = [
    "https://oolita.es/cabo-de-gata/", "https://oolita.es/en/cabo-de-gata/",
    "https://oolita.es/sobre-oolita/", "https://oolita.es/en/about/",
    "https://oolita.es/colaborar/", "https://oolita.es/en/work-with-oolita/",
]
for url in new_urls:
    if url not in sm:
        entry = f"  <url><loc>{url}</loc><lastmod>2026-08-22</lastmod></url>\n"
        if "</urlset>" not in sm:
            raise SystemExit("Unexpected sitemap format")
        sm = sm.replace("</urlset>", entry + "</urlset>", 1)
p.write_text(sm, encoding="utf-8")

# Final invariants.
required = {
    "index.html": ["place-based" if False else "proyecto editorial y de trabajo de campo", 'href="/cabo-de-gata/"', '<span class="n">14</span><span class="nom">Contacto</span>'],
    "en/index.html": ["place-based publishing and fieldwork project", 'href="/en/cabo-de-gata/"', '<span class="n">14</span><span class="nom">Contact</span>'],
    "ediciones/index.html": ["Las ediciones son la parte que puedes conservar.", 'id="cuaderno-campo"'],
    "en/editions/index.html": ["The editions are the part you can keep.", 'id="field-book"'],
    "ediciones/libro/index.html": ['data-checkout="book"', "Precio por anunciar"],
    "en/editions/book/index.html": ['data-checkout="book"', "Price will be announced"],
    "ediciones/camiseta/index.html": ['data-checkout="textile-01"', "Precio por anunciar"],
    "en/editions/t-shirt/index.html": ['data-checkout="textile-01"', "Price will be announced"],
    "cabo-de-gata/index.html": ["Observar sin recoger ni alterar nada.", "Hallado, no tomado", "Relaciones reales, no logotipos"],
    "en/cabo-de-gata/index.html": ["Observe without collecting or disturbing anything.", "Found, not taken", "Real relationships, not logos"],
    "sobre-oolita/index.html": ["Piedra, papel y código", "Raquel Costantini"],
    "en/about/index.html": ["Stone, paper and code", "Raquel Costantini"],
}
for path, forbidden in [
    ("cabo-de-gata/index.html", "Antes de recoger, mirar."),
    ("en/cabo-de-gata/index.html", "Look before collecting."),
]:
    _, generated = read(path)
    if forbidden in generated:
        raise SystemExit(f"Forbidden collection wording remains in {path}: {forbidden}")

for path, needles in required.items():
    _, s = read(path)
    for needle in needles:
        if needle not in s:
            raise SystemExit(f"Growth invariant missing in {path}: {needle}")
if error_page:
    _, s = read(error_page)
    if '<span class="n">14</span><span class="nom">Contacto</span>' not in s:
        raise SystemExit(f"Growth invariant missing in {error_page}: Contact row 14")

for path, canonical in {
    "cabo-de-gata/index.html": "https://oolita.es/cabo-de-gata/",
    "en/cabo-de-gata/index.html": "https://oolita.es/en/cabo-de-gata/",
    "sobre-oolita/index.html": "https://oolita.es/sobre-oolita/",
    "en/about/index.html": "https://oolita.es/en/about/",
    "colaborar/index.html": "https://oolita.es/colaborar/",
    "en/work-with-oolita/index.html": "https://oolita.es/en/work-with-oolita/",
}.items():
    _, s = read(path)
    for needle in [
        f'<meta property="og:url" content="{canonical}">',
        '<meta property="og:image" content="https://oolita.es/og.png">',
        '<link rel="alternate" hreflang="x-default"',
    ]:
        if needle not in s:
            raise SystemExit(f"Growth social invariant missing in {path}: {needle}")
    if "what-is-an-ooid" in re.search(r'<meta property="og:url" content="([^"]+)">', s).group(1):
        raise SystemExit(f"Inherited ooid social URL remains in {path}")

print("OOLITA growth layer validated successfully.")
