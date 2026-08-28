#!/usr/bin/env python3
"""Restore the original homepage Sunday hero, route the current Sunday, and keep project credits out of the opening reading sequence."""
from __future__ import annotations

from pathlib import Path
import re
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
STYLE_ID = "oolita-desktop-sunday-panel-fix-v1"
STYLE = r'''<style id="oolita-desktop-sunday-panel-fix-v1">
#oolita-art-field-sundays{position:relative}
#oolita-art-field-sundays .oolita-current-sunday-hit{position:absolute;inset:0;z-index:4;display:block;color:inherit;text-decoration:none}
#oolita-art-field-sundays .oolita-current-sunday-hit:focus-visible{outline:2px solid currentColor;outline-offset:-6px}
body.art-home p.oolita-project-credit{
  max-width:46rem!important;
  margin-top:clamp(2rem,4vw,4rem)!important;
  margin-right:max(3vw,calc((100vw - 1640px)/2))!important;
  margin-bottom:clamp(3rem,6vw,5rem)!important;
  margin-left:max(3vw,calc((100vw - 1640px)/2))!important;
  font-size:clamp(.82rem,1vw,.95rem)!important;
  line-height:1.55!important;
  letter-spacing:.01em!important;
}
@media(min-width:760.01px){
  body.art-home .hero .der{
    min-width:0;
    overflow:hidden;
    display:flex;
    flex-direction:column;
    margin-inline:auto!important;
  }
  body.art-home #oolita-art-field-sundays{
    width:100%!important;
    max-width:100%!important;
    min-height:0!important;
    height:18.5rem!important;
    max-height:18.5rem!important;
    aspect-ratio:auto!important;
    flex:0 0 auto!important;
    margin-block:0!important;
    margin-inline:auto!important;
    padding:clamp(1.4rem,2.2vw,2rem)!important;
    display:flex!important;
    flex-direction:column!important;
    align-content:initial!important;
    justify-content:flex-start!important;
  }
  body.art-home #oolita-art-field-sundays .art-kicker{
    position:static!important;
    inset:auto!important;
    display:block!important;
    margin:0!important;
    font-size:clamp(.68rem,.78vw,.78rem)!important;
    line-height:1.3!important;
    letter-spacing:.15em!important;
  }
  body.art-home #oolita-art-field-sundays .art-word{
    max-width:100%!important;
    margin:2.25rem 0 0!important;
    font-size:clamp(5rem,6vw,5.75rem)!important;
    line-height:.74!important;
    letter-spacing:-.06em!important;
    overflow-wrap:normal!important;
    white-space:nowrap!important;
  }
  body.art-home #oolita-art-field-sundays .art-caption{
    max-width:16rem!important;
    margin:clamp(.9rem,1.3vw,1.25rem) 0 0!important;
    font-size:clamp(.8rem,.88vw,.9rem)!important;
    line-height:1.35!important;
  }
}
@media(max-width:760px){
  body.art-home p.oolita-project-credit{margin:2rem 1.35rem 3rem!important;font-size:.88rem!important}
}
</style>'''

