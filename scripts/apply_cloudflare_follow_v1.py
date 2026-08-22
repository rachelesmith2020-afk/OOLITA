#!/usr/bin/env python3
"""Render OOLITA's first-party Cloudflare Follow form.

The form records explicit consent and optional interests in Cloudflare D1. A
valid consent submission becomes active immediately; the page then shows a
simple subscription confirmation. No marketing email is sent by this layer.
"""
from pathlib import Path
import re
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")

STYLE = r'''<style id="oolita-follow-style">
#seguir-oolita,#follow-oolita{padding-top:clamp(4rem,9vw,8rem);padding-bottom:clamp(4rem,9vw,8rem)}
#seguir-oolita .oolita-follow-grid,#follow-oolita .oolita-follow-grid{display:grid;grid-template-columns:minmax(0,.82fr) minmax(0,1.18fr);gap:clamp(2.25rem,7vw,7rem);align-items:start}
#seguir-oolita .oolita-follow-intro,#follow-oolita .oolita-follow-intro{max-width:34rem}
#seguir-oolita .oolita-follow-intro .grande,#follow-oolita .oolita-follow-intro .grande{margin:.45rem 0 1rem;max-width:9ch;line-height:.92}
#seguir-oolita .oolita-follow-intro .glosa,#follow-oolita .oolita-follow-intro .glosa{max-width:31rem;margin:0}
.oolita-follow{max-width:43rem;border-top:1.5px solid currentColor;padding-top:1.15rem}
.oolita-follow [hidden]{display:none!important}
.oolita-follow .follow-status{margin:0 0 2.25rem;font-size:.82rem;line-height:1.35;letter-spacing:.035em;text-transform:uppercase;opacity:.72}
.oolita-follow .follow-field-label{display:block;margin:0 0 .55rem;font-size:.78rem;line-height:1.2;letter-spacing:.055em;text-transform:uppercase}
.oolita-follow input[type="email"]{box-sizing:border-box;width:100%;min-height:3.4rem;padding:.2rem 0 .55rem;border:0;border-bottom:2px solid currentColor;border-radius:0;background:transparent;color:inherit;font:inherit;font-size:clamp(1.3rem,3vw,2rem);outline:none;box-shadow:none}
.oolita-follow input[type="email"]:focus{border-bottom-width:4px}
.oolita-follow .follow-interests{margin:2.5rem 0 2.1rem;padding:0;border:0}
.oolita-follow .follow-interests legend{padding:0;margin:0 0 .9rem;font-size:.78rem;letter-spacing:.055em;text-transform:uppercase}
.oolita-follow .follow-chip-set{display:flex;flex-wrap:wrap;gap:.55rem}
.oolita-follow .follow-chip{display:inline-flex;align-items:center;gap:.55rem;padding:.58rem .78rem;border:1.25px solid currentColor;border-radius:999px;font-size:.96rem;line-height:1.15;cursor:pointer;user-select:none}
.oolita-follow .follow-chip input{appearance:none;-webkit-appearance:none;width:.88rem;height:.88rem;margin:0;border:1.25px solid currentColor;border-radius:50%;background:transparent;display:inline-grid;place-items:center}
.oolita-follow .follow-chip input:checked{background:currentColor;box-shadow:inset 0 0 0 2.5px #f1e6cf}
.oolita-follow .follow-consent{display:grid;grid-template-columns:1.1rem 1fr;gap:.75rem;align-items:start;margin:0 0 1.8rem;font-size:.92rem;line-height:1.45;cursor:pointer}
.oolita-follow .follow-consent input{appearance:none;-webkit-appearance:none;width:1.08rem;height:1.08rem;margin:.12rem 0 0;border:1.5px solid currentColor;background:transparent}
.oolita-follow .follow-consent input:checked{background:currentColor;box-shadow:inset 0 0 0 3px #f1e6cf}
.oolita-follow .follow-submit{width:100%;display:grid;grid-template-columns:auto 1fr auto;align-items:center;gap:1rem;min-height:4.35rem;padding:.9rem 1.05rem;border:1.5px solid #2d4e23;border-radius:0;background:#2d4e23;color:#f1e6cf;font:inherit;text-align:left;cursor:pointer;transition:transform .16s ease,opacity .16s ease}
.oolita-follow .follow-submit:hover{transform:translateY(-2px)}
.oolita-follow .follow-submit:focus-visible{outline:3px solid #132572;outline-offset:4px}
.oolita-follow .follow-submit:disabled{opacity:.82;cursor:wait;transform:none}
.oolita-follow .follow-submit .follow-arrow{font-size:1.25rem;line-height:1}
.oolita-follow .follow-submit .follow-name{font-size:1.04rem;font-weight:650}
.oolita-follow .follow-submit .follow-note{font-size:.74rem;line-height:1.2;text-align:right;opacity:.78}
.oolita-follow .follow-fallback{display:block;margin-top:1rem;font-size:.88rem}
.oolita-follow .follow-privacy{margin:1.6rem 0 0;padding-top:1rem;border-top:1px solid color-mix(in srgb,currentColor 38%,transparent);font-size:.78rem;line-height:1.5;opacity:.76}
.oolita-follow .follow-privacy a{color:inherit;text-decoration-thickness:1px;text-underline-offset:.16em}
@media(max-width:760px){
 #seguir-oolita .oolita-follow-grid,#follow-oolita .oolita-follow-grid{grid-template-columns:1fr;gap:2.5rem}
 #seguir-oolita .oolita-follow-intro .grande,#follow-oolita .oolita-follow-intro .grande{max-width:11ch}
 .oolita-follow{padding-top:1rem}
 .oolita-follow .follow-status{margin-bottom:1.8rem}
 .oolita-follow .follow-submit{grid-template-columns:auto 1fr;min-height:4rem}
 .oolita-follow .follow-submit .follow-note{grid-column:2;text-align:left;margin-top:-.45rem}
 .oolita-follow .follow-chip{font-size:.9rem;padding:.52rem .7rem}
}
</style>'''

