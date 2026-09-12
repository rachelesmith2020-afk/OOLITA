#!/usr/bin/env python3
"""Restore Sundays 04/05 from Metricool's confirmed published posts.

Run after the legacy Sunday transforms, before the final static audit.
Future scheduled posts and draft Reels are deliberately not publication evidence.
"""
from pathlib import Path
from html import escape
import json
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else 'site')
BASE = 'https://oolita.es'
POSTS = [
    dict(n=4, date='2026-08-30', short='30.08.26', es='El guardián', en='The Guardian',
         es_slug='04-el-guardian', en_slug='04-the-guardian',
         instagram='https://www.instagram.com/p/DcrAFHdiCd_/',
         image='https://static.metricool.com/planner/202608/6767285-file-11209243474009143100.jpg',
         alt='La Batería de San Felipe, del siglo XVIII, sobre la duna fósil de oolita frente al mar en Los Escullos, Cabo de Gata, cerca del laberinto. · The 18th-century Batería de San Felipe standing on the oolitic fossil dune above the sea at Los Escullos, Cabo de Gata, near the labyrinth.',
         es_text="La Batería de San Felipe, mil setecientos setenta y uno. Una de las de Carlos III, entre Garrucha y Manilva.\nSe levanta sobre ocho metros de la misma duna fósil que da nombre al laberinto, trescientos veinticinco metros al norte.\nFuerte y laberinto comparten cimiento: piedra que fue mar.\nDentro del mundo guardará las cuarenta y cuatro obras.",
         en_text="The Batería de San Felipe, seventeen seventy-one. One of Carlos III's, between Garrucha and Manilva.\nIt stands on eight metres of the same fossil dune that names the labyrinth, three hundred and twenty-five metres to the north.\nFort and labyrinth share a footing: stone that was once sea.\nInside the world it will hold the forty-four works."),
    dict(n=5, date='2026-09-06', short='06.09.26', es='El mundo', en='The World',
         es_slug='05-el-mundo', en_slug='05-the-world',
         instagram='https://www.instagram.com/p/Dc9Bop-COdr/',
         image='https://static.metricool.com/planner/202608/6767285-file-1415095040247793992.jpg',
         alt='La galería Hallazgo sobre la duna a la hora dorada, la figura y el gato en la senda, Morrón de Mateo y Cerro de la Viña nombrados: modelado sobre Los Escullos, Cabo de Gata. · The Hallazgo gallery on the dune at golden hour, the figure and the cat on the track before it, Morrón de Mateo and Cerro de la Viña named — modelled on Los Escullos, Cabo de Gata.',
         es_text='Esto no es una fotografía. Es el mismo terreno, medido y vuelto a levantar.\nLa galería que guardará las cuarenta y cuatro obras, y delante, la figura y el gato en la senda.\nLos cerros conservan sus nombres: Morrón de Mateo, Cerro de la Viña.\nNada de esto se ha inventado. Se ha registrado.',
         en_text='This is not a photograph. It is the same ground, measured and raised again.\nThe gallery that will hold the forty-four works, and before it, the figure and the cat on the track.\nThe hills keep their names: Morrón de Mateo, Cerro de la Viña.\nNone of it was invented. It was recorded.'),
]

def route(p, lang):
    return ('/domingos/' if lang == 'es' else '/en/sundays/') + p[lang + '_slug'] + '/'

def once(pattern, replacement, text, label):
    text, count = re.subn(pattern, lambda m: replacement(m) if callable(replacement) else replacement,
                          text, count=1, flags=re.S)
    if count != 1:
        raise SystemExit('Missing expected markup: ' + label)
    return text

def paragraphs(text):
    return ''.join('<p>' + escape(line) + '</p>' for line in text.splitlines())

def img(p, lazy=True):
    return (f'<img src="/domingos/img/{p["n"]:02}.jpg" alt="{escape(p["alt"], quote=True)}" '
            f'loading="{"lazy" if lazy else "eager"}" decoding="async" style="max-width:100%;height:auto">')

def write(rel, text):
    path = ROOT / rel.lstrip('/')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')

# Download the exact published media, never a screenshot or a generated substitute.
for p in POSTS:
    target = ROOT / f'domingos/img/{p["n"]:02}.jpg'
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.is_file():
        req = urllib.request.Request(p['image'], headers={'User-Agent': 'OOLITA archive repair'})
        with urllib.request.urlopen(req, timeout=45) as response:
            data = response.read()
        if len(data) < 1000 or not data.startswith(b'\xff\xd8'):
            raise SystemExit('Invalid published JPEG: ' + p['image'])
        target.write_bytes(data)

