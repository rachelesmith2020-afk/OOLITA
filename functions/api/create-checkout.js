import { BOOK, checkoutReadiness } from '../_lib/commerce-config.js';

function json(body, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      'content-type': 'application/json; charset=utf-8',
      'cache-control': 'no-store',
    },
  });
}

function originAllowed(request) {
  const origin = request.headers.get('origin');
  if (!origin) return true;
  let parsed;
  try {
    parsed = new URL(origin);
  } catch (_) {
    return false;
  }
  if (parsed.protocol !== 'https:') return false;
  const host = parsed.hostname.toLowerCase();
  return (
    host === 'oolita.es' ||
    host === 'www.oolita.es' ||
    host === 'oolita.pages.dev' ||
    host.endsWith('.oolita.pages.dev')
  );
}

function pageFor(locale) {
  return locale === 'es'
    ? 'https://oolita.es/ediciones/libro/'
    : 'https://oolita.es/en/editions/book/';
}

async function createStripeCheckout({ env, route, phase, locale, requestId }) {
  const params = new URLSearchParams();
  const page = pageFor(locale);

  params.set('mode', 'payment');
  params.set('locale', locale);
  params.set('success_url', `${page}?order=success&session_id={CHECKOUT_SESSION_ID}`);
  params.set('cancel_url', `${page}?order=cancelled`);
  params.set('customer_creation', 'always');
  params.set('phone_number_collection[enabled]', 'true');
  params.set('shipping_address_collection[allowed_countries][0]', route.country);
  params.set('line_items[0][price]', env[route.priceEnv]);
  params.set('line_items[0][quantity]', '1');
  params.set('shipping_options[0][shipping_rate]', env[route.shippingRateEnv]);
  params.set('metadata[oolita_product_key]', BOOK.productKey);
  params.set('metadata[oolita_isbn13]', BOOK.isbn13);
  params.set('metadata[oolita_delivery_country]', route.country);
  params.set('metadata[oolita_fulfilment_provider]', route.provider);
  params.set('metadata[oolita_sales_phase]', phase);
  params.set('metadata[oolita_release_at]', BOOK.releaseAt);
  params.set('metadata[oolita_locale]', locale);

  const response = await fetch('https://api.stripe.com/v1/checkout/sessions', {
    method: 'POST',
    headers: {
      authorization: `Bearer ${env.STRIPE_SECRET_KEY}`,
      'content-type': 'application/x-www-form-urlencoded',
      'idempotency-key': `oolita-checkout-${requestId}`,
    },
    body: params.toString(),
  });

  const text = await response.text();
  let parsed = null;
  try {
    parsed = text ? JSON.parse(text) : null;
  } catch (_) {
    parsed = null;
  }

  if (!response.ok) {
    const message = parsed?.error?.message || `Stripe returned HTTP ${response.status}`;
    throw new Error(message);
  }
  if (!parsed?.id || !parsed?.url) throw new Error('Stripe did not return a Checkout Session URL');
  return parsed;
}

export async function onRequestPost({ request, env }) {
  if (!originAllowed(request)) return json({ error: 'Origin not allowed' }, 403);

  let body;
  try {
    body = await request.json();
  } catch (_) {
    return json({ error: 'Expected a JSON request body' }, 400);
  }

  const country = typeof body?.country === 'string' ? body.country.trim().toUpperCase() : '';
  const locale = body?.locale === 'es' ? 'es' : body?.locale === 'en' ? 'en' : null;
  if (!country || !locale) return json({ error: 'country and locale are required' }, 400);

  const readiness = checkoutReadiness(country, env);
  if (!readiness.ready) {
    const status = readiness.reason === 'preorder_not_open' ? 409 : readiness.reason === 'unsupported_country' ? 400 : 503;
    return json({
      error: readiness.reason,
      phase: readiness.phase,
      preorder_opens_at: BOOK.preorderOpensAt,
      release_at: BOOK.releaseAt,
    }, status);
  }

  const requestId =
    typeof body?.request_id === 'string' && /^[A-Za-z0-9_-]{8,80}$/.test(body.request_id)
      ? body.request_id
      : crypto.randomUUID();

  try {
    const session = await createStripeCheckout({
      env,
      route: readiness.route,
      phase: readiness.phase,
      locale,
      requestId,
    });
    return json({
      session_id: session.id,
      url: session.url,
      phase: readiness.phase,
      country: readiness.route.country,
      currency: readiness.route.currency,
    });
  } catch (error) {
    return json({ error: 'checkout_creation_failed', detail: String(error.message || error).slice(0, 300) }, 502);
  }
}
