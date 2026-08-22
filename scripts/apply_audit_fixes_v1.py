#!/usr/bin/env python3
"""Apply the 22 August 2026 accessibility, discovery and privacy audit fixes.

This pass runs after the Follow form is activated and before the common
analytics/search passes. It is intentionally strict: a source change that
invalidates an audited replacement stops the build instead of silently
shipping a partial fix.
"""
from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit


ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
BASE = "https://oolita.es"
LASTMOD = "2026-08-22"
OLD_COORDINATES = "36°44′ N · 2°07′ W"
EXACT_COORDINATES = "36°47′58″ N · 2°03′47″ W"


def read(path: str) -> tuple[Path, str]:
    p = ROOT / path
    if not p.is_file():
        raise SystemExit(f"Missing audited page: {path}")
    return p, p.read_text(encoding="utf-8")


def write(path: str, text: str) -> None:
    p = ROOT / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def replace_required(text: str, old: str, new: str, *, page: str) -> str:
    if new in text:
        return text
    if old not in text:
        raise SystemExit(f"Audit source text missing in {page}: {old[:120]!r}")
    return text.replace(old, new, 1)


def set_meta(text: str, attr: str, key: str, value: str, *, page: str) -> str:
    pattern = rf'<meta\s+{re.escape(attr)}=["\']{re.escape(key)}["\'][^>]*>'
    tag = f'<meta {attr}="{key}" content="{value}">'
    if re.search(pattern, text, flags=re.I):
        return re.sub(pattern, tag, text, count=1, flags=re.I)
    if "</head>" not in text:
        raise SystemExit(f"Missing </head> while setting {key} in {page}")
    return text.replace("</head>", tag + "\n</head>", 1)


def set_title_and_social(path: str, *, title: str | None = None, description: str | None = None) -> None:
    p, text = read(path)
    if title is not None:
        text, count = re.subn(r"<title>[\s\S]*?</title>", f"<title>{title}</title>", text, count=1, flags=re.I)
        if count != 1:
            raise SystemExit(f"Missing title in {path}")
        text = set_meta(text, "property", "og:title", title, page=path)
        text = set_meta(text, "name", "twitter:title", title, page=path)
    if description is not None:
        text = set_meta(text, "name", "description", description, page=path)
        text = set_meta(text, "property", "og:description", description, page=path)
        text = set_meta(text, "name", "twitter:description", description, page=path)
    p.write_text(text, encoding="utf-8")


STYLE = r'''<style id="oolita-audit-fixes-style">
.top a,.pie a{display:inline-flex;align-items:center;min-height:2.75rem;padding:.45rem .2rem;margin:-.45rem -.2rem;text-underline-offset:.16em}
.oolita-actions{display:flex;flex-wrap:wrap;gap:.65rem;margin-top:clamp(1.15rem,3vw,1.8rem)}
.oolita-action{display:inline-flex;align-items:center;min-height:2.75rem;padding:.62rem .82rem;border:1.5px solid currentColor;color:var(--verde);font-size:.82rem;font-weight:700;letter-spacing:.045em;text-decoration:none;text-transform:uppercase}
.oolita-action:first-child{background:var(--verde);color:var(--papel);border-color:var(--verde)}
.oolita-action:hover{text-decoration:underline;text-underline-offset:.18em}
.oolita-action:focus-visible,.top a:focus-visible,.pie a:focus-visible{outline:3px solid var(--azul);outline-offset:3px}
.oolita-directory{display:block}
@media(max-width:34rem){.oolita-action{width:100%;justify-content:space-between}}
</style>'''


def add_audit_style(text: str, *, page: str) -> str:
    if 'id="oolita-audit-fixes-style"' in text:
        return re.sub(r'<style id="oolita-audit-fixes-style">[\s\S]*?</style>', STYLE, text, count=1)
    if "</head>" not in text:
        raise SystemExit(f"Missing </head> in {page}")
    return text.replace("</head>", STYLE + "\n</head>", 1)