SCRIPT = r'''<script id="oolita-follow-client">(function(){
function setup(id,lang){var f=document.getElementById(id);if(!f)return;var s=f.querySelector('[data-follow-status]');var b=f.querySelector('button[type="submit"]');var fb=f.querySelector('[data-follow-fallback]');fetch('/api/subscribe?health=1',{credentials:'omit'}).then(function(r){if(r.status!==204)throw new Error('unavailable');if(b)b.disabled=false;if(fb)fb.hidden=true;if(s)s.textContent=lang==='es'?'Lista activa · tú eliges qué seguir.':'List active · choose what you want to follow.';}).catch(function(){if(s)s.textContent=lang==='es'?'La lista no está disponible ahora mismo. Puedes escribir a oolita@tutamail.com.':'The list is unavailable right now. You can write to oolita@tutamail.com.';if(fb)fb.hidden=false;});f.addEventListener('submit',async function(e){e.preventDefault();if(b&&b.disabled)return;if(b)b.disabled=true;if(s)s.textContent=lang==='es'?'Guardando…':'Saving…';var fd=new FormData(f);var payload={email:fd.get('email'),language:lang,consent:fd.get('consent')==='on',website:fd.get('website')||'',source_path:location.pathname,interests:fd.getAll('interest')};try{var r=await fetch('/api/subscribe',{method:'POST',headers:{'Content-Type':'application/json'},credentials:'omit',body:JSON.stringify(payload)});var j=await r.json();if(!r.ok||!j.ok)throw new Error(j.error||'subscribe_failed');f.reset();if(s)s.textContent=lang==='es'?'Ya estás dentro · gracias por seguir OOLITA.':'You’re in · thank you for following OOLITA.';if(window.OOLITA_EVENT)window.OOLITA_EVENT('follow-signup-recorded',{state:j.state||'active'});}catch(err){if(s)s.textContent=lang==='es'?'No se ha podido guardar. Inténtalo de nuevo o escribe a oolita@tutamail.com.':'We could not save this. Try again or write to oolita@tutamail.com.';}finally{if(b)b.disabled=false;}});}
setup('oolita-follow-es','es');setup('oolita-follow-en','en');})();</script>'''

