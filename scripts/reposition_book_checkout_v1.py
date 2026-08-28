#!/usr/bin/env python3
"""Place and wire the OOLITA book checkout beside the availability row.

The rendered page always ships with an inert staged control. At runtime the
control asks /api/commerce-status for the authoritative launch phase and route
readiness. It becomes usable only when the server says checkout is open. The
customer chooses delivery territory; site language never determines fulfilment.
"""
from __future__ import annotations

from html import unescape
from pathlib import Path
import re
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site")

PAGES = {
    "ediciones/libro/index.html": {
        "notify": "Avísame por correo",
        "staged_label": "Comprar el libro · próximamente",
        "live_label": "Comprar el libro",
        "preorder_label": "Reservar el libro",
        "staged_title": "Compra todavía no disponible",
        "page_marker": "48 páginas",
        "offer": "es_eur",
        "currency": "EUR",
    },
    "en/editions/book/index.html": {
        "notify": "Let me know by email",
        "staged_label": "Buy the book · coming soon",
        "live_label": "Buy the book",
        "preorder_label": "Pre-order the book",
        "staged_title": "Checkout is not active yet",
        "page_marker": "48 pages",
        "offer": "en_gbp",
        "currency": "GBP",
    },
}

STYLE = r'''<style id="oolita-book-buy-position-v1">
.oolita-book-buy{display:inline-flex;align-items:baseline;gap:.32em;margin-left:1rem;padding:0;border:0;background:none;color:inherit;text-decoration:underline;text-decoration-thickness:1px;text-underline-offset:.16em;font:inherit;line-height:inherit;white-space:nowrap;vertical-align:baseline;cursor:pointer}
.oolita-book-buy[data-commerce-state="staged"]{display:none!important}
.oolita-book-buy .oolita-book-buy-arrow{display:none}
.oolita-book-checkout-dialog{max-width:32rem;width:calc(100% - 2rem);border:1px solid currentColor;background:#fff;color:#111;padding:1.25rem;font:inherit}
.oolita-book-checkout-dialog::backdrop{background:rgba(0,0,0,.35)}
.oolita-book-checkout-dialog form{display:grid;gap:.9rem}
.oolita-book-checkout-dialog label{display:grid;gap:.35rem}
.oolita-book-checkout-dialog select,.oolita-book-checkout-dialog input,.oolita-book-checkout-dialog button{font:inherit;padding:.55rem .7rem}
.oolita-book-checkout-dialog menu{display:flex;gap:.6rem;justify-content:flex-end;margin:0;padding:0}
.oolita-book-checkout-error{min-height:1.2em;margin:0}
.oolita-book-postcode[hidden]{display:none!important}
@media (max-width:720px){.oolita-book-buy{margin-left:0;margin-top:.55rem}}
</style>'''

