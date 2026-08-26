#!/usr/bin/env python3
"""Apply and validate OOLITA reader-facing final consistency fixes.

This final consistency pass applies the reviewed rhetorical voice cleanup, then keeps
the published Sunday archive, Hallazgo work count, current book specification, and
Sunday 03 geology wording aligned across Spanish and English.
"""
from __future__ import annotations

import html as html_lib
from pathlib import Path
import re
import shutil
import subprocess
import sys


ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")

# Keep the rhetorical contrast cleanup in the reconstruction-safe consistency layer.
# Native-English editing runs later in the workflow, after all legacy migrations and
# validators have completed, so it cannot disturb their expected intermediate copy.
import apply_voice_contrast_v1  # noqa: E402,F401

# Reuse only the already-reviewed detailed archive row renderer. Do not call its
# broad archive patcher: Sunday 03 is already linked in the compact archive, so a
# generic href match can select that correct top tile instead of the stale lower row.
import apply_engagement_depth_v1 as engagement  # noqa: E402


def read(rel: str) -> tuple[Path, str]:
    path = ROOT / rel
    if not path.is_file():
        raise SystemExit(f"Missing consistency page: {rel}")
    return path, path.read_text(encoding="utf-8")


def replace_state(rel: str, old: str, new: str) -> None:
    path, text = read(rel)
    if old in text:
        path.write_text(text.replace(old, new), encoding="utf-8")
        return
    if new in text:
        return
    raise SystemExit(f"Neither stale nor corrected copy found in {rel}: {old!r}")


def replace_if_present(rel: str, old: str, new: str) -> None:
    path, text = read(rel)
    if old in text:
        path.write_text(text.replace(old, new), encoding="utf-8")


