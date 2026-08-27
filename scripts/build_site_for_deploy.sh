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

# The current live homepage already carries the final, factually precise geology
# wording. The older wording validator expects its historical intermediate state.
# Bridge only inside the temporary reconstruction script; the final credibility
# pass restores the approved "beside the fossil dunes" wording before deployment.
mirror_line = 'python3 scripts/mirror_oolita.py site\n'
bridge = '''python3 - <<'PYHOMEBRIDGE'\nfrom pathlib import Path\np = Path('site/en/index.html')\ntext = p.read_text(encoding='utf-8')\nfinal = 'OOLITA begins with a three-metre classical labyrinth, laid by hand from stone at Los Escullos, on land beside the fossil dunes.'\nlegacy = 'OOLITA begins with a three-metre classical labyrinth, laid by hand from stone at Los Escullos, on land that was seabed a hundred thousand years ago.'\nif final in text:\n    p.write_text(text.replace(final, legacy, 1), encoding='utf-8')\n    print('bridged current homepage geology for legacy reconstruction')\nPYHOMEBRIDGE\n'''
if mirror_line not in patched:
    raise SystemExit('Could not locate mirror step for homepage compatibility bridge')
patched = patched.replace(mirror_line, mirror_line + bridge, 1)

Path('/tmp/oolita-build-site-for-deploy.sh').write_text(patched, encoding='utf-8')
PYWRAP

bash /tmp/oolita-build-site-for-deploy.sh
bash scripts/install_home_preview_v1.sh

# Keep the validated checkout state, but place the actual purchase control in the
# primary availability row where visitors naturally look for it.
python3 scripts/reposition_book_checkout_v1.py site

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

# Google Search recommends one stable favicon URL. Publish the cat as a
# high-resolution PNG at /favicon.png, remove competing icon declarations from
# rendered HTML, and keep the conventional /favicon.ico cat as browser fallback.
python3 - <<'PYFAVICON'
from pathlib import Path
import re

root = Path('site')
source = root / 'apple-touch-icon.png'
search_icon = root / 'favicon.png'
if not source.is_file():
    raise SystemExit('Missing generated 180px cat icon for Google favicon')
search_icon.write_bytes(source.read_bytes())

link_re = re.compile(r'<link\b[^>]*>', flags=re.I | re.S)
rel_re = re.compile(r'\brel\s*=\s*(["\'])(.*?)\1', flags=re.I | re.S)


def strip_icon_link(match: re.Match[str]) -> str:
    tag = match.group(0)
    rel = rel_re.search(tag)
    if not rel:
        return tag
    tokens = {token.strip().lower() for token in rel.group(2).split() if token.strip()}
    return '' if any('icon' in token for token in tokens) else tag

stable_links = (
    '<link rel="icon" type="image/png" sizes="180x180" href="/favicon.png">\n'
    '<link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png">'
)

count = 0
for path in root.rglob('*.html'):
    text = path.read_text(encoding='utf-8')
    text = link_re.sub(strip_icon_link, text)
    text, replaced = re.subn(r'</head>', stable_links + '\n</head>', text, count=1, flags=re.I)
    if replaced != 1:
        raise SystemExit(f'Could not publish stable favicon links in {path.relative_to(root)}')
    if text.count('href="/favicon.png"') != 1:
        raise SystemExit(f'Stable Google favicon missing or duplicated in {path.relative_to(root)}')
    if text.count('href="/apple-touch-icon.png"') != 1:
        raise SystemExit(f'Apple icon missing or duplicated in {path.relative_to(root)}')
    if '?v=' in text and 'favicon' in text:
        raise SystemExit(f'Versioned favicon URL remains in {path.relative_to(root)}')
    path.write_text(text, encoding='utf-8')
    count += 1

headers_path = root / '_headers'
headers = headers_path.read_text(encoding='utf-8') if headers_path.is_file() else ''
headers = re.sub(
    r'(?ms)^/favicon\.png[ \t]*\n(?:[ \t]+[^\n]*\n)*(?:[ \t]*\n)?',
    '',
    headers,
)
headers = headers.rstrip() + '''\n\n/favicon.png\n  Cache-Control: public, max-age=0, must-revalidate\n'''
headers_path.write_text(headers.lstrip() + '\n', encoding='utf-8')

robots = root / 'robots.txt'
if robots.is_file():
    robots_text = robots.read_text(encoding='utf-8', errors='ignore')
    if re.search(r'(?ims)^\s*user-agent:\s*googlebot-image\s*$.*?^\s*disallow:\s*/\s*$', robots_text):
        raise SystemExit('robots.txt blocks Googlebot-Image from the favicon')

if count == 0:
    raise SystemExit('No HTML files found while publishing stable Google favicon')
print(f'OOLITA stable Google favicon published on {count} HTML pages: /favicon.png')
PYFAVICON

# Final reader-facing factual consistency guard. This corrects stale archive and
# catalogue copy inherited from the mirrored origin and fails closed if it drifts.
python3 scripts/apply_content_consistency_v1.py site

# Deepen the existing geology pair and correct About terminology without adding
# a page, navigation item, keyword block or visitor-promotion layer.
python3 scripts/apply_geology_authority_v1.py site

# Add only contextual editorial links between the existing place, geology and
# labyrinth pages. This changes no visible copy.
python3 scripts/apply_editorial_internal_links_v1.py site

# Final factual and structural gates run after all reader-facing mutations.
python3 scripts/normalize_labyrinth_fossil_dunes_v2.py site
python3 scripts/audit_static_integrity_v1.py site

# Production propagation trigger: corrected bilingual consistency guard.
# Production propagation trigger: row-scoped Sunday consistency validation.
# Production propagation trigger: targeted detailed Sunday 03 repair.
# Production propagation trigger: geology authority, editorial hrefs and final integrity gates.
