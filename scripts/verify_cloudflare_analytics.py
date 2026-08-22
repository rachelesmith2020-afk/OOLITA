#!/usr/bin/env python3
"""Read-only preflight for the OOLITA Pages Analytics Engine binding."""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

ACCOUNT_ID = os.environ.get("CLOUDFLARE_ACCOUNT_ID", "").strip()
TOKEN = os.environ.get("CLOUDFLARE_API_TOKEN", "").strip()
PROJECT = "oolita"
BINDING = "OOLITA_ANALYTICS"
DATASET = "oolita_events"

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
prod = ((project.get("deployment_configs") or {}).get("production") or {})
bindings = prod.get("analytics_engine_datasets") or {}
binding = bindings.get(BINDING) or {}
print(f"analytics_binding_dataset={binding.get('dataset')!r}")
if binding.get("dataset") != DATASET:
    raise SystemExit(f"Expected {BINDING} -> {DATASET}; binding is missing or different")
print("Cloudflare Analytics Engine production binding verified read-only.")
