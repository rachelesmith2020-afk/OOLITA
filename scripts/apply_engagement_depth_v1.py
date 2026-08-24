#!/usr/bin/env python3
"""Add the next OOLITA engagement-depth and discovery improvements.

This deployment layer deepens the bilingual Cabo de Gata pages with approved
place facts and clear onward paths, adds contextual links to every published
Sunday, creates small and 700-pixel image variants for the Sunday sequence,
adds visual thumbnails to the archive, and publishes factual structured data
for the Cabo de Gata and About pages.
"""
from __future__ import annotations

import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET


ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
BASE = "https://oolita.es"
LASTMOD = "2026-08-24"
STYLE_ID = "oolita-engagement-depth-v1"

CHANGED_ROUTES = {
    "/cabo-de-gata/",
    "/en/cabo-de-gata/",
    "/sobre-oolita/",
    "/en/about/",
    "/domingos/",
    "/en/sundays/",
    "/domingos/01-el-doble/",
    "/en/sundays/01-the-double/",
    "/domingos/02-el-gato-de-verdad/",
    "/en/sundays/02-the-cat-for-real/",
    "/domingos/03-la-memoria-del-mar/",
    "/en/sundays/03-the-memory-of-the-sea/",
}

SUNDAYS = {
    1: {
        "es": "01-el-doble",
        "en": "01-the-double",
        "es_title": "El doble",
        "en_title": "The double",
        "date": "2026-08-09",
        "display_es": "09.08.26",
        "display_en": "9 Aug 26",
        "width": 417,
        "height": 518,
    },
    2: {
        "es": "02-el-gato-de-verdad",
        "en": "02-the-cat-for-real",
        "es_title": "El gato, de verdad",
        "en_title": "The cat, for real",
        "date": "2026-08-16",
        "display_es": "16.08.26",
        "display_en": "16 Aug 26",
        "width": 1440,
        "height": 1800,
    },
    3: {
        "es": "03-la-memoria-del-mar",
        "en": "03-the-memory-of-the-sea",
        "es_title": "La memoria del mar",
        "en_title": "The Memory of the Sea",
        "date": "2026-08-23",
        "display_es": "23.08.26",
        "display_en": "23 Aug 26",
        "width": 1080,
        "height": 1350,
    },
}


STYLE = r'''<style id="oolita-engagement-depth-v1">
/* A quiet factual bridge between the Cabo de Gata page and the rest of OOLITA. */
.oolita-place-facts{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:1px;margin:2rem 0;background:rgba(45,78,35,.28)}
.oolita-place-fact{display:flex;flex-direction:column;gap:.3rem;padding:1rem;background:#f1e7d4}
.oolita-place-fact .k{font-size:.67rem;letter-spacing:.1em;text-transform:uppercase}
.oolita-place-fact .v{font-size:clamp(1rem,1.4vw,1.2rem)}
.oolita-context-links{margin-top:1.4rem}
.oolita-context-links a{font-weight:600;text-underline-offset:.2em}

/* Archive thumbnails: an image now leads each published Sunday row. */
.sunday-archive-thumb{display:block;flex:0 0 clamp(3.75rem,7vw,5.75rem);width:clamp(3.75rem,7vw,5.75rem);aspect-ratio:4/5;overflow:hidden;background:rgba(45,78,35,.12)}
.sunday-archive-thumb picture,.sunday-archive-thumb img{display:block;width:100%;height:100%}
.sunday-archive-thumb img{object-fit:cover}
a.fila[data-sunday-archive-row]{align-items:center}
a.fila[data-sunday-archive-row] .cuerpo{min-width:0;flex:1}

/* Contextual links on each Sunday should read as a continuation, not an advert. */
.sunday-context-note{max-width:46rem}
.sunday-context-note p{margin-bottom:1rem}
.sunday-context-note a{text-underline-offset:.2em}
.sunday-context-more{display:flex;flex-wrap:wrap;gap:.65rem 1.15rem;font-size:.82rem}

@media(max-width:640px){
  .oolita-place-facts{grid-template-columns:1fr}
  .sunday-archive-thumb{flex-basis:3.75rem;width:3.75rem}
  a.fila[data-sunday-archive-row]{gap:.75rem!important}
}
</style>'''


