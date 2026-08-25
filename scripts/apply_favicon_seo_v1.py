#!/usr/bin/env python3
"""Publish the OOLITA cat favicon consistently across browser, Apple and SEO surfaces."""
from __future__ import annotations

from pathlib import Path
import math
import re
import struct
import sys
import zlib

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
PAPER = (242, 234, 219)
INK = (29, 33, 28)

SVG_NAME = "favicon-cat.svg"
PNG48_NAME = "favicon-48-cat.png"
ICO_NAME = "favicon-cat.ico"
APPLE_NAME = "apple-touch-icon-cat.png"

ICON_LINKS = (
    f'<link rel="icon" type="image/svg+xml" sizes="any" href="/{SVG_NAME}">\n'
    f'<link rel="icon" type="image/png" sizes="48x48" href="/{PNG48_NAME}">\n'
    f'<link rel="shortcut icon" type="image/x-icon" href="/{ICO_NAME}">\n'
    f'<link rel="apple-touch-icon" sizes="180x180" href="/{APPLE_NAME}">'
)


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


def _canvas(size: int, colour: tuple[int, int, int]) -> bytearray:
    return bytearray(colour * (size * size))


def _pixel(px: bytearray, size: int, x: int, y: int, colour: tuple[int, int, int]) -> None:
    if 0 <= x < size and 0 <= y < size:
        i = (y * size + x) * 3
        px[i : i + 3] = bytes(colour)


def _fill_ellipse(
    px: bytearray,
    size: int,
    cx: float,
    cy: float,
    rx: float,
    ry: float,
    colour: tuple[int, int, int],
) -> None:
    x0 = max(0, int(math.floor(cx - rx)))
    x1 = min(size - 1, int(math.ceil(cx + rx)))
    y0 = max(0, int(math.floor(cy - ry)))
    y1 = min(size - 1, int(math.ceil(cy + ry)))
    inv_rx = 1.0 / max(rx, 1e-6)
    inv_ry = 1.0 / max(ry, 1e-6)
    for y in range(y0, y1 + 1):
        dy = (y + 0.5 - cy) * inv_ry
        dy2 = dy * dy
        if dy2 > 1.0:
            continue
        span = rx * math.sqrt(max(0.0, 1.0 - dy2))
        xa = max(0, int(math.floor(cx - span)))
        xb = min(size - 1, int(math.ceil(cx + span)))
        for x in range(xa, xb + 1):
            _pixel(px, size, x, y, colour)


def _fill_polygon(
    px: bytearray,
    size: int,
    points: list[tuple[float, float]],
    colour: tuple[int, int, int],
) -> None:
    if len(points) < 3:
        return
    y0 = max(0, int(math.floor(min(y for _, y in points))))
    y1 = min(size - 1, int(math.ceil(max(y for _, y in points))))
    for y in range(y0, y1 + 1):
        scan_y = y + 0.5
        xs: list[float] = []
        for (x1, y1p), (x2, y2p) in zip(points, points[1:] + points[:1]):
            if y1p == y2p:
                continue
            if (y1p <= scan_y < y2p) or (y2p <= scan_y < y1p):
                t = (scan_y - y1p) / (y2p - y1p)
                xs.append(x1 + t * (x2 - x1))
        xs.sort()
        for i in range(0, len(xs) - 1, 2):
            xa = max(0, int(math.floor(xs[i])))
            xb = min(size - 1, int(math.ceil(xs[i + 1])))
            for x in range(xa, xb + 1):
                _pixel(px, size, x, y, colour)


def _stroke_segment(
    px: bytearray,
    size: int,
    a: tuple[float, float],
    b: tuple[float, float],
    width: float,
    colour: tuple[int, int, int],
) -> None:
    x1, y1 = a
    x2, y2 = b
    half = width / 2
    x0 = max(0, int(math.floor(min(x1, x2) - half - 1)))
    x3 = min(size - 1, int(math.ceil(max(x1, x2) + half + 1)))
    y0 = max(0, int(math.floor(min(y1, y2) - half - 1)))
    y3 = min(size - 1, int(math.ceil(max(y1, y2) + half + 1)))
    dx = x2 - x1
    dy = y2 - y1
    denom = dx * dx + dy * dy
    for y in range(y0, y3 + 1):
        for x in range(x0, x3 + 1):
            if denom <= 1e-9:
                t = 0.0
            else:
                t = ((x + 0.5 - x1) * dx + (y + 0.5 - y1) * dy) / denom
                t = min(1.0, max(0.0, t))
            qx = x1 + t * dx
            qy = y1 + t * dy
            if (x + 0.5 - qx) ** 2 + (y + 0.5 - qy) ** 2 <= half * half:
                _pixel(px, size, x, y, colour)


def _stroke_polyline(
    px: bytearray,
    size: int,
    points: list[tuple[float, float]],
    width: float,
    colour: tuple[int, int, int],
) -> None:
    for a, b in zip(points, points[1:]):
        _stroke_segment(px, size, a, b, width, colour)
    radius = width / 2
    for x, y in points:
        _fill_ellipse(px, size, x, y, radius, radius, colour)


