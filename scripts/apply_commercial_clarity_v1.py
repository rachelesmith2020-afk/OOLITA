#!/usr/bin/env python3
"""Make OOLITA availability and release status immediately legible.

This is not a conversion layer. It keeps the existing voice and product pages,
but makes the higher-level routes answer four practical questions at a glance:
what exists now, what opens free, when the book is released, and when the first
textile edition is released. It also keeps the textile specification precise.
"""
from __future__ import annotations

from html import unescape
from pathlib import Path
import re
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")


def read(rel: str) -> tuple[Path, str]:
    path = ROOT / rel
    if not path.is_file():
        raise SystemExit(f"Missing commercial-clarity target: {rel}")
    return path, path.read_text(encoding="utf-8")


def rendered(fragment: str) -> str:
    text = unescape(re.sub(r"<[^>]+>", "", fragment))
    return re.sub(r"\s+", " ", text).strip()


def replace_any_once(rel: str, old_forms: tuple[str, ...], new: str) -> None:
    """Accept the known live/source variants but publish one reviewed final form."""
    path, text = read(rel)
    if new in text:
        return
    for old in old_forms:
        count = text.count(old)
        if count == 1:
            path.write_text(text.replace(old, new, 1), encoding="utf-8")
            return
        if count > 1:
            raise SystemExit(f"Commercial source duplicated in {rel}: {old!r}; found {count}")
    raise SystemExit(f"No known commercial source state found in {rel}: {old_forms[0]!r}")


def replace_paragraph(
    rel: str,
    marker: str | tuple[str, ...],
    new_inner: str,
) -> None:
    """Replace one paragraph from any known source state; safe on rebuilt live HTML."""
    path, text = read(rel)
    if new_inner in text:
        return
    markers = (marker,) if isinstance(marker, str) else marker
    pattern = re.compile(r"(<p\b[^>]*>)(.*?)(</p>)", flags=re.I | re.S)
    matches = [
        m
        for m in pattern.finditer(text)
        if any(source in rendered(m.group(2)) for source in markers)
    ]
    if len(matches) != 1:
        raise SystemExit(
            f"Expected one paragraph in {rel} for one of {markers!r}; found {len(matches)}"
        )
    match = matches[0]
    replacement = match.group(1) + new_inner + match.group(3)
    path.write_text(text[: match.start()] + replacement + text[match.end() :], encoding="utf-8")


def ensure_status_after_paragraph(
    rel: str,
    anchor_marker: str,
    old_statuses: tuple[str, ...],
    status: str,
) -> None:
    """Replace an older status paragraph, or insert it once when absent."""
    path, text = read(rel)
    pattern = re.compile(r"(<p\b[^>]*>)(.*?)(</p>)", flags=re.I | re.S)
    paragraphs = list(pattern.finditer(text))
    if any(rendered(m.group(2)) == status for m in paragraphs):
        return

    for old in old_statuses:
        matches = [m for m in paragraphs if rendered(m.group(2)) == old]
        if len(matches) > 1:
            raise SystemExit(f"Duplicate old commercial status in {rel}: {old}")
        if len(matches) == 1:
            match = matches[0]
            replacement = match.group(1) + status + match.group(3)
            path.write_text(text[: match.start()] + replacement + text[match.end() :], encoding="utf-8")
            return

    anchors = [m for m in paragraphs if anchor_marker in rendered(m.group(2))]
    if len(anchors) != 1:
        raise SystemExit(f"Expected one status anchor in {rel} for {anchor_marker!r}; found {len(anchors)}")
    match = anchors[0]
    insertion = match.group(0) + "\n<p>" + status + "</p>"
    path.write_text(text[: match.start()] + insertion + text[match.end() :], encoding="utf-8")


STATUS_EN = (
    "NOW · labyrinth at Los Escullos · 22 Sundays. "
    "03 JAN 27 · 3D world opens · free. "
    "31 JAN 27 · book release. "
    "11 APR 27 · first textile edition release."
)
STATUS_ES = (
    "AHORA · laberinto en Los Escullos · 22 domingos. "
    "03 ENE 27 · abre el mundo 3D · gratis. "
    "31 ENE 27 · publicación del libro. "
    "11 ABR 27 · primera edición textil."
)
OLD_STATUS_EN = (
    "NOW · labyrinth at Los Escullos · 22 Sundays. 03 JAN 27 · 3D world opens · free. 31 JAN 27 · book goes on sale. 11 APR 27 · first textile edition goes on sale.",
)
OLD_STATUS_ES = (
    "AHORA · laberinto en Los Escullos · 22 domingos. 03 ENE 27 · abre el mundo 3D · gratis. 31 ENE 27 · el libro sale a la venta. 11 ABR 27 · sale a la venta la primera edición textil.",
)

