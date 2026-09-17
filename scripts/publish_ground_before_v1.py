#!/usr/bin/env python3
"""Place the supplied archival image beside OOLITA's account of the clearing."""
from __future__ import annotations

from pathlib import Path
import re
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
image = root / "laberinto/el-suelo-antes.jpg"
if not image.is_file():
    raise SystemExit(f"Missing supplied archive image: {image}")

style = """<style id="oolita-ground-before-style">
.oolita-ground-before{max-width:44rem;margin:clamp(1.5rem,4vw,2.5rem) 0 0}
.oolita-ground-before img{display:block;width:100%;height:auto;border:1px solid var(--linea)}
.oolita-ground-before figcaption{margin-top:.7rem;color:var(--tinta);font-size:.82rem;line-height:1.45}
</style>"""

pages = (
    (
        "laberinto/index.html",
        "El método",
        "El suelo antes",
        "Vista del terreno despejado y la vegetación baja antes de aparecer el trazado de piedras; al fondo, la costa y las montañas.",
        "Imagen del archivo de OOLITA, rotulada «septiembre 2021».",
    ),
    (
        "en/labyrinth/index.html",
        "The method",
        "The ground before",
        "A clearing with sparse low vegetation before the stone pattern appears; coast and mountains in the background.",
        "From the OOLITA archive, labelled “September 2021”.",
    ),
)

for rel, marker, label, alt, caption in pages:
    path = root / rel
    if not path.is_file():
        raise SystemExit(f"Missing labyrinth page: {rel}")
    page = path.read_text(encoding="utf-8")
    if 'data-oolita-ground-before="true"' in page:
        if page.count('data-oolita-ground-before="true"') != 1:
            raise SystemExit(f"Duplicate archive figure: {rel}")
        continue
    figure = (
        '<figure class="oolita-ground-before" data-oolita-ground-before="true">'
        f'<img src="/laberinto/el-suelo-antes.jpg" width="1380" height="1480" '
        f'loading="lazy" decoding="async" alt="{alt}">'
        f'<figcaption><strong>{label}.</strong> {caption}</figcaption></figure>'
    )
    pattern = rf'(<section class="tramo"><span class="rot">{re.escape(marker)}</span>.*?)(</section>)'
    page, count = re.subn(pattern, lambda match: match.group(1) + figure + match.group(2), page, count=1, flags=re.S)
    if count != 1:
        raise SystemExit(f"Could not locate the method section: {rel}")
    if "oolita-ground-before-style" not in page:
        page = page.replace("</head>", style + "\n</head>", 1)
    path.write_text(page, encoding="utf-8")
    print(f"Archived ground photograph published on {rel}")