def patch_home(path: str, *, lang: str) -> None:
    p, text = read(path)
    if OLD_COORDINATES in text:
        text = text.replace(OLD_COORDINATES, EXACT_COORDINATES, 1)
    elif EXACT_COORDINATES not in text:
        raise SystemExit(f"Homepage coordinates missing in {path}")

    if lang == "es":
        countdown_old = '<span class="rot">Abre / Opens</span>'
        countdown_new = '<span class="rot">El mundo 3D abre</span>'
        action_label = "Acciones principales"
        actions = (
            '<nav class="oolita-actions" aria-label="Acciones principales">'
            '<a class="oolita-action" data-oolita-event="home-primary-labyrinth" href="/laberinto/">Visitar el laberinto <span aria-hidden="true">→</span></a>'
            '<a class="oolita-action" data-oolita-event="home-primary-follow" href="#seguir-oolita">Seguir la apertura <span aria-hidden="true">↓</span></a>'
            '<a class="oolita-action" data-oolita-event="home-primary-book" href="/ediciones/libro/">Ver el libro <span aria-hidden="true">→</span></a>'
            '</nav>'
        )
        directory_title = "directorio-oolita"
        directory_label = "Directorio de OOLITA"
    else:
        countdown_old = '<span class="rot">Opens / Abre</span>'
        countdown_new = '<span class="rot">The 3D world opens</span>'
        action_label = "Primary actions"
        actions = (
            '<nav class="oolita-actions" aria-label="Primary actions">'
            '<a class="oolita-action" data-oolita-event="home-primary-labyrinth" href="/en/labyrinth/">Visit the labyrinth <span aria-hidden="true">→</span></a>'
            '<a class="oolita-action" data-oolita-event="home-primary-follow" href="#follow-oolita">Follow the opening <span aria-hidden="true">↓</span></a>'
            '<a class="oolita-action" data-oolita-event="home-primary-book" href="/en/editions/book/">View the book <span aria-hidden="true">→</span></a>'
            '</nav>'
        )
        directory_title = "oolita-directory-title"
        directory_label = "OOLITA directory"

    text = replace_required(text, countdown_old, countdown_new, page=path)

    if f'aria-label="{action_label}"' not in text:
        match = re.search(r'<div class="firma">[\s\S]*?</div>', text)
        if not match:
            raise SystemExit(f"Homepage signature block missing in {path}")
        text = text[:match.end()] + actions + text[match.end():]

    if 'class="oolita-directory"' not in text:
        pattern = (
            r'(<section class="lista env">\s*)'
            r'(<span class="rot"[^>]*>[\s\S]*?</span>)'
            r'([\s\S]*?)'
            r'(</section>\s*<section class="tramo env" id="(?:seguir-oolita|follow-oolita)")'
        )
        match = re.search(pattern, text)
        if not match:
            raise SystemExit(f"Homepage directory block missing in {path}")
        heading = match.group(2).replace('<span class="rot"', f'<span class="rot" id="{directory_title}"', 1)
        nav = f'<nav class="oolita-directory" aria-labelledby="{directory_title}" aria-label="{directory_label}">{match.group(3)}</nav>\n'
        replacement = match.group(1) + heading + nav + match.group(4)
        text = text[:match.start()] + replacement + text[match.end():]

    if '<span class="n">14</span>' not in text:
        raise SystemExit(f"Homepage contact number 14 missing in {path}")
    p.write_text(text, encoding="utf-8")


