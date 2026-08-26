#!/usr/bin/env python3
"""Compatibility entry point for the post-audit OOLITA growth system."""
from pathlib import Path

# The final consistency workflow imports this v1 name. Execute the resilient
# implementation after adapting two primary-action selectors to the links that
# are intentionally present on the current explainer pages. This changes no
# reader-facing copy or navigation.
path = Path(__file__).with_name("apply_post_audit_growth_system_v2.py")
source = path.read_text(encoding="utf-8")
source = source.replace(
    '("que-es-un-laberinto/index.html","see-oolita-labyrinth","explainer-labyrinth",dict(href_exact="/laberinto/"),None,None),',
    '("que-es-un-laberinto/index.html","continue-into-oolita","explainer-oolita",dict(href_exact="/"),None,None),',
)
source = source.replace(
    '("en/what-is-a-labyrinth/index.html","see-oolita-labyrinth","explainer-labyrinth",dict(href_exact="/en/labyrinth/"),None,None),',
    '("en/what-is-a-labyrinth/index.html","continue-into-oolita","explainer-oolita",dict(href_exact="/en/"),None,None),',
)
exec(compile(source, str(path), "exec"), globals(), globals())
