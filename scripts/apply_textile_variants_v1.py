#!/usr/bin/env python3
"""Publish both garment choices for OOLITA's first textile edition.

Applied at the final integrity gate. No price is exposed and no checkout is enabled.
"""
from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
STYLE_MARKER = 'data-oolita-textile-variants="v1"'
CHOICE_MARKER = 'data-oolita-textile-choices="v1"'
SCHEMA_MARKER = 'data-oolita-textile-product-schema="v1"'

PAGES = {
    "en/editions/t-shirt/index.html": {
        "canonical": "https://oolita.es/en/editions/t-shirt/",
        "title": "OOLITA T-shirt — regular and heavy oversized · OOLITA",
        "description": "OOLITA's first textile edition: 180 gsm Stanley/Stella RE-Creator regular or 200 gsm Blaster 2.0 heavy oversized. Made on demand.",
        "hero_fragments": ("Blaster 2.0", "oversized", "design"),
        "hero_new": "White Stanley/Stella Blaster 2.0, heavy oversized option, without the design",
        "intro_fragments": ("200 gsm", "oversized", "spring"),
        "intro_new": "White, one OOLITA design and two unisex cuts: a 180 gsm regular option and a 200 gsm heavy oversized option. Details and the story of the design will unfold Sunday by Sunday through to spring.",
        "garment_heading_fragments": ("which", "garment"),
        "garment_heading_new": "Which garments.",
        "garment_fragments": ("Stanley/Stella Blaster 2.0", "200 gsm", "dropped shoulder"),
        "garment_new": "There are two Stanley/Stella choices. Regular is the RE-Creator STTU787: 180 gsm, medium fit, 50% recycled cotton and 50% organic cotton, made from Stanley/Stella's own organic cutting waste. Heavy Oversized is the Blaster 2.0 STTU959: 200 gsm, 100% organic ring-spun combed cotton, oversized with dropped shoulders and a 1x1 rib mock-neck collar. Both are unisex and available from XXS to 3XL.",
        "credentials_fragments": ("Blaster 2.0", "GOTS", "OEKO-TEX", "Fair Wear"),
        "credentials_new": "Stanley/Stella lists the RE-Creator with GRS, OCS and OEKO-TEX credentials and the Blaster 2.0 with GOTS and OEKO-TEX; both product pages also show Fair Wear. The two options keep the same traceable-garment standard while giving a choice of weight and cut.",
        "story_heading_fragments": ("why", "story", "slow"),
        "cards": '<div class="textile-choice-grid" data-oolita-textile-choices="v1"><article class="textile-choice"><p class="textile-choice-kicker">REGULAR</p><h3>Stanley/Stella RE-Creator</h3><p>STTU787 · 180 gsm · medium unisex fit</p><p>50% recycled cotton · 50% organic cotton · 1x1 rib neckline · XXS–3XL</p></article><article class="textile-choice"><p class="textile-choice-kicker">HEAVY OVERSIZED</p><h3>Stanley/Stella Blaster 2.0</h3><p>STTU959 · 200 gsm · oversized unisex fit</p><p>100% organic combed cotton · dropped shoulders · mock neck · XXS–3XL</p></article></div>',
        "specs": {
            "Stanley/Stella Blaster 2.0": "Regular · RE-Creator STTU787 / Heavy Oversized · Blaster 2.0 STTU959",
            "100% organic combed cotton": "Regular · 50% recycled cotton + 50% organic / Heavy · 100% organic combed cotton",
            "200 gsm · 20 singles": "Regular · 180 gsm / Heavy Oversized · 200 gsm",
            "Oversized unisex · dropped shoulder": "Regular · medium unisex / Heavy Oversized · dropped shoulders",
            "Mock-neck, elastane-free 1x1 rib": "Regular · 1x1 rib neckline / Heavy Oversized · mock-neck 1x1 rib",
            "GOTS · OEKO-TEX · Fair Wear member · PETA-Approved": "RE-Creator · GRS · OCS · OEKO-TEX · Fair Wear / Blaster 2.0 · GOTS · OEKO-TEX · Fair Wear",
        },
        "schema_name": "OOLITA first textile edition",
    },
    "ediciones/camiseta/index.html": {
        "canonical": "https://oolita.es/ediciones/camiseta/",
        "title": "Camiseta OOLITA — regular y heavy oversized · OOLITA",
        "description": "Primera edición textil OOLITA: RE-Creator Stanley/Stella de 180 g/m² regular o Blaster 2.0 de 200 g/m² heavy oversized, bajo demanda.",
        "hero_fragments": ("Blaster 2.0", "oversized", "diseño"),
        "hero_new": "Camiseta blanca Stanley/Stella Blaster 2.0, opción heavy oversized, sin el diseño",
        "intro_fragments": ("200 g/m²", "oversized", "primavera"),
        "intro_new": "Blanca, un diseño OOLITA y dos cortes unisex: opción regular de 180 g/m² y opción heavy oversized de 200 g/m². Los detalles y la historia del diseño se irán contando domingo a domingo hasta la primavera.",
        "garment_heading_fragments": ("qué", "prenda"),
        "garment_heading_new": "Qué prendas son.",
        "garment_fragments": ("Stanley/Stella Blaster 2.0", "200 g/m²", "hombro caído"),
        "garment_new": "Hay dos opciones Stanley/Stella. Regular es la RE-Creator STTU787: 180 g/m², corte medio, 50% algodón reciclado y 50% algodón orgánico, fabricada con recortes de algodón orgánico de la propia marca. Heavy Oversized es la Blaster 2.0 STTU959: 200 g/m², 100% algodón orgánico peinado e hilado en anillo, corte oversized con hombros caídos y cuello alto de canalé 1x1. Ambas son unisex y están disponibles de XXS a 3XL.",
        "credentials_fragments": ("Blaster 2.0", "GOTS", "OEKO-TEX", "Fair Wear"),
        "credentials_new": "Stanley/Stella muestra la RE-Creator con credenciales GRS, OCS y OEKO-TEX, y la Blaster 2.0 con GOTS y OEKO-TEX; las fichas de ambas prendas también muestran Fair Wear. Las dos opciones mantienen el mismo criterio de trazabilidad y permiten elegir gramaje y corte.",
        "story_heading_fragments": ("por qué", "despacio"),
        "cards": '<div class="textile-choice-grid" data-oolita-textile-choices="v1"><article class="textile-choice"><p class="textile-choice-kicker">REGULAR</p><h3>Stanley/Stella RE-Creator</h3><p>STTU787 · 180 g/m² · corte medio unisex</p><p>50% algodón reciclado · 50% algodón orgánico · cuello canalé 1x1 · XXS–3XL</p></article><article class="textile-choice"><p class="textile-choice-kicker">HEAVY OVERSIZED</p><h3>Stanley/Stella Blaster 2.0</h3><p>STTU959 · 200 g/m² · corte oversized unisex</p><p>100% algodón orgánico peinado · hombros caídos · cuello alto · XXS–3XL</p></article></div>',
        "specs": {
            "Stanley/Stella Blaster 2.0": "Regular · RE-Creator STTU787 / Heavy Oversized · Blaster 2.0 STTU959",
            "100 % algodón orgánico peinado": "Regular · 50% algodón reciclado + 50% orgánico / Heavy · 100% algodón orgánico peinado",
            "200 g/m² · 20 singles": "Regular · 180 g/m² / Heavy Oversized · 200 g/m²",
            "Oversized unisex · hombro caído": "Regular · corte medio unisex / Heavy Oversized · hombros caídos",
            "Alto, canalé 1x1 sin elastano": "Regular · cuello canalé 1x1 / Heavy Oversized · cuello alto canalé 1x1",
            "GOTS · OEKO-TEX · miembro de Fair Wear · PETA-Approved": "RE-Creator · GRS · OCS · OEKO-TEX · Fair Wear / Blaster 2.0 · GOTS · OEKO-TEX · Fair Wear",
        },
        "schema_name": "Primera edición textil OOLITA",
    },
}

