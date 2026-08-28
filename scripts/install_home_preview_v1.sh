#!/usr/bin/env bash
set -euo pipefail

# Install the approved homepage Three.js preview as a first-party asset.
# Keep the canonical asset path required by the publication/SEO validators, but
# append a cache-busting query string in homepage markup so browsers do not
# retain an older preview. The approved source is 800x450, so desktop rendering
# must never enlarge it beyond its intrinsic width; doing so makes it visibly
# soft and can exaggerate the wide aspect ratio.
mkdir -p site/img

tmp_preview="$(mktemp)"
staged_ok=0
if cat overrides/images/oolita-home-preview-640-b64/part-*.b64 | tr -d '\r\n\t ' | base64 -d > "$tmp_preview" 2>/dev/null; then
  if python3 - "$tmp_preview" <<'PY'
from pathlib import Path
import hashlib
import sys

asset = Path(sys.argv[1])
data = asset.read_bytes()
expected_sha256 = '247fe78afa9c9f7be9b307c8e37b99b9fb2d24488aed3e2ce408d9490409b1d1'
if hashlib.sha256(data).hexdigest() != expected_sha256:
    raise SystemExit('Homepage preview checksum mismatch')
if len(data) != 28490:
    raise SystemExit(f'Homepage preview byte-length mismatch: {len(data)}')
if not data.startswith(b'\xff\xd8'):
    raise SystemExit('Homepage preview is not JPEG')

def jpeg_size(blob: bytes):
    i = 2
    sof = {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}
    while i < len(blob):
        if blob[i] != 0xFF:
            i += 1
            continue
        while i < len(blob) and blob[i] == 0xFF:
            i += 1
        if i >= len(blob):
            break
        marker = blob[i]
        i += 1
        if marker in {0xD8, 0xD9}:
            continue
        if i + 2 > len(blob):
            break
        seglen = int.from_bytes(blob[i:i+2], 'big')
        if marker in sof and i + 7 <= len(blob):
            height = int.from_bytes(blob[i+3:i+5], 'big')
            width = int.from_bytes(blob[i+5:i+7], 'big')
            return width, height
        if seglen < 2:
            break
        i += seglen
    return None

size = jpeg_size(data)
if size != (800, 450):
    raise SystemExit(f'Homepage preview dimensions mismatch: {size}')
PY
  then
    mv "$tmp_preview" site/img/oolita-browser-world-preview.jpg
    staged_ok=1
    echo 'Homepage Three.js preview installed: 800x450, green poster spine.'
  fi
fi

if [ "$staged_ok" -ne 1 ]; then
  rm -f "$tmp_preview"
  echo 'Homepage preview staging invalid/incomplete; refusing to publish a stale fallback.' >&2
  exit 1
fi

# The Sunday-03 publication layer predates the approved green-spine still and
# still contains a legacy Google Drive download for the old blue-spine image.
# It runs later in the same deployment, so without this guard it silently
# overwrites the correct asset after this installer has succeeded. Disable that
# one obsolete download in the checked-out build workspace. The Sunday image
# download and all homepage markup logic in that layer remain untouched.
python3 - <<'PY'
from pathlib import Path

publisher = Path('scripts/publish_sunday03_and_3d_preview_v1.py')
if not publisher.is_file():
    raise SystemExit(f'Missing later preview publisher: {publisher}')
text = publisher.read_text(encoding='utf-8')
legacy = 'download(WORLD_IMAGE, ROOT / "img/oolita-browser-world-preview.jpg")'
guarded = '''# Homepage browser-world preview is owned by install_home_preview_v1.sh.
# Do not restore the retired Drive-hosted blue-spine still here.
world_preview = ROOT / "img/oolita-browser-world-preview.jpg"
if not world_preview.is_file():
    raise SystemExit(f"Approved homepage preview missing before Sunday publication: {world_preview}")'''
if legacy in text:
    text = text.replace(legacy, guarded, 1)
    publisher.write_text(text, encoding='utf-8')
elif 'Homepage browser-world preview is owned by install_home_preview_v1.sh.' not in text:
    raise SystemExit('Legacy world-preview download changed unexpectedly; refusing an ambiguous deployment')
print('Later Sunday publication prevented from overwriting the approved homepage preview.')
PY

python3 - <<'PY'
from pathlib import Path
import re

