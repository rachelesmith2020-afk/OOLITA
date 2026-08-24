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
success_ui_patches = 0
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

    # A successful submit used to update a status line at the top of the form,
    # which can be outside the viewport when the visitor is at the submit button.
    # Make the confirmation unmistakable and bring it into view.
    old_success = (
        "if(s)s.textContent=lang==='es'?'Ya estás dentro · gracias por seguir OOLITA.':'You’re in · thank you for following OOLITA.';"
    )
    new_success = (
        "if(s){s.textContent=lang==='es'?'Gracias · ya estás dentro. Nos vemos pronto.':'Thanks · you’re in. See you soon.';"
        "s.setAttribute('tabindex','-1');s.style.opacity='1';s.style.textTransform='none';s.style.fontSize='1rem';"
        "s.style.borderTop='1.5px solid currentColor';s.style.borderBottom='1.5px solid currentColor';s.style.padding='1rem 0';"
        "s.focus({preventScroll:true});s.scrollIntoView({behavior:'smooth',block:'center'});}"
    )
    if old_success in text:
        success_ui_patches += text.count(old_success)
        text = text.replace(old_success, new_success)

    path.write_text(text, encoding="utf-8")

if success_ui_patches == 0:
    raise SystemExit("Follow success confirmation UI was not found in the rendered site")

print("OOLITA Follow Cloudflare activation, mobile CTA and visible success confirmation validated successfully.")