templates = {'es': '/domingos/03-la-memoria-del-mar/', 'en': '/en/sundays/03-the-memory-of-the-sea/'}
for p in POSTS:
    for lang in ('es', 'en'):
        other = 'en' if lang == 'es' else 'es'
        text = (ROOT / (templates[lang].lstrip('/') + 'index.html')).read_text(encoding='utf-8')
        for locale, old in templates.items():
            text = text.replace(old, route(p, locale))
        label = f'{"Domingo" if lang == "es" else "Sunday"} {p["n"]:02} {"de" if lang == "es" else "of"} 22 · {p["short"]}'
        article = (f'<article class="tramo" data-metricool-published="{p["date"]}"><span class="rot">{label}</span>'
                   f'<h1 class="grande">{escape(p[lang])}</h1><p class="lema-en" lang="{other}">{escape(p[other])}</p>'
                   f'<figure class="lamina">{img(p, False)}</figure><div class="cuento">{paragraphs(p[lang+"_text"])}'
                   f'<div class="otroidioma" lang="{other}">{paragraphs(p[other+"_text"])}</div></div>'
                   f'<p><a href="{p["instagram"]}">{"Ver publicación en Instagram" if lang == "es" else "View Instagram post"} ↗</a></p></article>')
        text = once(r'<article\b[^>]*>.*?</article>', article, text, 'Sunday article')
        text = re.sub(r'<section\b[^>]*data-sunday-context[^>]*>.*?</section>', '', text, flags=re.S)
        # Template navigation must point at the actual previous Sunday.
        previous = POSTS[0] if p['n'] == 5 else None
        prev_route = route(previous, lang) if previous else templates[lang]
        prev_title = previous[lang] if previous else ('La memoria del mar' if lang == 'es' else 'The Memory of the Sea')
        text = once(r'<a class="fila" href="/(?:domingos/02-el-gato-de-verdad|en/sundays/02-the-cat-for-real)/">.*?</a>',
                    f'<a class="fila" href="{prev_route}"><span class="num">{p["n"]-1:02}</span><span class="cuerpo"><span class="nombre">{escape(prev_title)}</span><span class="glo">{"Domingo anterior" if lang == "es" else "Previous Sunday"}</span></span><span class="flecha">←</span></a>', text, 'previous Sunday')
        title = p[lang] + ' — ' + label + ' · OOLITA'
        text = once(r'<title>.*?</title>', '<title>' + escape(title) + '</title>', text, 'title')
        published = p['date'] + 'T19:00:00+02:00'
        values = {'description': p[lang+'_text'].splitlines()[0], 'og:title': title, 'twitter:title': title,
                  'og:description': p[lang+'_text'].splitlines()[0], 'twitter:description': p[lang+'_text'].splitlines()[0],
                  'og:url': BASE + route(p, lang), 'og:image': BASE + f'/domingos/img/{p["n"]:02}.jpg',
                  'og:image:secure_url': BASE + f'/domingos/img/{p["n"]:02}.jpg', 'twitter:image': BASE + f'/domingos/img/{p["n"]:02}.jpg',
                  'og:image:alt': p['alt'], 'article:published_time': published, 'article:modified_time': published}
        def meta(m):
            tag = m[0]
            key = re.search(r'(?:name|property)="([^"]+)"', tag)
            if key and key[1] in ('og:image:width', 'og:image:height'):
                return ''
            if key and key[1] in values:
                return re.sub(r'content="[^"]*"', lambda _: 'content="' + escape(values[key[1]], quote=True) + '"', tag)
            return tag
        text = re.sub(r'<meta\b[^>]*>', meta, text)
        text = re.sub(r'<script\b[^>]*type="application/ld\+json"[^>]*>.*?</script>', '', text, flags=re.S)
        schema = {'@context': 'https://schema.org', '@type': 'Article', 'url': BASE+route(p,lang), 'headline': p[lang],
                  'datePublished': published, 'dateModified': published, 'inLanguage': lang, 'position': p['n'],
                  'image': BASE+f'/domingos/img/{p["n"]:02}.jpg', 'author': {'@type':'Person','name':'Raquel Costantini'},
                  'isPartOf': {'@type':'CollectionPage','url': BASE+('/domingos/' if lang == 'es' else '/en/sundays/')},
                  'isAccessibleForFree': True, 'sameAs': p['instagram']}
        text = text.replace('</head>', '<script type="application/ld+json">'+json.dumps(schema, ensure_ascii=False)+'</script>\n</head>')
        write(route(p, lang) + 'index.html', text)

