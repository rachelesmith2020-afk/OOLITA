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
  site/que-es-un-laberinto/index.html
  site/en/what-is-a-labyrinth/index.html
  site/que-es-un-oolito/index.html
  site/en/what-is-an-ooid/index.html
  site/carteles/index.html
  site/en/posters/index.html
  site/sitemap.xml
  site/robots.txt
  site/favicon.svg
)
for f in "${required[@]}"; do
  if [ ! -f "$f" ]; then
    echo "Missing required deployment file: $f"
    exit 1
  fi
done

grep -Fq 'El mismo camino, hecho de luz.' site/index.html
grep -Fq 'The same path, made of light.' site/en/index.html
grep -Fq 'La misma senda en tres materiales.' site/index.html
grep -Fq 'The same path in three materials.' site/en/index.html
grep -Fq '48-page bilingual fable' site/en/posters/index.html

if grep -RIl --include='*.html' '/cdn-cgi/l/email-protection' site >/tmp/oolita-obfuscated-mail.txt; then
  echo 'Cloudflare-obfuscated email links found in reconstructed origin; refusing to deploy:'
  cat /tmp/oolita-obfuscated-mail.txt
  exit 1
fi

count=$(find site -type f | wc -l | tr -d ' ')
echo "Reconstructed file count: $count"
if [ "$count" -lt 80 ]; then
  echo 'Site reconstruction looks incomplete; refusing to deploy.'
  exit 1
fi

bad=$(find site \( -name '*.bak*' -o -name '*.py' -o -name '*~' -o -name '.DS_Store' \) -print)
if [ -n "$bad" ]; then
  echo 'Refusing to deploy forbidden files:'
  printf '%s\n' "$bad"
  exit 1
fi

echo 'OOLITA deployment bundle validated.'
