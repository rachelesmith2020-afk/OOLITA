#!/usr/bin/env python3
"""Final visual cleanup for OOLITA after the contemporary-art restage.

Prevents hero typography collisions and regularises mobile spacing without
undoing the poster-scale art direction or changing content/SEO/navigation.
"""
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
STYLE_ID = "oolita-visual-spacing-cleanup-v1"
STYLE = r'''<style id="oolita-visual-spacing-cleanup-v1">
/* Hero: dramatic, but never colliding. */
body.art-home h1{
  font-size:clamp(5rem,15vw,12.5rem)!important;
  line-height:.78!important;
  letter-spacing:-.055em!important;
  margin:.12em 0 .28em!important;
  position:relative!important;
  z-index:1!important;
}
body.art-home .art-manifesto{
  position:relative!important;
  z-index:2!important;
  max-width:14ch!important;
  margin:0 0 clamp(3rem,7vw,6rem)!important;
  font-size:clamp(2.35rem,5.5vw,5.2rem)!important;
  line-height:.96!important;
  letter-spacing:-.03em!important;
}
body.art-home .art-manifesto.art-manifesto--echo{
  max-width:23ch!important;
  margin:0 0 clamp(4rem,8vw,7rem) min(28vw,20rem)!important;
  font-size:clamp(1.15rem,2vw,1.8rem)!important;
  line-height:1.15!important;
}

/* Keep content rhythm legible between the large art fields. */
body.art-restaged main > section{scroll-margin-top:5rem}
body.art-home main > section{margin-block:clamp(3.5rem,8vw,8rem)!important}
body.art-home .art-field{min-height:min(66vh,680px)!important}
body.art-home p.parr{margin-top:1.1rem;margin-bottom:1.5rem}
body.art-restaged h1,body.art-restaged h2,body.art-restaged h3{overflow-wrap:anywhere}
body.art-restaged p,body.art-restaged li{overflow-wrap:break-word}

/* Interior pages: consistent air around headings and prose. */
body.art-restaged:not(.art-home) main > section{margin-block:clamp(2.5rem,6vw,5.5rem)}
body.art-restaged:not(.art-home) h1{margin-bottom:clamp(1.5rem,4vw,3rem)!important}
body.art-restaged:not(.art-home) h2{margin-top:clamp(2.5rem,6vw,5rem)!important;margin-bottom:1.1rem!important}

@media(max-width:760px){
  /* Mobile homepage: no text overlap, no off-screen echo, balanced breathing room. */
  body.art-home h1{
    font-size:clamp(4.5rem,23vw,7.2rem)!important;
    line-height:.82!important;
    letter-spacing:-.05em!important;
    margin:.12em 0 .32em!important;
  }
  body.art-home .art-manifesto{
    max-width:12ch!important;
    margin:0 0 2.5rem!important;
    font-size:clamp(2.2rem,10.5vw,3.6rem)!important;
    line-height:.98!important;
  }
  body.art-home .art-manifesto.art-manifesto--echo{
    max-width:22ch!important;
    margin:0 0 3.75rem 12vw!important;
    font-size:clamp(1.05rem,4.8vw,1.35rem)!important;
    line-height:1.18!important;
  }
  body.art-home main > section{margin-block:3rem!important}
  body.art-home .art-field{min-height:56svh!important;padding:1.25rem!important}
  body.art-home .art-field--stone{padding-top:42svh!important}
  body.art-home .art-field-photo{height:40svh!important}
  body.art-home .art-field--stone::after{inset:26svh 0 auto 0!important;height:16svh!important}
  body.art-home .art-field .art-word{font-size:clamp(4.8rem,28vw,8rem)!important;line-height:.68!important}
  body.art-home .art-field--stone .art-word{font-size:clamp(4rem,21vw,6.6rem)!important}
  body.art-home .art-caption{margin-top:1rem!important;font-size:1rem!important;line-height:1.4!important}
  body.art-home a.fila{padding-block:1.15rem!important}
  body.art-home a.fila .n{font-size:clamp(2.4rem,13vw,4rem)!important}
  body.art-home .menu-group-label{margin-top:3.2rem!important}
  body.art-home p.parr{font-size:1.05rem!important;line-height:1.55!important;margin:0 0 1.35rem!important}

  /* All mobile pages: avoid cramped edges and excessive vertical voids. */
  body.art-restaged:not(.art-home) h1{
    font-size:clamp(2.8rem,15vw,5rem)!important;
    line-height:.92!important;
    margin-bottom:1.5rem!important;
  }
  body.art-restaged:not(.art-home) h2{
    font-size:clamp(2rem,10vw,3.2rem)!important;
    line-height:1!important;
    margin-top:2.8rem!important;
    margin-bottom:1rem!important;
  }
  body.art-restaged:not(.art-home) main > section{margin-block:2.6rem!important}
  body.art-restaged figure{margin-block:2.4rem!important}
  body.art-restaged figcaption{margin-top:.65rem!important;font-size:.75rem!important}
}

@media(max-width:420px){
  body.art-home h1{font-size:clamp(4.1rem,21vw,6rem)!important}
  body.art-home .art-manifesto{font-size:clamp(2rem,10vw,3rem)!important}
  body.art-home .art-manifesto.art-manifesto--echo{margin-left:7vw!important}
  body.art-home .art-field{min-height:52svh!important}
}
</style>'''

if not ROOT.is_dir():
    raise SystemExit(f"Missing built site: {ROOT}")
html_files = sorted(ROOT.rglob("*.html"))
if not html_files:
    raise SystemExit("No HTML pages found")

for target in html_files:
    html = target.read_text(encoding="utf-8")
    if f'id="{STYLE_ID}"' in html:
        continue
    if "</head>" not in html:
        raise SystemExit(f"Missing </head>: {target.relative_to(ROOT)}")
    html = html.replace("</head>", STYLE + "\n</head>", 1)
    target.write_text(html, encoding="utf-8")

for rel in ("index.html", "en/index.html"):
    target = ROOT / rel
    html = target.read_text(encoding="utf-8")
    if STYLE_ID not in html or "art-manifesto" not in html or "art-home" not in html:
        raise SystemExit(f"Visual spacing cleanup invariant failed: {rel}")

print(f"OOLITA visual overlap and mobile spacing cleanup validated across {len(html_files)} HTML pages.")
