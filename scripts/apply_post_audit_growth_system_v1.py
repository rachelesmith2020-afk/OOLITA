#!/usr/bin/env python3
"""Lock approved copy, map primary actions, instrument reader journeys and stage launches.

This post-audit layer changes attributes, spacing and launch-state markers only.
It does not rewrite authored project prose.
"""
from __future__ import annotations

from datetime import datetime
from html import unescape
from pathlib import Path
from zoneinfo import ZoneInfo
import os
import re
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
TZ = ZoneInfo("Europe/Madrid")
STYLE_ID = "oolita-reader-pacing-v1"
STATE_ID = "oolita-launch-state-v1"


def read(rel: str) -> tuple[Path, str]:
    p = ROOT / rel
    if not p.is_file():
        raise SystemExit(f"Missing post-audit page: {rel}")
    return p, p.read_text(encoding="utf-8")


def visible(fragment: str) -> str:
    text = unescape(re.sub(r"<[^>]+>", " ", fragment))
    return re.sub(r"\s+", " ", text).strip()


def set_attr(tag: str, name: str, value: str) -> str:
    pattern = re.compile(rf'\s{name}=(["\']).*?\1', re.I | re.S)
    if pattern.search(tag):
        return pattern.sub(f' {name}="{value}"', tag, count=1)
    return tag[:-1] + f' {name}="{value}">'


def remove_attr(text: str, name: str) -> str:
    return re.sub(rf'\s{name}=(["\']).*?\1', "", text, flags=re.I | re.S)


def mark_link(rel: str, *, event: str, href_exact: str | None = None,
              href_contains: str | None = None, text_contains: str | None = None,
              primary: bool = False, journey: str | None = None, pick: int = 0) -> None:
    p, text = read(rel)
    matches = []
    pat = re.compile(r'(?P<open><a\b[^>]*>)(?P<body>[\s\S]*?)</a>', re.I)
    for m in pat.finditer(text):
        open_tag = m.group("open")
        href_m = re.search(r'\bhref=(["\'])(.*?)\1', open_tag, re.I | re.S)
        href = href_m.group(2) if href_m else ""
        label = visible(m.group("body"))
        if href_exact is not None and href != href_exact:
            continue
        if href_contains is not None and href_contains not in href:
            continue
        if text_contains is not None and text_contains not in label:
            continue
        matches.append(m)
    if len(matches) <= pick:
        raise SystemExit(f"Could not mark {event} in {rel}: matches={len(matches)}")
    m = matches[pick]
    opening = set_attr(m.group("open"), "data-oolita-event", event)
    if primary:
        opening = set_attr(opening, "data-primary-action", "true")
    if journey:
        opening = set_attr(opening, "data-reader-journey", journey)
    replacement = opening + m.group("body") + "</a>"
    p.write_text(text[:m.start()] + replacement + text[m.end():], encoding="utf-8")


def add_page_meta(rel: str, purpose: str, primary_event: str) -> None:
    p, text = read(rel)
    text = remove_attr(text, "data-primary-action")
    main = re.search(r"<main\b[^>]*>", text, re.I)
    if not main:
        raise SystemExit(f"Missing <main> in {rel}")
    tag = set_attr(main.group(0), "data-page-purpose", purpose)
    tag = set_attr(tag, "data-primary-event", primary_event)
    p.write_text(text[:main.start()] + tag + text[main.end():], encoding="utf-8")


def mark_section_by_text(rel: str, needle: str, class_name: str) -> None:
    p, text = read(rel)
    section_re = re.compile(r"<section\b[^>]*>[\s\S]*?</section>", re.I)
    hits = [m for m in section_re.finditer(text) if needle in visible(m.group(0))]
    if not hits:
        raise SystemExit(f"Pacing section not found in {rel}: {needle}")
    m = hits[0]
    block = m.group(0)
    opening = re.match(r"<section\b[^>]*>", block, re.I)
    tag = opening.group(0)
    cls_m = re.search(r'class=(["\'])(.*?)\1', tag, re.I | re.S)
    classes = cls_m.group(2).split() if cls_m else []
    if class_name not in classes:
        classes.append(class_name)
    tag = set_attr(tag, "class", " ".join(classes))
    block = tag + block[opening.end():]
    p.write_text(text[:m.start()] + block + text[m.end():], encoding="utf-8")


