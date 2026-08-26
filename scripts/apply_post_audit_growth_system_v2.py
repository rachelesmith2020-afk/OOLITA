#!/usr/bin/env python3
"""Post-audit conversion, journeys, pacing, launch states and copy freeze.

This layer intentionally changes only technical attributes, analytics hooks,
layout/pacing and approved launch-state behaviour. It does not rewrite authored
OOLITA prose.
"""
from __future__ import annotations

from html import unescape
from pathlib import Path
import re
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
STYLE_ID = "oolita-reader-pacing-v2"
STATE_ID = "oolita-launch-state-v2"


def read(rel: str) -> tuple[Path, str]:
    p = ROOT / rel
    if not p.is_file():
        raise SystemExit(f"Missing post-audit page: {rel}")
    return p, p.read_text(encoding="utf-8")


def visible(fragment: str) -> str:
    return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", " ", fragment))).strip()


def set_attr(tag: str, name: str, value: str) -> str:
    rx = re.compile(rf'\s{name}=(["\']).*?\1', re.I | re.S)
    if rx.search(tag):
        return rx.sub(f' {name}="{value}"', tag, count=1)
    return tag[:-1] + f' {name}="{value}">'


def remove_attr(text: str, name: str) -> str:
    return re.sub(rf'\s{name}=(["\']).*?\1', "", text, flags=re.I | re.S)


def link_matches(text: str, *, href_exact: str | None = None, href_contains: str | None = None,
                 text_contains: str | None = None) -> list[re.Match[str]]:
    out = []
    for m in re.finditer(r'(?P<open><a\b[^>]*>)(?P<body>[\s\S]*?)</a>', text, re.I):
        hm = re.search(r'\bhref=(["\'])(.*?)\1', m.group("open"), re.I | re.S)
        href = hm.group(2) if hm else ""
        label = visible(m.group("body"))
        if href_exact is not None and href != href_exact:
            continue
        if href_contains is not None and href_contains not in href:
            continue
        if text_contains is not None and text_contains not in label:
            continue
        out.append(m)
    return out


def mark_link(rel: str, event: str, *, primary: bool = False, journey: str | None = None,
              href_exact: str | None = None, href_contains: str | None = None,
              text_contains: str | None = None, pick: int = 0) -> None:
    p, text = read(rel)
    matches = link_matches(text, href_exact=href_exact, href_contains=href_contains, text_contains=text_contains)
    if len(matches) <= pick:
        raise SystemExit(f"Could not mark {event} in {rel}: matches={len(matches)}")
    m = matches[pick]
    opening = set_attr(m.group("open"), "data-oolita-event", event)
    if primary:
        opening = set_attr(opening, "data-primary-action", "true")
    if journey:
        opening = set_attr(opening, "data-reader-journey", journey)
    p.write_text(text[:m.start()] + opening + m.group("body") + "</a>" + text[m.end():], encoding="utf-8")


def set_page_state(rel: str, purpose: str, primary_event: str, launch_id: str | None = None,
                   launch_at: str | None = None) -> None:
    p, text = read(rel)
    text = remove_attr(text, "data-primary-action")
    m = re.search(r"<main\b[^>]*>", text, re.I)
    if not m:
        raise SystemExit(f"Missing <main> in {rel}")
    tag = set_attr(m.group(0), "data-page-purpose", purpose)
    tag = set_attr(tag, "data-primary-event", primary_event)
    if launch_id:
        tag = set_attr(tag, "data-launch-id", launch_id)
    if launch_at:
        tag = set_attr(tag, "data-launch-at", launch_at)
    p.write_text(text[:m.start()] + tag + text[m.end():], encoding="utf-8")


