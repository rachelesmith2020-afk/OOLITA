#!/usr/bin/env python3
"""Manage OOLITA's Cloudflare canonical URL redirect rule.

Check mode is read-only and is used on pull requests.
Apply mode creates or updates one named Single Redirect rule while preserving
all unrelated redirect rules in the zone.
"""
from __future__ import annotations

import argparse
import json
import os
import urllib.error
import urllib.parse
import urllib.request

ACCOUNT_ID = os.environ.get("CLOUDFLARE_ACCOUNT_ID", "").strip()
TOKEN = os.environ.get("CLOUDFLARE_API_TOKEN", "").strip()
ZONE_NAME = "oolita.es"
PHASE = "http_request_dynamic_redirect"
RULE_REF = "oolita_canonical_url"

RULE_EXPRESSION = (
    '(http.host in {"oolita.es" "www.oolita.es"} and '
    '(http.host ne "oolita.es" or not ssl or '
    'http.request.uri.path ne lower(http.request.uri.path)))'
)
TARGET_EXPRESSION = 'concat("https://oolita.es", lower(http.request.uri.path))'

DESIRED_RULE = {
    "ref": RULE_REF,
    "description": "OOLITA canonical host, HTTPS and lowercase path",
    "expression": RULE_EXPRESSION,
    "action": "redirect",
    "action_parameters": {
        "from_value": {
            "target_url": {"expression": TARGET_EXPRESSION},
            "status_code": 301,
            "preserve_query_string": True,
        }
    },
    "enabled": True,
}


def api(method: str, url: str, payload=None, *, allow_404: bool = False):
    headers = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")
        if allow_404 and exc.code == 404:
            return None
        raise SystemExit(
            f"Cloudflare API {method} {url} failed with HTTP {exc.code}: {detail[:1200]}"
        )
    if not body.get("success"):
        raise SystemExit(f"Cloudflare API {method} unsuccessful: {body.get('errors')}")
    return body.get("result")


def get_zone_id() -> str:
    query = urllib.parse.urlencode({"name": ZONE_NAME, "account.id": ACCOUNT_ID})
    zones = api("GET", f"https://api.cloudflare.com/client/v4/zones?{query}") or []
    exact = [z for z in zones if z.get("name") == ZONE_NAME]
    if len(exact) != 1:
        raise SystemExit(f"Expected exactly one Cloudflare zone for {ZONE_NAME}; found {len(exact)}")
    return exact[0]["id"]


def entrypoint_url(zone_id: str) -> str:
    return (
        f"https://api.cloudflare.com/client/v4/zones/{zone_id}/rulesets/"
        f"phases/{PHASE}/entrypoint"
    )


def ruleset_url(zone_id: str, ruleset_id: str) -> str:
    return f"https://api.cloudflare.com/client/v4/zones/{zone_id}/rulesets/{ruleset_id}"


def normalise_rule(rule: dict) -> dict:
    """Keep only fields relevant to desired-state comparison."""
    return {
        "ref": rule.get("ref"),
        "description": rule.get("description"),
        "expression": rule.get("expression"),
        "action": rule.get("action"),
        "action_parameters": rule.get("action_parameters"),
        "enabled": rule.get("enabled", True),
    }


def get_entrypoint(zone_id: str):
    return api("GET", entrypoint_url(zone_id), allow_404=True)


def create_entrypoint(zone_id: str) -> dict:
    payload = {
        "name": "OOLITA redirect rules",
        "kind": "zone",
        "phase": PHASE,
        "rules": [DESIRED_RULE],
    }
    return api(
        "POST",
        f"https://api.cloudflare.com/client/v4/zones/{zone_id}/rulesets",
        payload,
    )


def add_rule(zone_id: str, ruleset_id: str) -> dict:
    return api(
        "POST",
        f"{ruleset_url(zone_id, ruleset_id)}/rules",
        DESIRED_RULE,
    )


def update_rule(zone_id: str, ruleset_id: str, rule_id: str) -> dict:
    return api(
        "PATCH",
        f"{ruleset_url(zone_id, ruleset_id)}/rules/{rule_id}",
        DESIRED_RULE,
    )


def inspect(entrypoint: dict | None) -> tuple[str, dict | None]:
    if not entrypoint:
        return "missing-ruleset", None
    rules = entrypoint.get("rules") or []
    matching = [rule for rule in rules if rule.get("ref") == RULE_REF]
    if len(matching) > 1:
        raise SystemExit(f"Cloudflare has {len(matching)} rules with ref {RULE_REF}; refusing to guess")
    if not matching:
        return "missing-rule", None
    current = matching[0]
    if normalise_rule(current) == normalise_rule(DESIRED_RULE):
        return "current", current
    return "drifted", current


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Create/update the rule")
    args = parser.parse_args()

    if not ACCOUNT_ID or not TOKEN:
        raise SystemExit("Missing CLOUDFLARE_ACCOUNT_ID or CLOUDFLARE_API_TOKEN")

    zone_id = get_zone_id()
    entrypoint = get_entrypoint(zone_id)
    state, current = inspect(entrypoint)

    if not args.apply:
        print(f"OOLITA Cloudflare redirect check: zone={ZONE_NAME} state={state}")
        if state != "current":
            print("Desired canonical redirect is not yet active; production apply will reconcile it.")
        return

    if state == "missing-ruleset":
        create_entrypoint(zone_id)
        print("Created OOLITA Cloudflare Single Redirect ruleset.")
    elif state == "missing-rule":
        add_rule(zone_id, entrypoint["id"])
        print("Added OOLITA canonical redirect rule.")
    elif state == "drifted":
        update_rule(zone_id, entrypoint["id"], current["id"])
        print("Updated OOLITA canonical redirect rule.")
    else:
        print("OOLITA canonical redirect rule already current.")

    verified = get_entrypoint(zone_id)
    final_state, _ = inspect(verified)
    if final_state != "current":
        raise SystemExit(f"Cloudflare canonical redirect verification failed: {final_state}")
    print("OOLITA canonical redirect verified: HTTPS + apex host + lowercase path, 301, query preserved.")


if __name__ == "__main__":
    main()