ES = '''<section class="tramo env" id="seguir-oolita" data-oolita-follow="cloudflare"><div class="oolita-follow-grid"><div class="oolita-follow-intro"><span class="rot">Seguir OOLITA</span><h2 class="grande">Seguir el proyecto.</h2><p class="glosa">Una sola lista. Elige lo que quieres seguir: mundo 3D, libro, publicaciones de campo o ediciones textiles.</p></div><form class="oolita-follow" id="oolita-follow-es" action="/api/subscribe" method="post"><p class="follow-status" data-follow-status aria-live="polite">Comprobando la lista…</p><label class="follow-field-label" for="oolita-follow-email-es">Correo electrónico</label><input id="oolita-follow-email-es" type="email" name="email" autocomplete="email" inputmode="email" placeholder="tu@correo.es" required><fieldset class="follow-interests"><legend>Me interesa · opcional</legend><div class="follow-chip-set"><label class="follow-chip"><input type="checkbox" name="interest" value="3d"><span>Mundo 3D</span></label><label class="follow-chip"><input type="checkbox" name="interest" value="book"><span>Libro</span></label><label class="follow-chip"><input type="checkbox" name="interest" value="field"><span>Publicaciones de campo</span></label><label class="follow-chip"><input type="checkbox" name="interest" value="textile"><span>Ediciones textiles</span></label></div></fieldset><label class="follow-consent"><input type="checkbox" name="consent" required><span>Quiero recibir noticias de OOLITA. Puedo darme de baja en cualquier momento.</span></label><label style="position:absolute;left:-10000px" aria-hidden="true">Sitio web <input type="text" name="website" tabindex="-1" autocomplete="off"></label><input type="hidden" name="language" value="es"><button class="follow-submit" type="submit" data-oolita-event="follow-submit" disabled><span class="follow-arrow">↗</span><span class="follow-name">Seguir OOLITA</span><span class="follow-note">Sin publicidad · baja cuando quieras</span></button><a class="follow-fallback" data-follow-fallback href="mailto:oolita@tutamail.com?subject=OOLITA%20%C2%B7%20seguir%20el%20proyecto" rel="nofollow" hidden>Mientras tanto, escríbeme a oolita@tutamail.com</a><p class="follow-privacy">Responsable: Raquel Costantini (OOLITA). Usamos tu correo, idioma, intereses elegidos y registro de consentimiento para gestionar la suscripción y adaptar las noticias a tus preferencias. Base jurídica: tu consentimiento; puedes retirarlo y ejercer tus derechos escribiendo a <a href="mailto:oolita@tutamail.com">oolita@tutamail.com</a>. <a href="/privacidad/">Política de privacidad</a>.</p></form></div></section>'''