STYLE = """<style data-oolita-textile-variants="v1">
.textile-choice-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:0;border-top:1px solid currentColor;border-bottom:1px solid currentColor;margin:1.75rem 0 2.25rem}.textile-choice{padding:1.2rem 1.25rem 1.25rem 0}.textile-choice+.textile-choice{border-left:1px solid currentColor;padding-left:1.25rem}.textile-choice h3{margin:.2rem 0 .55rem}.textile-choice p{margin:.35rem 0}.textile-choice-kicker{font-size:.75em;letter-spacing:.12em}.textile-choice-grid p:not(.textile-choice-kicker){opacity:.82}@media(max-width:700px){.textile-choice-grid{grid-template-columns:1fr}.textile-choice{padding:1rem 0}.textile-choice+.textile-choice{border-left:0;border-top:1px solid currentColor;padding-left:0}}
</style>"""

TAG_RE = re.compile(r"<[^>]+>")

def rendered(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(TAG_RE.sub(" ", value))).strip()


def contains_all(value: str, fragments: tuple[str, ...]) -> bool:
    low = value.casefold()
    return all(fragment.casefold() in low for fragment in fragments)


def replace_element(text: str, tag: str, fragments: tuple[str, ...], new: str, label: str) -> str:
    if new in text:
        return text
    pattern = re.compile(rf"<(?P<tag>{re.escape(tag)})\b(?P<attrs>[^>]*)>(?P<body>[\s\S]*?)</(?P=tag)>", re.I)
    matches = [m for m in pattern.finditer(text) if contains_all(rendered(m.group("body")), fragments)]
    if len(matches) != 1:
        raise SystemExit(f"{label}: expected one semantic match for {fragments!r}, found {len(matches)}")
    m = matches[0]
    replacement = f"<{m.group('tag')}{m.group('attrs')}>{new}</{m.group('tag')}>"
    return text[:m.start()] + replacement + text[m.end():]