def visible_text(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", text)).strip()


def correct_english_book_page_count() -> None:
    """Keep the visible English specification row aligned with the 48-page book."""
    path, text = read("en/editions/book/index.html")
    visible = visible_text(text)
    if re.search(r"\bPages\s+48\b", visible, flags=re.I):
        return
    if not re.search(r"\bPages\s+44\b", visible, flags=re.I):
        raise SystemExit("English book page count is neither visible as 44 nor 48")

    match = re.search(r"(Pages[\s\S]{0,300}?)(?<!\d)44(?!\d)", text, flags=re.I)
    if not match:
        raise SystemExit("Could not locate the stale English book specification value 44")
    start = match.start(0) + len(match.group(1))
    text = text[:start] + "48" + text[start + 2:]
    path.write_text(text, encoding="utf-8")

    corrected = visible_text(text)
    if not re.search(r"\bPages\s+48\b", corrected, flags=re.I):
        raise SystemExit("English book specification did not resolve to Pages 48")


def matching_div_end(text: str, start: int) -> int:
    token_re = re.compile(r'</?div\b[^>]*>', flags=re.I)
    depth = 0
    for match in token_re.finditer(text, start):
        token = match.group(0)
        if token.lower().startswith("</div"):
            depth -= 1
            if depth == 0:
                return match.end()
        else:
            depth += 1
    raise SystemExit("Unclosed <div> while locating Sunday archive row")


def pending_sunday03_blocks(text: str) -> list[tuple[int, int]]:
    starts: list[tuple[int, int]] = []
    start_re = re.compile(r'<div\b[^>]*class=["\'][^"\']*\bfila\b[^"\']*\bespera\b[^"\']*["\'][^>]*>', flags=re.I)
    for match in start_re.finditer(text):
        end = matching_div_end(text, match.start())
        block = text[match.start():end]
        if re.search(r'<time\b[^>]*datetime=["\']2026-08-23["\']', block, flags=re.I):
            starts.append((match.start(), end))
    return starts


def publish_detailed_sunday03(rel: str, language: str) -> None:
    path, text = read(rel)
    blocks = pending_sunday03_blocks(text)
    if blocks:
        if len(blocks) != 1:
            raise SystemExit(f"Expected one pending Sunday 03 detailed row in {rel}, found {len(blocks)}")
        start, end = blocks[0]
        row = engagement.archive_row(3, language)
        text = text[:start] + row + text[end:]
        path.write_text(text, encoding="utf-8")
        return

    expected_route = "/en/sundays/03-the-memory-of-the-sea/" if language == "en" else "/domingos/03-la-memoria-del-mar/"
    if 'data-sunday-archive-row="3"' in text and f'href="{expected_route}"' in text:
        return
    raise SystemExit(f"Could not locate pending or published detailed Sunday 03 row in {rel}")


for rel in ("carteles/index.html", "en/posters/index.html"):
    replace_if_present(rel,"Hallazgo reúne 42 obras, registradas de H001 a H044.","Hallazgo reúne 44 obras, registradas de H001 a H044.")
    replace_if_present(rel,"Hallazgo brings together 42 works, registered H001 to H044.","Hallazgo brings together 44 works, registered H001 to H044.")

for rel in ("domingos/03-la-memoria-del-mar/index.html","en/sundays/03-the-memory-of-the-sea/index.html"):
    replace_state(rel,"Cada grano se redondeaba hacia dentro, capa sobre capa, hasta volverse una esfera diminuta.","Alrededor de cada grano crecía una capa tras otra, hasta volverlo una esfera diminuta.")
    replace_state(rel,"Each grain rounded inward, layer upon layer, until it became a tiny sphere.","Layer upon layer grew around each grain until it became a tiny sphere.")

correct_english_book_page_count()
publish_detailed_sunday03("domingos/index.html", "es")
publish_detailed_sunday03("en/sundays/index.html", "en")

# Historic poster/archive copy is allowed to preserve an earlier page-count state.
# The canonical 48-page specification is enforced only on the current book pages.
stale_strings = (
    "Hallazgo reúne 42 obras, registradas de H001 a H044.",
    "Hallazgo brings together 42 works, registered H001 to H044.",
    "Cada grano se redondeaba hacia dentro, capa sobre capa, hasta volverse una esfera diminuta.",
    "Each grain rounded inward, layer upon layer, until it became a tiny sphere.",
)
violations: list[str] = []
for html in ROOT.rglob("*.html"):
    text = html.read_text(encoding="utf-8", errors="ignore")
    for stale in stale_strings:
        if stale in text:
            violations.append(f"{html.relative_to(ROOT)}: {stale}")
    rel = html.relative_to(ROOT).as_posix()
    if rel == "en/editions/book/index.html" and re.search(r"\bPages\s+44\b", visible_text(text), flags=re.I):
        violations.append("en/editions/book/index.html: Pages 44")
    if rel == "ediciones/libro/index.html" and re.search(r"\bPáginas\s+44\b", visible_text(text), flags=re.I):
        violations.append("ediciones/libro/index.html: Páginas 44")
if violations:
    raise SystemExit("Stale factual copy remains:\n" + "\n".join(violations))

checks = {
    "carteles/index.html": ("Hallazgo reúne 44 obras, registradas de H001 a H044.",),
    "en/posters/index.html": ("Hallazgo brings together 44 works, registered H001 to H044.",),
    "catalogo-hallazgo/index.html": ("Hallazgo reúne 44 obras",),
    "en/hallazgo-catalogue/index.html": ("Hallazgo brings together 44 works",),
    "domingos/03-la-memoria-del-mar/index.html": ("Alrededor de cada grano crecía una capa tras otra",),
    "en/sundays/03-the-memory-of-the-sea/index.html": ("Layer upon layer grew around each grain",),
    "domingos/index.html": ('data-sunday-archive-row="3"','href="/domingos/03-la-memoria-del-mar/"'),
    "en/sundays/index.html": ('data-sunday-archive-row="3"','href="/en/sundays/03-the-memory-of-the-sea/"'),
}
for rel, needles in checks.items():
    _, text = read(rel)
    for needle in needles:
        if needle not in text:
            raise SystemExit(f"Consistency invariant missing in {rel}: {needle}")

_, english_book = read("en/editions/book/index.html")
if not re.search(r"\bPages\s+48\b", visible_text(english_book), flags=re.I):
    raise SystemExit("English book specification must visibly read Pages 48")

_, spanish_book = read("ediciones/libro/index.html")
if not re.search(r"\bPáginas\s+48\b", visible_text(spanish_book), flags=re.I):
    raise SystemExit("Spanish book specification must visibly read Páginas 48")

for rel in ("domingos/index.html", "en/sundays/index.html"):
    _, text = read(rel)
    if pending_sunday03_blocks(text):
        raise SystemExit(f"Sunday 03 still pending in detailed archive: {rel}")

print("OOLITA factual/content consistency validated successfully.")

# The reconstructed origin runs this consistency module before the search/SEO
# layers; the final workflow runs it again afterwards. og.png is created by the
# later search-visibility pass, so it is a stable final-stage marker and prevents
# the reader-facing edits from disturbing legacy reconstruction validators.
if (ROOT / "og.png").is_file():
    import apply_credibility_precision_v1  # noqa: E402,F401
    import apply_content_quality_v1  # noqa: E402,F401
    import apply_connective_copy_v1  # noqa: E402,F401
    import apply_original_audit_completion_v1  # noqa: E402,F401
    import apply_post_audit_growth_system_v1  # noqa: E402,F401
else:
    print("OOLITA final reader precision deferred until final reader build.")

# Restore only the machine-readable Wednesday publishing bank and its approved
# R01-R09 MP4s. During initial reconstruction ffmpeg is not installed yet; the
# workflow invokes this guard again after installing ffmpeg, which is the bank step.
if shutil.which("ffmpeg"):
    subprocess.run([sys.executable, str(Path(__file__).with_name("build_wednesday_bank_v1.py")), str(ROOT)], check=True)
else:
    print("Wednesday bank deferred until ffmpeg is available in the final build stage.")

# Absolute final accessibility gate. A skip link is local page navigation; it must
# target the page's own <main>, never Hallazgo or another route. Match rendered
# anchor text rather than raw inner HTML so nested spans/icons cannot evade repair.
SKIP_LABELS = {"Saltar al contenido", "Skip to content"}
ANCHOR_RE = re.compile(r'<a\b(?P<attrs>[^>]*)>(?P<body>[\s\S]*?)</a>', re.I)
HREF_RE = re.compile(r'\bhref\s*=\s*(["\'])(?P<href>[^"\']*)\1', re.I)
MAIN_RE = re.compile(r'<main\b[^>]*>', re.I)
ID_RE = re.compile(r'\bid\s*=\s*(["\'])(?P<id>[^"\']+)\1', re.I)


def rendered_anchor_text(body: str) -> str:
    return re.sub(r"\s+", " ", html_lib.unescape(re.sub(r"<[^>]+>", " ", body))).strip()


def set_anchor_href(anchor: str, target: str) -> str:
    if HREF_RE.search(anchor):
        return HREF_RE.sub(lambda m: f'href={m.group(1)}{target}{m.group(1)}', anchor, count=1)
    return anchor[:-1] + f' href="{target}">'


skip_pages = 0
skip_links = 0
for page in sorted(ROOT.rglob("*.html")):
    text = page.read_text(encoding="utf-8", errors="ignore")
    matches = [m for m in ANCHOR_RE.finditer(text) if rendered_anchor_text(m.group("body")) in SKIP_LABELS]
    if not matches:
        continue

    main_match = MAIN_RE.search(text)
    if not main_match:
        raise SystemExit(f"Skip link without <main>: {page.relative_to(ROOT)}")
    main_tag = main_match.group(0)
    main_id_match = ID_RE.search(main_tag)
    if main_id_match:
        target_id = main_id_match.group("id")
    else:
        target_id = "contenido"
        fixed_main = main_tag[:-1] + f' id="{target_id}">'
        text = text[:main_match.start()] + fixed_main + text[main_match.end():]

    # Re-scan after a possible <main> insertion so anchor offsets remain valid.
    def repair_anchor(match: re.Match[str]) -> str:
        nonlocal_marker = rendered_anchor_text(match.group("body"))
        if nonlocal_marker not in SKIP_LABELS:
            return match.group(0)
        return set_anchor_href(match.group(0), f"#{target_id}")

    text, repaired = ANCHOR_RE.subn(repair_anchor, text)
    page.write_text(text, encoding="utf-8")

    final_text = page.read_text(encoding="utf-8")
    final_matches = [m for m in ANCHOR_RE.finditer(final_text) if rendered_anchor_text(m.group("body")) in SKIP_LABELS]
    if not final_matches:
        raise SystemExit(f"Skip link disappeared during repair: {page.relative_to(ROOT)}")
    for match in final_matches:
        href_match = HREF_RE.search(match.group(0))
        if not href_match or href_match.group("href") != f"#{target_id}":
            raise SystemExit(f"Non-local skip link survived in {page.relative_to(ROOT)}")
    if not re.search(rf'<main\b[^>]*\bid=(["\']){re.escape(target_id)}\1', final_text, flags=re.I):
        raise SystemExit(f"Skip target missing from <main>: {page.relative_to(ROOT)}#{target_id}")

    skip_pages += 1
    skip_links += len(final_matches)

if skip_pages == 0:
    raise SystemExit("Final accessibility gate found no skip links to validate")
print(f"OOLITA final skip-link gate passed: {skip_links} local link(s) across {skip_pages} page(s).")

# Direct-entry navigation is applied and validated earlier by apply_cta_clarity_v1.py.
# Production propagation trigger: post-audit conversion, journey, pacing and launch system.
