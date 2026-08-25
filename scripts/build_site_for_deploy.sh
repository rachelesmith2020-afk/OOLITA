#!/usr/bin/env bash
set -euo pipefail

rm -rf site
python3 scripts/mirror_oolita.py site
python3 scripts/apply_wording_resilient.py site
# The current live origin already carries the safer access wording. Normalize
# its structured FAQ copy before the older direction validator checks it.
python3 scripts/normalize_labyrinth_access_faq_v1.py site

if [ -d overrides ]; then
  cp -a overrides/. site/
fi

# Reconstruct the sharp Hallazgo catalogue cover from the staged source chunks.
# This deliberately overwrites the old low-resolution mirrored JPEG on every deploy.
if compgen -G 'assets/hallazgo-q75-v2/part*.txt' >/dev/null; then
  mkdir -p site/hallazgo
  cat assets/hallazgo-q75-v2/part*.txt | tr -d '\r\n' | base64 --decode > site/hallazgo/hallazgo-catalogue-cover.jpg
  python3 - <<'PY'
from pathlib import Path
p = Path('site/hallazgo/hallazgo-catalogue-cover.jpg')
data = p.read_bytes()
if not (data.startswith(b'\xff\xd8') and data.endswith(b'\xff\xd9')):
    raise SystemExit('Hallazgo cover reconstruction did not produce a valid JPEG')
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
print(f'Hallazgo cover reconstructed and validated: {width}x{height}, {len(data)} bytes')
PY
fi

required=(
  site/index.html
  site/en/index.html
  site/laberinto/index.html
  site/en/labyrinth/index.html
  site/domingos/index.html
  site/en/sundays/index.html
  site/que-es-un-laberinto/index.html
  site/en/what-is-a-labyrinth/index.html
  site/que-es-un-oolito/index.html
  site/en/what-is-an-ooid/index.html
  site/carteles/index.html
  site/en/posters/index.html
  site/ediciones/index.html
  site/en/editions/index.html
  site/ediciones/libro/index.html
  site/en/editions/book/index.html
  site/ediciones/camiseta/index.html
  site/en/editions/t-shirt/index.html
  site/catalogo-hallazgo/index.html
  site/en/hallazgo-catalogue/index.html
  site/hallazgo/hallazgo-catalogue-cover.jpg
  site/sitemap.xml
  site/robots.txt
  site/favicon.svg
  site/fonts/fonts.v3.css
  site/fonts/instrument-sans-var-latin.woff2
  site/fonts/instrument-sans-var-latin-ext.woff2
  site/fonts/instrument-serif-400-normal.woff2
  site/fonts/instrument-serif-400-italic.woff2
  site/laberinto/laberinto-oolita-los-escullos.avif
  site/laberinto/laberinto-oolita-los-escullos.jpg
  site/laberinto/laberinto-oolita-los-escullos-700.avif
  site/laberinto/laberinto-oolita-los-escullos-700.jpg
  site/que-es-un-oolito/diagrama-oolito.avif
  site/que-es-un-oolito/diagrama-oolito.jpg
  site/ediciones/img/blaster-blanca.avif
  site/ediciones/img/blaster-blanca.jpg
  site/domingos/img/01.avif
  site/domingos/img/01.jpg
  site/domingos/img/02.avif
  site/domingos/img/02.jpg
)
for f in "${required[@]}"; do
  if [ ! -f "$f" ]; then
    echo "Missing required deployment file: $f"
    exit 1
  fi
done

# Retire the Wednesday/Reels page completely. The current origin may still
# contain the old page while this deploy is being reconstructed, so remove the
# page, reverse every link/copy insertion that advertised it, remove it from the
# sitemap, and leave permanent redirects for any already-shared old URLs.
python3 - <<'PY'
from pathlib import Path
import re
import shutil

