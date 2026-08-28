import { salesPhase } from '../_lib/commerce-config.js';

function json(body, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      'content-type': 'application/json; charset=utf-8',
      'cache-control': 'no-store',
    },
  });
}

export async function onRequestPost({ env }) {
  if (salesPhase() !== 'interest') return json({ error: 'diagnostic_disabled' }, 404);
  if (!env?.STRIPE_SECRET_KEY) return json({ ok: false, stage: 'configuration' }, 503);

  const params = new URLSearchParams();
  params.set('mode', 'payment');
  params.set('success_url', 'https://oolita.es/en/?stripe_diagnostic=success');
  params.set('cancel_url', 'https://oolita.es/en/?stripe_diagnostic=cancel');
  params.set('customer_email', 'diagnostic@oolita.es');
  params.set('customer_creation', 'if_required');
  params.set('payment_method_collection', 'if_required');
  params.set('client_reference_id', 'OOLITA-WEBHOOK-DIAGNOSTIC-20260828');
  params.set('line_items[0][price_data][currency]', 'gbp');
  params.set('line_items[0][price_data][unit_amount]', '0');
  params.set('line_items[0][price_data][product_data][name]', 'OOLITA webhook diagnostic');
  params.set('line_items[0][quantity]', '1');
  params.set('metadata[diagnostic]', 'webhook-pairing-20260828');

  const response = await fetch('https://api.stripe.com/v1/checkout/sessions', {
    method: 'POST',
    headers: {
      authorization: `Bearer ${env.STRIPE_SECRET_KEY}`,
      'content-type': 'application/x-www-form-urlencoded',
      'idempotency-key': 'oolita-zero-webhook-diagnostic-20260828',
    },
    body: params.toString(),
  });

  const text = await response.text();
  let parsed = null;
  try { parsed = text ? JSON.parse(text) : null; } catch (_) {}

  if (!response.ok) {
    return json({
      ok: false,
      stage: 'create_session',
      stripe_http_status: response.status,
      stripe_error_type: parsed?.error?.type || null,
      stripe_error_code: parsed?.error?.code || null,
      stripe_error_message: String(parsed?.error?.message || '').slice(0, 220) || null,
    }, 502);
  }

  return json({
    ok: true,
    session_id: parsed?.id || null,
    checkout_url: parsed?.url || null,
    status: parsed?.status || null,
    payment_status: parsed?.payment_status || null,
    amount_total: parsed?.amount_total ?? null,
    currency: parsed?.currency || null,
    livemode: parsed?.livemode ?? null,
  });
}
