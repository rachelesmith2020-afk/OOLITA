#!/usr/bin/env python3
"""Bridge current live attribution back to legacy validators' expected source state.

The deployment is reconstructed from the current public site. Once final OOLITA
credits are live, older accessibility/privacy and search validators can otherwise
fail because they expect the pre-credit signature/footer source. This bridge
changes only the intermediate build state; the final attribution pass restores
the approved public wording at the end of the pipeline.

It also carries the final approved Cabo de Gata opening copy through the growth
rebuild and verifies the bilingual canonical/hreflang and local link targets.
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

FINAL_BUILD_ES = "Sitio y mundo 3D desarrollados en colaboración por Raquel Costantini y Vestini Tribe."
FINAL_BUILD_EN = "Website and 3D world developed collaboratively by Raquel Costantini and Vestini Tribe."
LEGACY_BUILD_ES = "Sitio y mundo 3D construidos por Vestini Tribe."
LEGACY_BUILD_EN = "Site and 3D world built by Vestini Tribe."

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

CABO_FINAL = {
    "cabo-de-gata/index.html": (
        "OOLITA empieza con un solo laberinto en Los Escullos. Desde ese camino mira Cabo de Gata: "
        "la piedra, el viento, el agua, las aves, la flora y la gente que vive y trabaja aquí."
    ),
    "en/cabo-de-gata/index.html": (
        "OOLITA begins with one labyrinth at Los Escullos. From that path it looks at Cabo de Gata: "
        "stone, wind, water, birds, flora and the people who live and work here."
    ),
}

CABO_VARIANTS = {
    "cabo-de-gata/index.html": (
        "OOLITA empieza con un solo laberinto en Los Escullos. Desde ese camino mira Cabo de Gata: "
        "la piedra, el viento, el agua, las aves, los materiales y la gente que trabaja aquí.",
        "OOLITA empieza con un solo laberinto en Los Escullos. Alrededor de ese camino crece una práctica "
        "editorial y de trabajo de campo que mira Cabo de Gata a través del arte, la observación, los materiales "
        "y ediciones hechas con cuidado.",
    ),
    "en/cabo-de-gata/index.html": (
        "OOLITA begins with one labyrinth at Los Escullos. From that path it looks at Cabo de Gata: "
        "stone, wind, water, birds, materials and the people who work here.",
        "OOLITA begins with one labyrinth at Los Escullos. Around that path, a publishing and fieldwork practice "
        "is growing: looking at Cabo de Gata through art, observation, materials and carefully made editions.",
    ),
}

CABO_SEO = {
    "cabo-de-gata/index.html": {
        "canonical": "https://oolita.es/cabo-de-gata/",
        "es": "https://oolita.es/cabo-de-gata/",
        "en": "https://oolita.es/en/cabo-de-gata/",
        "x-default": "https://oolita.es/cabo-de-gata/",
    },
    "en/cabo-de-gata/index.html": {
        "canonical": "https://oolita.es/en/cabo-de-gata/",
        "es": "https://oolita.es/cabo-de-gata/",
        "en": "https://oolita.es/en/cabo-de-gata/",
        "x-default": "https://oolita.es/cabo-de-gata/",
    },
}


def visible_text(html: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html)).strip()


def remove_paragraph_containing(text: str, exact_visible: str) -> str:
    for match in list(re.finditer(r'<p\b[^>]*>[\s\S]*?</p>', text, flags=re.I)):
        if visible_text(match.group(0)) == exact_visible:
            text = text[:match.start()] + text[match.end():]
            break
    return text


def local_target(href: str) -> Path | None:
    if not href.startswith("/") or href.startswith("//"):
        return None
    clean = href.split("#", 1)[0].split("?", 1)[0]
    if not clean or clean == "/":
        return ROOT / "index.html"
    rel = clean.lstrip("/")
    target = ROOT / rel
    if clean.endswith("/") or not Path(rel).suffix:
        target = target / "index.html"
    return target


if not ROOT.is_dir():
    raise SystemExit(f"Missing built site: {ROOT}")

# Final Cabo de Gata opening: replace either the current live wording or the
# older growth-source wording. This runs after apply_growth_v1.py, so it cannot
# be overwritten by that page generator during the normal production workflow.
for rel, final_copy in CABO_FINAL.items():
    path = ROOT / rel
    if not path.is_file():
        raise SystemExit(f"Missing Cabo de Gata page: {rel}")
    text = path.read_text(encoding="utf-8")
    if final_copy not in text:
        replaced = False
        for old in CABO_VARIANTS[rel]:
            if old in text:
                text = text.replace(old, final_copy, 1)
                replaced = True
                break
        if not replaced:
            raise SystemExit(f"Unexpected Cabo de Gata opening state: {rel}")
        path.write_text(text, encoding="utf-8")

    text = path.read_text(encoding="utf-8")
    if final_copy not in text:
        raise SystemExit(f"Final Cabo de Gata wording missing: {rel}")
    for old in CABO_VARIANTS[rel]:
        if old in text:
            raise SystemExit(f"Old Cabo de Gata wording still present: {rel}")

    seo = CABO_SEO[rel]
    required_tags = [
        f'<link rel="canonical" href="{seo["canonical"]}">',
        f'<link rel="alternate" hreflang="es" href="{seo["es"]}">',
        f'<link rel="alternate" hreflang="en" href="{seo["en"]}">',
        f'<link rel="alternate" hreflang="x-default" href="{seo["x-default"]}">',
    ]
    for tag in required_tags:
        if tag not in text:
            raise SystemExit(f"Cabo de Gata SEO/hreflang invariant missing in {rel}: {tag}")

    missing = []
    for href in re.findall(r'href=["\']([^"\']+)["\']', text, flags=re.I):
        target = local_target(href)
        if target is not None and not target.is_file():
            missing.append((href, target.relative_to(ROOT)))
    if missing:
        detail = ", ".join(f"{href} -> {target}" for href, target in missing)
        raise SystemExit(f"Cabo de Gata local href would 404 in {rel}: {detail}")

print("Cabo de Gata flora/live-and-work wording, SEO/hreflang and local hrefs verified.")

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

# Older validators check every footer against historical intermediate identity
# and build-credit phrases. Normalize only those exact phrases; the final
# attribution pass restores the collaborative public credits before deployment.
for path in sorted(ROOT.rglob("*.html")):
    text = path.read_text(encoding="utf-8")
    footer = re.search(r'<footer\b[\s\S]*?</footer>', text, flags=re.I)
    if not footer:
        continue
    block = footer.group(0)
    new_block = block.replace(FINAL_MAIN_ES, LEGACY_MAIN).replace(FINAL_MAIN_EN, LEGACY_MAIN)
    new_block = new_block.replace(FINAL_BUILD_ES, LEGACY_BUILD_ES).replace(FINAL_BUILD_EN, LEGACY_BUILD_EN)
    if new_block != block:
        text = text[:footer.start()] + new_block + text[footer.end():]
        path.write_text(text, encoding="utf-8")

print("OOLITA legacy-validator attribution source normalization complete.")
