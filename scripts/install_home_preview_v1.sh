#!/usr/bin/env bash
set -euo pipefail

# Install the approved homepage Three.js preview as a first-party asset.
# Fail safe: if the staged base64 is incomplete/invalid, preserve the mirrored
# live preview already present in site/img instead of blocking all deployment.
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
expected_sha256 = '0fa5d0ab6b25ef08ec68849769e3fbf4bf31ff84d0eb7cdf05278a7463f10f95'
if hashlib.sha256(data).hexdigest() != expected_sha256:
    raise SystemExit(1)
if len(data) != 14812:
    raise SystemExit(1)
if not data.startswith(b'\xff\xd8'):
    raise SystemExit(1)
PY
  then
    mv "$tmp_preview" site/img/oolita-browser-world-preview.jpg
    staged_ok=1
    echo 'Homepage Three.js preview staging verified and installed.'
  fi
fi

if [ "$staged_ok" -ne 1 ]; then
  rm -f "$tmp_preview"
  if [ ! -s site/img/oolita-browser-world-preview.jpg ]; then
    echo 'Homepage preview staging invalid and no mirrored fallback exists.' >&2
    exit 1
  fi
  echo 'Homepage preview staging invalid/incomplete; preserving mirrored live preview.'
fi

cat >> site/_headers <<'EOF'
/img/oolita-browser-world-preview.jpg
  Cache-Control: public, max-age=0, must-revalidate
EOF