def inject_style(rel: str) -> None:
    p, text = read(rel)
    style = r'''<style id="oolita-reader-pacing-v1">
/* Post-audit pacing: alter space and emphasis, never authored copy. */
body.art-home .pacing-countdown{min-height:clamp(20rem,46vh,36rem)!important;display:grid!important;align-content:center!important;padding-block:clamp(4rem,10vw,9rem)!important;border-block:1px solid rgba(45,78,35,.28)}
body.art-home .pacing-countdown [role="timer"],body.art-home .pacing-countdown .countdown{max-width:54rem}
body.art-home .pacing-three-materials{padding-block:clamp(2rem,5vw,5rem)!important}
body.art-home .pacing-cabo{max-width:56rem;margin-inline:auto!important;padding-block:clamp(3rem,7vw,7rem)!important}
body.art-home .pacing-index{padding-top:clamp(3rem,8vw,8rem)!important;padding-bottom:clamp(4rem,10vw,10rem)!important}
body.art-home .pacing-follow{margin-top:clamp(5rem,12vw,12rem)!important;padding-top:clamp(4rem,8vw,8rem)!important;border-top:1px solid rgba(45,78,35,.35)}
body.art-home #oolita-art-field-stone,body.art-home #oolita-art-field-sundays,body.art-home #oolita-art-field-paper{min-height:min(72vh,760px)!important}
body.art-restaged:not(.art-home) main > section + section{margin-top:clamp(3rem,7vw,6.5rem)!important}
@media(max-width:760px){body.art-home .pacing-countdown{min-height:30svh!important;padding-block:3.25rem!important}body.art-home .pacing-three-materials{padding-block:1.5rem!important}body.art-home .pacing-cabo{padding-block:2.5rem!important}body.art-home .pacing-index{padding-block:3.25rem!important}body.art-home .pacing-follow{margin-top:4.25rem!important;padding-top:3.25rem!important}body.art-home #oolita-art-field-stone,body.art-home #oolita-art-field-sundays,body.art-home #oolita-art-field-paper{min-height:54svh!important}}
</style>'''
    text = re.sub(rf'<style\b[^>]*id=["\']{STYLE_ID}["\'][^>]*>[\s\S]*?</style>\s*', "", text, flags=re.I)
    if "</head>" not in text:
        raise SystemExit(f"Missing </head> in {rel}")
    p.write_text(text.replace("</head>", style + "\n</head>", 1), encoding="utf-8")


def add_launch_state_script(rel: str, language: str) -> None:
    p, text = read(rel)
    home_3d = "/mundo-3d/" if language == "es" else "/en/3d-world/"
    live_label = "ENTRAR EN EL MUNDO 3D" if language == "es" else "ENTER THE 3D WORLD"
    state = f'''<script id="oolita-launch-state-v1">(function(){{
var now=new Date();
var states=[{{id:"3d",at:"2027-01-03T00:00:00+01:00"}},{{id:"book",at:"2027-01-31T00:00:00+01:00"}},{{id:"textile",at:"2027-04-11T00:00:00+02:00"}},{{id:"hallazgo-publication",at:"2027-09-16T00:00:00+02:00"}},{{id:"hallazgo-launch",at:"2027-09-19T00:00:00+02:00"}}];
document.documentElement.dataset.oolitaLaunchState=states.filter(function(s){{return now>=new Date(s.at)}}).map(function(s){{return s.id}}).join(",");
document.querySelectorAll("[data-launch-at]").forEach(function(el){{var at=new Date(el.getAttribute("data-launch-at"));el.dataset.launchStatus=now>=at?"live":"upcoming";}});
if(now>=new Date("2027-01-03T00:00:00+01:00")){{var a=document.querySelector('[data-oolita-event="home-follow"]');if(a){{a.href="{home_3d}";a.textContent="{live_label}";a.setAttribute("data-oolita-event","home-3d-live");}}}}
}})();</script>'''
    text = re.sub(rf'<script\b[^>]*id=["\']{STATE_ID}["\'][^>]*>[\s\S]*?</script>\s*', "", text, flags=re.I)
    if "</body>" not in text:
        raise SystemExit(f"Missing </body> in {rel}")
    p.write_text(text.replace("</body>", state + "\n</body>", 1), encoding="utf-8")


