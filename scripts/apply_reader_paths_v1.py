#!/usr/bin/env python3
"""Give the book, 3D world and Sundays one clear onward path.

The existing OOLITA list remains the only signup point. These pages lead back
to it with the relevant interest already selected, while keeping each page's
own rhythm and language intact.
"""
from __future__ import annotations

from html import unescape
from pathlib import Path
import re
import sys


ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")

BOOK_PATHS = {
    "ediciones/libro/index.html": {
        "follow": "/?follow=book#seguir-oolita",
        "phrases": ("Avísame por correo", "Avísame cuando pueda comprarlo"),
    },
    "en/editions/book/index.html": {
        "follow": "/en/?follow=book#follow-oolita",
        "phrases": ("Let me know by email", "Tell me when I can buy it"),
    },
}

THREE_D_BLOCKS = {
    "mundo-3d/index.html": '''<section class="tramo env" data-reader-next="3d">
<span class="rot">03.01.27</span><h2 class="grande">El 3 de enero, aquí.</h2>
<p class="parr">Ese día el enlace se abre. Si quieres que te llegue el aviso, deja tu correo en OOLITA.</p>
<a class="fila" href="/?follow=3d#seguir-oolita" data-oolita-event="3d-follow-intent"><span class="n">→</span><span class="nom">Avísame cuando abra</span><span class="glo">Mundo 3D · sin descarga · sin cuenta</span></a>
</section>''',
    "en/3d-world/index.html": '''<section class="tramo env" data-reader-next="3d">
<span class="rot">03.01.27</span><h2 class="grande">On 3 January, here.</h2>
<p class="parr">That day the link opens. If you want the notice, leave your email with OOLITA.</p>
<a class="fila" href="/en/?follow=3d#follow-oolita" data-oolita-event="3d-follow-intent"><span class="n">→</span><span class="nom">Tell me when it opens</span><span class="glo">3D world · no download · no account</span></a>
</section>''',
}

SUNDAY_BLOCKS = {
    "domingos/index.html": '''<section class="tramo env" data-reader-next="sundays">
<span class="rot">03.01.27</span><h2 class="grande">El último domingo abre el mundo.</h2>
<p class="parr">La serie termina donde empieza el mundo 3D. Si quieres que te llegue el aviso de la apertura, deja tu correo en OOLITA.</p>
<a class="fila" href="/?follow=3d#seguir-oolita" data-oolita-event="sundays-follow-intent"><span class="n">→</span><span class="nom">Avísame el 3 de enero</span><span class="glo">El último domingo · la salida</span></a>
</section>''',
    "en/sundays/index.html": '''<section class="tramo env" data-reader-next="sundays">
<span class="rot">03.01.27</span><h2 class="grande">The last Sunday opens the world.</h2>
<p class="parr">The series ends where the 3D world begins. If you want the opening notice, leave your email with OOLITA.</p>
<a class="fila" href="/en/?follow=3d#follow-oolita" data-oolita-event="sundays-follow-intent"><span class="n">→</span><span class="nom">Tell me on 3 January</span><span class="glo">The last Sunday · the exit</span></a>
</section>''',
}

PREFILL = r'''<script id="oolita-follow-prefill">(function(){
var interest=new URLSearchParams(location.search).get('follow');
if(['book','3d','field','textile'].indexOf(interest)===-1)return;
var form=document.getElementById(document.documentElement.lang==='en'?'oolita-follow-en':'oolita-follow-es');
if(!form)return;
var input=form.querySelector('input[name="interest"][value="'+interest+'"]');
if(input)input.checked=true;
})();</script>'''


def read(rel: str) -> tuple[Path, str]:
    target = ROOT / rel
    if not target.is_file():
        raise SystemExit(f"Missing reader-path page: {rel}")
    return target, target.read_text(encoding="utf-8")


def visible(html: str) -> str:
    return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", " ", html))).strip()


def replace_link_href(rel: str, phrase: str, href: str) -> None:
    target, text = read(rel)
    found = 0

    def repl(match: re.Match[str]) -> str:
        nonlocal found
        body = match.group("body")
        if phrase not in visible(body):
            return match.group(0)
        found += 1
        start = match.group("start")
        if re.search(r'\bhref=["\'][^"\']*["\']', start, flags=re.I):
            start = re.sub(r'\bhref=["\'][^"\']*["\']', f'href="{href}"', start, count=1, flags=re.I)
        else:
            start = start[:-1] + f' href="{href}">'
        return start + body + "</a>"

    text = re.sub(
        r'(?P<start><a\b[^>]*>)(?P<body>[\s\S]*?)</a>',
        repl,
        text,
        flags=re.I,
    )
    if found != 1:
        raise SystemExit(f"Expected one link containing {phrase!r} in {rel}; found {found}")
    target.write_text(text, encoding="utf-8")


def replace_marked_section(rel: str, marker: str, block: str) -> None:
    target, text = read(rel)
    text = re.sub(
        rf'<section\b[^>]*data-reader-next=["\']{re.escape(marker)}["\'][^>]*>[\s\S]*?</section>\s*',
        "",
        text,
        flags=re.I,
    )
    footer = re.search(r"<footer\b", text, flags=re.I)
    if not footer:
        raise SystemExit(f"Footer anchor missing in {rel}")
    text = text[:footer.start()] + block + "\n" + text[footer.start():]
    target.write_text(text, encoding="utf-8")


def install_prefill(rel: str) -> None:
    target, text = read(rel)
    text = re.sub(r'<script\b[^>]*id=["\']oolita-follow-prefill["\'][^>]*>[\s\S]*?</script>\s*', "", text, flags=re.I)
    if "</body>" not in text:
        raise SystemExit(f"Missing </body> in {rel}")
    text = text.replace("</body>", PREFILL + "\n</body>", 1)
    target.write_text(text, encoding="utf-8")


for rel, spec in BOOK_PATHS.items():
    for phrase in spec["phrases"]:
        replace_link_href(rel, phrase, spec["follow"])

for rel, block in THREE_D_BLOCKS.items():
    replace_marked_section(rel, "3d", block)

for rel, block in SUNDAY_BLOCKS.items():
    replace_marked_section(rel, "sundays", block)

install_prefill("index.html")
install_prefill("en/index.html")


# Final-state checks.
for rel, spec in BOOK_PATHS.items():
    _, text = read(rel)
    if text.count(spec["follow"]) != 2:
        raise SystemExit(f"Book follow path count wrong in {rel}")
    for phrase in spec["phrases"]:
        if phrase not in visible(text):
            raise SystemExit(f"Book invitation missing in {rel}: {phrase}")

for rel in THREE_D_BLOCKS:
    _, text = read(rel)
    if text.count('data-reader-next="3d"') != 1 or text.count('data-oolita-event="3d-follow-intent"') != 1:
        raise SystemExit(f"3D onward path invariant failed in {rel}")

for rel in SUNDAY_BLOCKS:
    _, text = read(rel)
    if text.count('data-reader-next="sundays"') != 1 or text.count('data-oolita-event="sundays-follow-intent"') != 1:
        raise SystemExit(f"Sunday onward path invariant failed in {rel}")

for rel in ("index.html", "en/index.html"):
    _, text = read(rel)
    if text.count('id="oolita-follow-prefill"') != 1:
        raise SystemExit(f"Follow prefill invariant failed in {rel}")
    for value in ("book", "3d", "field", "textile"):
        if f'value="{value}"' not in text:
            raise SystemExit(f"Follow interest {value!r} missing in {rel}")

print("OOLITA reader paths installed and validated.")
