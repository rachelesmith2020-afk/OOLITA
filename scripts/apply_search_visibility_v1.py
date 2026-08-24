#!/usr/bin/env python3
"""Run the final reader-facing deployment layers after search/identity normalization."""
from __future__ import annotations

from pathlib import Path
import re
import runpy
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
HERE = Path(__file__).resolve().parent


# A deployment rebuild starts from the current live origin. The later
# reader-facing pass may therefore already have converted English display dates
# to month-name forms. The public-identity layer inside the search core validates
# its canonical dotted intermediate forms, so restore only those display strings
# before running the core. The reader layer converts them back afterwards.
ENGLISH_DATE_NORMALISATION = (
    ("3 Jan 2027", "03.01.2027"),
    ("3 Jan 27", "03.01.27"),
    ("9 Aug 26", "09.08.26"),
    ("31 Jan 27", "31.01.27"),
    ("16 May 27", "16.05.27"),
    ("16 Sep 27", "16.09.27"),
    ("19 Sep 27", "19.09.27"),
    ("11 Apr 27", "11.04.27"),
)
for rel in ("en/index.html", "en/editions/book/index.html"):
    target = ROOT / rel
    if not target.is_file():
        continue
    text = target.read_text(encoding="utf-8")

    # The mobile 2027 repair makes the year an inline span. On the next
    # deployment, the site is reconstructed from that already-enhanced live
    # homepage, so plain-string normalization alone cannot see "3 Jan 2027".
    # Collapse only this known display wrapper back to the canonical
    # intermediate form; the mobile layer below restores it after validation.
    if rel == "en/index.html":
        text = re.sub(
            r'3\s+Jan\s*<span\b[^>]*class=["\'][^"\']*\bmobile-2027-clear\b[^"\']*["\'][^>]*>\s*2027\s*</span>',
            "03.01.2027",
            text,
            flags=re.I,
        )

    for reader_form, canonical_form in ENGLISH_DATE_NORMALISATION:
        text = text.replace(reader_form, canonical_form)
    target.write_text(text, encoding="utf-8")


def run_layer(filename: str) -> None:
    script = HERE / filename
    if not script.is_file():
        raise SystemExit(f"Missing deployment layer: {script}")
    old_argv = sys.argv[:]
    sys.argv = [str(script), str(ROOT)]
    try:
        runpy.run_path(str(script), run_name="__main__")
    finally:
        sys.argv = old_argv


run_layer("apply_search_visibility_core_v1.py")
# Apply the agreed reader-assessment priorities after search/identity
# normalization so the final reader-facing copy wins over canonical
# intermediate forms used by earlier validation layers.
run_layer("apply_reader_assessment_v1.py")
run_layer("apply_book_excerpt_v1.py")
run_layer("apply_sunday_archive_v1.py")
run_layer("apply_seo_followup_v1.py")
run_layer("apply_menu_hierarchy_v1.py")
# The reconstructed live homepage may carry inline links inside otherwise
# unchanged source paragraphs. Normalize those visible-text-equivalent sources
# for compatibility diagnostics, but do not run the obsolete literal-string
# soft-marketing transformer. Production rebuilds mirror a homepage that already
# contains its final reader-facing marketing layer, and later editorial passes
# have legitimately superseded several of the transformer's source strings.
run_layer("normalize_soft_marketing_sources_v1.py")

# Growth validation temporarily restores an institutional definition paragraph
# that the final live homepage intentionally omits. This single cleanup is the
# only still-relevant effect of the retired soft-marketing layer; remove it
# directly without re-running that layer over newer editorial copy.
for rel, definition in (
    ("index.html", '<p class="parr definicion">OOLITA es un proyecto editorial y de trabajo de campo arraigado en Los Escullos, Cabo de Gata.</p>'),
    ("en/index.html", '<p class="parr definicion">OOLITA is a place-based publishing and fieldwork project rooted in Los Escullos, Cabo de Gata.</p>'),
):
    page = ROOT / rel
    if not page.is_file():
        raise SystemExit(f"Missing homepage while removing legacy definition: {rel}")
    text = page.read_text(encoding="utf-8")
    if definition in text:
        page.write_text(text.replace(definition, ""), encoding="utf-8")
        print(f"removed legacy taxonomy-first definition from {rel}")