def mark_launch_at(rel: str, text_contains: str, iso: str) -> None:
    p, text = read(rel)
    for pat in (re.compile(r"<a\b[^>]*>[\s\S]*?</a>", re.I), re.compile(r"<p\b[^>]*>[\s\S]*?</p>", re.I), re.compile(r"<div\b[^>]*>[\s\S]*?</div>", re.I)):
        hits = [m for m in pat.finditer(text) if text_contains in visible(m.group(0))]
        if not hits:
            continue
        m = hits[0]
        block = m.group(0)
        opening = re.match(r"<(?:a|p|div)\b[^>]*>", block, re.I)
        tag = set_attr(opening.group(0), "data-launch-at", iso)
        p.write_text(text[:m.start()] + tag + block[opening.end():] + text[m.end():], encoding="utf-8")
        return
    raise SystemExit(f"Launch-state marker not found in {rel}: {text_contains}")


PAGES = [
    ("index.html","follow-project","home-follow",dict(text_contains="SEGUIR EL CAMINO HASTA EL 3 DE ENERO")),
    ("laberinto/index.html","continue-remotely","labyrinth-follow-3d",dict(href_contains="follow=3d")),
    ("domingos/index.html","read-current-sunday","sundays-current",dict(href_exact="/domingos/03-la-memoria-del-mar/")),
    ("domingos/01-el-doble/index.html","read-next-sunday","sunday-next",dict(href_exact="/domingos/02-22-domingos/")),
    ("domingos/02-22-domingos/index.html","read-next-sunday","sunday-next",dict(href_exact="/domingos/03-la-memoria-del-mar/")),
    ("domingos/03-la-memoria-del-mar/index.html","return-to-sundays","sunday-archive",dict(href_exact="/domingos/")),
    ("cabo-de-gata/index.html","continue-to-labyrinth","cabo-labyrinth",dict(href_exact="/laberinto/")),
    ("ediciones/index.html","open-book-edition","editions-book",dict(href_exact="/ediciones/libro/")),
    ("ediciones/libro/index.html","follow-book","book-follow",dict(href_contains="follow=book")),
    ("ediciones/camiseta/index.html","follow-textile","textile-follow",dict(href_contains="follow=textile")),
    ("que-es-un-laberinto/index.html","see-oolita-labyrinth","explainer-labyrinth",dict(href_exact="/laberinto/")),
    ("que-es-un-oolito/index.html","see-place","ooid-cabo",dict(href_exact="/cabo-de-gata/")),
    ("carteles/index.html","open-sundays-archive","posters-sundays",dict(href_exact="/domingos/")),
    ("catalogo-hallazgo/index.html","follow-hallazgo","hallazgo-follow",dict(href_contains="interest=hallazgo")),
    ("sobre-oolita/index.html","open-hallazgo","about-hallazgo",dict(href_exact="/catalogo-hallazgo/")),
    ("colaborar/index.html","contact-oolita","partner-contact",dict(href_contains="mailto:oolita@tutamail.com")),
    ("mundo-3d/index.html","follow-3d","3d-follow",dict(href_contains="follow=3d")),
    ("privacidad/index.html","return-to-index","privacy-index",dict(href_contains="#oolita-index")),
    ("en/index.html","follow-project","home-follow",dict(text_contains="FOLLOW THE PATH TO 3 JANUARY")),
    ("en/labyrinth/index.html","continue-remotely","labyrinth-follow-3d",dict(href_contains="follow=3d")),
    ("en/sundays/index.html","read-current-sunday","sundays-current",dict(href_exact="/en/sundays/03-the-memory-of-the-sea/")),
    ("en/sundays/01-the-double/index.html","read-next-sunday","sunday-next",dict(href_exact="/en/sundays/02-22-sundays/")),
    ("en/sundays/02-22-sundays/index.html","read-next-sunday","sunday-next",dict(href_exact="/en/sundays/03-the-memory-of-the-sea/")),
    ("en/sundays/03-the-memory-of-the-sea/index.html","return-to-sundays","sunday-archive",dict(href_exact="/en/sundays/")),
    ("en/cabo-de-gata/index.html","continue-to-labyrinth","cabo-labyrinth",dict(href_exact="/en/labyrinth/")),
    ("en/editions/index.html","open-book-edition","editions-book",dict(href_exact="/en/editions/book/")),
    ("en/editions/book/index.html","follow-book","book-follow",dict(href_contains="follow=book")),
    ("en/editions/t-shirt/index.html","follow-textile","textile-follow",dict(href_contains="follow=textile")),
    ("en/what-is-a-labyrinth/index.html","see-oolita-labyrinth","explainer-labyrinth",dict(href_exact="/en/labyrinth/")),
    ("en/what-is-an-ooid/index.html","see-place","ooid-cabo",dict(href_exact="/en/cabo-de-gata/")),
    ("en/posters/index.html","open-sundays-archive","posters-sundays",dict(href_exact="/en/sundays/")),
    ("en/hallazgo-catalogue/index.html","follow-hallazgo","hallazgo-follow",dict(href_contains="interest=hallazgo")),
    ("en/about/index.html","open-hallazgo","about-hallazgo",dict(href_exact="/en/hallazgo-catalogue/")),
    ("en/work-with-oolita/index.html","contact-oolita","partner-contact",dict(href_contains="mailto:oolita@tutamail.com")),
    ("en/3d-world/index.html","follow-3d","3d-follow",dict(href_contains="follow=3d")),
    ("en/privacy/index.html","return-to-index","privacy-index",dict(href_contains="#oolita-index")),
]
for rel, purpose, event, selector in PAGES:
    add_page_meta(rel, purpose, event)
    mark_link(rel, event=event, primary=True, journey="primary", **selector)

