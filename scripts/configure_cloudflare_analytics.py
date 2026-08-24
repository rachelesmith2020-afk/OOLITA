#!/usr/bin/env python3
"""Remove the unsupported Analytics Engine binding from the OOLITA Pages project.

Cloudflare's Pages project PATCH API deletes bindings by setting the binding key
to null. OOLITA analytics stays non-blocking until Analytics Engine is explicitly
enabled at account level.
"""
from __future__ import annotations

import json
import os
import subprocess
import urllib.error
import urllib.request
from pathlib import Path

ACCOUNT_ID = os.environ.get("CLOUDFLARE_ACCOUNT_ID", "").strip()
TOKEN = os.environ.get("CLOUDFLARE_API_TOKEN", "").strip()
PROJECT = "oolita"
BINDING = "OOLITA_ANALYTICS"

# Search visibility and engagement layers run after the initial site build and
# can reintroduce the rich Sunday archive rows. Re-run the idempotent mobile
# repair here, immediately before Cloudflare deployment, so Sundays 01–03 are
# the final compact image tiles that ship to production.
mobile_repair = Path(__file__).with_name("apply_mobile_layout_repairs_v1.py")
if not mobile_repair.is_file():
    raise SystemExit(f"Missing final mobile Sunday repair: {mobile_repair}")
subprocess.run(["python3", str(mobile_repair), "site"], check=True)

# Sunday 01 is the only published source that is not an exact 4:5 frame
# (417x518; 02 and 03 are exact 4:5). The mobile tile is exactly 4:5, so
# object-fit:cover can shave the outermost edge and hide the thin green line
# that is visible in the Instagram artwork. Preserve the complete artwork in
# the final deployed Sunday field instead of cropping any edge pixels.
for rel in ("domingos/index.html", "en/sundays/index.html"):
    page = Path("site") / rel
    if not page.is_file():
        raise SystemExit(f"Missing final Sunday page while preserving artwork edge: {rel}")
    text = page.read_text(encoding="utf-8")
    old = "object-fit:cover!important;"
    new = "object-fit:contain!important;"
    if old not in text:
        raise SystemExit(f"Expected mobile Sunday cover rule missing in {rel}")
    text = text.replace(old, new, 1)
    page.write_text(text, encoding="utf-8")
    final_text = page.read_text(encoding="utf-8")
    if new not in final_text:
        raise SystemExit(f"Sunday artwork edge-preservation rule failed in {rel}")
    print(f"Sunday artwork edge preserved without cropping: {rel}")

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

project = api("GET", base) or {}
configs = project.get("deployment_configs") or {}
patch = {}
changed = False
for env_name in ("production", "preview"):
    env_cfg = configs.get(env_name) or {}
    existing = dict(env_cfg.get("analytics_engine_datasets") or {})
    if BINDING in existing:
        existing[BINDING] = None
        patch[env_name] = {"analytics_engine_datasets": existing}
        changed = True

if changed:
    api("PATCH", base, {"deployment_configs": patch})
    print(f"Requested Analytics Engine binding deletion via null: {BINDING}")
else:
    print(f"Analytics Engine binding already absent: {BINDING}")

project = api("GET", base) or {}
configs = project.get("deployment_configs") or {}
for env_name in ("production", "preview"):
    bindings = ((configs.get(env_name) or {}).get("analytics_engine_datasets") or {})
    if bindings.get(BINDING) is not None:
        raise SystemExit(f"Analytics Engine binding removal failed for {env_name}")

print("OOLITA deployment is no longer blocked by Analytics Engine.")

# Final deployment content invariant. The final reader-facing layer replaces the
# older material-description sentence with the approved experience-first opening.
# Keep the provenance safeguard, but validate the copy that is actually meant to
# ship rather than requiring an obsolete phrase.
homepage = Path("site/en/index.html")
if not homepage.is_file():
    raise SystemExit("Missing final English homepage: site/en/index.html")
final = homepage.read_text(encoding="utf-8")
if "loose calcarenite" in final:
    raise SystemExit("Final homepage still contains disallowed wording: loose calcarenite")
approved = "Beside the sea at Los Escullos lies a three-metre stone labyrinth."
if approved not in final:
    raise SystemExit(f"Final homepage does not contain approved opening: {approved}")
if "place-based publishing and fieldwork project rooted" in final:
    raise SystemExit("Final homepage still contains the obsolete taxonomy-first opening")
print("Final English homepage engagement opening verified exactly.")
