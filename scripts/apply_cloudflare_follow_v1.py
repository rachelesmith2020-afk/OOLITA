#!/usr/bin/env python3
"""Replace OOLITA's temporary email CTA with a first-party Cloudflare list form.

The form records explicit consent and optional interests in Cloudflare D1. New
addresses remain pending_confirmation until an outbound verification-email
service is added; no marketing email is sent by this layer.
"""
from pathlib import Path
import re
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")

SCRIPT = r'''<script id="oolita-follow-client">(function(){
function setup(id,lang){var f=document.getElementById(id);if(!f)return;var s=f.querySelector('[data-follow-status]');f.addEventListener('submit',async function(e){e.preventDefault();var b=f.querySelector('button[type="submit"]');if(b)b.disabled=true;if(s)s.textContent=lang==='es'?'Guardando…':'Saving…';var fd=new FormData(f);var payload={email:fd.get('email'),language:lang,consent:fd.get('consent')==='on',website:fd.get('website')||'',source_path:location.pathname,interests:fd.getAll('interest')};try{var r=await fetch('/api/subscribe',{method:'POST',headers:{'Content-Type':'application/json'},credentials:'omit',body:JSON.stringify(payload)});var j=await r.json();if(!r.ok||!j.ok)throw new Error(j.error||'subscribe_failed');f.reset();if(s)s.textContent=lang==='es'?'Gracias. Tu interés queda registrado. Antes de enviar boletines, verificaremos la dirección por correo.':'Thank you. Your interest is recorded. Before newsletters are sent, the address will be verified by email.';if(window.OOLITA_EVENT)window.OOLITA_EVENT('follow-signup-recorded',{state:j.state||'recorded'});}catch(err){if(s)s.textContent=lang==='es'?'No se ha podido guardar. Inténtalo de nuevo o escribe a oolita@tutamail.com.':'We could not save this. Try again or write to oolita@tutamail.com.';}finally{if(b)b.disabled=false;}});}
setup('oolita-follow-es','es');setup('oolita-follow-en','en');})();</script>'''

ES = '''<section class="tramo env" id="seguir-oolita" data-oolita-follow="cloudflare"><span class="rot">Seguir OOLITA</span><h2 class="grande">Seguir el proyecto.</h2><p class="glosa">Una sola lista para noticias del mundo 3D, el libro, las publicaciones de campo y las ediciones textiles.</p><form class="oolita-follow" id="oolita-follow-es" action="/api/subscribe" method="post"><label class="parr">Correo electrónico<br><input type="email" name="email" autocomplete="email" inputmode="email" required></label><fieldset><legend class="parr">Me interesa <span aria-hidden="true">·</span> opcional</legend><label><input type="checkbox" name="interest" value="3d"> Mundo 3D</label> <label><input type="checkbox" name="interest" value="book"> Libro</label> <label><input type="checkbox" name="interest" value="field"> Publicaciones de campo</label> <label><input type="checkbox" name="interest" value="textile"> Ediciones textiles</label></fieldset><label class="parr"><input type="checkbox" name="consent" required> Quiero recibir noticias de OOLITA. Puedo retirar mi consentimiento y darme de baja en cualquier momento.</label><label style="position:absolute;left:-10000px" aria-hidden="true">Sitio web <input type="text" name="website" tabindex="-1" autocomplete="off"></label><input type="hidden" name="language" value="es"><button class="fila" type="submit" data-oolita-event="follow-submit"><span class="n">→</span><span class="nom">Seguir OOLITA</span><span class="glo">Sin publicidad · baja cuando quieras</span></button><p class="parr" data-follow-status aria-live="polite">Guardamos sólo el correo, idioma, intereses elegidos y el registro de consentimiento para gestionar la lista. No se vende ni se usa para publicidad. Para borrar tus datos: <a href="mailto:oolita@tutamail.com">oolita@tutamail.com</a>.</p></form></section>'''

EN = '''<section class="tramo env" id="follow-oolita" data-oolita-follow="cloudflare"><span class="rot">Follow OOLITA</span><h2 class="grande">Follow the project.</h2><p class="glosa">One list for news about the 3D world, the book, field publications and textile editions.</p><form class="oolita-follow" id="oolita-follow-en" action="/api/subscribe" method="post"><label class="parr">Email<br><input type="email" name="email" autocomplete="email" inputmode="email" required></label><fieldset><legend class="parr">I am interested in <span aria-hidden="true">·</span> optional</legend><label><input type="checkbox" name="interest" value="3d"> 3D world</label> <label><input type="checkbox" name="interest" value="book"> Book</label> <label><input type="checkbox" name="interest" value="field"> Field publications</label> <label><input type="checkbox" name="interest" value="textile"> Textile editions</label></fieldset><label class="parr"><input type="checkbox" name="consent" required> I want to receive OOLITA news. I can withdraw consent and unsubscribe at any time.</label><label style="position:absolute;left:-10000px" aria-hidden="true">Website <input type="text" name="website" tabindex="-1" autocomplete="off"></label><input type="hidden" name="language" value="en"><button class="fila" type="submit" data-oolita-event="follow-submit"><span class="n">→</span><span class="nom">Follow OOLITA</span><span class="glo">No advertising · unsubscribe any time</span></button><p class="parr" data-follow-status aria-live="polite">We store only your email, language, selected interests and consent record to manage the list. It is not sold or used for advertising. To request deletion: <a href="mailto:oolita@tutamail.com">oolita@tutamail.com</a>.</p></form></section>'''


def swap(path, section_id, block):
    p = ROOT / path
    if not p.is_file():
        raise SystemExit(f"Missing page: {path}")
    s = p.read_text(encoding="utf-8")
    if 'data-oolita-follow="cloudflare"' in s:
        return
    pattern = rf'<section class="tramo env" id="{re.escape(section_id)}"[\s\S]*?</section>'
    ns, n = re.subn(pattern, block, s, count=1)
    if n != 1:
        raise SystemExit(f"Could not replace Follow OOLITA section in {path}")
    if 'id="oolita-follow-client"' not in ns:
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
    ]
    for needle in required:
        if needle not in s:
            raise SystemExit(f"Cloudflare Follow invariant missing in {path}: {needle}")
    if 'data-oolita-follow="pending"' in s:
        raise SystemExit(f"Pending Follow state still present in {path}")

print("OOLITA first-party Cloudflare Follow form validated successfully.")
