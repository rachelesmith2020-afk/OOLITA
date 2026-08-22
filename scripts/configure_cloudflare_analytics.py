#!/usr/bin/env python3
"""Remove the unsupported Analytics Engine binding from the OOLITA Pages project.

Cloudflare currently rejects Pages Function deployments when the binding exists
but Analytics Engine has not been enabled at account level. OOLITA analytics is
therefore kept non-blocking until that product is explicitly enabled later.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

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
        existing.pop(BINDING, None)
        patch[env_name] = {"analytics_engine_datasets": existing}
        changed = True

if changed:
    api("PATCH", base, {"deployment_configs": patch})
    print(f"Removed unsupported Cloudflare Analytics Engine binding: {BINDING}")
else:
    print(f"Analytics Engine binding already absent: {BINDING}")

project = api("GET", base) or {}
configs = project.get("deployment_configs") or {}
for env_name in ("production", "preview"):
    bindings = ((configs.get(env_name) or {}).get("analytics_engine_datasets") or {})
    if BINDING in bindings:
        raise SystemExit(f"Analytics Engine binding removal failed for {env_name}")

print("OOLITA deployment is no longer blocked by Analytics Engine.")
