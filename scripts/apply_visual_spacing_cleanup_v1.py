#!/usr/bin/env python3
"""Final visual cleanup for OOLITA after the contemporary-art restage.

Prevents hero typography collisions and regularises mobile spacing without
undoing the poster-scale art direction or changing content/SEO/navigation.
The style block is replaced on every run so a mirrored live origin cannot keep
an obsolete copy of this final visual layer.
"""
from __future__ import annotations

from pathlib import Path
import re
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

/* Stone field: keep the title on one line and keep the kicker out of it.
   The old art-restage rule used 14vw here, which breaks PIEDRA around laptop widths. */
body.art-home #oolita-art-field-stone{
  grid-template-columns:minmax(0,1.15fr) minmax(15rem,.85fr)!important;
  gap:clamp(1.5rem,4vw,4rem)!important;
  padding:clamp(2.25rem,5vw,4.5rem)!important;
  align-items:end!important;
}
body.art-home #oolita-art-field-stone .art-copy{
  width:100%!important;
  max-width:44rem!important;
  align-self:end!important;
}
body.art-home #oolita-art-field-stone .art-kicker{
  position:static!important;
  inset:auto!important;
  display:block!important;
  margin:0 0 1.1rem!important;
  font-size:clamp(.72rem,.9vw,.86rem)!important;
  line-height:1.2!important;
  letter-spacing:.14em!important;
}
body.art-home #oolita-art-field-stone .art-word{
  max-width:100%!important;
  margin:0!important;
  white-space:nowrap!important;
  overflow-wrap:normal!important;
  word-break:keep-all!important;
  font-size:clamp(4.25rem,10vw,9rem)!important;
  line-height:.78!important;
  letter-spacing:-.055em!important;
}
body.art-home #oolita-art-field-stone .art-caption{
  max-width:31rem!important;
  margin:clamp(1.25rem,2.4vw,1.9rem) 0 0!important;
  font-size:clamp(1rem,1.35vw,1.2rem)!important;
  line-height:1.45!important;
}

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
  /* Match the desktop selector's ID specificity so the mobile one-column grid
     actually wins despite both declarations being !important. */
  body.art-home #oolita-art-field-stone{
    grid-template-columns:minmax(0,1fr)!important;
    gap:0!important;
    padding:42svh 1.25rem 1.25rem!important;
  }
  body.art-home #oolita-art-field-stone .art-copy{
    grid-column:1 / -1!important;
    min-width:0!important;
    width:100%!important;
    max-width:none!important;
  }
  body.art-home .art-field-photo{height:40svh!important}
  body.art-home .art-field--stone::after{inset:26svh 0 auto 0!important;height:16svh!important}
  body.art-home .art-field .art-word{font-size:clamp(4.8rem,28vw,8rem)!important;line-height:.68!important}
  body.art-home .art-field--stone .art-word{font-size:clamp(4rem,21vw,6.6rem)!important;white-space:nowrap!important}
  body.art-home #oolita-art-field-stone .art-caption{
    width:min(100%,31rem)!important;
    margin-top:1rem!important;
    font-size:1rem!important;
    line-height:1.4!important;
  }
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

style_pattern = re.compile(
    rf'<style\s+id=["\']{re.escape(STYLE_ID)}["\'][^>]*>.*?</style>',
    flags=re.I | re.S,
)
for target in html_files:
    html = target.read_text(encoding="utf-8")
    if style_pattern.search(html):
        html = style_pattern.sub(STYLE, html, count=1)
    else:
        if "</head>" not in html:
            raise SystemExit(f"Missing </head>: {target.relative_to(ROOT)}")
        html = html.replace("</head>", STYLE + "\n</head>", 1)
    target.write_text(html, encoding="utf-8")

for rel in ("index.html", "en/index.html"):
    target = ROOT / rel
    html = target.read_text(encoding="utf-8")
    for needle in (
        STYLE_ID,
        "art-manifesto",
        "art-home",
        "#oolita-art-field-stone .art-word",
        "white-space:nowrap!important",
        "font-size:clamp(4.25rem,10vw,9rem)!important",
        "grid-template-columns:minmax(0,1fr)!important",
        "grid-column:1 / -1!important",
    ):
        if needle not in html:
            raise SystemExit(f"Visual spacing cleanup invariant failed in {rel}: {needle}")

print(f"OOLITA visual overlap and mobile spacing cleanup validated across {len(html_files)} HTML pages.")
