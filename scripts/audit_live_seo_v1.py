#!/usr/bin/env python3
"""Audit every public OOLITA sitemap route and its first-party links/assets."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from html.parser import HTMLParser
import json
import re
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urldefrag, urljoin, urlsplit, urlunsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener, urlopen
import xml.etree.ElementTree as ET


BASE = (sys.argv[1] if len(sys.argv) > 1 else "https://oolita.es").rstrip("/")
SITEMAP = BASE + "/sitemap.xml"
USER_AGENT = "OOLITA technical SEO audit/1.0"
TIMEOUT = 20


@dataclass
class Page:
    url: str
    final_url: str
    status: int
    content_type: str
    html: str
    title: str = ""
    description: str = ""
    robots: str = ""
    lang: str = ""
    h1_count: int = 0
    canonical: str = ""
    alternates: dict[str, str] = field(default_factory=dict)
    hrefs: list[str] = field(default_factory=list)
    assets: list[str] = field(default_factory=list)
    schemas: list[object] = field(default_factory=list)
    schema_errors: list[str] = field(default_factory=list)


class Parser(HTMLParser):
    def __init__(self, page_url: str):
        super().__init__(convert_charrefs=True)
        self.page_url = page_url
        self.title_parts: list[str] = []
        self.in_title = False
        self.h1_count = 0
        self.lang = ""
        self.description = ""
        self.robots = ""
        self.canonical = ""
        self.alternates: dict[str, str] = {}
        self.hrefs: list[str] = []
        self.assets: list[str] = []
        self.in_jsonld = False
        self.jsonld_parts: list[str] = []
        self.jsonld_blocks: list[str] = []

    @staticmethod
    def attrs_list(attrs: list[tuple[str, str | None]]) -> dict[str, str]:
        return {k.lower(): (v or "") for k, v in attrs}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        data = self.attrs_list(attrs)
        if tag == "html":
            self.lang = data.get("lang", "")
        elif tag == "title":
            self.in_title = True
        elif tag == "h1":
            self.h1_count += 1
        elif tag == "meta":
            name = data.get("name", "").lower()
            if name == "description":
                self.description = data.get("content", "").strip()
            elif name == "robots":
                self.robots = data.get("content", "").strip().lower()
        elif tag == "link":
            rel = {item.lower() for item in data.get("rel", "").split()}
            href = data.get("href", "")
            if "canonical" in rel:
                self.canonical = urljoin(self.page_url, href)
            if "alternate" in rel and data.get("hreflang"):
                self.alternates[data["hreflang"].lower()] = urljoin(self.page_url, href)
            if "stylesheet" in rel and href:
                self.assets.append(href)
        elif tag == "a" and data.get("href"):
            self.hrefs.append(data["href"])
        elif tag in {"img", "script", "source", "video", "audio"}:
            for key in ("src", "poster"):
                if data.get(key):
                    self.assets.append(data[key])
            for candidate in data.get("srcset", "").split(","):
                value = candidate.strip().split(" ", 1)[0]
                if value:
                    self.assets.append(value)
        if tag == "script" and data.get("type", "").lower() == "application/ld+json":
            self.in_jsonld = True
            self.jsonld_parts = []

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag == "title":
            self.in_title = False
        elif tag == "script" and self.in_jsonld:
            self.jsonld_blocks.append("".join(self.jsonld_parts).strip())
            self.in_jsonld = False
            self.jsonld_parts = []

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title_parts.append(data)
        if self.in_jsonld:
            self.jsonld_parts.append(data)


class RedirectRecorder(HTTPRedirectHandler):
    def __init__(self):
        super().__init__()
        self.chain: list[tuple[int, str, str]] = []

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        self.chain.append((code, req.full_url, newurl))
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def request(url: str, *, method: str = "GET", follow: bool = True) -> tuple[int, str, dict[str, str], bytes, list[tuple[int, str, str]]]:
    recorder = RedirectRecorder()
    opener = build_opener(recorder) if follow else build_opener(HTTPRedirectHandler)
    req = Request(url, method=method, headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/xml;q=0.9,*/*;q=0.8"})
    try:
        with opener.open(req, timeout=TIMEOUT) as response:
            body = response.read() if method != "HEAD" else b""
            return response.status, response.geturl(), {k.lower(): v for k, v in response.headers.items()}, body, recorder.chain
    except HTTPError as exc:
        body = exc.read() if method != "HEAD" else b""
        return exc.code, exc.geturl(), {k.lower(): v for k, v in exc.headers.items()}, body, recorder.chain


def normalise(url: str, source: str) -> str | None:
    absolute = urljoin(source, url.strip())
    absolute, _ = urldefrag(absolute)
    parts = urlsplit(absolute)
    if parts.scheme not in {"http", "https"}:
        return None
    host = (parts.hostname or "").lower()
    if host not in {"oolita.es", "www.oolita.es"}:
        return None
    netloc = "oolita.es" if host == "oolita.es" else "www.oolita.es"
    return urlunsplit((parts.scheme.lower(), netloc, parts.path or "/", parts.query, ""))


def parse_page(url: str) -> Page:
    status, final_url, headers, body, _ = request(url)
    content_type = headers.get("content-type", "")
    html = body.decode("utf-8", "replace")
    page = Page(url, final_url, status, content_type, html)
    if status != 200 or "html" not in content_type.lower():
        return page
    parser = Parser(url)
    parser.feed(html)
    page.title = re.sub(r"\s+", " ", "".join(parser.title_parts)).strip()
    page.description = parser.description
    page.robots = parser.robots
    page.lang = parser.lang
    page.h1_count = parser.h1_count
    page.canonical = parser.canonical
    page.alternates = parser.alternates
    page.hrefs = parser.hrefs
    page.assets = parser.assets
    for index, block in enumerate(parser.jsonld_blocks, start=1):
        try:
            page.schemas.append(json.loads(block))
        except json.JSONDecodeError as exc:
            page.schema_errors.append(f"block {index}: {exc.msg}")
    return page


def schema_types(value: object) -> list[str]:
    found: list[str] = []
    if isinstance(value, dict):
        kind = value.get("@type")
        if isinstance(kind, str):
            found.append(kind)
        elif isinstance(kind, list):
            found.extend(str(item) for item in kind)
        for child in value.values():
            found.extend(schema_types(child))
    elif isinstance(value, list):
        for child in value:
            found.extend(schema_types(child))
    return found


def schema_nodes(value: object, wanted_type: str) -> list[dict[str, object]]:
    """Return all typed JSON-LD nodes, including nodes nested in an @graph."""
    found: list[dict[str, object]] = []
    if isinstance(value, dict):
        kind = value.get("@type")
        kinds = [kind] if isinstance(kind, str) else kind if isinstance(kind, list) else []
        if wanted_type in kinds:
            found.append(value)
        for child in value.values():
            found.extend(schema_nodes(child, wanted_type))
    elif isinstance(value, list):
        for child in value:
            found.extend(schema_nodes(child, wanted_type))
    return found


def sitemap_urls() -> list[str]:
    status, final_url, headers, body, chain = request(SITEMAP)
    if status != 200 or chain or final_url != SITEMAP:
        raise SystemExit(f"Sitemap request failed: status={status} final={final_url} redirects={len(chain)}")
    root = ET.fromstring(body)
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    urls = [(node.text or "").strip() for node in root.findall("sm:url/sm:loc", ns)]
    if not urls:
        raise SystemExit("Sitemap contains no URLs")
    return urls


def main() -> None:
    urls = sitemap_urls()
    issues: list[str] = []
    pages: dict[str, Page] = {}
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = {pool.submit(parse_page, url): url for url in urls}
        for future in as_completed(futures):
            url = futures[future]
            try:
                pages[url] = future.result()
            except (URLError, TimeoutError, OSError) as exc:
                issues.append(f"PAGE FETCH {url}: {exc}")

    if len(urls) != len(set(urls)):
        issues.append("SITEMAP contains duplicate URLs")
    for url in urls:
        page = pages.get(url)
        if not page:
            continue
        if page.status != 200:
            issues.append(f"STATUS {url}: {page.status}")
            continue
        if page.final_url != url:
            issues.append(f"SITEMAP REDIRECT {url} -> {page.final_url}")
        if page.canonical != url:
            issues.append(f"CANONICAL {url}: {page.canonical or 'missing'}")
        if not page.title:
            issues.append(f"TITLE missing: {url}")
        if not page.description:
            issues.append(f"DESCRIPTION missing: {url}")
        elif len(page.description) > 160:
            issues.append(f"DESCRIPTION over 160 ({len(page.description)}): {url}")
        if "noindex" in page.robots:
            issues.append(f"NOINDEX sitemap page: {url}")
        if page.h1_count != 1:
            issues.append(f"H1 count {page.h1_count}: {url}")
        if page.schema_errors:
            issues.append(f"JSON-LD invalid {url}: {'; '.join(page.schema_errors)}")
        types = [kind.lower() for schema in page.schemas for kind in schema_types(schema)]
        if "product" in types:
            issues.append(f"PRODUCT schema without verified offer review needed: {url}")
        serialised = [json.dumps(schema, ensure_ascii=False, sort_keys=True, separators=(",", ":")) for schema in page.schemas]
        if len(serialised) != len(set(serialised)):
            issues.append(f"DUPLICATE JSON-LD block: {url}")
        breadcrumbs = [node for schema in page.schemas for node in schema_nodes(schema, "BreadcrumbList")]
        if len(breadcrumbs) > 1:
            issues.append(f"DUPLICATE BreadcrumbList schema ({len(breadcrumbs)}): {url}")
        for breadcrumb in breadcrumbs:
            items = breadcrumb.get("itemListElement")
            if not isinstance(items, list):
                issues.append(f"BREADCRUMB items missing: {url}")
                continue
            positions = [item.get("position") for item in items if isinstance(item, dict)]
            if positions != list(range(1, len(items) + 1)):
                issues.append(f"BREADCRUMB positions {positions}: {url}")

        # Only paired language routes require ES/EN alternates. A deliberately
        # bilingual single page such as /reels/ uses x-default only.
        if urlsplit(url).path.startswith("/en/") or {"es", "en"} & set(page.alternates):
            expected = {"en", "es"}
            if not expected.issubset(page.alternates):
                issues.append(f"HREFLANG pair missing {url}: {sorted(page.alternates)}")

        if "/03-" in url:
            schema_text = " ".join(serialised).lower()
            stale = ("el gato de la fábula", "the cat in the fable", "domingo 2 de", "sunday 2 of")
            for needle in stale:
                if needle in schema_text:
                    issues.append(f"STALE Sunday 02 schema text ({needle}): {url}")

    internal_links: set[str] = set()
    assets: set[str] = set()
    for page in pages.values():
        for href in page.hrefs:
            target = normalise(href, page.url)
            if target:
                if urlsplit(target).path.startswith("/cdn-cgi/l/email-protection"):
                    # Cloudflare rewrites mailto links in the delivered HTML;
                    # this protection endpoint is not a navigable site route.
                    continue
                internal_links.add(target)
                path = urlsplit(target).path
                if path != path.lower():
                    issues.append(f"MIXED-CASE internal href {page.url}: {href}")
                if urlsplit(target).hostname == "www.oolita.es":
                    issues.append(f"WWW internal href {page.url}: {href}")
        for src in page.assets:
            target = normalise(src, page.url)
            if target:
                assets.add(target)

    def check_target(url: str) -> tuple[str, int, str, int]:
        status, final, _, _, chain = request(url, method="HEAD")
        return url, status, final, len(chain)

    targets = sorted(internal_links | assets)
    with ThreadPoolExecutor(max_workers=12) as pool:
        futures = [pool.submit(check_target, target) for target in targets]
        for future in as_completed(futures):
            try:
                target, status, final, redirects = future.result()
            except (URLError, TimeoutError, OSError) as exc:
                issues.append(f"TARGET FETCH failed: {exc}")
                continue
            if status >= 400:
                issues.append(f"BROKEN TARGET {status}: {target}")
            elif target in internal_links and redirects:
                issues.append(f"INTERNAL REDIRECT ({redirects}) {target} -> {final}")

    robots_status, _, robots_headers, robots_body, _ = request(BASE + "/robots.txt")
    robots_text = robots_body.decode("utf-8", "replace")
    if robots_status != 200 or f"Sitemap: {SITEMAP}" not in robots_text:
        issues.append("ROBOTS missing, blocked or does not advertise the canonical sitemap")
    if "x-robots-tag" in robots_headers and "noindex" in robots_headers["x-robots-tag"].lower():
        issues.append("ROBOTS response unexpectedly carries noindex")

    pages_status, _, pages_headers, _, _ = request("https://oolita.pages.dev/", method="HEAD")
    if pages_status != 200 or "noindex" not in pages_headers.get("x-robots-tag", "").lower():
        issues.append("PAGES.DEV preview origin is indexable; expected X-Robots-Tag: noindex")

    cache_probes = {
        BASE + "/fonts/instrument-sans-var-latin.woff2": (31536000, True),
        BASE + "/domingos/img/03.jpg": (2592000, False),
        BASE + "/reels/r01.mp4": (2592000, False),
    }
    for cache_url, (minimum_age, immutable) in cache_probes.items():
        cache_status, _, cache_headers, _, _ = request(cache_url, method="HEAD")
        cache_control = cache_headers.get("cache-control", "").lower()
        match = re.search(r"max-age=(\d+)", cache_control)
        age = int(match.group(1)) if match else 0
        if cache_status != 200 or age < minimum_age or (immutable and "immutable" not in cache_control):
            issues.append(f"CACHE policy insufficient {cache_url}: {cache_control or 'missing'}")

    probe = "http://www.oolita.es/laberinto/?utm_source=seo-audit"
    status, final, _, _, chain = request(probe)
    expected_final = BASE + "/laberinto/?utm_source=seo-audit"
    if status != 200 or final != expected_final or len(chain) != 1:
        issues.append(f"WWW REDIRECT chain={len(chain)} final={final} expected={expected_final}")

    case_probe = BASE + "/Laberinto/?utm_source=seo-audit"
    case_status, case_final, _, _, case_chain = request(case_probe)
    case_expected = BASE + "/laberinto/?utm_source=seo-audit"
    if case_status != 200 or case_final != case_expected or len(case_chain) != 1:
        issues.append(
            f"CASE REDIRECT chain={len(case_chain)} final={case_final} expected={case_expected}"
        )

    print(f"Sitemap URLs: {len(urls)}")
    print(f"HTML pages fetched: {len(pages)}")
    print(f"Internal targets checked: {len(targets)}")
    print(f"Issues: {len(issues)}")
    for issue in sorted(set(issues)):
        print(f"- {issue}")
    if issues:
        raise SystemExit(1)
    print("OOLITA live SEO audit passed.")


if __name__ == "__main__":
    main()
