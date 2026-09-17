#!/usr/bin/env python3
"""Place the supplied archival image just below each labyrinth page opening."""
from __future__ import annotations

from pathlib import Path
import re
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
image = root / "laberinto/el-suelo-antes.jpg"
if not image.is_file():
    raise SystemExit(f"Missing supplied archive image: {image}")

style = """<style id="oolita-ground-before-style">
.oolita-ground-before{max-width:44rem;margin:0}
.oolita-ground-before img{display:block;width:100%;height:auto;border:1px solid var(--linea)}
</style>"""

pages = (
    (
        "laberinto/index.html",
        "Imagen de OOLITA rotulada «el suelo antes» y «septiembre 2021»: terreno arenoso con vegetación baja y montañas al fondo.",
    ),
    (
        "en/labyrinth/index.html",
        "OOLITA photograph labelled 'el suelo antes' and 'septiembre 2021': sandy ground with low vegetation and mountains in the background.",
    ),
)

for rel, alt in pages:
    path = root / rel
    if not path.is_file():
        raise SystemExit(f"Missing labyrinth page: {rel}")
    page = path.read_text(encoding="utf-8")
    page, style_count = re.subn(
        r'<style id="oolita-ground-before-style">.*?</style>',
        style,
        page,
        flags=re.S,
    )
    if style_count > 1:
        raise SystemExit(f"Duplicate archive styles: {rel}")
    if style_count == 0:
        if "</head>" not in page:
            raise SystemExit(f"Missing page head: {rel}")
        page = page.replace("</head>", style + "\n</head>", 1)
    if 'data-oolita-ground-before="true"' in page:
        if page.count('data-oolita-ground-before="true"') != 1:
            raise SystemExit(f"Duplicate archive figure: {rel}")
        path.write_text(page, encoding="utf-8")
        continue
    archive = (
        '<section class="tramo env" data-oolita-archive="true">'
        '<figure class="oolita-ground-before" data-oolita-ground-before="true">'
        f'<img src="/laberinto/el-suelo-antes.jpg" width="1380" height="1480" '
        f'loading="lazy" decoding="async" alt="{alt}">'
        '</figure></section>'
    )
    pattern = r'(<section class="hero">.*?</section>)'
    page, count = re.subn(pattern, lambda match: match.group(1) + "\n" + archive, page, count=1, flags=re.S)
    if count != 1:
        raise SystemExit(f"Could not locate the labyrinth opening: {rel}")
    path.write_text(page, encoding="utf-8")
    print(f"Archived ground photograph published on {rel}")
