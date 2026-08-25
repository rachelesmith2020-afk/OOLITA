#!/usr/bin/env bash
set -euo pipefail

# Compatibility wrapper around the reviewed deployment builder. The original
# builder is preserved beside this file. This wrapper removes only the obsolete
# live-site Hallazgo cover download, then reconstructs a versioned first-party
# cover and normalizes the custom 404 artifact for downstream validators.
python3 - <<'PYWRAP'
from pathlib import Path

source_path = Path('scripts/build_site_for_deploy_original.sh')
source = source_path.read_text(encoding='utf-8')
start_marker = '# Preserve the currently published Hallazgo catalogue cover while deploying'
end_marker = '\nrequired=('
start = source.index(start_marker)
end = source.index(end_marker, start)
replacement = '''# Hallazgo cover is reconstructed from versioned repository assets after the\n# reviewed builder completes; do not depend on the currently published origin.\n'''
patched = source[:start] + replacement + source[end:]
patched = patched.replace('  site/hallazgo/hallazgo-catalogue-cover.jpg\n', '')
patched = patched.replace(
    '# Production propagation trigger: preserve published Hallazgo cover while shipping copy update.',
    '# Production propagation trigger: reconstruct first-party Hallazgo cover from repository assets.'
)
Path('/tmp/oolita-build-site-for-deploy.sh').write_text(patched, encoding='utf-8')
PYWRAP

bash /tmp/oolita-build-site-for-deploy.sh

# Reconstruct the Hallazgo catalogue cover from the complete q75 repository
# payload. Keeping it first-party prevents broken internal image hrefs and makes
# the deployment independent of Drive or the previous production deployment.
mkdir -p site/hallazgo
cat assets/hallazgo-q75-b64/part*.txt | tr -d '\n\r ' | base64 --decode > site/hallazgo/hallazgo-catalogue-cover.jpg
python3 - <<'PY'
from pathlib import Path

cover = Path('site/hallazgo/hallazgo-catalogue-cover.jpg')
data = cover.read_bytes()
if len(data) < 1000 or not data.startswith(b'\xff\xd8') or not data.endswith(b'\xff\xd9'):
    raise SystemExit('Versioned Hallazgo cover did not decode to a valid JPEG')

for rel in ('catalogo-hallazgo/index.html', 'en/hallazgo-catalogue/index.html'):
    page = Path('site') / rel
    text = page.read_text(encoding='utf-8')
    text = text.replace('hallazgo-catalogue-cover.png', 'hallazgo-catalogue-cover.jpg')
    text = text.replace('content="image/png"', 'content="image/jpeg"')
    page.write_text(text, encoding='utf-8')

print(f'First-party Hallazgo cover reconstructed and linked: {len(data)} bytes, image/jpeg')
PY

# The live mirror may expose the custom error document as /404.html while the
# downstream release-calendar compatibility layer expects /404/index.html.
# Keep both forms in the deployment bundle; neither changes the public URL.
if [ -f site/404.html ] && [ ! -f site/404/index.html ]; then
  mkdir -p site/404
  cp site/404.html site/404/index.html
  echo '404 compatibility mirror created: site/404/index.html'
fi

# Rebuild every browser/search favicon surface from the published cat icon.
# The mirrored origin can contain a stale legacy favicon.ico, so this runs only
# after reconstruction and 404 normalization and validates every HTML page.
python3 scripts/apply_favicon_seo_v1.py site