bare = '/img/oolita-browser-world-preview.jpg'
versioned = '/img/oolita-browser-world-preview.jpg?v=green-fit-20260828-1202'
style_id = 'oolita-home-preview-desktop-fit'
style = f'''<style id="{style_id}">
/* The approved green-spine still is 800x450. Never upscale it on desktop. */
figure.oolita-world-preview,
figure[data-browser-world-preview]{{
  box-sizing:border-box!important;
  width:min(100%,800px)!important;
  max-width:800px!important;
  margin:2.5rem auto!important;
  overflow:visible!important;
}}
figure.oolita-world-preview img,
figure[data-browser-world-preview] img{{
  box-sizing:border-box!important;
  display:block!important;
  width:100%!important;
  max-width:800px!important;
  height:auto!important;
  max-height:none!important;
  aspect-ratio:auto!important;
  object-fit:contain!important;
  object-position:center!important;
  transform:none!important;
}}
</style>'''

for rel in ('index.html', 'en/index.html'):
    page = Path('site') / rel
    if not page.is_file():
        raise SystemExit(f'Missing homepage during preview verification: {rel}')
    text = page.read_text(encoding='utf-8', errors='strict')

    # Normalize either a previous cache-bust or the bare path to this release URL.
    text = re.sub(r'/img/oolita-browser-world-preview\.jpg(?:\?[^"\'\s<>]*)?', versioned, text)

    # Correct the HTML intrinsic dimensions. The old publication block was
    # authored for a 4:5 still (1080x1350); leaving those attributes on a 16:9
    # file can create a visibly wrong layout before CSS/image decode settles.
    def normalise_img(match: re.Match[str]) -> str:
        tag = match.group(0)
        if versioned not in tag:
            return tag
        if re.search(r'\bwidth=["\'][^"\']*["\']', tag, flags=re.I):
            tag = re.sub(r'\bwidth=(["\'])[^"\']*\1', 'width="800"', tag, count=1, flags=re.I)
        else:
            tag = tag[:-1] + ' width="800">'
        if re.search(r'\bheight=["\'][^"\']*["\']', tag, flags=re.I):
            tag = re.sub(r'\bheight=(["\'])[^"\']*\1', 'height="450"', tag, count=1, flags=re.I)
        else:
            tag = tag[:-1] + ' height="450">'
        return tag

    text = re.sub(r'<img\b[^>]*>', normalise_img, text, flags=re.I)

    # Replace an older copy of this targeted rule or insert it once. Mobile has
    # its own later layout repair and remains fluid below the viewport width.
    style_re = re.compile(
        rf'<style\s+id=["\']{re.escape(style_id)}["\'][^>]*>[\s\S]*?</style>',
        flags=re.I,
    )
    if style_re.search(text):
        text = style_re.sub(style, text, count=1)
    else:
        if '</head>' not in text:
            raise SystemExit(f'Missing </head> while constraining homepage preview: {rel}')
        text = text.replace('</head>', style + '\n</head>', 1)

    page.write_text(text, encoding='utf-8')
    verify = page.read_text(encoding='utf-8')
    if versioned not in verify:
        raise SystemExit(f'Cache-busted homepage preview href missing from {rel}: {versioned}')
    if bare not in verify:
        raise SystemExit(f'Canonical preview path missing from {rel}: {bare}')
    tags = [tag for tag in re.findall(r'<img\b[^>]*>', verify, flags=re.I) if versioned in tag]
    if len(tags) != 1:
        raise SystemExit(f'Expected one homepage preview image in {rel}; found {len(tags)}')
    if 'width="800"' not in tags[0] or 'height="450"' not in tags[0]:
        raise SystemExit(f'Homepage preview intrinsic dimensions incorrect in {rel}: {tags[0]}')
    required_style = (
        f'id="{style_id}"',
        'width:min(100%,800px)!important',
        'max-width:800px!important',
        'height:auto!important',
        'aspect-ratio:auto!important',
        'object-fit:contain!important',
    )
    for needle in required_style:
        if needle not in verify:
            raise SystemExit(f'Homepage preview anti-stretch rule missing in {rel}: {needle}')

asset = Path('site/img/oolita-browser-world-preview.jpg')
if not asset.is_file() or asset.stat().st_size != 28490:
    raise SystemExit('Installed homepage preview is missing or has drifted')
print('Homepage preview dimensions corrected; desktop upscaling disabled on Spanish and English homepages.')
PY

cat >> site/_headers <<'EOF'
/img/oolita-browser-world-preview.jpg
  Cache-Control: no-store, no-cache, must-revalidate, max-age=0
/
  Cache-Control: public, max-age=0, must-revalidate
/en/
  Cache-Control: public, max-age=0, must-revalidate
EOF
