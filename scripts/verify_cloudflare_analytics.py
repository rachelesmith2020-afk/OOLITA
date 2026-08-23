#!/usr/bin/env python3
"""Read-only report for OOLITA Pages Analytics Engine and runtime settings.

This check is informational only. The deploy step removes the unsupported
binding before publishing so account-level Analytics Engine availability can
never block the site. Runtime fields printed here are non-secret and are used
to preserve the existing Pages compatibility configuration when adding tracing.
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
    raise SystemExit("Missing Cloudflare credentials for analytics preflight")

url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/pages/projects/{PROJECT}"
req = urllib.request.Request(
    url,
    method="GET",
    headers={"Authorization": f"Bearer {TOKEN}", "Accept": "application/json"},
)
try:
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = json.loads(resp.read().decode("utf-8"))
except urllib.error.HTTPError as exc:
    detail = exc.read().decode("utf-8", "replace")
    raise SystemExit(f"Cloudflare project read failed HTTP {exc.code}: {detail[:800]}")

if not body.get("success"):
    raise SystemExit(f"Cloudflare project read unsuccessful: {body.get('errors')}")
project = body.get("result") or {}
configs = project.get("deployment_configs") or {}
for env_name in ("production", "preview"):
    cfg = configs.get(env_name) or {}
    bindings = cfg.get("analytics_engine_datasets") or {}
    binding = bindings.get(BINDING)
    print(f"{env_name}_analytics_binding={binding!r}")
    print(f"{env_name}_compatibility_date={cfg.get('compatibility_date')!r}")
    print(f"{env_name}_compatibility_flags={cfg.get('compatibility_flags')!r}")
    print(f"{env_name}_always_use_latest_compatibility_date={cfg.get('always_use_latest_compatibility_date')!r}")
    print(f"{env_name}_fail_open={cfg.get('fail_open')!r}")
    print(f"{env_name}_wrangler_config_hash={cfg.get('wrangler_config_hash')!r}")
print("Analytics binding and runtime state reported; deployment cleanup remains authoritative.")
