#!/usr/bin/env python3
"""Report OOLITA reader interactions from the first-party D1 store.

The report intentionally discovers event names from the database instead of
keeping a hard-coded list, so approved journey changes do not silently disappear
from reporting. It reports aggregate counts only; OOLITA does not assign visitor
IDs or reconstruct individual browsing histories.
"""
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


def query_rows(db_id: str, sql: str, params=None) -> list[dict]:
    body = {"sql": sql.strip()}
    if params:
        body["params"] = params
    result = cf("POST", f"/accounts/{ACCOUNT_ID}/d1/database/{db_id}/query", body) or []
    rows: list[dict] = []
    for group in result:
        rows.extend(group.get("results") or [])
    return rows


lookup = urllib.parse.urlencode({"name": DB_NAME, "per_page": 100})
items = cf("GET", f"/accounts/{ACCOUNT_ID}/d1/database?{lookup}") or []
match = next((x for x in items if x.get("name") == DB_NAME), None)
if not match or not match.get("uuid"):
    raise SystemExit("OOLITA D1 database not found")
db_id = match["uuid"]

# Discover all reader-facing interaction names. System health checks and raw
# pageviews are reported separately, never mixed into conversion-event counts.
event_rows = query_rows(
    db_id,
    """
    SELECT event, COUNT(*) AS n
    FROM site_events
    WHERE created_at >= datetime('now','-30 days')
      AND event NOT IN ('pageview','deployment-health')
    GROUP BY event
    ORDER BY n DESC, event ASC;
    """,
)

page_rows = query_rows(
    db_id,
    """
    SELECT path, COUNT(*) AS n
    FROM site_events
    WHERE created_at >= datetime('now','-30 days') AND event='pageview'
    GROUP BY path
    ORDER BY n DESC, path ASC
    LIMIT 20;
    """,
)

total_events = sum(int(row.get("n") or 0) for row in event_rows)
total_pageviews = sum(int(row.get("n") or 0) for row in page_rows)

lines = [
    "### OOLITA reader interactions · last 30 days",
    "",
    "Aggregate first-party counts only; no visitor IDs or individual browsing histories.",
    "",
    f"- Measured interaction events: **{total_events}**",
    f"- Pageviews represented in top-path table: **{total_pageviews}**",
    "",
    "| Event | Count |",
    "|---|---:|",
]
if event_rows:
    for row in event_rows:
        lines.append(f"| `{row.get('event','')}` | {int(row.get('n') or 0)} |")
else:
    lines.append("| _No measured interaction events yet_ | 0 |")

lines += ["", "Top pageviews:", "", "| Path | Views |", "|---|---:|"]
if page_rows:
    for row in page_rows:
        lines.append(f"| `{row.get('path','')}` | {int(row.get('n') or 0)} |")
else:
    lines.append("| _No pageviews yet_ | 0 |")

report = "\n".join(lines)
print(report)
summary = os.environ.get("GITHUB_STEP_SUMMARY", "").strip()
if summary:
    with Path(summary).open("a", encoding="utf-8") as fh:
        fh.write("\n" + report + "\n")
