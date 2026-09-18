#!/usr/bin/env python3
"""Retire the obsolete 22-Sundays launch campaign from the built OOLITA site.

This is deliberately a final deployment layer. Older reconstruction scripts may
still know how to rebuild the historical Sundays archive, but the public site
must no longer expose that campaign or the superseded 3 January 2027 launch
date.

Public state after this pass:
- 3D world: 23 May 2027, 00:00 CEST.
- No 22 Sundays / 22 domingos campaign copy, navigation or archive pages.
- Legacy Sunday URLs redirect permanently to the appropriate language homepage.
- Poster 03 (the "22 DOMINGOS / 22 SUNDAYS" artwork) is not published.
"""
from __future__ import annotations

from pathlib import Path
import json
import re
import shutil
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
if not ROOT.is_dir():
    raise SystemExit(f"Missing built site: {ROOT}")

FLAGS = re.I | re.S

OLD_DATE_REPLACEMENTS = (
    ("2027-01-03T00:00:00+01:00", "2027-05-23T00:00:00+02:00"),
    ("2027-01-03T00:00:00Z", "2027-05-23T00:00:00+02:00"),
    ("2027-01-03", "2027-05-23"),
    ("03.01.2027", "23.05.2027"),
    ("03.01.27", "23.05.27"),
    ("03 JAN 27", "23 MAY 27"),
    ("03 ENE 27", "23 MAY 27"),
    ("3 Jan 2027", "23 May 2027"),
    ("3 Jan 27", "23 May 27"),
    ("3 Jan", "23 May"),
    ("03 Jan", "23 May"),
    ("3 ene", "23 mayo"),
    ("03 ene", "23 mayo"),
    ("3 January 2027", "23 May 2027"),
    ("3 January", "23 May"),
    ("3 de enero de 2027", "23 de mayo de 2027"),
    ("3 de enero", "23 de mayo"),
    ("00:00 CET", "00:00 CEST"),
)

NEUTRAL_REPLACEMENTS = (
    ("Seguir el camino hasta el 3 de enero", "Explorar OOLITA"),
    ("Follow the path to 3 January", "Explore OOLITA"),
    ("El camino, domingo a domingo.", "Los Escullos en el navegador."),
    ("The path, one Sunday at a time.", "Los Escullos in the browser."),
    ("Los Escullos en 3D, desde el 3 de enero.", "El mundo 3D abre el 23 de mayo de 2027."),
    ("Los Escullos in 3D, from 3 January.", "The 3D world opens on 23 May 2027."),
    ("@oolita.es · una imagen cada domingo ↗", "@oolita.es ↗"),
    ("@oolita.es · one image every Sunday ↗", "@oolita.es ↗"),
    ("Los nueve carteles de la apertura de la cuenta", "Los carteles que abrieron la cuenta"),
    ("The nine posters that opened the account", "The posters that opened the account"),
    ("The nine posters — the opening of OOLITA", "The posters — OOLITA"),
    ("Los nueve carteles", "Los carteles"),
    ("The nine posters", "The posters"),
    ("nueve carteles", "carteles"),
    ("nine posters", "posters"),
    ("nueve láminas", "una serie de láminas"),
    ("nine plates", "a series of plates"),
    ("9 carteles", "Archivo bilingüe"),
    ("9 posters", "Bilingual archive"),
    ("Cada domingo aparece un poco más del diseño.", "El diseño se irá revelando poco a poco hasta el verano."),
    ("Each Sunday a little more of the design appears.", "The design will be revealed gradually through to summer."),
    ("Detalles e historia · domingo a domingo", "Detalles e historia · revelados poco a poco"),
    ("Details and story · Sunday by Sunday", "Details and story · revealed gradually"),
    ("domingo a domingo hasta el verano.", "poco a poco hasta el verano."),
    ("Sunday by Sunday through to summer.", "gradually through to summer."),
)

