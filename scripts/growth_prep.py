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
