#!/usr/bin/env python3
"""Activate and finish OOLITA's first-party Cloudflare Follow form."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
subprocess.run([sys.executable, "scripts/apply_cloudflare_follow_v1.py", str(ROOT)], check=True)
subprocess.run([sys.executable, "scripts/apply_follow_mobile_finish.py", str(ROOT)], check=True)

# The deployment mirror now starts from a live origin on which later final
# passes have already published newer identity/date wording. Normalize only
# the intermediate source strings expected by the older strict transformers;
# apply_release_calendar_v1.py, apply_public_identity_v2.py and the reader pass
# restore the current public wording and English display dates later.
for path in ROOT.rglob("*.html"):
    text = path.read_text(encoding="utf-8")
    text = text.replace(
        "OOLITA · Un proyecto de Vestini Tribe · Raquel Costantini, artista y autora",
        "OOLITA · Raquel Costantini",
    )
    text = text.replace(
        "OOLITA · A Vestini Tribe project · Raquel Costantini, artist and author",
        "OOLITA · Raquel Costantini",
    )
    text = text.replace(
        "Castillo virtual · entrada libre · abre 16.05.27 · 19:00 CEST ↗",
        "Obra de Raquel Costantini ↗",
    )
    text = text.replace(
        "Virtual castle · free to enter · opens 16.05.27 · 19:00 CEST ↗",
        "Work by Raquel Costantini ↗",
    )
    text = text.replace(
        "Virtual castle · free to enter · opens 16 May 27 · 19:00 CEST ↗",
        "Work by Raquel Costantini ↗",
    )
    text = text.replace(
        "En el castillo: catálogo completo con clave · tapa dura 16.09.27 · presentación pública 19.09.27 ↗",
        "En el castillo: catálogo completo con clave · tapa dura prevista para otoño de 2027 ↗",
    )
    text = text.replace(
        "In the castle: full catalogue with a key · hardback 16.09.27 · public launch 19.09.27 ↗",
        "In the castle: full catalogue with a key · hardback planned for autumn 2027 ↗",
    )
    text = text.replace(
        "In the castle: full catalogue with a key · hardback 16 Sep 27 · public launch 19 Sep 27 ↗",
        "In the castle: full catalogue with a key · hardback planned for autumn 2027 ↗",
    )
    path.write_text(text, encoding="utf-8")

# The reader-assessment pass deliberately humanises visible English dates on
# these two pages. Reverse that presentation only during reconstruction because
# the older identity validator still checks its dotted intermediate values.
# apply_reader_assessment_v1.py restores the human-readable forms at the end.
for rel in ("en/index.html", "en/editions/book/index.html"):
    path = ROOT / rel
    if not path.is_file():
        continue
    text = path.read_text(encoding="utf-8")
    for human, dotted in (
        ("3 Jan 2027", "03.01.2027"),
        ("3 Jan 27", "03.01.27"),
        ("9 Aug 26", "09.08.26"),
        ("31 Jan 27", "31.01.27"),
        ("16 May 27", "16.05.27"),
        ("16 Sep 27", "16.09.27"),
        ("19 Sep 27", "19.09.27"),
        ("11 Apr 27", "11.04.27"),
    ):
        text = text.replace(human, dotted)
    path.write_text(text, encoding="utf-8")

print("OOLITA Follow Cloudflare activation and mobile CTA validated successfully.")
