#!/usr/bin/env python3
"""Re-stage OOLITA as an authored contemporary-art website.

This is deliberately a spatial/visual layer, not a content rewrite. It keeps the
existing bilingual copy, SEO, forms, navigation, analytics and release logic,
while changing how the pages occupy the screen: more scale, colour fields,
material presence and asymmetric rhythm; fewer institutional-looking boxes.
"""
from __future__ import annotations

from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
BASE = "https://oolita.es"
LASTMOD = "2026-08-23"

STYLE = r'''<style id="oolita-art-restage-v1">
:root{
  --art-blue:#3F73E8;--art-blue-deep:#184EC8;--art-gold:#F5D64A;
  --art-coral:#EF725E;--art-paper:#F1E7D4;--art-sage:#5E9A70;
  --art-green:#2D4E23;--art-ink-blue:#132572;
}
html{scroll-behavior:auto}
body{background:var(--art-paper)}
main>section,main>.bloque,main>.seccion,main>.section{position:relative}
body.art-restaged main{overflow:hidden}
body.art-restaged h1{
  font-size:clamp(5.5rem,20vw,18rem)!important;line-height:.72!important;
  letter-spacing:-.065em!important;font-weight:500!important;
  margin:.08em 0 .18em!important;max-width:none!important
}
body.art-restaged h2{
  font-size:clamp(2.7rem,7vw,7.5rem)!important;line-height:.91!important;
  letter-spacing:-.035em!important;max-width:12ch;text-wrap:balance
}
body.art-restaged .rot{letter-spacing:.13em}
body.art-restaged .art-field{
  position:relative;width:100%;min-height:min(78vh,760px);display:grid;
  align-content:end;padding:clamp(2rem,6vw,6rem);box-sizing:border-box;
  overflow:hidden;isolation:isolate
}
body.art-restaged .art-field--blue{background:var(--art-blue-deep);color:var(--art-paper)}
body.art-restaged .art-field--gold{background:var(--art-gold);color:var(--art-ink-blue)}
body.art-restaged .art-field--coral{background:var(--art-coral);color:var(--art-ink-blue)}
body.art-restaged .art-field--sage{background:var(--art-sage);color:var(--art-green)}
body.art-restaged .art-field--paper{background:var(--art-paper);color:var(--art-green)}
body.art-restaged .art-field .art-kicker{
  position:absolute;top:clamp(1.25rem,3vw,2.5rem);left:clamp(1.25rem,4vw,4rem);
  font-size:.72rem;letter-spacing:.16em;text-transform:uppercase;font-weight:600
}
body.art-restaged .art-field .art-word{
  font-size:clamp(6rem,25vw,23rem);line-height:.62;letter-spacing:-.075em;
  font-weight:500;margin:0;max-width:none
}
body.art-restaged .art-field .art-caption{
  max-width:34rem;margin:clamp(1.4rem,3vw,2.4rem) 0 0 auto;
  font-size:clamp(1rem,1.5vw,1.25rem);line-height:1.45
}
body.art-restaged img:not(.icon):not([width="1"]){border-radius:0!important}
body.art-restaged figure{margin:clamp(3rem,9vw,9rem) 0}
body.art-restaged figure img,body.art-restaged .foto img,body.art-restaged .imagen img,body.art-restaged .hero img{
  width:min(100%,1600px);max-height:88vh;object-fit:cover
}
body.art-restaged figcaption{
  max-width:36rem;margin:.75rem clamp(1rem,4vw,4rem) 0 auto;
  font-size:.76rem;letter-spacing:.045em
}
body.art-restaged .card,body.art-restaged .tarjeta,body.art-restaged .panel:not(.art-field),
body.art-restaged .ficha:not(form),body.art-restaged .modulo{
  border-radius:0!important;box-shadow:none!important
}
body.art-restaged a.fila{
  border-radius:0!important;box-shadow:none!important;
  padding-block:clamp(1rem,2vw,1.6rem)!important
}
body.art-restaged .menu-group-label{
  margin-top:clamp(3rem,8vw,8rem)!important;font-size:.68rem!important;
  letter-spacing:.16em!important;opacity:.72!important
}
body.art-restaged a.fila[href="/laberinto/"],body.art-restaged a.fila[href="/en/labyrinth/"]{
  background:var(--art-blue-deep)!important;color:var(--art-paper)!important;
  margin-inline:calc(50% - 50vw);padding-inline:max(5vw,calc((100vw - 1180px)/2))!important
}
body.art-restaged a.fila[href="/domingos/"],body.art-restaged a.fila[href="/en/sundays/"]{
  background:var(--art-gold)!important;color:var(--art-ink-blue)!important;
  margin-inline:calc(50% - 50vw);padding-inline:max(5vw,calc((100vw - 1180px)/2))!important
}
body.art-restaged a.fila[href="/cabo-de-gata/"],body.art-restaged a.fila[href="/en/cabo-de-gata/"]{
  background:var(--art-coral)!important;color:var(--art-ink-blue)!important;
  margin-inline:calc(50% - 50vw);padding-inline:max(5vw,calc((100vw - 1180px)/2))!important
}
body.art-restaged a.fila .n{
  font-size:clamp(2.4rem,6vw,6rem)!important;line-height:1!important;
  font-variant-numeric:tabular-nums
}
body.art-restaged p.parr{
  max-width:46rem;font-size:clamp(1.08rem,1.55vw,1.32rem);line-height:1.62
}
body.art-restaged p.parr:nth-of-type(3n+1){margin-left:min(12vw,9rem)}
body.art-restaged p.parr:nth-of-type(3n+2){margin-left:min(24vw,17rem)}
body.art-restaged .oolita-book-excerpt,body.art-restaged [class*="book-excerpt"]{
  margin-inline:calc(50% - 50vw)!important;
  padding:clamp(3rem,7vw,7rem) max(5vw,calc((100vw - 1180px)/2))!important;
  background:var(--art-paper)!important;
  border-top:1px solid rgba(45,78,35,.35)!important;border-bottom:1px solid rgba(45,78,35,.35)!important
}
body.art-restaged .oolita-sunday-archive,body.art-restaged [class*="sunday-archive"]{
  margin-inline:calc(50% - 50vw)!important;
  padding-inline:max(4vw,calc((100vw - 1280px)/2))!important
}
body.art-restaged input,body.art-restaged button,body.art-restaged select{border-radius:0!important}
@media(max-width:760px){
  body.art-restaged h1{font-size:clamp(5rem,27vw,9.5rem)!important}
  body.art-restaged h2{font-size:clamp(2.6rem,13vw,5rem)!important}
  body.art-restaged .art-field{min-height:70svh;padding:1.35rem}
  body.art-restaged .art-field .art-word{font-size:clamp(5.5rem,31vw,11rem)}
  body.art-restaged p.parr:nth-of-type(n){margin-left:0}
}
@media(prefers-reduced-motion:reduce){*{scroll-behavior:auto!important;animation:none!important;transition:none!important}}
</style>'''


