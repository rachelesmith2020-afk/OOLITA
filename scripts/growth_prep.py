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
