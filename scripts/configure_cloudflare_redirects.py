#!/usr/bin/env python3
"""Create or update OOLITA's one-hop www-to-apex Cloudflare redirect.

The rule runs in Cloudflare's dynamic redirect phase, before the Pages origin,
so both HTTP and HTTPS requests can reach the canonical host in one hop.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request


ACCOUNT_ID = os.environ.get("CLOUDFLARE_ACCOUNT_ID", "").strip()
TOKEN = os.environ.get("CLOUDFLARE_API_TOKEN", "").strip()
ZONE_NAME = "oolita.es"
API = "https://api.cloudflare.com/client/v4"
PHASE = "http_request_dynamic_redirect"
RULE_REF = "oolita_www_to_apex"

if not ACCOUNT_ID or not TOKEN:
    raise SystemExit("Missing CLOUDFLARE_ACCOUNT_ID or CLOUDFLARE_API_TOKEN")


def api(method: str, path: str, payload: object | None = None, *, allow_404: bool = False):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        API + path,
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")
        if allow_404 and exc.code == 404:
            return None
        raise SystemExit(
            f"Cloudflare API {method} {path} failed with HTTP {exc.code}: {detail[:1000]}"
        ) from exc
    if not body.get("success"):
        raise SystemExit(f"Cloudflare API {method} {path} unsuccessful: {body.get('errors')}")
    return body.get("result")


zone_query = urllib.parse.urlencode({"name": ZONE_NAME, "account.id": ACCOUNT_ID})
zones = api("GET", f"/zones?{zone_query}") or []
if len(zones) != 1:
    raise SystemExit(f"Expected exactly one accessible {ZONE_NAME} zone; found {len(zones)}")
zone_id = zones[0]["id"]

rule = {
    "action": "redirect",
    "action_parameters": {
        "from_value": {
            "status_code": 301,
            "target_url": {
                "expression": 'concat("https://oolita.es", http.request.uri.path)'
            },
            "preserve_query_string": True,
        }
    },
    "expression": '(http.host eq "www.oolita.es")',
    "description": "OOLITA canonical www to apex",
    "enabled": True,
    "ref": RULE_REF,
}

entrypoint_path = f"/zones/{zone_id}/rulesets/phases/{PHASE}/entrypoint"
ruleset = api("GET", entrypoint_path, allow_404=True)
if ruleset is None:
    ruleset = api(
        "POST",
        f"/zones/{zone_id}/rulesets",
        {
            "name": "OOLITA canonical redirects",
            "description": "Canonical host redirects managed by the OOLITA deployment",
            "kind": "zone",
            "phase": PHASE,
            "rules": [rule],
        },
    )
    print("Created the OOLITA dynamic redirect ruleset.")
else:
    ruleset_id = ruleset["id"]
    existing = next(
        (
            item
            for item in ruleset.get("rules", [])
            if item.get("ref") == RULE_REF
            or item.get("description") == rule["description"]
        ),
        None,
    )
    if existing:
        api(
            "PUT",
            f"/zones/{zone_id}/rulesets/{ruleset_id}/rules/{existing['id']}",
            rule,
        )
        print("Updated the OOLITA www-to-apex redirect rule.")
    else:
        api("POST", f"/zones/{zone_id}/rulesets/{ruleset_id}/rules", rule)
        print("Added the OOLITA www-to-apex redirect rule.")

verified = api("GET", entrypoint_path) or {}
matching = [
    item
    for item in verified.get("rules", [])
    if item.get("ref") == RULE_REF and item.get("enabled", True)
]
if len(matching) != 1:
    raise SystemExit(f"Canonical redirect verification failed; active matches={len(matching)}")
print("Cloudflare canonical redirect is active: www.oolita.es -> oolita.es (301).")
