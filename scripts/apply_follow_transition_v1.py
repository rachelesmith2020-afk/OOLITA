#!/usr/bin/env python3
"""Activate and finish OOLITA's first-party Cloudflare Follow form."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
subprocess.run([sys.executable, "scripts/apply_cloudflare_follow_v1.py", str(ROOT)], check=True)
subprocess.run([sys.executable, "scripts/apply_follow_mobile_finish.py", str(ROOT)], check=True)

# The deployment mirror now starts from a live origin on which later final
# passes have already published newer identity/date wording. Normalize only
# the intermediate source strings expected by the older strict transformers;
# apply_public_identity_v2.py restores the current public wording at the end.
success_ui_patches = 0
for path in ROOT.rglob("*.html"):
    text = path.read_text(encoding="utf-8")
    text = text.replace(
        "OOLITA · Un proyecto de Vestini Tribe · Raquel Costantini, artista y autora",
        "OOLITA · Raquel Costantini",
    )
    text = text.replace(
        "OOLITA · A Vestini Tribe project · Raquel Costantini, artist and author",
        "OOLITA · Raquel Costantini",
    )
    text = text.replace(
        "En el castillo: catálogo completo con clave · tapa dura 16.09.27 · presentación pública 19.09.27 ↗",
        "En el castillo: catálogo completo con clave · tapa dura prevista para otoño de 2027 ↗",
    )
    text = text.replace(
        "In the castle: full catalogue with a key · hardback 16.09.27 · public launch 19.09.27 ↗",
        "In the castle: full catalogue with a key · hardback planned for autumn 2027 ↗",
    )

    # Double opt-in: a new address is pending until the confirmation link is
    # opened. An address that was already confirmed stays active and only has
    # its preferences refreshed. The result must also be visibly brought into
    # view because the status line sits above the submit button.
    old_success = (
        "if(s)s.textContent=lang==='es'?'Ya estás dentro · gracias por seguir OOLITA.':'You’re in · thank you for following OOLITA.';"
    )
    new_success = (
        "if(s){s.textContent=j.state==='active'?(lang==='es'?'Gracias · tu correo ya estaba confirmado. Hemos actualizado tus preferencias.':'Thanks · your email was already confirmed. We updated your preferences.'):(lang==='es'?'Gracias · revisa tu correo y confirma el enlace. Nos vemos pronto.':'Thanks · check your email and confirm the link. See you soon.');"
        "s.setAttribute('tabindex','-1');s.style.opacity='1';s.style.textTransform='none';s.style.fontSize='1rem';"
        "s.style.borderTop='1.5px solid currentColor';s.style.borderBottom='1.5px solid currentColor';s.style.padding='1rem 0';"
        "s.focus({preventScroll:true});s.scrollIntoView({behavior:'smooth',block:'center'});}"
    )
    if old_success in text:
        success_ui_patches += text.count(old_success)
        text = text.replace(old_success, new_success)

    # Fallback for any mirrored page whose client script has already been
    # transformed independently.
    text = text.replace(
        "Ya estás dentro · gracias por seguir OOLITA.",
        "Gracias · revisa tu correo y confirma el enlace. Nos vemos pronto.",
    )
    text = text.replace(
        "You’re in · thank you for following OOLITA.",
        "Thanks · check your email and confirm the link. See you soon.",
    )
    text = text.replace(
        "Quiero recibir noticias de OOLITA. Puedo darme de baja en cualquier momento.",
        "Quiero recibir noticias de OOLITA. Confirmaré mi correo antes de entrar en la lista y puedo darme de baja en cualquier momento.",
    )
    text = text.replace(
        "I want to receive OOLITA news. I can unsubscribe at any time.",
        "I want to receive OOLITA news. I will confirm my email before joining the list and can unsubscribe at any time.",
    )

    # "book" is the stable machine-facing interest key used by existing
    # follow links and subscriber data. Only the public category label is
    # plural so it covers both the OOLITA and Hallazgo books.
    text = text.replace(
        "Elige lo que quieres seguir: mundo 3D, libro, publicaciones de campo o ediciones textiles.",
        "Elige lo que quieres seguir: mundo 3D, libros, publicaciones de campo o ediciones textiles.",
    )
    text = text.replace(
        '<input type="checkbox" name="interest" value="book"><span>Libro</span>',
        '<input type="checkbox" name="interest" value="book"><span>Libros</span>',
    )
    text = text.replace(
        "Choose what you want to follow: the 3D world, book, field publications or textile editions.",
        "Choose what you want to follow: the 3D world, books, field publications or textile editions.",
    )
    text = text.replace(
        '<input type="checkbox" name="interest" value="book"><span>Book</span>',
        '<input type="checkbox" name="interest" value="book"><span>Books</span>',
    )

    if 'id="oolita-follow-en"' in text:
        expected = '<input type="checkbox" name="interest" value="book"><span>Books</span>'
        if text.count(expected) != 1 or '<span>Book</span>' in text:
            raise SystemExit(f"English Books interest label invariant failed in {path.relative_to(ROOT)}")
    if 'id="oolita-follow-es"' in text:
        expected = '<input type="checkbox" name="interest" value="book"><span>Libros</span>'
        if text.count(expected) != 1 or '<span>Libro</span>' in text:
            raise SystemExit(f"Spanish Libros interest label invariant failed in {path.relative_to(ROOT)}")

    path.write_text(text, encoding="utf-8")

if success_ui_patches == 0:
    raise SystemExit("Double-opt-in success confirmation UI was not found in the rendered site")

print("OOLITA Follow Cloudflare activation, double opt-in copy, plural Books/Libros interest, mobile CTA and visible success confirmation validated successfully.")
