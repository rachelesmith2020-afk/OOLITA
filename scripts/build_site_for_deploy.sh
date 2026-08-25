#!/usr/bin/env bash
set -euo pipefail

# Compatibility wrapper around the reviewed deployment builder. The original
# builder is preserved beside this file. Hallazgo uses the exact PNG uploaded
# to the repository and serves it first-party as /images/hallazgo-cover.png.
python3 - <<'PYWRAP'
from pathlib import Path
source_path = Path('scripts/build_site_for_deploy_original.sh')
source = source_path.read_text(encoding='utf-8')
start_marker = '# Preserve the currently published Hallazgo catalogue cover while deploying'
end_marker = '\nrequired=('
start = source.index(start_marker)
end = source.index(end_marker, start)
replacement = '''# Hallazgo cover is supplied by the repository override after the reviewed builder completes.\n'''
patched = source[:start] + replacement + source[end:]
patched = patched.replace('  site/hallazgo/hallazgo-catalogue-cover.jpg\n', '')
patched = patched.replace('# Production propagation trigger: preserve published Hallazgo cover while shipping copy update.','# Production propagation trigger: ship exact first-party Hallazgo cover.')
Path('/tmp/oolita-build-site-for-deploy.sh').write_text(patched, encoding='utf-8')
PYWRAP

bash /tmp/oolita-build-site-for-deploy.sh

# Install the exact PNG uploaded to GitHub. Do not fetch or transform it.
mkdir -p site/images site/catalogo-hallazgo site/en/hallazgo-catalogue
cp 'overrides/images/Untitled design.png' site/images/hallazgo-cover.png
cp overrides/catalogo-hallazgo/index.html site/catalogo-hallazgo/index.html
cp overrides/en/hallazgo-catalogue/index.html site/en/hallazgo-catalogue/index.html

python3 - <<'PY'
from pathlib import Path
import hashlib
import struct

asset = Path('site/images/hallazgo-cover.png')
data = asset.read_bytes()
expected_sha256 = '70bfe7790ac27c0f1438a0924565510a8404398b08c5532ea8e0c67553aff72f'
actual_sha256 = hashlib.sha256(data).hexdigest()
if actual_sha256 != expected_sha256:
    raise SystemExit(f'Hallazgo PNG checksum mismatch: {actual_sha256}')
if len(data) != 128383:
    raise SystemExit(f'Hallazgo PNG byte length mismatch: {len(data)}')
if not data.startswith(b'\x89PNG\r\n\x1a\n'):
    raise SystemExit('Hallazgo cover is not PNG')
width, height = struct.unpack('>II', data[16:24])
if (width, height) != (737, 822):
    raise SystemExit(f'Hallazgo PNG dimensions mismatch: {width}x{height}')

for rel in ('catalogo-hallazgo/index.html', 'en/hallazgo-catalogue/index.html'):
    page = Path('site') / rel
    text = page.read_text(encoding='utf-8')
    required = (
        '/images/hallazgo-cover.png',
        'https://oolita.es/images/hallazgo-cover.png',
        'content="image/png"',
        'width="737" height="822"',
    )
    for needle in required:
        if needle not in text:
            raise SystemExit(f'Missing Hallazgo reference {needle!r} in {rel}')
    if 'lh3.googleusercontent.com' in text or 'drive.google.com' in text or 'drive.usercontent.google.com' in text:
        raise SystemExit(f'Google-hosted Hallazgo reference remains in {rel}')

print(f'Exact Hallazgo PNG verified: {len(data)} bytes, {width}x{height}, sha256={actual_sha256}')
PY

cat >> site/_redirects <<'EOF'
/hallazgo/hallazgo-catalogue-cover.jpg /images/hallazgo-cover.png 301
/images/hallazgo-cover.jpg /images/hallazgo-cover.png 301
/images/hallazgo-cover-v2.jpg /images/hallazgo-cover.png 301
/images/hallazgo-cover-v2.png /images/hallazgo-cover.png 301
EOF

cat >> site/_headers <<'EOF'
/catalogo-hallazgo/
  Cache-Control: no-store, no-cache, must-revalidate, max-age=0
/en/hallazgo-catalogue/
  Cache-Control: no-store, no-cache, must-revalidate, max-age=0
/images/hallazgo-cover.png
  Cache-Control: no-store, no-cache, must-revalidate, max-age=0
EOF

if [ -f site/404.html ] && [ ! -f site/404/index.html ]; then
  mkdir -p site/404
  cp site/404.html site/404/index.html
elif [ -f site/404/index.html ] && [ ! -f site/404.html ]; then
  cp site/404/index.html site/404.html
fi

python3 scripts/apply_favicon_seo_v1.py site
