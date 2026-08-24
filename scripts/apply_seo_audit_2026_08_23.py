#!/usr/bin/env python3
"""Repair the critical/high SEO faults found in the 23 Aug 2026 live audit.

This runs on the reconstructed Cloudflare Pages bundle. It deliberately creates
its own canonical social card and 404 page instead of trusting a soft-200 origin.
"""
from __future__ import annotations

from pathlib import Path
import re
import struct
import sys
import zlib

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
SOCIAL_URL = "https://oolita.es/og.png"
PAPER = (242, 234, 219)
GREEN = (45, 78, 57)
BLUE = (42, 83, 105)
INK = (34, 43, 36)


def _chunk(kind: bytes, payload: bytes) -> bytes:
    body = kind + payload
    return struct.pack(">I", len(payload)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)


def _png(width: int, height: int, pixels: bytearray) -> bytes:
    stride = width * 3
    raw = bytearray()
    for y in range(height):
        raw.append(0)
        start = y * stride
        raw.extend(pixels[start : start + stride])
    signature = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return signature + _chunk(b"IHDR", ihdr) + _chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + _chunk(b"IEND", b"")


def _canvas(width: int, height: int, bg: tuple[int, int, int]) -> bytearray:
    return bytearray(bg * (width * height))


def _rect(px: bytearray, width: int, height: int, x: int, y: int, w: int, h: int, colour: tuple[int, int, int]) -> None:
    x0, x1 = max(0, x), min(width, x + w)
    y0, y1 = max(0, y), min(height, y + h)
    row = bytes(colour) * max(0, x1 - x0)
    for yy in range(y0, y1):
        i = (yy * width + x0) * 3
        px[i : i + len(row)] = row


