#!/usr/bin/env python3
"""Publish and enforce OOLITA's single first textile garment.

The first textile edition is Stanley/Stella Blaster 2.0 STTU959 only. This file
keeps its historical name because the deployment integrity gate already invokes
it, but it now acts as a fail-closed single-garment normalizer. It removes the
accidental RE-Creator option, removes pre-launch Product schema, cleans the
Editions summaries, and rejects any retired two-garment copy before deployment.
"""
from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")

PAGES = {
    "en/editions/t-shirt/index.html": {
        "canonical": "https://oolita.es/en/editions/t-shirt/",
        "title": "OOLITA T-shirt — Stanley/Stella Blaster 2.0 · OOLITA",
        "description": "OOLITA's first textile edition: white Stanley/Stella Blaster 2.0, 200 gsm organic cotton, oversized unisex fit. Made on demand.",
        "hero": "White Stanley/Stella Blaster 2.0, oversized unisex fit, without the design",
        "intro": "White, 200 gsm organic cotton, an oversized unisex fit. For now just the bare garment: the design is unveiled Sunday by Sunday, through to spring.",
        "heading": "Which garment.",
        "garment": "It is a Stanley/Stella Blaster 2.0, not a generic tee: 200 gsm single jersey in organic ring-spun combed cotton. Oversized unisex cut with dropped shoulders, side seams, an elastane-free 1x1 rib mock-neck collar, self-fabric back-neck tape and twin-needle stitching at cuffs and hem. Available from XXS to 3XL.",
        "credentials": "Stanley/Stella lists the Blaster 2.0 with GOTS and OEKO-TEX credentials. Stanley/Stella is a Fair Wear member and its products are listed as PETA-Approved Vegan.",
        "facts": {
            "Regular · RE-Creator STTU787 / Heavy Oversized · Blaster 2.0 STTU959": "Stanley/Stella Blaster 2.0",
            "Regular · 50% recycled cotton + 50% organic / Heavy · 100% organic combed cotton": "100% organic combed cotton",
            "Regular · 180 gsm / Heavy Oversized · 200 gsm": "200 gsm · 20 singles",
            "Regular · medium unisex / Heavy Oversized · dropped shoulders": "Oversized unisex · dropped shoulder",
            "Regular · 1x1 rib neckline / Heavy Oversized · mock-neck 1x1 rib": "Mock-neck, elastane-free 1x1 rib",
            "RE-Creator · GRS · OCS · OEKO-TEX · Fair Wear / Blaster 2.0 · GOTS · OEKO-TEX · Fair Wear": "GOTS · OEKO-TEX · Fair Wear member · PETA-Approved",
        },
        "double_title": "OOLITA T-shirt — regular and heavy oversized · OOLITA",
        "double_description": "OOLITA's first textile edition: 180 gsm Stanley/Stella RE-Creator regular or 200 gsm Blaster 2.0 heavy oversized. Made on demand.",
        "double_hero": "White Stanley/Stella Blaster 2.0, heavy oversized option, without the design",
        "double_intro": "White, one OOLITA design and two unisex cuts: a 180 gsm regular option and a 200 gsm heavy oversized option. Details and the story of the design will unfold Sunday by Sunday through to spring.",
        "double_heading": "Which garments.",
        "double_garment": "There are two Stanley/Stella choices. Regular is the RE-Creator STTU787: 180 gsm, medium fit, 50% recycled cotton and 50% organic cotton, made from Stanley/Stella's own organic cutting waste. Heavy Oversized is the Blaster 2.0 STTU959: 200 gsm, 100% organic ring-spun combed cotton, oversized with dropped shoulders and a 1x1 rib mock-neck collar. Both are unisex and available from XXS to 3XL.",
        "double_credentials": "Stanley/Stella lists the RE-Creator with GRS, OCS and OEKO-TEX credentials and the Blaster 2.0 with GOTS and OEKO-TEX; both product pages also show Fair Wear. The two options keep the same traceable-garment standard while giving a choice of weight and cut.",
    },
    "ediciones/camiseta/index.html": {
        "canonical": "https://oolita.es/ediciones/camiseta/",
        "title": "Camiseta OOLITA — Stanley/Stella Blaster 2.0 · OOLITA",
        "description": "Primera edición textil OOLITA: Stanley/Stella Blaster 2.0 blanca, 200 g/m² de algodón orgánico y corte oversized unisex. Bajo demanda.",
        "hero": "Camiseta blanca Stanley/Stella Blaster 2.0, corte oversized unisex, sin el diseño",
        "intro": "Blanca, de algodón orgánico de 200 g/m² y corte oversized unisex. Los detalles y la historia del diseño se irán contando domingo a domingo hasta la primavera.",
        "heading": "Qué prenda es.",
        "garment": "Es una Stanley/Stella Blaster 2.0, no una camiseta genérica: jersey sencillo de algodón orgánico peinado e hilado en anillo, 200 g/m². Corte oversized, manga montada, hombro caído, cuello alto de canalé 1x1, cinta interior del cuello y pespunte doble en puños y bajo. Disponible de XXS a 3XL.",
        "credentials": "Stanley/Stella muestra la Blaster 2.0 con certificaciones GOTS y OEKO-TEX. Stanley/Stella es miembro de Fair Wear y sus productos figuran como PETA-Approved Vegan.",
        "facts": {
            "Regular · RE-Creator STTU787 / Heavy Oversized · Blaster 2.0 STTU959": "Stanley/Stella Blaster 2.0",
            "Regular · 50% algodón reciclado + 50% orgánico / Heavy · 100% algodón orgánico peinado": "100 % algodón orgánico peinado",
            "Regular · 180 g/m² / Heavy Oversized · 200 g/m²": "200 g/m² · 20 singles",
            "Regular · corte medio unisex / Heavy Oversized · hombros caídos": "Oversized unisex · hombro caído",
            "Regular · cuello canalé 1x1 / Heavy Oversized · cuello alto canalé 1x1": "Alto, canalé 1x1 sin elastano",
            "RE-Creator · GRS · OCS · OEKO-TEX · Fair Wear / Blaster 2.0 · GOTS · OEKO-TEX · Fair Wear": "GOTS · OEKO-TEX · miembro de Fair Wear · PETA-Approved",
        },
        "double_title": "Camiseta OOLITA — regular y heavy oversized · OOLITA",
        "double_description": "Primera edición textil OOLITA: RE-Creator Stanley/Stella de 180 g/m² regular o Blaster 2.0 de 200 g/m² heavy oversized, bajo demanda.",
        "double_hero": "Camiseta blanca Stanley/Stella Blaster 2.0, opción heavy oversized, sin el diseño",
        "double_intro": "Blanca, un diseño OOLITA y dos cortes unisex: opción regular de 180 g/m² y opción heavy oversized de 200 g/m². Los detalles y la historia del diseño se irán contando domingo a domingo hasta la primavera.",
        "double_heading": "Qué prendas son.",
        "double_garment": "Hay dos opciones Stanley/Stella. Regular es la RE-Creator STTU787: 180 g/m², corte medio, 50% algodón reciclado y 50% algodón orgánico, fabricada con recortes de algodón orgánico de la propia marca. Heavy Oversized es la Blaster 2.0 STTU959: 200 g/m², 100% algodón orgánico peinado e hilado en anillo, corte oversized con hombros caídos y cuello alto de canalé 1x1. Ambas son unisex y están disponibles de XXS a 3XL.",
        "double_credentials": "Stanley/Stella muestra la RE-Creator con credenciales GRS, OCS y OEKO-TEX, y la Blaster 2.0 con GOTS y OEKO-TEX; las fichas de ambas prendas también muestran Fair Wear. Las dos opciones mantienen el mismo criterio de trazabilidad y permiten elegir gramaje y corte.",
    },
}

