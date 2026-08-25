#!/usr/bin/env python3
"""Final low-severity SEO/accessibility cleanup for OOLITA.

Runs after every reader-facing transform. It resolves the current GSC Wizard
low-severity findings without changing URLs or page hierarchy:
- descriptive title lengths,
- privacy-page WebPage structured data,
- archive-image alt text,
- genuinely useful copy on pages below the audit's thin-content threshold,
- sitemap lastmod refreshes,
- explicit post-patch validation so regressions fail the deployment.
"""
from __future__ import annotations

from pathlib import Path
import json
import re
import sys
import xml.etree.ElementTree as ET

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
SITEMAP = ROOT / "sitemap.xml"
LASTMOD = "2026-08-25"
BASE = "https://oolita.es"

if not ROOT.is_dir():
    raise SystemExit(f"Missing built site: {ROOT}")
if not SITEMAP.is_file():
    raise SystemExit(f"Missing sitemap: {SITEMAP}")


def page(rel: str) -> Path:
    p = ROOT / rel
    if not p.is_file():
        raise SystemExit(f"Missing required page: {rel}")
    return p


def read(rel: str) -> str:
    return page(rel).read_text(encoding="utf-8")


def write(rel: str, text: str) -> None:
    page(rel).write_text(text, encoding="utf-8")


def replace_title(rel: str, title: str) -> None:
    text = read(rel)
    new_text, count = re.subn(
        r"<title>[\s\S]*?</title>",
        f"<title>{title}</title>",
        text,
        count=1,
        flags=re.I,
    )
    if count != 1:
        raise SystemExit(f"Expected one <title> in {rel}; found {count}")

    def patch_meta(source: str, attr: str, key: str) -> str:
        tag_re = re.compile(r"<meta\b[^>]*>", re.I)
        matches = 0

        def repl(m: re.Match[str]) -> str:
            nonlocal matches
            tag = m.group(0)
            if not re.search(
                rf"\b{re.escape(attr)}=[\"']{re.escape(key)}[\"']",
                tag,
                flags=re.I,
            ):
                return tag
            matches += 1
            if re.search(r"\bcontent=[\"'][^\"']*[\"']", tag, flags=re.I):
                return re.sub(
                    r"\bcontent=([\"'])[^\"']*\1",
                    lambda cm: f"content={cm.group(1)}{title}{cm.group(1)}",
                    tag,
                    count=1,
                    flags=re.I,
                )
            return tag

        result = tag_re.sub(repl, source)
        if matches > 1:
            raise SystemExit(f"Duplicate meta {attr}={key} in {rel}")
        return result

    new_text = patch_meta(new_text, "property", "og:title")
    new_text = patch_meta(new_text, "name", "twitter:title")
    write(rel, new_text)
    print(f"low-severity SEO: title normalized {rel}: {title}")


TITLE_FIXES = {
    "que-es-un-laberinto/index.html":
        "Qué es un laberinto clásico y cómo funciona · OOLITA",
    "ediciones/libro/index.html":
        "El libro — una fábula de laberinto bilingüe · OOLITA",
    "cabo-de-gata/index.html":
        "Cabo de Gata-Níjar: territorio y paisaje · OOLITA",
    "en/cabo-de-gata/index.html":
        "Cabo de Gata-Níjar: landscape and territory · OOLITA",
    "privacidad/index.html":
        "Privacidad y datos personales · OOLITA",
    "en/privacy/index.html":
        "Privacy and personal data · OOLITA",
}
for rel, title in TITLE_FIXES.items():
    if not (30 <= len(title) <= 60):
        raise SystemExit(f"SEO title outside 30–60 char target: {rel}: {len(title)}")
    replace_title(rel, title)


