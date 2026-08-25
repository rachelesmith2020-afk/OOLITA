#!/usr/bin/env python3
"""Resolve the remaining low-severity GSC Wizard findings on the final build."""
from __future__ import annotations

from pathlib import Path
import json
import re
import sys
import xml.etree.ElementTree as ET

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
SITEMAP = ROOT / "sitemap.xml"
BASE = "https://oolita.es"
LASTMOD = "2026-08-25"

if not ROOT.is_dir():
    raise SystemExit(f"Missing built site: {ROOT}")
if not SITEMAP.is_file():
    raise SystemExit(f"Missing sitemap: {SITEMAP}")


def p(rel: str) -> Path:
    target = ROOT / rel
    if not target.is_file():
        raise SystemExit(f"Missing required page: {rel}")
    return target


def read(rel: str) -> str:
    return p(rel).read_text(encoding="utf-8")


def write(rel: str, text: str) -> None:
    p(rel).write_text(text, encoding="utf-8")


def patch_meta_title(html: str, attr: str, key: str, value: str) -> str:
    tag_re = re.compile(r"<meta\b[^>]*>", re.I)

    def repl(match: re.Match[str]) -> str:
        tag = match.group(0)
        if not re.search(rf"\b{re.escape(attr)}=[\"']{re.escape(key)}[\"']", tag, re.I):
            return tag
        if not re.search(r"\bcontent\s*=\s*([\"'])[^\"']*\1", tag, re.I):
            return tag
        return re.sub(
            r"\bcontent\s*=\s*([\"'])[^\"']*\1",
            lambda m: f"content={m.group(1)}{value}{m.group(1)}",
            tag,
            count=1,
            flags=re.I,
        )

    return tag_re.sub(repl, html)


def set_title(rel: str, title: str) -> None:
    if not 30 <= len(title) <= 60:
        raise SystemExit(f"Title outside 30–60 character target: {rel} ({len(title)})")
    text = read(rel)
    text, count = re.subn(
        r"<title>[\s\S]*?</title>", f"<title>{title}</title>", text,
        count=1, flags=re.I,
    )
    if count != 1:
        raise SystemExit(f"Expected one title element: {rel}")
    text = patch_meta_title(text, "property", "og:title", title)
    text = patch_meta_title(text, "name", "twitter:title", title)
    write(rel, text)
    print(f"low-severity SEO: title normalized {rel}")


TITLE_FIXES = {
    "que-es-un-laberinto/index.html": "Qué es un laberinto clásico y cómo funciona · OOLITA",
    "ediciones/libro/index.html": "El libro — una fábula de laberinto bilingüe · OOLITA",
    "cabo-de-gata/index.html": "Cabo de Gata-Níjar: territorio y paisaje · OOLITA",
    "en/cabo-de-gata/index.html": "Cabo de Gata-Níjar: landscape and territory · OOLITA",
    "privacidad/index.html": "Privacidad y datos personales · OOLITA",
    "en/privacy/index.html": "Privacy and personal data · OOLITA",
}
for rel, title in TITLE_FIXES.items():
    set_title(rel, title)


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
SCHEMA_ID = "oolita-privacy-webpage-schema"
for rel, payload in PRIVACY_SCHEMA.items():
    text = read(rel)
    text = re.sub(
        rf'<script\b[^>]*id=["\']{SCHEMA_ID}["\'][^>]*>[\s\S]*?</script>\s*',
        "", text, flags=re.I,
    )
    block = (
        f'<script type="application/ld+json" id="{SCHEMA_ID}">'
        + json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        + "</script>"
    )
    if "</head>" not in text:
        raise SystemExit(f"Missing </head>: {rel}")
    text = text.replace("</head>", block + "\n</head>", 1)
    write(rel, text)
    m = re.search(
        rf'<script\b[^>]*id=["\']{SCHEMA_ID}["\'][^>]*>([\s\S]*?)</script>',
        text, re.I,
    )
    if not m:
        raise SystemExit(f"Privacy schema insertion failed: {rel}")
    json.loads(m.group(1))
    print(f"low-severity SEO: WebPage schema valid {rel}")


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

    def image_repl(match: re.Match[str]) -> str:
        tag = match.group(0)
        key = next(
            (n for n in ("01", "02", "03") if re.search(rf"(?:/|domingos/img/){n}(?:[-.]|[\"'])", tag, re.I)),
            None,
        )
        if key is None:
            return tag
        alt = alts[key]
        if re.search(r"\balt\s*=", tag, re.I):
            return re.sub(
                r"\balt\s*=\s*([\"'])[^\"']*\1",
                lambda m: f'alt={m.group(1)}{alt}{m.group(1)}',
                tag, count=1, flags=re.I,
            )
        return tag[:-1] + f' alt="{alt}">'

    text = re.sub(r"<img\b[^>]*>", image_repl, text, flags=re.I)
    write(rel, text)
    imgs = re.findall(r"<img\b[^>]*>", text, flags=re.I)
    if not imgs:
        raise SystemExit(f"No Sunday archive images found: {rel}")
    missing = [tag for tag in imgs if not re.search(r"\balt\s*=\s*([\"'])[^\"']+\1", tag, re.I)]
    if missing:
        raise SystemExit(f"Sunday archive image(s) still missing alt: {rel}")
    print(f"low-severity accessibility: {len(imgs)} image alt text(s) valid {rel}")