def read(rel: str) -> tuple[Path, str]:
    p = ROOT / rel
    if not p.is_file():
        raise SystemExit(f"Missing expected page for art restage: {rel}")
    return p, p.read_text(encoding="utf-8")


def inject_style(text: str) -> str:
    if 'id="oolita-art-restage-v1"' in text:
        return text
    if "</head>" not in text:
        raise SystemExit("Page has no </head>")
    return text.replace("</head>", STYLE + "\n</head>", 1)


def mark_body(text: str) -> str:
    m = re.search(r'<body\b([^>]*)>', text, flags=re.I)
    if not m:
        raise SystemExit("Page has no <body>")
    attrs = m.group(1)
    cm = re.search(r'class=["\']([^"\']*)["\']', attrs, flags=re.I)
    if cm:
        classes = cm.group(1).split()
        if "art-restaged" in classes:
            return text
        newattrs = attrs[:cm.start(1)] + (cm.group(1) + " art-restaged").strip() + attrs[cm.end(1):]
    else:
        newattrs = attrs + ' class="art-restaged"'
    return text[:m.start()] + '<body' + newattrs + '>' + text[m.end():]


def add_home_fields(text: str, *, en: bool) -> str:
    if 'id="oolita-art-field-stone"' in text:
        return text
    stone = (
        '<section id="oolita-art-field-stone" class="art-field art-field--blue" aria-label="Stone · Los Escullos">'
        '<span class="art-kicker">01 · Los Escullos</span><p class="art-word" aria-hidden="true">STONE</p>'
        '<p class="art-caption">The labyrinth is already there. Three metres. One path. No ticket, no sign, no booking.</p></section>'
        if en else
        '<section id="oolita-art-field-stone" class="art-field art-field--blue" aria-label="Piedra · Los Escullos">'
        '<span class="art-kicker">01 · Los Escullos</span><p class="art-word" aria-hidden="true">PIEDRA</p>'
        '<p class="art-caption">El laberinto ya está allí. Tres metros. Un camino. Sin entrada, sin cartel, sin reserva.</p></section>'
    )
    sunday = (
        '<section id="oolita-art-field-sundays" class="art-field art-field--gold" aria-label="22 Sundays">'
        '<span class="art-kicker">02 · 22 Sundays</span><p class="art-word" aria-hidden="true">22</p>'
        '<p class="art-caption">One image each Sunday. The work accumulates until the digital path opens.</p></section>'
        if en else
        '<section id="oolita-art-field-sundays" class="art-field art-field--gold" aria-label="22 domingos">'
        '<span class="art-kicker">02 · 22 domingos</span><p class="art-word" aria-hidden="true">22</p>'
        '<p class="art-caption">Una imagen cada domingo. La obra se acumula hasta que se abra el camino digital.</p></section>'
    )
    paper = (
        '<section id="oolita-art-field-paper" class="art-field art-field--coral" aria-label="Paper · the bilingual book">'
        '<span class="art-kicker">PAPER · PAPEL</span><p class="art-word" aria-hidden="true">48</p>'
        '<p class="art-caption">Forty-eight pages. Spanish and English together. The same path, carried onto paper.</p></section>'
        if en else
        '<section id="oolita-art-field-paper" class="art-field art-field--coral" aria-label="Papel · el libro bilingüe">'
        '<span class="art-kicker">PAPEL · PAPER</span><p class="art-word" aria-hidden="true">48</p>'
        '<p class="art-caption">Cuarenta y ocho páginas. Español e inglés juntos. La misma senda, llevada al papel.</p></section>'
    )
    anchors = [
        (r'(<span\b[^>]*class=["\']rot["\'][^>]*>\s*(?:El laberinto|The labyrinth)\s*</span>)', stone),
        (r'(<span\b[^>]*class=["\']rot["\'][^>]*>\s*(?:22 domingos|22 Sundays)\s*</span>)', sunday),
        (r'(<span\b[^>]*class=["\']rot["\'][^>]*>\s*(?:Piedra · papel · código|Stone · paper · code)\s*</span>)', paper),
    ]
    for pattern, block in anchors:
        m = re.search(pattern, text, flags=re.I)
        if not m:
            raise SystemExit(f"Could not place homepage art field for pattern: {pattern}")
        text = text[:m.start()] + block + "\n" + text[m.start():]
    return text


