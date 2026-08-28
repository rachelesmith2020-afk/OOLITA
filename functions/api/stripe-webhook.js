import { BOOK, getRoute } from '../_lib/commerce-config.js';

const DEFAULT_PRODUCTION_LEVEL = 'Standard';
const DEFAULT_REQUESTED_SERVICE = 'CheapestTracked';
const SIGNATURE_TOLERANCE_SECONDS = 300;
const PROCESSING_LEASE_MS = 120000;

function json(body, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'content-type': 'application/json; charset=utf-8' },
  });
}

function toHex(buffer) {
  return Array.from(new Uint8Array(buffer), (b) => b.toString(16).padStart(2, '0')).join('');
}

function constantTimeEqual(a, b) {
  if (typeof a !== 'string' || typeof b !== 'string' || a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i += 1) diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return diff === 0;
}

async function validStripeSignature(rawBody, signatureHeader, secret) {
  if (!signatureHeader || !secret) return false;
  const fields = signatureHeader.split(',').map((part) => part.trim());
  const timestampField = fields.find((part) => part.startsWith('t='));
  const signatures = fields.filter((part) => part.startsWith('v1=')).map((part) => part.slice(3));
  if (!timestampField || signatures.length === 0) return false;

  const timestamp = Number(timestampField.slice(2));
  if (!Number.isFinite(timestamp)) return false;
  if (Math.abs(Math.floor(Date.now() / 1000) - timestamp) > SIGNATURE_TOLERANCE_SECONDS) return false;

  const key = await crypto.subtle.importKey(
    'raw',
    new TextEncoder().encode(secret),
    { name: 'HMAC', hash: 'SHA-256' },
    false,
    ['sign'],
  );
  const digest = toHex(
    await crypto.subtle.sign('HMAC', key, new TextEncoder().encode(`${timestamp}.${rawBody}`)),
  );
  return signatures.some((candidate) => constantTimeEqual(digest, candidate));
}

async function ensureOrdersTable(db) {
  await db.prepare(`
    CREATE TABLE IF NOT EXISTS commerce_orders (
      stripe_session_id TEXT PRIMARY KEY,
      stripe_event_id TEXT NOT NULL,
      provider TEXT NOT NULL,
      state TEXT NOT NULL,
      provider_doc_ref TEXT NOT NULL,
      provider_order_ref TEXT,
      last_error TEXT,
      updated_at TEXT NOT NULL
    )
  `).run();
}

async function getOrder(db, sessionId) {
  return db.prepare(
    'SELECT provider, state, updated_at, provider_order_ref FROM commerce_orders WHERE stripe_session_id = ?1',
  ).bind(sessionId).first();
}

async function claimOrder(db, sessionId, eventId, provider, docRef) {
  const now = new Date().toISOString();
  const inserted = await db.prepare(`
    INSERT INTO commerce_orders
      (stripe_session_id, stripe_event_id, provider, state, provider_doc_ref, provider_order_ref, last_error, updated_at)
    VALUES (?1, ?2, ?3, 'processing', ?4, NULL, NULL, ?5)
    ON CONFLICT(stripe_session_id) DO NOTHING
  `).bind(sessionId, eventId, provider, docRef, now).run();

  if ((inserted.meta?.changes || 0) === 1) return { acquired: true };

  const prior = await getOrder(db, sessionId);
  if (!prior) return { acquired: false, retry: true };
  if (prior.state === 'fulfilled') {
    return { acquired: false, fulfilled: true, provider: prior.provider, providerRef: prior.provider_order_ref || null };
  }

  const ageMs = Date.now() - Date.parse(prior.updated_at);
  if (prior.state === 'processing' && Number.isFinite(ageMs) && ageMs < PROCESSING_LEASE_MS) {
    return { acquired: false, retry: true };
  }

  const resumed = await db.prepare(`
    UPDATE commerce_orders
       SET stripe_event_id = ?2,
           provider = ?3,
           state = 'processing',
           provider_doc_ref = ?4,
           provider_order_ref = NULL,
           last_error = NULL,
           updated_at = ?5
     WHERE stripe_session_id = ?1
       AND state != 'fulfilled'
       AND updated_at = ?6
  `).bind(sessionId, eventId, provider, docRef, now, prior.updated_at).run();

  return { acquired: (resumed.meta?.changes || 0) === 1, retry: true };
}

