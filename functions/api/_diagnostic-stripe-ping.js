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

const TARGET_URL = 'https://oolita.es/api/stripe-webhook';
const STRIPE_VERSION = '2026-08-26.dahlia';

export async function onRequestGet({ env }) {
  if (salesPhase() !== 'interest') return json({ error: 'diagnostic_disabled' }, 404);
  if (!env?.STRIPE_SECRET_KEY) return json({ ok: false, stage: 'configuration' }, 503);

  const listUrl = new URL('https://api.stripe.com/v2/core/event_destinations');
  listUrl.searchParams.set('include[0]', 'webhook_endpoint.url');
  listUrl.searchParams.set('limit', '100');

  const headers = {
    authorization: `Bearer ${env.STRIPE_SECRET_KEY}`,
    'Stripe-Version': STRIPE_VERSION,
  };

  const listed = await fetch(listUrl.toString(), { headers });
  const listText = await listed.text();
  let listJson = null;
  try { listJson = listText ? JSON.parse(listText) : null; } catch (_) {}

  if (!listed.ok) {
    return json({ ok: false, stage: 'list', stripe_http_status: listed.status }, 502);
  }

  const destinations = Array.isArray(listJson?.data) ? listJson.data : [];
  const destination = destinations.find((item) =>
    item?.type === 'webhook_endpoint' && item?.webhook_endpoint?.url === TARGET_URL
  );

  if (!destination?.id) {
    return json({
      ok: false,
      stage: 'match',
      stripe_http_status: listed.status,
      destination_count: destinations.length,
      found: false,
    }, 404);
  }

  const ping = await fetch(`https://api.stripe.com/v2/core/event_destinations/${encodeURIComponent(destination.id)}/ping`, {
    method: 'POST',
    headers,
  });
  const pingText = await ping.text();
  let pingJson = null;
  try { pingJson = pingText ? JSON.parse(pingText) : null; } catch (_) {}

  return json({
    ok: ping.ok,
    stage: 'ping',
    stripe_http_status: ping.status,
    destination_id: destination.id,
    destination_status: destination.status || null,
    event_id: pingJson?.id || null,
    event_type: pingJson?.type || null,
    livemode: pingJson?.livemode ?? null,
  }, ping.ok ? 200 : 502);
}
