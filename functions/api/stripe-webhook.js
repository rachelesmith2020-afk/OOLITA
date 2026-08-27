const BOOK_PRODUCT_KEY = 'oolita-book';
const DEFAULT_ISBN = '9781066939800';
const DEFAULT_PRODUCTION_LEVEL = 'Standard';
const DEFAULT_REQUESTED_SERVICE = 'CheapestTracked';
const STRIPE_TOLERANCE_SECONDS = 300;

function jsonResponse(body, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'content-type': 'application/json; charset=utf-8' },
  });
}

function hex(bytes) {
  return Array.from(new Uint8Array(bytes), (b) => b.toString(16).padStart(2, '0')).join('');
}

function constantTimeEqual(a, b) {
  if (typeof a !== 'string' || typeof b !== 'string' || a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i += 1) diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return diff === 0;
}

async function verifyStripeSignature(rawBody, header, secret) {
  if (!header || !secret) return false;
  const parts = header.split(',').map((part) => part.trim());
  const timestampPart = parts.find((part) => part.startsWith('t='));
  const signatures = parts.filter((part) => part.startsWith('v1=')).map((part) => part.slice(3));
  if (!timestampPart || signatures.length === 0) return false;

  const timestamp = Number(timestampPart.slice(2));
  if (!Number.isFinite(timestamp)) return false;
  const now = Math.floor(Date.now() / 1000);
  if (Math.abs(now - timestamp) > STRIPE_TOLERANCE_SECONDS) return false;

  const key = await crypto.subtle.importKey(
    'raw',
    new TextEncoder().encode(secret),
    { name: 'HMAC', hash: 'SHA-256' },
    false,
    ['sign'],
  );
  const signed = `${timestamp}.${rawBody}`;
  const digest = hex(await crypto.subtle.sign('HMAC', key, new TextEncoder().encode(signed)));
  return signatures.some((candidate) => constantTimeEqual(digest, candidate));
}

async function ensureTable(db) {
  await db.prepare(`
    CREATE TABLE IF NOT EXISTS commerce_fulfilment (
      stripe_session_id TEXT PRIMARY KEY,
      stripe_event_id TEXT NOT NULL,
      state TEXT NOT NULL,
      bookvault_doc_ref TEXT NOT NULL,
      bookvault_pod_ref TEXT,
      last_error TEXT,
      updated_at TEXT NOT NULL
    )
  `).run();
}

async function existingFulfilment(db, sessionId) {
  return db.prepare(
    'SELECT state, updated_at, bookvault_pod_ref FROM commerce_fulfilment WHERE stripe_session_id = ?1',
  ).bind(sessionId).first();
}

async function markState(db, { sessionId, eventId, state, docRef, podRef = null, error = null }) {
  const now = new Date().toISOString();
  await db.prepare(`
    INSERT INTO commerce_fulfilment
      (stripe_session_id, stripe_event_id, state, bookvault_doc_ref, bookvault_pod_ref, last_error, updated_at)
    VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7)
    ON CONFLICT(stripe_session_id) DO UPDATE SET
      stripe_event_id = excluded.stripe_event_id,
      state = excluded.state,
      bookvault_pod_ref = excluded.bookvault_pod_ref,
      last_error = excluded.last_error,
      updated_at = excluded.updated_at
  `).bind(sessionId, eventId, state, docRef, podRef, error, now).run();
}

function shippingDetails(session) {
  return session.shipping_details || session.collected_information?.shipping_details || null;
}

function buildBookvaultOrder(session, env) {
  const shipping = shippingDetails(session);
  const address = shipping?.address;
  const customer = session.customer_details || {};
  if (!shipping?.name || !address?.line1 || !address?.city || !address?.postal_code || !address?.country) {
    throw new Error('Stripe session is missing a complete shipping address');
  }

  const docRef = `OOLITA-${session.id}`.slice(0, 90);
  const status = env.BOOKVAULT_ORDER_STATUS || 'Active';
  if (!['Draft', 'Active', 'PreSale', 'BatchPayment'].includes(status)) {
    throw new Error('BOOKVAULT_ORDER_STATUS is invalid');
  }

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
        Country: { ISO_Code: address.country },
        TelNumber: customer.phone || '',
        Email: customer.email || session.customer_email || '',
      },
      OrderLines: [
        {
          ISBN: env.BOOKVAULT_OOLITA_ISBN || DEFAULT_ISBN,
          OrderQuantity: 1,
        },
      ],
    },
  };
}