PRIVACY_ES = '''<section class="hero"><span class="rot">Privacidad</span><h1 class="grande">Tus datos, en claro.</h1><p class="glosa">OOLITA recoge lo mínimo para gestionar la lista y entender, sin cookies publicitarias, qué partes del sitio resultan útiles.</p></section>
<section class="tramo"><span class="rot">Responsable</span><h2 class="grande">Raquel Costantini · OOLITA.</h2><p class="parr">Raquel Costantini, en Almería, España, es la responsable del tratamiento. Para cualquier consulta o para ejercer tus derechos, escribe a <a href="mailto:oolita@tutamail.com">oolita@tutamail.com</a>.</p></section>
<section class="tramo env"><span class="rot">Lista de OOLITA</span><h2 class="grande">Suscripción voluntaria.</h2><p class="parr"><strong>Datos:</strong> correo electrónico, idioma, intereses opcionales, versión y fecha del consentimiento, página de origen, estado de la suscripción y un identificador privado de baja.</p><p class="parr"><strong>Finalidad:</strong> gestionar tu suscripción y enviarte noticias de OOLITA. Los intereses son opcionales y sólo sirven para adaptar esos envíos a tus preferencias.</p><p class="parr"><strong>Base jurídica:</strong> tu consentimiento. Puedes retirarlo en cualquier momento sin afectar a la licitud del tratamiento anterior. El correo y la aceptación son necesarios para suscribirte; los intereses no lo son. No hay decisiones automatizadas con efectos jurídicos ni venta de datos.</p></section>
<section class="tramo"><span class="rot">Medición del sitio</span><h2 class="grande">Sin cookies analíticas.</h2><p class="parr">OOLITA registra el nombre de una visita o acción, la ruta local relacionada y la fecha y hora. La base de medición no guarda correo, dirección IP, agente de usuario, identificadores publicitarios ni la URL completa de procedencia. Estos datos se usan para comprender el funcionamiento y la utilidad del sitio, sobre la base del interés legítimo en mantenerlo y mejorarlo.</p></section>
<section class="tramo env"><span class="rot">Conservación</span><h2 class="grande">Sólo mientras sea necesario.</h2><p class="parr">Los datos de suscripción se conservan mientras ésta siga activa. Tras la baja o una solicitud de supresión, sólo se mantiene de forma restringida lo necesario para respetar la baja, cumplir obligaciones aplicables o atender posibles responsabilidades; después se elimina. Los eventos del sitio se conservan durante el tiempo necesario para analizar su funcionamiento y se eliminan cuando dejan de ser útiles.</p></section>
<section class="tramo"><span class="rot">Proveedores y transferencias</span><h2 class="grande">Infraestructura de Cloudflare.</h2><p class="parr">Cloudflare presta el alojamiento, las funciones y la base de datos como encargado del tratamiento. La base de OOLITA está configurada con jurisdicción de la Unión Europea. Cloudflare es un proveedor global y puede apoyarse en subencargados o mecanismos de transferencia internacional sujetos a su <a href="https://www.cloudflare.com/cloudflare-customer-dpa/">Acuerdo de Tratamiento de Datos</a> y a las garantías aplicables. No se comunican datos a otros destinatarios, salvo obligación legal.</p></section>
<section class="tramo env"><span class="rot">Tus derechos</span><h2 class="grande">Acceso, rectificación y control.</h2><p class="parr">Puedes solicitar acceso, rectificación, supresión, limitación, oposición y portabilidad, y retirar el consentimiento, escribiendo a <a href="mailto:oolita@tutamail.com">oolita@tutamail.com</a>. También puedes reclamar ante la <a href="https://www.aepd.es/derechos-y-deberes/ejerce-tus-derechos">Agencia Española de Protección de Datos</a>. Para protegerte, OOLITA puede pedir información razonable para comprobar tu identidad antes de atender una solicitud.</p><p class="parr"><strong>Última actualización:</strong> 22 de agosto de 2026.</p></section>'''