TAG_RE = re.compile(r"<[^>]+>")
SCRIPT_RE = re.compile(
    r"<script(?P<attrs>[^>]*)type=[\"']application/ld\+json[\"'](?P<attrs2>[^>]*)>(?P<body>[\s\S]*?)</script>",
    re.I,
)


def rendered(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(TAG_RE.sub(" ", value))).strip()


def literal(text: str, old: str, new: str) -> str:
    return text.replace(old, new) if old in text else text


def set_title(text: str, title: str) -> str:
    matches = re.findall(r"<title>[^<]*</title>", text, flags=re.I)
    if len(matches) != 1:
        raise SystemExit(f"Expected exactly one title tag, found {len(matches)}")
    return re.sub(r"<title>[^<]*</title>", f"<title>{title}</title>", text, count=1, flags=re.I)


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


def normalize_jsonld(text: str, cfg: dict, label: str) -> str:
    webpage_id = cfg["canonical"] + "#webpage"
    product_id = cfg["canonical"] + "#producto"
    webpage_found = 0
    product_removed = 0

    def patch(match: re.Match[str]) -> str:
        nonlocal webpage_found, product_removed
        body = html.unescape(match.group("body")).strip()
        try:
            obj = json.loads(body)
        except Exception:
            return match.group(0)
        if not isinstance(obj, dict):
            return match.group(0)
        obj_id = str(obj.get("@id", ""))
        if obj_id == product_id:
            product_removed += 1
            return ""
        if obj_id == webpage_id:
            webpage_found += 1
            obj["name"] = cfg["title"]
            obj["description"] = cfg["description"]
            return '<script type="application/ld+json">' + json.dumps(
                obj, ensure_ascii=False, separators=(",", ":")
            ) + "</script>"
        return match.group(0)

    result = SCRIPT_RE.sub(patch, text)
    if webpage_found != 1:
        raise SystemExit(f"{label}: expected one WebPage JSON-LD block, found {webpage_found}")
    if product_removed > 1:
        raise SystemExit(f"{label}: duplicated textile Product schema ({product_removed})")
    return result


