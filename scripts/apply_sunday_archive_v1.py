#!/usr/bin/env python3
"""Turn the 22-Sundays index into an accumulating visual archive.

The detailed chronological list remains in place for titles, dates and no-JS
access. A compact 22-cell field is inserted above it and mirrors whatever
Sunday entries are actually linked on the page. Client-side enhancement lets
newly published Sunday links light up without requiring this layer to know the
future titles in advance.
"""
from __future__ import annotations

from datetime import datetime
from html import escape
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET
from zoneinfo import ZoneInfo

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
BASE = "https://oolita.es"
LASTMOD = "2026-08-23"
CHANGED_PATHS = {"/domingos/", "/en/sundays/"}

SUNDAYS = (
    (1, "2026-08-09", "09.08"),
    (2, "2026-08-16", "16.08"),
    (3, "2026-08-23", "23.08"),
    (4, "2026-08-30", "30.08"),
    (5, "2026-09-06", "06.09"),
    (6, "2026-09-13", "13.09"),
    (7, "2026-09-20", "20.09"),
    (8, "2026-09-27", "27.09"),
    (9, "2026-10-04", "04.10"),
    (10, "2026-10-11", "11.10"),
    (11, "2026-10-18", "18.10"),
    (12, "2026-10-25", "25.10"),
    (13, "2026-11-01", "01.11"),
    (14, "2026-11-08", "08.11"),
    (15, "2026-11-15", "15.11"),
    (16, "2026-11-22", "22.11"),
    (17, "2026-11-29", "29.11"),
    (18, "2026-12-06", "06.12"),
    (19, "2026-12-13", "13.12"),
    (20, "2026-12-20", "20.12"),
    (21, "2026-12-27", "27.12"),
    (22, "2027-01-03", "03.01"),
)

STYLE = r'''<style id="oolita-sunday-field-style">
.sunday-field{margin:clamp(2rem,5vw,4.5rem) 0 2rem}
.sunday-field-head{display:flex;align-items:flex-end;justify-content:space-between;gap:1.25rem;margin-bottom:1.35rem}
.sunday-field-count{margin:0;font:inherit;letter-spacing:.02em}
.sunday-field-count strong{font-size:clamp(1.8rem,4vw,3.3rem);font-weight:500;line-height:.9}
.sunday-field-note{max-width:34rem;margin:0;text-align:right;opacity:.7}
.sunday-field-grid{display:grid;grid-template-columns:repeat(11,minmax(0,1fr));gap:clamp(.35rem,.8vw,.7rem);padding:0;margin:0;list-style:none}
.sunday-field-grid li{min-width:0}
.sunday-tile{box-sizing:border-box;display:flex;flex-direction:column;justify-content:space-between;aspect-ratio:1/1;padding:clamp(.45rem,.8vw,.75rem);border:1px solid currentColor;color:inherit;text-decoration:none;opacity:.27;transition:opacity .18s ease,transform .18s ease;cursor:default}
.sunday-tile.is-published{opacity:1;cursor:pointer}
.sunday-tile.is-published:hover,.sunday-tile.is-published:focus-visible{transform:translateY(-2px)}
.sunday-tile.is-current{opacity:.78;outline:2px solid currentColor;outline-offset:3px}
.sunday-tile[data-sunday="11"],.sunday-tile[data-sunday="12"]{border-width:2px}
.sunday-tile[data-sunday="22"]{border-style:double;border-width:3px}
.sunday-tile-n{font-size:clamp(1rem,1.7vw,1.35rem);line-height:1}
.sunday-tile-date{font-size:.72rem;letter-spacing:.05em;opacity:.72}
.sunday-tile-state{min-height:1em;font-size:.62rem;letter-spacing:.08em;text-transform:uppercase;opacity:.72}
.sunday-field-axis{display:flex;justify-content:space-between;gap:1rem;margin:.7rem 0 0;font-size:.7rem;letter-spacing:.06em;text-transform:uppercase;opacity:.58}
@media(max-width:980px){.sunday-field-grid{grid-template-columns:repeat(6,minmax(0,1fr))}}
@media(max-width:640px){.sunday-field-head{display:block}.sunday-field-note{margin-top:.75rem;text-align:left}.sunday-field-grid{grid-template-columns:repeat(4,minmax(0,1fr));gap:.45rem}.sunday-tile{padding:.55rem}.sunday-field-axis{font-size:.62rem}}
@media(prefers-reduced-motion:reduce){.sunday-tile{transition:none}.sunday-tile.is-published:hover,.sunday-tile.is-published:focus-visible{transform:none}}
</style>'''