CABO_BLOCKS = {
    "es": '''<section class="tramo env" data-place-depth>
<span class="rot">El lugar</span><h2 class="grande">Un territorio medido.</h2>
<p class="parr">El punto de partida está en Los Escullos, Níjar, Almería. El laberinto ocupa tres metros sobre la duna fósil de la Playa del Arco, en las coordenadas 36.7993, −2.0632. Fue colocado a mano en 2021 con calcarenita suelta, sin cortar, fijar ni excavar.</p>
<p class="parr">A 325 metros al norte, la Batería de San Felipe, de 1771, se levanta sobre la misma duna fósil. Entre la piedra, el castillo y la orilla se forma el territorio que OOLITA observa y vuelve a registrar.</p>
<div class="oolita-place-facts" aria-label="Datos del lugar"><span class="oolita-place-fact"><span class="k">Lugar</span><span class="v">Los Escullos · Níjar · Almería</span></span><span class="oolita-place-fact"><span class="k">Coordenadas</span><span class="v">36.7993, −2.0632</span></span><span class="oolita-place-fact"><span class="k">Laberinto</span><span class="v">Tres metros · piedra suelta · 2021</span></span><span class="oolita-place-fact"><span class="k">Terreno</span><span class="v">Duna fósil · Playa del Arco</span></span></div>
<p class="parr oolita-context-links"><a href="/laberinto/">Cómo encontrar y caminar el laberinto →</a> &nbsp; <a href="/que-es-un-oolito/">Cómo se formó esta piedra →</a></p>
</section>
<section class="tramo" data-material-paths>
<span class="rot">Piedra · papel · código</span><h2 class="grande">El lugar cambia de material.</h2>
<p class="parr">La piedra es el laberinto. El papel es la fábula bilingüe. El código es el mundo 3D levantado a partir del terreno real de Los Escullos. El mundo abre el 3 de enero de 2027 a las 00:00 CET, desde el navegador, sin descarga, cuenta ni pago.</p>
<a class="fila" href="/ediciones/"><span class="n">01</span><span class="nom">Ediciones</span><span class="glo">La fábula y las publicaciones de campo</span></a>
<a class="fila" href="/mundo-3d/"><span class="n">02</span><span class="nom">Mundo 3D</span><span class="glo">El mismo camino, hecho de luz</span></a>
<a class="fila" href="/domingos/"><span class="n">03</span><span class="nom">22 domingos</span><span class="glo">Una imagen por semana hasta la apertura</span></a>
</section>''',
    "en": '''<section class="tramo env" data-place-depth>
<span class="rot">The place</span><h2 class="grande">A measured territory.</h2>
<p class="parr">The starting point is Los Escullos, Níjar, Almería. The labyrinth occupies three metres on the Playa del Arco fossil dune, at 36.7993, −2.0632. It was laid by hand in 2021 with loose calcarenite: nothing cut, fixed or excavated.</p>
<p class="parr">Three hundred and twenty-five metres to the north, the Batería de San Felipe, built in 1771, stands on the same fossil dune. The stone, castle and shore form the territory OOLITA observes and records again.</p>
<div class="oolita-place-facts" aria-label="Place facts"><span class="oolita-place-fact"><span class="k">Place</span><span class="v">Los Escullos · Níjar · Almería</span></span><span class="oolita-place-fact"><span class="k">Coordinates</span><span class="v">36.7993, −2.0632</span></span><span class="oolita-place-fact"><span class="k">Labyrinth</span><span class="v">Three metres · loose stone · 2021</span></span><span class="oolita-place-fact"><span class="k">Ground</span><span class="v">Fossil dune · Playa del Arco</span></span></div>
<p class="parr oolita-context-links"><a href="/en/labyrinth/">How to find and walk the labyrinth →</a> &nbsp; <a href="/en/what-is-an-ooid/">How this stone was formed →</a></p>
</section>
<section class="tramo" data-material-paths>
<span class="rot">Stone · paper · code</span><h2 class="grande">The place changes material.</h2>
<p class="parr">Stone is the labyrinth. Paper is the bilingual fable. Code is the 3D world raised from the real terrain at Los Escullos. The world opens on 3 January 2027 at 00:00 CET, in the browser, with no download, account or payment.</p>
<a class="fila" href="/en/editions/"><span class="n">01</span><span class="nom">Editions</span><span class="glo">The fable and field publications</span></a>
<a class="fila" href="/en/3d-world/"><span class="n">02</span><span class="nom">3D world</span><span class="glo">The same path, made of light</span></a>
<a class="fila" href="/en/sundays/"><span class="n">03</span><span class="nom">22 Sundays</span><span class="glo">One image a week until the opening</span></a>
</section>''',
}


