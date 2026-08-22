#!/usr/bin/env python3
"""Submit the current OOLITA sitemap URLs to IndexNow after deployment."""
from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

SITEMAP = Path(sys.argv[1] if len(sys.argv) > 1 else "site/sitemap.xml")
KEY_FILE = Path(sys.argv[2] if len(sys.argv) > 2 else "search/indexnow-key.txt")
HOST = "oolita.es"
BASE = f"https://{HOST}"
ENDPOINT = "https://api.indexnow.org/indexnow"

if not SITEMAP.is_file() or not KEY_FILE.is_file():
    raise SystemExit("Missing sitemap or IndexNow key")
key = KEY_FILE.read_text(encoding="utf-8").strip()

ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
root = ET.parse(SITEMAP).getroot()
urls = []
for loc in root.findall("sm:url/sm:loc", ns):
    if loc.text:
        url = loc.text.strip()
        if url.startswith(BASE + "/") or url == BASE:
            urls.append(url)
urls = sorted(set(urls))
if not urls:
    raise SystemExit("No OOLITA URLs found in sitemap")
if len(urls) > 10000:
    raise SystemExit("IndexNow URL set exceeds 10,000 URLs")

key_url = f"{BASE}/{key}.txt"
for attempt in range(1, 11):
    try:
        with urllib.request.urlopen(key_url, timeout=15) as response:
            body = response.read().decode("utf-8", "replace").strip()
            if response.status == 200 and body == key:
                break
    except Exception:
        pass
    if attempt == 10:
        raise SystemExit(f"IndexNow key is not publicly verifiable at {key_url}")
    time.sleep(3)

payload = json.dumps({
    "host": HOST,
    "key": key,
    "keyLocation": key_url,
    "urlList": urls,
}).encode("utf-8")
request = urllib.request.Request(
    ENDPOINT,
    data=payload,
    method="POST",
    headers={
        "Content-Type": "application/json; charset=utf-8",
        "User-Agent": "OOLITA-indexing/1.0",
    },
)

last_error = None
for attempt in range(1, 4):
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            status = response.status
            if status in (200, 202):
                print(f"IndexNow accepted {len(urls)} URLs with HTTP {status}.")
                raise SystemExit(0)
            last_error = f"HTTP {status}"
    except urllib.error.HTTPError as exc:
        last_error = f"HTTP {exc.code}: {exc.read().decode('utf-8', 'replace')[:500]}"
    except Exception as exc:
        last_error = repr(exc)
    if attempt < 3:
        time.sleep(5 * attempt)

raise SystemExit(f"IndexNow submission failed: {last_error}")
