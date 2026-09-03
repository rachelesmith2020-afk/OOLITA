export const TEXTILE = Object.freeze({
  productKey: 'oolita-textile-01',
  releaseAt: '2027-04-11T00:00:00+02:00',
  country: 'GB',
  currency: 'gbp',
  provider: 'inner_sanctum_manual',
  supplier: 'The Inner Sanctum Group',
  shippingMode: 'fixed_manual',
  stripePriceEnv: 'TEXTILE_BLASTER_PRICE_GBP_ID',
  storefronts: Object.freeze({
    es: Object.freeze({
      key: 'es',
      locale: 'es',
      page: 'https://oolita.es/ediciones/camiseta/',
    }),
    en: Object.freeze({
      key: 'en',
      locale: 'en',
      page: 'https://oolita.es/en/editions/t-shirt/',
    }),
  }),
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

export function getTextileStorefront(value) {
  if (typeof value !== 'string') return null;
  const key = value.trim().toLowerCase();
  return TEXTILE.storefronts[key] || null;
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

export function validStripePriceId(value) {
  return typeof value === 'string' && /^price_[A-Za-z0-9]+$/.test(value.trim()) ? value.trim() : null;
}

export function textileRuntimeConfig(env, variant, storefront) {
  const missing = [];
  if (!env?.STRIPE_SECRET_KEY) missing.push('stripe_secret');
  if (!env?.OOLITA_SUBSCRIBERS) missing.push('orders_database');
  if (env?.TEXTILE_UK_ENABLED !== 'true') missing.push('textile_uk_enabled');
  if (!storefront) missing.push('textile_storefront');

  const retailMinor = positiveMinor(env?.[variant.priceEnv]);
  if (retailMinor == null || retailMinor <= 0) missing.push(variant.priceEnv.toLowerCase());

  const shippingMinor = positiveMinor(env?.TEXTILE_UK_SHIPPING_GBP_MINOR);
  if (shippingMinor == null) missing.push('textile_uk_shipping_gbp_minor');

  const priceId = validStripePriceId(env?.[TEXTILE.stripePriceEnv]);
  if (!priceId) missing.push(TEXTILE.stripePriceEnv.toLowerCase());

  return {
    configured: missing.length === 0,
    missing,
    retailMinor,
    shippingMinor,
    priceId,
  };
}