SUNDAY_CONTEXT = {
    ("es", 1): '''<section class="tramo sunday-context-note" data-sunday-context>
<span class="rot">Piedra y código</span><h2>El doble tiene un original.</h2>
<p class="parr">La imagen vuelve a levantar el trazado dentro de una pantalla. El punto de partida sigue siendo el <a href="/laberinto/">laberinto de piedra que se puede caminar en Los Escullos</a>.</p>
<p class="sunday-context-more"><a href="/cabo-de-gata/">El lugar: Cabo de Gata →</a><a href="/ediciones/">El camino sobre papel →</a></p>
</section>''',
    ("es", 2): '''<section class="tramo sunday-context-note" data-sunday-context>
<span class="rot">Papel y lugar</span><h2>El gato entra en el libro.</h2>
<p class="parr">Esta historia continúa en la <a href="/ediciones/">fábula bilingüe de OOLITA</a>: el mismo gato, el mismo camino, español e inglés en cada recorrido.</p>
<p class="sunday-context-more"><a href="/laberinto/">Caminar el laberinto →</a><a href="/cabo-de-gata/">Mirar Cabo de Gata de cerca →</a></p>
</section>''',
    ("es", 3): '''<section class="tramo sunday-context-note" data-sunday-context>
<span class="rot">Piedra que fue mar</span><h2>El nombre nace del lugar.</h2>
<p class="parr">La calcarenita oolítica enlaza el laberinto con la duna fósil. Sigue hacia <a href="/cabo-de-gata/">el territorio que OOLITA observa en Cabo de Gata</a>.</p>
<p class="sunday-context-more"><a href="/laberinto/">El laberinto de Los Escullos →</a><a href="/ediciones/">La piedra llevada al papel →</a></p>
</section>''',
    ("en", 1): '''<section class="tramo sunday-context-note" data-sunday-context>
<span class="rot">Stone and code</span><h2>The double has an original.</h2>
<p class="parr">The image raises the drawing again inside a screen. Its starting point remains <a href="/en/labyrinth/">the stone labyrinth you can walk at Los Escullos</a>.</p>
<p class="sunday-context-more"><a href="/en/cabo-de-gata/">The place: Cabo de Gata →</a><a href="/en/editions/">The path on paper →</a></p>
</section>''',
    ("en", 2): '''<section class="tramo sunday-context-note" data-sunday-context>
<span class="rot">Paper and place</span><h2>The cat enters the book.</h2>
<p class="parr">This story continues in <a href="/en/editions/">the bilingual OOLITA fable</a>: the same cat, the same path, Spanish and English together throughout.</p>
<p class="sunday-context-more"><a href="/en/labyrinth/">Walk the labyrinth →</a><a href="/en/cabo-de-gata/">Look closely at Cabo de Gata →</a></p>
</section>''',
    ("en", 3): '''<section class="tramo sunday-context-note" data-sunday-context>
<span class="rot">Stone that was sea</span><h2>The name begins in the place.</h2>
<p class="parr">Oolitic calcarenite joins the labyrinth to the fossil dune. Continue into <a href="/en/cabo-de-gata/">the territory OOLITA observes in Cabo de Gata</a>.</p>
<p class="sunday-context-more"><a href="/en/labyrinth/">The Los Escullos labyrinth →</a><a href="/en/editions/">The stone carried onto paper →</a></p>
</section>''',
}