CONTENT_BLOCKS = {
    "en/about/index.html": (
        "working-rhythm",
        '''<section class="tramo" id="working-rhythm"><span class="rot">22 Sundays</span><h2 class="grande">A public working rhythm.</h2><p class="parr">The 22 Sundays are the public rhythm of OOLITA. Each release adds an image, a short text and another route into the place. The editions and the 3D world develop alongside that sequence, while the labyrinth at Los Escullos remains the physical starting point. The archive keeps those stages visible rather than presenting the project as a finished object.</p></section>''',
    ),
    "en/work-with-oolita/index.html": (
        "before-writing",
        '''<section class="tramo" id="before-writing"><span class="rot">Before writing</span><h2 class="grande">A useful proposal is specific.</h2><p class="parr">If you are a bookshop, say where you are and what kind of publication you would like to stock. If you are an educator or cultural organisation, describe the group, place, date range and the kind of activity you have in mind. Makers can explain the material, process and production scale they work with.</p><p class="parr">OOLITA is interested in small, clearly attributed collaborations connected to books, observation, fieldwork and material practice. It does not add partner names speculatively: authorship, production, materials, quantities and responsibilities are stated only after an agreement exists.</p><p class="parr">Where a proposal involves Cabo de Gata, the starting point is low-impact use: no collecting from the site and no second OOLITA labyrinth. The aim is to extend attention to the place, not increase pressure on it.</p><p class="parr">A first email does not need to be formal. A few sentences, a location and a link to relevant work are enough to begin.</p></section>''',
    ),
    "colaborar/index.html": (
        "antes-de-escribir",
        '''<section class="tramo" id="antes-de-escribir"><span class="rot">Antes de escribir</span><h2 class="grande">Una propuesta útil es concreta.</h2><p class="parr">Si eres una librería, indica dónde estás y qué tipo de publicación te interesaría tener. Si eres educador u organización cultural, describe el grupo, el lugar, el intervalo de fechas y el tipo de actividad que imaginas. Los artesanos o productores pueden explicar el material, el proceso y la escala con la que trabajan.</p><p class="parr">OOLITA busca colaboraciones pequeñas y claramente atribuidas, relacionadas con libros, observación, trabajo de campo y práctica material. No añade nombres de colaboradores de forma especulativa: autoría, producción, materiales, cantidades y responsabilidades se indican sólo cuando existe un acuerdo.</p><p class="parr">Cuando una propuesta afecta a Cabo de Gata, el punto de partida es un uso de bajo impacto: no recoger materiales del lugar y no crear un segundo laberinto OOLITA. La intención es ampliar la atención al territorio, no aumentar la presión sobre él.</p><p class="parr">Un primer correo no tiene que ser formal. Unas frases, una ubicación y un enlace a trabajo relevante bastan para empezar.</p></section>''',
    ),
    "en/sundays/03-the-memory-of-the-sea/index.html": (
        "sunday-03-sequence-context",
        '''<section class="tramo" id="sunday-03-sequence-context"><span class="rot">22 Sundays</span><p class="parr">Sunday 03 belongs to the 22-Sunday publication sequence leading toward the 2027 opening. The weekly archive keeps the image, text and onward routes together as the project develops, so this geological note remains part of a continuing public record rather than an isolated post.</p></section>''',
    ),
    "domingos/03-la-memoria-del-mar/index.html": (
        "domingo-03-secuencia-contexto",
        '''<section class="tramo" id="domingo-03-secuencia-contexto"><span class="rot">22 domingos</span><p class="parr">El Domingo 03 forma parte de la secuencia de 22 domingos que conduce a la apertura de 2027. El archivo semanal conserva juntos la imagen, el texto y los recorridos que continúan mientras el proyecto se desarrolla, de modo que esta nota geológica queda dentro de un registro público en curso y no como una publicación aislada.</p></section>''',
    ),
}
for rel, (block_id, block) in CONTENT_BLOCKS.items():
    text = read(rel)
    text = re.sub(
        rf'<section\b[^>]*id=["\']{re.escape(block_id)}["\'][^>]*>[\s\S]*?</section>\s*',
        "", text, flags=re.I,
    )
    if "</main>" not in text:
        raise SystemExit(f"Missing </main> for content-depth insertion: {rel}")
    text = text.replace("</main>", block + "\n</main>", 1)
    write(rel, text)
    if text.count(f'id="{block_id}"') != 1:
        raise SystemExit(f"Content-depth block validation failed: {rel}")
    print(f"low-severity content: useful depth added {rel}")


