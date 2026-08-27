#!/usr/bin/env python3
"""Publish one stable, crawlable cat favicon URL as the final deployment mutation."""
from __future__ import annotations

from pathlib import Path
import re
import struct
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
SEARCH_NAME = "favicon.png"
APPLE_NAME = "apple-touch-icon.png"


def png_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise SystemExit(f"Invalid PNG: {path}")
    return struct.unpack(">II", data[16:24])


def main() -> None:
    if not ROOT.is_dir():
        raise SystemExit(f"Missing built site: {ROOT}")

    # apply_favicon_seo_v1.py is the canonical cat generator. Run it here, at
    # the end of the deployment pipeline, so later SEO layers cannot restore an
    # older icon or declaration.
    source = ROOT / "apple-touch-icon-cat.png"
    if not source.is_file():
        raise SystemExit("Missing canonical generated cat icon: apple-touch-icon-cat.png")
    if png_size(source) != (180, 180):
        raise SystemExit("Canonical cat icon is not 180x180")

    search_icon = ROOT / SEARCH_NAME
    apple_icon = ROOT / APPLE_NAME
    search_icon.write_bytes(source.read_bytes())
    apple_icon.write_bytes(source.read_bytes())

    link_re = re.compile(r"<link\b[^>]*>", flags=re.I | re.S)
    rel_re = re.compile(r"\brel\s*=\s*([\"'])(.*?)\1", flags=re.I | re.S)

    def strip_icon_link(match: re.Match[str]) -> str:
        tag = match.group(0)
        rel = rel_re.search(tag)
        if not rel:
            return tag
        tokens = {token.strip().lower() for token in rel.group(2).split() if token.strip()}
        return "" if any("icon" in token for token in tokens) else tag

    stable_links = (
        '<link rel="icon" type="image/png" sizes="180x180" href="/favicon.png">\n'
        '<link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png">'
    )

    count = 0
    for path in ROOT.rglob("*.html"):
        text = path.read_text(encoding="utf-8")
        if "</head>" not in text.lower():
            raise SystemExit(f"Missing </head>: {path.relative_to(ROOT)}")
        text = link_re.sub(strip_icon_link, text)
        text, replaced = re.subn(r"</head>", stable_links + "\n</head>", text, count=1, flags=re.I)
        if replaced != 1:
            raise SystemExit(f"Could not publish stable favicon in {path.relative_to(ROOT)}")
        if text.count('href="/favicon.png"') != 1:
            raise SystemExit(f"Stable favicon missing or duplicated in {path.relative_to(ROOT)}")
        if text.count('href="/apple-touch-icon.png"') != 1:
            raise SystemExit(f"Apple icon missing or duplicated in {path.relative_to(ROOT)}")
        if re.search(r'href=["\'][^"\']*favicon[^"\']*\?v=', text, flags=re.I):
            raise SystemExit(f"Versioned favicon URL remains in {path.relative_to(ROOT)}")
        path.write_text(text, encoding="utf-8")
        count += 1

    headers_path = ROOT / "_headers"
    headers = headers_path.read_text(encoding="utf-8") if headers_path.is_file() else ""
    for route in ("/favicon.png", "/favicon.ico", "/apple-touch-icon.png"):
        headers = re.sub(
            rf"(?ms)^{re.escape(route)}[ \t]*\n(?:[ \t]+[^\n]*\n)*(?:[ \t]*\n)?",
            "",
            headers,
        )
    headers = headers.rstrip() + """

# Stable Google Search favicon 2026-08-27
/favicon.png
  Cache-Control: public, max-age=0, must-revalidate

/favicon.ico
  Cache-Control: public, max-age=0, must-revalidate

/apple-touch-icon.png
  Cache-Control: public, max-age=0, must-revalidate
"""
    headers_path.write_text(headers.lstrip() + "\n", encoding="utf-8")

    robots = ROOT / "robots.txt"
    if not robots.is_file():
        raise SystemExit("Missing robots.txt")
    robots_text = robots.read_text(encoding="utf-8", errors="ignore")
    if re.search(r"(?ims)^\s*user-agent:\s*googlebot-image\s*$.*?^\s*disallow:\s*/\s*$", robots_text):
        raise SystemExit("robots.txt blocks Googlebot-Image")
    if re.search(r"(?m)^\s*disallow:\s*/\s*$", robots_text, flags=re.I):
        raise SystemExit("robots.txt blocks site root")

    if png_size(search_icon) != (180, 180):
        raise SystemExit("Final /favicon.png is not 180x180")
    if search_icon.read_bytes() != source.read_bytes():
        raise SystemExit("Final /favicon.png does not match cat icon")

    print(f"Stable Google favicon finalized on {count} HTML pages: /favicon.png (180x180 cat PNG)")


if __name__ == "__main__":
    main()
