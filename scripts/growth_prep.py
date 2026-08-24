#!/usr/bin/env python3
from pathlib import Path
import re, sys
ROOT=Path(sys.argv[1] if len(sys.argv)>1 else 'site')

# The final SEO pass publishes a deliberately minimal hard-404 page. On the
# next live-origin reconstruction, older intermediate growth/audit transforms
# still expect the historical homepage-shell 404. Restore that shell only for
# the build pipeline; the SEO pass recreates the hard 404 as the final mutation.
for rel in ('404.html','404/index.html'):
 p=ROOT/rel
 if not p.is_file():
  continue
 s=p.read_text(encoding='utf-8')
 if '<title>404 · OOLITA</title>' in s and 'noindex,follow' in s:
  home=(ROOT/'index.html').read_text(encoding='utf-8')
  p.write_text(home,encoding='utf-8')
  print('growth prep restored homepage-shell 404',rel)

# The final Editions pass explains Hallazgo access through the first-party 3D
# San Felipe replica and points the catalogue link at OOLITA. The legacy release
# calendar still validates the former keyed-castle sentence and Canva href, so
# bridge only those exact final forms back to its intermediate source. The final
# search pass restores the approved first-party copy and href after validation.
hallazgo_access_bridges = {
 'en/editions/index.html': (
  'On the 3D site, the full catalogue of works is housed inside the castle — a digital replica of the 1771 Batería de San Felipe, standing on the fossil dune not far from the labyrinth at Los Escullos. The catalogue is secured by a keypad, and subscribers will receive the code in the launch newsletter.',
  'The full catalogue remains inside the castle, with a key.',
  '/en/hallazgo-catalogue/',
 ),
 'ediciones/index.html': (
  'En el sitio 3D, el catálogo completo de obras se encuentra dentro del castillo — una réplica digital de la Batería de San Felipe de 1771, situada sobre la duna fósil no lejos del laberinto de Los Escullos. El catálogo está protegido por un teclado numérico, y los suscriptores recibirán el código en el boletín de lanzamiento.',
  'El catálogo completo permanece dentro del castillo, con clave.',
  '/catalogo-hallazgo/',
 ),
}
legacy_hallazgo_href='https://hallazgo.my.canva.site/hallazgo/catlogo'
for path,(final_copy,intermediate_copy,final_href) in hallazgo_access_bridges.items():
 p=ROOT/path
 if not p.is_file():
  continue
 s=p.read_text(encoding='utf-8')
 changed=False
 if final_copy in s:
  s=s.replace(final_copy,intermediate_copy,1)
  changed=True
 if f'href="{final_href}"' in s:
  s=s.replace(f'href="{final_href}"',f'href="{legacy_hallazgo_href}"',1)
  changed=True
 if changed:
  p.write_text(s,encoding='utf-8')
  print('growth prep bridged final Hallazgo access copy for',path)

# The final book-voice pass deliberately supersedes older growth copy. The
# growth and soft-marketing layers still validate their historical intermediate
# wording, so normalize only these approved final blocks before those validators.
# apply_voice_audit_v1.py restores the book voice at the end of the pipeline.
voice_bridges = {
 'index.html': [
  (
   'OOLITA seguirá teniendo un solo laberinto: el de Los Escullos. Alrededor de él vendrán publicaciones de campo, pequeñas ediciones textiles y colaboraciones hechas en Cabo de Gata.',
   'OOLITA seguirá siendo un solo laberinto, en Los Escullos. Alrededor de ese camino desarrolla publicaciones de campo, ediciones textiles y colaboraciones arraigadas en Cabo de Gata.'
  ),
  (
   'No se trata de llevar más gente al laberinto. Se trata de mirar Cabo de Gata más despacio, aprender de quien trabaja aquí y dejar el lugar como estaba.',
   'Entre las líneas en desarrollo hay cuadernos para recorrer el territorio en familia, ensayos con color natural y posibles colaboraciones con artesanos locales en torno a saberes materiales como la fibra de pita.'
  ),
 ],
 'en/index.html': [
  (
   'There will still be one OOLITA labyrinth: the one at Los Escullos. Around it will come field publications, small textile editions and collaborations made in Cabo de Gata.',
   'OOLITA will remain one labyrinth at Los Escullos. Around that path it is developing field publications, textile editions and collaborations rooted in Cabo de Gata.'
  ),
  (
   'The point is not to bring more people to one labyrinth. It is to look at Cabo de Gata more slowly, learn from people who work here and leave the place as it was.',
   'Directions in development include field books for family visits, experiments with natural colour, and possible collaborations with local makers around material traditions such as pita fibre.'
  ),
 ],
}
for path,pairs in voice_bridges.items():
 p=ROOT/path
 s=p.read_text(encoding='utf-8')
 changed=False
 for final_voice,intermediate in pairs:
  if final_voice in s:
   s=s.replace(final_voice,intermediate,1)
   changed=True
 if changed:
  p.write_text(s,encoding='utf-8')
  print('growth prep bridged final voice for',path)

