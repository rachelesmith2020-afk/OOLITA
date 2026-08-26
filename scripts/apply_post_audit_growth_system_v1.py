#!/usr/bin/env python3
"""Compatibility entry point for the post-audit OOLITA growth system."""
from pathlib import Path

# The final consistency workflow imports this v1 name. Execute the resilient
# implementation after adapting selectors to the links intentionally present on
# the published explainer pages. This changes no reader-facing copy or navigation.
path = Path(__file__).with_name("apply_post_audit_growth_system_v2.py")
source = path.read_text(encoding="utf-8")

# The two factual explainers lead into OOLITA through their existing final
# "Piedra, papel y código / Stone, paper and code" route, rather than by adding
# new navigation solely for measurement.
source = source.replace(
    '("que-es-un-laberinto/index.html","see-oolita-labyrinth","explainer-labyrinth",dict(href_exact="/laberinto/"),None,None),',
    '("que-es-un-laberinto/index.html","continue-into-oolita","explainer-oolita",dict(href_exact="/",text_contains="Piedra, papel y código"),None,None),',
)
source = source.replace(
    '("en/what-is-a-labyrinth/index.html","see-oolita-labyrinth","explainer-labyrinth",dict(href_exact="/en/labyrinth/"),None,None),',
    '("en/what-is-a-labyrinth/index.html","continue-into-oolita","explainer-oolita",dict(href_exact="/en/",text_contains="Stone, paper and code"),None,None),',
)
source = source.replace(
    '("que-es-un-oolito/index.html","see-place","ooid-cabo",dict(href_exact="/cabo-de-gata/"),None,None),',
    '("que-es-un-oolito/index.html","continue-into-oolita","ooid-oolita",dict(href_exact="/",text_contains="Piedra, papel y código"),None,None),',
)
source = source.replace(
    '("en/what-is-an-ooid/index.html","see-place","ooid-cabo",dict(href_exact="/en/cabo-de-gata/"),None,None),',
    '("en/what-is-an-ooid/index.html","continue-into-oolita","ooid-oolita",dict(href_exact="/en/",text_contains="Stone, paper and code"),None,None),',
)

# Measure the same published geology path: ooid explainer -> OOLITA -> labyrinth
# -> remote 3D follow. The homepage-to-labyrinth click is added as a measured edge.
source = source.replace(
    '("que-es-un-oolito/index.html","ooid-cabo",dict(href_exact="/cabo-de-gata/")),',
    '("que-es-un-oolito/index.html","ooid-oolita",dict(href_exact="/",text_contains="Piedra, papel y código")),',
)
source = source.replace(
    '("en/what-is-an-ooid/index.html","ooid-cabo",dict(href_exact="/en/cabo-de-gata/")),',
    '("en/what-is-an-ooid/index.html","ooid-oolita",dict(href_exact="/en/",text_contains="Stone, paper and code")),',
)
source = source.replace(
    '("index.html","home-about",dict(href_exact="/sobre-oolita/")),',
    '("index.html","home-about",dict(href_exact="/sobre-oolita/")),\n    ("index.html","home-labyrinth",dict(href_exact="/laberinto/")),',
)
source = source.replace(
    '("en/index.html","home-about",dict(href_exact="/en/about/")),',
    '("en/index.html","home-about",dict(href_exact="/en/about/")),\n    ("en/index.html","home-labyrinth",dict(href_exact="/en/labyrinth/")),',
)
source = source.replace(
    '"geology-es": [("que-es-un-oolito/index.html","/cabo-de-gata/"),("cabo-de-gata/index.html","/laberinto/"),("laberinto/index.html","follow=3d")],',
    '"geology-es": [("que-es-un-oolito/index.html","/"),("index.html","/laberinto/"),("laberinto/index.html","follow=3d")],',
)
source = source.replace(
    '"geology-en": [("en/what-is-an-ooid/index.html","/en/cabo-de-gata/"),("en/cabo-de-gata/index.html","/en/labyrinth/"),("en/labyrinth/index.html","follow=3d")],',
    '"geology-en": [("en/what-is-an-ooid/index.html","/en/"),("en/index.html","/en/labyrinth/"),("en/labyrinth/index.html","follow=3d")],',
)

exec(compile(source, str(path), "exec"), globals(), globals())
