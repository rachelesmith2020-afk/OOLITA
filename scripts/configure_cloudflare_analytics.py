#!/usr/bin/env python3
"""Bind a Cloudflare Analytics Engine dataset to the OOLITA Pages project.

Uses the same Pages Write token already required for deployment. It only adds the
OOLITA_ANALYTICS binding to production and verifies the project afterwards.
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
DATASET = "oolita_events"

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

project = api("GET", base)
prod = ((project or {}).get("deployment_configs") or {}).get("production") or {}
existing = prod.get("analytics_engine_datasets") or {}
current = existing.get(BINDING)
if isinstance(current, dict) and current.get("dataset") == DATASET:
    print(f"Cloudflare analytics binding already present: {BINDING} -> {DATASET}")
else:
    merged = dict(existing)
    merged[BINDING] = {"dataset": DATASET}
    api("PATCH", base, {"deployment_configs": {"production": {"analytics_engine_datasets": merged}}})
    print(f"Cloudflare analytics binding configured: {BINDING} -> {DATASET}")

project = api("GET", base)
prod = ((project or {}).get("deployment_configs") or {}).get("production") or {}
verify = (prod.get("analytics_engine_datasets") or {}).get(BINDING) or {}
if verify.get("dataset") != DATASET:
    raise SystemExit("Cloudflare Analytics Engine binding verification failed")
print("OOLITA Cloudflare Analytics Engine binding verified.")
