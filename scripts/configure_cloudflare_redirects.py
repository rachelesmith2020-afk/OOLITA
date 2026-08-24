#!/usr/bin/env python3
"""Ensure OOLITA's one-hop www-to-apex Cloudflare redirect.

When the deployment token can manage the zone, create or update the redirect
rule. If the token is deliberately scoped to Pages and cannot access zone
rules, verify the already-configured live redirect instead. The script only
succeeds when the canonical redirect is correct in production.
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
PROBE_PATH = "/laberinto/?utm_source=redirect-deploy-check"
EXPECTED_PROBE = f"https://{ZONE_NAME}{PROBE_PATH}"

if not ACCOUNT_ID or not TOKEN:
    raise SystemExit("Missing CLOUDFLARE_ACCOUNT_ID or CLOUDFLARE_API_TOKEN")


class NoRedirect(urllib.request.HTTPRedirectHandler):
    """Expose redirect responses instead of following them."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


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


def one_hop_status(source: str) -> tuple[int, str]:
    opener = urllib.request.build_opener(NoRedirect())
    request = urllib.request.Request(
        source,
        headers={"User-Agent": "OOLITA canonical redirect deployment check/1.0"},
    )
    try:
        with opener.open(request, timeout=30) as response:
            return response.status, response.headers.get("Location", "")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.headers.get("Location", "")


def verify_live_redirect() -> None:
    for scheme in ("http", "https"):
        source = f"{scheme}://www.{ZONE_NAME}{PROBE_PATH}"
        status, location = one_hop_status(source)
        resolved = urllib.parse.urljoin(source, location)
        if status != 301 or resolved != EXPECTED_PROBE:
            raise SystemExit(
                "Live canonical redirect verification failed: "
                f"{source} returned {status} -> {resolved or '(no Location)'}; "
                f"expected 301 -> {EXPECTED_PROBE}"
            )

    request = urllib.request.Request(
        EXPECTED_PROBE,
        headers={"User-Agent": "OOLITA canonical redirect deployment check/1.0"},
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            status = response.status
            final = response.geturl()
    except urllib.error.HTTPError as exc:
        raise SystemExit(
            f"Canonical destination failed with HTTP {exc.code}: {EXPECTED_PROBE}"
        ) from exc

    if status != 200 or final != EXPECTED_PROBE:
        raise SystemExit(
            f"Canonical destination verification failed: status={status} final={final}"
        )

    print(
        "Live canonical redirect verified: HTTP/HTTPS www.oolita.es -> "
        "https://oolita.es (301, one hop, query preserved)."
    )


def manage_redirect() -> None:
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
        api(
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
        raise SystemExit(
            f"Canonical redirect API verification failed; active matches={len(matching)}"
        )
    print("Cloudflare canonical redirect rule is active in the zone.")


def main() -> None:
    try:
        manage_redirect()
    except SystemExit as exc:
        print(
            "Cloudflare zone redirect API is unavailable to this deploy token; "
            f"checking the required live behavior instead. Detail: {exc}"
        )
        verify_live_redirect()
        print(
            "Canonical redirect already satisfies production requirements; "
            "no zone API change was necessary."
        )
        return

    verify_live_redirect()


if __name__ == "__main__":
    main()