# Exactly one meaningful primary action on every published ES/EN page.
# Selectors use stable destinations rather than reader-facing wording so the
# copy freeze and the conversion system do not fight each other.
PAGES = [
    ("index.html","follow-project","home-follow",dict(href_contains="#seguir-oolita"),None,None),
    ("laberinto/index.html","continue-remotely","labyrinth-follow-3d",dict(href_contains="follow=3d"),None,None),
    ("carteles/index.html","open-sundays-archive","posters-sundays",dict(href_exact="/domingos/"),None,None),
    ("que-es-un-laberinto/index.html","see-oolita-labyrinth","explainer-labyrinth",dict(href_exact="/laberinto/"),None,None),
    ("que-es-un-oolito/index.html","see-place","ooid-cabo",dict(href_exact="/cabo-de-gata/"),None,None),
    ("ediciones/index.html","open-book-edition","editions-book",dict(href_exact="/ediciones/libro/"),None,None),
    ("ediciones/libro/index.html","follow-book","book-follow",dict(href_contains="follow=book"),"book","2027-01-31T00:00:00+01:00"),
    ("ediciones/camiseta/index.html","follow-textile","textile-follow",dict(href_contains="follow=textile"),"textile","2027-04-11T00:00:00+02:00"),
    ("domingos/index.html","read-current-sunday","sundays-current",dict(href_exact="/domingos/03-la-memoria-del-mar/"),None,None),
    ("domingos/01-el-doble/index.html","read-next-sunday","sunday-next",dict(href_exact="/domingos/02-el-gato-de-verdad/"),None,None),
    ("domingos/02-el-gato-de-verdad/index.html","read-next-sunday","sunday-next",dict(href_exact="/domingos/03-la-memoria-del-mar/"),None,None),
    ("domingos/03-la-memoria-del-mar/index.html","return-to-sundays","sunday-archive",dict(href_exact="/domingos/"),None,None),
    ("cabo-de-gata/index.html","continue-to-labyrinth","cabo-labyrinth",dict(href_exact="/laberinto/"),None,None),
    ("sobre-oolita/index.html","open-hallazgo","about-hallazgo",dict(href_exact="/catalogo-hallazgo/"),None,None),
    ("colaborar/index.html","contact-oolita","partner-contact",dict(href_contains="mailto:oolita@tutamail.com"),None,None),
    ("privacidad/index.html","return-to-index","privacy-index",dict(href_contains="#oolita-index"),None,None),
    ("mundo-3d/index.html","follow-3d","3d-follow",dict(href_contains="follow=3d"),"3d","2027-01-03T00:00:00+01:00"),
    ("catalogo-hallazgo/index.html","follow-hallazgo","hallazgo-follow",dict(href_contains="interest=hallazgo"),"hallazgo","2027-09-16T00:00:00+02:00"),

    ("en/index.html","follow-project","home-follow",dict(href_contains="#follow-oolita"),None,None),
    ("en/labyrinth/index.html","continue-remotely","labyrinth-follow-3d",dict(href_contains="follow=3d"),None,None),
    ("en/posters/index.html","open-sundays-archive","posters-sundays",dict(href_exact="/en/sundays/"),None,None),
    ("en/what-is-a-labyrinth/index.html","see-oolita-labyrinth","explainer-labyrinth",dict(href_exact="/en/labyrinth/"),None,None),
    ("en/what-is-an-ooid/index.html","see-place","ooid-cabo",dict(href_exact="/en/cabo-de-gata/"),None,None),
    ("en/editions/index.html","open-book-edition","editions-book",dict(href_exact="/en/editions/book/"),None,None),
    ("en/editions/book/index.html","follow-book","book-follow",dict(href_contains="follow=book"),"book","2027-01-31T00:00:00+01:00"),
    ("en/editions/t-shirt/index.html","follow-textile","textile-follow",dict(href_contains="follow=textile"),"textile","2027-04-11T00:00:00+02:00"),
    ("en/sundays/index.html","read-current-sunday","sundays-current",dict(href_exact="/en/sundays/03-the-memory-of-the-sea/"),None,None),
    ("en/sundays/01-the-double/index.html","read-next-sunday","sunday-next",dict(href_exact="/en/sundays/02-the-cat-for-real/"),None,None),
    ("en/sundays/02-the-cat-for-real/index.html","read-next-sunday","sunday-next",dict(href_exact="/en/sundays/03-the-memory-of-the-sea/"),None,None),
    ("en/sundays/03-the-memory-of-the-sea/index.html","return-to-sundays","sunday-archive",dict(href_exact="/en/sundays/"),None,None),
    ("en/cabo-de-gata/index.html","continue-to-labyrinth","cabo-labyrinth",dict(href_exact="/en/labyrinth/"),None,None),
    ("en/about/index.html","open-hallazgo","about-hallazgo",dict(href_exact="/en/hallazgo-catalogue/"),None,None),
    ("en/work-with-oolita/index.html","contact-oolita","partner-contact",dict(href_contains="mailto:oolita@tutamail.com"),None,None),
    ("en/privacy/index.html","return-to-index","privacy-index",dict(href_contains="#oolita-index"),None,None),
    ("en/3d-world/index.html","follow-3d","3d-follow",dict(href_contains="follow=3d"),"3d","2027-01-03T00:00:00+01:00"),
    ("en/hallazgo-catalogue/index.html","follow-hallazgo","hallazgo-follow",dict(href_contains="interest=hallazgo"),"hallazgo","2027-09-16T00:00:00+02:00"),
]
if len(PAGES) != 36:
    raise SystemExit(f"Expected 36 primary-action pages, got {len(PAGES)}")

