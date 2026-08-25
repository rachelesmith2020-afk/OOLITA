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

# Pull the verified source only during CI, then serve it first-party from OOLITA.
# This avoids fragile binary commits while keeping runtime pages independent of Google.
mkdir -p site/images
cover_tmp=/tmp/oolita-hallazgo-cover.png
rm -f "$cover_tmp"

if ! curl --fail --location --silent --show-error --retry 3 --retry-delay 2 \
  'https://drive.usercontent.google.com/download?id=1zZdwTiVmeEH03uP1f9KkxFU00up4dPRZ&export=view&authuser=0' \
  -o "$cover_tmp"; then
  curl --fail --location --silent --show-error --retry 3 --retry-delay 2 \
    'https://drive.google.com/uc?export=download&id=1zZdwTiVmeEH03uP1f9KkxFU00up4dPRZ' \
    -o "$cover_tmp"
fi

python3 - "$cover_tmp" <<'PY'
from pathlib import Path
import hashlib, struct, sys

src = Path(sys.argv[1])
data = src.read_bytes()
expected_sha256 = '0ba3fb1b897349dca50eb264fde164e9700ac49e63dc62412965f43476186a46'
actual_sha256 = hashlib.sha256(data).hexdigest()
if actual_sha256 != expected_sha256:
    raise SystemExit(f'Hallazgo source digest mismatch: {actual_sha256}')
if not data.startswith(b'\x89PNG\r\n\x1a\n'):
    raise SystemExit('Hallazgo source is not a PNG')
if len(data) < 24 or data[12:16] != b'IHDR':
    raise SystemExit('Hallazgo PNG IHDR missing')
width, height = struct.unpack('>II', data[16:24])
if (width, height) != (737, 822):
    raise SystemExit(f'Unexpected Hallazgo dimensions: {width}x{height}')

images = Path('site/images')
images.mkdir(parents=True, exist_ok=True)
(images / 'hallazgo-cover.jpg').unlink(missing_ok=True)
asset = images / 'hallazgo-cover.png'
asset.write_bytes(data)

root = '/images/hallazgo-cover.png'
absolute = 'https://oolita.es/images/hallazgo-cover.png'
for rel in ('catalogo-hallazgo/index.html', 'en/hallazgo-catalogue/index.html'):
    p = Path('site') / rel
    text = p.read_text(encoding='utf-8')
    text = text.replace('/images/hallazgo-cover.jpg', root)
    text = text.replace('https://oolita.es/images/hallazgo-cover.jpg', absolute)
    text = text.replace('https://lh3.googleusercontent.com/d/1zZdwTiVmeEH03uP1f9KkxFU00up4dPRZ=w1000', absolute)
    text = text.replace('content="image/jpeg"', 'content="image/png"')
    p.write_text(text, encoding='utf-8')
    check = p.read_text(encoding='utf-8')
    if f'src="{root}"' not in check or absolute not in check:
        raise SystemExit(f'Hallazgo first-party image reference missing in {rel}')
    if 'googleusercontent.com' in check or 'drive.google.com' in check or 'drive.usercontent.google.com' in check:
        raise SystemExit(f'Google runtime image reference remains in {rel}')

print(f'Verified Hallazgo cover published: {width}x{height}, {len(data)} bytes, image/png, sha256={actual_sha256}')
PY

cat >> site/_redirects <<'EOF'
/hallazgo/hallazgo-catalogue-cover.jpg /images/hallazgo-cover.png 301
/hallazgo/hallazgo-catalogue-cover.png /images/hallazgo-cover.png 301
/images/hallazgo-cover.jpg /images/hallazgo-cover.png 301
EOF

# Keep SEO-visible hrefs clean while forcing a fresh document URL for in-app browsers.
python3 - <<'PY'
from pathlib import Path
updates={
 'index.html':('href="/catalogo-hallazgo/"','href="/catalogo-hallazgo/" onclick="window.location.href=\'/catalogo-hallazgo/?v=20260825-2143\'; return false;"'),
 'en/index.html':('href="/en/hallazgo-catalogue/"','href="/en/hallazgo-catalogue/" onclick="window.location.href=\'/en/hallazgo-catalogue/?v=20260825-2143\'; return false;"')}
for rel,(old,new) in updates.items():
    p=Path('site')/rel
    text=p.read_text(encoding='utf-8')
    if new not in text:
        if old not in text:
            raise SystemExit(f'Hallazgo homepage href not found in {rel}')
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
/images/hallazgo-cover.png
  Cache-Control: no-cache, must-revalidate, max-age=0
EOF

if [ -f site/404.html ] && [ ! -f site/404/index.html ]; then mkdir -p site/404; cp site/404.html site/404/index.html; fi
if [ -f site/404/index.html ] && [ ! -f site/404.html ]; then cp site/404/index.html site/404.html; fi
python3 scripts/apply_favicon_seo_v1.py site
