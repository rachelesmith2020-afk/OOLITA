#!/usr/bin/env python3
"""Publish the approved third Sunday and one restrained browser-world still."""
from __future__ import annotations

from pathlib import Path
import re
import shutil
import sys
import urllib.request
import xml.etree.ElementTree as ET

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
ES_ROUTE = "/domingos/03-la-memoria-del-mar/"
EN_ROUTE = "/en/sundays/03-the-memory-of-the-sea/"
SUNDAY_IMAGE = "https://drive.google.com/uc?export=download&id=1h85sZKS8or4G1bpxmV8y7uk1PzsPyelB"
WORLD_IMAGE = "https://drive.google.com/uc?export=download&id=1ZHu-4x14vZ-g2k8LYwy3qen6FBIuiSec"


def download(url: str, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.is_file() and target.stat().st_size > 100_000:
        return
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 OOLITA deployment"})
    with urllib.request.urlopen(req, timeout=45) as response, target.open("wb") as out:
        shutil.copyfileobj(response, out)
    if target.stat().st_size < 100_000:
        raise SystemExit(f"Downloaded asset is unexpectedly small: {target}")


download(SUNDAY_IMAGE, ROOT / "domingos/img/03.jpg")
download(WORLD_IMAGE, ROOT / "img/oolita-browser-world-preview.jpg")


def make_page(source: str, target: str, language: str) -> None:
    src = ROOT / source
    dst = ROOT / target
    if not src.is_file():
        raise SystemExit(f"Missing Sunday template: {source}")
    text = src.read_text(encoding="utf-8")
    if language == "es":
        replacements = {
            "02-el-gato-de-verdad": "03-la-memoria-del-mar",
            "02-the-cat-for-real": "03-the-memory-of-the-sea",
            "El gato, de verdad": "La memoria del mar",
            "The cat, for real": "The Memory of the Sea",
            "Domingo 02 de 22": "Domingo 03 de 22",
            "Domingo 02 de los 22": "Domingo 03 de los 22",
            "16 de agosto de 2026": "23 de agosto de 2026",
            "2026-08-16T19:00:00+02:00": "2026-08-23T19:00:00+02:00",
            "/domingos/img/02": "/domingos/img/03",
            '"position": 2': '"position": 3',
        }
        article = """<article class="tramo">
<span class="rot">Domingo 03 de 22 · 23 de agosto de 2026</span>
<h1 class="grande">La memoria del mar</h1>
<p class="lema-en" lang="en">The Memory of the Sea</p>
<p class="lema">La piedra guarda la memoria del mar.</p>
<figure class="lamina">
<img src="/domingos/img/03.jpg" alt="Diagrama de cómo los granos de oolito formaron la duna fósil de calcarenita oolítica de Los Escullos, Cabo de Gata: la piedra sobre la que se traza el laberinto de OOLITA." width="1080" height="1350" loading="eager" decoding="async" fetchpriority="high">
<figcaption>Calcarenita oolítica · duna fósil de la Playa del Arco, Los Escullos.</figcaption>
</figure>
<div class="cuento">
<p>En agua cálida y poco profunda, granos sueltos de arena rodaban unos contra otros.</p>
<p>Cada grano se redondeaba hacia dentro, capa sobre capa, hasta volverse una esfera diminuta.</p>
<p>Se llaman oolitos. Nadie los hizo.</p>
<p>El viento los llevó tierra adentro y levantó dunas; las dunas se endurecieron en piedra.</p>
<p>La piedra guarda la memoria del mar. De esa redondez viene el nombre.</p>
<div class="otroidioma" lang="en">
<p>In warm shallow water, loose grains of sand rolled against one another.</p>
<p>Each grain rounded inward, layer upon layer, until it became a tiny sphere.</p>
<p>They are called ooids. No one made them.</p>
<p>The wind carried them inland and built them into dunes; the dunes hardened into stone.</p>
<p>The stone holds the memory of the sea. The name comes from that roundness.</p>
</div></div>
</article>"""
    else:
        replacements = {
            "02-the-cat-for-real": "03-the-memory-of-the-sea",
            "02-el-gato-de-verdad": "03-la-memoria-del-mar",
            "The cat, for real": "The Memory of the Sea",
            "El gato, de verdad": "La memoria del mar",
            "Sunday 02 of 22": "Sunday 03 of 22",
            "Sunday 02 of the 22": "Sunday 03 of the 22",
            "16 August 2026": "23 August 2026",
            "2026-08-16T19:00:00+02:00": "2026-08-23T19:00:00+02:00",
            "/domingos/img/02": "/domingos/img/03",
            '"position": 2': '"position": 3',
        }
        article = """<article class="tramo">
<span class="rot">Sunday 03 of 22 · 23 August 2026</span>
<h1 class="grande">The Memory of the Sea</h1>
<p class="lema-en" lang="es">La memoria del mar</p>
<p class="lema">The stone holds the memory of the sea.</p>
<figure class="lamina">
<img src="/domingos/img/03.jpg" alt="Diagrama de cómo los granos de oolito formaron la duna fósil de calcarenita oolítica de Los Escullos, Cabo de Gata: la piedra sobre la que se traza el laberinto de OOLITA. · Diagram of how ooid grains formed the oolitic calcarenite fossil dune at Los Escullos, Cabo de Gata — the stone the OOLITA labyrinth is laid from." width="1080" height="1350" loading="eager" decoding="async" fetchpriority="high">
<figcaption>Oolitic calcarenite · the Playa del Arco fossil dune, Los Escullos.</figcaption>
</figure>
<div class="cuento">
<p>In warm shallow water, loose grains of sand rolled against one another.</p>
<p>Each grain rounded inward, layer upon layer, until it became a tiny sphere.</p>
<p>They are called ooids. No one made them.</p>
<p>The wind carried them inland and built them into dunes; the dunes hardened into stone.</p>
<p>The stone holds the memory of the sea. The name comes from that roundness.</p>
<div class="otroidioma" lang="es">
<p>En agua cálida y poco profunda, granos sueltos de arena rodaban unos contra otros.</p>
<p>Cada grano se redondeaba hacia dentro, capa sobre capa, hasta volverse una esfera diminuta.</p>
<p>Se llaman oolitos. Nadie los hizo.</p>
<p>El viento los llevó tierra adentro y levantó dunas; las dunas se endurecieron en piedra.</p>
<p>La piedra guarda la memoria del mar. De esa redondez viene el nombre.</p>
</div></div>
</article>"""
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = re.sub(r'<article class="tramo">[\s\S]*?</article>', article, text, count=1)
    text = re.sub(r'<section class="tramo">\s*<span class="rot">(?:Hacia dentro|Inward)[\s\S]*?</section>', "", text, count=1)
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(text, encoding="utf-8")


make_page("domingos/02-el-gato-de-verdad/index.html", "domingos/03-la-memoria-del-mar/index.html", "es")
make_page("en/sundays/02-the-cat-for-real/index.html", "en/sundays/03-the-memory-of-the-sea/index.html", "en")


def publish_tile(path: str, href: str, label: str) -> None:
    target = ROOT / path
    text = target.read_text(encoding="utf-8")
    pattern = r'<a\b[^>]*data-sunday="3"[^>]*>[\s\S]*?</a>'
    match = re.search(pattern, text)
    if not match:
        raise SystemExit(f"Sunday 03 tile missing in {path}")
    tile = match.group(0)
    tile = re.sub(r'class="[^"]*"', 'class="sunday-tile is-published"', tile, count=1)
    tile = re.sub(r'\saria-disabled="true"', "", tile)
    if " aria-label=" in tile:
        tile = re.sub(r'aria-label="[^"]*"', f'aria-label="{label}"', tile)
    else:
        tile = tile.replace("<a ", f'<a aria-label="{label}" ', 1)
    if " href=" not in tile:
        tile = tile.replace(" data-sunday-tile", f' href="{href}" data-sunday-tile', 1)
    tile = re.sub(r'(<span class="sunday-tile-state" data-sunday-state>)[^<]*(</span>)', r'\1abierto\2' if path.startswith("domingos/") else r'\1open\2', tile)
    target.write_text(text[:match.start()] + tile + text[match.end():], encoding="utf-8")


publish_tile("domingos/index.html", ES_ROUTE, "Domingo 03 · publicado")
publish_tile("en/sundays/index.html", EN_ROUTE, "Sunday 03 · published")


def add_world_preview(path: str, language: str) -> None:
    target = ROOT / path
    text = target.read_text(encoding="utf-8")
    if "data-browser-world-preview" in text:
        return
    if language == "es":
        block = """<figure class="lamina oolita-world-preview" data-browser-world-preview>
<img src="/img/oolita-browser-world-preview.jpg" alt="La galería Hallazgo sobre la duna a la hora dorada, la figura y el gato en la senda, Morrón de Mateo y Cerro de la Viña nombrados: modelado sobre Los Escullos, Cabo de Gata." width="1080" height="1350" loading="lazy" decoding="async">
<figcaption>El tercer material: Los Escullos levantado en el navegador. Una imagen; el camino completo abre el 3 de enero.</figcaption>
</figure>"""
    else:
        block = """<figure class="lamina oolita-world-preview" data-browser-world-preview>
<img src="/img/oolita-browser-world-preview.jpg" alt="The Hallazgo gallery on the dune at golden hour, the figure and the cat on the track before it, Morrón de Mateo and Cerro de la Viña named — modelled on Los Escullos, Cabo de Gata." width="1080" height="1350" loading="lazy" decoding="async">
<figcaption>The third material: Los Escullos raised in the browser. One still; the full path opens on 3 January.</figcaption>
</figure>"""
    anchor = re.search(r"<section\b[^>]*\bid=[\"']cabo-de-gata[\"'][^>]*>", text, flags=re.I)
    if not anchor:
        # Later reader-facing transforms may replace the section wrapper while
        # preserving the Cabo de Gata pillar. Insert before that stable route.
        route = "/en/cabo-de-gata/" if language == "en" else "/cabo-de-gata/"
        anchor = re.search(
            rf"<a\b[^>]*href=[\"']{re.escape(route)}[\"'][^>]*>",
            text,
            flags=re.I,
        )
    if not anchor:
        raise SystemExit(f"Homepage Cabo de Gata anchor missing: {path}")
    pos = anchor.start()
    text = text[:pos] + block + text[pos:]
    target.write_text(text, encoding="utf-8")


add_world_preview("index.html", "es")
add_world_preview("en/index.html", "en")


ET.register_namespace("", "http://www.sitemaps.org/schemas/sitemap/0.9")
sitemap = ROOT / "sitemap.xml"
tree = ET.parse(sitemap)
root = tree.getroot()
ns = "http://www.sitemaps.org/schemas/sitemap/0.9"
existing = {el.text for el in root.findall(f"{{{ns}}}url/{{{ns}}}loc")}
for route in (ES_ROUTE, EN_ROUTE):
    loc = "https://oolita.es" + route
    if loc not in existing:
        u = ET.SubElement(root, f"{{{ns}}}url")
        ET.SubElement(u, f"{{{ns}}}loc").text = loc
        ET.SubElement(u, f"{{{ns}}}lastmod").text = "2026-08-24"
tree.write(sitemap, encoding="utf-8", xml_declaration=True)

checks = {
    "domingos/index.html": [ES_ROUTE, "Domingo 03 · publicado"],
    "en/sundays/index.html": [EN_ROUTE, "Sunday 03 · published"],
    "domingos/03-la-memoria-del-mar/index.html": ["La piedra guarda la memoria del mar", "/domingos/img/03.jpg"],
    "en/sundays/03-the-memory-of-the-sea/index.html": ["The stone holds the memory of the sea", "/domingos/img/03.jpg"],
    "index.html": ["data-browser-world-preview", "/img/oolita-browser-world-preview.jpg"],
    "en/index.html": ["data-browser-world-preview", "/img/oolita-browser-world-preview.jpg"],
}
for name, needles in checks.items():
    data = (ROOT / name).read_text(encoding="utf-8")
    for needle in needles:
        if needle not in data:
            raise SystemExit(f"Publication invariant missing in {name}: {needle}")

print("Sunday 03 and controlled browser-world preview validated successfully.")
