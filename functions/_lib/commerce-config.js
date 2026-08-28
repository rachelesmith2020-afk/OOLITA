export const BOOK = Object.freeze({
  productKey: 'oolita-book',
  isbn13: '9781066939800',
  preorderOpensAt: '2027-01-03T00:00:00Z',
  releaseAt: '2027-01-31T00:00:00Z',
  routes: Object.freeze({
    GB: Object.freeze({
      provider: 'bookvault',
      implemented: true,
      currency: 'gbp',
      priceEnv: 'STRIPE_BOOK_PRICE_GBP_ID',
      shippingRateEnv: 'STRIPE_BOOK_SHIPPING_GB_GBP_ID',
    }),
    ES: Object.freeze({
      provider: 'spanish_pod',
      implemented: false,
      currency: 'eur',
      priceEnv: 'STRIPE_BOOK_PRICE_EUR_ID',
      shippingRateEnv: 'STRIPE_BOOK_SHIPPING_ES_EUR_ID',
    }),
  }),
});

export function salesPhase(now = new Date()) {
  const timestamp = now instanceof Date ? now.getTime() : new Date(now).getTime();
  const preorderAt = Date.parse(BOOK.preorderOpensAt);
  const releaseAt = Date.parse(BOOK.releaseAt);

  if (!Number.isFinite(timestamp)) throw new Error('Invalid commerce clock');
  if (timestamp < preorderAt) return 'interest';
  if (timestamp < releaseAt) return 'preorder';
  return 'sale';
}

export function getRoute(country) {
  if (typeof country !== 'string') return null;
  const code = country.trim().toUpperCase();
  return BOOK.routes[code] ? { country: code, ...BOOK.routes[code] } : null;
}

export function routeConfiguration(route, env) {
  if (!route) return { configured: false, missing: ['route'] };

  const missing = [];
  if (!route.implemented) missing.push('provider_adapter');
  if (!env?.STRIPE_SECRET_KEY) missing.push('stripe_secret');
  if (!env?.[route.priceEnv]) missing.push('stripe_price');
  if (!env?.[route.shippingRateEnv]) missing.push('stripe_shipping_rate');

  if (route.provider === 'bookvault') {
    if (env?.BOOKVAULT_ENABLED !== 'true') missing.push('bookvault_enabled');
    if (!env?.BOOKVAULT_API_KEY) missing.push('bookvault_api_key');
  } else if (route.provider === 'spanish_pod') {
    if (env?.SPANISH_POD_ENABLED !== 'true') missing.push('spanish_pod_enabled');
  } else {
    missing.push('unknown_provider');
  }

  return { configured: missing.length === 0, missing };
}

export function checkoutReadiness(country, env, now = new Date()) {
  const phase = salesPhase(now);
  const route = getRoute(country);
  if (!route) return { ready: false, phase, reason: 'unsupported_country', route: null };

  if (phase === 'interest') {
    return { ready: false, phase, reason: 'preorder_not_open', route };
  }

  const configuration = routeConfiguration(route, env);
  if (!configuration.configured) {
    return {
      ready: false,
      phase,
      reason: 'route_not_configured',
      route,
      missing: configuration.missing,
    };
  }

  return { ready: true, phase, reason: null, route, missing: [] };
}