JOURNEY_EDGES = [
    ("index.html","home-book",dict(href_exact="/ediciones/libro/")),("index.html","home-3d",dict(href_exact="/mundo-3d/")),("index.html","home-about",dict(href_exact="/sobre-oolita/")),
    ("en/index.html","home-book",dict(href_exact="/en/editions/book/")),("en/index.html","home-3d",dict(href_exact="/en/3d-world/")),("en/index.html","home-about",dict(href_exact="/en/about/")),
    ("sobre-oolita/index.html","about-hallazgo",dict(href_exact="/catalogo-hallazgo/")),("en/about/index.html","about-hallazgo",dict(href_exact="/en/hallazgo-catalogue/")),
    ("catalogo-hallazgo/index.html","hallazgo-follow",dict(href_contains="interest=hallazgo")),("en/hallazgo-catalogue/index.html","hallazgo-follow",dict(href_contains="interest=hallazgo")),
    ("ediciones/index.html","editions-book",dict(href_exact="/ediciones/libro/")),("en/editions/index.html","editions-book",dict(href_exact="/en/editions/book/")),
    ("que-es-un-oolito/index.html","ooid-cabo",dict(href_exact="/cabo-de-gata/")),("en/what-is-an-ooid/index.html","ooid-cabo",dict(href_exact="/en/cabo-de-gata/")),
    ("domingos/01-el-doble/index.html","sunday-next",dict(href_exact="/domingos/02-22-domingos/")),("domingos/02-22-domingos/index.html","sunday-next",dict(href_exact="/domingos/03-la-memoria-del-mar/")),
    ("en/sundays/01-the-double/index.html","sunday-next",dict(href_exact="/en/sundays/02-22-sundays/")),("en/sundays/02-22-sundays/index.html","sunday-next",dict(href_exact="/en/sundays/03-the-memory-of-the-sea/")),
]
for rel, event, selector in JOURNEY_EDGES:
    mark_link(rel, event=event, journey="measured", **selector)

JOURNEYS = {
    "curator-es":[("index.html","/sobre-oolita/"),("sobre-oolita/index.html","/catalogo-hallazgo/"),("catalogo-hallazgo/index.html","interest=hallazgo")],
    "curator-en":[("en/index.html","/en/about/"),("en/about/index.html","/en/hallazgo-catalogue/"),("en/hallazgo-catalogue/index.html","interest=hallazgo")],
    "book-es":[("index.html","/ediciones/libro/"),("ediciones/libro/index.html","follow=book")],"book-en":[("en/index.html","/en/editions/book/"),("en/editions/book/index.html","follow=book")],
    "geology-es":[("que-es-un-oolito/index.html","/cabo-de-gata/"),("cabo-de-gata/index.html","/laberinto/"),("laberinto/index.html","follow=3d")],
    "geology-en":[("en/what-is-an-ooid/index.html","/en/cabo-de-gata/"),("en/cabo-de-gata/index.html","/en/labyrinth/"),("en/labyrinth/index.html","follow=3d")],
    "instagram-es":[("domingos/01-el-doble/index.html","/domingos/02-22-domingos/"),("domingos/02-22-domingos/index.html","/domingos/03-la-memoria-del-mar/"),("domingos/03-la-memoria-del-mar/index.html","/domingos/")],
    "instagram-en":[("en/sundays/01-the-double/index.html","/en/sundays/02-22-sundays/"),("en/sundays/02-22-sundays/index.html","/en/sundays/03-the-memory-of-the-sea/"),("en/sundays/03-the-memory-of-the-sea/index.html","/en/sundays/")],
    "remote-es":[("index.html","/mundo-3d/"),("mundo-3d/index.html","follow=3d")],"remote-en":[("en/index.html","/en/3d-world/"),("en/3d-world/index.html","follow=3d")],
}
for name, edges in JOURNEYS.items():
    for rel, href_piece in edges:
        _, text = read(rel)
        if href_piece not in text:
            raise SystemExit(f"Reader journey {name} broken at {rel}: {href_piece}")