# HOMEPAGE — the dates already existed, but were scattered through long sections.
# Use release language here rather than implying that checkout is open now.
ensure_status_after_paragraph(
    "en/index.html",
    "The stone labyrinth is already at Los Escullos; there is no ticket or booking.",
    OLD_STATUS_EN,
    STATUS_EN,
)
ensure_status_after_paragraph(
    "index.html",
    "El laberinto de piedra ya está en Los Escullos",
    OLD_STATUS_ES,
    STATUS_ES,
)

# EDITIONS — future dates should not read as if sales are open now. Product detail
# pages already say explicitly that sales have not opened.
replace_any_once(
    "en/editions/index.html",
    ("On sale · 31.01.27", "Available 31.01.27"),
    "Available from 31.01.27",
)
replace_any_once(
    "en/editions/index.html",
    ("On sale · 11.04.27", "Coming · 11.04.27"),
    "Available from 11.04.27",
)
replace_any_once(
    "ediciones/index.html",
    ("A la venta · 31.01.27", "Disponible 31.01.27"),
    "Disponible desde el 31.01.27",
)
replace_any_once(
    "ediciones/index.html",
    ("A la venta · 11.04.27", "Próximamente · 11.04.27"),
    "Disponible desde el 11.04.27",
)

# FIELD BOOK — future, but not dated. Say that instead of making the reader infer it.
replace_paragraph(
    "en/editions/index.html",
    "A bilingual publication for children and families",
    "In development. No release date yet. A bilingual publication for children and families: observe, draw, listen and record without collecting or disturbing anything.",
)
replace_paragraph(
    "ediciones/index.html",
    "Una publicación bilingüe para niños y familias",
    "En desarrollo. Aún no hay fecha de publicación. Una publicación bilingüe para niños y familias: observar, dibujar, escuchar y registrar sin recoger ni alterar nada.",
)

# TEXTILE DETAIL — use the current European Blaster 2.0 specification and distinguish
# product certifications from company memberships. No Fair Wear start year is stated
# because the brand and Fair Wear currently publish different membership years.
replace_paragraph(
    "en/editions/t-shirt/index.html",
    "It is a Stanley/Stella Blaster 2.0",
    "It is a Stanley/Stella Blaster 2.0, not a generic tee: 200 gsm single jersey in 100% organic ring-spun combed cotton. Oversized fit, set-in sleeves, dropped shoulders, 1x1 rib mock-neck collar, inside back-neck tape and twin-needle topstitching at sleeves and hem.",
)
replace_paragraph(
    "en/editions/t-shirt/index.html",
    (
        "It carries GOTS organic cotton certification",
        "PETA lists the company as 100% vegan",
        "PETA-Approved; its products are made from 100% vegan materials",
    ),
    "Stanley/Stella lists the Blaster 2.0 with GOTS and OEKO-TEX certification. Stanley/Stella is a Fair Wear member and PETA-Approved; its products are made from 100% vegan materials.",
)
replace_paragraph(
    "ediciones/camiseta/index.html",
    "Es una Stanley/Stella Blaster 2.0",
    "Es una Stanley/Stella Blaster 2.0, no una camiseta genérica: jersey sencillo de algodón orgánico peinado e hilado en anillo, 200 g/m². Corte oversized, manga montada, hombro caído, cuello alto de canalé 1x1, cinta interior del cuello y pespunte doble en puños y bajo.",
)
replace_paragraph(
    "ediciones/camiseta/index.html",
    (
        "Lleva certificación GOTS de algodón orgánico",
        "PETA incluye a la empresa entre sus compañías 100 % veganas",
        "está aprobada por PETA; sus productos están hechos con materiales 100 % veganos",
    ),
    "La ficha de Stanley/Stella muestra la Blaster 2.0 con certificaciones GOTS y OEKO-TEX. Stanley/Stella es miembro de Fair Wear y está aprobada por PETA; sus productos están hechos con materiales 100 % veganos.",
)
replace_any_once(
    "en/editions/t-shirt/index.html",
    ("Certified", "Credentials"),
    "Credentials",
)
replace_any_once(
    "en/editions/t-shirt/index.html",
    (
        "GOTS · OEKO-TEX · PETA Vegan · Fair Wear",
        "GOTS · OEKO-TEX · Fair Wear member · PETA-listed vegan company",
    ),
    "GOTS · OEKO-TEX · Fair Wear member · PETA-Approved",
)
replace_any_once(
    "ediciones/camiseta/index.html",
    ("Certificados", "Credenciales"),
    "Credenciales",
)
replace_any_once(
    "ediciones/camiseta/index.html",
    (
        "GOTS · OEKO-TEX · Vegano PETA · Fair Wear",
        "GOTS · OEKO-TEX · miembro de Fair Wear · empresa vegana en PETA",
    ),
    "GOTS · OEKO-TEX · miembro de Fair Wear · PETA-Approved",
)