async function markOrder(db, sessionId, eventId, provider, state, docRef, providerRef = null, error = null) {
  await db.prepare(`
    UPDATE commerce_orders
       SET stripe_event_id = ?2,
           provider = ?3,
           state = ?4,
           provider_doc_ref = ?5,
           provider_order_ref = ?6,
           last_error = ?7,
           updated_at = ?8
     WHERE stripe_session_id = ?1
  `).bind(
    sessionId,
    eventId,
    provider,
    state,
    docRef,
    providerRef,
    error,
    new Date().toISOString(),
  ).run();
}

function shippingFrom(session) {
  return session.shipping_details || session.collected_information?.shipping_details || null;
}

function validateSessionRoute(session) {
  const shipping = shippingFrom(session);
  const actualCountry = shipping?.address?.country?.toUpperCase?.() || '';
  const route = getRoute(actualCountry);
  if (!route) throw new Error(`Unsupported delivery country: ${actualCountry || 'missing'}`);

  const metadataCountry = session.metadata?.oolita_delivery_country?.toUpperCase?.() || '';
  const metadataProvider = session.metadata?.oolita_fulfilment_provider || '';
  const metadataPhase = session.metadata?.oolita_sales_phase || '';

  if (metadataCountry !== route.country) {
    throw new Error(`Checkout country ${metadataCountry || 'missing'} does not match shipping country ${route.country}`);
  }
  if (metadataProvider !== route.provider) {
    throw new Error(`Checkout provider ${metadataProvider || 'missing'} does not match route provider ${route.provider}`);
  }
  if (!['preorder', 'sale'].includes(metadataPhase)) {
    throw new Error(`Invalid sales phase metadata: ${metadataPhase || 'missing'}`);
  }
  if (session.currency && session.currency.toLowerCase() !== route.currency) {
    throw new Error(`Checkout currency ${session.currency} does not match ${route.currency}`);
  }

  return { route, phase: metadataPhase, shipping };
}

function bookVaultHeaders(env) {
  return {
    Authorization: `basic ${env.BOOKVAULT_API_KEY}`,
    accept: 'application/json',
  };
}

function requireBookVault(env) {
  if (env.BOOKVAULT_ENABLED !== 'true') throw new Error('BookVault fulfilment is not enabled');
  if (!env.BOOKVAULT_API_KEY) throw new Error('BOOKVAULT_API_KEY is not configured');
}

function buildBookVaultOrder(session, env, phase, shipping) {
  const address = shipping?.address;
  const customer = session.customer_details || {};
  if (!shipping?.name || !address?.line1 || !address?.city || !address?.postal_code || address?.country !== 'GB') {
    throw new Error('BookVault UK requires a complete GB shipping address');
  }

  const status = env.BOOKVAULT_ORDER_STATUS || (phase === 'preorder' ? 'PreSale' : 'Active');
  if (!['Draft', 'Active', 'PreSale', 'BatchPayment'].includes(status)) {
    throw new Error('BOOKVAULT_ORDER_STATUS is invalid');
  }

  const docRef = `OOLITA-BV-${session.id}`.slice(0, 90);
  return {
    docRef,
    payload: {
      Status: status,
      DocRef: docRef,
      DispatchRequest: {
        RequestedService: env.BOOKVAULT_REQUESTED_SERVICE || DEFAULT_REQUESTED_SERVICE,
      },
      ProductionLevel: env.BOOKVAULT_PRODUCTION_LEVEL || DEFAULT_PRODUCTION_LEVEL,
      Address: {
        Addressee: shipping.name,
        Address1: address.line1,
        Address2: address.line2 || '',
        Town: address.city,
        County: address.state || '',
        Postcode: address.postal_code,
        Country: { ISO_Code: 'GB' },
        TelNumber: customer.phone || '',
        Email: customer.email || session.customer_email || '',
      },
      OrderLines: [{
        ISBN: env.BOOKVAULT_OOLITA_ISBN || BOOK.isbn13,
        OrderQuantity: 1,
      }],
    },
  };
}

async function loadBookVaultOrder(docRef, env) {
  requireBookVault(env);
  const url = new URL('https://api.bookvault.app/v3/Order');
  url.searchParams.set('DocRef', docRef);
  const response = await fetch(url.toString(), { headers: bookVaultHeaders(env) });
  if (response.status === 404) return null;
  const text = await response.text();
  if (!response.ok) throw new Error(`BookVault lookup returned HTTP ${response.status}: ${text.slice(0, 500)}`);
  if (!text) return null;
  try {
    const parsed = JSON.parse(text);
    return parsed && Object.keys(parsed).length ? parsed : null;
  } catch (_) {
    throw new Error('BookVault lookup returned invalid JSON');
  }
}

