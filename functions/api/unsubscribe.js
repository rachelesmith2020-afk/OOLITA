function page(lang, title, body, status = 200) {
  return new Response(`<!doctype html><html lang="${lang}"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow"><title>${title}</title><body><main style="max-width:42rem;margin:10vh auto;padding:0 1.25rem;font:18px/1.5 system-ui,sans-serif"><h1>${title}</h1><p>${body}</p><p><a href="${lang === "es" ? "/" : "/en/"}">OOLITA</a></p></main></body></html>`, {
    status,
    headers: { "Content-Type": "text/html; charset=utf-8", "Cache-Control": "no-store", "X-Robots-Tag": "noindex, nofollow" },
  });
}

export async function onRequestGet(context) {
  const url = new URL(context.request.url);
  const token = (url.searchParams.get("token") || "").trim();
  const lang = url.searchParams.get("lang") === "es" ? "es" : "en";
  if (!context.env.OOLITA_SUBSCRIBERS) {
    return page(lang, lang === "es" ? "No disponible" : "Unavailable", lang === "es" ? "La lista no está disponible en este momento." : "The list is unavailable right now.", 503);
  }
  if (!/^[a-f0-9]{48}$/.test(token)) {
    return page(lang, lang === "es" ? "Enlace no válido" : "Invalid link", lang === "es" ? "Este enlace de baja no es válido." : "This unsubscribe link is not valid.", 400);
  }

  const now = new Date().toISOString();
  try {
    const result = await context.env.OOLITA_SUBSCRIBERS.prepare(
      "UPDATE subscribers SET status='unsubscribed', unsubscribed_at=?, updated_at=? WHERE unsubscribe_token=?"
    ).bind(now, now, token).run();
    if (!result.meta || result.meta.changes < 1) {
      return page(lang, lang === "es" ? "Enlace no válido" : "Invalid link", lang === "es" ? "Este enlace ya no corresponde a una suscripción activa." : "This link no longer matches an active subscription.", 404);
    }
  } catch (err) {
    console.error("unsubscribe D1 error", err);
    return page(lang, lang === "es" ? "No disponible" : "Unavailable", lang === "es" ? "No hemos podido procesar la baja. Escríbenos a oolita@tutamail.com." : "We could not process the unsubscribe request. Write to oolita@tutamail.com.", 500);
  }

  return page(lang, lang === "es" ? "Baja confirmada" : "Unsubscribed", lang === "es" ? "Tu dirección ha sido dada de baja de OOLITA." : "Your address has been unsubscribed from OOLITA.");
}

export function onRequest() {
  return new Response("Method not allowed", { status: 405, headers: { Allow: "GET", "X-Robots-Tag": "noindex, nofollow" } });
}