# Regression/positive guards.
required = {
    "en/index.html": (STATUS_EN,),
    "index.html": (STATUS_ES,),
    "en/editions/index.html": (
        "Available from 31.01.27",
        "Available from 11.04.27",
        "In development. No release date yet.",
    ),
    "ediciones/index.html": (
        "Disponible desde el 31.01.27",
        "Disponible desde el 11.04.27",
        "En desarrollo. Aún no hay fecha de publicación.",
    ),
    "en/editions/t-shirt/index.html": (
        "200 gsm single jersey in 100% organic ring-spun combed cotton",
        "Stanley/Stella is a Fair Wear member and PETA-Approved; its products are made from 100% vegan materials",
        "Credentials",
        "GOTS · OEKO-TEX · Fair Wear member · PETA-Approved",
    ),
    "ediciones/camiseta/index.html": (
        "algodón orgánico peinado e hilado en anillo",
        "Stanley/Stella es miembro de Fair Wear y está aprobada por PETA; sus productos están hechos con materiales 100 % veganos",
        "Credenciales",
        "GOTS · OEKO-TEX · miembro de Fair Wear · PETA-Approved",
    ),
}
stale = {
    "en/index.html": ("book goes on sale", "first textile edition goes on sale"),
    "index.html": ("el libro sale a la venta", "sale a la venta la primera edición textil"),
    "en/editions/index.html": ("On sale · 31.01.27", "On sale · 11.04.27"),
    "ediciones/index.html": ("A la venta · 31.01.27", "A la venta · 11.04.27"),
    "en/editions/t-shirt/index.html": (
        "Fair Wear accreditation in the making",
        "Fair Wear member since 2012",
        "PETA Vegan · Fair Wear",
        "PETA-listed vegan company",
        "PETA lists the company as 100% vegan",
    ),
    "ediciones/camiseta/index.html": (
        "algodón orgánico peinado de hilo abierto",
        "Fair Wear en la confección",
        "miembro de Fair Wear desde 2012",
        "Vegano PETA · Fair Wear",
        "empresa vegana en PETA",
        "PETA incluye a la empresa entre sus compañías 100 % veganas",
    ),
}
for rel, phrases in required.items():
    _, text = read(rel)
    visible = rendered(text)
    for phrase in phrases:
        if phrase not in visible:
            raise SystemExit(f"Commercial-clarity invariant missing in {rel}: {phrase}")
for rel, phrases in stale.items():
    _, text = read(rel)
    visible = rendered(text)
    for phrase in phrases:
        if phrase in visible:
            raise SystemExit(f"Stale commercial status remains in {rel}: {phrase}")

# Site-wide no-straggler gate. The target-page assertions above prove the new copy
# exists; this scan proves retired commercial/credential wording does not survive
# elsewhere in the final deploy bundle.
sitewide_stale = (
    "book goes on sale",
    "first textile edition goes on sale",
    "el libro sale a la venta",
    "sale a la venta la primera edición textil",
    "On sale · 31.01.27",
    "On sale · 11.04.27",
    "A la venta · 31.01.27",
    "A la venta · 11.04.27",
    "algodón orgánico peinado de hilo abierto",
    "Fair Wear accreditation in the making",
    "Fair Wear en la confección",
    "Fair Wear member since 2012",
    "miembro de Fair Wear desde 2012",
    "PETA-listed vegan company",
    "empresa vegana en PETA",
)
stragglers: list[str] = []
for page in sorted(ROOT.rglob("*.html")):
    visible = rendered(page.read_text(encoding="utf-8"))
    for phrase in sitewide_stale:
        if phrase in visible:
            stragglers.append(f"{page.relative_to(ROOT)}: {phrase}")
if stragglers:
    raise SystemExit("Commercial/credential stragglers remain:\n  - " + "\n  - ".join(stragglers))

print("OOLITA commercial availability/status clarity, textile precision and site-wide no-straggler gate passed.")