def replace_fact_value(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    pattern = re.compile(r"<span\b(?P<attrs>[^>]*)>(?P<body>[\s\S]*?)</span>", re.I)
    matches = [m for m in pattern.finditer(text) if re.search(r"\bclass=[\"'][^\"']*\bv\b[^\"']*[\"']", m.group("attrs"), re.I) and rendered(m.group("body")) == old]
    if len(matches) != 1:
        raise SystemExit(f"{label}: expected one fact value {old!r}, found {len(matches)}")
    m = matches[0]
    return text[:m.start()] + f"<span{m.group('attrs')}>{new}</span>" + text[m.end():]


def replace_img_alt(text: str, fragments: tuple[str, ...], new: str, label: str) -> str:
    if new in text:
        return text
    pattern = re.compile(r"<img\b[^>]*\balt=(?P<q>[\"'])(?P<alt>.*?)(?P=q)[^>]*>", re.I | re.S)
    matches = [m for m in pattern.finditer(text) if contains_all(html.unescape(m.group("alt")), fragments)]
    if len(matches) != 1:
        raise SystemExit(f"{label}: expected one image alt match, found {len(matches)}")
    m = matches[0]
    tag = re.sub(r"\balt=([\"']).*?\1", lambda x: f'alt={x.group(1)}{new}{x.group(1)}', m.group(0), count=1, flags=re.I | re.S)
    return text[:m.start()] + tag + text[m.end():]


def insert_before_heading(text: str, fragments: tuple[str, ...], block: str, label: str) -> str:
    if CHOICE_MARKER in text:
        return text
    pattern = re.compile(r"<h2\b[^>]*>[\s\S]*?</h2>", re.I)
    matches = [m for m in pattern.finditer(text) if contains_all(rendered(m.group(0)), fragments)]
    if len(matches) != 1:
        raise SystemExit(f"{label}: expected one story heading, found {len(matches)}")
    m = matches[0]
    return text[:m.start()] + block + "\n" + text[m.start():]


def set_title(text: str, title: str) -> str:
    pattern = re.compile(r"<title>[^<]*</title>", re.I)
    if len(pattern.findall(text)) != 1:
        raise SystemExit("Expected exactly one title tag")
    return pattern.sub(f"<title>{title}</title>", text, count=1)


def set_meta(text: str, attr: str, value: str, content: str, required: bool = True) -> str:
    tag_re = re.compile(r"<meta\b[^>]*>", re.I)
    matched = 0
    def patch(m: re.Match[str]) -> str:
        nonlocal matched
        tag = m.group(0)
        if not re.search(rf"\b{re.escape(attr)}=[\"']{re.escape(value)}[\"']", tag, re.I):
            return tag
        matched += 1
        if re.search(r"\bcontent=([\"'])[^\"']*\1", tag, re.I):
            return re.sub(r"\bcontent=([\"'])[^\"']*\1", lambda x: f"content={x.group(1)}{content}{x.group(1)}", tag, count=1, flags=re.I)
        return tag[:-1] + f' content="{content}">'
    result = tag_re.sub(patch, text)
    if required and matched != 1:
        raise SystemExit(f"Expected one meta {attr}={value}, found {matched}")
    if not required and matched > 1:
        raise SystemExit(f"Expected at most one meta {attr}={value}, found {matched}")
    return result


def product_variants() -> list[dict]:
    return [
        {"@type": "Product", "name": "OOLITA Regular", "sku": "OOLITA-UK-REGULAR-WHITE", "model": "Stanley/Stella RE-Creator STTU787", "material": "50% recycled cotton, 50% organic cotton", "size": "XXS–3XL", "color": "White"},
        {"@type": "Product", "name": "OOLITA Heavy Oversized", "sku": "OOLITA-UK-OVERSIZED-WHITE", "model": "Stanley/Stella Blaster 2.0 STTU959", "material": "100% organic ring-spun combed cotton", "size": "XXS–3XL", "color": "White"},
    ]


def update_jsonld(text: str, cfg: dict, label: str) -> str:
    script_re = re.compile(r"<script(?P<attrs>[^>]*)type=[\"']application/ld\+json[\"'](?P<attrs2>[^>]*)>(?P<body>[\s\S]*?)</script>", re.I)
    webpage_id = cfg["canonical"] + "#webpage"
    product_id = cfg["canonical"] + "#producto"
    found_page = 0
    found_product = 0

    def patch(m: re.Match[str]) -> str:
        nonlocal found_page, found_product
        try:
            obj = json.loads(html.unescape(m.group("body")).strip())
        except Exception:
            return m.group(0)
        if not isinstance(obj, dict):
            return m.group(0)
        obj_id = obj.get("@id")
        marker = ""
        if obj_id == webpage_id:
            found_page += 1
            obj["name"] = cfg["title"]
            obj["description"] = cfg["description"]
        elif obj_id == product_id:
            found_product += 1
            obj["@type"] = "ProductGroup"
            obj["name"] = cfg["schema_name"]
            obj["description"] = cfg["description"]
            obj["releaseDate"] = "2027-04-11"
            obj["brand"] = {"@type": "Brand", "name": "OOLITA"}
            obj["color"] = "White"
            obj["productGroupID"] = "oolita-textile-01"
            obj["hasVariant"] = product_variants()
            marker = ' data-oolita-textile-product-schema="v1"'
        else:
            return m.group(0)
        return f'<script type="application/ld+json"{marker}>' + json.dumps(obj, ensure_ascii=False, separators=(",", ":")) + "</script>"

    result = script_re.sub(patch, text)
    if found_page != 1 or found_product != 1:
        raise SystemExit(f"{label}: expected one WebPage and one textile product JSON-LD block; found {found_page}/{found_product}")
    return result


if not ROOT.is_dir():
    raise SystemExit(f"Missing built site: {ROOT}")

for rel, cfg in PAGES.items():
    path = ROOT / rel
    if not path.is_file():
        raise SystemExit(f"Missing textile page: {rel}")
    text = path.read_text(encoding="utf-8")

    text = replace_img_alt(text, cfg["hero_fragments"], cfg["hero_new"], rel + " hero")
    text = replace_element(text, "p", cfg["intro_fragments"], cfg["intro_new"], rel + " intro")
    text = replace_element(text, "h2", cfg["garment_heading_fragments"], cfg["garment_heading_new"], rel + " garment heading")
    text = replace_element(text, "p", cfg["garment_fragments"], cfg["garment_new"], rel + " garment copy")
    text = replace_element(text, "p", cfg["credentials_fragments"], cfg["credentials_new"], rel + " credentials")
    for old, new in cfg["specs"].items():
        text = replace_fact_value(text, old, new, rel + " fact table")
    text = insert_before_heading(text, cfg["story_heading_fragments"], cfg["cards"], rel + " choices")

    if STYLE_MARKER not in text:
        if "</head>" not in text:
            raise SystemExit(f"Missing </head> in {rel}")
        text = text.replace("</head>", STYLE + "\n</head>", 1)

    text = set_title(text, cfg["title"])
    text = set_meta(text, "name", "description", cfg["description"])
    text = set_meta(text, "property", "og:title", cfg["title"], False)
    text = set_meta(text, "property", "og:description", cfg["description"], False)
    text = set_meta(text, "name", "twitter:title", cfg["title"], False)
    text = set_meta(text, "name", "twitter:description", cfg["description"], False)
    text = update_jsonld(text, cfg, rel)

    if len(cfg["description"]) > 160:
        raise SystemExit(f"Meta description exceeds 160 characters: {rel}")
    for needle in ("RE-Creator STTU787", "Blaster 2.0 STTU959", CHOICE_MARKER, SCHEMA_MARKER, "2027-04-11"):
        if needle not in text:
            raise SystemExit(f"Missing textile marker {needle!r} in {rel}")
    path.write_text(text, encoding="utf-8")
    print(f"textile variants + SEO published: {rel}")

summaries = {
    "en/editions/index.html": ("White, 200 gsm organic cotton, an oversized unisex fit.", "White, two unisex cuts: 180 gsm regular or 200 gsm heavy oversized."),
    "ediciones/index.html": ("Blanca, de algodón orgánico de 200 gramos, de corte oversized unisex.", "Blanca, dos cortes unisex: regular de 180 g/m² o heavy oversized de 200 g/m²."),
}
for rel, (old, new) in summaries.items():
    path = ROOT / rel
    if not path.is_file():
        raise SystemExit(f"Missing Editions directory: {rel}")
    text = path.read_text(encoding="utf-8")
    if new not in text:
        count = text.count(old)
        if count != 1:
            raise SystemExit(f"{rel} textile summary: expected one exact source string, found {count}")
        text = text.replace(old, new, 1)
        path.write_text(text, encoding="utf-8")
    print(f"textile directory summary published: {rel}")

print("OOLITA textile regular + heavy oversized public copy and SEO complete.")