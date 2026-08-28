#!/usr/bin/env python3
"""Keep the homepage Sunday artwork inside its desktop hero column and make the current Sunday the live hero route."""
from __future__ import annotations

from pathlib import Path
import re
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
STYLE_ID = "oolita-desktop-sunday-panel-fix-v1"
STYLE = r'''<style id="oolita-desktop-sunday-panel-fix-v1">
/* The Sunday field is nested in the hero's right column. The general art-field
   rule makes fields viewport-wide; on desktop that caused this one to cover the
   hero copy. Keep it contained here, while retaining the full-width mobile row. */
#oolita-art-field-sundays{position:relative}
#oolita-art-field-sundays .oolita-current-sunday-hit{
  position:absolute;
  inset:0;
  z-index:4;
  display:block;
  color:inherit;
  text-decoration:none;
}
#oolita-art-field-sundays .oolita-current-sunday-hit:focus-visible{
  outline:2px solid currentColor;
  outline-offset:-6px;
}
@media(min-width:56.001rem){
  body.art-home .hero .der{
    min-width:0;
    overflow:hidden;
    display:flex;
    flex-direction:column;
  }
  body.art-home #oolita-art-field-sundays{
    width:100%!important;
    max-width:100%!important;
    min-height:100%!important;
    margin:0!important;
    padding:clamp(1.5rem,2.4vw,2.5rem)!important;
  }
  body.art-home #oolita-art-field-sundays .art-kicker{
    top:clamp(1.5rem,2.4vw,2.5rem)!important;
    left:clamp(1.5rem,2.4vw,2.5rem)!important;
  }
  body.art-home #oolita-art-field-sundays .art-word{
    max-width:100%!important;
    font-size:clamp(8rem,11.5vw,12rem)!important;
    line-height:.68!important;
    overflow-wrap:normal!important;
    white-space:nowrap!important;
  }
  body.art-home #oolita-art-field-sundays .art-caption{
    max-width:18rem!important;
    margin:clamp(1.25rem,2vw,2rem) 0 0!important;
    font-size:clamp(.95rem,1.1vw,1.1rem)!important;
  }
}
</style>'''

CURRENT = {
    "index.html": {
        "href": "/domingos/03-la-memoria-del-mar/",
        "aria": "Domingo 03 · La memoria del mar · 23 de agosto de 2026",
        "kicker": "03 · LA MEMORIA DEL MAR",
        "word": "03",
        "caption": "23.08.26 · La piedra guarda la memoria del mar.",
    },
    "en/index.html": {
        "href": "/en/sundays/03-the-memory-of-the-sea/",
        "aria": "Sunday 03 · The Memory of the Sea · 23 August 2026",
        "kicker": "03 · THE MEMORY OF THE SEA",
        "word": "03",
        "caption": "23 Aug 26 · The stone holds the memory of the sea.",
    },
}

if not ROOT.is_dir():
    raise SystemExit(f"Missing built site: {ROOT}")

style_pattern = re.compile(
    rf'<style\s+id=["\']{re.escape(STYLE_ID)}["\'][^>]*>.*?</style>',
    flags=re.I | re.S,
)
panel_pattern = re.compile(
    r'<section\b(?=[^>]*\bid=["\']oolita-art-field-sundays["\'])[^>]*>[\s\S]*?</section>',
    flags=re.I,
)
hit_pattern = re.compile(
    r'<a\b[^>]*class=["\'][^"\']*\boolita-current-sunday-hit\b[^"\']*["\'][^>]*>[\s\S]*?</a>',
    flags=re.I,
)


def set_tag_attribute(tag: str, name: str, value: str) -> str:
    attr = re.compile(rf'\b{re.escape(name)}\s*=\s*(["\']).*?\1', flags=re.I | re.S)
    replacement = f'{name}="{value}"'
    if attr.search(tag):
        return attr.sub(replacement, tag, count=1)
    return tag[:-1] + f' {replacement}>'


def replace_class_text(block: str, class_name: str, value: str) -> str:
    pattern = re.compile(
        rf'(<(?P<tag>[a-z0-9]+)\b[^>]*class=["\'][^"\']*\b{re.escape(class_name)}\b[^"\']*["\'][^>]*>)[\s\S]*?(</(?P=tag)>)',
        flags=re.I,
    )
    updated, count = pattern.subn(lambda m: m.group(1) + value + m.group(3), block, count=1)
    if count != 1:
        raise SystemExit(f"Current Sunday panel is missing .{class_name}")
    return updated


def patch_current_sunday(html: str, config: dict[str, str], rel: str) -> str:
    match = panel_pattern.search(html)
    if not match:
        raise SystemExit(f"Sunday hero panel missing in {rel}")
    block = hit_pattern.sub("", match.group(0))
    opening = re.match(r'<section\b[^>]*>', block, flags=re.I)
    if not opening:
        raise SystemExit(f"Sunday hero panel opening tag malformed in {rel}")
    tag = opening.group(0)
    tag = set_tag_attribute(tag, "aria-label", config["aria"])
    tag = set_tag_attribute(tag, "data-current-sunday", "03")
    block = tag + block[opening.end():]
    block = replace_class_text(block, "art-kicker", config["kicker"])
    block = replace_class_text(block, "art-word", config["word"])
    block = replace_class_text(block, "art-caption", config["caption"])
    hit = (
        f'<a class="oolita-current-sunday-hit" href="{config["href"]}" '
        f'aria-label="{config["aria"]}"></a>'
    )
    block = block.replace("</section>", hit + "</section>", 1)
    return html[:match.start()] + block + html[match.end():]


for rel, config in CURRENT.items():
    target = ROOT / rel
    if not target.is_file():
        raise SystemExit(f"Missing homepage: {rel}")
    html = target.read_text(encoding="utf-8")
    if style_pattern.search(html):
        html = style_pattern.sub(STYLE, html, count=1)
    elif "</head>" in html:
        html = html.replace("</head>", STYLE + "\n</head>", 1)
    else:
        raise SystemExit(f"Homepage has no </head>: {rel}")
    html = patch_current_sunday(html, config, rel)
    target.write_text(html, encoding="utf-8")

for rel, config in CURRENT.items():
    html = (ROOT / rel).read_text(encoding="utf-8")
    required = (
        STYLE_ID,
        "#oolita-art-field-sundays",
        "width:100%!important",
        'data-current-sunday="03"',
        f'href="{config["href"]}"',
        config["kicker"],
        config["caption"],
        "oolita-current-sunday-hit",
    )
    for needle in required:
        if needle not in html:
            raise SystemExit(f"Desktop Sunday panel invariant failed in {rel}: {needle}")
    if html.count('class="oolita-current-sunday-hit"') != 1:
        raise SystemExit(f"Current Sunday hit target duplicated in {rel}")

print("OOLITA current-Sunday hero route and desktop panel containment validated in both homepages.")