SCRIPT = r'''<script id="oolita-sunday-field-script">
(()=>{
  const field=document.querySelector('[data-sunday-field]');
  if(!field)return;
  const lang=field.dataset.lang==='en'?'en':'es';
  const rx=lang==='en'?/^\/en\/sundays\/(\d{2})-[^/]+\/$/:/^\/domingos\/(\d{2})-[^/]+\/$/;
  const published=new Map();
  document.querySelectorAll('a[href]').forEach(a=>{
    try{
      const path=new URL(a.getAttribute('href'),location.origin).pathname;
      const m=path.match(rx);
      if(m)published.set(Number(m[1]),a.getAttribute('href'));
    }catch(_){ }
  });
  const parts=Object.fromEntries(new Intl.DateTimeFormat('en-GB',{timeZone:'Europe/Madrid',year:'numeric',month:'2-digit',day:'2-digit'}).formatToParts(new Date()).filter(p=>p.type!=='literal').map(p=>[p.type,p.value]));
  const today=`${parts.year}-${parts.month}-${parts.day}`;
  field.querySelectorAll('[data-sunday-tile]').forEach(tile=>{
    const n=Number(tile.dataset.sunday);
    const href=published.get(n);
    const isToday=tile.dataset.date===today;
    const state=tile.querySelector('[data-sunday-state]');
    tile.classList.toggle('is-published',Boolean(href));
    tile.classList.toggle('is-current',!href&&isToday);
    if(href){
      tile.setAttribute('href',href);
      tile.removeAttribute('aria-disabled');
      state.textContent=lang==='en'?'open':'abierto';
      tile.setAttribute('aria-label',`${lang==='en'?'Sunday':'Domingo'} ${String(n).padStart(2,'0')} · ${lang==='en'?'published':'publicado'}`);
    }else{
      tile.removeAttribute('href');
      tile.setAttribute('aria-disabled','true');
      state.textContent=isToday?(lang==='en'?'today':'hoy'):'';
      tile.setAttribute('aria-label',`${lang==='en'?'Sunday':'Domingo'} ${String(n).padStart(2,'0')} · ${isToday?(lang==='en'?'today':'hoy'):(lang==='en'?'to come':'por venir')}`);
    }
  });
  const count=field.querySelector('[data-sunday-count]');
  if(count)count.textContent=String(published.size);
})();
</script>'''


def existing_links(text: str, language: str) -> dict[int, str]:
    segment = r"en/sundays" if language == "en" else r"domingos"
    pattern = rf'href=["\']([^"\']*/{segment}/(\d{{2}})-[^"\']*/)["\']'
    found: dict[int, str] = {}
    for href, number in re.findall(pattern, text, flags=re.I):
        found[int(number)] = href
    return found


def build_field(language: str, links: dict[int, str]) -> str:
    en = language == "en"
    today = datetime.now(ZoneInfo("Europe/Madrid")).date().isoformat()
    published_count = len(links)
    cells: list[str] = []
    for number, iso_date, short_date in SUNDAYS:
        href = links.get(number)
        classes = ["sunday-tile"]
        state = ""
        attrs = [f'data-sunday-tile', f'data-sunday="{number}"', f'data-date="{iso_date}"']
        if href:
            classes.append("is-published")
            attrs.append(f'href="{escape(href, quote=True)}"')
            state = "open" if en else "abierto"
        else:
            attrs.append('aria-disabled="true"')
            if iso_date == today:
                classes.append("is-current")
                state = "today" if en else "hoy"
        cells.append(
            '<li><a class="' + " ".join(classes) + '" ' + " ".join(attrs) + '>'
            f'<span class="sunday-tile-n">{number:02d}</span>'
            f'<span class="sunday-tile-date">{short_date}</span>'
            f'<span class="sunday-tile-state" data-sunday-state>{state}</span>'
            '</a></li>'
        )

    if en:
        progress = "published · the archive grows each Sunday"
        note = "Entrance → centre → return → exit. Sundays 11 and 12 hold the turn."
        axis_a, axis_b = "inward", "outward"
    else:
        progress = "publicados · el archivo crece cada domingo"
        note = "Entrada → centro → regreso → salida. Los domingos 11 y 12 contienen el giro."
        axis_a, axis_b = "hacia dentro", "hacia fuera"

    return f'''<div class="sunday-field" id="sunday-field" data-sunday-field data-lang="{language}">
  <div class="sunday-field-head">
    <p class="sunday-field-count"><strong data-sunday-count>{published_count}</strong> / 22 · {progress}</p>
    <p class="sunday-field-note">{note}</p>
  </div>
  <ol class="sunday-field-grid" aria-label="{'22 Sundays archive' if en else 'Archivo de 22 domingos'}">
    {''.join(cells)}
  </ol>
  <div class="sunday-field-axis" aria-hidden="true"><span>{axis_a}</span><span>{axis_b}</span></div>
</div>'''


