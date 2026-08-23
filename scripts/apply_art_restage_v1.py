#!/usr/bin/env python3
"""Re-stage OOLITA as an authored contemporary-art website.

The project already has its visual language: the poster palette, paper, stone,
numbering and bilingual text. This final layer makes that language spatial.
It does not replace the site's content, routes, forms, SEO or release logic.
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
  --art-blue:#3F73E8;
  --art-blue-deep:#184EC8;
  --art-gold:#F5D64A;
  --art-coral:#EF725E;
  --art-paper:#F1E7D4;
  --art-sage:#5E9A70;
  --art-green:#2D4E23;
  --art-ink-blue:#132572;
}
html{scroll-behavior:auto}
body.art-restaged{background:var(--art-paper)}
body.art-restaged ::selection{background:var(--art-gold);color:var(--art-ink-blue)}
body.art-restaged img:not(.icon):not([width="1"]){border-radius:0!important}
body.art-restaged input,
body.art-restaged button,
body.art-restaged select,
body.art-restaged textarea{border-radius:0!important}
body.art-restaged .card,
body.art-restaged .tarjeta,
body.art-restaged .panel:not(.art-field),
body.art-restaged .ficha:not(form),
body.art-restaged .modulo{border-radius:0!important;box-shadow:none!important}
body.art-restaged .rot{letter-spacing:.12em}
body.art-restaged figure{margin-block:clamp(2.5rem,7vw,7rem)}
body.art-restaged figcaption{max-width:38rem;margin:.7rem 0 0 auto;font-size:.76rem;letter-spacing:.04em}

/* Interior pages inherit the material/editorial language without becoming a
   spectacle: larger headings, flat surfaces, more air, genuine images square. */
body.art-restaged:not(.art-home) h1{
  font-size:clamp(3.5rem,9vw,8rem)!important;
  line-height:.86!important;
  letter-spacing:-.04em!important;
  font-weight:500!important;
  max-width:12ch
}
body.art-restaged:not(.art-home) h2{
  font-size:clamp(2rem,4.8vw,4.6rem)!important;
  line-height:.98!important;
  letter-spacing:-.025em!important;
  max-width:16ch
}

/* Homepage: exhibition entrance rather than institutional index. */
body.art-home main{overflow:hidden}
body.art-home h1{
  font-size:clamp(6rem,21vw,18rem)!important;
  line-height:.70!important;
  letter-spacing:-.072em!important;
  font-weight:500!important;
  margin:.08em 0 .16em!important;
  max-width:none!important
}
body.art-home h2{
  font-size:clamp(3rem,7.7vw,7.8rem)!important;
  line-height:.90!important;
  letter-spacing:-.042em!important;
  max-width:11ch;
  text-wrap:balance
}
body.art-home .art-manifesto{
  max-width:12ch;
  margin:clamp(1rem,3vw,2.2rem) 0 clamp(2.5rem,7vw,6.5rem)!important;
  font-size:clamp(2.8rem,7.8vw,7.5rem)!important;
  line-height:.88!important;
  letter-spacing:-.04em!important;
  text-wrap:balance
}
body.art-home .art-manifesto.art-manifesto--echo{
  max-width:18ch;
  margin-left:min(34vw,24rem)!important;
  font-size:clamp(1.25rem,2.7vw,2.3rem)!important;
  line-height:1.05!important;
  letter-spacing:-.015em!important
}
body.art-home .art-context{
  max-width:38rem!important;
  font-size:clamp(.88rem,1.15vw,1rem)!important;
  line-height:1.5!important;
  letter-spacing:.01em
}
body.art-home main>section{margin-block:clamp(4rem,11vw,11rem)}

/* Full-bleed poster fields: colours come directly from the nine printed
   posters; the darker blue is the documented accessible screen step. */
body.art-home .art-field{
  position:relative;
  width:100vw;
  margin-inline:calc(50% - 50vw)!important;
  min-height:min(78vh,780px);
  display:grid;
  align-content:end;
  padding:clamp(2rem,6vw,6rem);
  box-sizing:border-box;
  overflow:hidden;
  isolation:isolate
}
body.art-home .art-field--blue{background:var(--art-blue-deep);color:var(--art-paper)}
body.art-home .art-field--gold{background:var(--art-gold);color:var(--art-ink-blue)}
body.art-home .art-field--coral{background:var(--art-coral);color:var(--art-ink-blue)}
body.art-home .art-kicker{
  position:absolute;
  top:clamp(1.25rem,3vw,2.5rem);
  left:clamp(1.25rem,4vw,4rem);
  z-index:2;
  font-size:.72rem;
  letter-spacing:.17em;
  text-transform:uppercase;
  font-weight:600
}
body.art-home .art-word{
  position:relative;
  z-index:2;
  margin:0;
  max-width:none;
  font-size:clamp(6rem,25vw,23rem);
  line-height:.62;
  letter-spacing:-.075em;
  font-weight:500
}
body.art-home .art-caption{
  position:relative;
  z-index:2;
  max-width:33rem;
  margin:clamp(1.2rem,3vw,2.2rem) 0 0 auto;
  font-size:clamp(1rem,1.5vw,1.25rem);
  line-height:1.45
}
body.art-home .art-field--stone{grid-template-columns:minmax(0,1fr) minmax(18rem,.92fr);gap:clamp(1.5rem,5vw,6rem)}
body.art-home .art-field--stone .art-copy{align-self:end;position:relative;z-index:2}
body.art-home .art-field-photo{
  position:absolute;
  inset:0 0 0 52%;
  width:48%;
  height:100%;
  object-fit:cover;
  object-position:center;
  margin:0!important;
  z-index:1
}
body.art-home .art-field--stone::after{
  content:"";
  position:absolute;
  inset:0 45% 0 0;
  background:linear-gradient(90deg,var(--art-blue-deep) 72%,rgba(24,78,200,0));
  z-index:1;
  pointer-events:none
}
body.art-home .art-field--stone .art-word{font-size:clamp(5.5rem,14vw,14rem)}

/* Existing primary navigation becomes three large poster-like thresholds. */
body.art-home a.fila{
  border-radius:0!important;
  box-shadow:none!important;
  padding-block:clamp(1.2rem,2.8vw,2.4rem)!important
}
body.art-home a.fila[href="/laberinto/"],
body.art-home a.fila[href="/en/labyrinth/"]{
  background:var(--art-blue-deep)!important;
  color:var(--art-paper)!important;
  margin-inline:calc(50% - 50vw);
  padding-inline:max(5vw,calc((100vw - 1180px)/2))!important
}
body.art-home a.fila[href="/domingos/"],
body.art-home a.fila[href="/en/sundays/"]{
  background:var(--art-gold)!important;
  color:var(--art-ink-blue)!important;
  margin-inline:calc(50% - 50vw);
  padding-inline:max(5vw,calc((100vw - 1180px)/2))!important
}
body.art-home a.fila[href="/cabo-de-gata/"],
body.art-home a.fila[href="/en/cabo-de-gata/"]{
  background:var(--art-coral)!important;
  color:var(--art-ink-blue)!important;
  margin-inline:calc(50% - 50vw);
  padding-inline:max(5vw,calc((100vw - 1180px)/2))!important
}
body.art-home a.fila .n{
  font-size:clamp(2.8rem,6.4vw,6.3rem)!important;
  line-height:.85!important;
  font-variant-numeric:tabular-nums
}
body.art-home .menu-group-label{
  margin-top:clamp(4rem,10vw,10rem)!important;
  margin-bottom:1rem!important;
  font-size:.67rem!important;
  letter-spacing:.17em!important;
  opacity:.72!important
}

/* Reading remains quiet, but no longer forms one institutional column. */
body.art-home p.parr{
  max-width:46rem;
  font-size:clamp(1.08rem,1.55vw,1.32rem);
  line-height:1.62
}
body.art-home p.parr:nth-of-type(3n+1){margin-left:min(10vw,8rem)}
body.art-home p.parr:nth-of-type(3n+2){margin-left:min(21vw,15rem)}

/* Existing bilingual excerpt and Sundays archive are allowed to occupy the
   viewport like works rather than widgets. */
body.art-restaged .oolita-book-excerpt,
body.art-restaged [class*="book-excerpt"]{
  border-radius:0!important;
  box-shadow:none!important
}
body.art-home .oolita-book-excerpt,
body.art-home [class*="book-excerpt"]{
  margin-inline:calc(50% - 50vw)!important;
  padding:clamp(3rem,7vw,7rem) max(5vw,calc((100vw - 1180px)/2))!important;
  background:var(--art-paper)!important;
  border-top:1px solid rgba(45,78,35,.35)!important;
  border-bottom:1px solid rgba(45,78,35,.35)!important
}
body.art-home .oolita-sunday-archive,
body.art-home [class*="sunday-archive"]{
  margin-inline:calc(50% - 50vw)!important;
  padding-inline:max(4vw,calc((100vw - 1280px)/2))!important
}

@media(max-width:760px){
  body.art-home h1{font-size:clamp(5.3rem,28vw,10rem)!important}
  body.art-home h2{font-size:clamp(2.7rem,13vw,5.2rem)!important}
  body.art-home .art-manifesto{font-size:clamp(2.5rem,13vw,5.2rem)!important}
  body.art-home .art-manifesto.art-manifesto--echo{margin-left:18vw!important}
  body.art-home .art-field{min-height:72svh;padding:1.35rem}
  body.art-home .art-field--stone{grid-template-columns:1fr;padding-top:48svh}
  body.art-home .art-field-photo{inset:0 0 auto 0;width:100%;height:45svh}
  body.art-home .art-field--stone::after{inset:30svh 0 auto 0;height:20svh;background:linear-gradient(180deg,rgba(24,78,200,0),var(--art-blue-deep))}
  body.art-home .art-field .art-word{font-size:clamp(5.5rem,32vw,11rem)}
  body.art-home .art-field--stone .art-word{font-size:clamp(4.6rem,24vw,8rem)}
  body.art-home p.parr:nth-of-type(n){margin-left:0}
}
@media(prefers-reduced-motion:reduce){*{scroll-behavior:auto!important;animation:none!important;transition:none!important}}
</style>'''


def read(rel: str) -> tuple[Path, str]:
    target = ROOT / rel
    if not target.is_file():
        raise SystemExit(f"Missing expected page for art restage: {rel}")
    return target, target.read_text(encoding="utf-8")


def add_class_to_tag(tag: str, class_name: str) -> str:
    match = re.search(r'class=["\']([^"\']*)["\']', tag, flags=re.I)
    if match:
        classes = match.group(1).split()
        if class_name in classes:
            return tag
        value = (match.group(1) + " " + class_name).strip()
        return tag[:match.start(1)] + value + tag[match.end(1):]
    return tag[:-1] + f' class="{class_name}">'


def mark_body(text: str, *, homepage: bool) -> str:
    match = re.search(r'<body\b[^>]*>', text, flags=re.I)
    if not match:
        raise SystemExit("Page has no <body>")
    tag = add_class_to_tag(match.group(0), "art-restaged")
    if homepage:
        tag = add_class_to_tag(tag, "art-home")
    return text[:match.start()] + tag + text[match.end():]


def inject_style(text: str) -> str:
    if 'id="oolita-art-restage-v1"' in text:
        return text
    if "</head>" not in text:
        raise SystemExit("Page has no </head>")
    return text.replace("</head>", STYLE + "\n</head>", 1)


def add_class_to_paragraph_containing(text: str, needle: str, class_name: str) -> str:
    pattern = re.compile(r'<p\b[^>]*>.*?</p>', flags=re.I | re.S)
    for match in pattern.finditer(text):
        block = match.group(0)
        plain = re.sub(r'<[^>]+>', '', block)
        if needle not in plain:
            continue
        opening = re.match(r'<p\b[^>]*>', block, flags=re.I)
        if not opening:
            continue
        new_open = add_class_to_tag(opening.group(0), class_name)
        new_block = new_open + block[opening.end():]
        return text[:match.start()] + new_block + text[match.end():]
    return text


def promote_manifesto(text: str, primary: str, echo: str) -> str:
    """Move the existing bilingual fable lines directly under the H1."""
    blocks: list[str] = []
    for needle, extra in ((primary, "art-manifesto"), (echo, "art-manifesto art-manifesto--echo")):
        pattern = re.compile(r'<p\b[^>]*>.*?</p>', flags=re.I | re.S)
        found = None
        for match in pattern.finditer(text):
            block = match.group(0)
            plain = re.sub(r'<[^>]+>', '', block).strip()
            if plain.rstrip('.') == needle.rstrip('.'):
                found = match
                break
        if not found:
            raise SystemExit(f"Could not find homepage manifesto line: {needle}")
        block = found.group(0)
        opening = re.match(r'<p\b[^>]*>', block, flags=re.I)
        if not opening:
            raise SystemExit(f"Malformed manifesto paragraph: {needle}")
        new_open = opening.group(0)
        for cls in extra.split():
            new_open = add_class_to_tag(new_open, cls)
        blocks.append(new_open + block[opening.end():])
        text = text[:found.start()] + text[found.end():]

    h1 = re.search(r'<h1\b[^>]*>.*?</h1>', text, flags=re.I | re.S)
    if not h1:
        raise SystemExit("Could not find homepage H1")
    insertion = "\n".join(blocks)
    return text[:h1.end()] + "\n" + insertion + text[h1.end():]


def insert_before_patterns(text: str, patterns: tuple[str, ...], block: str, label: str) -> str:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.I | re.S)
        if match:
            return text[:match.start()] + block + "\n" + text[match.start():]
    raise SystemExit(f"Could not place homepage art field: {label}")


def add_home_fields(text: str, *, en: bool) -> str:
    if 'id="oolita-art-field-stone"' in text:
        return text

    stone = (
        '<section id="oolita-art-field-stone" class="art-field art-field--blue art-field--stone" aria-label="Stone · Los Escullos">'
        '<img class="art-field-photo" src="/laberinto/laberinto-oolita-los-escullos.jpg" alt="The OOLITA stone labyrinth at Los Escullos" loading="lazy" decoding="async">'
        '<div class="art-copy"><span class="art-kicker">01 · Los Escullos</span><p class="art-word" aria-hidden="true">STONE</p>'
        '<p class="art-caption">The labyrinth is already there. Three metres. One path. No ticket, no sign, no booking.</p></div></section>'
        if en else
        '<section id="oolita-art-field-stone" class="art-field art-field--blue art-field--stone" aria-label="Piedra · Los Escullos">'
        '<img class="art-field-photo" src="/laberinto/laberinto-oolita-los-escullos.jpg" alt="El laberinto de piedra OOLITA en Los Escullos" loading="lazy" decoding="async">'
        '<div class="art-copy"><span class="art-kicker">01 · Los Escullos</span><p class="art-word" aria-hidden="true">PIEDRA</p>'
        '<p class="art-caption">El laberinto ya está allí. Tres metros. Un camino. Sin entrada, sin cartel, sin reserva.</p></div></section>'
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
        '<section id="oolita-art-field-paper" class="art-field art-field--coral" aria-label="Paper · bilingual book">'
        '<span class="art-kicker">PAPER · PAPEL</span><p class="art-word" aria-hidden="true">48</p>'
        '<p class="art-caption">Forty-eight pages. Spanish and English together. The same path carried onto paper.</p></section>'
        if en else
        '<section id="oolita-art-field-paper" class="art-field art-field--coral" aria-label="Papel · libro bilingüe">'
        '<span class="art-kicker">PAPEL · PAPER</span><p class="art-word" aria-hidden="true">48</p>'
        '<p class="art-caption">Cuarenta y ocho páginas. Español e inglés juntos. La misma senda llevada al papel.</p></section>'
    )

    text = insert_before_patterns(
        text,
        (
            r'<span\b[^>]*>\s*(?:El laberinto|The labyrinth)\s*</span>',
            r'<h2\b[^>]*>\s*Los Escullos\s*</h2>',
        ),
        stone,
        "stone",
    )
    text = insert_before_patterns(
        text,
        (
            r'<span\b[^>]*>\s*(?:22 domingos|22 Sundays)\s*</span>',
            r'<h2\b[^>]*>\s*(?:El mismo camino, hecho de luz\.?|The same path, made of light\.?)\s*</h2>',
        ),
        sunday,
        "22 Sundays",
    )
    text = insert_before_patterns(
        text,
        (
            r'<span\b[^>]*>\s*(?:Piedra · papel · código|Stone · paper · code)\s*</span>',
            r'<h2\b[^>]*>\s*(?:La misma senda en tres materiales\.?|The same path in three materials\.?)\s*</h2>',
        ),
        paper,
        "paper",
    )
    return text


def patch(rel: str, *, homepage: bool, en: bool) -> None:
    target, text = read(rel)
    text = inject_style(text)
    text = mark_body(text, homepage=homepage)
    if homepage:
        if en:
            text = promote_manifesto(text, "A labyrinth fable for loud days", "Una fábula de laberinto para días ruidosos")
            text = add_class_to_paragraph_containing(text, "place-based publishing and fieldwork project", "art-context")
            text = add_class_to_paragraph_containing(text, "publishing work of Vestini Tribe", "art-context")
        else:
            text = promote_manifesto(text, "Una fábula de laberinto para días ruidosos", "A labyrinth fable for loud days")
            text = add_class_to_paragraph_containing(text, "proyecto editorial y de trabajo de campo", "art-context")
            text = add_class_to_paragraph_containing(text, "labor editorial de Vestini Tribe", "art-context")
        text = add_home_fields(text, en=en)
    target.write_text(text, encoding="utf-8")


if not ROOT.is_dir():
    raise SystemExit(f"Missing built site: {ROOT}")

html_files = sorted(ROOT.rglob("*.html"))
if not html_files:
    raise SystemExit("No HTML pages found")
for html in html_files:
    rel = html.relative_to(ROOT).as_posix()
    patch(rel, homepage=rel in {"index.html", "en/index.html"}, en=rel.startswith("en/"))

# Invariants: the art direction is global, the homepage intervention is complete,
# and the primary links/content are still present.
for html in html_files:
    text = html.read_text(encoding="utf-8")
    if 'id="oolita-art-restage-v1"' not in text or "art-restaged" not in text:
        raise SystemExit(f"Art-restage layer incomplete: {html.relative_to(ROOT)}")

for rel, needles in {
    "index.html": [
        "art-home", 'id="oolita-art-field-stone"', 'id="oolita-art-field-sundays"', 'id="oolita-art-field-paper"',
        'class="art-manifesto"', 'href="/laberinto/"', 'href="/domingos/"', 'href="/cabo-de-gata/"',
        "#3F73E8", "#184EC8", "#F5D64A", "#EF725E", "#F1E7D4", "#5E9A70", "#2D4E23",
        "/laberinto/laberinto-oolita-los-escullos.jpg",
    ],
    "en/index.html": [
        "art-home", 'id="oolita-art-field-stone"', 'id="oolita-art-field-sundays"', 'id="oolita-art-field-paper"',
        'class="art-manifesto"', 'href="/en/labyrinth/"', 'href="/en/sundays/"', 'href="/en/cabo-de-gata/"',
        "/laberinto/laberinto-oolita-los-escullos.jpg",
    ],
}.items():
    _, text = read(rel)
    for needle in needles:
        if needle not in text:
            raise SystemExit(f"Art-restage invariant missing in {rel}: {needle}")

# Genuine photograph referenced by the homepage must exist in the built bundle.
photo = ROOT / "laberinto" / "laberinto-oolita-los-escullos.jpg"
if not photo.is_file() or photo.stat().st_size < 10000:
    raise SystemExit("Missing/invalid genuine labyrinth photograph for art restage")

# The two materially changed homepages get a fresh lastmod.
sitemap = ROOT / "sitemap.xml"
if not sitemap.is_file():
    raise SystemExit("Missing sitemap.xml")
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
