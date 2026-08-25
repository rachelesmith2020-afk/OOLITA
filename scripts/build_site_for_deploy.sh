#!/usr/bin/env bash
set -euo pipefail

# Compatibility wrapper around the reviewed deployment builder. The original
# builder is preserved beside this file. This wrapper removes the obsolete
# Hallazgo live-origin cover dependency and uses the versioned first-party
# Hallazgo cover shipped in overrides.
# mirror_oolita.py deliberately skips the replaced broken Hallazgo PNG.
python3 - <<'PYWRAP'
from pathlib import Path

source_path = Path('scripts/build_site_for_deploy_original.sh')
source = source_path.read_text(encoding='utf-8')
start_marker = '# Preserve the currently published Hallazgo catalogue cover while deploying'
end_marker = '\nrequired=('
start = source.index(start_marker)
end = source.index(end_marker, start)
replacement = '''# Hallazgo catalogue cover is supplied by overrides as a versioned first-party JPEG.\n'''
patched = source[:start] + replacement + source[end:]
patched = patched.replace('  site/hallazgo/hallazgo-catalogue-cover.jpg\n', '')
patched = patched.replace(
    '# Production propagation trigger: preserve published Hallazgo cover while shipping copy update.',
    '# Production propagation trigger: ship versioned first-party Hallazgo cover.'
)
Path('/tmp/oolita-build-site-for-deploy.sh').write_text(patched, encoding='utf-8')
PYWRAP

bash /tmp/oolita-build-site-for-deploy.sh

# Validate the repository-owned Hallazgo cover and normalize every catalogue
# image reference to the canonical first-party URL.
python3 - <<'PY'
from pathlib import Path

asset = Path('site/hallazgo/hallazgo-catalogue-cover.jpg')
data = asset.read_bytes()
if not (data.startswith(b'\xff\xd8') and data.endswith(b'\xff\xd9')):
    raise SystemExit('First-party Hallazgo cover is not a valid JPEG')

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

external = 'https://lh3.googleusercontent.com/d/1zZdwTiVmeEH03uP1f9KkxFU00up4dPRZ=w1000'
absolute = 'https://oolita.es/hallazgo/hallazgo-catalogue-cover.jpg'
relative = '/hallazgo/hallazgo-catalogue-cover.jpg'
for rel in ('catalogo-hallazgo/index.html', 'en/hallazgo-catalogue/index.html'):
    page = Path('site') / rel
    text = page.read_text(encoding='utf-8')
    text = text.replace(external, absolute)
    text = text.replace('https://oolita.es/hallazgo/hallazgo-catalogue-cover.png', absolute)
    text = text.replace('/hallazgo/hallazgo-catalogue-cover.png', relative)
    text = text.replace('content="image/png"', 'content="image/jpeg"')
    page.write_text(text, encoding='utf-8')

print(f'First-party Hallazgo cover validated: {width}x{height}, {len(data)} bytes, image/jpeg')
PY

# The live mirror may expose the custom error document as either /404.html or
# /404/index.html. Keep both forms in the deployment bundle; neither changes the
# public URL, and the release layer synchronizes them after validation.
if [ -f site/404.html ] && [ ! -f site/404/index.html ]; then
  mkdir -p site/404
  cp site/404.html site/404/index.html
  echo '404 compatibility mirror created: site/404/index.html'
elif [ -f site/404/index.html ] && [ ! -f site/404.html ]; then
  cp site/404/index.html site/404.html
  echo '404 compatibility mirror created: site/404.html'
fi

# Rebuild every browser/search favicon surface from the published cat icon.
# The mirrored origin can contain a stale legacy favicon.ico, so this runs only
# after reconstruction and 404 normalization and validates every HTML page.
python3 scripts/apply_favicon_seo_v1.py site