def _arc_points(cx: float, cy: float, rx: float, ry: float, start_deg: float, end_deg: float, steps: int) -> list[tuple[float, float]]:
    return [
        (
            cx + rx * math.cos(math.radians(start_deg + (end_deg - start_deg) * i / steps)),
            cy + ry * math.sin(math.radians(start_deg + (end_deg - start_deg) * i / steps)),
        )
        for i in range(steps + 1)
    ]


def _quadratic_points(
    a: tuple[float, float],
    control: tuple[float, float],
    b: tuple[float, float],
    steps: int = 32,
) -> list[tuple[float, float]]:
    out = []
    for i in range(steps + 1):
        t = i / steps
        u = 1 - t
        out.append((
            u * u * a[0] + 2 * u * t * control[0] + t * t * b[0],
            u * u * a[1] + 2 * u * t * control[1] + t * t * b[1],
        ))
    return out


def _cat_icon_png(size: int) -> bytes:
    scale = 4
    s = size * scale
    px = _canvas(s, PAPER)
    ink = INK

    def n(x: float) -> float:
        return x * s

    line = max(2.0, n(0.006))

    _stroke_polyline(px, s, _arc_points(n(.50), n(.50), n(.405), n(.405), 110, 430, 180), line, ink)
    _stroke_polyline(px, s, _arc_points(n(.50), n(.50), n(.285), n(.285), 155, 515, 160), line, ink)
    _stroke_polyline(px, s, _arc_points(n(.50), n(.50), n(.165), n(.165), 205, 565, 130), line, ink)
    _stroke_polyline(
        px,
        s,
        [(n(.463), n(.645)), (n(.463), n(.825))] + _quadratic_points((n(.463), n(.825)), (n(.505), n(.94)), (n(.62), n(.89)), 34),
        line,
        ink,
    )

    tail = _quadratic_points((n(.435), n(.66)), (n(.285), n(.69)), (n(.305), n(.505)), 34)
    tail += _quadratic_points((n(.305), n(.505)), (n(.322), n(.435)), (n(.386), n(.435)), 20)[1:]
    _stroke_polyline(px, s, tail, n(.052), ink)
    _fill_ellipse(px, s, n(.50), n(.585), n(.125), n(.175), ink)
    _fill_polygon(
        px,
        s,
        [(n(.43), n(.55)), (n(.455), n(.39)), (n(.545), n(.39)), (n(.57), n(.55)), (n(.565), n(.70)), (n(.435), n(.70))],
        ink,
    )
    _fill_ellipse(px, s, n(.50), n(.382), n(.083), n(.090), ink)
    _fill_polygon(px, s, [(n(.435), n(.35)), (n(.440), n(.275)), (n(.485), n(.335))], ink)
    _fill_polygon(px, s, [(n(.515), n(.335)), (n(.560), n(.275)), (n(.565), n(.35))], ink)

    whisker_w = max(1.5, n(.006))
    for yoff, bend in ((-.012, -.006), (.012, .006)):
        _stroke_polyline(px, s, [(n(.44), n(.392 + yoff)), (n(.385), n(.382 + bend)), (n(.36), n(.392 + bend))], whisker_w, ink)
        _stroke_polyline(px, s, [(n(.56), n(.392 + yoff)), (n(.615), n(.382 + bend)), (n(.64), n(.392 + bend))], whisker_w, ink)

    out = bytearray(size * size * 3)
    block = scale * scale
    for oy in range(size):
        for ox in range(size):
            sums = [0, 0, 0]
            for sy in range(scale):
                for sx in range(scale):
                    i = (((oy * scale + sy) * s) + (ox * scale + sx)) * 3
                    sums[0] += px[i]
                    sums[1] += px[i + 1]
                    sums[2] += px[i + 2]
            j = (oy * size + ox) * 3
            out[j : j + 3] = bytes(v // block for v in sums)
    return _png(size, size, out)


def _ico_with_png(png: bytes, size: int) -> bytes:
    header = struct.pack("<HHH", 0, 1, 1)
    entry = struct.pack("<BBBBHHII", size if size < 256 else 0, size if size < 256 else 0, 0, 0, 1, 32, len(png), 22)
    return header + entry + png


def _normalise_icon_links() -> None:
    link_re = re.compile(r"<link\b[^>]*>", flags=re.I | re.S)
    rel_re = re.compile(r"\brel\s*=\s*([\"'])(.*?)\1", flags=re.I | re.S)

    def strip_icon_link(match: re.Match[str]) -> str:
        tag = match.group(0)
        rel = rel_re.search(tag)
        if not rel:
            return tag
        tokens = {token.strip().lower() for token in rel.group(2).split() if token.strip()}
        return "" if any("icon" in token for token in tokens) else tag

    count = 0
    for path in ROOT.rglob("*.html"):
        text = path.read_text(encoding="utf-8")
        if "</head>" not in text.lower():
            raise SystemExit(f"Missing </head> while publishing favicon links: {path.relative_to(ROOT)}")
        before = text
        text = link_re.sub(strip_icon_link, text)
        text, replaced = re.subn(r"</head>", ICON_LINKS + "\n</head>", text, count=1, flags=re.I)
        if replaced != 1:
            raise SystemExit(f"Could not publish favicon links in {path.relative_to(ROOT)}")
        if text != before:
            path.write_text(text, encoding="utf-8")
        count += 1
    if count == 0:
        raise SystemExit("No HTML files found while publishing favicon links")


def _normalise_headers() -> None:
    path = ROOT / "_headers"
    text = path.read_text(encoding="utf-8") if path.is_file() else ""
    routes = (
        "/favicon.svg",
        "/favicon.ico",
        "/apple-touch-icon.png",
        f"/{SVG_NAME}",
        f"/{PNG48_NAME}",
        f"/{ICO_NAME}",
        f"/{APPLE_NAME}",
    )
    for route in routes:
        text = re.sub(
            rf"(?ms)^{re.escape(route)}[ \t]*\n(?:[ \t]+[^\n]*\n)*(?:[ \t]*\n)?",
            "",
            text,
        )
    marker = "# OOLITA cat favicon + search favicon 2026-08-25"
    text = text.replace(marker, "")
    text = text.rstrip() + f"""

{marker}
/favicon.svg
  Cache-Control: public, max-age=0, must-revalidate

/favicon.ico
  Cache-Control: public, max-age=0, must-revalidate

/apple-touch-icon.png
  Cache-Control: public, max-age=0, must-revalidate

/{SVG_NAME}
  Cache-Control: public, max-age=31536000, immutable

/{PNG48_NAME}
  Cache-Control: public, max-age=31536000, immutable

/{ICO_NAME}
  Cache-Control: public, max-age=31536000, immutable

/{APPLE_NAME}
  Cache-Control: public, max-age=31536000, immutable
"""
    path.write_text(text.lstrip() + "\n", encoding="utf-8")


def _validate_png(path: Path, expected: int) -> None:
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise SystemExit(f"Invalid PNG favicon asset: {path.name}")
    width, height = struct.unpack(">II", data[16:24])
    if (width, height) != (expected, expected):
        raise SystemExit(f"Wrong PNG favicon dimensions for {path.name}: {width}x{height}")


def _validate() -> None:
    svg = ROOT / "favicon.svg"
    copied = ROOT / SVG_NAME
    if not svg.is_file() or b"<svg" not in svg.read_bytes()[:2048].lower():
        raise SystemExit("Source favicon.svg is missing or invalid")
    if copied.read_bytes() != svg.read_bytes():
        raise SystemExit("Versioned SVG favicon does not match source cat favicon")
    _validate_png(ROOT / PNG48_NAME, 48)
    _validate_png(ROOT / APPLE_NAME, 180)
    _validate_png(ROOT / "apple-touch-icon.png", 180)
    for ico_name in (ICO_NAME, "favicon.ico"):
        data = (ROOT / ico_name).read_bytes()
        if data[:6] != b"\x00\x00\x01\x00\x01\x00":
            raise SystemExit(f"Invalid ICO favicon asset: {ico_name}")

    for path in ROOT.rglob("*.html"):
        text = path.read_text(encoding="utf-8")
        for href in (f"/{SVG_NAME}", f"/{PNG48_NAME}", f"/{ICO_NAME}", f"/{APPLE_NAME}"):
            if text.count(f'href="{href}"') != 1:
                raise SystemExit(f"Favicon href {href} missing or duplicated in {path.relative_to(ROOT)}")

    robots = ROOT / "robots.txt"
    if robots.is_file():
        lower = robots.read_text(encoding="utf-8", errors="ignore").lower()
        if re.search(r"(?m)^\s*disallow:\s*/\s*$", lower):
            raise SystemExit("robots.txt blocks the site root; search favicon would not be crawlable")

    print("OOLITA favicon SEO validated: cat SVG + 48px search icon + ICO + Apple icon published on every HTML page.")


def main() -> None:
    if not ROOT.is_dir():
        raise SystemExit(f"Missing built site: {ROOT}")
    svg = ROOT / "favicon.svg"
    if not svg.is_file():
        raise SystemExit("Missing source favicon.svg")
    (ROOT / SVG_NAME).write_bytes(svg.read_bytes())

    png48 = _cat_icon_png(48)
    png64 = _cat_icon_png(64)
    png180 = _cat_icon_png(180)

    (ROOT / PNG48_NAME).write_bytes(png48)
    (ROOT / "favicon-48.png").write_bytes(png48)
    ico = _ico_with_png(png64, 64)
    (ROOT / ICO_NAME).write_bytes(ico)
    (ROOT / "favicon.ico").write_bytes(ico)
    (ROOT / APPLE_NAME).write_bytes(png180)
    (ROOT / "apple-touch-icon.png").write_bytes(png180)

    _normalise_icon_links()
    _normalise_headers()
    _validate()


if __name__ == "__main__":
    main()
