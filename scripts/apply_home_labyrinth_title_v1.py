"""Apply the user-approved title to the English homepage's labyrinth section."""
from pathlib import Path
import re
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
page = root / "en/index.html"
source = page.read_bytes()
heading = re.compile(rb'(<h2\b[^>]*>)(Los Escullos|Oolita)(</h2>)')
matches = list(heading.finditer(source))
if len(matches) != 1:
    raise SystemExit(f"Expected one homepage labyrinth heading; found {len(matches)}")
result = heading.sub(rb'\g<1>Oolita\g<3>', source)
if result != source:
    page.write_bytes(result)
print("English homepage labyrinth title: Oolita; markup and other content preserved.")
