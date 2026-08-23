#!/usr/bin/env bash
set -euo pipefail

rm -rf site
python3 scripts/mirror_oolita.py site
python3 scripts/apply_wording_resilient.py site

if [ -d overrides ]; then
  cp -a overrides/. site/
fi

required=(
  site/index.html
  site/en/index.html
  site/laberinto/index.html
  site/en/labyrinth/index.html
  site/domingos/index.html
  site/en/sundays/index.html
  site/que-es-un-laberinto/index.html
  site/en/what-is-a-labyrinth/index.html
  site/que-es-un-oolito/index.html
  site/en/what-is-an-ooid/index.html
  site/carteles/index.html
  site/en/posters/index.html
  site/ediciones/index.html
  site/en/editions/index.html
  site/ediciones/libro/index.html
  site/en/editions/book/index.html
  site/ediciones/camiseta/index.html
  site/en/editions/t-shirt/index.html
  site/sitemap.xml
  site/robots.txt
  site/favicon.svg
  site/fonts/fonts.v3.css
  site/fonts/instrument-sans-var-latin.woff2
  site/fonts/instrument-sans-var-latin-ext.woff2
  site/fonts/instrument-serif-400-normal.woff2
  site/fonts/instrument-serif-400-italic.woff2
  site/laberinto/laberinto-oolita-los-escullos.avif
  site/laberinto/laberinto-oolita-los-escullos.jpg
  site/laberinto/laberinto-oolita-los-escullos-700.avif
  site/laberinto/laberinto-oolita-los-escullos-700.jpg
  site/que-es-un-oolito/diagrama-oolito.avif
  site/que-es-un-oolito/diagrama-oolito.jpg
  site/ediciones/img/blaster-blanca.avif
  site/ediciones/img/blaster-blanca.jpg
  site/domingos/img/01.avif
  site/domingos/img/01.jpg
  site/domingos/img/02.avif
  site/domingos/img/02.jpg
)
for f in "${required[@]}"; do
  if [ ! -f "$f" ]; then
    echo "Missing required deployment file: $f"
    exit 1
  fi
done

# Bank the complete Wednesday Reel line during deployment. Reels are rendered
# from canonical site poster assets plus the approved, repository-banked Abrigo
# sources. Runtime publishing never renders or improvises content.
command -v ffmpeg >/dev/null 2>&1 || {
  echo 'ERROR: ffmpeg is required to build the OOLITA Wednesday reel bank.' >&2
  exit 1
}
python3 scripts/build_wednesday_reels_v1.py site

# Every URL advertised by the current production sitemap must be present in the
# reconstructed deployment folder. This is a current invariant, unlike an old
# historical ZIP file-count.
python3 - <<'PY'
from pathlib import Path
from urllib.parse import urlsplit
import re

root = Path('site')
text = root.joinpath('sitemap.xml').read_text(encoding='utf-8')
locs = re.findall(r'<loc>\s*(.*?)\s*</loc>', text, flags=re.I | re.S)
if not locs:
    raise SystemExit('No URLs found in reconstructed sitemap.xml')
missing = []
for loc in locs:
    path = urlsplit(loc.strip()).path or '/'
    rel = path.lstrip('/')
    candidate = root / rel
    if path.endswith('/'):
        candidate = candidate / 'index.html'
    elif not Path(path).suffix:
        candidate = candidate / 'index.html'
    if not candidate.is_file():
        missing.append((loc.strip(), str(candidate)))
if missing:
    for url, filename in missing:
        print(f'Missing sitemap page: {url} -> {filename}')
    raise SystemExit('Sitemap completeness check failed')
print(f'Sitemap completeness: {len(locs)} URLs present')
PY

# Poster pages deliberately ship all three image encodings.
for i in $(seq 1 9); do
  n=$(printf '%02d' "$i")
  for ext in avif webp png; do
    test -f "site/carteles/img/cartel-${n}.${ext}" || {
      echo "Missing poster asset: site/carteles/img/cartel-${n}.${ext}"
      exit 1
    }
  done
done

grep -Fq 'El mismo camino, hecho de luz.' site/index.html
grep -Fq 'The same path, made of light.' site/en/index.html
grep -Fq 'La misma senda en tres materiales.' site/index.html
grep -Fq 'The same path in three materials.' site/en/index.html
grep -Fq '48-page bilingual fable' site/en/posters/index.html

# The clean origin must not introduce Cloudflare zone-layer email rewriting.
if grep -RIl --include='*.html' '/cdn-cgi/l/email-protection' site >/tmp/oolita-obfuscated-mail.txt; then
  echo 'Cloudflare-obfuscated email links found in reconstructed origin; refusing to deploy:'
  cat /tmp/oolita-obfuscated-mail.txt
  exit 1
fi

bad=$(find site \( -name '*.bak*' -o -name '*.py' -o -name '*~' -o -name '.DS_Store' \) -print)
if [ -n "$bad" ]; then
  echo 'Refusing to deploy forbidden files:'
  printf '%s\n' "$bad"
  exit 1
fi

count=$(find site -type f | wc -l | tr -d ' ')
echo "Validated current-origin deployment file count: $count"
echo 'OOLITA deployment bundle validated.'