CAMPAIGN_P_RE = re.compile(
    r'<p\b[^>]*>(?:(?!</p>).)*?'
    r'(?:22\s*(?:Sundays|domingos)|22[- ]Sunday|'
    r'twenty[- ]two\s+Sundays|veintid[oó]s\s+domingos|'
    r'one image (?:every Sunday|each Sunday|a week)|'
    r'una imagen (?:cada domingo|cada semana)|'
    r'one Sunday at a time|domingo a domingo|'
    r'archive grows each Sunday|archivo crece cada domingo|'
    r'Sundays eleven and twelve|domingos once y doce)'
    r'(?:(?!</p>).)*?</p>',
    FLAGS,
)

CAMPAIGN_SMALL_ELEMENT_RE = re.compile(
    r'<(?P<tag>h[1-6]|span|li)\b[^>]*>(?:(?!</(?P=tag)>).)*?'
    r'(?:22\s*(?:Sundays|domingos)|22[- ]Sunday|'
    r'twenty[- ]two\s+Sundays|veintid[oó]s\s+domingos)'
    r'(?:(?!</(?P=tag)>).)*?</(?P=tag)>',
    FLAGS,
)

SUNDAY_LINK_RE = re.compile(
    r'<a\b[^>]*href=["\'](?:https://oolita\.es)?/'
    r'(?:domingos|en/sundays)(?:/[^"\']*)?["\'][^>]*>.*?</a>',
    FLAGS,
)

PILAR_ES_RE = re.compile(
    r'<a\b(?=[^>]*class=["\'][^"\']*\bpilar\b[^"\']*["\'])'
    r'(?=[^>]*href=["\']/domingos/?["\'])[^>]*>.*?</a>',
    FLAGS,
)
PILAR_EN_RE = re.compile(
    r'<a\b(?=[^>]*class=["\'][^"\']*\bpilar\b[^"\']*["\'])'
    r'(?=[^>]*href=["\']/en/sundays/?["\'])[^>]*>.*?</a>',
    FLAGS,
)

PILAR_ES = (
    '<a class="pilar b" href="/mundo-3d/">'
    '<span class="n">02</span><h3>Mundo 3D</h3>'
    '<span class="glo">Los Escullos en el navegador · abre 23.05.27</span>'
    '<span class="fl">→</span></a>'
)
PILAR_EN = (
    '<a class="pilar b" href="/en/3d-world/">'
    '<span class="n">02</span><h3>3D world</h3>'
    '<span class="glo">Los Escullos in the browser · opens 23 May 27</span>'
    '<span class="fl">→</span></a>'
)

def replace_dates(text: str) -> str:
    for old, new in OLD_DATE_REPLACEMENTS:
        text = text.replace(old, new)
    return text

def remove_marker_block(text: str, marker: str, tags: tuple[str, ...]) -> tuple[str, bool]:
    escaped = re.escape(marker)
    for tag in tags:
        pattern = re.compile(
            rf'<{tag}\b[^>]*>(?:(?!</{tag}>).)*?{escaped}(?:(?!</{tag}>).)*?</{tag}>',
            FLAGS,
        )
        text, count = pattern.subn("", text, count=1)
        if count:
            return text, True
    return text, False

