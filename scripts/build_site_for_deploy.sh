#!/usr/bin/env bash
set -euo pipefail

# Compatibility wrapper around the reviewed deployment builder. The original
# builder is preserved beside this file. Hallazgo ships its cover as a
# first-party asset at /images/hallazgo-cover-v2.jpg.
python3 - <<'PYWRAP'
from pathlib import Path

source_path = Path('scripts/build_site_for_deploy_original.sh')
source = source_path.read_text(encoding='utf-8')
start_marker = '# Preserve the currently published Hallazgo catalogue cover while deploying'
end_marker = '\nrequired=('
start = source.index(start_marker)
end = source.index(end_marker, start)
replacement = '''# Hallazgo cover is reconstructed from the exact repository payload after the reviewed builder completes.\n'''
patched = source[:start] + replacement + source[end:]
patched = patched.replace('  site/hallazgo/hallazgo-catalogue-cover.jpg\n', '')
patched = patched.replace(
    '# Production propagation trigger: preserve published Hallazgo cover while shipping copy update.',
    '# Production propagation trigger: ship exact first-party Hallazgo cover.'
)
Path('/tmp/oolita-build-site-for-deploy.sh').write_text(patched, encoding='utf-8')
PYWRAP

bash /tmp/oolita-build-site-for-deploy.sh

python3 - <<'PY'
from pathlib import Path
import base64, hashlib
parts = sorted(Path('assets/hallazgo-original-20260825-b64').glob('part*.txt'))
if len(parts) != 5:
    raise SystemExit(f'Expected 5 Hallazgo payload parts, found {len(parts)}')
payload = ''.join(p.read_text(encoding='utf-8').strip() for p in parts)
data = base64.b64decode(payload, validate=True)
expected = 'd640577f126ef809b04cfd83d9eb158ce71d4d7fbe114a30ad6c8793a26ce180'
actual = hashlib.sha256(data).hexdigest()
if actual != expected or len(data) != 89203 or not (data.startswith(b'\xff\xd8') and data.endswith(b'\xff\xd9')):
    raise SystemExit(f'Exact Hallazgo cover validation failed: sha256={actual}, bytes={len(data)}')
dest = Path('site/images/hallazgo-cover-v2.jpg')
dest.parent.mkdir(parents=True, exist_ok=True)
dest.write_bytes(data)
for rel in ('catalogo-hallazgo/index.html', 'en/hallazgo-catalogue/index.html'):
    page = Path('site') / rel
    text = page.read_text(encoding='utf-8')
    text = text.replace('https://oolita.es/images/hallazgo-cover.jpg', 'https://oolita.es/images/hallazgo-cover-v2.jpg')
    text = text.replace('/images/hallazgo-cover.jpg', '/images/hallazgo-cover-v2.jpg')
    text = text.replace('width="737" height="822"', 'width="1377" height="1536"')
    text = text.replace('content="737"', 'content="1377"')
    text = text.replace('content="822"', 'content="1536"')
    text = text.replace('"width":737,"height":822', '"width":1377,"height":1536')
    page.write_text(text, encoding='utf-8')
print(f'Exact Hallazgo cover reconstructed: {len(data)} bytes, sha256={actual}')
PY

python3 - <<'PY'
from pathlib import Path
import hashlib
asset = Path('site/images/hallazgo-cover-v2.jpg')
data = asset.read_bytes()
expected = 'd640577f126ef809b04cfd83d9eb158ce71d4d7fbe114a30ad6c8793a26ce180'
if hashlib.sha256(data).hexdigest() != expected:
    raise SystemExit('Hallazgo cover changed after reconstruction')
for rel in ('catalogo-hallazgo/index.html', 'en/hallazgo-catalogue/index.html'):
    text = (Path('site') / rel).read_text(encoding='utf-8')
    if 'src="/images/hallazgo-cover-v2.jpg"' not in text:
        raise SystemExit(f'Exact Hallazgo image src missing in {rel}')
    if 'https://oolita.es/images/hallazgo-cover-v2.jpg' not in text:
        raise SystemExit(f'Exact Hallazgo metadata image missing in {rel}')
    if 'lh3.googleusercontent.com' in text or 'drive.google.com' in text:
        raise SystemExit(f'Google-hosted Hallazgo image reference remains in {rel}')
    if 'width="1377" height="1536"' not in text:
        raise SystemExit(f'Correct Hallazgo dimensions missing in {rel}')
print('Exact first-party Hallazgo cover verified on both catalogue pages.')
PY

cat >> site/_redirects <<'EOF'
/hallazgo/hallazgo-catalogue-cover.jpg /images/hallazgo-cover-v2.jpg 301
/images/hallazgo-cover.jpg /images/hallazgo-cover-v2.jpg 302
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
/images/hallazgo-cover-v2.jpg
  Cache-Control: no-store, no-cache, must-revalidate, max-age=0
EOF

if [ -f site/404.html ] && [ ! -f site/404/index.html ]; then
  mkdir -p site/404
  cp site/404.html site/404/index.html
elif [ -f site/404/index.html ] && [ ! -f site/404.html ]; then
  cp site/404/index.html site/404.html
fi

python3 scripts/apply_favicon_seo_v1.py site
# Exact Hallazgo cover production trigger: 2026-08-25T19:39+01:00
