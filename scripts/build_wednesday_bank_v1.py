#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "site"
META = ROOT / "social" / "wednesday_reels.json"
FPS = 24
DURATION = 6
FRAMES = FPS * DURATION


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def make_poster_reel(src: Path, out: Path) -> None:
    vf = (
        "scale=1080:1350:flags=lanczos,"
        "pad=1080:1920:0:285:color=black,"
        "fillborders=top=285:bottom=285:mode=smear,"
        "zoompan=z='1+0.015*on/143':"
        "x='iw/2-(iw/zoom/2)':"
        "y='ih/2-(ih/zoom/2)':"
        f"d={FRAMES}:s=1080x1920:fps={FPS},format=yuv420p"
    )
    run([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-loop", "1", "-i", str(src),
        "-vf", vf,
        "-t", str(DURATION), "-an",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(out),
    ])


def main() -> None:
    data = json.loads(META.read_text(encoding="utf-8"))
    reels = data.get("reels", [])
    if len(reels) != 9:
        raise SystemExit(f"Expected exactly R01-R09, found {len(reels)} entries")
    expected_ids = [f"R{i:02d}" for i in range(1, 10)]
    if [item.get("id") for item in reels] != expected_ids:
        raise SystemExit("Wednesday bank must contain exactly R01-R09 in order")
    if any(item.get("approved") is not True for item in reels):
        raise SystemExit("Every Wednesday bank entry must contain approved: true")
    if any(not str(item.get("asset", "")).startswith("poster:") for item in reels):
        raise SystemExit("Wednesday bank accepts poster assets only")

    outdir = SITE / "reels"
    outdir.mkdir(parents=True, exist_ok=True)
    for old in outdir.glob("r*.mp4"):
        old.unlink()

    public_reels = []
    for item in reels:
        rid = item["id"].lower()
        poster_number = int(item["asset"].split(":", 1)[1])
        src = SITE / "carteles" / "img" / f"cartel-{poster_number:02d}.png"
        if not src.is_file():
            raise SystemExit(f"Missing approved poster source: {src}")
        out = outdir / f"{rid}.mp4"
        make_poster_reel(src, out)
        if out.stat().st_size < 10000:
            raise SystemExit(f"Approved MP4 output unexpectedly small: {out}")
        public_reels.append({**item, "video": f"https://oolita.es/reels/{rid}.mp4"})

    bank = {
        "account": data.get("account"),
        "timezone": data.get("timezone"),
        "publish_time": data.get("publish_time"),
        "spain_time": data.get("spain_time"),
        "series": data.get("series"),
        "audio": data.get("audio"),
        "reels": public_reels,
    }
    (outdir / "index.json").write_text(
        json.dumps(bank, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    # This is a machine-readable publishing bank, not a public archive page.
    index_html = outdir / "index.html"
    if index_html.exists():
        index_html.unlink()
    print("Built approved Wednesday bank: R01-R09, JSON + nine MP4s")


if __name__ == "__main__":
    main()
