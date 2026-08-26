#!/usr/bin/env python3
"""Read-only report for the OOLITA Pages Analytics Engine binding.

This check is informational only. The deploy step removes the unsupported
binding before publishing so account-level Analytics Engine availability can
never block the site.
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
    bindings = ((configs.get(env_name) or {}).get("analytics_engine_datasets") or {})
    binding = bindings.get(BINDING)
    print(f"{env_name}_analytics_binding={binding!r}")
print("Analytics binding state reported; deployment cleanup remains authoritative.")

# Production propagation trigger: source-verified commercial status, textile specs and credential labels.