def clean_html(path: Path) -> None:
    rel = path.relative_to(ROOT).as_posix()
    text = path.read_text(encoding="utf-8", errors="strict")
    original = text

    text = replace_dates(text)

    # Preserve the homepage's three-part structural rhythm without inventing a
    # successor campaign: the existing 3D world takes the retired archive slot.
    if rel in {"index.html", "404.html", "404/index.html"}:
        text = PILAR_ES_RE.sub(PILAR_ES, text)
    elif rel == "en/index.html":
        text = PILAR_EN_RE.sub(PILAR_EN, text)

    # Remove known campaign-only blocks before broad text cleanup.
    text = re.sub(
        r'<section\b[^>]*id=["\']oolita-art-field-sundays["\'][^>]*>.*?</section>',
        "",
        text,
        flags=FLAGS,
    )
    text = re.sub(
        r'<section\b[^>]*id=["\']working-rhythm["\'][^>]*>.*?</section>',
        "",
        text,
        flags=FLAGS,
    )

    # Poster 03 is itself the obsolete campaign artwork. Do not rewrite the art;
    # retire it from the published poster archive.
    if rel in {"carteles/index.html", "en/posters/index.html"}:
        text, removed = remove_marker_block(text, "cartel-03.", ("article", "li", "figure"))
        if not removed:
            text = re.sub(
                r'<picture\b[^>]*>.*?cartel-03\.(?:avif|webp|png).*?</picture>',
                "",
                text,
                flags=FLAGS,
            )
            text = re.sub(
                r'<img\b[^>]*cartel-03\.(?:avif|webp|png)[^>]*>',
                "",
                text,
                flags=FLAGS,
            )
        text = re.sub(
            r'/carteles/img/social-(?:carteles|posters)\.(?:png|jpe?g|webp|avif)',
            '/carteles/img/cartel-01.png',
            text,
            flags=re.I,
        )

    # Poster 03 was the retired campaign artwork. Any residual metadata,
    # preload or responsive-image reference must point at an existing neutral
    # poster asset with the same encoding.
    text = re.sub(
        r'/carteles/img/cartel-03\.(avif|webp|png)',
        lambda match: f'/carteles/img/cartel-01.{match.group(1).lower()}',
        text,
        flags=re.I,
    )

    # Campaign paragraphs and labels are removed rather than rewritten into a
    # second countdown concept.
    text = CAMPAIGN_P_RE.sub("", text)
    text = CAMPAIGN_SMALL_ELEMENT_RE.sub("", text)

    # Any remaining links into the retired archive are removed. The homepage
    # primary pillar has already been converted to the existing 3D-world page.
    text = SUNDAY_LINK_RE.sub("", text)

    # Some late site layers inject the archive route into shared navigation as
    # plain href attributes after the original anchor markup has been assembled.
    # No public page should retain a reference to the retired archive: route any
    # such residual href to the appropriate language homepage.
    text = re.sub(
        r"href=([\"'])(?:https://oolita\.es)?/domingos(?:/[^\"']*)?\1",
        r"href=\1/\1",
        text,
        flags=re.I,
    )
    text = re.sub(
        r"href=([\"'])(?:https://oolita\.es)?/en/sundays(?:/[^\"']*)?\1",
        r"href=\1/en/\1",
        text,
        flags=re.I,
    )

    # Remove retired archive imagery that was embedded outside archive pages.
    text = re.sub(
        r'<picture\b[^>]*>.*?/(?:domingos|en/sundays)/.*?</picture>',
        "",
        text,
        flags=FLAGS,
    )
    text = re.sub(
        r'<img\b[^>]*(?:/domingos/|/en/sundays/)[^>]*>',
        "",
        text,
        flags=FLAGS,
    )

    # Strip the status-line fragments without disturbing the approved release
    # dates that follow them.
    text = re.sub(r'\s*·\s*22\s*domingos\b', "", text, flags=re.I)
    text = re.sub(r'\s*·\s*22\s*Sundays\b', "", text, flags=re.I)

    for old, new in NEUTRAL_REPLACEMENTS:
        text = text.replace(old, new)

    # Homepage-only labels: turn the obsolete campaign label into a direct label
    # for the existing 3D world and its approved May launch.
    if rel in {"index.html", "404.html", "404/index.html", "en/index.html"}:
        text = re.sub(r'22\s+domingos', "Mundo 3D", text, flags=re.I)
        text = re.sub(r'22\s+Sundays', "3D world", text, flags=re.I)

    # Final neutralisation for metadata/search snippets that are not wrapped in
    # ordinary reader-facing elements.
    text = re.sub(r'22[- ]Sunday(?:s)?', "project", text, flags=re.I)
    text = re.sub(r'22\s+domingos', "proyecto", text, flags=re.I)
    text = re.sub(r'twenty[- ]two\s+Sundays', "project", text, flags=re.I)
    text = re.sub(r'veintid[oó]s\s+domingos', "proyecto", text, flags=re.I)
    text = re.sub(r'one image every Sunday', "project updates", text, flags=re.I)
    text = re.sub(r'one image each Sunday', "project updates", text, flags=re.I)
    text = re.sub(r'una imagen cada domingo', "notas del proyecto", text, flags=re.I)
    text = re.sub(r'Sunday by Sunday', "gradually", text, flags=re.I)
    text = re.sub(r'domingo a domingo', "poco a poco", text, flags=re.I)

    if text != original:
        path.write_text(text, encoding="utf-8")

