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

function normalizeUkPostcode(value) {
  if (typeof value !== 'string') return '';
  return value.trim().toUpperCase().replace(/\s+/g, ' ');
}

function validUkPostcode(value) {
  return /^[A-Z]{1,2}\d[A-Z\d]?\s?\d[A-Z]{2}$/.test(value.replace(/\s+/g, ''));
}

function bookVaultHeaders(env) {
  return {
    Authorization: `basic ${env.BOOKVAULT_API_KEY}`,
    accept: 'application/json',
    'content-type': 'application/json',
  };
}

function shipmentDateFor(phase) {
  return phase === 'preorder' ? BOOK.releaseAt : new Date().toISOString();
}

function deliveryFromService(service) {
  const dispatch = service?.Dispatch || service?.dispatch || service;
  const rawAmount = dispatch?.DelTotal ?? dispatch?.delTotal ?? service?.DelTotal ?? service?.delTotal;
  const amountMajor = Number(rawAmount);
  const serviceId = Number(dispatch?.ServID ?? dispatch?.servID ?? service?.ServID ?? service?.servID);
  const tracked = dispatch?.Tracked ?? dispatch?.tracked ?? service?.Tracked ?? service?.tracked;
  if (!Number.isFinite(amountMajor) || amountMajor < 0 || !Number.isInteger(serviceId) || serviceId <= 0) return null;
  if (tracked === false) return null;

  const minDays = Number(dispatch?.MinDeliveryDays ?? dispatch?.minDeliveryDays ?? service?.MinDeliveryDays);
  const maxDays = Number(dispatch?.MaxDeliveryDays ?? dispatch?.maxDeliveryDays ?? service?.MaxDeliveryDays);
  return {
    serviceId,
    name: String(dispatch?.ServName ?? dispatch?.servName ?? service?.ServName ?? 'Tracked delivery').slice(0, 100),
    code: String(dispatch?.ServCode ?? dispatch?.servCode ?? service?.ServCode ?? '').slice(0, 100),
    amountMinor: Math.round(amountMajor * 100),
    minDays: Number.isInteger(minDays) && minDays >= 0 ? minDays : null,
    maxDays: Number.isInteger(maxDays) && maxDays >= 0 ? maxDays : null,
  };
}

async function quoteBookVaultDelivery(env, postcode, phase) {
  const payload = {
    OrderLines: [{
      ISBN: env.BOOKVAULT_OOLITA_ISBN || BOOK.isbn13,
      OrderQuantity: 1,
    }],
    CountryCode: 'GB',
    ServiceLevel: 'CheapestTracked',
    PartnerID: 0,
    Currency: 'GBP',
    ShipmentDate: shipmentDateFor(phase),
    AreaCode: postcode,
  };

  const response = await fetch('https://api.bookvault.app/v3/Dispatch', {
    method: 'POST',
    headers: bookVaultHeaders(env),
    body: JSON.stringify(payload),
  });
  const text = await response.text();
  let parsed = null;
  try {
    parsed = text ? JSON.parse(text) : null;
  } catch (_) {
    parsed = null;
  }
  if (!response.ok) {
    throw new Error(`BookVault delivery quote returned HTTP ${response.status}: ${text.slice(0, 250)}`);
  }

  const services = Array.isArray(parsed?.Services)
    ? parsed.Services
    : Array.isArray(parsed?.services)
      ? parsed.services
      : [];
  const options = services.map(deliveryFromService).filter(Boolean).sort((a, b) => a.amountMinor - b.amountMinor);
  if (!options.length) throw new Error('BookVault returned no usable tracked delivery service');
  return options[0];
}

function addStripeShipping(params, quote, locale) {
  params.set('shipping_options[0][shipping_rate_data][type]', 'fixed_amount');
  params.set('shipping_options[0][shipping_rate_data][fixed_amount][amount]', String(quote.amountMinor));
  params.set('shipping_options[0][shipping_rate_data][fixed_amount][currency]', 'gbp');
  params.set(
    'shipping_options[0][shipping_rate_data][display_name]',
    locale === 'es' ? `Entrega con seguimiento · ${quote.name}` : `Tracked delivery · ${quote.name}`,
  );
  if (quote.minDays != null && quote.maxDays != null) {
    params.set('shipping_options[0][shipping_rate_data][delivery_estimate][minimum][unit]', 'business_day');
    params.set('shipping_options[0][shipping_rate_data][delivery_estimate][minimum][value]', String(Math.max(1, quote.minDays)));
    params.set('shipping_options[0][shipping_rate_data][delivery_estimate][maximum][unit]', 'business_day');
    params.set('shipping_options[0][shipping_rate_data][delivery_estimate][maximum][value]', String(Math.max(1, quote.maxDays)));
  }
}

async function createStripeCheckout({ env, route, phase, locale, requestId, postcode }) {
  const params = new URLSearchParams();
  const page = pageFor(locale);

  let deliveryQuote = null;
  if (route.provider === 'bookvault') {
    deliveryQuote = await quoteBookVaultDelivery(env, postcode, phase);
  } else {
    throw new Error(`Delivery quoting is not implemented for ${route.provider}`);
  }

  params.set('mode', 'payment');
  params.set('locale', locale);
  params.set('success_url', `${page}?order=success&session_id={CHECKOUT_SESSION_ID}`);
  params.set('cancel_url', `${page}?order=cancelled`);
  params.set('customer_creation', 'always');
  params.set('phone_number_collection[enabled]', 'true');
  params.set('shipping_address_collection[allowed_countries][0]', route.country);
  params.set('line_items[0][price]', env[route.priceEnv]);
  params.set('line_items[0][quantity]', '1');
  addStripeShipping(params, deliveryQuote, locale);
  params.set('metadata[oolita_product_key]', BOOK.productKey);
  params.set('metadata[oolita_isbn13]', BOOK.isbn13);
  params.set('metadata[oolita_delivery_country]', route.country);
  params.set('metadata[oolita_fulfilment_provider]', route.provider);
  params.set('metadata[oolita_sales_phase]', phase);
  params.set('metadata[oolita_release_at]', BOOK.releaseAt);
  params.set('metadata[oolita_locale]', locale);
  params.set('metadata[oolita_quote_postcode]', postcode);
  params.set('metadata[oolita_bookvault_service_id]', String(deliveryQuote.serviceId));
  params.set('metadata[oolita_bookvault_service_code]', deliveryQuote.code);
  params.set('metadata[oolita_shipping_amount_minor]', String(deliveryQuote.amountMinor));

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
  return { session: parsed, deliveryQuote };
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

  let postcode = '';
  if (readiness.route.provider === 'bookvault') {
    postcode = normalizeUkPostcode(body?.postal_code);
    if (!postcode || !validUkPostcode(postcode)) {
      return json({ error: 'valid_uk_postcode_required' }, 400);
    }
  }

  const requestId =
    typeof body?.request_id === 'string' && /^[A-Za-z0-9_-]{8,80}$/.test(body.request_id)
      ? body.request_id
      : crypto.randomUUID();

  try {
    const { session, deliveryQuote } = await createStripeCheckout({
      env,
      route: readiness.route,
      phase: readiness.phase,
      locale,
      requestId,
      postcode,
    });
    return json({
      session_id: session.id,
      url: session.url,
      phase: readiness.phase,
      country: readiness.route.country,
      currency: readiness.route.currency,
      shipping_amount_minor: deliveryQuote.amountMinor,
    });
  } catch (error) {
    return json({ error: 'checkout_creation_failed', detail: String(error.message || error).slice(0, 300) }, 502);
  }
}