# The final attribution layer likewise supersedes the older audit layer's
# intermediate credit wording. A deployment reconstructs from the already-final
# live site, so normalize only those exact final credits before the legacy audit
# validates them. apply_attribution_consistency_v2.py restores the authoritative
# public wording at the end of the search/reader pipeline.
attribution_signature_bridges = {
 'index.html': (
  '<div class="firma"><span class="rot">Raquel Costantini — artista y autora</span><span class="rot">Vestini Tribe — editorial del libro</span></div>',
  '<div class="firma"><span class="rot">Raquel Costantini — artista y autora</span><span class="rot">Vestini Tribe — editorial</span></div>',
 ),
 'en/index.html': (
  '<div class="firma"><span class="rot">Raquel Costantini — artist and author</span><span class="rot">Vestini Tribe — book publisher</span></div>',
  '<div class="firma"><span class="rot">Raquel Costantini — artist and author</span><span class="rot">Vestini Tribe — publisher</span></div>',
 ),
}
for path,(final_credit,intermediate) in attribution_signature_bridges.items():
 p=ROOT/path
 s=p.read_text(encoding='utf-8')
 if final_credit in s:
  p.write_text(s.replace(final_credit,intermediate,1),encoding='utf-8')
  print('growth prep bridged final homepage attribution for',path)

footer_bridges = (
 ('OOLITA · Un proyecto de Raquel Costantini con Vestini Tribe',
  'OOLITA · Raquel Costantini, artista y autora · Vestini Tribe, editorial'),
 ('OOLITA · A project by Raquel Costantini with Vestini Tribe',
  'OOLITA · Raquel Costantini, artist and author · Vestini Tribe, publisher'),
)
bridged_footers=0
for p in sorted(ROOT.rglob('*.html')):
 s=p.read_text(encoding='utf-8')
 changed=False
 for final_credit,intermediate in footer_bridges:
  if final_credit in s:
   s=s.replace(final_credit,intermediate,1)
   changed=True
 if changed:
  p.write_text(s,encoding='utf-8')
  bridged_footers+=1
if bridged_footers:
 print('growth prep bridged final footer attribution on',bridged_footers,'pages')

for path, sentence in [
 ('index.html','OOLITA es un proyecto editorial y de trabajo de campo arraigado en Los Escullos, Cabo de Gata.'),
 ('en/index.html','OOLITA is a place-based publishing and fieldwork project rooted in Los Escullos, Cabo de Gata.'),
]:
 p=ROOT/path; s=p.read_text(encoding='utf-8')
 if sentence in s:
  continue
 m=re.search(r'(<h1\b[^>]*>\s*OOLITA\s*</h1>)',s,flags=re.I)
 if not m:
  raise SystemExit(f'Could not find OOLITA h1 in {path}')
 s=s[:m.end()]+f'<p class="parr definicion">{sentence}</p>'+s[m.end():]
 p.write_text(s,encoding='utf-8')
 print('growth prep patched',path)