EN = '''<section class="tramo env" id="follow-oolita" data-oolita-follow="cloudflare"><div class="oolita-follow-grid"><div class="oolita-follow-intro"><span class="rot">Follow OOLITA</span><h2 class="grande">Follow the project.</h2><p class="glosa">One list. Choose what you want to follow: the 3D world, book, field publications or textile editions.</p></div><form class="oolita-follow" id="oolita-follow-en" action="/api/subscribe" method="post"><p class="follow-status" data-follow-status aria-live="polite">Checking the list…</p><label class="follow-field-label" for="oolita-follow-email-en">Email</label><input id="oolita-follow-email-en" type="email" name="email" autocomplete="email" inputmode="email" placeholder="you@email.com" required><fieldset class="follow-interests"><legend>I am interested in · optional</legend><div class="follow-chip-set"><label class="follow-chip"><input type="checkbox" name="interest" value="3d"><span>3D world</span></label><label class="follow-chip"><input type="checkbox" name="interest" value="book"><span>Book</span></label><label class="follow-chip"><input type="checkbox" name="interest" value="field"><span>Field publications</span></label><label class="follow-chip"><input type="checkbox" name="interest" value="textile"><span>Textile editions</span></label></div></fieldset><label class="follow-consent"><input type="checkbox" name="consent" required><span>I want to receive OOLITA news. I can unsubscribe at any time.</span></label><label style="position:absolute;left:-10000px" aria-hidden="true">Website <input type="text" name="website" tabindex="-1" autocomplete="off"></label><input type="hidden" name="language" value="en"><button class="follow-submit" type="submit" data-oolita-event="follow-submit" disabled><span class="follow-arrow">↗</span><span class="follow-name">Follow OOLITA</span><span class="follow-note">No advertising · unsubscribe any time</span></button><a class="follow-fallback" data-follow-fallback href="mailto:oolita@tutamail.com?subject=OOLITA%20%C2%B7%20follow%20the%20project" rel="nofollow" hidden>Meanwhile, write to oolita@tutamail.com</a><p class="follow-privacy">Controller: Raquel Costantini (OOLITA). We use your email, language, selected interests and consent record to manage the subscription and tailor news to your preferences. Legal basis: your consent; you can withdraw it and exercise your rights by writing to <a href="mailto:oolita@tutamail.com">oolita@tutamail.com</a>. <a href="/en/privacy/">Privacy policy</a>.</p></form></div></section>'''


def swap(path, section_id, block):
    p = ROOT / path
    if not p.is_file():
        raise SystemExit(f"Missing page: {path}")
    s = p.read_text(encoding="utf-8")
    pattern = rf'<section class="tramo env" id="{re.escape(section_id)}"[\s\S]*?</section>'
    ns, n = re.subn(pattern, block, s, count=1)
    if n != 1:
        raise SystemExit(f"Could not replace Follow OOLITA section in {path}")

    if 'id="oolita-follow-style"' in ns:
        ns = re.sub(r'<style id="oolita-follow-style">[\s\S]*?</style>', STYLE, ns, count=1)
    else:
        if "</head>" not in ns:
            raise SystemExit(f"Missing </head> in {path}")
        ns = ns.replace("</head>", STYLE + "\n</head>", 1)

    if 'id="oolita-follow-client"' in ns:
        ns = re.sub(r'<script id="oolita-follow-client">[\s\S]*?</script>', SCRIPT, ns, count=1)
    else:
        if "</body>" not in ns:
            raise SystemExit(f"Missing </body> in {path}")
        ns = ns.replace("</body>", SCRIPT + "\n</body>", 1)

    p.write_text(ns, encoding="utf-8")


swap("index.html", "seguir-oolita", ES)
swap("en/index.html", "follow-oolita", EN)

for path, form_id in [("index.html", "oolita-follow-es"), ("en/index.html", "oolita-follow-en")]:
    s = (ROOT / path).read_text(encoding="utf-8")
    required = [
        'data-oolita-follow="cloudflare"',
        f'id="{form_id}"',
        'action="/api/subscribe"',
        'name="consent"',
        'value="field"',
        'value="textile"',
        'id="oolita-follow-client"',
        'id="oolita-follow-style"',
        'class="follow-chip-set"',
        'class="follow-submit"',
        'data-follow-fallback',
        'href="/privacidad/"' if path == "index.html" else 'href="/en/privacy/"',
    ]
    for needle in required:
        if needle not in s:
            raise SystemExit(f"Cloudflare Follow invariant missing in {path}: {needle}")
    if 'pending_confirmation' in s:
        raise SystemExit(f"Pending confirmation language still present in {path}")

print("OOLITA first-party Cloudflare Follow form validated successfully.")
