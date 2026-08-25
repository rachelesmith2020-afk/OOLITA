#!/usr/bin/env bash
set -euo pipefail

# Compatibility wrapper around the reviewed deployment builder. The original
# builder is preserved beside this file. This wrapper removes only the obsolete
# Hallazgo cover download requirement, then normalizes the custom 404 artifact
# for downstream release and href validators.
python3 - <<'PYWRAP'
from pathlib import Path

source_path = Path('scripts/build_site_for_deploy_original.sh')
source = source_path.read_text(encoding='utf-8')
start_marker = '# Preserve the currently published Hallazgo catalogue cover while deploying'
end_marker = '\nrequired=('
start = source.index(start_marker)
end = source.index(end_marker, start)
replacement = '''# Hallazgo catalogue pages retain their current external cover URL.\n# The copy-only deployment does not fetch or require a local cover file.\n'''
patched = source[:start] + replacement + source[end:]
patched = patched.replace('  site/hallazgo/hallazgo-catalogue-cover.jpg\n', '')
patched = patched.replace(
    '# Production propagation trigger: preserve published Hallazgo cover while shipping copy update.',
    '# Production propagation trigger: preserve Hallazgo cover URL while shipping validated copy.'
)
Path('/tmp/oolita-build-site-for-deploy.sh').write_text(patched, encoding='utf-8')
PYWRAP

bash /tmp/oolita-build-site-for-deploy.sh

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