def clean_json_value(value):
    if isinstance(value, dict):
        # Search/result records pointing to retired routes are removed whole.
        direct_strings = [v for v in value.values() if isinstance(v, str)]
        if any("/domingos/" in v or "/en/sundays/" in v for v in direct_strings):
            return None
        out = {}
        for k, v in value.items():
            cleaned = clean_json_value(v)
            if cleaned is not None:
                out[k] = cleaned
        return out
    if isinstance(value, list):
        out = []
        for item in value:
            cleaned = clean_json_value(item)
            if cleaned is not None:
                out.append(cleaned)
        return out
    if isinstance(value, str):
        value = replace_dates(value)
        value = re.sub(
            r'/carteles/img/cartel-03\.(avif|webp|png)',
            lambda match: f'/carteles/img/cartel-01.{match.group(1).lower()}',
            value,
            flags=re.I,
        )
        for old, new in NEUTRAL_REPLACEMENTS:
            value = value.replace(old, new)
        value = re.sub(r'22[- ]Sunday(?:s)?', "project", value, flags=re.I)
        value = re.sub(r'22\s+domingos', "proyecto", value, flags=re.I)
        value = re.sub(r'twenty[- ]two\s+Sundays', "project", value, flags=re.I)
        value = re.sub(r'veintid[oó]s\s+domingos', "proyecto", value, flags=re.I)
        value = re.sub(r'one image every Sunday', "project updates", value, flags=re.I)
        value = re.sub(r'una imagen cada domingo', "notas del proyecto", value, flags=re.I)
        value = re.sub(r'Sunday by Sunday', "gradually", value, flags=re.I)
        value = re.sub(r'domingo a domingo', "poco a poco", value, flags=re.I)
        return value
    return value

# Process all public HTML first.
for page in sorted(ROOT.rglob("*.html")):
    clean_html(page)

# Retire the archive itself.
shutil.rmtree(ROOT / "domingos", ignore_errors=True)
shutil.rmtree(ROOT / "en" / "sundays", ignore_errors=True)

# Retire the campaign poster artwork from direct public asset URLs as well.
for ext in ("avif", "webp", "png"):
    (ROOT / "carteles" / "img" / f"cartel-03.{ext}").unlink(missing_ok=True)
for name in ("social-carteles.png", "social-posters.png"):
    (ROOT / "carteles" / "img" / name).unlink(missing_ok=True)

# Remove retired URLs from the sitemap without disturbing the rest of its
# formatting or hreflang structure.
sitemap = ROOT / "sitemap.xml"
if sitemap.is_file():
    text = sitemap.read_text(encoding="utf-8")
    text = re.sub(
        r'/carteles/img/cartel-03\.(avif|webp|png)',
        lambda match: f'/carteles/img/cartel-01.{match.group(1).lower()}',
        text,
        flags=re.I,
    )
    text = re.sub(
        r'\s*<url>\s*<loc>https://oolita\.es/(?:domingos|en/sundays)(?:/[^<]*)?</loc>.*?</url>\s*',
        "\n",
        text,
        flags=FLAGS,
    )
    sitemap.write_text(text, encoding="utf-8")

