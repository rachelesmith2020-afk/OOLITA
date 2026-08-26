#!/usr/bin/env python3
"""Apply a narrow native-English editorial pass to OOLITA.

This script corrects reader-facing English that is grammatically understandable but
carries Spanish syntax too literally. It deliberately leaves authored literary text,
functional microcopy and factual terminology alone unless the English itself is the
problem. The pass is idempotent and runs at the final pre-publish stage.
"""
from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")


def read(rel: str) -> tuple[Path, str]:
    path = ROOT / rel
    if not path.is_file():
        raise SystemExit(f"Missing English editorial page: {rel}")
    return path, path.read_text(encoding="utf-8")


def replace_state(rel: str, old: str, new: str) -> None:
    path, text = read(rel)
    if old in text:
        path.write_text(text.replace(old, new), encoding="utf-8")
        return
    if new in text:
        return
    raise SystemExit(f"Neither source nor revised English found in {rel}: {old!r}")


# HOMEPAGE — preserve OOLITA's short cadence while removing English constructions
# that read as direct transfers from Spanish.
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
replace_state(
    "en/index.html",
    "A labyrinth asks you to decide nothing. You follow.",
    "A labyrinth gives you one path to follow. You keep going.",
)
replace_state(
    "en/index.html",
    "There will still be one OOLITA labyrinth: the one at Los Escullos. Around it will come field publications, small textile editions and collaborations made in Cabo de Gata.",
    "OOLITA will continue to have one labyrinth: the one at Los Escullos. Around it, the project will grow through field publications, small textile editions and collaborations made in Cabo de Gata.",
)
replace_state(
    "en/index.html",
    "The point is not to bring more people to one labyrinth. It is to look at Cabo de Gata more slowly, learn from the people who live and work here, and leave the land as you found it.",
    "The aim is to look at Cabo de Gata more slowly, learn from the people who live and work here, and leave the land as you found it.",
)


# ABOUT — remove ambiguous reference and literal phrasing while keeping attribution
# and the stone / paper / code structure exactly intact.
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
    "Each copy is printed to order, so there is no fixed stock or reprint cycle. Printing and delivery details will be published before release.",
)


# OOID PAGE — make the prose idiomatic without changing the geological claim.
replace_state(
    "en/what-is-an-ooid/index.html",
    "A grain that sits still does not come out round.",
    "A grain that stays still will not become round.",
)
replace_state(
    "en/what-is-an-ooid/index.html",
    "When the dune that hardened was a wind-blown dune rather than an underwater deposit, the technical name is ",
    "When a wind-blown carbonate dune hardens into rock, the technical term is ",
)


# LABYRINTH PAGE — 'free to encounter' is a literal-sounding formulation in English.
replace_state(
    "en/labyrinth/index.html",
    "It is unstaffed, free to encounter and should be approached lightly and respectfully.",
    "It is unstaffed and free to visit; approach it lightly and with respect for the site.",
)


# Regression guard for the exact translated constructions addressed here. Do not
# prohibit all negative language: functional negatives remain legitimate elsewhere.
stale = {
    "en/index.html": (
        "whoever walks past either finds it or does not",
        "as two voices of one text — published by Vestini Tribe",
        "as long to read as the path takes to walk slowly",
        "stays open from elsewhere",
        "asks you to decide nothing",
        "Around it will come field publications",
        "The point is not to bring more people to one labyrinth",
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
        "sits still does not come out round",
        "When the dune that hardened was a wind-blown dune",
    ),
    "en/labyrinth/index.html": ("free to encounter",),
}
for rel, phrases in stale.items():
    _, text = read(rel)
    for phrase in phrases:
        if phrase in text:
            raise SystemExit(f"Literal-English regression remains in {rel}: {phrase}")

print("OOLITA native-English editorial pass applied and validated successfully.")