print("OOLITA final soft-marketing state preserved; legacy transformer skipped.")
run_layer("publish_sunday03_and_3d_preview_v1.py")
run_layer("apply_engagement_depth_v1.py")
# Keep the external research trail attached to the About material section.
run_layer("apply_arena_archive_link_v1.py")
# Public provenance/practice credential: keep it on About and Labyrinth only,
# with a live external link to the Veriditas facilitator directory.
run_layer("apply_veriditas_facilitator_v1.py")
# Reader-facing visual layers.
run_layer("apply_art_restage_v1.py")
run_layer("apply_mobile_english_2027_fix_v1.py")
run_layer("apply_visual_spacing_cleanup_v1.py")
run_layer("apply_mobile_footer_cleanup_v1.py")
run_layer("apply_home_overlay_reset_v1.py")
# Always finish with the two idempotent quality layers after every other
# transformation. This prevents mirrored-origin CSS or a later visual pass from
# reintroducing the PIEDRA/STONE collision or low-contrast secondary text.
run_layer("apply_visual_spacing_cleanup_v1.py")
run_layer("apply_contrast_accessibility_v1.py")
# Final editorial safeguard. The book is the voice reference; this removes
# generic promotional diction after every other content layer has finished.
run_layer("apply_voice_audit_v1.py")
run_layer("apply_voice_audit_spanish_editions_v1.py")
# Final credit safeguard: distinguish artistic authorship, book publishing and
# the collaborative website/Three.js build after every other content layer.
run_layer("apply_attribution_consistency_v2.py")
# Final onward paths from the book, labyrinth, 3D world and Sundays into the OOLITA list.
run_layer("apply_reader_paths_v1.py")
# Final narrow SEO/editorial pass for the three pages still below standard.
run_layer("apply_three_page_seo_v1.py")
# Absolute final gate: retire the former Wednesday/Reels route after every SEO,
# archive, menu and visual pass so nothing downstream can reintroduce it.
run_layer("finalize_reels_retirement_v1.py")
# Absolute final Editions copy gate: keep the approved physical-edition order
# explicit on the English page, with the Hallazgo hardback immediately after
# the first OOLITA book and T-shirt.
run_layer("normalize_editions_hallazgo_hardback_v1.py")

# A later reader-facing transform can recreate the old homepage sentence
# "It stands on a fossil dune." Normalize that exact location claim before the
# final factual gate. Using "is on land beside" also avoids the San Felipe-only
# restoration rule from mistaking the labyrinth for the battery.
en_home = ROOT / "en/index.html"
if not en_home.is_file():
    raise SystemExit("Missing English homepage before final fossil-dune gate")
en_home_text = en_home.read_text(encoding="utf-8")
en_home_text = en_home_text.replace(
    "It stands on a fossil dune.",
    "It is on land beside the fossil dunes.",
)
en_home.write_text(en_home_text, encoding="utf-8")

# Absolute final factual/SEO gate: the labyrinth is on land beside the fossil
# dunes; the nearby Batería de San Felipe is allowed to stand on a fossil dune.
# The same pass uses "loose stones", refreshes changed sitemap routes and rejects
# factual/wording stragglers plus broken internal hrefs.
run_layer("normalize_labyrinth_fossil_dunes_v1.py")
# The production mirror can retain the retired Canva Hallazgo host outside href
# attributes (metadata/inline data). Scrub it before the final Hallazgo gate so
# the deployed bundle contains only first-party catalogue routes.
run_layer("preclean_hallazgo_legacy_urls_v1.py")
# Final Hallazgo access copy runs after the geological normalizer because this
# sentence describes the approved 3D castle replica standing on the fossil dune.
# It validates first-party hrefs, Editions SEO alternates/canonicals, removes the
# former keyed-castle wording and refreshes the relevant sitemap routes.
run_layer("normalize_hallazgo_3d_castle_access_v1.py")

# Absolute post-transform SEO/copy gate. The geological normalizer can lengthen
# the Spanish labyrinth description by replacing the former singular dune claim;
# keep the final description concise and factual after every reader-facing pass.
LABERINTO_DESCRIPTION = (
    "Laberinto OOLITA en Los Escullos, Cabo de Gata: un camino de piedras sueltas "
    "en terreno junto a las dunas fósiles, sin entrada ni reserva."
)
laberinto = ROOT / "laberinto/index.html"
if not laberinto.is_file():
    raise SystemExit("Missing Spanish labyrinth page at final SEO gate")
lab_text = laberinto.read_text(encoding="utf-8")


