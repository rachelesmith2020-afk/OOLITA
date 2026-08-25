#!/usr/bin/env bash
set -euo pipefail

# Compatibility wrapper around the reviewed deployment builder. The original
# builder is preserved beside this file. Hallazgo ships its cover as a
# first-party asset at /images/hallazgo-cover-v2.png.
python3 - <<'PYWRAP'
from pathlib import Path
source_path = Path('scripts/build_site_for_deploy_original.sh')
source = source_path.read_text(encoding='utf-8')
start_marker = '# Preserve the currently published Hallazgo catalogue cover while deploying'
end_marker = '\nrequired=('
start = source.index(start_marker)
end = source.index(end_marker, start)
replacement = '''# Hallazgo cover is fetched once during deployment, checksum-verified, then served first-party.\n'''
patched = source[:start] + replacement + source[end:]
patched = patched.replace('  site/hallazgo/hallazgo-catalogue-cover.jpg\n', '')
patched = patched.replace('# Production propagation trigger: preserve published Hallazgo cover while shipping copy update.','# Production propagation trigger: ship exact first-party Hallazgo cover.')
Path('/tmp/oolita-build-site-for-deploy.sh').write_text(patched, encoding='utf-8')
PYWRAP

bash /tmp/oolita-build-site-for-deploy.sh

# Fetch the exact current Drive file, then verify it byte-for-byte before it
# enters the site. The source file is currently a PNG.
mkdir -p site/images
curl --fail --location --retry 3 --retry-delay 1 --silent --show-error \
  -A 'Mozilla/5.0' \
  'https://drive.google.com/uc?export=download&id=1zZdwTiVmeEH03uP1f9KkxFU00up4dPRZ' \
  --output site/images/hallazgo-cover-v2.png

python3 - <<'PY'
from pathlib import Path
import hashlib
import struct

asset = Path('site/images/hallazgo-cover-v2.png')
data = asset.read_bytes()
expected = '70bfe7790ac27c0f1438a0924565510a8404398b08c5532ea8e0c67553aff72f'
actual = hashlib.sha256(data).hexdigest()
if actual != expected or len(data) != 128383:
    raise SystemExit(f'Exact Hallazgo cover validation failed: sha256={actual}, bytes={len(data)}')
if not data.startswith(b'\x89PNG\r\n\x1a\n'):
    raise SystemExit('Exact Hallazgo cover is not a PNG')
width, height = struct.unpack('>II', data[16:24])
if (width, height) != (737, 822):
    raise SystemExit(f'Exact Hallazgo cover dimensions invalid: {width}x{height}')

for rel in ('catalogo-hallazgo/index.html','en/hallazgo-catalogue/index.html'):
    page = Path('site') / rel
    text = page.read_text(encoding='utf-8')
    text = text.replace('https://oolita.es/images/hallazgo-cover-v2.jpg','https://oolita.es/images/hallazgo-cover-v2.png')
    text = text.replace('/images/hallazgo-cover-v2.jpg','/images/hallazgo-cover-v2.png')
    text = text.replace('https://oolita.es/images/hallazgo-cover.jpg','https://oolita.es/images/hallazgo-cover-v2.png')
    text = text.replace('/images/hallazgo-cover.jpg','/images/hallazgo-cover-v2.png')
    text = text.replace('width="1377" height="1536"','width="737" height="822"')
    text = text.replace('content="1377"','content="737"')
    text = text.replace('content="1536"','content="822"')
    text = text.replace('"width":1377,"height":1536','"width":737,"height":822')
    page.write_text(text, encoding='utf-8')

print(f'Exact Hallazgo cover verified: {len(data)} bytes, sha256={actual}, dimensions={width}x{height}')
PY

python3 - <<'PY'
from pathlib import Path
for rel in ('catalogo-hallazgo/index.html','en/hallazgo-catalogue/index.html'):
    text = (Path('site') / rel).read_text(encoding='utf-8')
    if 'src="/images/hallazgo-cover-v2.png"' not in text:
        raise SystemExit(f'Exact Hallazgo image src missing in {rel}')
    if 'https://oolita.es/images/hallazgo-cover-v2.png' not in text:
        raise SystemExit(f'Exact Hallazgo metadata image missing in {rel}')
    if 'width="737" height="822"' not in text:
        raise SystemExit(f'Correct Hallazgo dimensions missing in {rel}')
    if 'lh3.googleusercontent.com' in text or 'drive.google.com' in text:
        raise SystemExit(f'Google-hosted Hallazgo reference remains in {rel}')
PY

cat >> site/_redirects <<'EOF'
/hallazgo/hallazgo-catalogue-cover.jpg /images/hallazgo-cover-v2.png 301
/images/hallazgo-cover.jpg /images/hallazgo-cover-v2.png 302
/images/hallazgo-cover-v2.jpg /images/hallazgo-cover-v2.png 301
EOF

python3 - <<'PY'
from pathlib import Path
updates = {
    'index.html': ('href="/catalogo-hallazgo/"', 'href="/catalogo-hallazgo/" onclick="window.location.href=\'/catalogo-hallazgo/?v=20260825-1939\'; return false;"'),
    'en/index.html': ('href="/en/hallazgo-catalogue/"', 'href="/en/hallazgo-catalogue/" onclick="window.location.href=\'/en/hallazgo-catalogue/?v=20260825-1939\'; return false;"'),
}
for rel, (old, new) in updates.items():
    page = Path('site') / rel
    text = page.read_text(encoding='utf-8')
    if new not in text:
        if old not in text:
            raise SystemExit(f'Hallazgo homepage href not found in {rel}')
        page.write_text(text.replace(old, new, 1), encoding='utf-8')
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
/images/hallazgo-cover-v2.png
  Cache-Control: no-store, no-cache, must-revalidate, max-age=0
EOF

if [ -f site/404.html ] && [ ! -f site/404/index.html ]; then
  mkdir -p site/404
  cp site/404.html site/404/index.html
elif [ -f site/404/index.html ] && [ ! -f site/404.html ]; then
  cp site/404/index.html site/404.html
fi

python3 scripts/apply_favicon_seo_v1.py site
