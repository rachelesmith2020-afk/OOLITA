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
latest = project.get("latest_deployment") or {}
trigger = latest.get("deployment_trigger") or {}
metadata = trigger.get("metadata") or {}
print(f"latest_deployment_id={latest.get('id')!r}")
print(f"latest_environment={latest.get('environment')!r}")
print(f"latest_url={latest.get('url')!r}")
print(f"latest_created_on={latest.get('created_on')!r}")
print(f"latest_commit_hash={metadata.get('commit_hash')!r}")
print(f"latest_branch={metadata.get('branch')!r}")
print(f"latest_stage={(latest.get('latest_stage') or {}).get('status')!r}")

# Diagnostic-only canonical-domain verification for the restored Sunday archive.
sunday_paths = (
    "/domingos/",
    "/en/sundays/",
    "/domingos/01-el-doble/",
    "/en/sundays/01-the-double/",
    "/domingos/02-el-gato-de-verdad/",
    "/en/sundays/02-the-cat-for-real/",
    "/domingos/03-la-memoria-del-mar/",
    "/en/sundays/03-the-memory-of-the-sea/",
    "/domingos/04-el-guardian/",
    "/en/sundays/04-the-guardian/",
    "/domingos/05-el-mundo/",
    "/en/sundays/05-the-world/",
    "/domingos/06-el-mapa/",
    "/en/sundays/06-the-map/",
)
for path in sunday_paths:
    target = "https://oolita.es" + path
    request = urllib.request.Request(
        target,
        headers={"Cache-Control": "no-cache", "User-Agent": "OOLITA canonical Sunday verification/1.0"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        status = response.status
        final_url = response.geturl()
        body = response.read().decode("utf-8", "replace")
    if status != 200 or final_url != target:
        raise SystemExit(f"Sunday route failed: {target} status={status} final={final_url}")
    if path in {"/domingos/", "/en/sundays/"}:
        if "42" not in body or "2027-05-23" not in body:
            raise SystemExit(f"Sunday archive framing incomplete: {target}")
    print(f"sunday_route_ok={path}")

# Production propagation trigger: all six reviewed passes, exact-block Hallazgo fix, SEO/href/no-straggler verification.