PRIVACY_SCHEMA = {
    "privacidad/index.html": {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": "Privacidad y datos personales",
        "url": f"{BASE}/privacidad/",
        "inLanguage": "es",
        "isPartOf": {"@type": "WebSite", "name": "OOLITA", "url": f"{BASE}/"},
    },
    "en/privacy/index.html": {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": "Privacy and personal data",
        "url": f"{BASE}/en/privacy/",
        "inLanguage": "en",
        "isPartOf": {"@type": "WebSite", "name": "OOLITA", "url": f"{BASE}/"},
    },
}
for rel, payload in PRIVACY_SCHEMA.items():
    text = read(rel)
    marker = 'id="oolita-privacy-webpage-schema"'
    if marker not in text:
        block = (
            '<script type="application/ld+json" id="oolita-privacy-webpage-schema">'
            + json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
            + "</script>"
        )
        if "</head>" not in text:
            raise SystemExit(f"Missing </head> in privacy page: {rel}")
        text = text.replace("</head>", block + "\n</head>", 1)
        write(rel, text)
        print(f"low-severity SEO: privacy WebPage schema added {rel}")

    current = read(rel)
    m = re.search(
        r'<script[^>]*id=["\']oolita-privacy-webpage-schema["\'][^>]*>([\s\S]*?)</script>',
        current,
        flags=re.I,
    )
    if not m:
        raise SystemExit(f"Privacy schema marker missing after patch: {rel}")
    json.loads(m.group(1))


ALT_TEXT = {
    "domingos/index.html": {
        "01": "Domingo 01 · El doble — OOLITA en Los Escullos",
        "02": "Domingo 02 · El gato, de verdad — OOLITA",
        "03": "Domingo 03 · La memoria del mar — oolitos y duna fósil",
    },
    "en/sundays/index.html": {
        "01": "Sunday 01 · The double — OOLITA at Los Escullos",
        "02": "Sunday 02 · The cat, for real — OOLITA",
        "03": "Sunday 03 · The Memory of the Sea — ooids and fossil dune",
    },
}

for rel, alts in ALT_TEXT.items():
    text = read(rel)

    def patch_img(m: re.Match[str]) -> str:
        tag = m.group(0)
        key = None
        for candidate in ("01", "02", "03"):
            if re.search(
                rf"(?:/|domingos/img/){candidate}(?:[-.]|[\"'])",
                tag,
                flags=re.I,
            ):
                key = candidate
                break
        if key is None:
            return tag
        alt = alts[key]
        if re.search(r"\balt\s*=", tag, flags=re.I):
            return re.sub(
                r"\balt\s*=\s*([\"'])[\s\S]*?\1",
                lambda cm: f'alt={cm.group(1)}{alt}{cm.group(1)}',
                tag,
                count=1,
                flags=re.I,
            )
        return tag[:-1] + f' alt="{alt}">'

    patched = re.sub(r"<img\b[^>]*>", patch_img, text, flags=re.I)
    write(rel, patched)

    img_tags = re.findall(r"<img\b[^>]*>", patched, flags=re.I)
    if not img_tags:
        raise SystemExit(f"No archive images found in {rel}")
    missing = [
        tag for tag in img_tags
        if not re.search(r"\balt\s*=\s*([\"'])\s*[^\"']+\1", tag, flags=re.I)
    ]
    if missing:
        raise SystemExit(f"Archive image alt validation failed in {rel}: {missing}")
    print(f"low-severity accessibility: {len(img_tags)} image alt text(s) valid in {rel}")


ABOUT_EN_BLOCK = '''<section class="tramo" id="working-rhythm"><span class="rot">22 Sundays</span><h2 class="grande">A public working rhythm.</h2><p class="parr">The 22 Sundays are the public rhythm of OOLITA: each release adds an image, a short text and another route into the place. The editions and the 3D world develop alongside that sequence, while the labyrinth at Los Escullos remains the physical starting point. The archive keeps those stages visible rather than presenting the project as a finished object.</p></section>'''