for rel, purpose, event, selector, launch_id, launch_at in PAGES:
    set_page_state(rel, purpose, event, launch_id, launch_at)
    mark_link(rel, event, primary=True, journey="primary", **selector)


# Additional edges that answer the actual questions the user will ask later:
# which route people took, rather than only which pages were viewed.
EDGES = [
    ("index.html","home-book",dict(href_exact="/ediciones/libro/")),
    ("index.html","home-3d",dict(href_exact="/mundo-3d/")),
    ("index.html","home-about",dict(href_exact="/sobre-oolita/")),
    ("en/index.html","home-book",dict(href_exact="/en/editions/book/")),
    ("en/index.html","home-3d",dict(href_exact="/en/3d-world/")),
    ("en/index.html","home-about",dict(href_exact="/en/about/")),
    ("sobre-oolita/index.html","about-hallazgo",dict(href_exact="/catalogo-hallazgo/")),
    ("en/about/index.html","about-hallazgo",dict(href_exact="/en/hallazgo-catalogue/")),
    ("catalogo-hallazgo/index.html","hallazgo-follow",dict(href_contains="interest=hallazgo")),
    ("en/hallazgo-catalogue/index.html","hallazgo-follow",dict(href_contains="interest=hallazgo")),
    ("ediciones/index.html","editions-book",dict(href_exact="/ediciones/libro/")),
    ("en/editions/index.html","editions-book",dict(href_exact="/en/editions/book/")),
    ("que-es-un-oolito/index.html","ooid-cabo",dict(href_exact="/cabo-de-gata/")),
    ("en/what-is-an-ooid/index.html","ooid-cabo",dict(href_exact="/en/cabo-de-gata/")),
    ("cabo-de-gata/index.html","cabo-labyrinth",dict(href_exact="/laberinto/")),
    ("en/cabo-de-gata/index.html","cabo-labyrinth",dict(href_exact="/en/labyrinth/")),
    ("domingos/01-el-doble/index.html","sunday-next",dict(href_exact="/domingos/02-el-gato-de-verdad/")),
    ("domingos/02-el-gato-de-verdad/index.html","sunday-next",dict(href_exact="/domingos/03-la-memoria-del-mar/")),
    ("en/sundays/01-the-double/index.html","sunday-next",dict(href_exact="/en/sundays/02-the-cat-for-real/")),
    ("en/sundays/02-the-cat-for-real/index.html","sunday-next",dict(href_exact="/en/sundays/03-the-memory-of-the-sea/")),
]
for rel, event, selector in EDGES:
    mark_link(rel, event, journey="measured", **selector)


# Five routes, validated in both languages. No new navigation or prose is added.
JOURNEYS = {
    "curator-es": [("index.html","/sobre-oolita/"),("sobre-oolita/index.html","/catalogo-hallazgo/"),("catalogo-hallazgo/index.html","interest=hallazgo")],
    "curator-en": [("en/index.html","/en/about/"),("en/about/index.html","/en/hallazgo-catalogue/"),("en/hallazgo-catalogue/index.html","interest=hallazgo")],
    "book-es": [("index.html","/ediciones/libro/"),("ediciones/libro/index.html","follow=book")],
    "book-en": [("en/index.html","/en/editions/book/"),("en/editions/book/index.html","follow=book")],
    "geology-es": [("que-es-un-oolito/index.html","/cabo-de-gata/"),("cabo-de-gata/index.html","/laberinto/"),("laberinto/index.html","follow=3d")],
    "geology-en": [("en/what-is-an-ooid/index.html","/en/cabo-de-gata/"),("en/cabo-de-gata/index.html","/en/labyrinth/"),("en/labyrinth/index.html","follow=3d")],
    "instagram-es": [("domingos/01-el-doble/index.html","/domingos/02-el-gato-de-verdad/"),("domingos/02-el-gato-de-verdad/index.html","/domingos/03-la-memoria-del-mar/"),("domingos/03-la-memoria-del-mar/index.html","/domingos/")],
    "instagram-en": [("en/sundays/01-the-double/index.html","/en/sundays/02-the-cat-for-real/"),("en/sundays/02-the-cat-for-real/index.html","/en/sundays/03-the-memory-of-the-sea/"),("en/sundays/03-the-memory-of-the-sea/index.html","/en/sundays/")],
    "remote-es": [("index.html","/mundo-3d/"),("mundo-3d/index.html","follow=3d")],
    "remote-en": [("en/index.html","/en/3d-world/"),("en/3d-world/index.html","follow=3d")],
}
for name, edges in JOURNEYS.items():
    for rel, href_piece in edges:
        _, text = read(rel)
        if href_piece not in text:
            raise SystemExit(f"Reader journey {name} broken at {rel}: {href_piece}")