def read(rel: str) -> tuple[Path, str]:
    target = ROOT / rel
    if not target.is_file():
        raise SystemExit(f"Missing engagement-depth page: {rel}")
    return target, target.read_text(encoding="utf-8")


def write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def inject_style(text: str) -> str:
    pattern = re.compile(
        rf'<style\s+id=["\']{re.escape(STYLE_ID)}["\'][^>]*>[\s\S]*?</style>',
        flags=re.I,
    )
    if pattern.search(text):
        return pattern.sub(STYLE, text, count=1)
    if "</head>" not in text:
        raise SystemExit("Missing </head> while adding engagement-depth style")
    return text.replace("</head>", STYLE + "\n</head>", 1)


def remove_marked_section(text: str, marker: str) -> str:
    return re.sub(
        rf'<section\b[^>]*\b{re.escape(marker)}\b[^>]*>[\s\S]*?</section>\s*',
        "",
        text,
        flags=re.I,
    )


def patch_cabo(rel: str, language: str) -> None:
    target, text = read(rel)
    text = remove_marked_section(text, "data-place-depth")
    text = remove_marked_section(text, "data-material-paths")
    hero = re.search(r'<section\b[^>]*class=["\'][^"\']*\bhero\b[^"\']*["\'][^>]*>[\s\S]*?</section>', text, flags=re.I)
    if not hero:
        raise SystemExit(f"Cabo de Gata hero missing in {rel}")
    text = text[:hero.end()] + CABO_BLOCKS[language] + text[hero.end():]
    write(target, inject_style(text))


def run_ffmpeg(args: list[str]) -> None:
    result = subprocess.run(args, capture_output=True, text=True)
    if result.returncode:
        message = (result.stderr or result.stdout).strip().splitlines()
        raise SystemExit(f"ffmpeg image build failed: {message[-1] if message else result.returncode}")


def make_variant(source: Path, target: Path, width: int) -> None:
    if target.is_file() and target.stat().st_size > 1_000:
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    common = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(source), "-vf", f"scale='min({width},iw)':-2", "-frames:v", "1"]
    if target.suffix == ".avif":
        common += ["-c:v", "libaom-av1", "-still-picture", "1", "-cpu-used", "6", "-crf", "35", "-pix_fmt", "yuv420p"]
    else:
        common += ["-q:v", "3"]
    run_ffmpeg(common + [str(target)])
    if not target.is_file() or target.stat().st_size < 1_000:
        raise SystemExit(f"Generated Sunday image is unexpectedly small: {target}")


def build_sunday_images() -> None:
    if not shutil.which("ffmpeg"):
        raise SystemExit("ffmpeg is required for responsive Sunday images")
    image_dir = ROOT / "domingos" / "img"
    for number, item in SUNDAYS.items():
        source = image_dir / f"{number:02d}.jpg"
        if not source.is_file():
            raise SystemExit(f"Missing Sunday source image: {source}")
        for ext in ("jpg", "avif"):
            make_variant(source, image_dir / f"{number:02d}-180.{ext}", 180)
        if item["width"] > 700:
            for ext in ("jpg", "avif"):
                make_variant(source, image_dir / f"{number:02d}-700.{ext}", 700)
        full_avif = image_dir / f"{number:02d}.avif"
        if not full_avif.is_file():
            make_variant(source, full_avif, item["width"])


def responsive_picture(number: int, alt: str, loading: str, priority: bool) -> str:
    item = SUNDAYS[number]
    full_width = item["width"]
    sizes = "(max-width: 760px) calc(100vw - 2rem), min(90vw, 980px)"
    if full_width > 700:
        avif_srcset = f'/domingos/img/{number:02d}-700.avif 700w, /domingos/img/{number:02d}.avif {full_width}w'
        jpg_srcset = f'/domingos/img/{number:02d}-700.jpg 700w, /domingos/img/{number:02d}.jpg {full_width}w'
    else:
        avif_srcset = f'/domingos/img/{number:02d}.avif {full_width}w'
        jpg_srcset = f'/domingos/img/{number:02d}.jpg {full_width}w'
    priority_attr = ' fetchpriority="high"' if priority else ""
    return (
        f'<picture data-sunday-responsive>'
        f'<source type="image/avif" srcset="{avif_srcset}" sizes="{sizes}">'
        f'<img src="/domingos/img/{number:02d}.jpg" srcset="{jpg_srcset}" sizes="{sizes}" '
        f'alt="{alt}" width="{item["width"]}" height="{item["height"]}" '
        f'loading="{loading}" decoding="async"{priority_attr}>'
        f'</picture>'
    )