async function sendToBookvault(payload, env) {
  if (env.BOOKVAULT_ENABLED !== 'true') {
    throw new Error('BookVault fulfilment is staged but not enabled');
  }
  if (!env.BOOKVAULT_API_KEY) {
    throw new Error('BOOKVAULT_API_KEY is not configured');
  }

  const response = await fetch('https://api.bookvault.app/v3/Order', {
    method: 'POST',
    headers: {
      Authorization: `basic ${env.BOOKVAULT_API_KEY}`,
      'content-type': 'application/json',
      accept: 'application/json',
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
  if (!response.ok) {
    throw new Error(`BookVault returned HTTP ${response.status}: ${text.slice(0, 500)}`);
  }
  return parsed || {};
}

export async function onRequestPost(context) {
  const { request, env } = context;
  if (!env.STRIPE_WEBHOOK_SECRET) {
    return jsonResponse({ error: 'Stripe webhook is not configured' }, 503);
  }
  if (!env.OOLITA_SUBSCRIBERS) {
    return jsonResponse({ error: 'Commerce idempotency database is not configured' }, 503);
  }

  const rawBody = await request.text();
  const signature = request.headers.get('stripe-signature');
  const verified = await verifyStripeSignature(rawBody, signature, env.STRIPE_WEBHOOK_SECRET);
  if (!verified) return jsonResponse({ error: 'Invalid Stripe signature' }, 400);

  let event;
  try {
    event = JSON.parse(rawBody);
  } catch (_) {
    return jsonResponse({ error: 'Invalid JSON payload' }, 400);
  }

  if (!['checkout.session.completed', 'checkout.session.async_payment_succeeded'].includes(event.type)) {
    return jsonResponse({ received: true, ignored: event.type });
  }

  const session = event.data?.object;
  if (!session?.id) return jsonResponse({ error: 'Missing Checkout Session' }, 400);
  if (session.payment_status !== 'paid') {
    return jsonResponse({ received: true, waiting_for_payment: true });
  }
  if (session.metadata?.oolita_product_key !== BOOK_PRODUCT_KEY) {
    return jsonResponse({ received: true, ignored: 'non-OOLITA-book session' });
  }

  const db = env.OOLITA_SUBSCRIBERS;
  await ensureTable(db);
  const prior = await existingFulfilment(db, session.id);
  if (prior?.state === 'fulfilled') {
    return jsonResponse({ received: true, duplicate: true, bookvault_pod_ref: prior.bookvault_pod_ref || null });
  }
  if (prior?.state === 'processing') {
    const ageMs = Date.now() - Date.parse(prior.updated_at);
    if (Number.isFinite(ageMs) && ageMs < 120000) {
      return jsonResponse({ error: 'Fulfilment already processing; retry later' }, 503);
    }
  }

  let order;
  try {
    order = buildBookvaultOrder(session, env);
  } catch (error) {
    return jsonResponse({ error: error.message }, 422);
  }

  await markState(db, {
    sessionId: session.id,
    eventId: event.id || 'unknown',
    state: 'processing',
    docRef: order.docRef,
  });

  try {
    const result = await sendToBookvault(order.payload, env);
    const podRef = result.PodRef ?? result.podRef ?? result.PODRef ?? null;
    await markState(db, {
      sessionId: session.id,
      eventId: event.id || 'unknown',
      state: 'fulfilled',
      docRef: order.docRef,
      podRef: podRef == null ? null : String(podRef),
    });
    return jsonResponse({ received: true, fulfilled: true, bookvault_pod_ref: podRef });
  } catch (error) {
    await markState(db, {
      sessionId: session.id,
      eventId: event.id || 'unknown',
      state: 'error',
      docRef: order.docRef,
      error: String(error.message || error).slice(0, 1000),
    });
    return jsonResponse({ error: 'BookVault fulfilment failed; Stripe should retry' }, 502);
  }
}