RUNTIME = r'''<script id="oolita-book-checkout-runtime-v1">
(() => {
  const button = document.querySelector('[data-checkout="book"]');
  if (!button) return;
  const locale = document.documentElement.lang && document.documentElement.lang.toLowerCase().startsWith('es') ? 'es' : 'en';
  const copy = locale === 'es'
    ? {
        preorder: 'Reservar el libro', sale: 'Comprar el libro', title: 'Entrega',
        country: 'País de entrega', postcode: 'Código postal', continueText: 'Continuar al pago', cancel: 'Cancelar',
        delivery: 'La entrega se calcula con BookVault para tu código postal y se añade al pago.',
        unavailable: 'todavía no disponible', postcodeError: 'Introduce un código postal válido del Reino Unido.',
        error: 'No se pudo iniciar el pago. Inténtalo de nuevo.'
      }
    : {
        preorder: 'Pre-order the book', sale: 'Buy the book', title: 'Delivery',
        country: 'Delivery country', postcode: 'Postcode', continueText: 'Continue to payment', cancel: 'Cancel',
        delivery: 'Delivery is quoted from BookVault for your postcode and added at checkout.',
        unavailable: 'not yet available', postcodeError: 'Enter a valid UK postcode.',
        error: 'Checkout could not be started. Please try again.'
      };
  const countryNames = locale === 'es'
    ? {GB: 'Reino Unido', ES: 'España'}
    : {GB: 'United Kingdom', ES: 'Spain'};
  let status = null;

  function labelButton(phase) {
    const label = button.querySelector('span:last-child') || button;
    label.textContent = phase === 'preorder' ? copy.preorder : copy.sale;
  }

  function setReady(next) {
    status = next;
    const ready = ['preorder', 'sale'].includes(next.phase) && Array.isArray(next.checkout_countries) && next.checkout_countries.length > 0;
    if (!ready) {
      button.dataset.commerceState = 'staged';
      button.setAttribute('aria-disabled', 'true');
      button.setAttribute('tabindex', '-1');
      return;
    }
    button.dataset.commerceState = next.phase;
    button.setAttribute('aria-disabled', 'false');
    button.setAttribute('tabindex', '0');
    button.removeAttribute('title');
    labelButton(next.phase);
  }

  function normalizeUkPostcode(value) {
    return String(value || '').trim().toUpperCase().replace(/\s+/g, ' ');
  }

  function validUkPostcode(value) {
    return /^[A-Z]{1,2}\d[A-Z\d]?\d[A-Z]{2}$/.test(normalizeUkPostcode(value).replace(/\s+/g, ''));
  }

  function ensureDialog() {
    let dialog = document.getElementById('oolita-book-checkout-dialog');
    if (dialog) return dialog;
    dialog = document.createElement('dialog');
    dialog.id = 'oolita-book-checkout-dialog';
    dialog.className = 'oolita-book-checkout-dialog';
    dialog.innerHTML = `<form method="dialog">
      <strong>${copy.title}</strong>
      <label>${copy.country}<select name="country" required></select></label>
      <label class="oolita-book-postcode" hidden>${copy.postcode}<input name="postal_code" type="text" autocomplete="postal-code" inputmode="text" maxlength="9"></label>
      <p>${copy.delivery}</p>
      <p class="oolita-book-checkout-error" role="status" aria-live="polite"></p>
      <menu><button value="cancel" type="button" data-cancel>${copy.cancel}</button><button value="continue" type="submit">${copy.continueText}</button></menu>
    </form>`;
    document.body.appendChild(dialog);

    const select = dialog.querySelector('select[name="country"]');
    const postcodeWrap = dialog.querySelector('.oolita-book-postcode');
    const postcode = dialog.querySelector('input[name="postal_code"]');
    const syncPostcode = () => {
      const needsPostcode = select.value === 'GB';
      postcodeWrap.hidden = !needsPostcode;
      postcode.required = needsPostcode;
      if (!needsPostcode) postcode.value = '';
    };
    select.addEventListener('change', syncPostcode);
    dialog.querySelector('[data-cancel]').addEventListener('click', () => dialog.close());
    dialog.querySelector('form').addEventListener('submit', async (event) => {
      event.preventDefault();
      const error = dialog.querySelector('.oolita-book-checkout-error');
      const submit = dialog.querySelector('button[type="submit"]');
      error.textContent = '';
      const country = select.value;
      const postalCode = normalizeUkPostcode(postcode.value);
      if (country === 'GB' && !validUkPostcode(postalCode)) {
        error.textContent = copy.postcodeError;
        postcode.focus();
        return;
      }
      submit.disabled = true;
      try {
        const response = await fetch('/api/create-checkout', {
          method: 'POST',
          headers: {'content-type': 'application/json'},
          body: JSON.stringify({country, locale, postal_code: postalCode, request_id: crypto.randomUUID()})
        });
        const body = await response.json().catch(() => ({}));
        if (!response.ok || !body.url) throw new Error(body.error || 'checkout_creation_failed');
        window.location.assign(body.url);
      } catch (_) {
        error.textContent = copy.error;
        submit.disabled = false;
      }
    });
    dialog._oolitaSyncPostcode = syncPostcode;
    return dialog;
  }

  function openCheckout() {
    if (!status || !['preorder', 'sale'].includes(status.phase) || !status.checkout_countries?.length) return;
    const dialog = ensureDialog();
    const select = dialog.querySelector('select[name="country"]');
    select.replaceChildren();
    const supported = Array.isArray(status.supported_countries) && status.supported_countries.length ? status.supported_countries : ['GB', 'ES'];
    const configured = new Set(status.checkout_countries);
    for (const code of supported) {
      const option = document.createElement('option');
      option.value = code;
      option.disabled = !configured.has(code);
      option.textContent = `${countryNames[code] || code}${configured.has(code) ? '' : ` — ${copy.unavailable}`}`;
      if (configured.has(code) && !select.value) option.selected = true;
      select.appendChild(option);
    }
    if (typeof dialog._oolitaSyncPostcode === 'function') dialog._oolitaSyncPostcode();
    dialog.showModal();
  }

  button.addEventListener('click', (event) => {
    event.preventDefault();
    if (button.getAttribute('aria-disabled') === 'true') return;
    openCheckout();
  });
  button.addEventListener('keydown', (event) => {
    if ((event.key === 'Enter' || event.key === ' ') && button.getAttribute('aria-disabled') !== 'true') {
      event.preventDefault();
      openCheckout();
    }
  });

  async function refresh() {
    try {
      const response = await fetch('/api/commerce-status', {cache: 'no-store'});
      if (!response.ok) throw new Error('status');
      setReady(await response.json());
    } catch (_) {
      setReady({phase: 'interest', checkout_countries: []});
    }
  }
  refresh();
  setInterval(refresh, 300000);
})();
</script>'''


def rendered(fragment: str) -> str:
    return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", " ", fragment))).strip()