def patch(rel: str, *, homepage: bool = False, en: bool = False) -> None:
    p, text = read(rel)
    text = inject_style(text)
    text = mark_body(text)
    if homepage:
        text = add_home_fields(text, en=en)
    p.write_text(text, encoding="utf-8")


if not ROOT.is_dir():
    raise SystemExit(f"Missing built site: {ROOT}")
html_files = sorted(ROOT.rglob("*.html"))
if not html_files:
    raise SystemExit("No HTML pages found")
for html in html_files:
    rel = html.relative_to(ROOT).as_posix()
    patch(rel, homepage=rel in {"index.html", "en/index.html"}, en=rel.startswith("en/"))

for rel, needles in {
    "index.html": [
        'id="oolita-art-restage-v1"','id="oolita-art-field-stone"','id="oolita-art-field-sundays"',
        'id="oolita-art-field-paper"','href="/laberinto/"','href="/domingos/"','href="/cabo-de-gata/"',
        "#3F73E8","#F5D64A","#EF725E","#F1E7D4","#5E9A70","#2D4E23",
    ],
    "en/index.html": [
        'id="oolita-art-restage-v1"','id="oolita-art-field-stone"','id="oolita-art-field-sundays"',
        'id="oolita-art-field-paper"','href="/en/labyrinth/"','href="/en/sundays/"','href="/en/cabo-de-gata/"',
    ],
}.items():
    _, text = read(rel)
    for needle in needles:
        if needle not in text:
            raise SystemExit(f"Art-restage invariant missing in {rel}: {needle}")
for html in html_files:
    text = html.read_text(encoding="utf-8")
    if 'id="oolita-art-restage-v1"' not in text or "art-restaged" not in text:
        raise SystemExit(f"Art-restage layer incomplete: {html.relative_to(ROOT)}")

sitemap = ROOT / "sitemap.xml"
if sitemap.is_file():
    ET.register_namespace("", "http://www.sitemaps.org/schemas/sitemap/0.9")
    tree = ET.parse(sitemap)
    root = tree.getroot()
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    wanted = {"/", "/en/"}
    seen: set[str] = set()
    for url_el in root.findall("sm:url", ns):
        loc = url_el.find("sm:loc", ns)
        if loc is None or not loc.text or not loc.text.startswith(BASE):
            continue
        route = loc.text[len(BASE):] or "/"
        if route not in wanted:
            continue
        seen.add(route)
        lastmod = url_el.find("sm:lastmod", ns)
        if lastmod is None:
            lastmod = ET.SubElement(url_el, "{http://www.sitemaps.org/schemas/sitemap/0.9}lastmod")
        lastmod.text = LASTMOD
    if seen != wanted:
        raise SystemExit(f"Art-restage homepage URLs missing from sitemap: {sorted(wanted-seen)}")
    tree.write(sitemap, encoding="utf-8", xml_declaration=True)

print(f"OOLITA contemporary-art restage validated across {len(html_files)} HTML pages.")
