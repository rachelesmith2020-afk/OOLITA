#!/usr/bin/env python3
"""Apply the final language/voice edit to OOLITA.

This pass corrects English that carries Spanish syntax too literally, but it does
not normalise deliberate authorial oddness. The final homepage ethos is also
kept bilingual: OOLITA is not a device for adding tourism pressure to Cabo de
Gata. Authored literary text, functional microcopy and factual terminology stay
untouched unless the language itself is the problem.
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
        raise SystemExit(f"Missing final editorial page: {rel}")
    return path, path.read_text(encoding="utf-8")


def replace_state(rel: str, old: str, new: str) -> None:
    path, text = read(rel)
    if new in text:
        return
    if old in text:
        path.write_text(text.replace(old, new), encoding="utf-8")
        return
    raise SystemExit(f"Neither source nor revised copy found in {rel}: {old!r}")


def replace_any_state(rel: str, old_forms: tuple[str, ...], new: str) -> None:
    """Accept known pipeline/origin variants but publish one reviewed final form."""
    path, text = read(rel)
    if new in text:
        return
    for old in old_forms:
        if old in text:
            path.write_text(text.replace(old, new, 1), encoding="utf-8")
            return
    raise SystemExit(f"No known source state found in {rel}: {old_forms[0]!r}")


def replace_paragraph_by_markers(rel: str, markers: tuple[str, ...], new: str) -> bool:
    """Replace one reader paragraph by its rendered-text marker, preserving its opening tag.

    Some late reader layers insert inline markup into otherwise unchanged prose. Matching
    rendered text lets the final author-voice pass remain exact without depending on those
    incidental tags. Returns False when no marker is present so a controlled fallback can run.
    """
    path, text = read(rel)
    if new in text:
        return True

    paragraph_re = re.compile(r'(<p\b[^>]*>)(.*?)(</p>)', flags=re.I | re.S)
    matches: list[tuple[int, int, str, str]] = []
    for match in paragraph_re.finditer(text):
        rendered = unescape(re.sub(r'<[^>]+>', '', match.group(2)))
        rendered = re.sub(r'\s+', ' ', rendered).strip()
        if any(marker in rendered for marker in markers):
            matches.append((match.start(), match.end(), match.group(1), match.group(3)))

    if not matches:
        return False
    if len(matches) != 1:
        raise SystemExit(f"Expected one marked paragraph in {rel}, found {len(matches)}")

    start, end, opening, closing = matches[0]
    path.write_text(text[:start] + opening + new + closing + text[end:], encoding="utf-8")
    return True


def replace_fragment_if_present(rel: str, old: str, new: str) -> None:
    """Replace a stable text fragment without assuming surrounding inline markup."""
    path, text = read(rel)
    if old in text:
        path.write_text(text.replace(old, new), encoding="utf-8")


# HOMEPAGE — correct literal English, but preserve the author's abruptness and
# deliberate negative constructions where they are doing real argumentative work.
replace_state(
    "en/index.html",
    "Nothing marks it on the ground: whoever walks past either finds it or does not.",
    "Nothing marks it on the ground: you either notice it or walk past.",
)
replace_state(
    "en/index.html",
    "Forty-eight pages, bilingual from first page to last — Spanish and English share each spread, as two voices of one text — published by Vestini Tribe.",
    "Forty-eight pages, bilingual from first page to last, with Spanish and English sharing each spread as two voices of one text. Published by Vestini Tribe.",
)
replace_state(
    "en/index.html",
    "It takes about as long to read as the path takes to walk slowly.",
    "Reading it takes about as long as walking the path slowly.",
)
replace_state(
    "en/index.html",
    "The same path stays open from elsewhere.",
    "The same path remains open from wherever you are.",
)

# This is intentionally less conventional English. It matches the Spanish idea
# and the author's established syntax: proposition, hard stop, short consequence.
replace_any_state(
    "en/index.html",
    (
        "A labyrinth gives you one path to follow. You keep going.",
        "A labyrinth asks you to decide nothing. You follow.",
    ),
    "A labyrinth asks you to decide nothing. You follow.",
)
replace_state(
    "en/index.html",
    "There will still be one OOLITA labyrinth: the one at Los Escullos. Around it will come field publications, small textile editions and collaborations made in Cabo de Gata.",
    "OOLITA will continue to have one labyrinth: the one at Los Escullos. Around it, the project will grow through field publications, small textile editions and collaborations made in Cabo de Gata.",
)

# The environmental position is not decorative brand language. It explains why
# OOLITA keeps one physical labyrinth and opens the same path digitally. The
# growth pipeline may still hold a temporary development paragraph here; that
# intermediate copy is replaced, not added to, at publication.
ETHOS_EN = (
    "The point is not to bring more people to one labyrinth. "
    "Cabo de Gata does not need more tourism pressure. "
    "Look more slowly. Learn from the people who live and work here. "
    "Leave the place as you found it."
)
if not replace_paragraph_by_markers(
    "en/index.html",
    (
        "The point is not to bring more people to one labyrinth.",
        "The aim is to look at Cabo de Gata more slowly",
        "Directions in development include field books for family visits",
        "They will grow slowly and will only be presented",
    ),
    ETHOS_EN,
):
    raise SystemExit("Could not locate the final English Cabo de Gata ethos paragraph")

# Keep the same project position visible in Spanish. Replace either the public
# voice paragraph or the temporary growth paragraph so the homepage carries one
# clear environmental statement rather than duplicate messaging.
ETHOS_ES = (
    "No se trata de llevar más gente al laberinto. "
    "Cabo de Gata no necesita más presión turística. "
    "Mira más despacio. Aprende de la gente que vive y trabaja aquí. "
    "Deja el lugar como lo encontraste."
)
if not replace_paragraph_by_markers(
    "index.html",
    (
        "No se trata de llevar más gente al laberinto.",
        "Se trata de mirar Cabo de Gata más despacio",
        "Entre las líneas en desarrollo hay cuadernos para recorrer el territorio en familia",
        "Crecerán despacio y sólo se presentarán",
    ),
    ETHOS_ES,
):
    raise SystemExit("Could not locate the final Spanish Cabo de Gata ethos paragraph")


# ABOUT — remove ambiguity and literal phrasing while keeping attribution and the
# stone / paper / code structure intact.
replace_state(
    "en/about/index.html",
    "OOLITA begins with a stone labyrinth laid by hand by Raquel Costantini at Los Escullos in September 2021.",
    "OOLITA begins with a stone labyrinth that Raquel Costantini laid by hand at Los Escullos in September 2021.",
)
replace_state(
    "en/about/index.html",
    "Hallazgo is their wider artistic practice.",
    "Hallazgo is Raquel Costantini’s wider artistic practice.",
)
replace_state(
    "en/about/index.html",
    "Code is the 3D world that will make it walkable in the browser.",
    "Code is the 3D world that will make the same path walkable in the browser.",
)
replace_state(
    "en/about/index.html",
    "None replaces the others.",
    "Each carries the same work in a different material.",
)
replace_state(
    "en/about/index.html",
    "Hallazgo works with observation, recording, found objects and landscape.",
    "Hallazgo works through observation, recording, found objects and landscape.",
)


# BOOK PAGE — editorial prose only. The bilingual literary excerpt is intentionally
# excluded: authored text is not normalised by this site-language pass.
replace_state(
    "en/editions/book/index.html",
    "Whoever reads in one language has the other in front of them, and that changes the pace of reading — you go more slowly, which is exactly what the text asks for.",
    "Reading one language with the other always in view changes the pace — you move more slowly, exactly as the text asks.",
)
replace_state(
    "en/editions/book/index.html",
    "How long it takes to arrive.",
    "Publication and delivery.",
)
replace_state(
    "en/editions/book/index.html",
    "Because it is printed one at a time, there is no stock to run out and no reprint to wait for. Each copy is produced after the order; printing and delivery details will be published before release.",
    "Each copy is printed to order, so there is no fixed stock or reprint cycle; printing and delivery details will be published before release.",
)


# OOID PAGE — inline markup can split rendered sentences. Work on the smallest
# stable fragments so the final visible English is corrected without touching links.
replace_fragment_if_present(
    "en/what-is-an-ooid/index.html",
    "sits still",
    "stays still",
)
replace_fragment_if_present(
    "en/what-is-an-ooid/index.html",
    "does not come out round.",
    "will not become round.",
)
replace_fragment_if_present(
    "en/what-is-an-ooid/index.html",
    "When the dune that hardened was a ",
    "When a ",
)
replace_fragment_if_present(
    "en/what-is-an-ooid/index.html",
    " rather than an underwater deposit, the technical name is ",
    " hardens into rock, the technical term is ",
)


# LABYRINTH PAGE — 'free to encounter' is a literal-sounding formulation in English.
replace_state(
    "en/labyrinth/index.html",
    "It is unstaffed, free to encounter and should be approached lightly and respectfully.",
    "It is unstaffed and free to visit; approach it lightly and with respect for the site.",
)


# Regression guard for only the constructions that are genuinely translation or
# clarity problems. Deliberate authorial negatives are explicitly allowed.
stale = {
    "en/index.html": (
        "whoever walks past either finds it or does not",
        "as two voices of one text — published by Vestini Tribe",
        "as long to read as the path takes to walk slowly",
        "stays open from elsewhere",
        "A labyrinth gives you one path to follow. You keep going.",
        "The aim is to look at Cabo de Gata more slowly",
        "Directions in development include field books for family visits",
    ),
    "index.html": (
        "Entre las líneas en desarrollo hay cuadernos para recorrer el territorio en familia",
    ),
    "en/about/index.html": (
        "laid by hand by Raquel Costantini",
        "Hallazgo is their wider artistic practice",
        "will make it walkable in the browser",
        "None replaces the others",
        "Hallazgo works with observation, recording, found objects and landscape",
    ),
    "en/editions/book/index.html": (
        "Whoever reads in one language has the other in front of them",
        "How long it takes to arrive.",
        "no stock to run out and no reprint to wait for",
    ),
    "en/what-is-an-ooid/index.html": (
        "sits still",
        "does not come out round",
        "When the dune that hardened was a",
        "rather than an underwater deposit, the technical name is",
    ),
    "en/labyrinth/index.html": ("free to encounter",),
}
for rel, phrases in stale.items():
    _, text = read(rel)
    for phrase in phrases:
        if phrase in text:
            raise SystemExit(f"Final-language regression remains in {rel}: {phrase}")

# Positive voice/ethos invariants.
for rel, needle in (
    ("en/index.html", "A labyrinth asks you to decide nothing. You follow."),
    ("en/index.html", ETHOS_EN),
    ("index.html", ETHOS_ES),
    ("en/what-is-an-ooid/index.html", "stays still"),
    ("en/what-is-an-ooid/index.html", "technical term is"),
):
    _, text = read(rel)
    if needle not in text:
        raise SystemExit(f"Final voice invariant missing in {rel}: {needle}")

print("OOLITA final language and author-voice pass applied and validated successfully.")