# Clean any generated public JSON/search indexes after the page retirement.
for path in sorted(ROOT.rglob("*.json")):
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        # If it is not strict JSON, leave structure alone but still update the
        # superseded date spellings.
        raw = path.read_text(encoding="utf-8", errors="ignore")
        updated = replace_dates(raw)
        if updated != raw:
            path.write_text(updated, encoding="utf-8")
        continue
    cleaned = clean_json_value(data)
    path.write_text(
        json.dumps(cleaned, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )

# Legacy indexed/bookmarked archive URLs should resolve cleanly.
redirects = ROOT / "_redirects"
existing = redirects.read_text(encoding="utf-8") if redirects.is_file() else ""
rules = (
    "/domingos / 301",
    "/domingos/ / 301",
    "/domingos/* / 301",
    "/en/sundays /en/ 301",
    "/en/sundays/ /en/ 301",
    "/en/sundays/* /en/ 301",
)
lines = [line for line in existing.splitlines() if line.strip()]
for rule in rules:
    if rule not in lines:
        lines.append(rule)
redirects.write_text("\n".join(lines) + "\n", encoding="utf-8")

# Final fail-closed audit. _redirects is intentionally excluded because it must
# contain the retired paths in order to redirect them.
forbidden_patterns = (
    re.compile(r'22\s+Sundays', re.I),
    re.compile(r'22\s+domingos', re.I),
    re.compile(r'22[- ]Sunday', re.I),
    re.compile(r'twenty[- ]two\s+Sundays', re.I),
    re.compile(r'veintid[oó]s\s+domingos', re.I),
    re.compile(r'one image every Sunday', re.I),
    re.compile(r'una imagen cada domingo', re.I),
    re.compile(r'Sunday by Sunday', re.I),
    re.compile(r'domingo a domingo', re.I),
    re.compile(r'(?:href|src|srcset)=["\'][^"\']*/(?:domingos|en/sundays)/', re.I),
    re.compile(r'cartel-03\.(?:avif|webp|png)', re.I),
    re.compile(r'2027-01-03', re.I),
    re.compile(r'03\.01\.2027', re.I),
    re.compile(r'03\.01\.27', re.I),
    re.compile(r'\b3 January(?: 2027)?\b', re.I),
    re.compile(r'\b3 Jan(?:uary)?(?: 2027| 27)?\b', re.I),
    re.compile(r'\b3 de enero(?: de 2027)?\b', re.I),
    re.compile(r'\b03 (?:JAN|ENE) 27\b', re.I),
)
bad = []
for path in sorted(ROOT.rglob("*")):
    if not path.is_file() or path.name == "_redirects":
        continue
    if path.suffix.lower() not in {".html", ".xml", ".json", ".js", ".css", ".txt"}:
        continue
    content = path.read_text(encoding="utf-8", errors="ignore")
    for pattern in forbidden_patterns:
        match = pattern.search(content)
        if match:
            bad.append(f"{path.relative_to(ROOT)}: {match.group(0)!r}")
            break

if (ROOT / "domingos").exists() or (ROOT / "en" / "sundays").exists():
    bad.append("retired Sunday archive directory still exists")

for ext in ("avif", "webp", "png"):
    if (ROOT / "carteles" / "img" / f"cartel-03.{ext}").exists():
        bad.append(f"carteles/img/cartel-03.{ext} still exists")

if bad:
    print("Obsolete Sundays/3-January material survived retirement:")
    print("\n".join(bad[:100]))
    raise SystemExit(1)

# Positive checks: the approved date and the new homepage replacement must be
# present, proving that retirement did not erase the current launch calendar.
required = {
    "index.html": ("23.05.2027", "Mundo 3D"),
    "en/index.html": ("23 May 2027", "3D world"),
    "mundo-3d/index.html": ("23.05.27", "23 de mayo"),
    "en/3d-world/index.html": ("23.05.27", "23 May"),
}
for rel, needles in required.items():
    page = ROOT / rel
    if not page.is_file():
        raise SystemExit(f"Missing required page after campaign retirement: {rel}")
    content = page.read_text(encoding="utf-8")
    for needle in needles:
        if needle not in content:
            raise SystemExit(f"Campaign retirement validation failed in {rel}: missing {needle!r}")

print("Retired 22 Sundays / 22 domingos from the public site.")
print("Retired poster 03 and Sunday archive URLs; legacy routes now redirect.")
print("Superseded 3 January 2027 launch references removed.")
print("Approved 3D-world launch remains 23 May 2027, 00:00 CEST.")