# Visual pacing: the homepage keeps all approved words, but dense information
# sections get separated by light fields and stronger vertical pauses.
PACING_CSS = r'''<style id="oolita-reader-pacing-v2">
body.art-home .pacing-countdown{min-height:clamp(20rem,45vh,36rem)!important;display:grid!important;align-content:center!important;padding-block:clamp(4rem,9vw,8rem)!important;border-block:1px solid rgba(45,78,35,.28)}
body.art-home .pacing-three-materials{padding-block:clamp(3rem,7vw,7rem)!important}
body.art-home .pacing-cabo{max-width:58rem;margin-inline:auto!important;padding-block:clamp(4rem,9vw,9rem)!important}
body.art-home .pacing-index{padding-block:clamp(4rem,9vw,9rem)!important}
body.art-home .pacing-follow{margin-top:clamp(5rem,11vw,11rem)!important;padding-top:clamp(4rem,8vw,8rem)!important;border-top:1px solid rgba(45,78,35,.35)}
body.art-home #oolita-art-field-stone,body.art-home #oolita-art-field-sundays,body.art-home #oolita-art-field-paper{min-height:min(72vh,760px)!important}
body.art-restaged:not(.art-home) main>section+section{margin-top:clamp(3rem,7vw,6rem)!important}
@media(max-width:760px){body.art-home .pacing-countdown{min-height:30svh!important;padding-block:3.25rem!important}body.art-home .pacing-three-materials{padding-block:2.25rem!important}body.art-home .pacing-cabo{padding-block:3rem!important}body.art-home .pacing-index{padding-block:3.5rem!important}body.art-home .pacing-follow{margin-top:4.5rem!important;padding-top:3.25rem!important}body.art-home #oolita-art-field-stone,body.art-home #oolita-art-field-sundays,body.art-home #oolita-art-field-paper{min-height:54svh!important}}
</style>'''
PACING_JS = r'''<script id="oolita-reader-pacing-map-v2">(function(){var map=[[["EL MUNDO 3D ABRE","THE 3D WORLD OPENS"],"pacing-countdown"],[["La misma senda en tres materiales.","The same path in three materials."],"pacing-three-materials"],[["De un camino, un paisaje más amplio.","From one path, a wider landscape."],"pacing-cabo"],[["EXPLORAR OOLITA","EXPLORE OOLITA"],"pacing-index"],[["Seguir el proyecto.","Follow the project."],"pacing-follow"]];document.querySelectorAll("main section").forEach(function(s){var t=(s.textContent||"").replace(/\s+/g," ");map.forEach(function(x){if(x[0].some(function(n){return t.indexOf(n)>=0;}))s.classList.add(x[1]);});});})();</script>'''
for rel in ("index.html","en/index.html"):
    p, text = read(rel)
    text = re.sub(rf'<style\b[^>]*id=["\']{STYLE_ID}["\'][^>]*>[\s\S]*?</style>\s*', "", text, flags=re.I)
    text = re.sub(r'<script\b[^>]*id=["\']oolita-reader-pacing-map-v2["\'][^>]*>[\s\S]*?</script>\s*', "", text, flags=re.I)
    if "</head>" not in text or "</body>" not in text:
        raise SystemExit(f"Homepage shell incomplete: {rel}")
    text = text.replace("</head>", PACING_CSS + "\n</head>", 1)
    text = text.replace("</body>", PACING_JS + "\n</body>", 1)
    p.write_text(text, encoding="utf-8")


