#!/usr/bin/env python3
"""Final factual/SEO gate for OOLITA's labyrinth and fossil-dune wording.

The current v1 gate owns the comprehensive corrections and straggler checks:
- the labyrinth is on land beside the fossil dunes;
- the named Batería de San Felipe may stand on a fossil dune;
- calcarenite shorthand is removed in favour of loose stones;
- malformed singular/plural variants and wrong location claims fail closed;
- dedicated geology explainers remain free to discuss fossil dunes geologically.

This v2 entry point runs that current gate unchanged, then adds explicit
principal-page assertions and canonicalises the single homepage CTA linking the
three-materials section to the 3D-world explainer. The CTA normalisation is
idempotent and prevents duplicate rows inherited from a previously mirrored
production homepage from accumulating across deployments.
"""
from pathlib import Path
import re
import runpy
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
HERE = Path(__file__).resolve().parent
v1 = HERE / "normalize_labyrinth_fossil_dunes_v1.py"

if not ROOT.is_dir():
    raise SystemExit(f"Missing built site: {ROOT}")
if not v1.is_file():
    raise SystemExit(f"Missing v1 fossil-dune gate: {v1}")

# Preserve the caller's site argument while executing the maintained v1 gate as
# its own __main__ program. No source rewriting: the actual current validator is
# what is tested and deployed.
original_argv = sys.argv[:]
try:
    sys.argv = [str(v1), str(ROOT)]
    runpy.run_path(str(v1), run_name="__main__")
finally:
    sys.argv = original_argv

# Canonicalise the 3D-material CTA on both homepages. Older deployments mirrored
# the already-published homepage and could carry several identical copies forward.
# Match the row by its route and exact visible span labels, remove every copy,
# then put back one canonical row at the first copy's original position.
for rel, href, label, gloss in (
    (
        "index.html",
        "/mundo-3d/",
        "Por qué está hecho en código",
        "Three.js · el navegador como material",
    ),
    (
        "en/index.html",
        "/en/3d-world/",
        "Why it is built in code",
        "Three.js · the browser as material",
    ),
):
    path = ROOT / rel
    if not path.is_file():
        raise SystemExit(f"Missing homepage while normalising 3D CTA: {rel}")
    text = path.read_text(encoding="utf-8")
    pattern = re.compile(
        r'<a\b(?=[^>]*\bhref=["\']'
        + re.escape(href)
        + r'["\'])[^>]*>\s*'
        + r'<span\b[^>]*class=["\']n["\'][^>]*>\s*→\s*</span>\s*'
        + r'<span\b[^>]*class=["\']nom["\'][^>]*>\s*'
        + re.escape(label)
        + r'\s*</span>\s*'
        + r'<span\b[^>]*class=["\']glo["\'][^>]*>\s*'
        + re.escape(gloss)
        + r'\s*</span>\s*</a>',
        flags=re.I,
    )
    matches = list(pattern.finditer(text))
    if not matches:
        raise SystemExit(f"3D-material homepage CTA missing from {rel}")

    first_start = matches[0].start()
    canonical = (
        f'<a class="fila" data-oolita-event="home-3d-world-material" href="{href}">'
        f'<span class="n">→</span><span class="nom">{label}</span>'
        f'<span class="glo">{gloss}</span></a>'
    )
    cleaned = pattern.sub("", text)
    cleaned = cleaned[:first_start] + canonical + cleaned[first_start:]

    if len(pattern.findall(cleaned)) != 1:
        raise SystemExit(f"3D-material homepage CTA did not normalise to one row in {rel}")
    if cleaned.count('data-oolita-event="home-3d-world-material"') != 1:
        raise SystemExit(f"3D-material homepage event marker is not unique in {rel}")

    path.write_text(cleaned, encoding="utf-8")
    print(f"Homepage 3D CTA normalised in {rel}: {len(matches)} -> 1")

# Principal-page assertions remain explicit after the complete v1 gate.
for rel, phrase in (
    ("en/index.html", "beside the fossil dunes"),
    ("en/labyrinth/index.html", "beside the fossil dunes"),
    ("index.html", "junto a las dunas fósiles"),
    ("laberinto/index.html", "junto a las dunas fósiles"),
):
    path = ROOT / rel
    if not path.is_file():
        raise SystemExit(f"Missing principal location page: {rel}")
    text = path.read_text(encoding="utf-8").lower()
    if phrase not in text:
        raise SystemExit(f"Approved labyrinth location wording missing from {rel}: {phrase}")

print("OOLITA fossil-dunes v2 final gate passed.")
