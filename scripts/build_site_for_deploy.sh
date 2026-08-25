#!/usr/bin/env bash
set -euo pipefail

# Compatibility wrapper around the reviewed deployment builder. The original
# builder is preserved beside this file. Hallazgo uses the reviewed first-party
# cover in overrides/hallazgo/ so in-app browsers never depend on Google Drive.
python3 - <<'PYWRAP'
from pathlib import Path

source_path = Path('scripts/build_site_for_deploy_original.sh')
source = source_path.read_text(encoding='utf-8')
start_marker = '# Preserve the currently published Hallazgo catalogue cover while deploying'
end_marker = '\nrequired=('
start = source.index(start_marker)
end = source.index(end_marker, start)
replacement = '''# Hallazgo cover is supplied by overrides/hallazgo/hallazgo-catalogue-cover.jpg.\n'''
patched = source[:start] + replacement + source[end:]
patched = patched.replace(
    '# Production propagation trigger: preserve published Hallazgo cover while shipping copy update.',
    '# Production propagation trigger: serve Hallazgo cover from first-party override.'
)
Path('/tmp/oolita-build-site-for-deploy.sh').write_text(patched, encoding='utf-8')
PYWRAP

bash /tmp/oolita-build-site-for-deploy.sh

# Enforce the first-party Hallazgo cover after all reviewed transforms. This
# deliberately removes the previous Google Drive fallback and keeps metadata,
# preload, structured data and the visible image on the same oolita.es asset.
python3 - <<'PY'
from pathlib import Path

external = 'https://lh3.googleusercontent.com/d/1zZdwTiVmeEH03uP1f9KkxFU00up4dPRZ=w1000'
absolute = 'https://oolita.es/hallazgo/hallazgo-catalogue-cover.jpg'
relative = '/hallazgo/hallazgo-catalogue-cover.jpg'
asset = Path('site/hallazgo/hallazgo-catalogue-cover.jpg')
if not asset.is_file():
    raise SystemExit('Missing first-party Hallazgo cover')
data = asset.read_bytes()
if not (data.startswith(b'\xff\xd8') and data.endswith(b'\xff\xd9')):
    raise SystemExit('First-party Hallazgo cover is not a valid JPEG')

for rel in ('catalogo-hallazgo/index.html', 'en/hallazgo-catalogue/index.html'):
    page = Path('site') / rel
    text = page.read_text(encoding='utf-8')
    text = text.replace(external, absolute)
    text = text.replace('https://oolita.es/hallazgo/hallazgo-catalogue-cover.png', absolute)
    text = text.replace('/hallazgo/hallazgo-catalogue-cover.png', relative)
    text = text.replace('content="image/png"', 'content="image/jpeg"')
    page.write_text(text, encoding='utf-8')
    if 'googleusercontent.com' in text:
        raise SystemExit(f'Google-hosted Hallazgo cover survived in {rel}')
    if 'hallazgo-catalogue-cover.jpg' not in text:
        raise SystemExit(f'First-party Hallazgo cover missing from {rel}')

redirects = Path('site/_redirects')
if redirects.exists():
    lines = redirects.read_text(encoding='utf-8').splitlines()
    lines = [line for line in lines if not line.strip().startswith('/hallazgo/hallazgo-catalogue-cover.jpg ')]
    redirects.write_text('\n'.join(lines) + ('\n' if lines else ''), encoding='utf-8')

print(f'Hallazgo cover first-party: {len(data)} bytes at {absolute}')
PY

# Keep the SEO-visible href canonical and validator-safe, but on an actual user
# click route Instagram's in-app browser to a versioned Hallazgo document URL.
python3 - <<'PY'
from pathlib import Path
import re

updates = {
    'index.html': (
        'href="/catalogo-hallazgo/"',
        'href="/catalogo-hallazgo/" onclick="window.location.href=\'/catalogo-hallazgo/?v=20260825-1813\'; return false;"'
    ),
    'en/index.html': (
        'href="/en/hallazgo-catalogue/"',
        'href="/en/hallazgo-catalogue/" onclick="window.location.href=\'/en/hallazgo-catalogue/?v=20260825-1813\'; return false;"'
    ),
}
for rel, (old, new) in updates.items():
    page = Path('site') / rel
    text = page.read_text(encoding='utf-8')
    pattern = re.escape(old) + r"(?: onclick=\"window\.location\.href='[^']+'; return false;\")?"
    text2, n = re.subn(pattern, new, text, count=1)
    if n != 1:
        raise SystemExit(f'Hallazgo homepage href not found in {rel}')
    page.write_text(text2, encoding='utf-8')

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
/hallazgo/hallazgo-catalogue-cover.jpg
  Cache-Control: public, max-age=3600
EOF

# Keep both custom-404 filesystem forms available to downstream validators.
if [ -f site/404.html ] && [ ! -f site/404/index.html ]; then
  mkdir -p site/404
  cp site/404.html site/404/index.html
elif [ -f site/404/index.html ] && [ ! -f site/404.html ]; then
  cp site/404/index.html site/404.html
fi

python3 scripts/apply_favicon_seo_v1.py site
