const BOOK_PRODUCT_KEY = 'oolita-book';
const DEFAULT_ISBN = '9781066939800';
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

async function ensureFulfilmentTable(db) {
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

async function getFulfilment(db, sessionId) {
  return db.prepare(
    'SELECT state, updated_at, bookvault_pod_ref FROM commerce_fulfilment WHERE stripe_session_id = ?1',
  ).bind(sessionId).first();
}

async function claimFulfilment(db, sessionId, eventId, docRef) {
  const now = new Date().toISOString();
  const inserted = await db.prepare(`
    INSERT INTO commerce_fulfilment
      (stripe_session_id, stripe_event_id, state, bookvault_doc_ref, bookvault_pod_ref, last_error, updated_at)
    VALUES (?1, ?2, 'processing', ?3, NULL, NULL, ?4)
    ON CONFLICT(stripe_session_id) DO NOTHING
  `).bind(sessionId, eventId, docRef, now).run();

  if ((inserted.meta?.changes || 0) === 1) return { acquired: true };

  const prior = await getFulfilment(db, sessionId);
  if (!prior) return { acquired: false, retry: true };
  if (prior.state === 'fulfilled') {
    return { acquired: false, fulfilled: true, podRef: prior.bookvault_pod_ref || null };
  }

  const ageMs = Date.now() - Date.parse(prior.updated_at);
  if (prior.state === 'processing' && Number.isFinite(ageMs) && ageMs < PROCESSING_LEASE_MS) {
    return { acquired: false, retry: true };
  }

  const resumed = await db.prepare(`
    UPDATE commerce_fulfilment
       SET stripe_event_id = ?2,
           state = 'processing',
           bookvault_doc_ref = ?3,
           bookvault_pod_ref = NULL,
           last_error = NULL,
           updated_at = ?4
     WHERE stripe_session_id = ?1
       AND state != 'fulfilled'
       AND updated_at = ?5
  `).bind(sessionId, eventId, docRef, now, prior.updated_at).run();

  return { acquired: (resumed.meta?.changes || 0) === 1, retry: true };
}

async function markFulfilment(db, sessionId, eventId, state, docRef, podRef = null, error = null) {
  await db.prepare(`
    UPDATE commerce_fulfilment
       SET stripe_event_id = ?2,
           state = ?3,
           bookvault_doc_ref = ?4,
           bookvault_pod_ref = ?5,
           last_error = ?6,
           updated_at = ?7
     WHERE stripe_session_id = ?1
  `).bind(
    sessionId,
    eventId,
    state,
    docRef,
    podRef,
    error,
    new Date().toISOString(),
  ).run();
}

function shippingFrom(session) {
  return session.shipping_details || session.collected_information?.shipping_details || null;
}

function buildBookVaultOrder(session, env) {
  const shipping = shippingFrom(session);
  const address = shipping?.address;
  const customer = session.customer_details || {};
  if (!shipping?.name || !address?.line1 || !address?.city || !address?.postal_code || !address?.country) {
    throw new Error('Stripe session is missing a complete shipping address');
  }

  const status = env.BOOKVAULT_ORDER_STATUS || 'Active';
  if (!['Draft', 'Active', 'PreSale', 'BatchPayment'].includes(status)) {
    throw new Error('BOOKVAULT_ORDER_STATUS is invalid');
  }

  const docRef = `OOLITA-${session.id}`.slice(0, 90);
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
      OrderLines: [{
        ISBN: env.BOOKVAULT_OOLITA_ISBN || DEFAULT_ISBN,
        OrderQuantity: 1,
      }],
    },
  };
}

function requireBookVault(env) {
  if (env.BOOKVAULT_ENABLED !== 'true') {
    throw new Error('BookVault fulfilment is staged but not enabled');
  }
  if (!env.BOOKVAULT_API_KEY) throw new Error('BOOKVAULT_API_KEY is not configured');
}

function bookVaultHeaders(env) {
  return {
    Authorization: `basic ${env.BOOKVAULT_API_KEY}`,
    accept: 'application/json',
  };
}

async function loadBookVaultOrder(docRef, env) {
  requireBookVault(env);
  const url = new URL('https://api.bookvault.app/v3/Order');
  url.searchParams.set('DocRef', docRef);
  const response = await fetch(url.toString(), { headers: bookVaultHeaders(env) });
  if (response.status === 404) return null;
  const text = await response.text();
  if (!response.ok) {
    throw new Error(`BookVault lookup returned HTTP ${response.status}: ${text.slice(0, 500)}`);
  }
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
  if (!response.ok) {
    throw new Error(`BookVault returned HTTP ${response.status}: ${text.slice(0, 500)}`);
  }
  return parsed || {};
}

function podRef(result) {
  return result?.PodRef ?? result?.podRef ?? result?.PODRef ?? null;
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
  if (session.metadata?.oolita_product_key !== BOOK_PRODUCT_KEY) {
    return json({ received: true, ignored: 'non-OOLITA-book session' });
  }

  let order;
  try {
    order = buildBookVaultOrder(session, env);
  } catch (error) {
    return json({ error: error.message }, 422);
  }

  const db = env.OOLITA_SUBSCRIBERS;
  const eventId = event.id || 'unknown';
  await ensureFulfilmentTable(db);
  const claim = await claimFulfilment(db, session.id, eventId, order.docRef);

  if (claim.fulfilled) {
    return json({ received: true, duplicate: true, bookvault_pod_ref: claim.podRef });
  }
  if (!claim.acquired) return json({ error: 'Fulfilment is already being handled; retry later' }, 503);

  try {
    // A deterministic DocRef closes the ambiguous-failure gap: if BookVault
    // accepted a prior POST but our response was lost, recover that order rather
    // than printing a second copy when Stripe retries the webhook.
    const existing = await loadBookVaultOrder(order.docRef, env);
    if (existing) {
      const existingPodRef = podRef(existing);
      await markFulfilment(
        db,
        session.id,
        eventId,
        'fulfilled',
        order.docRef,
        existingPodRef == null ? null : String(existingPodRef),
      );
      return json({
        received: true,
        fulfilled: true,
        recovered_existing_bookvault_order: true,
        bookvault_pod_ref: existingPodRef,
      });
    }

    const result = await createBookVaultOrder(order.payload, env);
    const resultPodRef = podRef(result);
    await markFulfilment(
      db,
      session.id,
      eventId,
      'fulfilled',
      order.docRef,
      resultPodRef == null ? null : String(resultPodRef),
    );
    return json({ received: true, fulfilled: true, bookvault_pod_ref: resultPodRef });
  } catch (error) {
    await markFulfilment(
      db,
      session.id,
      eventId,
      'error',
      order.docRef,
      null,
      String(error.message || error).slice(0, 1000),
    );
    return json({ error: 'BookVault fulfilment failed; Stripe should retry' }, 502);
  }
}
