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

cover_tmp=/tmp/oolita-hallazgo-cover
cover_ok=0
sources=(
  'https://lh3.googleusercontent.com/rd-d/ALs6j_FfcSc4FQu6zcOis04sPOfAm9DPBKieAt_0l21AZG-q8NkCFHnO45vHXk_wN_j0LV6zJAY3s5V1Rtm-tL6lDbQgZ6i8TLMArUM3Rf3tjLR0v576ZEtJyuQDLYjvvvbCIsHsTNLNCLy3PlcQT1Xg5uIH5WtwTK0bKtPYsA15PThuVLKwEb0-tH2OTZqUP41ju-MgLhCaxkLumeYRnbiuKSenxX-q51FKQHbNh-llAkFwfHLnJUdwriTbekbwbL7hBYmlQWSyPZTRDWyBVqQHmUve-Os8vnuuYeJNYcDLZmIwu8vyquB8bEXtaEb8q7vdOQzhMSPcdrx1OAlDOYHWdiOdZagXpM2ZGYwPMLYKwB8LuCnYU7BSjJIFu_WZegBnp_riBV9v5RM6cyMvQGb18rq5NoBqAVU2MqvfSxr8146Af8qsBxvsdfW3Fi32oNXBUgmr5QKXRPg1pSyWszlEigkjHLabnq8Xq5IymVM7WeNi4XvW8GFwk2eBfTYO8MSPDUAg9FTEZb56ClxiIurwwId0eASvtkEqLuEcyN4oGUl9VF6RUmwYMuBRFX_svuuaTorGy_C7KCW8D5CDabHcnLN-Bx52ya1E4ivy3eFG4w9eAPxqS5VgYmZVlVgXypqfNbmXJQ-6AHugT-O2tS-UK0VHZyl9rUuxjLssyjeoYzMmsndJcfDi6rYvrIiOFbztKh0_BApPOhlViw4qkv7ofFaK91PwRVHLoSf6-L48aG32gt-znw3fMBbbq9SWd0RB8qgLM8refhHbOYMNIHxzlmCAZNkJpesLsNQq2jZbKu8-LzCmVz6ad-O1gqfVeBwpj5CDW3UABljqajLgngiOy8k1zkVqePcmo_czNAcFU1Gj08w7OgnhL-RSuKPgLNylWIqs5_6Qz0GBTonpskywCXmnmm2ruGVNo6mlikF9ovD6-saBqK5QMXnFgMB5APJFrBw97k7Ya2cf8z4YTib0yqaWPKHISExZO6Fmd-FrAi453NBxvJDq74hDJIcPxgVUHZvsl_ZCCPB4LWTTIjR-7bAunpEZirLWowtYZ7LNugaFmYy7YP95nvoM5LnmgC6JYD0Eb8tXN4tzQyOMzUXL3Ul5vuPUfj-nSMzzSePgxZj-xBWZxfd4LNU7dtD7-i8=s16383-w1000'
  'https://drive.usercontent.google.com/download?id=1zZdwTiVmeEH03uP1f9KkxFU00up4dPRZ&export=view&authuser=0'
  'https://lh3.googleusercontent.com/d/1zZdwTiVmeEH03uP1f9KkxFU00up4dPRZ=w1000'
)

for source in "${sources[@]}"; do
  rm -f "$cover_tmp"
  echo "Trying Hallazgo cover source"
  if curl --fail --location --retry 3 --retry-all-errors --retry-delay 1 \
      --connect-timeout 15 --max-time 90 --silent --show-error \
      -H 'Accept: image/jpeg,image/png;q=0.9,*/*;q=0.1' \
      -H 'User-Agent: Mozilla/5.0' \
      "$source" --output "$cover_tmp"; then
    if python3 - "$cover_tmp" <<'PYVALID'
from pathlib import Path
import struct, sys
p = Path(sys.argv[1]); data = p.read_bytes()
if len(data) < 30000:
    raise SystemExit(f'cover response too small: {len(data)} bytes')
fmt = None; width = height = None
if data.startswith(b'\x89PNG\r\n\x1a\n'):
    if len(data) < 33 or not data.endswith(b'\x00\x00\x00\x00IEND\xaeB`\x82'):
        raise SystemExit('PNG source is incomplete')
    width, height = struct.unpack('>II', data[16:24]); fmt='png'
elif data.startswith(b'\xff\xd8') and data.endswith(b'\xff\xd9'):
    sof={0xC0,0xC1,0xC2,0xC3,0xC5,0xC6,0xC7,0xC9,0xCA,0xCB,0xCD,0xCE,0xCF}
    i=2
    while i+8 < len(data):
        if data[i] != 0xFF: i += 1; continue
        marker=data[i+1]; i += 2
        if marker in {0xD8,0xD9} or 0xD0 <= marker <= 0xD7: continue
        if i+2 > len(data): break
        length=int.from_bytes(data[i:i+2],'big')
        if marker in sof and i+7 <= len(data):
            height=int.from_bytes(data[i+3:i+5],'big'); width=int.from_bytes(data[i+5:i+7],'big'); break
        if length < 2: break
        i += length
    fmt='jpg'