root = Path('site')
replacements = {
    'index.html': (
        '\n  <a class="fila" href="/reels/"><span class="n">R</span><span class="nom">Los miércoles</span><span class="glo">Nueve carteles en movimiento · sin música</span></a>',
        '',
    ),
    'en/index.html': (
        '\n  <a class="fila" href="/reels/"><span class="n">R</span><span class="nom">The Wednesdays</span><span class="glo">Nine posters in motion · no music</span></a>',
        '',
    ),
    'carteles/index.html': (
        'Los carteles también se mueven: <a href="/reels/">nueve reels silenciosos, uno cada miércoles</a>. Después de los carteles, una imagen cada domingo hasta la apertura:',
        'Después de los carteles, una imagen cada domingo hasta la apertura:',
    ),
    'en/posters/index.html': (
        'The posters also move: <a href="/reels/">nine silent reels, one each Wednesday</a>. After the posters, one image every Sunday until the opening:',
        'After the posters, one image every Sunday until the opening:',
    ),
    'domingos/index.html': (
        'La serie no empezó aquí. Antes de los domingos hubo <a href="/carteles/">nueve carteles</a>, y esos carteles volvieron <a href="/reels/">en movimiento, uno cada miércoles</a>',
        'La serie no empezó aquí. Antes de los domingos hubo <a href="/carteles/">nueve carteles</a>',
    ),
    'en/sundays/index.html': (
        'The series did not start here. Before the Sundays there were <a href="/en/posters/">nine posters</a>, and those posters returned <a href="/reels/">in motion, one each Wednesday</a>',
        'The series did not start here. Before the Sundays there were <a href="/en/posters/">nine posters</a>',
    ),
}

for relative, (old, new) in replacements.items():
    path = root / relative
    text = path.read_text(encoding='utf-8')
    if old in text:
        path.write_text(text.replace(old, new, 1), encoding='utf-8')

sitemap = root / 'sitemap.xml'
text = sitemap.read_text(encoding='utf-8')
text = re.sub(
    r'\s*<url>\s*<loc>https://oolita\.es/reels/</loc>.*?</url>\s*',
    '\n',
    text,
    flags=re.I | re.S,
)
sitemap.write_text(text, encoding='utf-8')

shutil.rmtree(root / 'reels', ignore_errors=True)

redirects = root / '_redirects'
existing = redirects.read_text(encoding='utf-8') if redirects.exists() else ''
rules = [
    '/reels /carteles/ 301',
    '/reels/ /carteles/ 301',
    '/reels/* /carteles/ 301',
]
lines = existing.splitlines()
for rule in rules:
    if rule not in lines:
        lines.append(rule)
redirects.write_text('\n'.join(line for line in lines if line.strip()) + '\n', encoding='utf-8')

bad = []
needles = (
    'href="/reels/"',
    "href='/reels/'",
    'https://oolita.es/reels/',
    '>The Wednesdays<',
    '>Los miércoles<',
    'Nine posters in motion · no music',
    'Nueve carteles en movimiento · sin música',
)
for path in root.rglob('*'):
    if not path.is_file() or path.name == '_redirects':
        continue
    if path.suffix.lower() not in {'.html', '.xml', '.json', '.txt', '.js', '.css'}:
        continue
    content = path.read_text(encoding='utf-8', errors='ignore')
    for needle in needles:
        if needle in content:
            bad.append(f'{path}: {needle}')
if (root / 'reels').exists():
    bad.append('site/reels still exists')
if bad:
    print('Wednesday/Reels retirement left stragglers:')
    print('\n'.join(bad))
    raise SystemExit(1)
print('Wednesday/Reels page retired: links removed, sitemap clean, legacy URLs redirected.')
PY

# Every URL advertised by the current production sitemap must be present in the
# reconstructed deployment folder. This is a current invariant, unlike an old
# historical ZIP file-count.
python3 - <<'PY'
from pathlib import Path
from urllib.parse import urlsplit
import re

root = Path('site')
text = root.joinpath('sitemap.xml').read_text(encoding='utf-8')
locs = re.findall(r'<loc>\s*(.*?)\s*</loc>', text, flags=re.I | re.S)
if not locs:
    raise SystemExit('No URLs found in reconstructed sitemap.xml')