def normalize_page(rel: str, cfg: dict) -> None:
    path = ROOT / rel
    if not path.is_file():
        raise SystemExit(f"Missing textile page: {rel}")
    text = path.read_text(encoding="utf-8")

    replacements = (
        (cfg["double_title"], cfg["title"]),
        (cfg["double_description"], cfg["description"]),
        (cfg["double_hero"], cfg["hero"]),
        (cfg["double_intro"], cfg["intro"]),
        (cfg["double_heading"], cfg["heading"]),
        (cfg["double_garment"], cfg["garment"]),
        (cfg["double_credentials"], cfg["credentials"]),
    )
    for old, new in replacements:
        text = literal(text, old, new)
    for old, new in cfg["facts"].items():
        text = literal(text, old, new)

    # Remove the accidental two-choice cards and their dedicated CSS if present.
    text = re.sub(
        r'<div class="textile-choice-grid"[^>]*data-oolita-textile-choices="v1"[^>]*>[\s\S]*?</div>\s*',
        "",
        text,
        flags=re.I,
    )
    text = re.sub(
        r'<style[^>]*data-oolita-textile-variants="v1"[^>]*>[\s\S]*?</style>\s*',
        "",
        text,
        flags=re.I,
    )

    # Accept and normalize closely related single-Blaster source states produced
    # by older editorial passes.
    if rel.startswith("en/"):
        text = re.sub(
            r"<h2([^>]*)>Which garments\.</h2>",
            r"<h2\1>Which garment.</h2>",
            text,
            flags=re.I,
        )
    else:
        text = re.sub(
            r"<h2([^>]*)>Qué prendas son\.</h2>",
            r"<h2\1>Qué prenda es.</h2>",
            text,
            flags=re.I,
        )

    text = set_title(text, cfg["title"])
    text = set_meta(text, "name", "description", cfg["description"])
    text = set_meta(text, "property", "og:title", cfg["title"], required=False)
    text = set_meta(text, "property", "og:description", cfg["description"], required=False)
    text = set_meta(text, "name", "twitter:title", cfg["title"], required=False)
    text = set_meta(text, "name", "twitter:description", cfg["description"], required=False)
    text = normalize_jsonld(text, cfg, rel)

    # Positive and negative page-level gates.
    visible = rendered(text)
    for required in ("Stanley/Stella Blaster 2.0", "200", "XXS", "3XL"):
        if required not in visible:
            raise SystemExit(f"Single-Blaster invariant missing in {rel}: {required}")
    retired = (
        "RE-Creator",
        "STTU787",
        "two unisex cuts",
        "dos cortes unisex",
        "There are two Stanley/Stella choices",
        "Hay dos opciones Stanley/Stella",
        "Regular · RE-Creator",
    )
    for needle in retired:
        if needle.casefold() in text.casefold():
            raise SystemExit(f"Retired textile straggler remains in {rel}: {needle}")

    # No Product/ProductGroup structured data is published while checkout and a
    # verified public offer are not live.
    for match in SCRIPT_RE.finditer(text):
        try:
            obj = json.loads(html.unescape(match.group("body")).strip())
        except Exception:
            continue
        serial = json.dumps(obj, ensure_ascii=False).lower()
        if '"@type": "product"' in serial or '"@type": "productgroup"' in serial:
            raise SystemExit(f"Pre-launch Product schema remains in {rel}")

    path.write_text(text, encoding="utf-8")
    print(f"single Blaster textile + prelaunch SEO normalized: {rel}")


