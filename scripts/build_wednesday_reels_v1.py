#!/usr/bin/env python3
from __future__ import annotations

import base64
import binascii
import html
import json
import subprocess
import sys
import tempfile
from datetime import date, datetime, time
from zoneinfo import ZoneInfo
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "site"
META = ROOT / "social" / "wednesday_reels.json"
ROOM_PARTS = [ROOT / "social" / f"reel_room_{i:02d}.b64" for i in range(1, 4)]
SHELF_SOURCE = ROOT / "social" / "reel_shelf.b64"
COVERS_SOURCE = ROOT / "social" / "reel_covers.json"
FPS = 24
DURATION = 6
FRAMES = FPS * DURATION
PAPER = "0xF2EADB"


def run(cmd: list[str]) -> None:
    print("+", " ".join(cmd[:8]), "..." if len(cmd) > 8 else "")
    subprocess.run(cmd, check=True)


def audio_graph() -> str:
    # OOLITA's synthetic levante bed: brown noise plus the two documented
    # material tones (stone 125 Hz, canvas 520 Hz), kept deliberately low.
    return (
        f"anoisesrc=color=brown:amplitude=0.025:duration={DURATION}:sample_rate=44100[noise];"
        f"sine=frequency=125:sample_rate=44100:duration={DURATION}[stone];"
        f"sine=frequency=520:sample_rate=44100:duration={DURATION}[canvas];"
        "[stone]volume=0.012[s1];[canvas]volume=0.006[s2];"
        "[noise][s1][s2]amix=inputs=3:normalize=0,highpass=f=55,lowpass=f=1800[a]"
    )


def encode(src: Path, out: Path, vf: str) -> None:
    fc = f"[0:v]{vf}[v];{audio_graph()}"
    run([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-loop", "1", "-i", str(src),
        "-filter_complex", fc,
        "-map", "[v]", "-map", "[a]", "-t", str(DURATION),
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "24",
        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "96k",
        "-movflags", "+faststart", str(out),
    ])


def make_fit(src: Path, out: Path, width: int = 940) -> None:
    # Whole artwork remains visible; the movement is a small reading drift.
    vf = (
        f"scale={width}:-2:flags=lanczos,"
        f"pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color={PAPER},"
        "zoompan=z='1+0.00042*on':"
        "x='iw/2-(iw/zoom/2)':"
        f"y='(ih-ih/zoom)*on/{FRAMES-1}':"
        f"d={FRAMES}:s=1080x1920:fps={FPS},format=yuv420p"
    )
    encode(src, out, vf)


def make_pan(src: Path, out: Path, start: float, end: float) -> None:
    # Full-height traverse across the room from lamp to table.
    vf = (
        "scale=-2:1920:flags=lanczos,"
        f"crop=1080:1920:x='(iw-1080)*({start}+({end}-{start})*t/{DURATION})':y=0,"
        f"fps={FPS},format=yuv420p"
    )
    encode(src, out, vf)


def make_focus(src: Path, out: Path, xfrac: float) -> None:
    vf = (
        "scale=-2:1920:flags=lanczos,"
        f"crop=1080:1920:x='(iw-1080)*{xfrac}':y=0,"
        "zoompan=z='1+0.00032*on':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
        f"d={FRAMES}:s=1080x1920:fps={FPS},format=yuv420p"
    )
    encode(src, out, vf)


def _valid_media(path: Path) -> bool:
    probe = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(path), "-f", "null", "-"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return probe.returncode == 0


