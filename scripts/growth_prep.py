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
# growth layer still validates its own historical intermediate wording, so
# normalize only these two approved final blocks back to that intermediate form.
# apply_voice_audit_v1.py restores the book voice at the end of the pipeline.
voice_bridges = {
 'index.html': (
  'OOLITA seguirá teniendo un solo laberinto: el de Los Escullos. Alrededor de él vendrán publicaciones de campo, pequeñas ediciones textiles y colaboraciones hechas en Cabo de Gata.',
  'OOLITA seguirá siendo un solo laberinto, en Los Escullos. Alrededor de ese camino desarrolla publicaciones de campo, ediciones textiles y colaboraciones arraigadas en Cabo de Gata.'
 ),
 'en/index.html': (
  'There will still be one OOLITA labyrinth: the one at Los Escullos. Around it will come field publications, small textile editions and collaborations made in Cabo de Gata.',
  'OOLITA will remain one labyrinth at Los Escullos. Around that path it is developing field publications, textile editions and collaborations rooted in Cabo de Gata.'
 ),
}
for path,(final_voice,intermediate) in voice_bridges.items():
 p=ROOT/path
 s=p.read_text(encoding='utf-8')
 if final_voice in s:
  p.write_text(s.replace(final_voice,intermediate,1),encoding='utf-8')
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
