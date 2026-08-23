#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import subprocess
import sys
from datetime import date, datetime, time
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
SITE = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "site"
META = ROOT / "social" / "wednesday_reels.json"
FPS = 24
DURATION = 6
FRAMES = FPS * DURATION


def run(cmd: list[str]) -> None:
    print("+", " ".join(cmd[:8]), "..." if len(cmd) > 8 else "")
    subprocess.run(cmd, check=True)


def make_poster_reel(src: Path, out: Path) -> None:
    # Keep the complete 4:5 poster centred in 9:16. The top/bottom extension is
    # made by smearing the poster's flat edge colour, so no new graphic device
    # is introduced. Movement is deliberately almost imperceptible (1.5%).
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


def build_index(data: dict, outdir: Path) -> None:
    reels = data["reels"]
    public = {
        "series": data["series"],
        "audio": data["audio"],
        "timezone": data["timezone"],
        "publish_time": data["publish_time"],
        "reels": [
            {**x, "video": f"https://oolita.es/reels/{x['id'].lower()}.mp4"}
            for x in reels
        ],
    }
    (outdir / "index.json").write_text(
        json.dumps(public, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    cards: list[str] = []
    schema: list[dict] = []
    for item in public["reels"]:
        title = html.escape(item["title"])
        caption = html.escape(item["caption"]).replace("\n", "<br>")
        cards.append(
            f'<article><h2>{title}</h2><video controls preload="metadata" playsinline muted '
            f'src="{item["video"]}"></video><p>{caption}</p></article>'
        )
        description = item["caption"].split("\n\n", 2)[1] if "\n\n" in item["caption"] else item["caption"]
        local_dt = datetime.combine(date.fromisoformat(item["date"]), time(19, 0), tzinfo=ZoneInfo("Europe/Madrid"))
        schema.append({
            "@type": "VideoObject",
            "name": item["title"],
            "description": description,
            "contentUrl": item["video"],
            "uploadDate": local_dt.isoformat(),
            "inLanguage": ["es", "en"],
        })

    schema_json = json.dumps({"@context": "https://schema.org", "@graph": schema}, ensure_ascii=False)
    page = (
        '<!doctype html><html lang="es"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>Los miércoles · OOLITA</title>'
        '<meta name="description" content="Nueve reels silenciosos de OOLITA: los nueve carteles, de agosto a octubre de 2026.">'
        '<link rel="canonical" href="https://oolita.es/reels/">'
        f'<script type="application/ld+json">{schema_json}</script>'
        '<style>body{margin:0;background:#F2EADB;color:#2D4E23;font-family:system-ui,sans-serif}'
        'main{max-width:760px;margin:auto;padding:32px 20px}'
        'h1{font-size:clamp(2.4rem,8vw,5rem);line-height:.9}'
        'article{padding:34px 0;border-top:1px solid #2D4E2344}'
        'video{width:100%;max-height:78vh;background:#111}p{line-height:1.55}</style>'
        '</head><body><main><p>OOLITA · Los Escullos · Cabo de Gata-Níjar</p>'
        '<h1>Los miércoles</h1><p>Nueve carteles. Nueve miércoles. Sin música.</p>'
        + "".join(cards)
        + '</main><footer><span>OOLITA · Un proyecto de Vestini Tribe · Raquel Costantini, artista y autora</span></footer></body></html>'
    )
    (outdir / "index.html").write_text(page, encoding="utf-8")


def update_sitemap() -> None:
    sitemap = SITE / "sitemap.xml"
    if not sitemap.exists():
        return
    text = sitemap.read_text(encoding="utf-8")
    if "https://oolita.es/reels/" not in text:
        entry = "  <url><loc>https://oolita.es/reels/</loc><lastmod>2026-08-23</lastmod></url>\n"
        text = text.replace("</urlset>", entry + "</urlset>")
        sitemap.write_text(text, encoding="utf-8")


def main() -> None:
    data = json.loads(META.read_text(encoding="utf-8"))
    reels = data["reels"]
    if len(reels) != 9:
        raise SystemExit(f"Expected 9 Wednesday poster reels, found {len(reels)}")
    if any(not item.get("approved") for item in reels):
        raise SystemExit("Every scheduled poster reel must be explicitly approved")
    if any(not item.get("asset", "").startswith("poster:") for item in reels):
        raise SystemExit("Wednesday bank currently allows poster reels only")

    outdir = SITE / "reels"
    outdir.mkdir(parents=True, exist_ok=True)

    # Remove any old generated reel MP4s first, including the rejected R10-R19 batch.
    for old in outdir.glob("r*.mp4"):
        old.unlink()

    for item in reels:
        rid = item["id"].lower()
        _, value = item["asset"].split(":", 1)
        src = SITE / "carteles" / "img" / f"cartel-{int(value):02d}.png"
        if not src.is_file():
            raise SystemExit(f"Missing poster source: {src}")
        out = outdir / f"{rid}.mp4"
        make_poster_reel(src, out)
        if out.stat().st_size < 10000:
            raise SystemExit(f"Reel output unexpectedly small: {out}")

    build_index(data, outdir)
    update_sitemap()
    print(f"Built {len(reels)} silent Wednesday poster reels in {outdir}")


if __name__ == "__main__":
    main()
