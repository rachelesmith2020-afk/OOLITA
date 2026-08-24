const TOKEN_RE = /^[a-f0-9]{48}$/;

function token() {
  const bytes = new Uint8Array(24);
  crypto.getRandomValues(bytes);
  return Array.from(bytes, (b) => b.toString(16).padStart(2, "0")).join("");
}

function page(language, state) {
  const es = language === "es";
  const copy = {
    confirmed: es
      ? ["Correo confirmado", "Ya formas parte de la lista de OOLITA.", "Volver a OOLITA"]
      : ["Email confirmed", "You are now on the OOLITA list.", "Return to OOLITA"],
    expired: es
      ? ["Enlace caducado", "Vuelve a introducir tu correo en OOLITA para recibir un enlace nuevo.", "Volver a OOLITA"]
      : ["Link expired", "Enter your email again on OOLITA to receive a new confirmation link.", "Return to OOLITA"],
    invalid: es
      ? ["Enlace no válido", "Este enlace de confirmación no es válido o ya fue utilizado.", "Volver a OOLITA"]
      : ["Invalid link", "This confirmation link is invalid or has already been used.", "Return to OOLITA"],
  }[state];
  const lang = es ? "es" : "en";
  return `<!doctype html><html lang="${lang}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow"><title>${copy[0]} · OOLITA</title><style>body{margin:0;background:#f1e6cf;color:#132572;font-family:system-ui,sans-serif}main{max-width:42rem;margin:0 auto;padding:12vh 6vw}h1{font-size:clamp(2.5rem,8vw,6rem);line-height:.95;font-weight:500;margin:0 0 2rem}p{font-size:1.1rem;line-height:1.5;max-width:34rem}a{color:inherit;text-underline-offset:.18em}</style></head><body><main><p>OOLITA · Los Escullos</p><h1>${copy[0]}</h1><p>${copy[1]}</p><p><a href="${es ? "/" : "/en/"}">${copy[2]} ↗</a></p></main></body></html>`;
}

function htmlResponse(language, state, status = 200) {
  return new Response(page(language, state), {
    status,
    headers: {
      "Content-Type": "text/html; charset=utf-8",
      "Cache-Control": "no-store",
      "X-Robots-Tag": "noindex, nofollow",
      "Referrer-Policy": "no-referrer",
    },
  });
}

export async function onRequestGet(context) {
  const { request, env } = context;
  if (!env.OOLITA_SUBSCRIBERS) return htmlResponse("en", "invalid", 503);

  const url = new URL(request.url);
  const confirmationToken = String(url.searchParams.get("token") || "").trim().toLowerCase();
  if (!TOKEN_RE.test(confirmationToken)) return htmlResponse("en", "invalid", 400);

  let row;
  try {
    row = await env.OOLITA_SUBSCRIBERS.prepare(`
      SELECT email, language, consent_at
      FROM subscribers
      WHERE unsubscribe_token = ? AND status = 'pending_confirmation'
    `).bind(confirmationToken).first();
  } catch (err) {
    console.error("confirmation lookup error", err);
    return htmlResponse("en", "invalid", 503);
  }

  if (!row) return htmlResponse("en", "invalid", 404);
  const language = row.language === "es" ? "es" : "en";

  const consentAt = Date.parse(row.consent_at || "");
  if (!Number.isFinite(consentAt) || Date.now() - consentAt > 72 * 60 * 60 * 1000) {
    try {
      await env.OOLITA_SUBSCRIBERS.prepare(
        "DELETE FROM subscribers WHERE email = ? AND status = 'pending_confirmation'"
      ).bind(row.email).run();
    } catch (err) {
      console.error("expired confirmation cleanup error", err);
    }
    return htmlResponse(language, "expired", 410);
  }

  const now = new Date().toISOString();
  const unsubscribeToken = token();
  try {
    const result = await env.OOLITA_SUBSCRIBERS.prepare(`
      UPDATE subscribers
      SET status = 'active', verified_at = ?, unsubscribe_token = ?, updated_at = ?
      WHERE email = ? AND status = 'pending_confirmation' AND unsubscribe_token = ?
    `).bind(now, unsubscribeToken, now, row.email, confirmationToken).run();
    const changes = Number(result && result.meta && result.meta.changes);
    if (!result || !result.success || !Number.isFinite(changes) || changes !== 1) {
      return htmlResponse(language, "invalid", 409);
    }
  } catch (err) {
    console.error("confirmation update error", err);
    return htmlResponse(language, "invalid", 503);
  }

  return htmlResponse(language, "confirmed", 200);
}

export function onRequest() {
  return new Response("Method not allowed", { status: 405, headers: { Allow: "GET", "X-Robots-Tag": "noindex, nofollow" } });
}
