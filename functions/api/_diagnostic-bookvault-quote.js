import { BOOK, salesPhase } from '../_lib/commerce-config.js';

function json(body, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      'content-type': 'application/json; charset=utf-8',
      'cache-control': 'no-store',
    },
  });
}

export async function onRequestGet({ env }) {
  if (salesPhase() !== 'interest') return json({ error: 'diagnostic_disabled' }, 404);
  if (env?.BOOKVAULT_ENABLED !== 'true' || !env?.BOOKVAULT_API_KEY) {
    return json({ ok: false, stage: 'configuration' }, 503);
  }

  const payload = {
    OrderLines: [{ ISBN: env.BOOKVAULT_OOLITA_ISBN || BOOK.isbn13, OrderQuantity: 1 }],
    CountryCode: 'GB',
    ServiceLevel: 'CheapestTracked',
    PartnerID: 0,
    Currency: 'GBP',
    ShipmentDate: BOOK.releaseAt,
    AreaCode: 'SW1A 1AA',
  };

  try {
    const response = await fetch('https://api.bookvault.app/v3/Dispatch', {
      method: 'POST',
      headers: {
        Authorization: `basic ${env.BOOKVAULT_API_KEY}`,
        accept: 'application/json',
        'content-type': 'application/json',
      },
      body: JSON.stringify(payload),
    });
    const text = await response.text();
    let parsed = null;
    try { parsed = text ? JSON.parse(text) : null; } catch (_) {}
    const services = Array.isArray(parsed?.Services) ? parsed.Services : Array.isArray(parsed?.services) ? parsed.services : [];
    const usable = services.map((service) => service?.Dispatch || service?.dispatch || service).filter((d) => d && Number.isFinite(Number(d.DelTotal ?? d.delTotal)) && Number.isFinite(Number(d.ServID ?? d.servID)));
    return json({
      ok: response.ok && usable.length > 0,
      bookvault_http_status: response.status,
      service_count: services.length,
      usable_service_count: usable.length,
      sample: usable.length ? {
        service_id: Number(usable[0].ServID ?? usable[0].servID),
        service_code: String(usable[0].ServCode ?? usable[0].servCode ?? ''),
        service_name: String(usable[0].ServName ?? usable[0].servName ?? ''),
        tracked: usable[0].Tracked ?? usable[0].tracked ?? null,
        delivery_total_gbp: Number(usable[0].DelTotal ?? usable[0].delTotal),
      } : null,
    }, response.ok ? 200 : 502);
  } catch (_) {
    return json({ ok: false, stage: 'network' }, 502);
  }
}