PRIVACY_EN = '''<section class="hero"><span class="rot">Privacy</span><h1 class="grande">Your data, plainly.</h1><p class="glosa">OOLITA collects the minimum needed to manage the list and understand, without advertising cookies, which parts of the site are useful.</p></section>
<section class="tramo"><span class="rot">Controller</span><h2 class="grande">Raquel Costantini · OOLITA.</h2><p class="parr">Raquel Costantini, in Almería, Spain, is the data controller. For any question or to exercise your rights, write to <a href="mailto:oolita@tutamail.com">oolita@tutamail.com</a>.</p></section>
<section class="tramo env"><span class="rot">OOLITA list</span><h2 class="grande">Voluntary subscription.</h2><p class="parr"><strong>Data:</strong> email address, language, optional interests, consent version and timestamp, source page, subscription status and a private unsubscribe identifier.</p><p class="parr"><strong>Purpose:</strong> to manage your subscription and send OOLITA news. Interests are optional and are used only to tailor those messages to your preferences.</p><p class="parr"><strong>Legal basis:</strong> your consent. You may withdraw it at any time without affecting earlier lawful processing. Email and acceptance are required to subscribe; interests are not. There is no solely automated decision-making with legal effects and personal data is not sold.</p></section>
<section class="tramo"><span class="rot">Site measurement</span><h2 class="grande">No analytics cookies.</h2><p class="parr">OOLITA records the name of a visit or action, the related local path, and the date and time. The measurement database does not store email, IP address, user agent, advertising identifiers or a full referring URL. These records are used to understand the site's operation and usefulness, based on the legitimate interest in maintaining and improving it.</p></section>
<section class="tramo env"><span class="rot">Retention</span><h2 class="grande">Only while needed.</h2><p class="parr">Subscription data is kept while the subscription remains active. After unsubscribe or an erasure request, only what is needed to honour the opt-out, meet applicable obligations or handle possible legal claims is kept under restriction; it is then deleted. Site events are kept only as long as needed to analyse operation and are deleted when no longer useful.</p></section>
<section class="tramo"><span class="rot">Providers and transfers</span><h2 class="grande">Cloudflare infrastructure.</h2><p class="parr">Cloudflare provides hosting, functions and database services as a processor. OOLITA's database is configured for European Union jurisdiction. Cloudflare is a global provider and may rely on subprocessors or international-transfer mechanisms governed by its <a href="https://www.cloudflare.com/cloudflare-customer-dpa/">Data Processing Addendum</a> and applicable safeguards. Data is not disclosed to other recipients unless legally required.</p></section>
<section class="tramo env"><span class="rot">Your rights</span><h2 class="grande">Access, correction and control.</h2><p class="parr">You may request access, correction, erasure, restriction, objection and portability, and withdraw consent, by writing to <a href="mailto:oolita@tutamail.com">oolita@tutamail.com</a>. You may also complain to the <a href="https://www.aepd.es/derechos-y-deberes/ejerce-tus-derechos">Spanish Data Protection Agency</a>. To protect you, OOLITA may request reasonable information to verify your identity before acting on a request.</p><p class="parr"><strong>Last updated:</strong> 22 August 2026.</p></section>'''


