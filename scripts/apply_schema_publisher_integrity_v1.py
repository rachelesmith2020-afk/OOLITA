#!/usr/bin/env python3
"""Remove incomplete Vestini Tribe publisher Organization objects from JSON-LD.

The visible publishing credit remains in page copy. We deliberately do not
invent a publisher logo merely to satisfy structured-data tooling. Schema.org's
publisher property expects a Person or Organization, so replacing the object
with a plain string would be invalid; omission is the accurate fallback until
an authoritative Vestini Tribe logo asset exists.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
SCRIPT_RE = re.compile(
    r'(<script\b[^>]*\btype\s*=\s*["\']application/ld\+json["\'][^>]*>)(.*?)(</script>)',
    flags=re.I | re.S,
)

removed = 0
changed_files = 0


def is_incomplete_vestini_org(value: object) -> bool:
    if not isinstance(value, dict):
        return False
    raw_type = value.get("@type")
    types = {raw_type} if isinstance(raw_type, str) else set(raw_type or []) if isinstance(raw_type, list) else set()
    return (
        "Organization" in types
        and value.get("name") == "Vestini Tribe"
        and not value.get("logo")
    )


def clean(node: object) -> object:
    global removed
    if isinstance(node, dict):
        out = {}
        for key, value in node.items():
            if key == "publisher" and is_incomplete_vestini_org(value):
                removed += 1
                continue
            out[key] = clean(value)
        return out
    if isinstance(node, list):
        return [clean(value) for value in node]
    return node


def contains_incomplete_vestini_org(node: object) -> bool:
    if is_incomplete_vestini_org(node):
        return True
    if isinstance(node, dict):
        return any(contains_incomplete_vestini_org(value) for value in node.values())
    if isinstance(node, list):
        return any(contains_incomplete_vestini_org(value) for value in node)
    return False


for path in ROOT.rglob("*.html"):
    text = path.read_text(encoding="utf-8")
    touched = False

    def rewrite(match: re.Match[str]) -> str:
        nonlocal_touched = False
        raw = match.group(2).strip()
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            if "Vestini Tribe" in raw and "Organization" in raw:
                raise SystemExit(f"Unparseable relevant JSON-LD in {path}: {exc}")
            return match.group(0)
        before = json.dumps(payload, ensure_ascii=False, sort_keys=True)
        cleaned = clean(payload)
        after = json.dumps(cleaned, ensure_ascii=False, sort_keys=True)
        if before == after:
            return match.group(0)
        nonlocal_touched = True
        if nonlocal_touched:
            nonlocal touched
            touched = True
        return match.group(1) + json.dumps(cleaned, ensure_ascii=False, separators=(",", ":")) + match.group(3)

    updated = SCRIPT_RE.sub(rewrite, text)
    if touched:
        path.write_text(updated, encoding="utf-8")
        changed_files += 1

if removed == 0:
    raise SystemExit("No incomplete Vestini Tribe publisher Organization objects found; refusing silent no-op")

for path in ROOT.rglob("*.html"):
    text = path.read_text(encoding="utf-8")
    for match in SCRIPT_RE.finditer(text):
        raw = match.group(2).strip()
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if contains_incomplete_vestini_org(payload):
            raise SystemExit(f"Incomplete Vestini Tribe Organization remains in {path}")

print(f"Structured-data publisher repair: removed {removed} incomplete Organization object(s) across {changed_files} HTML file(s)")
