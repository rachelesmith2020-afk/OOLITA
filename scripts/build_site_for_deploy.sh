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

# Fetch the exact current Drive file. Google Drive can return an HTML download
# interstitial to non-browser clients, so follow the confirmation form with the
# same cookie jar instead of treating that HTML as the asset.
mkdir -p site/images
python3 - <<'PYFETCH'
from html.parser import HTMLParser
from http.cookiejar import CookieJar
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, build_opener, HTTPCookieProcessor

FILE_ID = '1zZdwTiVmeEH03uP1f9KkxFU00up4dPRZ'
OUT = Path('site/images/hallazgo-cover-v2.png')
PNG = b'\x89PNG\r\n\x1a\n'

class DownloadFormParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_download_form = False
        self.action = None
        self.fields = {}

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'form':
            action = attrs.get('action', '')
            if 'drive.usercontent.google.com/download' in action or '/uc' in action:
                self.in_download_form = True
                self.action = action
                self.fields = {}
        elif tag == 'input' and self.in_download_form:
            name = attrs.get('name')
            value = attrs.get('value', '')
            if name:
                self.fields[name] = value

    def handle_endtag(self, tag):
        if tag == 'form' and self.in_download_form:
            self.in_download_form = False

jar = CookieJar()
opener = build_opener(HTTPCookieProcessor(jar))
headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/151 Safari/537.36',
    'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
}

def fetch(url):
    req = Request(url, headers=headers)
    with opener.open(req, timeout=45) as response:
        return response.headers.get('Content-Type', ''), response.geturl(), response.read()

start = f'https://drive.google.com/uc?export=download&id={FILE_ID}'
content_type, final_url, data = fetch(start)

if not data.startswith(PNG):
    parser = DownloadFormParser()
    parser.feed(data.decode('utf-8', errors='replace'))
    if parser.action:
        fields = dict(parser.fields)
        fields.setdefault('id', FILE_ID)
        fields.setdefault('export', 'download')
        action = parser.action
        sep = '&' if '?' in action else '?'
        content_type, final_url, data = fetch(action + sep + urlencode(fields))

if not data.startswith(PNG):
    # Some Drive responses omit a visible form but accept the confirmation flag.
    direct = f'https://drive.usercontent.google.com/download?id={FILE_ID}&export=download&confirm=t'
    content_type, final_url, data = fetch(direct)

if not data.startswith(PNG):
    prefix = data[:32].hex()
    raise SystemExit(
        'Hallazgo Drive download did not return PNG bytes: '
        f'content_type={content_type!r}, bytes={len(data)}, prefix={prefix}'
    )

OUT.write_bytes(data)
print(f'Hallazgo Drive download resolved to PNG: {len(data)} bytes')
PYFETCH

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