def replace_meta_content(html: str, *, attr: str, value: str, content: str) -> str:
    tag_pattern = re.compile(r'<meta\b[^>]*>', re.I)
    matched = 0

    def patch(match: re.Match[str]) -> str:
        nonlocal matched
        tag = match.group(0)
        if not re.search(rf'\b{re.escape(attr)}=["\']{re.escape(value)}["\']', tag, flags=re.I):
            return tag
        matched += 1
        if not re.search(r'\bcontent=["\'][^"\']*["\']', tag, flags=re.I):
            raise SystemExit(f"Meta {attr}={value} has no content attribute")
        return re.sub(
            r'\bcontent=(["\'])[^"\']*\1',
            lambda content_match: f'content={content_match.group(1)}{content}{content_match.group(1)}',
            tag,
            count=1,
            flags=re.I,
        )

    result = tag_pattern.sub(patch, html)
    if matched != 1:
        raise SystemExit(f"Expected exactly one meta {attr}={value}; found {matched}")
    return result


lab_text = replace_meta_content(
    lab_text, attr="name", value="description", content=LABERINTO_DESCRIPTION
)
lab_text = replace_meta_content(
    lab_text, attr="property", value="og:description", content=LABERINTO_DESCRIPTION
)
lab_text = replace_meta_content(
    lab_text, attr="name", value="twitter:description", content=LABERINTO_DESCRIPTION
)
laberinto.write_text(lab_text, encoding="utf-8")
if len(LABERINTO_DESCRIPTION) > 160:
    raise SystemExit("Final Spanish labyrinth meta description exceeds 160 characters")

# Final user-approved Cabo opening must survive every subsequent editorial and
# factual pass. This is intentionally checked at the very end of the content
# pipeline, after voice normalization and fossil-dune corrections.
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
CABO_OLD = {
    "cabo-de-gata/index.html": (
        "la piedra, el viento, el agua, las aves, los materiales y la gente que trabaja aquí.",
        "a través del arte, la observación, los materiales y ediciones hechas con cuidado.",
    ),
    "en/cabo-de-gata/index.html": (
        "stone, wind, water, birds, materials and the people who work here.",
        "through art, observation, materials and carefully made editions.",
    ),
}
for rel, final_copy in CABO_FINAL.items():
    cabo_page = ROOT / rel
    if not cabo_page.is_file():
        raise SystemExit(f"Missing Cabo de Gata page at final gate: {rel}")
    cabo_text = cabo_page.read_text(encoding="utf-8")
    if cabo_text.count(final_copy) != 1:
        raise SystemExit(f"Approved Cabo de Gata opening missing or duplicated after final transforms: {rel}")
    for stale in CABO_OLD[rel]:
        if stale in cabo_text:
            raise SystemExit(f"Superseded Cabo de Gata wording survived final transforms: {rel}")

print(
    "Final SEO/copy gate passed: labyrinth description <=160; Cabo flora + "
    "live-and-work wording survived all transforms with no opening-copy stragglers."
)

# Deployment trigger: mobile stone field grid specificity fix, 2026-08-23.
# Deployment trigger: final OOLITA book-voice audit, 2026-08-24.
# Deployment trigger: final Spanish Editions voice pass, 2026-08-24.
# Deployment trigger: attribution consistency, 2026-08-24.
# Deployment trigger: direct reader paths including the labyrinth, 2026-08-24.
# Deployment trigger: Are.na process archive link, 2026-08-24.
# Deployment trigger: preserve final homepage copy across mirror rebuilds, 2026-08-24.
# Deployment trigger: final no-straggler Reels retirement gate, 2026-08-24.
# Deployment trigger: three-page SEO/content polish, 2026-08-24.
# Deployment trigger: actual hreflang link validator fix, 2026-08-24.
# Deployment trigger: labyrinth beside-fossil-dunes factual correction, 2026-08-24.
# Deployment trigger: Hallazgo hardback Editions sequence, 2026-08-24.
# Deployment trigger: San Felipe fossil-dune exception + loose-stones wording, 2026-08-24.
# Deployment trigger: location-only fossil-dune validator fix, 2026-08-24.
# Deployment trigger: rerun corrected location validator in production, 2026-08-24.
# Deployment trigger: pre-normalize regenerated English homepage location claim, 2026-08-24.
# Deployment trigger: Hallazgo 3D-castle keypad explanation, 2026-08-24.
# Deployment trigger: retire residual Canva Hallazgo host before final gate, 2026-08-24.
