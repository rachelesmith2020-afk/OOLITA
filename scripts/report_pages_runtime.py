#!/usr/bin/env python3
"""Read-only report of the live Cloudflare Pages runtime configuration."""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

ACCOUNT_ID = os.environ.get("CLOUDFLARE_ACCOUNT_ID", "").strip()
TOKEN = os.environ.get("CLOUDFLARE_API_TOKEN", "").strip()
PROJECT = "oolita"

if not ACCOUNT_ID or not TOKEN:
    raise SystemExit("Missing CLOUDFLARE_ACCOUNT_ID or CLOUDFLARE_API_TOKEN")

url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/pages/projects/{PROJECT}"
req = urllib.request.Request(
    url,
    headers={
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "application/json",
        "User-Agent": "OOLITA-runtime-inspector/1.0",
    },
)

try:
    with urllib.request.urlopen(req, timeout=20) as response:
        payload = json.load(response)
except urllib.error.HTTPError as exc:
    body = exc.read().decode("utf-8", "replace")
    raise SystemExit(f"Cloudflare Pages API returned HTTP {exc.code}: {body[:500]}") from exc

if not payload.get("success"):
    raise SystemExit(f"Cloudflare Pages API error: {payload.get('errors')}")

project = payload.get("result") or {}
configs = project.get("deployment_configs") or {}

safe = {
    "name": project.get("name"),
    "production_branch": project.get("production_branch"),
    "source": project.get("source", {}).get("type") if isinstance(project.get("source"), dict) else None,
    "production": {},
    "preview": {},
}

for environment in ("production", "preview"):
    cfg = configs.get(environment) or {}
    safe[environment] = {
        "compatibility_date": cfg.get("compatibility_date"),
        "compatibility_flags": cfg.get("compatibility_flags"),
        "always_use_latest_compatibility_date": cfg.get("always_use_latest_compatibility_date"),
        "fail_open": cfg.get("fail_open"),
        "wrangler_config_hash": cfg.get("wrangler_config_hash"),
    }

print(json.dumps(safe, indent=2, sort_keys=True))
