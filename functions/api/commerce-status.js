import { BOOK, getRoute, routeConfiguration, salesPhase } from '../_lib/commerce-config.js';

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
  const phase = salesPhase();
  const countries = Object.keys(BOOK.routes);
  const configuredCountries = countries.filter((country) => {
    const route = getRoute(country);
    return routeConfiguration(route, env).configured;
  });

  return json({
    product_key: BOOK.productKey,
    isbn13: BOOK.isbn13,
    phase,
    preorder_opens_at: BOOK.preorderOpensAt,
    release_at: BOOK.releaseAt,
    supported_countries: countries,
    configured_countries: configuredCountries,
    checkout_countries: phase === 'interest' ? [] : configuredCountries,
  });
}
