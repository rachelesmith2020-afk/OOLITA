#!/usr/bin/env python3
"""Publish the two UK garment choices for OOLITA's first textile edition.

Runs late in the deployment pipeline so the approved product copy and SEO metadata
win over mirrored-origin content. It does not expose price or enable checkout.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
MARKER = 'data-oolita-textile-variants="v1"'

PAGES = {
    "en/editions/t-shirt/index.html": {
        "canonical": "https://oolita.es/en/editions/t-shirt/",
        "title": "OOLITA T-shirt — regular and heavy oversized · OOLITA",
        "description": (
            "OOLITA's first textile edition: choose a 180 gsm Stanley/Stella RE-Creator regular fit "
            "or 200 gsm Blaster 2.0 heavy oversized. Made on demand."
        ),
        "hero_old": "White Stanley/Stella Blaster 2.0, oversized unisex fit, without the design",
        "hero_new": "White Stanley/Stella Blaster 2.0, heavy oversized option, without the design",
        "intro_old": (
            "White, 200 gsm organic cotton, an oversized unisex fit. For now just the bare garment: "
            "the design is unveiled Sunday by Sunday, through to spring."
        ),
        "intro_new": (
            "White cotton, one OOLITA design, two unisex cuts: a 180 gsm regular option and a 200 gsm "
            "heavy oversized option. For now the garments remain blank: the design is unveiled Sunday "
            "by Sunday, through to spring."
        ),
        "piece_old": (
            "This first piece is a 200 gsm organic-cotton T-shirt with a loose cut. The printed image — "
            "and where it sits — will be revealed little by little."
        ),
        "piece_new": (
            "The first textile edition is available in two cuts of the same OOLITA design: Regular at "
            "180 gsm and Heavy Oversized at 200 gsm. The printed image — and where it sits — will be "
            "revealed little by little."
        ),
        "garment_old": (
            "It is a Stanley/Stella Blaster 2.0, not a generic tee. Single jersey in organic ring-spun "
            "combed cotton, 20 singles, 200 grams per square metre. Oversized cut with a dropped shoulder, "
            "side-seamed, elastane-free 1x1 rib mock-neck collar and self-fabric tape inside the back neck. "
            "Twin-needle topstitching at cuffs and hem, and a tear-away label: nothing scratches."
        ),
        "garment_new": (
            "There are two Stanley/Stella choices. Regular is the RE-Creator STTU787: 180 gsm, medium fit, "
            "50% recycled cotton and 50% organic cotton, made from Stanley/Stella's own organic cutting waste. "
            "Heavy Oversized is the Blaster 2.0 STTU959: 200 gsm organic combed cotton, oversized with a dropped "
            "shoulder and mock-neck rib collar. Both are unisex, white and available from XXS to 3XL."
        ),
        "cert_old": (
            "The garment is made from XXS to 3XL. It carries GOTS organic cotton certification, OEKO-TEX, "
            "PETA-approved vegan status and Fair Wear accreditation in the making. That matters here: an object "
            "born of a labyrinth built from stone picked up off the ground cannot arrive from an opaque factory."
        ),
        "cert_new": (
            "The RE-Creator is listed by Stanley/Stella with GRS, OCS and OEKO-TEX credentials; the Blaster 2.0 "
            "with GOTS and OEKO-TEX. Stanley/Stella is a Fair Wear member and its garments are vegan. The two "
            "options keep the same traceable-garment standard while giving a choice of weight and cut."
        ),
        "heading_anchor": "Why it is revealed slowly.",
        "cards": (
            '<div class="textile-choice-grid" data-oolita-textile-choices="v1">'
            '<article class="textile-choice"><p class="textile-choice-kicker">REGULAR</p>'
            '<h3>Stanley/Stella RE-Creator</h3><p>STTU787 · 180 gsm · medium unisex fit</p>'
            '<p>50% recycled cotton · 50% organic cotton · XXS–3XL · white</p></article>'
            '<article class="textile-choice"><p class="textile-choice-kicker">HEAVY OVERSIZED</p>'
            '<h3>Stanley/Stella Blaster 2.0</h3><p>STTU959 · 200 gsm · oversized unisex fit</p>'
            '<p>100% organic combed cotton · dropped shoulder · XXS–3XL · white</p></article>'
            '</div>'
        ),
        "schema_name": "OOLITA first textile edition",
    },
    "ediciones/camiseta/index.html": {
        "canonical": "https://oolita.es/ediciones/camiseta/",
        "title": "Camiseta OOLITA — regular y heavy oversized · OOLITA",
        "description": (
            "Primera edición textil de OOLITA: RE-Creator Stanley/Stella de 180 g/m² corte regular o "
            "Blaster 2.0 de 200 g/m² heavy oversized, bajo demanda."
        ),
        "hero_old": "Camiseta blanca Stanley/Stella Blaster 2.0, corte oversized unisex, sin el diseño",
        "hero_new": "Camiseta blanca Stanley/Stella Blaster 2.0, opción heavy oversized, sin el diseño",
        "intro_old": (
            "Blanca, de algodón orgánico de 200 g/m² y corte oversized unisex. Los detalles y la historia "
            "del diseño se irán contando domingo a domingo hasta la primavera."
        ),
        "intro_new": (
            "Blanca, un diseño OOLITA y dos cortes unisex: opción regular de 180 g/m² y opción heavy oversized "
            "de 200 g/m². Los detalles y la historia del diseño se irán contando domingo a domingo hasta la primavera."
        ),
        "piece_old": (
            "Esta primera pieza es una camiseta de algodón orgánico de 200 gramos y corte holgado. Los detalles "
            "de la imagen impresa, su colocación y su historia se irán desvelando poco a poco."
        ),
        "piece_new": (
            "La primera edición textil se ofrece en dos cortes del mismo diseño OOLITA: Regular de 180 g/m² y "
            "Heavy Oversized de 200 g/m². La imagen impresa —y su colocación— se irá desvelando poco a poco."
        ),
        "garment_old": (
            "Es una Stanley/Stella Blaster 2.0, no una camiseta genérica: jersey sencillo de algodón orgánico "
            "peinado e hilado en anillo, 200 g/m². Corte oversized, manga montada, hombro caído, cuello alto de "
            "canalé 1x1, cinta interior del cuello y pespunte doble en puños y bajo."
        ),
        "garment_new": (
            "Hay dos opciones Stanley/Stella. Regular es la RE-Creator STTU787: 180 g/m², corte medio, 50% algodón "
            "reciclado y 50% algodón orgánico, fabricada con recortes de algodón orgánico de la propia marca. Heavy "
            "Oversized es la Blaster 2.0 STTU959: 200 g/m² de algodón orgánico peinado, corte oversized con hombro "
            "caído y cuello alto de canalé. Ambas son unisex, blancas y están disponibles de XXS a 3XL."
        ),
        "cert_old": (
            "La ficha de Stanley/Stella muestra la Blaster 2.0 con certificaciones GOTS y OEKO-TEX. Stanley/Stella "
            "es miembro de Fair Wear y está aprobada por PETA; sus productos están hechos con materiales 100 % veganos."
        ),
        "cert_new": (
            "Stanley/Stella muestra la RE-Creator con credenciales GRS, OCS y OEKO-TEX, y la Blaster 2.0 con GOTS "
            "y OEKO-TEX. La marca es miembro de Fair Wear y sus prendas son veganas. Las dos opciones mantienen el "
            "mismo criterio de trazabilidad y permiten elegir gramaje y corte."
        ),
        "heading_anchor": "Por qué se cuenta despacio.",
        "cards": (
            '<div class="textile-choice-grid" data-oolita-textile-choices="v1">'
            '<article class="textile-choice"><p class="textile-choice-kicker">REGULAR</p>'
            '<h3>Stanley/Stella RE-Creator</h3><p>STTU787 · 180 g/m² · corte medio unisex</p>'
            '<p>50% algodón reciclado · 50% algodón orgánico · XXS–3XL · blanca</p></article>'
            '<article class="textile-choice"><p class="textile-choice-kicker">HEAVY OVERSIZED</p>'
            '<h3>Stanley/Stella Blaster 2.0</h3><p>STTU959 · 200 g/m² · corte oversized unisex</p>'
            '<p>100% algodón orgánico peinado · hombro caído · XXS–3XL · blanca</p></article>'
            '</div>'
        ),
        "schema_name": "Primera edición textil OOLITA",
    },
}

STYLE = """<style data-oolita-textile-variants="v1">
.textile-choice-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:0;border-top:1px solid currentColor;border-bottom:1px solid currentColor;margin:1.75rem 0 2.25rem}.textile-choice{padding:1.2rem 1.25rem 1.25rem 0}.textile-choice+.textile-choice{border-left:1px solid currentColor;padding-left:1.25rem}.textile-choice h3{margin:.2rem 0 .55rem}.textile-choice p{margin:.35rem 0}.textile-choice-kicker{font-size:.75em;letter-spacing:.12em}.textile-choice-grid p:not(.textile-choice-kicker){opacity:.82}@media(max-width:700px){.textile-choice-grid{grid-template-columns:1fr}.textile-choice{padding:1rem 0}.textile-choice+.textile-choice{border-left:0;border-top:1px solid currentColor;padding-left:0}}
</style>"""


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one source string, found {count}")
    return text.replace(old, new, 1)


def set_title(text: str, title: str) -> str:
    pattern = re.compile(r"<title>[^<]*</title>", re.I)
    matches = pattern.findall(text)
    if len(matches) != 1:
        raise SystemExit(f"Expected one title tag, found {len(matches)}")
    return pattern.sub(f"<title>{title}</title>", text, count=1)


def set_meta(text: str, attr: str, value: str, content: str, *, required: bool = True) -> str:
    tag_re = re.compile(r"<meta\b[^>]*>", re.I)
    matched = 0

    def patch(match: re.Match[str]) -> str:
        nonlocal matched
        tag = match.group(0)
        if not re.search(rf"\b{re.escape(attr)}=[\"']{re.escape(value)}[\"']", tag, re.I):
            return tag
        matched += 1
        if re.search(r"\bcontent=([\"'])[^\"']*\1", tag, re.I):
            return re.sub(
                r"\bcontent=([\"'])[^\"']*\1",
                lambda m: f"content={m.group(1)}{content}{m.group(1)}",
                tag,
                count=1,
                flags=re.I,
            )
        return tag[:-1] + f' content="{content}">'

    result = tag_re.sub(patch, text)
    if required and matched != 1:
        raise SystemExit(f"Expected one meta {attr}={value}, found {matched}")
    if not required and matched > 1:
        raise SystemExit(f"Expected at most one meta {attr}={value}, found {matched}")
    return result


def insert_before_heading(text: str, heading: str, block: str) -> str:
    if 'data-oolita-textile-choices="v1"' in text:
        return text
    pattern = re.compile(rf"(<h2\b[^>]*>[\s\S]*?{re.escape(heading)}[\s\S]*?</h2>)", re.I)
    match = pattern.search(text)
    if not match:
        raise SystemExit(f"Could not locate textile insertion heading: {heading}")
    return text[:match.start()] + block + "\n" + text[match.start():]


def add_schema(text: str, cfg: dict) -> str:
    if 'data-oolita-textile-product-schema="v1"' in text:
        return text
    schema = {
        "@context": "https://schema.org",
        "@type": "ProductGroup",
        "@id": cfg["canonical"] + "#textile-edition",
        "url": cfg["canonical"],
        "name": cfg["schema_name"],
        "brand": {"@type": "Brand", "name": "OOLITA"},
        "color": "White",
        "releaseDate": "2027-04-11",
        "hasVariant": [
            {
                "@type": "Product",
                "name": "OOLITA Regular",
                "model": "Stanley/Stella RE-Creator STTU787",
                "material": "50% recycled cotton, 50% organic cotton",
                "size": "XXS–3XL",
            },
            {
                "@type": "Product",
                "name": "OOLITA Heavy Oversized",
                "model": "Stanley/Stella Blaster 2.0 STTU959",
                "material": "100% organic combed cotton",
                "size": "XXS–3XL",
            },
        ],
    }
    script = (
        '<script type="application/ld+json" data-oolita-textile-product-schema="v1">'
        + json.dumps(schema, ensure_ascii=False, separators=(",", ":"))
        + "</script>"
    )
    if "</head>" not in text:
        raise SystemExit("Missing </head> for textile product schema")
    return text.replace("</head>", script + "\n</head>", 1)


if not ROOT.is_dir():
    raise SystemExit(f"Missing built site: {ROOT}")

for rel, cfg in PAGES.items():
    path = ROOT / rel
    if not path.is_file():
        raise SystemExit(f"Missing textile page: {rel}")
    text = path.read_text(encoding="utf-8")

    text = replace_once(text, cfg["hero_old"], cfg["hero_new"], rel + " hero alt")
    text = replace_once(text, cfg["intro_old"], cfg["intro_new"], rel + " intro")
    text = replace_once(text, cfg["piece_old"], cfg["piece_new"], rel + " piece")
    text = replace_once(text, cfg["garment_old"], cfg["garment_new"], rel + " garment")
    text = replace_once(text, cfg["cert_old"], cfg["cert_new"], rel + " credentials")

    text = insert_before_heading(text, cfg["heading_anchor"], cfg["cards"])
    if MARKER not in text:
        if "</head>" not in text:
            raise SystemExit(f"Missing </head> in {rel}")
        text = text.replace("</head>", STYLE + "\n</head>", 1)

    text = set_title(text, cfg["title"])
    text = set_meta(text, "name", "description", cfg["description"])
    text = set_meta(text, "property", "og:title", cfg["title"], required=False)
    text = set_meta(text, "property", "og:description", cfg["description"], required=False)
    text = set_meta(text, "name", "twitter:title", cfg["title"], required=False)
    text = set_meta(text, "name", "twitter:description", cfg["description"], required=False)
    text = add_schema(text, cfg)

    if len(cfg["description"]) > 160:
        raise SystemExit(f"Meta description exceeds 160 characters: {rel}")
    required = (
        "RE-Creator STTU787",
        "Blaster 2.0 STTU959",
        'data-oolita-textile-choices="v1"',
        'data-oolita-textile-product-schema="v1"',
        "2027-04-11",
    )
    for needle in required:
        if needle not in text:
            raise SystemExit(f"Missing textile variant marker {needle!r} in {rel}")

    path.write_text(text, encoding="utf-8")
    print(f"textile variants + SEO published: {rel}")

# Keep Editions directory summaries accurate without turning the directory into a product spec sheet.
summary_replacements = {
    "en/editions/index.html": (
        "White, 200 gsm organic cotton, an oversized unisex fit.",
        "White, two unisex cuts: 180 gsm regular or 200 gsm heavy oversized.",
    ),
    "ediciones/index.html": (
        "Blanca, de algodón orgánico de 200 gramos, de corte oversized unisex.",
        "Blanca, dos cortes unisex: regular de 180 g/m² o heavy oversized de 200 g/m².",
    ),
}
for rel, (old, new) in summary_replacements.items():
    path = ROOT / rel
    if not path.is_file():
        raise SystemExit(f"Missing Editions directory: {rel}")
    text = path.read_text(encoding="utf-8")
    if new not in text:
        if text.count(old) != 1:
            raise SystemExit(f"Could not update textile summary in {rel}; source count={text.count(old)}")
        text = text.replace(old, new, 1)
        path.write_text(text, encoding="utf-8")
    print(f"textile directory summary published: {rel}")

print("OOLITA textile regular + heavy oversized public copy and SEO complete.")
