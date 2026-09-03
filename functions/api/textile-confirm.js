import {
  TEXTILE,
  getTextileStorefront,
  getTextileVariant,
  normaliseTextileSize,
  positiveMinor,
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

function textilePage(storefront, state, sessionId = '') {
  const url = new URL(storefront.page);
  url.searchParams.set('textile_order', state);
  if (sessionId) url.searchParams.set('session_id', sessionId);
  return url.toString();
}

async function loadStripeSession(env, sessionId) {
  const response = await fetch(`https://api.stripe.com/v1/checkout/sessions/${encodeURIComponent(sessionId)}`, {
    headers: { authorization: `Bearer ${env.STRIPE_SECRET_KEY}` },
  });
  const text = await response.text();
  let parsed = null;
  try {
    parsed = text ? JSON.parse(text) : null;
  } catch (_) {
    parsed = null;
  }
  if (!response.ok) throw new Error(parsed?.error?.message || `Stripe returned HTTP ${response.status}`);
  return parsed;
}

function shippingFrom(session) {
  return session?.shipping_details || session?.collected_information?.shipping_details || null;
}

async function ensureTextileOrdersTable(db) {
  await db.prepare(`
    CREATE TABLE IF NOT EXISTS textile_orders (
      stripe_session_id TEXT PRIMARY KEY,
      stripe_payment_intent TEXT,
      state TEXT NOT NULL,
      provider TEXT NOT NULL,
      product_key TEXT NOT NULL,
      variant TEXT NOT NULL,
      size TEXT NOT NULL,
      sku TEXT NOT NULL,
      supplier_product TEXT NOT NULL,
      customer_email TEXT,
      customer_name TEXT,
      customer_phone TEXT,
      shipping_address_json TEXT NOT NULL,
      retail_amount_minor INTEGER NOT NULL,
      shipping_amount_minor INTEGER NOT NULL,
      amount_total_minor INTEGER NOT NULL,
      currency TEXT NOT NULL,
      created_at TEXT NOT NULL,
      updated_at TEXT NOT NULL
    )
  `).run();
}

async function recordManualOrder(db, session, variant, size, shipping) {
  const customer = session.customer_details || {};
  const retailMinor = positiveMinor(session.metadata?.oolita_retail_amount_minor);
  const shippingMinor = positiveMinor(session.metadata?.oolita_shipping_amount_minor);
  if (retailMinor == null || shippingMinor == null) throw new Error('Missing textile price metadata');

  const expectedTotal = retailMinor + shippingMinor;
  const amountTotal = Number(session.amount_total);
  if (!Number.isInteger(amountTotal) || amountTotal !== expectedTotal) {
    throw new Error('Paid textile total does not match checkout metadata');
  }

  const now = new Date().toISOString();
  await db.prepare(`
    INSERT INTO textile_orders (
      stripe_session_id,
      stripe_payment_intent,
      state,
      provider,
      product_key,
      variant,
      size,
      sku,
      supplier_product,
      customer_email,
      customer_name,
      customer_phone,
      shipping_address_json,
      retail_amount_minor,
      shipping_amount_minor,
      amount_total_minor,
      currency,
      created_at,
      updated_at
    ) VALUES (?1, ?2, 'manual_pending', ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10, ?11, ?12, ?13, ?14, ?15, ?16, ?17, ?17)
    ON CONFLICT(stripe_session_id) DO NOTHING
  `).bind(
    session.id,
    typeof session.payment_intent === 'string' ? session.payment_intent : null,
    TEXTILE.provider,
    TEXTILE.productKey,
    variant.key,
    size,
    variant.sku,
    variant.supplierProduct,
    customer.email || session.customer_email || null,
    shipping.name || customer.name || null,
    customer.phone || null,
    JSON.stringify(shipping.address || {}),
    retailMinor,
    shippingMinor,
    amountTotal,
    TEXTILE.currency,
    now,
  ).run();
}

export async function onRequestGet({ request, env }) {
  if (!env?.STRIPE_SECRET_KEY) return json({ error: 'Stripe is not configured' }, 503);
  if (!env?.OOLITA_SUBSCRIBERS) return json({ error: 'Orders database is not configured' }, 503);

  const url = new URL(request.url);
  const sessionId = url.searchParams.get('session_id') || '';
  if (!/^cs_[A-Za-z0-9_]+$/.test(sessionId)) return json({ error: 'Invalid Checkout Session ID' }, 400);

  let session;
  try {
    session = await loadStripeSession(env, sessionId);
  } catch (error) {
    return json({ error: 'stripe_session_lookup_failed', detail: String(error.message || error).slice(0, 300) }, 502);
  }

  if (session.metadata?.oolita_product_key !== TEXTILE.productKey) {
    return json({ error: 'Not an OOLITA textile Checkout Session' }, 422);
  }
  if (session.metadata?.oolita_fulfilment_provider !== TEXTILE.provider) {
    return json({ error: 'Unexpected textile fulfilment provider' }, 422);
  }
  if (session.currency?.toLowerCase?.() !== TEXTILE.currency) {
    return json({ error: 'Unexpected textile checkout currency' }, 422);
  }

  const storefront = getTextileStorefront(session.metadata?.oolita_storefront);
  if (!storefront || session.metadata?.oolita_locale !== storefront.locale) {
    return json({ error: 'Invalid textile storefront metadata' }, 422);
  }

  const variant = getTextileVariant(session.metadata?.oolita_textile_variant);
  const size = normaliseTextileSize(variant, session.metadata?.oolita_textile_size);
  if (!variant || !size || session.metadata?.oolita_textile_sku !== variant.sku) {
    return json({ error: 'Invalid textile variant metadata' }, 422);
  }

  if (session.payment_status !== 'paid') {
    return Response.redirect(textilePage(storefront, 'payment_pending', sessionId), 303);
  }

  const shipping = shippingFrom(session);
  const address = shipping?.address || {};
  if (!shipping?.name || !address.line1 || !address.city || !address.postal_code || address.country !== TEXTILE.country) {
    return json({ error: 'Complete GB shipping address is required' }, 422);
  }

  try {
    await ensureTextileOrdersTable(env.OOLITA_SUBSCRIBERS);
    await recordManualOrder(env.OOLITA_SUBSCRIBERS, session, variant, size, shipping);
  } catch (error) {
    return json({ error: 'textile_order_record_failed', detail: String(error.message || error).slice(0, 300) }, 500);
  }

  return Response.redirect(textilePage(storefront, 'success', sessionId), 303);
}
