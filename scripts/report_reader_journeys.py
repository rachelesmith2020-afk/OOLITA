#!/usr/bin/env python3
"""Report OOLITA reader-journey events from the first-party D1 store."""
from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from pathlib import Path

ACCOUNT_ID = os.environ.get("CLOUDFLARE_ACCOUNT_ID", "").strip()
TOKEN = os.environ.get("CLOUDFLARE_API_TOKEN", "").strip()
API = "https://api.cloudflare.com/client/v4"
DB_NAME = "oolita-subscribers"

if not ACCOUNT_ID or not TOKEN:
    raise SystemExit("Missing CLOUDFLARE_ACCOUNT_ID or CLOUDFLARE_API_TOKEN")


def cf(method: str, path: str, body=None):
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        API + path,
        data=data,
        method=method,
        headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        payload = json.load(resp)
    if not payload.get("success"):
        raise SystemExit(f"Cloudflare API failed: {payload.get('errors')}")
    return payload.get("result")

query = urllib.parse.urlencode({"name": DB_NAME, "per_page": 100})
items = cf("GET", f"/accounts/{ACCOUNT_ID}/d1/database?{query}") or []
match = next((x for x in items if x.get("name") == DB_NAME), None)
if not match or not match.get("uuid"):
    raise SystemExit("OOLITA D1 database not found")
db_id = match["uuid"]

events = [
    "home-follow", "home-book", "home-3d", "home-about",
    "hallazgo-follow", "editions-book", "book-follow", "textile-follow",
    "about-hallazgo", "sunday-next", "sunday-archive", "sundays-current",
    "ooid-cabo", "cabo-labyrinth", "labyrinth-follow-3d", "3d-follow",
    "partner-contact",
]
quoted = ",".join("?" for _ in events)
sql = f"""
SELECT event, COUNT(*) AS n
FROM site_events
WHERE created_at >= datetime('now','-30 days')
  AND event IN ({quoted})
GROUP BY event
ORDER BY n DESC, event ASC;
""".strip()
result = cf("POST", f"/accounts/{ACCOUNT_ID}/d1/database/{db_id}/query", {"sql": sql, "params": events}) or []
rows = []
for group in result:
    rows.extend(group.get("results") or [])
counts = {row.get("event"): int(row.get("n") or 0) for row in rows}

page_sql = """
SELECT path, COUNT(*) AS n
FROM site_events
WHERE created_at >= datetime('now','-30 days') AND event='pageview'
GROUP BY path
ORDER BY n DESC, path ASC
LIMIT 20;
""".strip()
page_result = cf("POST", f"/accounts/{ACCOUNT_ID}/d1/database/{db_id}/query", {"sql": page_sql}) or []
page_rows = []
for group in page_result:
    page_rows.extend(group.get("results") or [])

lines = ["### OOLITA reader journeys · last 30 days", "", "| Event | Count |", "|---|---:|"]
for event in events:
    lines.append(f"| `{event}` | {counts.get(event, 0)} |")
lines += ["", "Top pageviews:", "", "| Path | Views |", "|---|---:|"]
for row in page_rows:
    lines.append(f"| `{row.get('path','')}` | {int(row.get('n') or 0)} |")
report = "\n".join(lines)
print(report)
summary = os.environ.get("GITHUB_STEP_SUMMARY", "").strip()
if summary:
    with Path(summary).open("a", encoding="utf-8") as fh:
        fh.write("\n" + report + "\n")
