#!/usr/bin/env python3
"""Publish the stable cat favicon and final reader-facing book excerpt composition."""
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


def finalize_book_excerpt() -> None:
    """Keep the genuine illustration physically and visually with its excerpt.

    This deliberately runs at the last reader-facing deployment stage so an
    earlier hierarchy pass cannot move the illustration back into the hero.
    """
    marker = "Electro frente al trazado del laberinto Oolita"
    style_id = "oolita-book-excerpt-final-v3"
    style = r'''<style id="oolita-book-excerpt-final-v3">
#extracto-libro .book-excerpt-layout{
  display:grid!important;
  grid-template-columns:minmax(15rem,20rem) minmax(0,1fr)!important;
  gap:clamp(2rem,4vw,4rem)!important;
  align-items:start!important;
  width:min(100%,72rem)!important;
  max-width:72rem!important;
  margin:clamp(1.75rem,3vw,2.75rem) auto 0!important;
}
#extracto-libro .book-excerpt-figure{
  display:block!important;
  float:none!important;
  clear:none!important;
  width:100%!important;
  max-width:20rem!important;
  margin:0 auto!important;
  padding:0!important;
  text-align:center!important;
}
#extracto-libro .book-excerpt-figure img{
  display:block!important;
  width:100%!important;
  max-width:20rem!important;
  height:auto!important;
  margin:0 auto!important;
}
#extracto-libro .book-excerpt-figure figcaption{
  margin:.7rem auto 0!important;
  max-width:20rem!important;
}
#extracto-libro .book-excerpt-spread{
  display:grid!important;
  grid-template-columns:repeat(2,minmax(0,1fr))!important;
  width:100%!important;
  max-width:none!important;
  margin:0!important;
}
@media(max-width:1100px){
  #extracto-libro .book-excerpt-layout{
    grid-template-columns:1fr!important;
    width:min(100%,52rem)!important;
    max-width:52rem!important;
  }
  #extracto-libro .book-excerpt-figure{max-width:18rem!important}
  #extracto-libro .book-excerpt-figure img{max-width:18rem!important}
}
@media(max-width:760px){
  #extracto-libro .book-excerpt-layout{width:100%!important}
  #extracto-libro .book-excerpt-spread{grid-template-columns:1fr!important}
  #extracto-libro .book-excerpt-page+.book-excerpt-page{
    border-left:0!important;
    border-top:1px solid rgba(45,78,35,.45)!important;
  }
}
</style>'''

    figure_re = re.compile(r'<figure\b[^>]*>[\s\S]*?</figure>', flags=re.I)
    layout_open_re = re.compile(
        r'<div\b[^>]*class=["\'][^"\']*\bbook-excerpt-layout\b[^"\']*["\'][^>]*>',
        flags=re.I,
    )

    for rel in ("ediciones/libro/index.html", "en/editions/book/index.html"):
        path = ROOT / rel
        if not path.is_file():
            raise SystemExit(f"Missing book page: {rel}")
        text = path.read_text(encoding="utf-8")

        figures = [m for m in figure_re.finditer(text) if marker in m.group(0)]
        if len(figures) != 1:
            raise SystemExit(f"Expected one genuine book illustration in {rel}; found {len(figures)}")

        figure = figures[0]
        block = figure.group(0)
        opening = re.match(r'<figure\b[^>]*>', block, flags=re.I)
        if not opening:
            raise SystemExit(f"Malformed book figure in {rel}")
        tag = opening.group(0)
        tag = re.sub(r'\s+style\s*=\s*(["\']).*?\1', '', tag, flags=re.I | re.S)
        cm = re.search(r'\bclass\s*=\s*(["\'])(.*?)\1', tag, flags=re.I | re.S)
        if cm:
            classes = [c for c in cm.group(2).split() if c != "oolita-book-hero-visual"]
            if "book-excerpt-figure" not in classes:
                classes.append("book-excerpt-figure")
            tag = tag[:cm.start(2)] + " ".join(classes) + tag[cm.end(2):]
        else:
            tag = tag[:-1] + ' class="book-excerpt-figure">'
        block = tag + block[opening.end():]

        # Remove the illustration from wherever an earlier stage placed it.
        text = text[:figure.start()] + text[figure.end():]

        layout = layout_open_re.search(text)
        if not layout:
            raise SystemExit(f"Missing book excerpt layout in {rel}")
        text = text[:layout.end()] + "\n" + block + "\n" + text[layout.end():]

        # One authoritative composition rule only.
        for old_id in (
            "oolita-book-visual-first-v1",
            "oolita-book-reading-width-v1",
            "oolita-book-excerpt-composed-v2",
            style_id,
        ):
            text = re.sub(
                rf'<style\s+id=["\']{re.escape(old_id)}["\'][^>]*>[\s\S]*?</style>',
                "",
                text,
                flags=re.I,
            )
        if "</head>" not in text.lower():
            raise SystemExit(f"Book page has no </head>: {rel}")
        text = re.sub(r"</head>", style + "\n</head>", text, count=1, flags=re.I)

        # Fail closed on the exact relationship the reader must see.
        id_pos = text.find('id="extracto-libro"')
        if id_pos < 0:
            raise SystemExit(f"Missing excerpt section in {rel}")
        section_start = text.rfind("<section", 0, id_pos)
        section_end = text.find("</section>", id_pos)
        if section_start < 0 or section_end < 0:
            raise SystemExit(f"Malformed excerpt section in {rel}")
        section = text[section_start:section_end]
        if marker not in section:
            raise SystemExit(f"Book illustration is not inside excerpt section in {rel}")
        layout_pos = section.find("book-excerpt-layout")
        marker_pos = section.find(marker)
        spread_pos = section.find("book-excerpt-spread")
        if not (0 <= layout_pos < marker_pos < spread_pos):
            raise SystemExit(f"Image and bilingual passage are not composed together in {rel}")
        if marker in text[:section_start] or marker in text[section_end:]:
            raise SystemExit(f"Book illustration remains outside excerpt in {rel}")
        if "oolita-book-hero-visual" in text:
            raise SystemExit(f"Hero-only illustration class survived in {rel}")
        if text.count(f'id="{style_id}"') != 1:
            raise SystemExit(f"Final excerpt style missing or duplicated in {rel}")

        path.write_text(text, encoding="utf-8")

    print("Book excerpt finalized: illustration + bilingual passage remain together and centered in ES/EN.")


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

    # This is intentionally the final reader-facing mutation before the static
    # href/canonical/hreflang/404 integrity audit in the deployment workflow.
    finalize_book_excerpt()

    print(f"Stable Google favicon finalized on {count} HTML pages: /favicon.png (180x180 cat PNG)")


if __name__ == "__main__":
    main()
