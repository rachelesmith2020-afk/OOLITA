#!/usr/bin/env python3
"""Activate OOLITA's first-party Cloudflare Follow form.

Kept under the existing pipeline filename so current deploy ordering remains
stable. The implementation lives in apply_cloudflare_follow_v1.py.
"""
from pathlib import Path
import subprocess
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
subprocess.run([sys.executable, "scripts/apply_cloudflare_follow_v1.py", str(ROOT)], check=True)
print("OOLITA Follow Cloudflare activation validated successfully.")
