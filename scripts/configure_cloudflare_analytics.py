#!/usr/bin/env python3
"""Remove the unsupported Analytics Engine binding from the OOLITA Pages project.

Cloudflare's Pages project PATCH API deletes bindings by setting the binding key
to null. OOLITA analytics stays non-blocking until Analytics Engine is explicitly
enabled at account level.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import urllib.error
import urllib.request
from pathlib import Path

ACCOUNT_ID = os.environ.get("CLOUDFLARE_ACCOUNT_ID", "").strip()
TOKEN = os.environ.get("CLOUDFLARE_API_TOKEN", "").strip()
PROJECT = "oolita"
BINDING = "OOLITA_ANALYTICS"

# Search visibility and engagement layers run after the initial site build and
# can reintroduce the rich Sunday archive rows. Re-run the idempotent mobile
# repair here, immediately before Cloudflare deployment, so Sundays 01–03 are
# the final compact image tiles that ship to production.
mobile_repair = Path(__file__).with_name("apply_mobile_layout_repairs_v1.py")
if not mobile_repair.is_file():
    raise SystemExit(f"Missing final mobile Sunday repair: {mobile_repair}")
subprocess.run(["python3", str(mobile_repair), "site"], check=True)

# Sunday 01's archived source does not contain the coloured left band that is
# present in the Instagram composition and in Sundays 02 and 03. Add that band
# at the final rendering stage so the compact archive reproduces the published
# visual language without altering the source image file itself.
SUNDAY01_STYLE_ID = "oolita-sunday-01-green-band"
SUNDAY01_STYLE = f'''<style id="{SUNDAY01_STYLE_ID}">
@media(max-width:640px){{
  .sunday-field-grid .sunday-image-tile[data-sunday="1"] .sunday-archive-thumb{{
    box-sizing:border-box!important;
    padding-left:9%!important;
    background:#2d4e23!important;
  }}
}}
</style>'''
for rel in ("domingos/index.html", "en/sundays/index.html"):
    page = Path("site") / rel
    if not page.is_file():
        raise SystemExit(f"Missing final Sunday page while restoring green band: {rel}")
    text = page.read_text(encoding="utf-8")
    text = re.sub(
        rf'<style\s+id=["\']{re.escape(SUNDAY01_STYLE_ID)}["\'][^>]*>[\s\S]*?</style>\s*',
        "",
        text,
        flags=re.I,
    )
    if "</head>" not in text:
        raise SystemExit(f"Missing </head> while restoring Sunday 01 green band: {rel}")
    text = text.replace("</head>", SUNDAY01_STYLE + "\n</head>", 1)
    page.write_text(text, encoding="utf-8")
    final_text = page.read_text(encoding="utf-8")
    required = (
        f'id="{SUNDAY01_STYLE_ID}"',
        'data-sunday="1"',
        'padding-left:9%!important',
        'background:#2d4e23!important',
        'object-fit:cover!important',
    )
    for needle in required:
        if needle not in final_text:
            raise SystemExit(f"Sunday 01 green-band invariant missing in {rel}: {needle}")
    print(f"Sunday 01 green band restored in compact archive: {rel}")

# Reader-facing voice edits can change contact headings without changing their
# structure or meaning (for example "Tell me" -> "Tell us"). Prepare stable
# markers before the strict low-severity gate so mirror-based rebuilds remain
# idempotent instead of failing on an obsolete literal heading.
low_severity_bridge = Path(__file__).with_name("prepare_low_severity_anchors_v1.py")
if not low_severity_bridge.is_file():
    raise SystemExit(f"Missing low-severity contact-anchor bridge: {low_severity_bridge}")
subprocess.run(["python3", str(low_severity_bridge), "site"], check=True)

# GSC Wizard's remaining findings are all low-severity editorial/accessibility
# items. Run this only after the final Sunday rendering repair so title, schema,
# alt-text and content-depth fixes are the last content changes before upload.
low_severity = Path(__file__).with_name("final_low_severity_seo_v1.py")
if not low_severity.is_file():
    raise SystemExit(f"Missing final low-severity SEO gate: {low_severity}")
subprocess.run(["python3", str(low_severity), "site"], check=True)

if not ACCOUNT_ID or not TOKEN:
    raise SystemExit("Missing CLOUDFLARE_ACCOUNT_ID or CLOUDFLARE_API_TOKEN")

base = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/pages/projects/{PROJECT}"
headers = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}


def api(method: str, url: str, payload=None):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")
        raise SystemExit(f"Cloudflare API {method} failed with HTTP {exc.code}: {detail[:1000]}")
    if not body.get("success"):
        raise SystemExit(f"Cloudflare API {method} unsuccessful: {body.get('errors')}")
    return body.get("result")

project = api("GET", base) or {}
configs = project.get("deployment_configs") or {}
patch = {}
changed = False
for env_name in ("production", "preview"):
    env_cfg = configs.get(env_name) or {}
    existing = dict(env_cfg.get("analytics_engine_datasets") or {})
    if BINDING in existing:
        existing[BINDING] = None
        patch[env_name] = {"analytics_engine_datasets": existing}
        changed = True

if changed:
    api("PATCH", base, {"deployment_configs": patch})
    print(f"Requested Analytics Engine binding deletion via null: {BINDING}")
else:
    print(f"Analytics Engine binding already absent: {BINDING}")

project = api("GET", base) or {}
configs = project.get("deployment_configs") or {}
for env_name in ("production", "preview"):
    bindings = ((configs.get(env_name) or {}).get("analytics_engine_datasets") or {})
    if bindings.get(BINDING) is not None:
        raise SystemExit(f"Analytics Engine binding removal failed for {env_name}")

print("OOLITA deployment is no longer blocked by Analytics Engine.")

# Final deployment content invariant. The final reader-facing layer replaces the
# older material-description sentence with the approved experience-first opening.
# Keep the provenance safeguard, but validate the copy that is actually meant to
# ship rather than requiring an obsolete phrase.
homepage = Path("site/en/index.html")
if not homepage.is_file():
    raise SystemExit("Missing final English homepage: site/en/index.html")
final = homepage.read_text(encoding="utf-8")
if "loose calcarenite" in final:
    raise SystemExit("Final homepage still contains disallowed wording: loose calcarenite")
approved = "Beside the sea at Los Escullos lies a three-metre stone labyrinth."
if approved not in final:
    raise SystemExit(f"Final homepage does not contain approved opening: {approved}")
if "place-based publishing and fieldwork project rooted" in final:
    raise SystemExit("Final homepage still contains the obsolete taxonomy-first opening")
print("Final English homepage engagement opening verified exactly.")