def patch_detail_image(text: str, number: int) -> str:
    figure = re.search(r'<figure\b[^>]*class=["\'][^"\']*\blamina\b[^"\']*["\'][^>]*>[\s\S]*?</figure>', text, flags=re.I)
    if not figure:
        raise SystemExit(f"Sunday {number:02d} image figure missing")
    block = figure.group(0)
    image = re.search(r'<img\b[^>]*\bsrc=["\']/domingos/img/%02d\.jpg["\'][^>]*>' % number, block, flags=re.I)
    if not image:
        raise SystemExit(f"Sunday {number:02d} source image missing from figure")
    alt_match = re.search(r'\balt=["\']([^"\']*)["\']', image.group(0), flags=re.I)
    if not alt_match:
        raise SystemExit(f"Sunday {number:02d} image alt missing")
    alt = alt_match.group(1)
    picture = responsive_picture(number, alt, "eager", True)
    if re.search(r'<picture\b[^>]*>[\s\S]*?</picture>', block, flags=re.I):
        block = re.sub(r'<picture\b[^>]*>[\s\S]*?</picture>', picture, block, count=1, flags=re.I)
    else:
        block = block[:image.start()] + picture + block[image.end():]
    return text[:figure.start()] + block + text[figure.end():]


def patch_sunday_detail(rel: str, language: str, number: int) -> None:
    target, text = read(rel)
    text = remove_marked_section(text, "data-sunday-context")
    text = patch_detail_image(text, number)
    label = "Keep walking" if language == "en" else "Seguir el camino"
    onward = re.search(
        rf'<section\b[^>]*class=["\'][^"\']*\btramo\b[^"\']*["\'][^>]*>\s*<h2\b[^>]*class=["\'][^"\']*\brot\b[^"\']*["\'][^>]*>\s*{re.escape(label)}\s*</h2>',
        text,
        flags=re.I,
    )
    if not onward:
        raise SystemExit(f"Sunday onward section missing in {rel}")
    text = text[:onward.start()] + SUNDAY_CONTEXT[(language, number)] + "\n" + text[onward.start():]
    write(target, inject_style(text))


def thumbnail(number: int) -> str:
    item = SUNDAYS[number]
    height = round(180 * item["height"] / item["width"])
    return (
        '<span class="sunday-archive-thumb" aria-hidden="true"><picture>'
        f'<source type="image/avif" srcset="/domingos/img/{number:02d}-180.avif">'
        f'<img src="/domingos/img/{number:02d}-180.jpg" alt="" width="180" height="{height}" loading="lazy" decoding="async">'
        '</picture></span>'
    )


def archive_row(number: int, language: str) -> str:
    item = SUNDAYS[number]
    if language == "es":
        route = f'/domingos/{item["es"]}/'
        title = item["es_title"]
        other = item["en_title"]
        display = item["display_es"]
        other_lang = "en"
    else:
        route = f'/en/sundays/{item["en"]}/'
        title = item["en_title"]
        other = item["es_title"]
        display = item["display_en"]
        other_lang = "es"
    return (
        f'<a class="fila" href="{route}" data-sunday-archive-row="{number}">'
        f'{thumbnail(number)}<span class="num">{number:02d}</span>'
        f'<span class="cuerpo"><span class="nombre">{title}</span><span class="glo" lang="{other_lang}">{other}</span></span>'
        f'<time class="cuando" datetime="{item["date"]}">{display}</time><span class="flecha">→</span></a>'
    )