def make_privacy_page(source: str, dest: str, *, lang: str, main_html: str) -> None:
    _, text = read(source)
    if lang == "es":
        title = "Privacidad · OOLITA"
        description = "Cómo trata OOLITA los datos de la lista y la medición del sitio: responsable, finalidad, base jurídica, conservación, proveedores y derechos."
        canonical = f"{BASE}/privacidad/"
        alt_es = canonical
        alt_en = f"{BASE}/en/privacy/"
        old_counterpart = "/en/about/"
        new_counterpart = "/en/privacy/"
        old_footer = '<span class="rot">Sobre OOLITA</span>'
        new_footer = '<span class="rot"><a href="/privacidad/">Privacidad</a></span>'
        social_alt = "Privacidad de OOLITA"
    else:
        title = "Privacy · OOLITA"
        description = "How OOLITA handles list and site-measurement data: controller, purpose, legal basis, retention, providers and your rights."
        canonical = f"{BASE}/en/privacy/"
        alt_es = f"{BASE}/privacidad/"
        alt_en = canonical
        old_counterpart = "/sobre-oolita/"
        new_counterpart = "/privacidad/"
        old_footer = '<span class="rot">About OOLITA</span>'
        new_footer = '<span class="rot"><a href="/en/privacy/">Privacy</a></span>'
        social_alt = "OOLITA privacy"

    text = re.sub(r'<meta\s+property=["\']article:[^>]+>\s*', '', text, flags=re.I)
    text, count = re.subn(r"<title>[\s\S]*?</title>", f"<title>{title}</title>", text, count=1, flags=re.I)
    if count != 1:
        raise SystemExit(f"Missing title in privacy shell {source}")
    text = set_meta(text, "name", "description", description, page=dest)
    text, count = re.subn(r'<link\s+rel=["\']canonical["\'][^>]*>', f'<link rel="canonical" href="{canonical}">', text, count=1, flags=re.I)
    if count != 1:
        raise SystemExit(f"Missing canonical in privacy shell {source}")
    text = re.sub(r'<link\s+rel=["\']alternate["\'][^>]*hreflang=[^>]+>\s*', '', text, flags=re.I)
    canonical_tag = f'<link rel="canonical" href="{canonical}">'
    alternates = (
        f'\n<link rel="alternate" hreflang="es" href="{alt_es}">'
        f'\n<link rel="alternate" hreflang="en" href="{alt_en}">'
        f'\n<link rel="alternate" hreflang="x-default" href="{alt_es}">'
    )
    text = text.replace(canonical_tag, canonical_tag + alternates, 1)
    for attr, key, value in [
        ("property", "og:type", "website"),
        ("property", "og:title", title),
        ("property", "og:description", description),
        ("property", "og:url", canonical),
        ("property", "og:image", f"{BASE}/og.png"),
        ("property", "og:image:secure_url", f"{BASE}/og.png"),
        ("property", "og:image:alt", social_alt),
        ("name", "twitter:title", title),
        ("name", "twitter:description", description),
        ("name", "twitter:image", f"{BASE}/og.png"),
        ("name", "twitter:image:alt", social_alt),
    ]:
        text = set_meta(text, attr, key, value, page=dest)
    text = text.replace(old_counterpart, new_counterpart)
    text, count = re.subn(
        r'(<main\b[^>]*>)[\s\S]*?(</main>)',
        lambda match: match.group(1) + "\n" + main_html + "\n" + match.group(2),
        text,
        count=1,
        flags=re.I,
    )
    if count != 1:
        raise SystemExit(f"Could not replace main in privacy shell {source}")
    footer = re.search(r'<footer\b[\s\S]*?</footer>', text, flags=re.I)
    if not footer or (old_footer not in footer.group(0) and new_footer not in footer.group(0)):
        raise SystemExit(f"Privacy footer shell marker missing in {source}")
    footer_text = footer.group(0).replace(old_footer, "").replace(new_footer, "")
    footer_text = footer_text.replace("</footer>", new_footer + "</footer>", 1)
    text = text[:footer.start()] + footer_text + text[footer.end():]
    write(dest, text)


