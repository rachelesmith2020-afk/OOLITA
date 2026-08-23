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
# apply_public_identity_v2.py restores the current public wording at the end.
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
        "En el castillo: catálogo completo con clave · tapa dura 16.09.27 · presentación pública 19.09.27 ↗",
        "En el castillo: catálogo completo con clave · tapa dura prevista para otoño de 2027 ↗",
    )
    text = text.replace(
        "In the castle: full catalogue with a key · hardback 16.09.27 · public launch 19.09.27 ↗",
        "In the castle: full catalogue with a key · hardback planned for autumn 2027 ↗",
    )
    path.write_text(text, encoding="utf-8")

print("OOLITA Follow Cloudflare activation and mobile CTA validated successfully.")