for lang, rel in (('es','domingos/index.html'), ('en','en/sundays/index.html')):
    text = (ROOT / rel).read_text(encoding='utf-8')
    other = 'en' if lang == 'es' else 'es'
    for p in POSTS:
        n = p['n']
        thumb = '<span class="sunday-archive-thumb" aria-hidden="true">'+img(p)+'</span>'
        tile = (f'<li><a class="sunday-image-tile is-published" href="{route(p,lang)}" data-sunday-image-tile data-sunday="{n}" '
                f'data-date="{p["date"]}" aria-label="{n:02} · {escape(p[lang], quote=True)} · {p["short"]}">{thumb}</a></li>')
        text = once(r'<li>(?:(?!</li>).)*data-sunday="'+str(n)+r'".*?</li>', tile, text, 'archive tile '+str(n))
        row = (f'<a class="fila" href="{route(p,lang)}" data-sunday-archive-row="{n}">{thumb}<span class="num">{n:02}</span>'
               f'<span class="cuerpo"><span class="nombre">{escape(p[lang])}</span><span class="glo" lang="{other}">{escape(p[other])}</span></span>'
               f'<time class="cuando" datetime="{p["date"]}">{p["short"]}</time><span class="flecha">→</span></a>')
        pattern = r'<div class="fila espera"><span class="num">'+f'{n:02}'+r'</span>.*?</div>|<a\b[^>]*data-sunday-archive-row="'+str(n)+r'"[^>]*>.*?</a>'
        text = once(pattern, row, text, 'archive row '+str(n))
    # Count linked archive rows rather than elapsed dates; future items stay pending.
    count = len(set(re.findall(r'data-sunday-archive-row="(\d+)"', text)))
    # Older 01/02 entries may not carry the row attribute.
    count = len(set(re.findall(r'href="/(?:domingos|en/sundays)/(\d{2})-[^"/]+/"', text)))
    text = once(r'(<strong\b[^>]*data-sunday-count[^>]*>).*?(</strong>)', lambda m: m[1]+str(count)+m[2], text, 'published count')
    write(rel, text)

# Advance the current-Sunday panel using the same published source.
latest = POSTS[-1]
for lang, rel in (('es','index.html'), ('en','en/index.html')):
    text = (ROOT / rel).read_text(encoding='utf-8')
    label = f'05 · {latest[lang]} · {latest["short"]}'
    panel = (f'<section id="oolita-art-field-sundays" class="art-field art-field--gold" aria-label="{label}" data-current-sunday="05">'
             f'<span class="art-kicker">05 · {latest[lang].upper()}</span><p class="art-word" aria-hidden="true">05</p>'
             f'<p class="art-caption">{latest["short"]} · {escape(latest[lang+"_text"].splitlines()[0])}</p>'
             f'<a class="oolita-current-sunday-hit" href="{route(latest,lang)}" aria-label="{label}"></a></section>')
    text = once(r'<section\b[^>]*id="oolita-art-field-sundays"[^>]*>.*?</section>', panel, text, 'homepage Sunday')
    write(rel, text)

ns = 'http://www.sitemaps.org/schemas/sitemap/0.9'
ET.register_namespace('', ns)
sitemap = ROOT / 'sitemap.xml'
tree = ET.parse(sitemap)
urls = {element.findtext('{'+ns+'}loc'): element for element in tree.getroot()}
for p in POSTS:
    for lang in ('es','en'):
        url = BASE + route(p,lang)
        if url not in urls:
            item = ET.SubElement(tree.getroot(), '{'+ns+'}url')
            ET.SubElement(item, '{'+ns+'}loc').text = url
            ET.SubElement(item, '{'+ns+'}lastmod').text = p['date']
tree.write(sitemap, encoding='utf-8', xml_declaration=True)

for p in POSTS:
    for lang in ('es', 'en'):
        text = (ROOT / (route(p,lang).lstrip('/')+'index.html')).read_text(encoding='utf-8')
        for line in (p['es_text']+'\n'+p['en_text']).splitlines():
            assert escape(line) in text, 'Published text changed'
        assert f'rel="canonical" href="{BASE+route(p,lang)}"' in text
        assert p['instagram'] in text
print('Published Sundays 04 and 05: bilingual pages, exact media, archive links, homepage and sitemap verified.')
