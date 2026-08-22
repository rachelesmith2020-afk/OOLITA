#!/usr/bin/env python3
"""Compact the Follow OOLITA mobile layout and make the submit action explicit."""
from pathlib import Path
import re
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")

STYLE = r'''<style id="oolita-follow-mobile-finish">
.oolita-follow .follow-submit{margin-top:.2rem}
@media(max-width:760px){
 #seguir-oolita,#follow-oolita{padding-top:2.7rem;padding-bottom:3.2rem}
 #seguir-oolita .oolita-follow-grid,#follow-oolita .oolita-follow-grid{gap:1.35rem}
 #seguir-oolita .oolita-follow-intro .grande,#follow-oolita .oolita-follow-intro .grande{margin:.3rem 0 .7rem;line-height:.94}
 #seguir-oolita .oolita-follow-intro .glosa,#follow-oolita .oolita-follow-intro .glosa{line-height:1.38}
 .oolita-follow{padding-top:.72rem}
 .oolita-follow .follow-status{margin:0 0 1rem;font-size:.72rem}
 .oolita-follow .follow-field-label{margin-bottom:.25rem;font-size:.72rem}
 .oolita-follow input[type="email"]{min-height:2.9rem;padding:.1rem 0 .38rem;font-size:1.55rem}
 .oolita-follow .follow-interests{margin:1.35rem 0 1.15rem}
 .oolita-follow .follow-interests legend{margin-bottom:.6rem;font-size:.72rem}
 .oolita-follow .follow-chip-set{gap:.4rem}
 .oolita-follow .follow-chip{font-size:.86rem;padding:.42rem .62rem;gap:.45rem}
 .oolita-follow .follow-chip input{width:.78rem;height:.78rem}
 .oolita-follow .follow-consent{grid-template-columns:1rem 1fr;gap:.65rem;margin-bottom:.8rem;font-size:.84rem;line-height:1.34}
 .oolita-follow .follow-consent input{width:1rem;height:1rem}
 .oolita-follow .follow-submit{grid-template-columns:auto 1fr;min-height:3.65rem;padding:.72rem .82rem;margin-top:0}
 .oolita-follow .follow-submit .follow-name{font-size:1rem}
 .oolita-follow .follow-submit .follow-note{grid-column:2;text-align:left;margin-top:-.35rem;font-size:.66rem}
 .oolita-follow .follow-privacy{margin-top:1rem;padding-top:.8rem;font-size:.7rem}
}
</style>'''

for rel, old_name, new_name in [
    ("index.html", "Seguir OOLITA", "Suscribirme"),
    ("en/index.html", "Follow OOLITA", "Subscribe"),
]:
    p = ROOT / rel
    if not p.is_file():
        raise SystemExit(f"Missing page: {rel}")
    s = p.read_text(encoding="utf-8")
    if 'data-oolita-follow="cloudflare"' not in s:
        raise SystemExit(f"Follow form missing in {rel}")

    old = f'<span class="follow-name">{old_name}</span>'
    new = f'<span class="follow-name">{new_name}</span>'
    if old in s:
        s = s.replace(old, new, 1)
    elif new not in s:
        raise SystemExit(f"Submit label missing in {rel}")

    if 'id="oolita-follow-mobile-finish"' in s:
        s = re.sub(r'<style id="oolita-follow-mobile-finish">[\s\S]*?</style>', STYLE, s, count=1)
    else:
        marker = '</head>'
        if marker not in s:
            raise SystemExit(f"Missing </head> in {rel}")
        s = s.replace(marker, STYLE + '\n' + marker, 1)

    p.write_text(s, encoding="utf-8")

for rel, label in [("index.html", "Suscribirme"), ("en/index.html", "Subscribe")]:
    s = (ROOT / rel).read_text(encoding="utf-8")
    required = [
        'id="oolita-follow-mobile-finish"',
        'class="follow-submit"',
        f'<span class="follow-name">{label}</span>',
        'name="consent"',
        'action="/api/subscribe"',
    ]
    for needle in required:
        if needle not in s:
            raise SystemExit(f"Mobile Follow invariant missing in {rel}: {needle}")

print("OOLITA Follow mobile CTA finish validated successfully.")