WORK_EN_BLOCK = '''<section class="tramo" id="before-writing"><span class="rot">Before writing</span><h2 class="grande">A useful proposal is specific.</h2><p class="parr">If you are a bookshop, say where you are and what kind of publication you would like to stock. If you are an educator or cultural organisation, describe the group, place, date range and the kind of activity you have in mind. Makers can explain the material, process and production scale they work with.</p><p class="parr">OOLITA is interested in small, clearly attributed collaborations connected to books, observation, fieldwork and material practice. It does not add partner names speculatively: authorship, production, materials, quantities and responsibilities are stated only after an agreement exists.</p><p class="parr">Where a proposal involves Cabo de Gata, the starting point is low-impact use: no collecting from the site and no second OOLITA labyrinth. The aim is to extend attention to the place, not increase pressure on it.</p><p class="parr">A first email does not need to be formal. A few sentences, a location and a link to relevant work are enough to begin.</p></section>'''

WORK_ES_BLOCK = '''<section class="tramo" id="antes-de-escribir"><span class="rot">Antes de escribir</span><h2 class="grande">Una propuesta útil es concreta.</h2><p class="parr">Si eres una librería, indica dónde estás y qué tipo de publicación te interesaría tener. Si eres educador u organización cultural, describe el grupo, el lugar, el intervalo de fechas y el tipo de actividad que imaginas. Los artesanos o productores pueden explicar el material, el proceso y la escala con la que trabajan.</p><p class="parr">OOLITA busca colaboraciones pequeñas y claramente atribuidas, relacionadas con libros, observación, trabajo de campo y práctica material. No añade nombres de colaboradores de forma especulativa: autoría, producción, materiales, cantidades y responsabilidades se indican sólo cuando existe un acuerdo.</p><p class="parr">Cuando una propuesta afecta a Cabo de Gata, el punto de partida es un uso de bajo impacto: no recoger materiales del lugar y no crear un segundo laberinto OOLITA. La intención es ampliar la atención al territorio, no aumentar la presión sobre él.</p><p class="parr">Un primer correo no tiene que ser formal. Unas frases, una ubicación y un enlace a trabajo relevante bastan para empezar.</p></section>'''

INSERT_BEFORE = {
    "en/about/index.html": (
        'id="working-rhythm"',
        '<section class="tramo"><span class="rot">Contact</span><h2 class="grande">Write.</h2>',
        ABOUT_EN_BLOCK,
    ),
    "en/work-with-oolita/index.html": (
        'id="before-writing"',
        '<section class="tramo env"><span class="rot">Contact</span><h2 class="grande">Tell me what you have in mind.</h2>',
        WORK_EN_BLOCK,
    ),
    "colaborar/index.html": (
        'id="antes-de-escribir"',
        '<section class="tramo env"><span class="rot">Contacto</span><h2 class="grande">Cuéntame qué tienes en mente.</h2>',
        WORK_ES_BLOCK,
    ),
}
for rel, (marker, anchor, block) in INSERT_BEFORE.items():
    text = read(rel)
    if marker in text:
        continue
    if anchor not in text:
        raise SystemExit(f"Thin-content insertion anchor missing in {rel}")
    text = text.replace(anchor, block + "\n" + anchor, 1)
    write(rel, text)
    print(f"low-severity content: useful depth added {rel}")


SUNDAY_DEPTH = {
    "en/sundays/03-the-memory-of-the-sea/index.html": (
        "Sunday 03 belongs to the 22-Sunday publication sequence",
        r'(<p\b[^>]*>Oolitic calcarenite joins the labyrinth to the fossil dune\.[\s\S]*?</p>)',
        '<p class="parr">Sunday 03 belongs to the 22-Sunday publication sequence leading toward the 2027 opening. The weekly archive keeps the image, text and onward routes together as the project develops.</p>',
    ),
    "domingos/03-la-memoria-del-mar/index.html": (
        "El Domingo 03 forma parte de la secuencia de 22 domingos",
        r'(<p\b[^>]*>La calcarenita oolítica une el laberinto con la duna fósil\.[\s\S]*?</p>)',
        '<p class="parr">El Domingo 03 forma parte de la secuencia de 22 domingos que conduce a la apertura de 2027. El archivo semanal conserva juntos la imagen, el texto y los recorridos que continúan mientras el proyecto se desarrolla.</p>',
    ),
}
for rel, (marker, pattern, addition) in SUNDAY_DEPTH.items():
    text = read(rel)
    if marker in text:
        continue
    patched, count = re.subn(
        pattern,
        lambda m: m.group(1) + addition,
        text,
        count=1,
        flags=re.I,
    )
    if count != 1:
        raise SystemExit(f"Sunday depth insertion anchor missing in {rel}")
    write(rel, patched)
    print(f"low-severity content: Sunday context added {rel}")