CURRENT = {
    "index.html": {
        "href": "/domingos/03-la-memoria-del-mar/",
        "aria": "Domingo 03 · La memoria del mar · 23 de agosto de 2026",
        "kicker": "03 · LA MEMORIA DEL MAR",
        "word": "03",
        "caption": "23.08.26 · La piedra guarda la memoria del mar.",
        "credit_marker": "Raquel Costantini hizo el laberinto",
    },
    "en/index.html": {
        "href": "/en/sundays/03-the-memory-of-the-sea/",
        "aria": "Sunday 03 · The Memory of the Sea · 23 August 2026",
        "kicker": "03 · THE MEMORY OF THE SEA",
        "word": "03",
        "caption": "23 Aug 26 · The stone holds the memory of the sea.",
        "credit_marker": "Raquel Costantini made the labyrinth",
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
hero_work_pattern = re.compile(
    r'<figure\b[^>]*class=["\'][^"\']*\boolita-hero-work\b[^"\']*["\'][^>]*>[\s\S]*?</figure>',
    flags=re.I,
)
paragraph_pattern = re.compile(r'<p\b[^>]*>[\s\S]*?</p>', flags=re.I)
timer_pattern = re.compile(r'\brole\s*=\s*["\']timer["\']', flags=re.I)


def set_tag_attribute(tag: str, name: str, value: str) -> str:
    attr = re.compile(rf'\b{re.escape(name)}\s*=\s*(["\']).*?\1', flags=re.I | re.S)
    replacement = f'{name}="{value}"'
    if attr.search(tag):
        return attr.sub(replacement, tag, count=1)
    return tag[:-1] + f' {replacement}>'


def add_class(tag: str, class_name: str) -> str:
    match = re.search(r'\bclass\s*=\s*(["\'])(.*?)\1', tag, flags=re.I | re.S)
    if match:
        classes = match.group(2).split()
        if class_name in classes:
            return tag
        updated = " ".join([*classes, class_name])
        return tag[:match.start(2)] + updated + tag[match.end(2):]
    return tag[:-1] + f' class="{class_name}">'


def visible_text(fragment: str) -> str:
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', fragment)).strip()


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


def move_project_credit(html: str, marker: str, rel: str) -> str:
    matches = [match for match in paragraph_pattern.finditer(html) if marker in visible_text(match.group(0))]
    if len(matches) != 1:
        raise SystemExit(f"Expected one homepage project credit in {rel}, found {len(matches)}")
    match = matches[0]
    block = match.group(0)
    opening = re.match(r'<p\b[^>]*>', block, flags=re.I)
    if not opening:
        raise SystemExit(f"Malformed homepage project credit in {rel}")
    new_opening = add_class(opening.group(0), "oolita-project-credit")
    block = new_opening + block[opening.end():]
    html = html[:match.start()] + html[match.end():]

    timer = timer_pattern.search(html)
    if not timer:
        raise SystemExit(f"Homepage countdown timer missing in {rel}")
    section_start = html.rfind("<section", 0, timer.start())
    section_end_start = html.find("</section>", timer.end())
    if section_start < 0 or section_end_start < 0:
        raise SystemExit(f"Could not locate countdown section boundaries in {rel}")
    insert_at = section_end_start + len("</section>")
    return html[:insert_at] + "\n" + block + "\n" + html[insert_at:]


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
    html = hero_work_pattern.sub("", html)
    html = patch_current_sunday(html, config, rel)
    html = move_project_credit(html, config["credit_marker"], rel)
    target.write_text(html, encoding="utf-8")

for rel, config in CURRENT.items():
    html = (ROOT / rel).read_text(encoding="utf-8")
    required = (
        STYLE_ID,
        "#oolita-art-field-sundays",
        "@media(min-width:760.01px)",
        "margin-inline:auto!important",
        "width:100%!important",
        "min-height:0!important",
        "height:18.5rem!important",
        "max-height:18.5rem!important",
        'data-current-sunday="03"',
        f'href="{config["href"]}"',
        config["kicker"],
        config["caption"],
        "oolita-current-sunday-hit",
        "oolita-project-credit",
        config["credit_marker"],
    )
    for needle in required:
        if needle not in html:
            raise SystemExit(f"Homepage hierarchy invariant failed in {rel}: {needle}")
    if 'oolita-hero-work' in html:
        raise SystemExit(f"Labyrinth hero image was not removed in {rel}")
    if html.count('class="oolita-current-sunday-hit"') != 1:
        raise SystemExit(f"Current Sunday hit target duplicated in {rel}")
    credit_pos = html.find(config["credit_marker"])
    timer = timer_pattern.search(html)
    if not timer or credit_pos <= timer.start():
        raise SystemExit(f"Project credit did not move below the countdown in {rel}")

print("OOLITA original no-image hero, centered current-Sunday panel, desktop containment and opening credit hierarchy validated in both homepages.")