for rel, labels in {
    "index.html":[("EL MUNDO 3D ABRE","pacing-countdown"),("La misma senda en tres materiales.","pacing-three-materials"),("De un camino, un paisaje más amplio.","pacing-cabo"),("EXPLORAR OOLITA","pacing-index"),("Seguir el proyecto.","pacing-follow")],
    "en/index.html":[("THE 3D WORLD OPENS","pacing-countdown"),("The same path in three materials.","pacing-three-materials"),("From one path, a wider landscape.","pacing-cabo"),("EXPLORE OOLITA","pacing-index"),("Follow the project.","pacing-follow")],
}.items():
    for needle, cls in labels:
        mark_section_by_text(rel, needle, cls)
    inject_style(rel)

for rel, lang in (("index.html","es"),("en/index.html","en")):
    add_launch_state_script(rel, lang)
for rel, needle, iso in [
    ("index.html","03.01.2027","2027-01-03T00:00:00+01:00"),("en/index.html","3 Jan 2027","2027-01-03T00:00:00+01:00"),
    ("ediciones/libro/index.html","31 de enero de 2027","2027-01-31T00:00:00+01:00"),("en/editions/book/index.html","31 January 2027","2027-01-31T00:00:00+01:00"),
    ("ediciones/camiseta/index.html","11 de abril de 2027","2027-04-11T00:00:00+02:00"),("en/editions/t-shirt/index.html","11 April 2027","2027-04-11T00:00:00+02:00"),
    ("catalogo-hallazgo/index.html","PUBLICACIÓN · 16.09.27","2027-09-16T00:00:00+02:00"),("en/hallazgo-catalogue/index.html","PUBLICATION · 16 SEP 27","2027-09-16T00:00:00+02:00"),
]:
    mark_launch_at(rel, needle, iso)

PROTECTED = {
    "sobre-oolita/index.html":("Primero fue un laberinto.","El lugar no es un fondo.","Hallazgo trabaja con observación, material encontrado, paisaje y la disciplina de no alterar lo vivo."),
    "en/about/index.html":("First there was a labyrinth.","The place is not a backdrop.","Hallazgo works with observation, found material, landscape and the discipline of leaving living things undisturbed."),
    "index.html":("Una fábula de laberinto para días ruidosos","Piedra. Papel. Código. Tres materiales, un camino."),
    "en/index.html":("A labyrinth fable for loud days","Stone. Paper. Code. Three materials, one path."),
}
FORBIDDEN = ("A public working rhythm.","Un ritmo de trabajo público.","A useful proposal is specific","Una propuesta útil es concreta","continuing public record","registro público en curso")
for rel, needles in PROTECTED.items():
    _, text = read(rel)
    plain = visible(text)
    for needle in needles:
        if needle not in plain:
            raise SystemExit(f"Copy-freeze anchor missing in {rel}: {needle}")
for html in ROOT.rglob("*.html"):
    plain = visible(html.read_text(encoding="utf-8", errors="ignore"))
    for stale in FORBIDDEN:
        if stale in plain:
            raise SystemExit(f"Copy-freeze violation in {html.relative_to(ROOT)}: {stale}")

for rel, _, event, _ in PAGES:
    _, text = read(rel)
    if text.count('data-primary-action="true"') != 1:
        raise SystemExit(f"Primary-action count wrong in {rel}")
    if f'data-primary-event="{event}"' not in text:
        raise SystemExit(f"Primary-event metadata missing in {rel}: {event}")
    if 'id="oolita-event-layer"' not in text:
        raise SystemExit(f"First-party analytics layer missing in {rel}")
if len(PAGES) != 36:
    raise SystemExit(f"Expected 36 primary-action pages; got {len(PAGES)}")

local_now = datetime.now(TZ)
print(f"OOLITA post-audit growth system validated: 36 primary actions, {len(JOURNEY_EDGES)} measured journey edges, {len(JOURNEYS)} bilingual journey checks, copy freeze active, desktop/mobile pacing active, launch clock={local_now.isoformat()}.")
