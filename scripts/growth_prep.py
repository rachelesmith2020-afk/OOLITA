#!/usr/bin/env python3
from pathlib import Path
import re, sys
ROOT=Path(sys.argv[1] if len(sys.argv)>1 else 'site')
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
