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
        poster_number = int(item["asset"].split(":", 1)[1])
        thumbnail = f"https://oolita.es/carteles/img/cartel-{poster_number:02d}.png"
        cards.append(
            f'<article class="reel-card" id="{item["id"].lower()}">'
            f'<div class="reel-meta"><span>{html.escape(item["id"])}</span>'
            f'<time datetime="{html.escape(item["date"])}">{html.escape(item["date"])}</time></div>'
            f'<h2>{title}</h2><video controls preload="metadata" playsinline muted '
            f'poster="{thumbnail}" src="{item["video"]}"></video>'
            f'<p>{caption}</p></article>'
        )
        description = item["caption"].split("\n\n", 2)[1] if "\n\n" in item["caption"] else item["caption"]
        local_dt = datetime.combine(date.fromisoformat(item["date"]), time(19, 0), tzinfo=ZoneInfo("Europe/Madrid"))
        schema.append({
            "@type": "VideoObject",
            "name": item["title"],
            "description": description,
            "contentUrl": item["video"],
            "thumbnailUrl": thumbnail,
            "uploadDate": local_dt.isoformat(),
            "duration": "PT6S",
            "inLanguage": ["es", "en"],
        })

    schema_json = json.dumps({"@context": "https://schema.org", "@graph": schema}, ensure_ascii=False)
    page = (
        '<!doctype html><html lang="es"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>Los miércoles — nueve reels · OOLITA</title>'
        '<meta name="description" content="Nueve reels silenciosos de OOLITA: versiones en movimiento de los nueve carteles de apertura, publicados los miércoles de agosto a octubre de 2026.">'
        '<link rel="canonical" href="https://oolita.es/reels/">'
        '<link rel="alternate" hreflang="x-default" href="https://oolita.es/reels/">'
        '<meta property="og:type" content="website"><meta property="og:site_name" content="OOLITA">'
        '<meta property="og:locale" content="es_ES"><meta property="og:locale:alternate" content="en_GB">'
        '<meta property="og:title" content="Los miércoles — nueve reels · OOLITA">'
        '<meta property="og:description" content="Nueve carteles de apertura, puestos en movimiento. Un reel silencioso cada miércoles.">'
        '<meta property="og:url" content="https://oolita.es/reels/">'
        '<meta property="og:image" content="https://oolita.es/carteles/img/cartel-03.png">'
        '<meta property="og:image:alt" content="Cartel tipográfico de OOLITA para la serie de 22 domingos">'
        '<meta name="twitter:card" content="summary_large_image">'
        '<meta name="twitter:title" content="Los miércoles — nueve reels · OOLITA">'
        '<meta name="twitter:description" content="Nueve carteles de apertura, puestos en movimiento.">'
        '<meta name="twitter:image" content="https://oolita.es/carteles/img/cartel-03.png">'
        f'<script type="application/ld+json">{schema_json}</script>'
        '<style>@font-face{font-family:Instrument Sans;src:url(/fonts/instrument-sans-var-latin.woff2) format("woff2");font-weight:100 900;font-display:swap}'
        ':root{--paper:#f2eadb;--green:#2d4e23;--blue:#315fd5;--rule:rgba(45,78,35,.3)}*{box-sizing:border-box}'
        'body{margin:0;background:var(--paper);color:var(--green);font-family:"Instrument Sans",system-ui,sans-serif}'
        'a{color:inherit;text-underline-offset:.18em}.skip{position:absolute;left:-9999px}.skip:focus{left:1rem;top:1rem;background:var(--paper);padding:.75rem;z-index:10}'
        '.site-head,.site-foot{display:flex;justify-content:space-between;gap:1rem;padding:1rem clamp(1rem,3vw,2.5rem);border-bottom:1px solid var(--rule);font-size:.78rem;letter-spacing:.06em;text-transform:uppercase}'
        '.site-foot{border-top:1px solid var(--rule);border-bottom:0;flex-wrap:wrap;text-transform:none;letter-spacing:0}'
        'main{max-width:82rem;margin:auto;padding:clamp(2.5rem,7vw,7rem) clamp(1rem,4vw,3rem)}'
        '.eyebrow,.reel-meta{font-size:.72rem;font-weight:700;letter-spacing:.12em;text-transform:uppercase}'
        'h1{max-width:10ch;margin:.25em 0;font-size:clamp(4rem,12vw,10rem);line-height:.78;letter-spacing:-.065em}'
        '.lead{max-width:34rem;margin:2rem 0 5rem;font-size:clamp(1.2rem,2.2vw,1.8rem);line-height:1.25}'
        '.archive-links{display:flex;flex-wrap:wrap;gap:.7rem;margin-top:1.5rem}.archive-links a{display:inline-flex;align-items:center;min-height:2.75rem;padding:.65rem .85rem;border:1.5px solid currentColor;font-size:.78rem;font-weight:700;letter-spacing:.05em;text-decoration:none;text-transform:uppercase}'
        '.reels{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:clamp(2.5rem,6vw,6rem) clamp(1.5rem,4vw,4rem)}'
        '.reel-card{min-width:0;padding-top:1rem;border-top:1px solid var(--rule)}.reel-card:nth-child(3n){grid-column:1/-1;max-width:48rem;justify-self:center;width:100%}'
        '.reel-meta{display:flex;justify-content:space-between}.reel-card h2{max-width:18ch;margin:.7rem 0 1.2rem;font-size:clamp(1.6rem,3vw,3rem);line-height:.98;letter-spacing:-.035em}'
        'video{display:block;width:100%;aspect-ratio:9/16;max-height:78vh;background:#111;object-fit:contain}.reel-card p{max-width:42rem;line-height:1.55}'
        'a:focus-visible,video:focus-visible{outline:3px solid var(--blue);outline-offset:4px}'
        '@media(max-width:700px){.site-head{align-items:flex-start;flex-direction:column}.reels{grid-template-columns:1fr}.reel-card:nth-child(3n){grid-column:auto}.lead{margin-bottom:3.5rem}}</style>'
        '</head><body><a class="skip" href="#contenido">Saltar al contenido</a>'
        '<header class="site-head"><a href="/">OOLITA</a><span>Los Escullos · Cabo de Gata-Níjar</span><a href="/carteles/">Los nueve carteles</a></header>'
        '<main id="contenido"><span class="eyebrow">Archivo · agosto—octubre de 2026</span>'
        '<h1>Los miércoles</h1><p class="lead">Nueve carteles de apertura, puestos en movimiento. Un reel silencioso cada miércoles. Castellano e inglés comparten la misma imagen.</p>'
        '<nav class="archive-links" aria-label="Archivos relacionados"><a href="/carteles/">Los nueve carteles</a><a href="/domingos/">22 domingos</a></nav>'
        '<section class="reels" aria-label="Nueve reels">'
        + "".join(cards)
        + '</section></main><footer class="site-foot"><span>OOLITA reúne la obra y la escritura de Raquel Costantini con la labor editorial de Vestini Tribe.</span><a href="/privacidad/">Privacidad</a></footer></body></html>'
    )
    (outdir / "index.html").write_text(page, encoding="utf-8")


