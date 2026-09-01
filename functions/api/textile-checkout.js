import {
  TEXTILE,
  getTextileVariant,
  normaliseTextileSize,
  positiveMinor,
  textilePhase,
  textileRuntimeConfig,
} from '../_lib/textile-config.js';

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
  return host === 'oolita.es' || host === 'www.oolita.es' || host === 'oolita.pages.dev' || host.endsWith('.oolita.pages.dev');
}

function editionsPage(locale) {
  return locale === 'es' ? 'https://oolita.es/ediciones/' : 'https://oolita.es/en/editions/';
}

function textileSelection(style, size, locale) {
  const variant = getTextileVariant(style);
  if (!variant) return { error: 'style must be regular or oversized', status: 400 };
  const normalisedSize = normaliseTextileSize(variant, size);
  if (!normalisedSize) return { error: 'unsupported_size', sizes: variant.sizes, status: 400 };
  const normalisedLocale = locale === 'es' ? 'es' : locale === 'en' ? 'en' : null;
  if (!normalisedLocale) return { error: 'locale must be en or es', status: 400 };
  return { variant, size: normalisedSize, locale: normalisedLocale };
}

function dryRunPayload(env, variant, size) {
  const runtime = textileRuntimeConfig(env, variant);
  return {
    dry_run: true,
    phase: textilePhase(),
    live_configured: runtime.configured,
    missing: runtime.missing,
    product_key: TEXTILE.productKey,
    provider: TEXTILE.provider,
    country: TEXTILE.country,
    currency: TEXTILE.currency,
    style: variant.key,
    size,
    sku: variant.sku,
    supplier_product: variant.supplierProduct,
    production_cost_minor: variant.productionCostMinor,
    provisional_retail_minor: variant.provisionalRetailMinor,
    configured_retail_minor: runtime.retailMinor,
    configured_shipping_minor: positiveMinor(env?.TEXTILE_UK_SHIPPING_GBP_MINOR),
    supplier_api_call: false,
    creates_payment: false,
  };
}

function addFixedShipping(params, amountMinor, locale) {
  if (!Number.isInteger(amountMinor) || amountMinor < 0) return;
  params.set('shipping_options[0][shipping_rate_data][type]', 'fixed_amount');
  params.set('shipping_options[0][shipping_rate_data][fixed_amount][amount]', String(amountMinor));
  params.set('shipping_options[0][shipping_rate_data][fixed_amount][currency]', TEXTILE.currency);
  params.set(
    'shipping_options[0][shipping_rate_data][display_name]',
    locale === 'es' ? 'Envío Reino Unido' : 'UK delivery',
  );
}

async function createStripeSession({ env, variant, size, locale, retailMinor, shippingMinor, requestId }) {
  const params = new URLSearchParams();
  const page = editionsPage(locale);

  params.set('mode', 'payment');
  params.set('locale', locale);
  params.set('success_url', `https://oolita.es/api/textile-confirm?session_id={CHECKOUT_SESSION_ID}&locale=${locale}`);
  params.set('cancel_url', `${page}?textile_order=cancelled`);
  params.set('customer_creation', 'always');
  params.set('phone_number_collection[enabled]', 'true');
  params.set('shipping_address_collection[allowed_countries][0]', TEXTILE.country);
  params.set('payment_method_types[0]', 'card');

  params.set('line_items[0][price_data][currency]', TEXTILE.currency);
  params.set('line_items[0][price_data][unit_amount]', String(retailMinor));
  params.set('line_items[0][price_data][product_data][name]', variant.name);
  params.set('line_items[0][price_data][product_data][description]', `${variant.supplierProduct} · White · ${size}`);
  params.set('line_items[0][quantity]', '1');
  addFixedShipping(params, shippingMinor, locale);

  params.set('metadata[oolita_product_key]', TEXTILE.productKey);
  params.set('metadata[oolita_textile_variant]', variant.key);
  params.set('metadata[oolita_textile_size]', size);
  params.set('metadata[oolita_textile_sku]', variant.sku);
  params.set('metadata[oolita_delivery_country]', TEXTILE.country);
  params.set('metadata[oolita_fulfilment_provider]', TEXTILE.provider);
  params.set('metadata[oolita_supplier_product]', variant.supplierProduct);
  params.set('metadata[oolita_supplier_product_path]', variant.supplierProductPath);
  params.set('metadata[oolita_production_cost_minor]', String(variant.productionCostMinor));
  params.set('metadata[oolita_retail_amount_minor]', String(retailMinor));
  params.set('metadata[oolita_shipping_amount_minor]', String(shippingMinor));
  params.set('metadata[oolita_locale]', locale);
  params.set('metadata[oolita_manual_fulfilment]', 'true');

  const response = await fetch('https://api.stripe.com/v1/checkout/sessions', {
    method: 'POST',
    headers: {
      authorization: `Bearer ${env.STRIPE_SECRET_KEY}`,
      'content-type': 'application/x-www-form-urlencoded',
      'idempotency-key': `oolita-textile-${requestId}`,
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
  if (!response.ok) throw new Error(parsed?.error?.message || `Stripe returned HTTP ${response.status}`);
  if (!parsed?.id || !parsed?.url) throw new Error('Stripe did not return a Checkout Session URL');
  return parsed;
}

// Safe production diagnostic. It never creates a Stripe session and never calls a supplier.
export async function onRequestGet({ request, env }) {
  const url = new URL(request.url);
  if (url.searchParams.get('dry_run') !== '1') return json({ error: 'dry_run_required' }, 400);
  const selected = textileSelection(
    url.searchParams.get('style'),
    url.searchParams.get('size'),
    url.searchParams.get('locale'),
  );
  if (selected.error) return json(selected, selected.status);
  return json(dryRunPayload(env, selected.variant, selected.size));
}

export async function onRequestPost({ request, env }) {
  if (!originAllowed(request)) return json({ error: 'Origin not allowed' }, 403);

  let body;
  try {
    body = await request.json();
  } catch (_) {
    return json({ error: 'Expected a JSON request body' }, 400);
  }

  const selected = textileSelection(body?.style, body?.size, body?.locale);
  if (selected.error) return json(selected, selected.status);
  const { variant, size, locale } = selected;
  const runtime = textileRuntimeConfig(env, variant);

  if (body?.dry_run === true) return json(dryRunPayload(env, variant, size));

  const phase = textilePhase();
  if (phase !== 'sale') {
    return json({ error: 'textile_not_released', release_at: TEXTILE.releaseAt }, 409);
  }
  if (!runtime.configured) {
    return json({ error: 'textile_checkout_not_configured', missing: runtime.missing }, 503);
  }

  const requestId =
    typeof body?.request_id === 'string' && /^[A-Za-z0-9_-]{8,80}$/.test(body.request_id)
      ? body.request_id
      : crypto.randomUUID();

  try {
    const session = await createStripeSession({
      env,
      variant,
      size,
      locale,
      retailMinor: runtime.retailMinor,
      shippingMinor: runtime.shippingMinor,
      requestId,
    });
    return json({
      session_id: session.id,
      url: session.url,
      style: variant.key,
      size,
      currency: TEXTILE.currency,
      retail_amount_minor: runtime.retailMinor,
      shipping_amount_minor: runtime.shippingMinor,
      fulfilment: 'manual',
    });
  } catch (error) {
    return json({ error: 'textile_checkout_creation_failed', detail: String(error.message || error).slice(0, 300) }, 502);
  }
}