if not ROOT.is_dir():
    raise SystemExit(f"Missing built site: {ROOT}")

for rel, cfg in PAGES.items():
    normalize_page(rel, cfg)

summaries = {
    "en/editions/index.html": (
        "White, two unisex cuts: 180 gsm regular or 200 gsm heavy oversized.",
        "White, 200 gsm organic cotton, an oversized unisex fit.",
    ),
    "ediciones/index.html": (
        "Blanca, dos cortes unisex: regular de 180 g/m² o heavy oversized de 200 g/m².",
        "Blanca, de algodón orgánico de 200 gramos, de corte oversized unisex.",
    ),
}
for rel, (old, new) in summaries.items():
    path = ROOT / rel
    if not path.is_file():
        raise SystemExit(f"Missing Editions directory: {rel}")
    text = path.read_text(encoding="utf-8")
    text = literal(text, old, new)
    if old in text:
        raise SystemExit(f"Retired two-garment summary remains in {rel}")
    if new not in text:
        raise SystemExit(f"Single-Blaster summary missing in {rel}")
    path.write_text(text, encoding="utf-8")
    print(f"single Blaster directory summary normalized: {rel}")

# The live canonical middleware intentionally redirects obsolete externally shared
# ?follow=3d URLs. Internal links must never point at those redirecting URLs.
for page in sorted(ROOT.rglob("*.html")):
    text = page.read_text(encoding="utf-8")
    updated = text.replace('/?follow=3d#seguir-oolita', '/#seguir-oolita')
    updated = updated.replace('/en/?follow=3d#follow-oolita', '/en/#follow-oolita')
    updated = updated.replace('https://oolita.es/?follow=3d#seguir-oolita', 'https://oolita.es/#seguir-oolita')
    updated = updated.replace('https://oolita.es/en/?follow=3d#follow-oolita', 'https://oolita.es/en/#follow-oolita')
    if updated != text:
        page.write_text(updated, encoding="utf-8")

# Final bundle-wide reader-facing straggler gate.
retired_sitewide = (
    "RE-Creator",
    "STTU787",
    "two unisex cuts",
    "dos cortes unisex",
    "regular and heavy oversized",
    "regular y heavy oversized",
    "?follow=3d",
)
stragglers: list[str] = []
for page in sorted(ROOT.rglob("*.html")):
    text = page.read_text(encoding="utf-8", errors="ignore")
    for needle in retired_sitewide:
        if needle.casefold() in text.casefold():
            stragglers.append(f"{page.relative_to(ROOT)}: {needle}")
if stragglers:
    raise SystemExit("Retired textile/redirect stragglers remain:\n  - " + "\n  - ".join(stragglers))

print("OOLITA single Blaster 2.0 textile source of truth enforced; retired textile and internal redirect stragglers absent.")