def attr(fragment: str, name: str) -> str | None:
    match = re.search(rf'\b{re.escape(name)}=["\']([^"\']+)["\']', fragment, flags=re.I)
    return match.group(1) if match else None


def find_anchor_with_text(text: str, phrase: str) -> re.Match[str]:
    matches = [m for m in re.finditer(r'<a\b[^>]*>[\s\S]*?</a>', text, flags=re.I) if phrase in rendered(m.group(0))]
    if len(matches) != 1:
        raise SystemExit(f"Expected exactly one anchor containing {phrase!r}; found {len(matches)}")
    return matches[0]


def staged_checkout(spec: dict[str, str]) -> str:
    return (
        f'<a class="oolita-book-buy" data-checkout="book" '
        f'data-commerce-offer="{spec["offer"]}" data-commerce-currency="{spec["currency"]}" '
        f'data-commerce-state="staged" data-book-pages="{spec["page_marker"]}" '
        f'data-oolita-event="book-interest" role="button" aria-disabled="true" tabindex="-1" '
        f'title="{spec["staged_title"]}">'
        f'<span class="oolita-book-buy-arrow">→</span><span>{spec["staged_label"]}</span></a>'
    )


def normalize_checkout(original: str, spec: dict[str, str]) -> str:
    offer = attr(original, "data-commerce-offer") or spec["offer"]
    currency = attr(original, "data-commerce-currency") or spec["currency"]
    analytics = attr(original, "data-oolita-event") or "book-interest"
    if analytics != "book-interest":
        raise SystemExit(f"Unexpected book analytics event: {analytics!r}")
    return (
        f'<a class="oolita-book-buy" data-checkout="book" data-commerce-offer="{offer}" '
        f'data-commerce-currency="{currency}" data-commerce-state="staged" '
        f'data-book-pages="{spec["page_marker"]}" data-oolita-event="book-interest" '
        f'role="button" aria-disabled="true" tabindex="-1" title="{spec["staged_title"]}">'
        f'<span class="oolita-book-buy-arrow">→</span><span>{spec["staged_label"]}</span></a>'
    )


def reposition(rel: str, spec: dict[str, str]) -> None:
    path = ROOT / rel
    if not path.is_file():
        raise SystemExit(f"Missing book page: {rel}")
    text = path.read_text(encoding="utf-8")
    checkout_re = re.compile(r'<a\b(?=[^>]*\bdata-checkout=["\']book["\'])[^>]*>[\s\S]*?</a>', flags=re.I)
    matches = list(checkout_re.finditer(text))
    if len(matches) > 1:
        raise SystemExit(f"Expected at most one book checkout in {rel}; found {len(matches)}")
    if matches:
        compact = normalize_checkout(matches[0].group(0), spec)
        text = text[:matches[0].start()] + text[matches[0].end():]
    else:
        compact = staged_checkout(spec)
        print(f"book checkout bootstrap restored inert staged hook: {rel}")

    notify = find_anchor_with_text(text, spec["notify"])
    text = text[:notify.end()] + "\n" + compact + text[notify.end():]

    style_re = re.compile(r'<style\s+id=["\']oolita-book-buy-position-v1["\']>[\s\S]*?</style>', flags=re.I)
    text = style_re.sub(lambda _: STYLE, text, count=1) if style_re.search(text) else text.replace('</head>', STYLE + '\n</head>', 1)
    runtime_re = re.compile(r'<script\s+id=["\']oolita-book-checkout-runtime-v1["\']>[\s\S]*?</script>', flags=re.I)
    text = runtime_re.sub(lambda _: RUNTIME, text, count=1) if runtime_re.search(text) else text.replace('</body>', RUNTIME + '\n</body>', 1)
    path.write_text(text, encoding="utf-8")

    final = path.read_text(encoding="utf-8")
    if len(list(checkout_re.finditer(final))) != 1:
        raise SystemExit(f"Book checkout count changed unexpectedly in {rel}")
    if final.count('id="oolita-book-buy-position-v1"') != 1 or final.count('id="oolita-book-checkout-runtime-v1"') != 1:
        raise SystemExit(f"Book commerce assets missing or duplicated in {rel}")
    if spec["page_marker"] not in final:
        raise SystemExit(f"Book page-count invariant missing after checkout placement in {rel}")
    checkout = checkout_re.search(final)
    assert checkout is not None
    if 'data-commerce-state="staged"' not in checkout.group(0) or 'href=' in checkout.group(0):
        raise SystemExit(f"Rendered checkout must remain inert until runtime status check in {rel}")
    if '/api/commerce-status' not in final or '/api/create-checkout' not in final or 'postal_code' not in final:
        raise SystemExit(f"Runtime commerce endpoints or postcode quote input missing in {rel}")
    print(f"book checkout positioned and runtime-wired: {rel}")


for rel, spec in PAGES.items():
    reposition(rel, spec)

print("OOLITA book checkout placement, postcode quote and launch-clock runtime validated on both language routes.")
