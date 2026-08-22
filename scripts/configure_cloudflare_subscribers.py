#!/usr/bin/env python3
"""Provision OOLITA's first-party Cloudflare subscriber database and Pages binding.

Creates/reuses an EU-jurisdiction D1 database, applies the subscriber schema,
and binds it to the OOLITA Pages project as OOLITA_SUBSCRIBERS for production
and preview deployments. No email-sending service is created here.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request

ACCOUNT_ID = os.environ.get("CLOUDFLARE_ACCOUNT_ID", "").strip()
TOKEN = os.environ.get("CLOUDFLARE_API_TOKEN", "").strip()
PROJECT = "oolita"
DB_NAME = "oolita-subscribers"
BINDING = "OOLITA_SUBSCRIBERS"
API = "https://api.cloudflare.com/client/v4"

if not ACCOUNT_ID or not TOKEN:
    raise SystemExit("Missing CLOUDFLARE_ACCOUNT_ID or CLOUDFLARE_API_TOKEN")


def cf(method: str, path: str, body=None):
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(API + path, data=data, method=method, headers={
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = json.load(resp)
    except urllib.error.HTTPError as exc:
        text = exc.read().decode("utf-8", "replace")
        raise SystemExit(f"Cloudflare API {method} {path} failed: HTTP {exc.code}: {text}")
    if not payload.get("success"):
        raise SystemExit(f"Cloudflare API {method} {path} failed: {payload.get('errors')}")
    return payload.get("result")


query = urllib.parse.urlencode({"name": DB_NAME, "per_page": 100})
items = cf("GET", f"/accounts/{ACCOUNT_ID}/d1/database?{query}") or []
match = next((x for x in items if x.get("name") == DB_NAME), None)
if match:
    db_id = match.get("uuid")
    print(f"subscriber database exists: {DB_NAME} ({db_id})")
else:
    created = cf("POST", f"/accounts/{ACCOUNT_ID}/d1/database", {
        "name": DB_NAME,
        "jurisdiction": "eu",
        "read_replication": {"mode": "disabled"},
    })
    db_id = created.get("uuid")
    print(f"subscriber database created: {DB_NAME} ({db_id})")

if not db_id:
    raise SystemExit("Cloudflare did not return a D1 database UUID")

schema = """
CREATE TABLE IF NOT EXISTS subscribers (
  email TEXT PRIMARY KEY COLLATE NOCASE,
  language TEXT NOT NULL CHECK (language IN ('es','en')),
  interests TEXT NOT NULL,
  consent_version TEXT NOT NULL,
  consent_at TEXT NOT NULL,
  source_path TEXT NOT NULL DEFAULT '/',
  status TEXT NOT NULL DEFAULT 'pending_confirmation' CHECK (status IN ('pending_confirmation','active','unsubscribed')),
  unsubscribe_token TEXT NOT NULL UNIQUE,
  verified_at TEXT,
  unsubscribed_at TEXT,
  updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_subscribers_status ON subscribers(status);
CREATE INDEX IF NOT EXISTS idx_subscribers_language ON subscribers(language);
""".strip()
cf("POST", f"/accounts/{ACCOUNT_ID}/d1/database/{db_id}/query", {"sql": schema})
print("subscriber schema applied")

project = cf("GET", f"/accounts/{ACCOUNT_ID}/pages/projects/{PROJECT}")
configs = project.get("deployment_configs") or {}
prod_d1 = dict(((configs.get("production") or {}).get("d1_databases")) or {})
prev_d1 = dict(((configs.get("preview") or {}).get("d1_databases")) or {})
prod_d1[BINDING] = {"id": db_id}
prev_d1[BINDING] = {"id": db_id}

cf("PATCH", f"/accounts/{ACCOUNT_ID}/pages/projects/{PROJECT}", {
    "deployment_configs": {
        "production": {"d1_databases": prod_d1},
        "preview": {"d1_databases": prev_d1},
    }
})
print(f"Pages D1 binding configured: {BINDING} -> {db_id}")

project = cf("GET", f"/accounts/{ACCOUNT_ID}/pages/projects/{PROJECT}")
configs = project.get("deployment_configs") or {}
for env_name in ("production", "preview"):
    bound = ((configs.get(env_name) or {}).get("d1_databases") or {}).get(BINDING)
    if not bound or bound.get("id") != db_id:
        raise SystemExit(f"D1 binding verification failed for {env_name}")

print("OOLITA Cloudflare subscriber storage is configured and verified.")