async function createBookVaultOrder(payload, env) {
  requireBookVault(env);
  const response = await fetch('https://api.bookvault.app/v3/Order', {
    method: 'POST',
    headers: {
      ...bookVaultHeaders(env),
      'content-type': 'application/json',
    },
    body: JSON.stringify(payload),
  });
  const text = await response.text();
  let parsed = null;
  try {
    parsed = text ? JSON.parse(text) : null;
  } catch (_) {
    parsed = null;
  }
  if (!response.ok) throw new Error(`BookVault returned HTTP ${response.status}: ${text.slice(0, 500)}`);
  return parsed || {};
}

function bookVaultPodRef(result) {
  return result?.PodRef ?? result?.podRef ?? result?.PODRef ?? null;
}

async function fulfilBookVault(session, env, phase, shipping) {
  const order = buildBookVaultOrder(session, env, phase, shipping);
  const existing = await loadBookVaultOrder(order.docRef, env);
  if (existing) {
    const existingRef = bookVaultPodRef(existing);
    return {
      docRef: order.docRef,
      providerRef: existingRef == null ? null : String(existingRef),
      recovered: true,
    };
  }

  const result = await createBookVaultOrder(order.payload, env);
  const resultRef = bookVaultPodRef(result);
  return {
    docRef: order.docRef,
    providerRef: resultRef == null ? null : String(resultRef),
    recovered: false,
  };
}

async function fulfilSpanishPod(session) {
  const docRef = `OOLITA-ES-${session.id}`.slice(0, 90);
  throw Object.assign(new Error('Spanish POD adapter is not configured; Spain checkout must remain disabled'), { docRef });
}

export async function onRequestPost({ request, env }) {
  if (!env.STRIPE_WEBHOOK_SECRET) return json({ error: 'Stripe webhook is not configured' }, 503);
  if (!env.OOLITA_SUBSCRIBERS) return json({ error: 'Commerce idempotency database is not configured' }, 503);

  const rawBody = await request.text();
  const verified = await validStripeSignature(
    rawBody,
    request.headers.get('stripe-signature'),
    env.STRIPE_WEBHOOK_SECRET,
  );
  if (!verified) return json({ error: 'Invalid Stripe signature' }, 400);

  let event;
  try {
    event = JSON.parse(rawBody);
  } catch (_) {
    return json({ error: 'Invalid JSON payload' }, 400);
  }

  if (!['checkout.session.completed', 'checkout.session.async_payment_succeeded'].includes(event.type)) {
    return json({ received: true, ignored: event.type });
  }

  const session = event.data?.object;
  if (!session?.id) return json({ error: 'Missing Checkout Session' }, 400);
  if (session.payment_status !== 'paid') return json({ received: true, waiting_for_payment: true });
  if (session.metadata?.oolita_product_key !== BOOK.productKey) {
    return json({ received: true, ignored: 'non-OOLITA-book session' });
  }

  let validated;
  try {
    validated = validateSessionRoute(session);
  } catch (error) {
    return json({ error: String(error.message || error) }, 422);
  }

  const { route, phase, shipping } = validated;
  const provisionalDocRef = `${route.provider === 'bookvault' ? 'OOLITA-BV' : 'OOLITA-ES'}-${session.id}`.slice(0, 90);
  const db = env.OOLITA_SUBSCRIBERS;
  const eventId = event.id || 'unknown';

  await ensureOrdersTable(db);
  const claim = await claimOrder(db, session.id, eventId, route.provider, provisionalDocRef);
  if (claim.fulfilled) {
    return json({
      received: true,
      duplicate: true,
      provider: claim.provider,
      provider_order_ref: claim.providerRef,
    });
  }
  if (!claim.acquired) return json({ error: 'Fulfilment is already being handled; retry later' }, 503);

  try {
    let result;
    if (route.provider === 'bookvault') {
      result = await fulfilBookVault(session, env, phase, shipping);
    } else if (route.provider === 'spanish_pod') {
      result = await fulfilSpanishPod(session, env, phase, shipping);
    } else {
      throw new Error(`Unsupported fulfilment provider: ${route.provider}`);
    }

    await markOrder(
      db,
      session.id,
      eventId,
      route.provider,
      'fulfilled',
      result.docRef,
      result.providerRef,
    );
    return json({
      received: true,
      fulfilled: true,
      provider: route.provider,
      provider_order_ref: result.providerRef,
      recovered_existing_order: Boolean(result.recovered),
    });
  } catch (error) {
    const docRef = error?.docRef || provisionalDocRef;
    await markOrder(
      db,
      session.id,
      eventId,
      route.provider,
      'error',
      docRef,
      null,
      String(error.message || error).slice(0, 1000),
    );
    return json({ error: 'Fulfilment failed; Stripe should retry', provider: route.provider }, 502);
  }
}
