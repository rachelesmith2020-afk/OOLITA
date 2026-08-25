#!/usr/bin/env bash
set -euo pipefail

# Run the reviewed site builder, but remove its retired Hallazgo-cover fetch.
python3 - <<'PYWRAP'
from pathlib import Path
src = Path('scripts/build_site_for_deploy_original.sh').read_text(encoding='utf-8')
start = src.index('# Preserve the currently published Hallazgo catalogue cover while deploying')
end = src.index('\nrequired=(', start)
src = src[:start] + '# Hallazgo cover is restored by the wrapper after the reviewed build.\n' + src[end:]
src = src.replace('  site/hallazgo/hallazgo-catalogue-cover.jpg\n', '')
src = src.replace(
    '# Production propagation trigger: preserve published Hallazgo cover while shipping copy update.',
    '# Production propagation trigger: restore verified Hallazgo cover after reviewed build.'
)
Path('/tmp/oolita-build-site-for-deploy.sh').write_text(src, encoding='utf-8')
PYWRAP

bash /tmp/oolita-build-site-for-deploy.sh

# Rebuild the Hallazgo cover from text chunks already committed in the repository.
# This avoids fragile binary uploads and avoids Google/Drive access from Actions.
cover_tmp=/tmp/oolita-hallazgo-cover.jpg
cover_ok=0
candidates=(
  assets/hallazgo-q75-v2
  assets/hallazgo-q75-b64
  assets/hallazgo-cover-b64
  assets/hallazgo-exact-q85-b64
  assets/hallazgo-q90-b64
)

for dir in "${candidates[@]}"; do
  [ -d "$dir" ] || continue
  echo "Trying Hallazgo repository source: $dir"
  rm -f "$cover_tmp" /tmp/oolita-hallazgo-cover.b64
  cat "$dir"/*.txt | tr -d '\r\n[:space:]' > /tmp/oolita-hallazgo-cover.b64
  if base64 --decode /tmp/oolita-hallazgo-cover.b64 > "$cover_tmp" 2>/dev/null; then
    if python3 - "$cover_tmp" <<'PYVALID'
from pathlib import Path
import sys
p=Path(sys.argv[1]); data=p.read_bytes()
if len(data) < 30000:
    raise SystemExit(f'candidate too small: {len(data)} bytes')
if not (data.startswith(b'\xff\xd8') and data.endswith(b'\xff\xd9')):
    raise SystemExit('candidate is not a complete JPEG')
sof={0xC0,0xC1,0xC2,0xC3,0xC5,0xC6,0xC7,0xC9,0xCA,0xCB,0xCD,0xCE,0xCF}
i=2; width=height=None
while i+8 < len(data):
    if data[i] != 0xFF: i += 1; continue
    marker=data[i+1]; i += 2
    if marker in {0xD8,0xD9} or 0xD0 <= marker <= 0xD7: continue
    if i+2 > len(data): break
    length=int.from_bytes(data[i:i+2],'big')
    if marker in sof and i+7 <= len(data):
        height=int.from_bytes(data[i+3:i+5],'big'); width=int.from_bytes(data[i+5:i+7],'big'); break
    if length < 2: break
    i += length
if (width,height)!=(737,822):
    raise SystemExit(f'unexpected Hallazgo dimensions: {width}x{height}')
print(f'Accepted Hallazgo repository JPEG: {width}x{height}, {len(data)} bytes')
PYVALID
    then cover_ok=1; break; fi
  fi
done

if [ "$cover_ok" -ne 1 ]; then
  echo 'No complete 737x822 Hallazgo JPEG could be reconstructed from repository text assets.' >&2
  exit 1
fi

python3 - "$cover_tmp" <<'PY'
from pathlib import Path
import hashlib, sys
src=Path(sys.argv[1]); data=src.read_bytes()
images=Path('site/images'); images.mkdir(parents=True,exist_ok=True)
(images/'hallazgo-cover.png').unlink(missing_ok=True)
asset=images/'hallazgo-cover.jpg'; asset.write_bytes(data)
root='/images/hallazgo-cover.jpg'; absolute='https://oolita.es/images/hallazgo-cover.jpg'
for rel in ('catalogo-hallazgo/index.html','en/hallazgo-catalogue/index.html'):
    p=Path('site')/rel; text=p.read_text(encoding='utf-8')
    text=text.replace('/images/hallazgo-cover.png',root)
    text=text.replace('https://oolita.es/images/hallazgo-cover.png',absolute)
    text=text.replace('https://lh3.googleusercontent.com/d/1zZdwTiVmeEH03uP1f9KkxFU00up4dPRZ=w1000',absolute)
    text=text.replace('content="image/png"','content="image/jpeg"')
    p.write_text(text,encoding='utf-8')
    check=p.read_text(encoding='utf-8')
    if f'src="{root}"' not in check or absolute not in check:
        raise SystemExit(f'Hallazgo first-party image reference missing in {rel}')
    if 'googleusercontent.com' in check or 'drive.google.com' in check or 'drive.usercontent.google.com' in check:
        raise SystemExit(f'Google runtime image reference remains in {rel}')
print('Hallazgo SHA-256:', hashlib.sha256(data).hexdigest())
print(f'First-party Hallazgo cover published: {root}, {len(data)} bytes, image/jpeg')
PY

cat >> site/_redirects <<'EOF'
/hallazgo/hallazgo-catalogue-cover.jpg /images/hallazgo-cover.jpg 301
/hallazgo/hallazgo-catalogue-cover.png /images/hallazgo-cover.jpg 301
EOF

python3 - <<'PY'
from pathlib import Path
updates={
 'index.html':('href="/catalogo-hallazgo/"','href="/catalogo-hallazgo/" onclick="window.location.href=\'/catalogo-hallazgo/?v=20260825-1544\'; return false;"'),
 'en/index.html':('href="/en/hallazgo-catalogue/"','href="/en/hallazgo-catalogue/" onclick="window.location.href=\'/en/hallazgo-catalogue/?v=20260825-1544\'; return false;"')}
for rel,(old,new) in updates.items():
    p=Path('site')/rel; text=p.read_text(encoding='utf-8')
    if new not in text:
        if old not in text: raise SystemExit(f'Hallazgo homepage href not found in {rel}')
        p.write_text(text.replace(old,new,1),encoding='utf-8')
PY

cat >> site/_headers <<'EOF'
/
  Cache-Control: no-store, no-cache, must-revalidate, max-age=0
/en/
  Cache-Control: no-store, no-cache, must-revalidate, max-age=0
/catalogo-hallazgo/
  Cache-Control: no-store, no-cache, must-revalidate, max-age=0
/en/hallazgo-catalogue/
  Cache-Control: no-store, no-cache, must-revalidate, max-age=0
/images/hallazgo-cover.jpg
  Cache-Control: no-cache, must-revalidate, max-age=0
EOF

if [ -f site/404.html ] && [ ! -f site/404/index.html ]; then mkdir -p site/404; cp site/404.html site/404/index.html; fi
if [ -f site/404/index.html ] && [ ! -f site/404.html ]; then cp site/404/index.html site/404.html; fi
python3 scripts/apply_favicon_seo_v1.py site