def add_archive_links() -> None:
    """Make the generated Reels page reachable from the public archive pages."""
    changes = {
        "index.html": (
            '  <a class="fila" href="/carteles/"><span class="n">07</span><span class="nom">Los carteles</span><span class="glo">Los nueve carteles de la apertura de la cuenta</span></a>',
            '  <a class="fila" href="/carteles/"><span class="n">07</span><span class="nom">Los carteles</span><span class="glo">Los nueve carteles de la apertura de la cuenta</span></a>\n  <a class="fila" href="/reels/"><span class="n">R</span><span class="nom">Los miércoles</span><span class="glo">Nueve carteles en movimiento · sin música</span></a>',
        ),
        "en/index.html": (
            '  <a class="fila" href="/en/posters/"><span class="n">07</span><span class="nom">The posters</span><span class="glo">The nine posters that opened the account</span></a>',
            '  <a class="fila" href="/en/posters/"><span class="n">07</span><span class="nom">The posters</span><span class="glo">The nine posters that opened the account</span></a>\n  <a class="fila" href="/reels/"><span class="n">R</span><span class="nom">The Wednesdays</span><span class="glo">Nine posters in motion · no music</span></a>',
        ),
        "carteles/index.html": (
            "Después de los carteles, una imagen cada domingo hasta la apertura:",
            'Los carteles también se mueven: <a href="/reels/">nueve reels silenciosos, uno cada miércoles</a>. Después de los carteles, una imagen cada domingo hasta la apertura:',
        ),
        "en/posters/index.html": (
            "After the posters, one image every Sunday until the opening:",
            'The posters also move: <a href="/reels/">nine silent reels, one each Wednesday</a>. After the posters, one image every Sunday until the opening:',
        ),
        "domingos/index.html": (
            "La serie no empezó aquí. Antes de los domingos hubo <a href=\"/carteles/\">nueve carteles</a>",
            'La serie no empezó aquí. Antes de los domingos hubo <a href="/carteles/">nueve carteles</a>, y esos carteles volvieron <a href="/reels/">en movimiento, uno cada miércoles</a>',
        ),
        "en/sundays/index.html": (
            "The series did not start here. Before the Sundays there were <a href=\"/en/posters/\">nine posters</a>",
            'The series did not start here. Before the Sundays there were <a href="/en/posters/">nine posters</a>, and those posters returned <a href="/reels/">in motion, one each Wednesday</a>',
        ),
    }
    for relative, (old, new) in changes.items():
        path = SITE / relative
        text = path.read_text(encoding="utf-8")
        if 'href="/reels/"' in text:
            continue
        if old not in text:
            raise SystemExit(f"Could not find Reels link anchor in {relative}")
        path.write_text(text.replace(old, new, 1), encoding="utf-8")


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
    add_archive_links()
    update_sitemap()
    print(f"Built {len(reels)} silent Wednesday poster reels in {outdir}")


if __name__ == "__main__":
    main()