def patch_archive(rel: str, language: str) -> None:
    target, text = read(rel)
    for number, item in SUNDAYS.items():
        segment = "en/sundays" if language == "en" else "domingos"
        slug = item[language]
        row_pattern = rf'<a\b[^>]*href=["\']/{segment}/{re.escape(slug)}/["\'][^>]*>[\s\S]*?</a>'
        pending_pattern = rf'<div\b[^>]*class=["\'][^"\']*\bfila\b[^"\']*\bespera\b[^"\']*["\'][^>]*>[\s\S]*?<time\b[^>]*datetime=["\']{item["date"]}["\'][^>]*>[\s\S]*?</div>'
        row = archive_row(number, language)
        if re.search(row_pattern, text, flags=re.I):
            text = re.sub(row_pattern, row, text, count=1, flags=re.I)
        elif re.search(pending_pattern, text, flags=re.I):
            text = re.sub(pending_pattern, row, text, count=1, flags=re.I)
        else:
            raise SystemExit(f"Sunday {number:02d} archive row missing in {rel}")
    write(target, inject_style(text))


def schema_script(script_id: str, payload: dict) -> str:
    data = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    return f'<script id="{script_id}" type="application/ld+json">{data}</script>'


def upsert_schema(rel: str, script_id: str, payload: dict) -> None:
    target, text = read(rel)
    block = schema_script(script_id, payload)
    pattern = re.compile(
        rf'<script\b[^>]*id=["\']{re.escape(script_id)}["\'][^>]*>[\s\S]*?</script>',
        flags=re.I,
    )
    if pattern.search(text):
        text = pattern.sub(block, text, count=1)
    else:
        if "</head>" not in text:
            raise SystemExit(f"Missing </head> while adding structured data: {rel}")
        text = text.replace("</head>", block + "\n</head>", 1)
    write(target, text)


def add_structured_data() -> None:
    for language, rel, route in (
        ("es", "cabo-de-gata/index.html", "/cabo-de-gata/"),
        ("en", "en/cabo-de-gata/index.html", "/en/cabo-de-gata/"),
    ):
        name = "Cabo de Gata · OOLITA"
        payload = {
            "@context": "https://schema.org",
            "@type": "WebPage",
            "@id": BASE + route + "#webpage",
            "url": BASE + route,
            "name": name,
            "inLanguage": language,
            "about": {
                "@type": "Place",
                "@id": BASE + "/#los-escullos",
                "name": "Los Escullos",
                "address": {
                    "@type": "PostalAddress",
                    "addressLocality": "Níjar",
                    "addressRegion": "Almería",
                    "addressCountry": "ES",
                },
                "geo": {"@type": "GeoCoordinates", "latitude": 36.7993, "longitude": -2.0632},
            },
        }
        upsert_schema(rel, "oolita-cabo-place-schema", payload)

    for language, rel, route, title, role in (
        ("es", "sobre-oolita/index.html", "/sobre-oolita/", "Sobre OOLITA", "artista y autora"),
        ("en", "en/about/index.html", "/en/about/", "About OOLITA", "artist and author"),
    ):
        payload = {
            "@context": "https://schema.org",
            "@type": "AboutPage",
            "@id": BASE + route + "#webpage",
            "url": BASE + route,
            "name": title,
            "inLanguage": language,
            "about": {
                "@type": "CreativeWork",
                "@id": BASE + "/#oolita-project",
                "name": "OOLITA",
                "creator": {
                    "@type": "Person",
                    "@id": BASE + "/#raquel-costantini",
                    "name": "Raquel Costantini",
                    "jobTitle": role,
                },
                "publisher": {"@type": "Organization", "name": "Vestini Tribe"},
                "locationCreated": {"@id": BASE + "/#los-escullos"},
            },
        }
        upsert_schema(rel, "oolita-about-project-schema", payload)