def patch(path: str, language: str) -> None:
    target = ROOT / path
    if not target.is_file():
        raise SystemExit(f"Missing Sundays page: {path}")
    text = target.read_text(encoding="utf-8")
    if 'id="sunday-field"' in text:
        return

    marker = "The path" if language == "en" else "El recorrido"
    detailed = "Detailed archive" if language == "en" else "Archivo detallado"
    match = re.search(rf'<span\b([^>]*)class=["\']rot["\']([^>]*)>\s*{re.escape(marker)}\s*</span>', text, flags=re.I)
    if not match:
        raise SystemExit(f"Sundays archive marker missing in {path}: {marker}")

    links = existing_links(text, language)
    field = build_field(language, links)
    replacement = field + f'\n<span class="rot">{detailed}</span>'
    text = text[:match.start()] + replacement + text[match.end():]

    if 'id="oolita-sunday-field-style"' not in text:
        if "</head>" not in text:
            raise SystemExit(f"No </head> in {path}")
        text = text.replace("</head>", STYLE + "\n</head>", 1)
    if 'id="oolita-sunday-field-script"' not in text:
        if "</body>" not in text:
            raise SystemExit(f"No </body> in {path}")
        text = text.replace("</body>", SCRIPT + "\n</body>", 1)

    target.write_text(text, encoding="utf-8")


if not ROOT.is_dir():
    raise SystemExit(f"Missing built site: {ROOT}")

patch("domingos/index.html", "es")
patch("en/sundays/index.html", "en")

for path, required in {
    "domingos/index.html": [
        'id="sunday-field"',
        'data-lang="es"',
        "Archivo detallado",
        "el archivo crece cada domingo",
        'data-sunday="11"',
        'data-sunday="12"',
        'data-sunday="22"',
        'id="oolita-sunday-field-script"',
    ],
    "en/sundays/index.html": [
        'id="sunday-field"',
        'data-lang="en"',
        "Detailed archive",
        "the archive grows each Sunday",
        'data-sunday="11"',
        'data-sunday="12"',
        'data-sunday="22"',
        'id="oolita-sunday-field-script"',
    ],
}.items():
    text = (ROOT / path).read_text(encoding="utf-8")
    for needle in required:
        if needle not in text:
            raise SystemExit(f"Sunday-field invariant missing in {path}: {needle}")

sitemap = ROOT / "sitemap.xml"
if not sitemap.is_file():
    raise SystemExit("Missing sitemap.xml")
ET.register_namespace("", "http://www.sitemaps.org/schemas/sitemap/0.9")
tree = ET.parse(sitemap)
root = tree.getroot()
ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
seen: set[str] = set()
for url_el in root.findall("sm:url", ns):
    loc = url_el.find("sm:loc", ns)
    if loc is None or not loc.text:
        continue
    url = loc.text.strip()
    if not url.startswith(BASE):
        continue
    route = url[len(BASE):] or "/"
    if route not in CHANGED_PATHS:
        continue
    seen.add(route)
    lastmod = url_el.find("sm:lastmod", ns)
    if lastmod is None:
        lastmod = ET.SubElement(url_el, "{http://www.sitemaps.org/schemas/sitemap/0.9}lastmod")
    lastmod.text = LASTMOD
if seen != CHANGED_PATHS:
    raise SystemExit(f"Sunday archive URLs missing from sitemap: {sorted(CHANGED_PATHS-seen)}")
tree.write(sitemap, encoding="utf-8", xml_declaration=True)

print("OOLITA accumulating Sunday archive validated successfully.")