def decode_b64(text: str, target: Path) -> None:
    """Decode a banked image strictly; repair only a single proven stray char.

    One historical shelf source was committed with one extra base64 data
    character. We do not synthesize or pad image bytes. If strict decoding
    fails with the characteristic 1-mod-4 length, try deleting one encoded
    character, require JPEG SOI/EOI markers, then require ffmpeg to decode the
    recovered image cleanly. Any other corruption still fails the build.
    """
    clean = "".join(text.split())
    try:
        target.write_bytes(base64.b64decode(clean, validate=True))
        if not _valid_media(target):
            raise SystemExit(f"Decoded media is not valid: {target}")
        return
    except binascii.Error as exc:
        if len(clean) % 4 != 1:
            raise SystemExit(f"Invalid base64 source for {target}: {exc}") from exc

    # Search from the tail first because the malformed source entered the repo
    # through a bounded text write. Only a candidate that is a complete JPEG
    # and decodes cleanly through ffmpeg is accepted.
    for i in range(len(clean) - 1, -1, -1):
        candidate = clean[:i] + clean[i + 1:]
        try:
            data = base64.b64decode(candidate, validate=True)
        except binascii.Error:
            continue
        if not (data.startswith(b"\xff\xd8") and data.endswith(b"\xff\xd9")):
            continue
        target.write_bytes(data)
        if _valid_media(target):
            print(f"repaired one stray base64 character in {target.name} at encoded index {i}")
            return

    raise SystemExit(f"Could not conservatively repair malformed base64 source for {target}")


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
            f'<article><h2>{title}</h2><video controls preload="metadata" playsinline '
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
        '<meta name="description" content="Diecinueve reels de OOLITA: los nueve carteles y El Abrigo de la Duna, de agosto a diciembre de 2026.">'
        '<link rel="canonical" href="https://oolita.es/reels/">'
        f'<script type="application/ld+json">{schema_json}</script>'
        '<style>body{margin:0;background:#F2EADB;color:#2D4E23;font-family:system-ui,sans-serif}'
        'main{max-width:760px;margin:auto;padding:32px 20px}'
        'h1{font-size:clamp(2.4rem,8vw,5rem);line-height:.9}'
        'article{padding:34px 0;border-top:1px solid #2D4E2344}'
        'video{width:100%;max-height:78vh;background:#111}p{line-height:1.55}</style>'
        '</head><body><main><p>OOLITA · Los Escullos · Cabo de Gata-Níjar</p>'
        '<h1>Los miércoles</h1><p>Domingo: la imagen. Miércoles: el movimiento.</p>'
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
    if len(reels) != 19:
        raise SystemExit(f"Expected 19 Wednesday reels, found {len(reels)}")

    outdir = SITE / "reels"
    outdir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="oolita-reels-") as td:
        tmp = Path(td)
        hero = tmp / "abrigo-room.jpg"
        shelf = tmp / "abrigo-shelf.jpg"
        room_b64 = "".join(p.read_text(encoding="utf-8").strip() for p in ROOM_PARTS)
        decode_b64(room_b64, hero)
        decode_b64(SHELF_SOURCE.read_text(encoding="utf-8").strip(), shelf)
        covers = json.loads(COVERS_SOURCE.read_text(encoding="utf-8"))
        cover_files = {}
        for name, svg in covers.items():
            cp = tmp / f"{name}.svg"
            cp.write_text(svg, encoding="utf-8")
            cover_files[name] = cp

        for item in reels:
            rid = item["id"].lower()
            out = outdir / f"{rid}.mp4"
            kind, value = item["asset"].split(":", 1)
            if kind == "poster":
                src = SITE / "carteles" / "img" / f"cartel-{int(value):02d}.png"
                if not src.is_file():
                    raise SystemExit(f"Missing poster source: {src}")
                make_fit(src, out, width=960)
            elif kind == "abrigo" and value == "room":
                make_fit(hero, out, width=1020)
            elif kind == "abrigo" and value == "design":
                make_pan(hero, out, 0.02, 0.72)
            elif kind == "abrigo" and value == "yaz":
                make_focus(hero, out, 0.33)
            elif kind == "abrigo" and value == "shelf":
                make_fit(shelf, out, width=1020)
            elif kind == "cover":
                src = cover_files.get(value)
                if src is None:
                    raise SystemExit(f"Missing cover source: {value}")
                make_fit(src, out, width=760)
            else:
                raise SystemExit(f"Unsupported reel asset {item['asset']}")

            if out.stat().st_size < 10000:
                raise SystemExit(f"Reel output unexpectedly small: {out}")

    build_index(data, outdir)
    update_sitemap()
    print(f"Built {len(reels)} Wednesday reels in {outdir}")


if __name__ == "__main__":
    main()
