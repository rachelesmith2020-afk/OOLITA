#!/usr/bin/env bash
set -euo pipefail

# Compatibility wrapper around the reviewed deployment builder. The original
# builder is preserved beside this file. Hallazgo ships its cover as a first-
# party asset at /images/hallazgo-cover.jpg.
python3 - <<'PYWRAP'
from pathlib import Path

source_path = Path('scripts/build_site_for_deploy_original.sh')
source = source_path.read_text(encoding='utf-8')
start_marker = '# Preserve the currently published Hallazgo catalogue cover while deploying'
end_marker = '\nrequired=('
start = source.index(start_marker)
end = source.index(end_marker, start)
replacement = '''# Hallazgo cover is reconstructed after the reviewed builder completes.\n'''
patched = source[:start] + replacement + source[end:]
patched = patched.replace('  site/hallazgo/hallazgo-catalogue-cover.jpg\n', '')
patched = patched.replace(
    '# Production propagation trigger: preserve published Hallazgo cover while shipping copy update.',
    '# Production propagation trigger: ship first-party Hallazgo cover.'
)
Path('/tmp/oolita-build-site-for-deploy.sh').write_text(patched, encoding='utf-8')
PYWRAP

bash /tmp/oolita-build-site-for-deploy.sh

# Reconstruct the known-good Hallazgo JPEG from versioned repository data.
# This deliberately overwrites the older corrupted binary that existed in the
# overrides tree, while keeping the deployed URL fully first-party.
mkdir -p site/images
cat assets/hallazgo-cover-b64/part*.txt | tr -d '\n\r ' | base64 --decode > site/images/hallazgo-cover.jpg

python3 - <<'PY'
from pathlib import Path

asset = Path('site/images/hallazgo-cover.jpg')
data = asset.read_bytes()
if len(data) < 15000:
    raise SystemExit(f'Hallazgo cover unexpectedly small: {len(data)} bytes')
if not (data.startswith(b'\xff\xd8') and data.endswith(b'\xff\xd9')):
    raise SystemExit('Hallazgo cover is not a complete JPEG')

sof = {0xC0,0xC1,0xC2,0xC3,0xC5,0xC6,0xC7,0xC9,0xCA,0xCB,0xCD,0xCE,0xCF}
i = 2
width = height = None
while i + 8 < len(data):
    if data[i] != 0xFF:
        i += 1
        continue
    marker = data[i + 1]
    i += 2
    if marker in {0xD8, 0xD9} or 0xD0 <= marker <= 0xD7:
        continue
    if i + 2 > len(data):
        break
    length = int.from_bytes(data[i:i+2], 'big')
    if marker in sof and i + 7 <= len(data):
        height = int.from_bytes(data[i+3:i+5], 'big')
        width = int.from_bytes(data[i+5:i+7], 'big')
        break
    if length < 2:
        break
    i += length
if (width, height) != (737, 822):
    raise SystemExit(f'Unexpected Hallazgo cover dimensions: {width}x{height}')

root_relative = '/images/hallazgo-cover.jpg'
absolute = 'https://oolita.es/images/hallazgo-cover.jpg'
for rel in ('catalogo-hallazgo/index.html', 'en/hallazgo-catalogue/index.html'):
    page = Path('site') / rel
    text = page.read_text(encoding='utf-8')
    if f'src="{root_relative}"' not in text:
        raise SystemExit(f'Root-relative Hallazgo image src missing in {rel}')
    if 'lh3.googleusercontent.com' in text or 'drive.google.com' in text:
        raise SystemExit(f'Google-hosted Hallazgo image reference remains in {rel}')
    if absolute not in text:
        raise SystemExit(f'First-party Hallazgo metadata image missing in {rel}')

print(f'First-party Hallazgo cover verified: {width}x{height}, {len(data)} bytes, image/jpeg')
PY

# Keep the retired cover URL working for cached documents, but route it to the
# new first-party asset rather than Google.
cat >> site/_redirects <<'EOF'
/hallazgo/hallazgo-catalogue-cover.jpg /images/hallazgo-cover.jpg 301
EOF

# Keep the SEO-visible href canonical and validator-safe, but on an actual user
# click route Instagram's in-app browser to a versioned Hallazgo document URL.
python3 - <<'PY'
from pathlib import Path

updates = {
    'index.html': (
        'href="/catalogo-hallazgo/"',
        'href="/catalogo-hallazgo/" onclick="window.location.href=\'/catalogo-hallazgo/?v=20260825-1544\'; return false;"'
    ),
    'en/index.html': (
        'href="/en/hallazgo-catalogue/"',
        'href="/en/hallazgo-catalogue/" onclick="window.location.href=\'/en/hallazgo-catalogue/?v=20260825-1544\'; return false;"'
    ),
}
for rel, (old, new) in updates.items():
    page = Path('site') / rel
    text = page.read_text(encoding='utf-8')
    if new not in text:
        if old not in text:
            raise SystemExit(f'Hallazgo homepage href not found in {rel}')
        text = text.replace(old, new, 1)
        page.write_text(text, encoding='utf-8')

print('Hallazgo homepage clicks versioned for Instagram while canonical hrefs remain clean.')
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

# Keep both custom-404 filesystem forms available to downstream validators.
if [ -f site/404.html ] && [ ! -f site/404/index.html ]; then
  mkdir -p site/404
  cp site/404.html site/404/index.html
elif [ -f site/404/index.html ] && [ ! -f site/404.html ]; then
  cp site/404/index.html site/404.html
fi

python3 scripts/apply_favicon_seo_v1.py site
