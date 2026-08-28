#!/usr/bin/env bash
set -euo pipefail

# Install the approved homepage Three.js preview as a first-party asset.
# Keep the canonical asset path required by the publication/SEO validators, but
# append a cache-busting query string in homepage markup so mobile browsers do
# not retain the retired blue-spine still.
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

bare = '/img/oolita-browser-world-preview.jpg'
versioned = '/img/oolita-browser-world-preview.jpg?v=green-20260828'
for rel in ('index.html', 'en/index.html'):
    page = Path('site') / rel
    if not page.is_file():
        raise SystemExit(f'Missing homepage during preview verification: {rel}')
    text = page.read_text(encoding='utf-8', errors='strict')
    # Normalize either a previous cache-bust or the bare path to this release URL.
    import re
    text = re.sub(r'/img/oolita-browser-world-preview\.jpg(?:\?[^"\'\s<>]*)?', versioned, text)
    page.write_text(text, encoding='utf-8')
    verify = page.read_text(encoding='utf-8')
    if versioned not in verify:
        raise SystemExit(f'Cache-busted homepage preview href missing from {rel}: {versioned}')
    # Keep the bare path substring present for downstream publication invariants.
    if bare not in verify:
        raise SystemExit(f'Canonical preview path missing from {rel}: {bare}')

asset = Path('site/img/oolita-browser-world-preview.jpg')
if not asset.is_file() or asset.stat().st_size != 28490:
    raise SystemExit('Installed homepage preview is missing or has drifted')
print('Homepage preview hrefs cache-busted on Spanish and English homepages.')
PY

cat >> site/_headers <<'EOF'
/img/oolita-browser-world-preview.jpg
  Cache-Control: no-store, no-cache, must-revalidate, max-age=0
/
  Cache-Control: public, max-age=0, must-revalidate
/en/
  Cache-Control: public, max-age=0, must-revalidate
EOF
