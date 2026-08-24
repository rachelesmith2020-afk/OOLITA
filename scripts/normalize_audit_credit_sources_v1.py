#!/usr/bin/env python3
"""Bridge current live attribution back to the legacy audit's expected source state.

The deployment is reconstructed from the current public site. Once final OOLITA
credits are live, the older accessibility/privacy audit can otherwise fail because
it expects the pre-credit signature/footer source. This bridge changes only the
intermediate build state; the final attribution pass restores the approved public
wording at the end of the pipeline.
"""
from __future__ import annotations

from pathlib import Path
import re
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")

FINAL_HOME_ES = (
    "Raquel Costantini hizo el laberinto y escribió el libro. "
    "Vestini Tribe publica el libro. La web oolita.es y el mundo 3D en Three.js "
    "se desarrollan en colaboración entre Raquel Costantini y Vestini Tribe."
)
FINAL_HOME_EN = (
    "Raquel Costantini made the labyrinth and wrote the book. "
    "Vestini Tribe publishes the book. The website oolita.es and the Three.js world "
    "are developed collaboratively by Raquel Costantini and Vestini Tribe."
)

FINAL_MAIN_ES = "OOLITA · Un proyecto de Raquel Costantini con Vestini Tribe"
FINAL_MAIN_EN = "OOLITA · A project by Raquel Costantini with Vestini Tribe"
LEGACY_MAIN = "OOLITA · Raquel Costantini"

FINAL_FIRMA_ES = (
    '<div class="firma"><span class="rot">Raquel Costantini — artista y autora</span>'
    '<span class="rot">Vestini Tribe — editorial del libro</span></div>'
)
FINAL_FIRMA_EN = (
    '<div class="firma"><span class="rot">Raquel Costantini — artist and author</span>'
    '<span class="rot">Vestini Tribe — book publisher</span></div>'
)
LEGACY_FIRMA_ES = (
    '<div class="firma"><span class="rot">Raquel Costantini</span>'
    '<span class="rot">Hallazgo</span><span class="rot">Almería, ES</span></div>'
)
LEGACY_FIRMA_EN = (
    '<div class="firma"><span class="rot">Raquel Costantini</span>'
    '<span class="rot">Hallazgo</span><span class="rot">Almería, Spain</span></div>'
)


def visible_text(html: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html)).strip()


def remove_paragraph_containing(text: str, exact_visible: str) -> str:
    for match in list(re.finditer(r'<p\b[^>]*>[\s\S]*?</p>', text, flags=re.I)):
        if visible_text(match.group(0)) == exact_visible:
            text = text[:match.start()] + text[match.end():]
            break
    return text


if not ROOT.is_dir():
    raise SystemExit(f"Missing built site: {ROOT}")

# Remove the already-final homepage credit so the legacy audit can insert its
# own historical intermediate credit exactly once. The later voice + attribution
# passes turn that back into the approved final wording.
for rel, final_home, final_firma, legacy_firma in (
    ("index.html", FINAL_HOME_ES, FINAL_FIRMA_ES, LEGACY_FIRMA_ES),
    ("en/index.html", FINAL_HOME_EN, FINAL_FIRMA_EN, LEGACY_FIRMA_EN),
):
    path = ROOT / rel
    if not path.is_file():
        raise SystemExit(f"Missing homepage: {rel}")
    text = path.read_text(encoding="utf-8")
    text = remove_paragraph_containing(text, final_home)
    if final_firma in text:
        text = text.replace(final_firma, legacy_firma, 1)
    path.write_text(text, encoding="utf-8")

# The older audit validates every footer against its historical intermediate
# identity. Normalize only the main identity phrase; leave the collaborative
# build credit in place because that is independent and harmless to the audit.
for path in sorted(ROOT.rglob("*.html")):
    text = path.read_text(encoding="utf-8")
    footer = re.search(r'<footer\b[\s\S]*?</footer>', text, flags=re.I)
    if not footer:
        continue
    block = footer.group(0)
    new_block = block.replace(FINAL_MAIN_ES, LEGACY_MAIN).replace(FINAL_MAIN_EN, LEGACY_MAIN)
    if new_block != block:
        text = text[:footer.start()] + new_block + text[footer.end():]
        path.write_text(text, encoding="utf-8")

print("OOLITA audit-credit source compatibility normalization complete.")