def update_sitemap() -> None:
    sitemap = ROOT / "sitemap.xml"
    if not sitemap.is_file():
        raise SystemExit("Missing sitemap.xml")
    ET.register_namespace("", "http://www.sitemaps.org/schemas/sitemap/0.9")
    tree = ET.parse(sitemap)
    root = tree.getroot()
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    seen: set[str] = set()
    for url_el in root.findall("sm:url", ns):
        loc = url_el.find("sm:loc", ns)
        if loc is None or not loc.text or not loc.text.strip().startswith(BASE):
            continue
        route = loc.text.strip()[len(BASE):] or "/"
        if route not in CHANGED_ROUTES:
            continue
        seen.add(route)
        lastmod = url_el.find("sm:lastmod", ns)
        if lastmod is None:
            lastmod = ET.SubElement(url_el, "{http://www.sitemaps.org/schemas/sitemap/0.9}lastmod")
        lastmod.text = LASTMOD
    missing = sorted(CHANGED_ROUTES - seen)
    if missing:
        raise SystemExit(f"Engagement-depth URLs missing from sitemap: {missing}")
    tree.write(sitemap, encoding="utf-8", xml_declaration=True)


def validate() -> None:
    checks = {
        "cabo-de-gata/index.html": ["data-place-depth", "data-material-paths", "/laberinto/", "/ediciones/", "/mundo-3d/", "oolita-cabo-place-schema"],
        "en/cabo-de-gata/index.html": ["data-place-depth", "data-material-paths", "/en/labyrinth/", "/en/editions/", "/en/3d-world/", "oolita-cabo-place-schema"],
        "sobre-oolita/index.html": ["oolita-about-project-schema", '"@type":"AboutPage"', "Raquel Costantini", "Vestini Tribe"],
        "en/about/index.html": ["oolita-about-project-schema", '"@type":"AboutPage"', "Raquel Costantini", "Vestini Tribe"],
        "domingos/index.html": ['data-sunday-archive-row="1"', 'data-sunday-archive-row="2"', 'data-sunday-archive-row="3"', "/domingos/img/03-180.avif"],
        "en/sundays/index.html": ['data-sunday-archive-row="1"', 'data-sunday-archive-row="2"', 'data-sunday-archive-row="3"', "/domingos/img/03-180.avif"],
    }
    for language, prefix, slugs in (
        ("es", "domingos", [SUNDAYS[n]["es"] for n in SUNDAYS]),
        ("en", "en/sundays", [SUNDAYS[n]["en"] for n in SUNDAYS]),
    ):
        for number, slug in enumerate(slugs, start=1):
            rel = f"{prefix}/{slug}/index.html"
            checks[rel] = ["data-sunday-context", "data-sunday-responsive", "sizes="]
            if SUNDAYS[number]["width"] > 700:
                checks[rel].append(f"/domingos/img/{number:02d}-700.avif 700w")
    for rel, needles in checks.items():
        _, text = read(rel)
        for needle in needles:
            if needle not in text:
                raise SystemExit(f"Engagement-depth invariant missing in {rel}: {needle}")
    for number, item in SUNDAYS.items():
        variants = [f"{number:02d}-180.jpg", f"{number:02d}-180.avif", f"{number:02d}.avif"]
        if item["width"] > 700:
            variants += [f"{number:02d}-700.jpg", f"{number:02d}-700.avif"]
        for name in variants:
            target = ROOT / "domingos" / "img" / name
            if not target.is_file() or target.stat().st_size < 1_000:
                raise SystemExit(f"Sunday responsive asset missing or invalid: {name}")


def main() -> None:
    if not ROOT.is_dir():
        raise SystemExit(f"Missing built site: {ROOT}")
    patch_cabo("cabo-de-gata/index.html", "es")
    patch_cabo("en/cabo-de-gata/index.html", "en")
    build_sunday_images()
    for number, item in SUNDAYS.items():
        patch_sunday_detail(f'domingos/{item["es"]}/index.html', "es", number)
        patch_sunday_detail(f'en/sundays/{item["en"]}/index.html', "en", number)
    patch_archive("domingos/index.html", "es")
    patch_archive("en/sundays/index.html", "en")
    add_structured_data()
    update_sitemap()
    validate()
    print("OOLITA engagement depth, responsive Sundays and structured data validated successfully.")


if __name__ == "__main__":
    main()
