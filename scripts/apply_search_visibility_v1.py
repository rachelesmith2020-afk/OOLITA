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
# Final content pass: strengthen invitation and conversion while preserving the
# restrained artistic voice established by the reader-assessment layers.
run_layer("apply_soft_marketing_v1.py")
run_layer("publish_sunday03_and_3d_preview_v1.py")
run_layer("apply_engagement_depth_v1.py")
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

# Deployment trigger: mobile stone field grid specificity fix, 2026-08-23.