def _line(px: bytearray, width: int, height: int, x0: int, y0: int, x1: int, y1: int, colour: tuple[int, int, int], thickness: int = 1) -> None:
    dx = abs(x1 - x0)
    sx = 1 if x0 < x1 else -1
    dy = -abs(y1 - y0)
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    r = max(0, thickness // 2)
    while True:
        _rect(px, width, height, x0 - r, y0 - r, 2 * r + 1, 2 * r + 1, colour)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("11111", "00100", "00100", "00100", "00100", "00100", "11111"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
}


def _text(px: bytearray, width: int, height: int, text: str, x: int, y: int, scale: int, colour: tuple[int, int, int]) -> None:
    cursor = x
    for ch in text:
        glyph = FONT.get(ch)
        if glyph:
            for gy, row in enumerate(glyph):
                for gx, bit in enumerate(row):
                    if bit == "1":
                        _rect(px, width, height, cursor + gx * scale, y + gy * scale, scale, scale, colour)
        cursor += 6 * scale


def _social_card() -> bytes:
    w, h = 1200, 630
    px = _canvas(w, h, PAPER)
    _rect(px, w, h, 0, 0, w, 10, GREEN)
    _rect(px, w, h, 0, h - 10, w, 10, BLUE)
    points = [
        (100, 315), (140, 315), (140, 125), (400, 125), (400, 505),
        (180, 505), (180, 165), (360, 165), (360, 465), (220, 465),
        (220, 205), (320, 205), (320, 425), (260, 425), (260, 245),
        (280, 245), (280, 385), (300, 385), (300, 285),
    ]
    for a, b in zip(points, points[1:]):
        _line(px, w, h, a[0], a[1], b[0], b[1], GREEN, 9)
    _line(px, w, h, 300, 285, 300, 315, BLUE, 9)
    _text(px, w, h, "OOLITA", 500, 235, 18, INK)
    _rect(px, w, h, 505, 400, 565, 3, GREEN)
    _rect(px, w, h, 505, 425, 360, 3, BLUE)
    return _png(w, h, px)


def _icon_png(size: int) -> bytes:
    px = _canvas(size, size, PAPER)
    margin = max(8, size // 10)
    rule = max(3, size // 24)
    _rect(px, size, size, margin, margin, size - 2 * margin, rule, GREEN)
    _rect(px, size, size, margin, size - margin - rule, size - 2 * margin, rule, BLUE)
    scale = max(4, size // 20)
    glyph_w = 5 * scale
    glyph_h = 7 * scale
    _text(px, size, size, "O", (size - glyph_w) // 2, (size - glyph_h) // 2, scale, GREEN)
    return _png(size, size, px)


def _ico_with_png(png: bytes, size: int) -> bytes:
    header = struct.pack("<HHH", 0, 1, 1)
    entry = struct.pack("<BBBBHHII", size, size, 0, 0, 1, 32, len(png), 6 + 16)
    return header + entry + png


def _set_meta(text: str, attr: str, key: str, value: str) -> str:
    pattern = rf'<meta\b(?=[^>]*\b{re.escape(attr)}=["\']{re.escape(key)}["\'])[^>]*>'
    tag = f'<meta {attr}="{key}" content="{value}">'
    if re.search(pattern, text, flags=re.I):
        return re.sub(pattern, tag, text, count=1, flags=re.I)
    return text


def _normalise_social_images() -> None:
    legacy_paths = (
        "/laberinto/social-laberinto.jpg",
        "/laberinto/social-labyrinth.jpg",
        "/carteles/img/social-carteles.png",
        "/carteles/img/social-posters.png",
        "/domingos/img/social-01.jpg",
        "/domingos/img/social-02.png",
        "/que-es-un-oolito/social.jpg",
    )
    for path in ROOT.rglob("*.html"):
        text = path.read_text(encoding="utf-8")
        before = text
        for legacy in legacy_paths:
            text = text.replace(f"https://oolita.es{legacy}", SOCIAL_URL)
            text = text.replace(f"https://www.oolita.es{legacy}", SOCIAL_URL)
        text = _set_meta(text, "property", "og:image", SOCIAL_URL)
        text = _set_meta(text, "property", "og:image:secure_url", SOCIAL_URL)
        text = _set_meta(text, "name", "twitter:image", SOCIAL_URL)
        lang_en = bool(re.search(r'<html\b[^>]*\blang=["\']en(?:-[^"\']*)?["\']', text, flags=re.I))
        alt = "OOLITA — stone, paper and code in Cabo de Gata" if lang_en else "OOLITA — piedra, papel y código en Cabo de Gata"
        text = _set_meta(text, "property", "og:image:alt", alt)
        text = _set_meta(text, "name", "twitter:image:alt", alt)
        if text != before:
            path.write_text(text, encoding="utf-8")


def _fix_schema() -> None:
    for rel in ("ediciones/libro/index.html", "en/editions/book/index.html"):
        path = ROOT / rel
        if not path.is_file():
            raise SystemExit(f"Missing book page: {rel}")
        text = path.read_text(encoding="utf-8")
        text = re.sub(r'("numberOfPages"\s*:\s*)44\b', r"\g<1>48", text)
        path.write_text(text, encoding="utf-8")

    for rel in ("ediciones/camiseta/index.html", "en/editions/t-shirt/index.html"):
        path = ROOT / rel
        if not path.is_file():
            raise SystemExit(f"Missing t-shirt page: {rel}")
        text = path.read_text(encoding="utf-8")
        text = re.sub(r'("@type"\s*:\s*["\'])Product(["\'])', r"\g<1>CreativeWork\g<2>", text)
        path.write_text(text, encoding="utf-8")

    lab = ROOT / "laberinto/index.html"
    if lab.is_file():
        text = lab.read_text(encoding="utf-8")
        text = text.replace(
            "Cómo llegar, qué esperar. Cómo llegar, qué esperar y cómo acercarse con cuidado.",
            "Cómo llegar, qué esperar y cómo acercarse con cuidado.",
        )
        lab.write_text(text, encoding="utf-8")


def _write_404() -> None:
    html = '''<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,follow">
<title>404 · OOLITA</title>
<style>
:root{--papel:#f2eadb;--verde:#2d4e39;--azul:#2a5369;--tinta:#222b24}
*{box-sizing:border-box}html,body{margin:0;min-height:100%;background:var(--papel);color:var(--tinta)}
body{font-family:system-ui,-apple-system,Segoe UI,sans-serif;display:grid;place-items:center;padding:2rem}
main{width:min(46rem,100%);border-top:8px solid var(--verde);border-bottom:8px solid var(--azul);padding:clamp(2rem,7vw,5rem) 0}
p{font-size:clamp(1rem,2.2vw,1.2rem);line-height:1.6;max-width:38rem}h1{font-size:clamp(4rem,18vw,10rem);line-height:.85;margin:0 0 1.5rem;letter-spacing:-.06em}
a{color:var(--verde);font-weight:700;text-underline-offset:.2em}nav{display:flex;gap:1.25rem;flex-wrap:wrap;margin-top:2rem}
</style>
</head>
<body><main>
<h1>404</h1>
<p><strong>Esta página no existe.</strong> Puedes volver a OOLITA o entrar directamente en el laberinto.</p>
<p lang="en"><strong>This page does not exist.</strong> Return to OOLITA or go directly to the labyrinth.</p>
<nav aria-label="404 navigation"><a href="/">OOLITA · ES</a><a href="/en/">OOLITA · EN</a><a href="/laberinto/">Laberinto</a><a href="/en/labyrinth/">Labyrinth</a></nav>
</main></body></html>'''
    (ROOT / "404.html").write_text(html, encoding="utf-8")


def _remove_spa_catchall() -> None:
    path = ROOT / "_redirects"
    if not path.is_file():
        return
    lines = path.read_text(encoding="utf-8").splitlines()
    kept = []
    for line in lines:
        compact = re.sub(r"\s+", " ", line.strip())
        if compact.lower() == "/* /index.html 200":
            continue
        kept.append(line)
    path.write_text("\n".join(kept).rstrip() + "\n", encoding="utf-8")


def _merge_headers() -> None:
    path = ROOT / "_headers"
    current = path.read_text(encoding="utf-8") if path.is_file() else ""

    audit_marker = "# OOLITA SEO audit 2026-08-23"
    if audit_marker not in current:
        current = current.rstrip() + f"""
{audit_marker}
/fonts/*
  Cache-Control: public, max-age=31536000, immutable

/*.avif
  Cache-Control: public, max-age=2592000

/*.webp
  Cache-Control: public, max-age=2592000

/og.png
  Cache-Control: public, max-age=604800

/apple-touch-icon.png
  Cache-Control: public, max-age=2592000

/favicon.ico
  Cache-Control: public, max-age=2592000
"""

    technical_marker = "# OOLITA technical SEO 2026-08-24"
    if technical_marker not in current:
        current = current.rstrip() + f"""
{technical_marker}
https://oolita.pages.dev/*
  X-Robots-Tag: noindex

https://:version.oolita.pages.dev/*
  X-Robots-Tag: noindex

/domingos/img/*
  Cache-Control: public, max-age=2592000

/carteles/img/*
  Cache-Control: public, max-age=2592000

/img/*
  Cache-Control: public, max-age=2592000

/reels/*
  Cache-Control: public, max-age=2592000
"""
    path.write_text(current.lstrip() + "\n", encoding="utf-8")


def _write_assets() -> None:
    (ROOT / "og.png").write_bytes(_social_card())
    (ROOT / "apple-touch-icon.png").write_bytes(_icon_png(180))
    icon = _icon_png(64)
    (ROOT / "favicon.ico").write_bytes(_ico_with_png(icon, 64))


def _validate() -> None:
    og = ROOT / "og.png"
    if not og.is_file() or og.read_bytes()[:8] != b"\x89PNG\r\n\x1a\n":
        raise SystemExit("og.png was not generated as a PNG")
    if not (ROOT / "404.html").is_file():
        raise SystemExit("404.html missing")
    error_html = (ROOT / "404.html").read_text(encoding="utf-8")
    if 'name="robots" content="noindex,follow"' not in error_html:
        raise SystemExit("404.html missing noindex,follow")
    headers_text = (ROOT / "_headers").read_text(encoding="utf-8")
    required_header_rules = (
        "https://oolita.pages.dev/*",
        "https://:version.oolita.pages.dev/*",
        "X-Robots-Tag: noindex",
        "/fonts/*",
        "max-age=31536000, immutable",
        "/domingos/img/*",
        "/reels/*",
    )
    for rule in required_header_rules:
        if rule not in headers_text:
            raise SystemExit(f"Required technical header rule missing: {rule}")

    redirects = ROOT / "_redirects"
    if redirects.is_file() and re.search(r"(?m)^\s*/\*\s+/index\.html\s+200\s*$", redirects.read_text(encoding="utf-8"), flags=re.I):
        raise SystemExit("SPA 200 catch-all still present in _redirects")

    for path in ROOT.rglob("*.html"):
        text = path.read_text(encoding="utf-8")
        head = text.split("</head>", 1)[0]
        if re.search(r'<meta\b(?=[^>]*(?:property|name)=["\'](?:og:image|twitter:image)["\'])[^>]*>', head, flags=re.I):
            if SOCIAL_URL not in head:
                raise SystemExit(f"Non-canonical social image remains in {path.relative_to(ROOT)}")

    for rel in ("ediciones/libro/index.html", "en/editions/book/index.html"):
        text = (ROOT / rel).read_text(encoding="utf-8")
        if re.search(r'"numberOfPages"\s*:\s*44\b', text):
            raise SystemExit(f"Stale 44-page schema remains in {rel}")
    for rel in ("ediciones/camiseta/index.html", "en/editions/t-shirt/index.html"):
        text = (ROOT / rel).read_text(encoding="utf-8")
        if re.search(r'"@type"\s*:\s*["\']Product["\']', text):
            raise SystemExit(f"Product schema without offers remains in {rel}")

    print(f"SEO audit fixes validated: og.png={og.stat().st_size} bytes; 404 + schema checks pass")


def main() -> None:
    if not ROOT.is_dir():
        raise SystemExit(f"Site root does not exist: {ROOT}")
    _write_assets()
    _write_404()
    _remove_spa_catchall()
    _merge_headers()
    _normalise_social_images()
    _fix_schema()
    _validate()


if __name__ == "__main__":
    main()