# Launch state system. Known dates are encoded now. The 3D transition has a
# known live destination, so it can switch automatically. Book/textile/Hallazgo
# expose machine-readable upcoming/live state without inventing a future shop or
# access URL that has not yet been confirmed.
def inject_launch_runtime(rel: str, language: str) -> None:
    p, text = read(rel)
    live_3d_href = "/mundo-3d/" if language == "es" else "/en/3d-world/"
    live_3d_label = "ENTRAR EN EL MUNDO 3D" if language == "es" else "ENTER THE 3D WORLD"
    script = f'''<script id="{STATE_ID}">(function(){{var states={{"3d":"2027-01-03T00:00:00+01:00","book":"2027-01-31T00:00:00+01:00","textile":"2027-04-11T00:00:00+02:00","hallazgo":"2027-09-16T00:00:00+02:00","hallazgo-launch":"2027-09-19T00:00:00+02:00"}};var now=Date.now();var live=[];Object.keys(states).forEach(function(k){{if(now>=Date.parse(states[k]))live.push(k);}});document.documentElement.setAttribute("data-oolita-launch-state",live.join(","));document.querySelectorAll("main[data-launch-id][data-launch-at]").forEach(function(m){{m.setAttribute("data-launch-status",now>=Date.parse(m.getAttribute("data-launch-at"))?"live":"upcoming");}});if(now>=Date.parse(states["3d"])){{var a=document.querySelector('[data-oolita-event="home-follow"]');if(a){{a.href="{live_3d_href}";a.textContent="{live_3d_label}";a.setAttribute("data-oolita-event","home-3d-live");}}}}}})();</script>'''
    text = re.sub(rf'<script\b[^>]*id=["\']{STATE_ID}["\'][^>]*>[\s\S]*?</script>\s*', "", text, flags=re.I)
    if "</body>" not in text:
        raise SystemExit(f"Missing </body> in {rel}")
    p.write_text(text.replace("</body>", script + "\n</body>", 1), encoding="utf-8")

for rel, *_ in PAGES:
    inject_launch_runtime(rel, "en" if rel.startswith("en/") else "es")


# Copy freeze: the approved voice cannot be silently padded or normalized away.
PROTECTED = {
    "index.html": ("Una fábula de laberinto para días ruidosos","Piedra. Papel. Código. Tres materiales, un camino."),
    "en/index.html": ("A labyrinth fable for loud days","Stone. Paper. Code. Three materials, one path."),
    "sobre-oolita/index.html": ("Primero fue un laberinto.","El lugar no es un fondo.","Hallazgo trabaja con observación, material encontrado, paisaje y la disciplina de no alterar lo vivo."),
    "en/about/index.html": ("First there was a labyrinth.","The place is not a backdrop.","Hallazgo works with observation, found material, landscape and the discipline of leaving living things undisturbed."),
}
FORBIDDEN = ("A public working rhythm.","Un ritmo de trabajo público.","A useful proposal is specific","Una propuesta útil es concreta","continuing public record","registro público en curso")
for rel, anchors in PROTECTED.items():
    _, text = read(rel)
    plain = visible(text)
    for anchor in anchors:
        if anchor not in plain:
            raise SystemExit(f"Copy-freeze anchor missing in {rel}: {anchor}")
for html in ROOT.rglob("*.html"):
    plain = visible(html.read_text(encoding="utf-8", errors="ignore"))
    for stale in FORBIDDEN:
        if stale in plain:
            raise SystemExit(f"Copy-freeze violation in {html.relative_to(ROOT)}: {stale}")


# Final fail-closed validation.
for rel, _, event, _, _, _ in PAGES:
    _, text = read(rel)
    if text.count('data-primary-action="true"') != 1:
        raise SystemExit(f"Primary-action count wrong in {rel}: {text.count('data-primary-action=\"true\"')}")
    if f'data-primary-event="{event}"' not in text:
        raise SystemExit(f"Primary-event metadata missing in {rel}: {event}")
    if 'id="oolita-event-layer"' not in text:
        raise SystemExit(f"First-party analytics layer missing in {rel}")
    if f'id="{STATE_ID}"' not in text:
        raise SystemExit(f"Launch-state runtime missing in {rel}")
for rel in ("index.html","en/index.html"):
    _, text = read(rel)
    for marker in (STYLE_ID,"oolita-reader-pacing-map-v2"):
        if marker not in text:
            raise SystemExit(f"Visual pacing marker missing in {rel}: {marker}")

print(f"OOLITA post-audit system passed: {len(PAGES)} primary actions, {len(EDGES)} measured edges, 5 reader journeys in ES/EN, copy freeze active, visual pacing installed, five launch states staged.")