else:
    raise SystemExit('cover response is neither PNG nor complete JPEG')
if (width,height)!=(737,822):
    raise SystemExit(f'unexpected Hallazgo cover dimensions: {width}x{height}')
print(f'Accepted Hallazgo source: {fmt}, {width}x{height}, {len(data)} bytes')
PYVALID
    then cover_ok=1; break; fi
  fi
done

if [ "$cover_ok" -ne 1 ]; then
  echo 'Unable to obtain a complete Hallazgo cover from verified sources.' >&2
  exit 1
fi

python3 - "$cover_tmp" <<'PY'
from pathlib import Path
import sys
src=Path(sys.argv[1]); data=src.read_bytes()
if data.startswith(b'\x89PNG\r\n\x1a\n'):
    ext='png'; mime='image/png'
else:
    ext='jpg'; mime='image/jpeg'
images=Path('site/images'); images.mkdir(parents=True,exist_ok=True)
for stale in (images/'hallazgo-cover.jpg', images/'hallazgo-cover.png'):
    stale.unlink(missing_ok=True)
asset=images/f'hallazgo-cover.{ext}'; asset.write_bytes(data)
root=f'/images/hallazgo-cover.{ext}'; absolute=f'https://oolita.es/images/hallazgo-cover.{ext}'
for rel in ('catalogo-hallazgo/index.html','en/hallazgo-catalogue/index.html'):
    p=Path('site')/rel; text=p.read_text(encoding='utf-8')
    text=text.replace('/images/hallazgo-cover.jpg',root).replace('/images/hallazgo-cover.png',root)
    text=text.replace('https://oolita.es/images/hallazgo-cover.jpg',absolute).replace('https://oolita.es/images/hallazgo-cover.png',absolute)
    text=text.replace('https://lh3.googleusercontent.com/d/1zZdwTiVmeEH03uP1f9KkxFU00up4dPRZ=w1000',absolute)
    text=text.replace('content="image/jpeg"',f'content="{mime}"').replace('content="image/png"',f'content="{mime}"')
    p.write_text(text,encoding='utf-8')
    check=p.read_text(encoding='utf-8')
    if f'src="{root}"' not in check or absolute not in check:
        raise SystemExit(f'Hallazgo first-party image reference missing in {rel}')
    if 'googleusercontent.com' in check or 'drive.google.com' in check or 'drive.usercontent.google.com' in check:
        raise SystemExit(f'Google runtime image reference remains in {rel}')
Path('/tmp/oolita-hallazgo-cover-path').write_text(root,encoding='utf-8')
print(f'First-party Hallazgo cover published: {root}, {len(data)} bytes, {mime}')
PY

cover_path="$(cat /tmp/oolita-hallazgo-cover-path)"
cat >> site/_redirects <<EOF
/hallazgo/hallazgo-catalogue-cover.jpg $cover_path 301
/hallazgo/hallazgo-catalogue-cover.png $cover_path 301
EOF

python3 - <<'PY'
from pathlib import Path
updates={
 'index.html':('href="/catalogo-hallazgo/"','href="/catalogo-hallazgo/" onclick="window.location.href=\'/catalogo-hallazgo/?v=20260825-1544\'; return false;"'),
 'en/index.html':('href="/en/hallazgo-catalogue/"','href="/en/hallazgo-catalogue/" onclick="window.location.href=\'/en/hallazgo-catalogue/?v=20260825-1544\'; return false;"')}
for rel,(old,new) in updates.items():
    p=Path('site')/rel; text=p.read_text(encoding='utf-8')
    if new not in text:
        if old not in text: raise SystemExit(f'Hallazgo homepage href not found in {rel}')
        p.write_text(text.replace(old,new,1),encoding='utf-8')
PY

cat >> site/_headers <<EOF
/
  Cache-Control: no-store, no-cache, must-revalidate, max-age=0
/en/
  Cache-Control: no-store, no-cache, must-revalidate, max-age=0
/catalogo-hallazgo/
  Cache-Control: no-store, no-cache, must-revalidate, max-age=0
/en/hallazgo-catalogue/
  Cache-Control: no-store, no-cache, must-revalidate, max-age=0
$cover_path
  Cache-Control: no-cache, must-revalidate, max-age=0
EOF

if [ -f site/404.html ] && [ ! -f site/404/index.html ]; then mkdir -p site/404; cp site/404.html site/404/index.html; fi
if [ -f site/404/index.html ] && [ ! -f site/404.html ]; then cp site/404/index.html site/404.html; fi
python3 scripts/apply_favicon_seo_v1.py site
