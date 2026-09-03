export const TEXTILE = Object.freeze({
  productKey: 'oolita-textile-01',
  releaseAt: '2027-04-11T00:00:00+02:00',
  country: 'GB',
  currency: 'gbp',
  provider: 'inner_sanctum_manual',
  supplier: 'The Inner Sanctum Group',
  shippingMode: 'fixed_manual',
  variants: Object.freeze({
    oversized: Object.freeze({
      key: 'oversized',
      sku: 'OOLITA-UK-OVERSIZED-WHITE',
      name: 'OOLITA Blaster 2.0',
      supplierProduct: 'Stanley/Stella Blaster 2.0 STTU959',
      supplierProductPath: '/products/sx795',
      productionCostMinor: 2300,
      provisionalRetailMinor: 3400,
      priceEnv: 'TEXTILE_OVERSIZED_PRICE_GBP_MINOR',
      sizes: Object.freeze(['XXS', 'XS', 'S', 'M', 'L', 'XL', '2XL', '3XL']),
    }),
  }),
});

export function textilePhase(now = new Date()) {
  const timestamp = now instanceof Date ? now.getTime() : new Date(now).getTime();
  if (!Number.isFinite(timestamp)) throw new Error('Invalid textile commerce clock');
  return timestamp < Date.parse(TEXTILE.releaseAt) ? 'staged' : 'sale';
}

export function getTextileVariant(value) {
  if (typeof value !== 'string') return null;
  const key = value.trim().toLowerCase();
  return TEXTILE.variants[key] || null;
}

export function normaliseTextileSize(variant, value) {
  if (!variant || typeof value !== 'string') return null;
  const size = value.trim().toUpperCase();
  return variant.sizes.includes(size) ? size : null;
}

export function positiveMinor(value) {
  const amount = Number(value);
  return Number.isInteger(amount) && amount >= 0 ? amount : null;
}

export function textileRuntimeConfig(env, variant) {
  const missing = [];
  if (!env?.STRIPE_SECRET_KEY) missing.push('stripe_secret');
  if (!env?.OOLITA_SUBSCRIBERS) missing.push('orders_database');
  if (env?.TEXTILE_UK_ENABLED !== 'true') missing.push('textile_uk_enabled');

  const retailMinor = positiveMinor(env?.[variant.priceEnv]);
  if (retailMinor == null || retailMinor <= 0) missing.push(variant.priceEnv.toLowerCase());

  const shippingMinor = positiveMinor(env?.TEXTILE_UK_SHIPPING_GBP_MINOR);
  if (shippingMinor == null) missing.push('textile_uk_shipping_gbp_minor');

  return {
    configured: missing.length === 0,
    missing,
    retailMinor,
    shippingMinor,
  };
}