missing = []
for loc in locs:
    path = urlsplit(loc.strip()).path or '/'
    rel = path.lstrip('/')
    candidate = root / rel
    if path.endswith('/'):
        candidate = candidate / 'index.html'
    elif not Path(path).suffix:
        candidate = candidate / 'index.html'
    if not candidate.is_file():
        missing.append((loc.strip(), str(candidate)))
if missing:
    for url, filename in missing:
        print(f'Missing sitemap page: {url} -> {filename}')
    raise SystemExit('Sitemap completeness check failed')
print(f'Sitemap completeness: {len(locs)} URLs present')
PY

# Poster pages deliberately ship all three image encodings.
for i in $(seq 1 9); do
  n=$(printf '%02d' "$i")
  for ext in avif webp png; do
    test -f "site/carteles/img/cartel-${n}.${ext}" || {
      echo "Missing poster asset: site/carteles/img/cartel-${n}.${ext}"
      exit 1
    }
  done
done

grep -Fq 'El camino, domingo a domingo.' site/index.html
grep -Fq 'The path, one Sunday at a time.' site/en/index.html
grep -Fq 'La misma senda en tres materiales.' site/index.html
grep -Fq 'The same path in three materials.' site/en/index.html
grep -Fq '48-page bilingual fable' site/en/posters/index.html

# Re-apply the final visual spacing layer to the mirrored live origin on every
# reconstruction. The layer replaces its own prior style block, preventing an
# obsolete desktop/laptop PIEDRA or STONE rule from surviving future deploys.
python3 scripts/apply_visual_spacing_cleanup_v1.py site

# The Sunday art field lives inside the hero's narrow right column. Prevent the
# general viewport-width art-field rule from covering the desktop hero copy.
python3 scripts/apply_desktop_sunday_panel_fix_v1.py site

# Re-apply the final WCAG contrast layer on every reconstruction. This prevents
# older opacity-based secondary-text styling from returning via the live mirror.
python3 scripts/apply_contrast_accessibility_v1.py site

# Repair the two mobile regressions inherited from the mirrored origin: constrain
# the browser-world preview to the viewport and restore compact 22-Sundays tiles.
python3 scripts/apply_mobile_layout_repairs_v1.py site

# Keep the English 3D-world launch notice in natural, direct English and ensure
# its signup path survives the reconstruction unchanged.
python3 scripts/apply_launch_notice_wording_v1.py site
grep -Fq 'Leave your email with OOLITA and we’ll let you know when it opens.' site/en/3d-world/index.html
if grep -Fq 'That day the link opens. If you want the notice, leave your email with OOLITA.' site/en/3d-world/index.html; then
  echo 'Old 3D-world launch notice survived the wording pass.'
  exit 1
fi
grep -Fq 'href="/en/?follow=3d#follow-oolita"' site/en/3d-world/index.html

# The clean origin must not introduce Cloudflare zone-layer email rewriting.
if grep -RIl --include='*.html' '/cdn-cgi/l/email-protection' site >/tmp/oolita-obfuscated-mail.txt; then
  echo 'Cloudflare-obfuscated email links found in reconstructed origin; refusing to deploy:'
  cat /tmp/oolita-obfuscated-mail.txt
  exit 1
fi

bad=$(find site \( -name '*.bak*' -o -name '*.py' -o -name '*~' -o -name '.DS_Store' \) -print)
if [ -n "$bad" ]; then
  echo 'Refusing to deploy forbidden files:'
  printf '%s\n' "$bad"
  exit 1
fi

count=$(find site -type f | wc -l | tr -d ' ')
echo "Validated current-origin deployment file count: $count"
echo 'OOLITA deployment bundle validated.'
# Production propagation trigger: desktop Sunday-panel containment.
# Production propagation trigger: integrated desktop, reels and 3D fixes.
# Production propagation trigger: mobile world-preview and Sunday-field repairs.
# Production propagation trigger: resilient labyrinth access FAQ normalization.
# Production propagation trigger: Veriditas credential compatibility bridge.
# Production propagation trigger: retire the Wednesday/Reels page cleanly.
# Production propagation trigger: validate the English 3D launch notice and follow href.
# Production propagation trigger: rebuild sharp Hallazgo catalogue cover and SEO.
