#!/usr/bin/env bash
set -euo pipefail

# Install the approved homepage Three.js preview as a first-party asset.
mkdir -p site/img
cat overrides/images/oolita-home-preview-640-b64/part-*.b64 | tr -d '\n' | base64 -d > site/img/oolita-browser-world-preview.jpg

python3 - <<'PY'
from pathlib import Path
import hashlib

asset = Path('site/img/oolita-browser-world-preview.jpg')
data = asset.read_bytes()
expected_sha256 = '0fa5d0ab6b25ef08ec68849769e3fbf4bf31ff84d0eb7cdf05278a7463f10f95'
actual_sha256 = hashlib.sha256(data).hexdigest()
if actual_sha256 != expected_sha256:
    raise SystemExit(f'Homepage preview checksum mismatch: {actual_sha256}')
if len(data) != 14812:
    raise SystemExit(f'Homepage preview byte length mismatch: {len(data)}')
if not data.startswith(b'\xff\xd8'):
    raise SystemExit('Homepage preview is not JPEG')
print(f'Homepage Three.js preview installed: {len(data)} bytes, sha256={actual_sha256}')
PY

cat >> site/_headers <<'EOF'
/img/oolita-browser-world-preview.jpg
  Cache-Control: public, max-age=0, must-revalidate
EOF