def visible_word_count(rel: str) -> int:
    text = read(rel)
    body_match = re.search(r"<body\b[^>]*>([\s\S]*?)</body>", text, flags=re.I)
    body = body_match.group(1) if body_match else text
    body = re.sub(r"<script\b[\s\S]*?</script>", " ", body, flags=re.I)
    body = re.sub(r"<style\b[\s\S]*?</style>", " ", body, flags=re.I)
    body = re.sub(r"<[^>]+>", " ", body)
    body = re.sub(r"&[a-zA-Z0-9#]+;", " ", body)
    words = re.findall(r"\b[\wÀ-ÿ'’.-]+\b", body, flags=re.UNICODE)
    return len(words)


MINIMUMS = {
    "en/about/index.html": 300,
    "en/work-with-oolita/index.html": 300,
    "colaborar/index.html": 300,
    "en/sundays/03-the-memory-of-the-sea/index.html": 300,
    "domingos/03-la-memoria-del-mar/index.html": 300,
}
for rel, minimum in MINIMUMS.items():
    count = visible_word_count(rel)
    if count < minimum:
        raise SystemExit(f"Visible word count remains below {minimum}: {rel} = {count}")
    print(f"low-severity content: {rel} visible words={count}")


ROUTES = {
    "/domingos/",
    "/en/sundays/",
    "/que-es-un-laberinto/",
    "/ediciones/libro/",
    "/cabo-de-gata/",
    "/en/cabo-de-gata/",
    "/privacidad/",
    "/en/privacy/",
    "/en/about/",
    "/colaborar/",
    "/en/work-with-oolita/",
    "/domingos/03-la-memoria-del-mar/",
    "/en/sundays/03-the-memory-of-the-sea/",
}
ET.register_namespace("", "http://www.sitemaps.org/schemas/sitemap/0.9")
tree = ET.parse(SITEMAP)
root = tree.getroot()
ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
matched: set[str] = set()
for url_el in root.findall("sm:url", ns):
    loc = url_el.find("sm:loc", ns)
    if loc is None or not loc.text:
        continue
    absolute = loc.text.strip()
    if not absolute.startswith(BASE):
        continue
    route = absolute[len(BASE):] or "/"
    if route not in ROUTES:
        continue
    matched.add(route)
    lastmod = url_el.find("sm:lastmod", ns)
    if lastmod is None:
        lastmod = ET.SubElement(
            url_el, "{http://www.sitemaps.org/schemas/sitemap/0.9}lastmod"
        )
    lastmod.text = LASTMOD

missing_routes = sorted(ROUTES - matched)
if missing_routes:
    raise SystemExit(f"Low-severity routes missing from sitemap: {missing_routes}")
tree.write(SITEMAP, encoding="utf-8", xml_declaration=True)

for rel, title in TITLE_FIXES.items():
    text = read(rel)
    if f"<title>{title}</title>" not in text:
        raise SystemExit(f"Final title validation failed: {rel}")
for rel in PRIVACY_SCHEMA:
    if 'id="oolita-privacy-webpage-schema"' not in read(rel):
        raise SystemExit(f"Final privacy schema validation failed: {rel}")

print(
    "OOLITA low-severity final gate passed: title lengths corrected; privacy "
    "schema present; Sunday image alts present; thin-content pages above 300 "
    "visible words; sitemap refreshed."
)