def add_privacy_footer(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    language = "en" if re.search(r'<html\s+lang=["\']en(?:-[^"\']+)?["\']', text, flags=re.I) else "es"
    href = "/en/privacy/" if language == "en" else "/privacidad/"
    label = "Privacy" if language == "en" else "Privacidad"
    footer = re.search(r'<footer\b[\s\S]*?</footer>', text, flags=re.I)
    if not footer:
        raise SystemExit(f"Missing footer in {path.relative_to(ROOT)}")
    if f'href="{href}"' not in footer.group(0):
        addition = f'<span class="rot"><a href="{href}">{label}</a></span>'
        if "</div></div></footer>" in text:
            text = text.replace("</div></div></footer>", addition + "</div></div></footer>", 1)
        elif "</footer>" in text:
            text = text.replace("</footer>", addition + "</footer>", 1)
    text = add_audit_style(text, page=str(path.relative_to(ROOT)))
    path.write_text(text, encoding="utf-8")


if not ROOT.is_dir():
    raise SystemExit(f"Missing built site: {ROOT}")

# Homepage orientation and action hierarchy.
patch_home("index.html", lang="es")
patch_home("en/index.html", lang="en")

# Search-result copy: remove the duplicated phrase and keep edition titles
# concise while preserving the page's more expressive on-page heading.
set_title_and_social(
    "laberinto/index.html",
    description="Laberinto clásico de piedra de 3 m, hecho a mano en 2021 sobre una duna fósil en Los Escullos, Cabo de Gata. Cómo llegar y visitarlo con cuidado.",
)
set_title_and_social("ediciones/index.html", title="Ediciones: libros, textiles y campo · OOLITA")
set_title_and_social("en/editions/index.html", title="Editions: books, textiles and fieldwork · OOLITA")

# A complete, bilingual first-party privacy notice grounded in the actual D1
# schema and event endpoint.
make_privacy_page("sobre-oolita/index.html", "privacidad/index.html", lang="es", main_html=PRIVACY_ES)
make_privacy_page("en/about/index.html", "en/privacy/index.html", lang="en", main_html=PRIVACY_EN)

# Correct the coordinate display wherever the mirrored shell still carries the
# old rounded value, then add the policy and 44px link targets to every footer.
for page in sorted(ROOT.rglob("index.html")):
    text = page.read_text(encoding="utf-8")
    if OLD_COORDINATES in text:
        text = text.replace(OLD_COORDINATES, EXACT_COORDINATES)
        page.write_text(text, encoding="utf-8")
    add_privacy_footer(page)

# Add the two policy routes to the sitemap before the common search pass marks
# all materially changed URLs.
sitemap, sitemap_text = read("sitemap.xml")
for url in (f"{BASE}/privacidad/", f"{BASE}/en/privacy/"):
    if url not in sitemap_text:
        entry = f"  <url><loc>{url}</loc><lastmod>{LASTMOD}</lastmod></url>\n"
        if "</urlset>" not in sitemap_text:
            raise SystemExit("Unexpected sitemap format")
        sitemap_text = sitemap_text.replace("</urlset>", entry + "</urlset>", 1)
sitemap.write_text(sitemap_text, encoding="utf-8")

# Strict regression checks for every audited issue.
for path, follow_id, countdown, policy in [
    ("index.html", "seguir-oolita", "El mundo 3D abre", "/privacidad/"),
    ("en/index.html", "follow-oolita", "The 3D world opens", "/en/privacy/"),
]:
    _, text = read(path)
    for needle in [
        EXACT_COORDINATES,
        countdown,
        'class="oolita-actions"',
        'class="oolita-directory"',
        '<span class="n">14</span>',
        f'href="#{follow_id}"',
        f'href="{policy}"',
        'background:#2d4e23;color:#f1e6cf',
        'outline:3px solid #132572',
    ]:
        if needle not in text:
            raise SystemExit(f"Homepage audit invariant missing in {path}: {needle}")
    if 'background:currentColor;color:#f1e6cf' in text:
        raise SystemExit(f"Invisible Follow button rule remains in {path}")

social_pages = {
    "cabo-de-gata/index.html": f"{BASE}/cabo-de-gata/",
    "en/cabo-de-gata/index.html": f"{BASE}/en/cabo-de-gata/",
    "sobre-oolita/index.html": f"{BASE}/sobre-oolita/",
    "en/about/index.html": f"{BASE}/en/about/",
    "colaborar/index.html": f"{BASE}/colaborar/",
    "en/work-with-oolita/index.html": f"{BASE}/en/work-with-oolita/",
}
for path, canonical in social_pages.items():
    _, text = read(path)
    for needle in [
        f'<meta property="og:url" content="{canonical}">',
        '<link rel="alternate" hreflang="x-default"',
        '<meta property="og:image" content="https://oolita.es/og.png">',
    ]:
        if needle not in text:
            raise SystemExit(f"Social audit invariant missing in {path}: {needle}")
    social_head = text.split("</head>", 1)[0]
    if "what-is-an-ooid" in social_head or "que-es-un-oolito" in social_head:
        raise SystemExit(f"Inherited ooid social metadata remains in {path}")

for path, expected_title in [
    ("ediciones/index.html", "Ediciones: libros, textiles y campo · OOLITA"),
    ("en/editions/index.html", "Editions: books, textiles and fieldwork · OOLITA"),
]:
    _, text = read(path)
    title = re.search(r"<title>(.*?)</title>", text, flags=re.S).group(1)
    if title != expected_title or len(title) > 60:
        raise SystemExit(f"Edition title invariant failed in {path}: {title!r}")

_, labyrinth = read("laberinto/index.html")
labyrinth_description = re.search(r'<meta name="description" content="([^"]+)">', labyrinth).group(1)
if len(labyrinth_description) > 160 or labyrinth_description.count("Cómo llegar") != 1:
    raise SystemExit("Spanish labyrinth description is still duplicated or too long")

for path, canonical, rights in [
    ("privacidad/index.html", f"{BASE}/privacidad/", "Agencia Española de Protección de Datos"),
    ("en/privacy/index.html", f"{BASE}/en/privacy/", "Spanish Data Protection Agency"),
]:
    _, text = read(path)
    for needle in [
        f'<link rel="canonical" href="{canonical}">',
        '<link rel="alternate" hreflang="x-default"',
        "Raquel Costantini",
        "oolita@tutamail.com",
        "cloudflare-customer-dpa",
        rights,
    ]:
        if needle not in text:
            raise SystemExit(f"Privacy invariant missing in {path}: {needle}")

for page in ROOT.rglob("index.html"):
    text = page.read_text(encoding="utf-8")
    language = "en" if re.search(r'<html\s+lang=["\']en(?:-[^"\']+)?["\']', text, flags=re.I) else "es"
    policy = "/en/privacy/" if language == "en" else "/privacidad/"
    footer = re.search(r'<footer\b[\s\S]*?</footer>', text, flags=re.I)
    if not footer or f'href="{policy}"' not in footer.group(0):
        raise SystemExit(f"Privacy footer link missing in {page.relative_to(ROOT)}")
    if 'id="oolita-audit-fixes-style"' not in text:
        raise SystemExit(f"Audit interaction style missing in {page.relative_to(ROOT)}")


class StructureParser(HTMLParser):
    """Small dependency-free check for the structural regressions in scope."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tags: dict[str, int] = {}
        self.ids: list[str] = []
        self.links: list[str] = []
        self.navs: list[dict[str, str | None]] = []
        self.language = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        self.tags[tag] = self.tags.get(tag, 0) + 1
        if tag == "html":
            self.language = values.get("lang") or ""
        if values.get("id"):
            self.ids.append(values["id"])
        if tag == "a" and values.get("href"):
            self.links.append(values["href"])
        if tag == "nav":
            self.navs.append(values)


parsed: dict[Path, StructureParser] = {}
for page in sorted(ROOT.rglob("index.html")):
    parser = StructureParser()
    parser.feed(page.read_text(encoding="utf-8"))
    parsed[page] = parser
    relative = page.relative_to(ROOT)
    duplicates = sorted({item for item in parser.ids if parser.ids.count(item) > 1})
    if duplicates:
        raise SystemExit(f"Duplicate IDs in {relative}: {duplicates}")
    for tag in ("html", "head", "body", "main", "h1", "footer", "title"):
        if parser.tags.get(tag, 0) != 1:
            raise SystemExit(f"Unexpected {tag} count in {relative}: {parser.tags.get(tag, 0)}")
    if parser.language not in {"es", "en"}:
        raise SystemExit(f"Unexpected document language in {relative}: {parser.language!r}")
    for nav in parser.navs:
        if not nav.get("aria-label") and not nav.get("aria-labelledby"):
            raise SystemExit(f"Unnamed navigation landmark in {relative}")

for page, parser in parsed.items():
    for href in parser.links:
        url = urlsplit(href)
        if (
            url.scheme
            or url.netloc
            or href.startswith(("#", "mailto:", "tel:", "javascript:"))
            or url.path.startswith("/api/")
            or not url.path.startswith("/")
        ):
            continue
        target = ROOT / url.path.lstrip("/")
        if url.path.endswith("/"):
            target /= "index.html"
        if not target.exists():
            raise SystemExit(f"Broken internal target in {page.relative_to(ROOT)}: {href}")
        if url.fragment and target.suffix == ".html":
            target_parser = parsed.get(target)
            if target_parser is None or url.fragment not in target_parser.ids:
                raise SystemExit(f"Broken internal fragment in {page.relative_to(ROOT)}: {href}")

print("OOLITA accessibility, discovery and privacy audit fixes validated successfully.")
