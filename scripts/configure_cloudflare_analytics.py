#!/usr/bin/env python3
"""Remove the unsupported Analytics Engine binding from the OOLITA Pages project.

Cloudflare's Pages project PATCH API deletes bindings by setting the binding key
to null. OOLITA analytics stays non-blocking until Analytics Engine is explicitly
enabled at account level.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path

ACCOUNT_ID = os.environ.get("CLOUDFLARE_ACCOUNT_ID", "").strip()
TOKEN = os.environ.get("CLOUDFLARE_API_TOKEN", "").strip()
PROJECT = "oolita"
BINDING = "OOLITA_ANALYTICS"

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

# Final deployment content invariant. Earlier rendering layers may reconstruct
# the homepage after the general wording pass, so enforce the approved wording
# verbatim immediately before Wrangler publishes the finished `site` directory.
homepage = Path("site/en/index.html")
if not homepage.is_file():
    raise SystemExit("Missing final English homepage: site/en/index.html")
html = homepage.read_text(encoding="utf-8")
for old in (
    "laid by hand in 2021 from loose calcarenite",
    "laid by hand in 2021 from stone",
    "laid by hand from loose calcarenite",
    "laid by hand from stone",
):
    html = html.replace(old, "built from stone")
homepage.write_text(html, encoding="utf-8")
final = homepage.read_text(encoding="utf-8")
if "loose calcarenite" in final:
    raise SystemExit("Final homepage still contains disallowed wording: loose calcarenite")
if "built from stone" not in final:
    raise SystemExit("Final homepage does not contain approved wording: built from stone")
print("Final English homepage wording verified exactly: built from stone.")
