#!/usr/bin/env bash
set -euo pipefail

# Install the approved homepage Three.js preview as a first-party asset.
# This version carries the OOLITA poster treatment: paper field plus the Salvia
# poster-palette spine, while preserving the existing homepage asset URL.
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

# Read dimensions from a JPEG SOF marker without introducing a build dependency.
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
    echo 'Homepage Three.js preview staging verified and installed: 800x450, green poster spine.'
  fi
fi

if [ "$staged_ok" -ne 1 ]; then
  rm -f "$tmp_preview"
  echo 'Homepage preview staging invalid/incomplete; refusing to publish a stale fallback.' >&2
  exit 1
fi

# The homepage asset URL is intentionally stable. Both language homepages must
# still reference it after reconstruction, otherwise fail before deployment.
python3 - <<'PY'
from pathlib import Path

ref = '/img/oolita-browser-world-preview.jpg'
for rel in ('index.html', 'en/index.html'):
    page = Path('site') / rel
    if not page.is_file():
        raise SystemExit(f'Missing homepage during preview verification: {rel}')
    text = page.read_text(encoding='utf-8', errors='strict')
    if ref not in text:
        raise SystemExit(f'Homepage preview href missing from {rel}: {ref}')

asset = Path('site/img/oolita-browser-world-preview.jpg')
if not asset.is_file() or asset.stat().st_size != 28490:
    raise SystemExit('Installed homepage preview is missing or has drifted')
print('Homepage preview hrefs verified on Spanish and English homepages.')
PY

cat >> site/_headers <<'EOF'
/img/oolita-browser-world-preview.jpg
  Cache-Control: public, max-age=0, must-revalidate
EOF
