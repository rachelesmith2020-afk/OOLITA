#!/usr/bin/env python3
"""Reconstruct the currently published OOLITA Pages site from its clean origin.

All same-site links are normalized to https://oolita.pages.dev before fetching,
so the custom-domain Cloudflare zone layer is never used. The crawler follows
HTML links/requisites, srcset assets, CSS url()/imports, and common static asset
references inside JS/JSON. It is intentionally bounded and fails on runaway
crawls rather than producing a partial deployment silently.
"""
from __future__ import annotations

from collections import deque
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlsplit, urlunsplit
from urllib.request import Request, urlopen
import re
import sys

ORIGIN = "https://oolita.pages.dev"
OUT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
MAX_FILES = 500
MAX_BYTES = 150 * 1024 * 1024
ALLOWED_HOSTS = {"oolita.pages.dev", "oolita.es", "www.oolita.es"}
# This stale production asset is deliberately replaced by the deployment
# wrapper after mirroring. Do not let its current 404 abort reconstruction.
REPLACED_PATHS = {"/hallazgo/hallazgo-catalogue-cover.png"}
ASSET_EXTS = (
    "html", "htm", "css", "js", "mjs", "json", "xml", "txt",
    "png", "jpg", "jpeg", "avif", "webp", "gif", "svg", "ico",
    "woff", "woff2", "ttf", "otf", "mp4", "webm", "glb", "gltf",
    "pdf", "zip"
)


def normalize(raw: str, base: str = ORIGIN + "/") -> str | None:
    raw = raw.strip().strip('"\'')
    if not raw or raw.startswith(("#", "mailto:", "tel:", "javascript:", "data:", "blob:")):
        return None
    absolute = urljoin(base, raw)
    parts = urlsplit(absolute)
    host = (parts.hostname or "").lower()
    if host not in ALLOWED_HOSTS:
        return None
    path = parts.path or "/"
    if path in REPLACED_PATHS:
        return None
    return urlunsplit(("https", "oolita.pages.dev", path, "", ""))


def destination(url: str, content_type: str, final_url: str) -> Path:
    path = urlsplit(final_url).path or urlsplit(url).path or "/"
    if path.endswith("/"):
        path += "index.html"
    elif not Path(path).suffix and "text/html" in content_type:
        path += "/index.html"
    return OUT / path.lstrip("/")


class LinkParser(HTMLParser):
    def __init__(self, base: str):
        super().__init__(convert_charrefs=True)
        self.base = base
        self.urls: list[str] = []

    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if not value:
                continue
            k = key.lower()
            if k in {"href", "src", "poster", "data-src", "data-href"}:
                u = normalize(value, self.base)
                if u:
                    self.urls.append(u)
            elif k in {"srcset", "data-srcset"}:
                for part in value.split(","):
                    candidate = part.strip().split()[0] if part.strip() else ""
                    u = normalize(candidate, self.base)
                    if u:
                        self.urls.append(u)
            elif k == "style":
                for candidate in re.findall(r"url\(\s*['\"]?([^)'\"]+)", value, flags=re.I):
                    u = normalize(candidate, self.base)
                    if u:
                        self.urls.append(u)


CSS_URL_RE = re.compile(r"url\(\s*['\"]?([^)'\"]+)|@import\s+(?:url\()?\s*['\"]([^'\"]+)", re.I)
STATIC_STRING_RE = re.compile(
    r"['\"]([^'\"\s?#]+\.(?:" + "|".join(ASSET_EXTS) + r"))(?:\?[^'\"]*)?['\"]",
    re.I,
)


def extract_links(text: str, content_type: str, base: str) -> list[str]:
    found: list[str] = []
    if "text/html" in content_type:
        parser = LinkParser(base)
        parser.feed(text)
        found.extend(parser.urls)
    if "text/css" in content_type:
        for a, b in CSS_URL_RE.findall(text):
            u = normalize(a or b, base)
            if u:
                found.append(u)
    if any(t in content_type for t in ("javascript", "json", "text/plain", "text/xml", "application/xml")):
        for candidate in STATIC_STRING_RE.findall(text):
            u = normalize(candidate, base)
            if u:
                found.append(u)
    return found


def request(url: str):
    req = Request(url, headers={"User-Agent": "OOLITA-deploy-mirror/1.0"})
    return urlopen(req, timeout=30)


OUT.mkdir(parents=True, exist_ok=True)
queue: deque[str] = deque()
queued: set[str] = set()
visited: set[str] = set()


def enqueue(raw: str, base: str = ORIGIN + "/"):
    u = normalize(raw, base)
    if u and u not in queued and u not in visited:
        queue.append(u)
        queued.add(u)


# Seed known public entry points and every sitemap URL.
for seed in ("/", "/sitemap.xml", "/robots.txt", "/favicon.svg", "/404.html"):
    enqueue(seed)

with request(ORIGIN + "/sitemap.xml") as r:
    sitemap_bytes = r.read()
sitemap_text = sitemap_bytes.decode("utf-8", errors="replace")
for loc in re.findall(r"<loc>\s*(.*?)\s*</loc>", sitemap_text, flags=re.I | re.S):
    enqueue(loc)

# These pages are edited by the reviewed wording patch even if a future sitemap
# accidentally omits one of them.
for path in (
    "/en/", "/que-es-un-laberinto/", "/en/what-is-a-labyrinth/",
    "/que-es-un-oolito/", "/en/what-is-an-ooid/", "/domingos/",
    "/laberinto/", "/en/labyrinth/", "/carteles/", "/en/posters/",
):
    enqueue(path)

total_bytes = 0
while queue:
    url = queue.popleft()
    queued.discard(url)
    if url in visited:
        continue
    visited.add(url)
    if len(visited) > MAX_FILES:
        raise SystemExit(f"Crawler exceeded {MAX_FILES} URLs; refusing runaway mirror")

    try:
        with request(url) as r:
            data = r.read()
            ctype = (r.headers.get("Content-Type") or "application/octet-stream").split(";", 1)[0].lower()
            final = normalize(r.geturl(), url) or url
    except Exception as exc:
        # 404.html is optional on some Pages deployments; everything else is required once linked.
        if url.endswith("/404.html"):
            print(f"optional fetch skipped: {url}: {exc}")
            continue
        raise SystemExit(f"Failed to fetch {url}: {exc}") from exc

    total_bytes += len(data)
    if total_bytes > MAX_BYTES:
        raise SystemExit(f"Mirror exceeded {MAX_BYTES} bytes; refusing runaway mirror")

    dest = destination(url, ctype, final)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    print(f"mirrored {urlsplit(url).path or '/'} -> {dest.relative_to(OUT)} ({len(data)} bytes)")

    if ctype.startswith("text/") or ctype in {
        "application/javascript", "application/json", "application/xml",
        "image/svg+xml",
    }:
        text = data.decode("utf-8", errors="replace")
        for linked in extract_links(text, ctype, final):
            enqueue(linked, final)

print(f"Mirrored {len(visited)} URLs, {total_bytes} bytes into {OUT}")