def visible_words(rel: str) -> int:
    text = read(rel)
    m = re.search(r"<body\b[^>]*>([\s\S]*?)</body>", text, re.I)
    body = m.group(1) if m else text
    body = re.sub(r"<script\b[\s\S]*?</script>", " ", body, flags=re.I)
    body = re.sub(r"<style\b[\s\S]*?</style>", " ", body, flags=re.I)
    body = re.sub(r"<[^>]+>", " ", body)
    return len(re.findall(r"\b[\wÀ-ÿ’'-]+\b", body, flags=re.UNICODE))


MIN_WORDS = {
    "en/about/index.html": 300,
    "en/work-with-oolita/index.html": 300,
    "colaborar/index.html": 300,
    "en/sundays/03-the-memory-of-the-sea/index.html": 300,
    "domingos/03-la-memoria-del-mar/index.html": 300,
}
for rel, minimum in MIN_WORDS.items():
    count = visible_words(rel)
    if count < minimum:
        raise SystemExit(f"Content remains below {minimum} visible words: {rel}={count}")
    print(f"low-severity content: visible words {rel}={count}")


ROUTES = {
    "/domingos/", "/en/sundays/", "/que-es-un-laberinto/", "/ediciones/libro/",
    "/cabo-de-gata/", "/en/cabo-de-gata/", "/privacidad/", "/en/privacy/",
    "/en/about/", "/colaborar/", "/en/work-with-oolita/",
    "/domingos/03-la-memoria-del-mar/", "/en/sundays/03-the-memory-of-the-sea/",
}
ET.register_namespace("", "http://www.sitemaps.org/schemas/sitemap/0.9")
tree = ET.parse(SITEMAP)
root = tree.getroot()
ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
seen: set[str] = set()
for url_el in root.findall("sm:url", ns):
    loc = url_el.find("sm:loc", ns)
    if loc is None or not loc.text or not loc.text.startswith(BASE):
        continue
    route = loc.text[len(BASE):] or "/"
    if route not in ROUTES:
        continue
    seen.add(route)
    lastmod = url_el.find("sm:lastmod", ns)
    if lastmod is None:
        lastmod = ET.SubElement(url_el, "{http://www.sitemaps.org/schemas/sitemap/0.9}lastmod")
    lastmod.text = LASTMOD
if seen != ROUTES:
    raise SystemExit(f"Low-severity routes missing from sitemap: {sorted(ROUTES-seen)}")
tree.write(SITEMAP, encoding="utf-8", xml_declaration=True)

for rel, title in TITLE_FIXES.items():
    if f"<title>{title}</title>" not in read(rel):
        raise SystemExit(f"Final title invariant failed: {rel}")
for rel in PRIVACY_SCHEMA:
    if f'id="{SCHEMA_ID}"' not in read(rel):
        raise SystemExit(f"Final privacy-schema invariant failed: {rel}")

print(
    "OOLITA low-severity final gate passed: title lengths corrected; privacy schema valid; "
    "Sunday image alts present; content-depth pages above 300 visible words; sitemap refreshed."
)
